# Redis 源码深度解读：核心数据结构与事件驱动模型

> "Redis 之所以快，不是因为它用了什么魔法，而是因为它的每一个数据结构都经过精心设计，每一个 I/O 操作都被事件循环精准调度。" —— antirez（Redis 作者）

---

## 📋 目录

1. [Redis 整体架构概览](#1-redis-整体架构概览)
2. [ SDS 动态字符串源码解析](#2-sds-动态字符串源码解析)
3. [ Dict 字典与渐进式 Rehash](#3-dict-字典与渐进式-rehash)
4. [ SkipList 跳表源码解析](#4-skiplist-跳表源码解析)
5. [ ZipList 压缩列表源码解析](#5-ziplist-压缩列表源码解析)
6. [ QuickList 快速列表源码解析](#6-quicklist-快速列表源码解析)
7. [ IntSet 整数集合源码解析](#7-intset-整数集合源码解析)
8. [事件驱动模型 Reactor 模式](#8-事件驱动模型-reactor-模式)
9. [ Redis 6.0 多线程 I/O 模型](#9-redis-60-多线程-io-模型)
10. [面试题速查](#10-面试题速查)

---

## 1. Redis 整体架构概览

Redis 是一个基于 C 语言编写的高性能键值对数据库，其核心设计理念是"单线程 + 事件驱动"。整个 Redis 服务端的架构可以分为以下几个层次：

```
┌─────────────────────────────────────────────┐
│                 客户端连接层                   │
├─────────────────────────────────────────────┤
│  命令解析层 ( networking.c / server.c )       │
├─────────────────────────────────────────────┤
│  命令执行层 ( t_string.c / t_list.c / ... )   │
├─────────────────────────────────────────────┤
│  数据结构层 ( sds.c / dict.c / t_zset.c )     │
├─────────────────────────────────────────────┤
│  持久化层 ( rdb.c / aof.c )                   │
├─────────────────────────────────────────────┤
│  事件驱动层 ( ae.c / networking.c )           │
└─────────────────────────────────────────────┘
```

Redis 的单线程模型并非没有多线程，而是在**命令执行阶段**使用单线程，I/O 层在 6.0 版本引入了多线程。这种设计避免了锁竞争和上下文切换的开销。

Redis 的核心数据结构在源码层面有一套自己的实现，与对外暴露的数据类型并不完全一一对应。下面我们逐个深入解析。

---

## 2. SDS 动态字符串源码解析

### 2.1 为什么不用 C 标准字符串

C 标准字符串（以 `\0` 结尾的字符数组）存在以下问题：

- 获取长度需要 O(n) 遍历
- 二进制不安全（中间出现 `\0` 会被截断）
- 缓冲区溢出风险
- 修改字符串时频繁内存分配

Redis 设计了 SDS（Simple Dynamic String）来解决这些问题。

### 2.2 SDS 数据结构定义

在 Redis 3.2 之后，SDS 被拆分为 5 种头部类型，根据字符串长度选择最紧凑的表示：

```c
// sds.h
struct __attribute__ ((__packed__)) sdshdr5 {
    unsigned char flags; /* 低3位存类型，高5位存长度 */
    char buf[];
};

struct __attribute__ ((__packed__)) sdshdr8 {
    uint8_t len;          /* 已使用长度 */
    uint8_t alloc;        /* 分配总长度 */
    unsigned char flags;  /* 低3位存类型标识 */
    char buf[];           /* 实际数据 */
};

struct __attribute__ ((__packed__)) sdshdr16 {
    uint16_t len;
    uint16_t alloc;
    unsigned char flags;
    char buf[];
};

// sdshdr32 和 sdshdr64 结构类似，只是 len/alloc 类型不同
```

`__attribute__ ((__packed__))` 告诉编译器取消结构体优化对齐，按实际字节紧凑排列，节省内存。`flags` 的低 3 位标识类型（0~4 对应 sdshdr5~sdshdr64），高 5 位在 sdshdr5 中复用存储短长度。

### 2.3 SDS 创建与扩容

```c
// sds.c
sds sdsnewlen(const void *init, size_t initlen) {
    void *sh;
    sds s;
    // 根据长度选择合适的头部类型
    char type = sdsReqType(initlen);
    /* 空字符串默认用 sdshdr8 而非 sdshdr5，因为空串通常会被追加 */
    if (type == SDS_TYPE_5 && initlen == 0) type = SDS_TYPE_8;
    int hdrlen = sdsHdrSize(type);
    unsigned char *fp; /* flags pointer */

    // 分配内存：头部 + 数据 + 1（'\0'）
    sh = s_malloc(hdrlen + initlen + 1);
    if (sh == NULL) return NULL;
    if (init == SDS_NOINIT)
        memset(sh, 0, hdrlen + initlen + 1);
    else if (init) {
        memcpy(sh, init, initlen);
    }
    s = (char*)sh + hdrlen;  // s 指向 buf 起始位置
    fp = (unsigned char*)s - 1; // flags 紧挨在 buf 前面

    switch(type) {
        case SDS_TYPE_5: {
            *fp = type | (initlen << SDS_TYPE_BITS);
            break;
        }
        case SDS_TYPE_8: {
            SDS_HDR_VAR(8,s);
            sh->len = initlen;
            sh->alloc = initlen;
            *fp = type;
            break;
        }
        // ... 其他类型类似
    }
    s[initlen] = '\0';
    return s;
}
```

关键设计：`sds` 返回的是 `buf` 的指针而非头部指针。这样所有 SDS API 都可以直接用 `s` 操作字符串，兼容 C 字符串函数。需要访问头部信息时，通过 `s - hdrlen` 反向定位头部。

### 2.4 SDS 扩容策略

```c
sds sdsMakeRoomFor(sds s, size_t addlen) {
    void *sh, *newsh;
    size_t avail = sdsavail(s);
    size_t len, newlen;
    char type, oldtype = s[-1] & SDS_TYPE_MASK;
    int hdrlen;

    /* 剩余空间足够，直接返回 */
    if (avail >= addlen) return s;

    len = sdslen(s);
    sh = (char*)s - sdsHdrSize(oldtype);
    newlen = len + addlen;

    // 预分配策略
    if (newlen < SDS_MAX_PREALLOC)   // 1MB
        newlen *= 2;                  // 小于1MB时翻倍
    else
        newlen += SDS_MAX_PREALLOC;   // 大于1MB时每次多分配1MB

    type = sdsReqType(newlen);
    if (type == SDS_TYPE_5) type = SDS_TYPE_8;

    hdrlen = sdsHdrSize(type);
    if (oldtype == type) {
        // 类型没变，原地 realloc
        newsh = s_realloc(sh, hdrlen + newlen + 1);
        if (newsh == NULL) return NULL;
        s = (char*)newsh + hdrlen;
    } else {
        // 类型变了，需要重新分配并移动数据
        newsh = s_malloc(hdrlen + newlen + 1);
        if (newsh == NULL) return NULL;
        memcpy((char*)newsh + hdrlen, s, len + 1);
        s_free(sh);
        s = (char*)newsh + hdrlen;
        s[-1] = type;
        sdssetlen(s, len);
    }
    sdssetalloc(s, newlen);
    return s;
}
```

预分配策略的精髓：
- 修改后长度 < 1MB：分配 `2 × newlen` 空间（翻倍）
- 修改后长度 ≥ 1MB：额外多分配 1MB

这种策略在连续追加操作时将内存分配次数从 O(n) 降到了 O(log n)。

### 2.5 SDS 关键特性总结

| 特性 | C 字符串 | SDS |
|------|---------|-----|
| 获取长度 | O(n) | O(1) |
| 缓冲区安全 | 可能溢出 | 自动扩容 |
| 二进制安全 | 否 | 是 |
| 内存分配次数 | 每次修改 | 摊还 O(1) |
| 兼容 C 函数 | - | 是（末尾 `\0`）|

---

## 3. Dict 字典与渐进式 Rehash

### 3.1 Dict 数据结构

Dict 是 Redis 最核心的数据结构，几乎所有功能都依赖它：数据库键空间、哈希表、Set 底层等。

```c
// dict.h
typedef struct dictEntry {
    void *key;
    union {
        void *val;
        uint64_t u64;
        int64_t s64;
        double d;
    } v;                    // 值使用 union 节省内存
    struct dictEntry *next; // 链地址法解决冲突
} dictEntry;

typedef struct dictht {
    dictEntry **table;      // 哈希桶数组
    unsigned long size;     // 桶数量（总是 2 的幂）
    unsigned long sizemask; // size - 1，用于快速取模
    unsigned long used;     // 已有节点数
} dictht;

typedef struct dict {
    dictType *type;         // 类型特定函数（hash、keyDup、valDup等）
    void *privdata;
    dictht ht[2];           // 两个哈希表，ht[1] 用于 rehash
    long rehashidx;         // rehash 进度，-1 表示未进行
    unsigned long iterators;
} dict;
```

Redis 使用两个哈希表 `ht[0]` 和 `ht[1]` 来实现渐进式 rehash。正常情况下只使用 `ht[0]`，当需要扩容/缩容时，`ht[1]` 被分配新空间，数据逐步从 `ht[0]` 迁移到 `ht[1]`。

### 3.2 哈希算法

```c
// dict.c
unsigned int dictHashKey(const dict *d, const void *key) {
    return d->type->hashFunction(key);
}

// Redis 默认使用 SipHash 算法
uint64_t siphash(const uint8_t *in, const size_t inlen, const uint8_t *k) {
    // SipHash 2-4 实现...
    // 提供 DOS 攻击防护，避免哈希碰撞攻击
}
```

Redis 使用 SipHash 算法（Redis 4.0 之前使用 MurmurHash2），它能有效防止哈希碰撞攻击。桶位置的计算非常简洁：

```c
h = dictHashKey(d, key);
index = h & d->ht[table].sizemask;  // 位运算替代取模，要求 size 是 2 的幂
```

### 3.3 渐进式 Rehash

rehash 的触发条件：
- **扩容**：负载因子 `used / size >= 1`（且没有 BGSAVE/AOF 重写在执行），或 `>= 5`（有子进程时强制扩容）
- **缩容**：负载因子 < 0.1

```c
int dictRehash(dict *d, int n) {
    int empty_visits = n * 10; /* 最多访问的空桶数 */
    if (!dictIsRehashing(d)) return 0;

    while (n-- && d->ht[0].used != 0) {
        dictEntry *de, *nextde;

        /* 跳过空桶 */
        while (d->ht[0].table[d->rehashidx] == NULL) {
            d->rehashidx++;
            if (--empty_visits == 0) return 1;
        }
        de = d->ht[0].table[d->rehashidx];
        /* 将整个桶的链表迁移到 ht[1] */
        while (de) {
            uint64_t h;
            nextde = de->next;
            /* 重新计算在新表中的位置 */
            h = dictHashKey(d, de->key) & d->ht[1].sizemask;
            de->next = d->ht[1].table[h];
            d->ht[1].table[h] = de;  // 头插法
            d->ht[0].used--;
            d->ht[1].used++;
            de = nextde;
        }
        d->ht[0].table[d->rehashidx] = NULL;
        d->rehashidx++;
    }

    /* 检查是否完成 rehash */
    if (d->ht[0].used == 0) {
        zfree(d->ht[0].table);
        d->ht[0] = d->ht[1];  // 用 ht[1] 替换 ht[0]
        _dictReset(&d->ht[1]);
        d->rehashidx = -1;
        return 0;  /* 已完成 */
    }
    return 1;  /* 未完成 */
}
```

渐进式 rehash 的调度时机：

```c
// server.c - 每次 CRUD 操作时触发
static void _dictRehashStep(dict *d) {
    if (d->iterators == 0) dictRehash(d, 1);
}

// server.c - 定时任务中触发
void incrementallyRehash(int dbid) {
    if (dictIsRehashing(server.db[dbid].dict)) {
        dictRehashMilliseconds(server.db[dbid].dict, 1);
    }
}
```

每次字典的增删改查操作会迁移 1 个桶，定时任务每次最多执行 1ms 的 rehash。这种设计保证了 rehash 不会阻塞服务，同时能在合理时间内完成。

### 3.4 在 rehash 期间的读写操作

在 rehash 期间，写操作会同时操作两个表：

```c
dictEntry *dictAddRaw(dict *d, void *key, dictEntry **existing) {
    int index;
    dictEntry *entry;
    dictht *ht;

    if (dictIsRehashing(d)) _dictRehashStep(d);

    if ((index = _dictKeyIndex(d, key, dictHashKey(d,key), existing)) == -1)
        return NULL;

    /* 如果正在 rehash，新节点放入 ht[1] */
    ht = dictIsRehashing(d) ? &d->ht[1] : &d->ht[0];
    entry = zmalloc(sizeof(*entry));
    entry->next = ht->table[index];
    ht->table[index] = entry;
    ht->used++;

    entry->key = key;
    return entry;
}
```

查找操作需要先查 `ht[0]`，没找到再查 `ht[1]`：

```c
dictEntry *dictFind(dict *d, const void *key) {
    dictEntry *he;
    uint64_t h, idx, table;

    if (dictSize(d) == 0) return NULL;

    if (dictIsRehashing(d)) _dictRehashStep(d);

    h = dictHashKey(d, key);
    for (table = 0; table <= 1; table++) {
        idx = h & d->ht[table].sizemask;
        he = d->ht[table].table[idx];
        while (he) {
            if (key == he->key || dictCompareKeys(d, key, he->key))
                return he;
            he = he->next;
        }
        if (!dictIsRehashing(d)) return NULL;
    }
    return NULL;
}
```

---

## 4. SkipList 跳表源码解析

### 4.1 跳表数据结构

跳表是 ZSet（有序集合）的底层实现之一，提供了 O(log n) 的查找和范围操作能力。

```c
// server.h
typedef struct zskiplistNode {
    sds ele;                            // 成员值
    double score;                       // 分值
    struct zskiplistNode *backward;     // 后退指针
    struct zskiplistLevel {
        struct zskiplistNode *forward;  // 前进指针
        unsigned long span;             // 跨度（用于计算 rank）
    } level[];                          // 柔性数组，层数动态
} zskiplistNode;

typedef struct zskiplist {
    struct zskiplistNode *header, *tail;
    unsigned long length;               // 节点数量
    int level;                          // 当前最大层数
} zskiplist;
```

`span`（跨度）是跳表设计的精髓之一，它记录了当前节点到下一个节点之间跨越了多少个节点，利用 span 可以在 O(log n) 时间内计算出某个节点的排名。

### 4.2 随机层数生成

```c
// t_zset.c
#define ZSKIPLIST_MAXLEVEL 32
#define ZSKIPLIST_P 0.25

int zslRandomLevel(void) {
    int level = 1;
    while ((random() & 0xFFFF) < (ZSKIPLIST_P * 0xFFFF))
        level += 1;
    return (level < ZSKIPLIST_MAXLEVEL) ? level : ZSKIPLIST_MAXLEVEL;
}
```

每次有 25% 的概率增加一层。这种概率模型保证了：
- 约 75% 的节点是 1 层
- 约 18.75% 的节点是 2 层
- 平均每个节点约 1.33 层

### 4.3 插入节点

```c
zskiplistNode *zslInsert(zskiplist *zsl, double score, sds ele) {
    zskiplistNode *update[ZSKIPLIST_MAXLEVEL], *x;
    unsigned int rank[ZSKIPLIST_MAXLEVEL];
    int i, level;

    x = zsl->header;
    // 从最高层向下查找插入位置
    for (i = zsl->level - 1; i >= 0; i--) {
        rank[i] = i == (zsl->level-1) ? 0 : rank[i+1];
        while (x->level[i].forward &&
            (x->level[i].forward->score < score ||
             (x->level[i].forward->score == score &&
              sdscmp(x->level[i].forward->ele, ele) < 0))) {
            rank[i] += x->level[i].span;
            x = x->level[i].forward;
        }
        update[i] = x;  // 记录每层的前驱节点
    }

    level = zslRandomLevel();
    if (level > zsl->level) {
        for (i = zsl->level; i < level; i++) {
            rank[i] = 0;
            update[i] = zsl->header;
            update[i]->level[i].span = zsl->length;
        }
        zsl->level = level;
    }

    x = zslCreateNode(level, score, ele);
    // 逐层插入节点并更新 span
    for (i = 0; i < level; i++) {
        x->level[i].forward = update[i]->level[i].forward;
        update[i]->level[i].forward = x;
        // span 更新
        x->level[i].span = update[i]->level[i].span - (rank[0] - rank[i]);
        update[i]->level[i].span = (rank[0] - rank[i]) + 1;
    }

    // 未触及的层 span + 1
    for (i = level; i < zsl->level; i++) {
        update[i]->level[i].span++;
    }

    // 设置后退指针
    x->backward = (update[0] == zsl->header) ? NULL : update[0];
    if (x->level[0].forward)
        x->level[0].forward->backward = x;
    else
        zsl->tail = x;

    zsl->length++;
    return x;
}
```

`rank` 数组记录了每层搜索路径上前驱节点的排名，通过 `rank[0] - rank[i]` 可以精确计算出 span 值。

---

## 5. ZipList 压缩列表源码解析

### 5.1 ZipList 结构

ZipList 是为了节省内存而设计的紧凑型双向列表，所有数据连续存储在一块内存中。

```
┌─────────┬─────────┬────────┬──────────────┬──────────────┬─────┬────────┐
│ zlbytes │ zltail  │ zllen  │ entry1       │ entry2       │ ... │ zlend  │
│ 4 bytes │ 4 bytes │ 2 bytes│              │              │     │ 1 byte │
└─────────┴─────────┴────────┴──────────────┴──────────────┴─────┴────────┘
```

每个 entry 的结构：

```
┌───────────────────┬───────────┬─────────┐
│ prevrawlen        │ encoding  │ data    │
│ 1 or 5 bytes      │ 1~5 bytes │ N bytes │
└───────────────────┴───────────┴─────────┘
```

`prevrawlen` 记录前一个 entry 的长度：如果 < 254 字节用 1 字节存储，否则用 5 字节（第一个字节为 0xFE，后 4 字节为实际长度）。这个设计支持从尾部向头部遍历。

### 5.2 连锁更新问题

当插入或删除元素时，可能导致 `prevrawlen` 从 1 字节变为 5 字节（或反向），进而引起后续所有 entry 的级联扩展/收缩，最坏情况 O(n²)：

```c
unsigned char *__ziplistInsert(unsigned char *zl, unsigned char *p,
                               unsigned char *s, unsigned int slen) {
    size_t curlen = intrev32ifbe(ZIPLIST_BYTES(zl)), reqlen;
    unsigned int prevlensize, prevlen = 0;
    size_t offset;
    int nextdiff = 0;
    unsigned char encoding = 0, *tail;
    zlentry entry;

    // ... 计算 prevlen、encoding、reqlen ...

    /* 检查是否需要扩展后续 entry 的 prevrawlen */
    nextdiff = (p[0] != ZIP_END) ? zipStorePrevEntryLengthLarge(p + 0, reqlen) - prevlensize : 0;

    // 扩容并移动数据
    offset = p - zl;
    zl = ziplistResize(zl, curlen + reqlen + nextdiff);
    p = zl + offset;

    if (p[0] != ZIP_END) {
        // 移动后续数据
        memmove(p + reqlen, p - nextdiff, curlen - offset - 1 + nextdiff);
        // 更新下一个 entry 的 prevrawlen
        zipStorePrevEntryLength(p + reqlen, reqlen);
        // 连锁更新检查
        if (nextdiff != 0) {
            zl = __ziplistCascadeUpdate(zl, p + reqlen);
        }
    }
    // ... 写入数据、更新 header ...
    return zl;
}
```

```c
unsigned char *__ziplistCascadeUpdate(unsigned char *zl, unsigned char *p) {
    while (p[0] != ZIP_END) {
        zipEntry(p, &cur);
        rawlen = ... // 当前 entry 编码后的总长度
        
        if (p[rawlen] == ZIP_END) break; // 到达尾部
        
        zipEntry(p + rawlen, &next);
        
        if (next.prevrawlensize < required_size) {
            // 需要扩展，可能引起连锁反应
            extra = required_size - next.prevrawlensize;
            // 重新分配内存，移动数据
            // ...
        }
        p += rawlen;
    }
    return zl;
}
```

由于连锁更新的存在，Redis 7.0 引入了 `listpack` 来替代 ziplist 作为 Hash 和 ZSet 的小数据量编码方式，listpack 不存储 prevrawlen，从而彻底解决了连锁更新问题。

---

## 6. QuickList 快速列表源码解析

QuickList 是 List 的底层实现，它是 ZipList 和双向链表的结合体：

```
QuickList:
  head ──► [node1] ◄──► [node2] ◄──► [node3] ◄──► ... ◄──► tail
              │            │            │
           ziplist      ziplist      ziplist
          [a,b,c]     [d,e,f]     [g,h,i]
```

```c
// quicklist.h
typedef struct quicklistNode {
    struct quicklistNode *prev;
    struct quicklistNode *next;
    unsigned char *entry;       // 指向 ziplist/listpack
    size_t sz;                  // entry 占用字节数
    unsigned int count : 16;    // entry 中元素数量
    unsigned int encoding : 2;  // 1=ziplist, 2=listpack
    unsigned int container : 2; // 1=plain node, 2=packed
    unsigned int recompress : 1;
    unsigned int attempted_compress : 1;
    unsigned int extra : 10;
    unsigned int compressed_size : 28; // 压缩后大小
} quicklistNode;

typedef struct quicklist {
    quicklistNode *head;
    quicklistNode *tail;
    unsigned long count;        // 所有节点中元素总数
    unsigned long len;          // quicklistNode 数量
    int fill : QL_FILL_BITS;    // 单节点最大大小
    unsigned int compress : QL_COMP_BITS; // 两端不压缩的节点数
    unsigned int bookmark_count: QL_BM_BITS;
} quicklist;
```

`fill` 参数控制单个 ziplist 的大小，可以是正数（元素数量上限）或负数（字节数上限）。`compress` 参数控制两端保留不压缩的节点数，中间节点可以用 LZF 压缩。

---

## 7. IntSet 整数集合源码解析

当 Set 全部为整数且数量不超过 512 时，使用 IntSet 作为底层实现：

```c
// intset.h
typedef struct intset {
    uint32_t encoding;  // INTSET_ENC_INT16/32/64
    uint32_t length;    // 元素数量
    int8_t contents[];  // 柔性数组，按 encoding 存储
} intset;
```

IntSet 始终保持有序，查找使用二分法 O(log n)。当插入更大类型的整数时，整个数组需要升级：

```c
intset *intsetAdd(intset *is, int64_t val, uint8_t *success) {
    uint8_t valenc = _intsetValueEncoding(val);
    uint32_t pos;
    if (success) *success = 1;

    /* 如果值编码超出当前编码，需要升级 */
    if (valenc > intrev32ifbe(is->encoding)) {
        return intsetUpgradeAndAdd(is, val);
    }

    /* 二分查找插入位置 */
    if (intsetSearch(is, val, &pos)) {
        if (success) *success = 0;  // 已存在
        return is;
    }

    /* 扩容并移动元素 */
    is = intsetResize(is, intrev32ifbe(is->length) + 1);
    if (pos < intrev32ifbe(is->length))
        memmove(((int8_t*)is->contents) + pos * valenc_size,
                ((int8_t*)is->contents) + pos * cur_enc_size,
                (intrev32ifbe(is->length) - pos) * cur_enc_size);
    _intsetSet(is, pos, val);
    is->length = intrev32ifbe(intrev32ifbe(is->length) + 1);
    return is;
}
```

编码升级是单向的，只升不降。即使删除了大整数，编码也不会降级。

---

## 8. 事件驱动模型 Reactor 模式

### 8.1 事件循环核心

Redis 实现了自己的事件库 `ae.c`，核心是 Reactor 模式：

```c
// ae.h
typedef struct aeEventLoop {
    int maxfd;
    int setsize;
    long long timeEventNextId;
    aeFileEvent *events;        /* 注册的事件 */
    aeFiredEvent *fired;        /* 就绪的事件 */
    aeTimeEvent *timeEventHead; // 时间事件链表
    int stop;
    void *apidata;              // epoll/kqueue/select 的数据
    aeBeforeSleepProc *beforesleep;
    aeBeforeSleepProc *aftersleep;
} aeEventLoop;
```

事件循环主体：

```c
// ae.c
void aeMain(aeEventLoop *eventLoop) {
    eventLoop->stop = 0;
    while (!eventLoop->stop) {
        aeProcessEvents(eventLoop, AE_ALL_EVENTS|AE_CALL_BEFORE_SLEEP|
                                   AE_CALL_AFTER_SLEEP);
    }
}

int aeProcessEvents(aeEventLoop *eventLoop, int flags) {
    int processed = 0, numevents;

    /* 如果没有文件事件，不计算最近时间事件 */
    if (!(flags & AE_TIME_EVENTS) && !(flags & AE_FILE_EVENTS)) return 0;

    if (eventLoop->maxfd != -1 ||
        ((flags & AE_TIME_EVENTS) && !(flags & AE_DONT_WAIT))) {
        int j;
        struct timeval tv, *tvp;
        tvp = aeSearchNearestTimer(eventLoop); // 找最近时间事件

        /* beforesleep 回调：在 epoll_wait 之前处理待写数据 */
        if (eventLoop->beforesleep != NULL && flags & AE_CALL_BEFORE_SLEEP)
            eventLoop->beforesleep(eventLoop);

        /* 调用 epoll_wait 等待事件 */
        numevents = aeApiPoll(eventLoop, tvp);

        /* aftersleep 回调 */
        if (eventLoop->aftersleep != NULL && flags & AE_CALL_AFTER_SLEEP)
            eventLoop->aftersleep(eventLoop);

        /* 处理就绪事件 */
        for (j = 0; j < numevents; j++) {
            aeFileEvent *fe = &eventLoop->events[eventLoop->fired[j].fd];
            int mask = eventLoop->fired[j].mask;
            int fd = eventLoop->fired[j].fd;
            int fired = 0;

            // 先读后写
            if (fe->mask & mask & AE_READABLE) {
                fe->rfileProc(eventLoop, fd, fe->clientData, mask);
                fired++;
            }
            if (fe->mask & mask & AE_WRITABLE) {
                if (!fired || fe->wfileProc != fe->rfileProc) {
                    fe->wfileProc(eventLoop, fd, fe->clientData, mask);
                    fired++;
                }
            }
            processed++;
        }
    }

    /* 处理时间事件 */
    if (flags & AE_TIME_EVENTS)
        processed += processTimeEvents(eventLoop);

    return processed;
}
```

### 8.2 I/O 多路复用封装

Redis 对不同平台的 I/O 多路复用做了统一封装：

```c
// ae_epoll.c (Linux)
static int aeApiPoll(aeEventLoop *eventLoop, struct timeval *tvp) {
    aeApiState *state = eventLoop->apidata;
    int retval, numevents = 0;

    retval = epoll_wait(state->epfd, state->events, eventLoop->setsize,
                        tvp ? (tvp->tv_sec*1000 + tvp->tv_usec/1000) : -1);
    if (retval > 0) {
        int j;
        for (j = 0; j < retval; j++) {
            int mask = 0;
            struct epoll_event *e = state->events + j;
            if (e->events & EPOLLIN)  mask |= AE_READABLE;
            if (e->events & EPOLLOUT) mask |= AE_WRITABLE;
            if (e->events & EPOLLERR) mask |= AE_WRITABLE;
            if (e->events & EPOLLHUP) mask |= AE_WRITABLE;
            eventLoop->fired[j].fd = e->data.fd;
            eventLoop->fired[j].mask = mask;
        }
        numevents = retval;
    }
    return numevents;
}
```

### 8.3 文件事件处理流程

```c
// networking.c
void readQueryFromClient(aeEventLoop *el, int fd, void *privdata, int mask) {
    client *c = (client*) privdata;
    int nread, readlen;
    readlen = PROTO_IOBUF_LEN;
    // ...
    nread = connRead(c->conn, c->querybuf+qblen, readlen);
    // ...
    sdsIncrLen(c->querybuf, nread);
    c->lastinteraction = server.unixtime;
    
    // 解析并执行命令
    if (processInputBuffer(c) == C_ERR) return;
}

int processInputBuffer(client *c) {
    while (c->qb_pos < sdslen(c->querybuf)) {
        // 解析 RESP 协议
        if (c->reqtype == PROTO_REQ_INLINE) {
            if (processInlineBuffer(c) != C_OK) break;
        } else if (c->reqtype == PROTO_REQ_MULTIBULK) {
            if (processMultibulkBuffer(c) != C_OK) break;
        }
        // 执行命令
        if (processCommand(c) == C_ERR) return C_ERR;
    }
    return C_OK;
}
```

---

## 9. Redis 6.0 多线程 I/O 模型

Redis 6.0 引入了多线程 I/O，但**命令执行仍然单线程**。多线程仅用于网络读写：

```
主线程:  epoll_wait → 分配任务 → 执行命令 → 分配写任务
              ↓                              ↓
I/O线程1: 读取客户端数据        写回响应给客户端
I/O线程2: 读取客户端数据        写回响应给客户端
I/O线程3: 读取客户端数据        写回响应给客户端
```

```c
// networking.c
int handleClientsWithPendingReadsUsingThreads(void) {
    if (!server.io_threads_active) return 0;
    
    int processed = listLength(server.clients_pending_read);
    if (processed == 0) return 0;

    // 轮询分配任务给 I/O 线程
    listIter li;
    listNode *ln;
    listRewind(server.clients_pending_read, &li);
    int item_id = 0;
    while ((ln = listNext(&li))) {
        client *c = listNodeValue(ln);
        int target_id = item_id % server.io_threads_num;
        listAddNodeTail(io_threads_list[target_id], c);
        item_id++;
    }

    // 设置各线程的任务量并等待完成
    io_threads_op = IO_THREADS_OP_READ;
    for (int j = 1; j < server.io_threads_num; j++) {
        int count = listLength(io_threads_list[j]);
        setIOPthreadCount(j, count);
    }
    // 主线程也处理一部分
    while (listLength(io_threads_list[0])) {
        // 读取数据并解析...
    }
    
    // 等待所有 I/O 线程完成
    while (1) {
        unsigned long pending = 0;
        for (int j = 1; j < server.io_threads_num; j++)
            pending += getIOPendingCount(j);
        if (pending == 0) break;
    }
    
    // 命令在主线程执行
    while ((ln = listNext(&li))) {
        client *c = listNodeValue(ln);
        if (c->querybuf) {
            processInputBuffer(c);
        }
    }
    return processed;
}
```

I/O 线程的工作函数：

```c
void *IOThreadMain(void *myid) {
    long id = (unsigned long)myid;
    while (1) {
        // 等待任务
        while (1) {
            if (getIOPendingCount(id) != 0) break;
        }
        
        int op = io_threads_op;
        list *list = io_threads_list[id];
        
        if (op == IO_THREADS_OP_READ) {
            // 读取客户端数据
            while ((ln = listNext(&li))) {
                client *c = listNodeValue(ln);
                readQueryFromClient(NULL, c->conn->fd, c, 0);
            }
        } else if (op == IO_THREADS_OP_WRITE) {
            // 写回响应
            while ((ln = listNext(&li))) {
                client *c = listNodeValue(ln);
                writeToClient(c->fd, c, 0);
            }
        }
        setIOPthreadCount(id, 0); // 标记完成
    }
}
```

这种设计的巧妙之处在于：
- **命令执行仍然串行**，无需考虑并发安全
- 网络读写是 CPU 密集型操作（序列化/反序列化），多线程可以显著提升吞吐
- 通过轮询分配实现负载均衡

---

## 10. 面试题速查

### Q1: Redis 为什么快？
1. 基于内存操作，数据存取速度极快
2. 单线程模型避免锁竞争和上下文切换
3. I/O 多路复用 + 事件驱动，高效处理并发连接
4. 自研高效数据结构（SDS O(1) 取长度、跳表 O(log n) 等）
5. 6.0 多线程 I/O 提升网络吞吐

### Q2: SDS 和 C 字符串有什么区别？
- SDS O(1) 获取长度，C 字符串 O(n)
- SDS 二进制安全，C 字符串不安全
- SDS 自动扩容 + 预分配策略，减少内存分配次数
- SDS 兼容 C 字符串函数（末尾有 `\0`）
- SDS 有 5 种头部类型，根据长度自动选择最省内存的

### Q3: 渐进式 Rehash 的过程是什么？
1. 分配 `ht[1]` 空间，`rehashidx` 设为 0
2. 每次 CRUD 操作迁移 1 个桶，定时任务每次最多 1ms
3. rehash 期间新数据写入 `ht[1]`，查找先查 `ht[0]` 再查 `ht[1]`
4. `ht[0]` 全部迁移完成后，`ht[1]` 变为 `ht[0]`，rehash 结束

### Q4: 跳表的 span 有什么用？
span 记录节点间的跨度，通过累加 span 可以在 O(log n) 时间内计算节点的排名（rank），这是 ZRANK/ZREVRANK 命令高效实现的基础。

### Q5: ZipList 的连锁更新是什么？如何解决？
当中间节点数据变化导致 `prevrawlen` 从 1 字节扩展到 5 字节时，后续节点级联更新，最坏 O(n²)。Redis 7.0 引入 listpack 替代 ziplist，listpack 不存储前驱长度，彻底消除连锁更新。

### Q6: Redis 6.0 多线程 I/O 模型是怎样的？
- 仅网络读写使用多线程，命令执行仍然单线程
- 主线程通过轮询将客户端分配给 I/O 线程
- 读阶段：I/O 线程读取数据，主线程解析并执行命令
- 写阶段：I/O 线程将响应写回客户端
- 无需加锁，因为命令执行是串行的

### Q7: Dict 的负载因子什么时候触发扩容？
- 没有子进程（BGSAVE/AOF rewrite）时，负载因子 ≥ 1 触发扩容
- 有子进程时，负载因子 ≥ 5 强制扩容（避免写时复制期间过多内存操作）
- 负载因子 < 0.1 触发缩容

### Q8: Redis 事件循环中 beforesleep 做了什么？
beforesleep 在 `epoll_wait` 之前调用，主要处理：
- 将 AOF 缓冲区写入文件
- 处理待写客户端的响应数据
- 如果开启了 lazy free，执行异步释放
- 刷写部分数据到磁盘

### Q9: QuickList 为什么不在每个节点存一个大 ziplist？
单个 ziplist 过大会导致：
- 插入/删除的内存拷贝开销大
- 连锁更新影响范围大
- 不利于 LZF 压缩
Redis 通过 `fill` 参数限制单个 ziplist 大小（默认 8KB），在内存利用率和操作效率之间取得平衡。

### Q10: Redis 为什么不直接用 libevent/libev？
antirez 认为 libevent 过于庞大且效率不高，自研 ae.c 更轻量（约 300 行），可以针对不同平台做最优适配，且没有额外依赖。Redis 只需要 I/O 多路复用 + 定时器，不需要 libevent 的高级功能。

---

> **总结**：Redis 源码的精妙之处在于每个数据结构都针对特定场景做了极致优化。SDS 兼顾安全与性能，Dict 的渐进式 rehash 平衡了扩容与可用性，跳表的 span 设计巧妙解决了排名问题，事件驱动的单线程模型在简洁与性能之间找到了最佳平衡点。理解这些源码级设计，是深入掌握 Redis 的必经之路。

# Redis Cluster 集群源码深度解析

> "Redis Cluster 是 Redis 官方提供的分布式方案，它通过一致性哈希槽（Slot）分区、Gossip 协议通信、自动故障转移，将 Redis 从单机 KV 存储提升为去中心化的分布式缓存系统。" —— 深入源码，你会发现其设计在简洁与健壮之间取得了精妙的平衡。

---

## 📋 目录

1. [集群架构总览](#1-集群架构总览)
2. [核心数据结构](#2-核心数据结构)
3. [哈希槽路由机制](#3-哈希槽路由机制)
4. [Gossip 协议实现](#4-gossip-协议实现)
5. [节点握手与加入集群](#5-节点握手与加入集群)
6. [槽位分配与迁移](#6-槽位分配与迁移)
7. [MOVED 与 ASK 重定向](#7-moved-与-ask-重定向)
8. [故障检测机制](#8-故障检测机制)
9. [故障转移与选主](#9-故障转移与选主)
10. [集群更新与配置传播](#10-集群更新与配置传播)
11. [面试题速查](#11-面试题速查)

---

## 1. 集群架构总览

Redis Cluster 采用 **去中心化** 架构，没有中心节点，所有节点通过 Gossip 协议互相通信。整个集群被划分为 16384 个哈希槽（Slot），每个节点负责一部分槽位。

```
┌──────────────────────────────────────────────────────────┐
│                    Redis Cluster                         │
│                                                          │
│  ┌──────────┐  Gossip  ┌──────────┐  Gossip  ┌──────────┐│
│  │ Node A   │◄────────►│ Node B   │◄────────►│ Node C   ││
│  │ Slots:   │          │ Slots:   │          │ Slots:   ││
│  │ 0-5460   │          │ 5461-10922│         │10923-16383││
│  │ (Master) │          │ (Master) │          │ (Master) ││
│  └────┬─────┘          └────┬─────┘          └────┬─────┘│
│       │                     │                     │      │
│  ┌────┴─────┐          ┌────┴─────┐          ┌────┴─────┐│
│  │ Node A'  │          │ Node B'  │          │ Node C'  ││
│  │ (Replica)│          │ (Replica)│          │ (Replica)││
│  └──────────┘          └──────────┘          └──────────┘│
└──────────────────────────────────────────────────────────┘
```

核心特征：
- **去中心化**：每个节点都持有完整的集群路由表
- **数据分片**：16384 个槽位，通过 CRC16 算法计算键的归属
- **高可用**：每个 Master 可以有多个 Replica，Master 宕机自动提升 Replica
- **最终一致性**：集群状态通过 Gossip 协议逐步收敛

## 2. 核心数据结构

### 2.1 clusterNode —— 节点信息

```c
// cluster.h
typedef struct clusterNode {
    mstime_t ctime;            // 节点创建时间

    char name[CLUSTER_NAMELEN]; // 节点名称（40字符十六进制）
    int flags;                  // 节点状态标志（MASTER/SLAVE/PFAIL/FAIL等）

    uint64_t configEpoch;       // 配置纪元（用于冲突解决）
    uint64_t lastVoteEpoch;     // 最后一次投票的纪元

    char slaveof[CLUSTER_NAMELEN]; // 如果是从节点，记录主节点名称

    int numslots;               // 该节点负责的槽数量
    unsigned char slots[CLUSTER_SLOTS / 8]; // 槽位位图（16384位=2048字节）

    int numslaves;              // 从节点数量
    struct clusterNode **slaves; // 从节点列表

    mstime_t ping_sent;         // 最后发送 PING 的时间
    mstime_t pong_received;     // 最后收到 PONG 的时间
    mstime_t data_received;     // 最后收到数据的时间

    mstime_t fail_time;         // 被标记为 FAIL 的时间

    mstime_t voted;             // 该节点投票的时间
    int port;                   // 节点端口
    int pport;                  // TLS 端口（可选）
    char *hostname;             // 主机名
    clusterLink *link;          // 与该节点的连接
    list *fail_reports;         // 其他节点对该节点的故障报告
} clusterNode;
```

`slots` 位图是路由的核心——每个 bit 对应一个槽位，1 表示该节点负责此槽位。16384 个槽只需要 2048 字节。

### 2.2 clusterState —— 本地集群状态

```c
typedef struct clusterState {
    clusterNode *myself;        // 当前节点自身
    uint64_t currentEpoch;      // 当前纪元

    int state;                  // CLUSTER_OK 或 CLUSTER_FAIL
    int size;                   // 已知的主节点数量

    dict *nodes;                // 所有节点的字典（name -> clusterNode）
    dict *nodes_black_list;     // 黑名单

    clusterNode *migrating_slots_to[CLUSTER_SLOTS];     // 槽位正在迁移到的目标节点
    clusterNode *importing_slots_from[CLUSTER_SLOTS];   // 槽位正在从哪个节点导入
    clusterNode *slots[CLUSTER_SLOTS];                  // 每个槽位归属的节点（快速查找）

    // 手动故障转移相关
    mstime_t mf_can_start;
    mstime_t mf_master_repl_offset;
    char mf_master_name[CLUSTER_NAMELEN];
    int mf_can_start_flag;
} clusterState;
```

`slots` 数组是 O(1) 查找的关键——给定槽号，直接索引到负责该槽的节点。与 `clusterNode.slots` 位图互为反向索引。

### 2.3 clusterLink —— 节点间连接

```c
typedef struct clusterLink {
    mstime_t ctime;
    connection *conn;           // TCP 连接
    sds sndbuf;                 // 发送缓冲区
    sds rcvbuf;                 // 接收缓冲区
    clusterNode *node;          // 关联的节点
    mstime_t last_activity_time;
} clusterLink;
```

每个节点对之间维护一条 TCP 长连接，用于 Gossip 消息交换。发送和接收使用独立的缓冲区。

## 3. 哈希槽路由机制

### 3.1 键到槽的映射

```c
// cluster.c
unsigned int keyHashSlot(char *key, int keylen) {
    int s, e;

    // 检查是否使用 Hash Tag
    for (s = 0; s < keylen; s++)
        if (key[s] == '{') break;

    if (s == keylen) return crc16(key, keylen) & 16383;

    // 查找匹配的 }
    for (e = s + 1; e < keylen; e++)
        if (key[e] == '}') break;

    // 没有 }，对整个 key 做 hash
    if (e == keylen || e == s + 1) return crc16(key, keylen) & 16383;

    // 只对 { 和 } 之间的内容做 hash
    return crc16(key + s + 1, e - s - 1) & 16383;
}
```

**Hash Tag** 机制允许用户将多个键映射到同一个槽位。例如 `user:{1000}.name` 和 `user:{1000}.email` 都会计算 `1000` 的 CRC16，保证落在同一个节点上，从而支持跨键操作（MGET、事务、Lua 脚本等）。

### 3.2 为什么是 16384 个槽？

Redis 作者 antirez 在 GitHub issue 中解释了这个问题：

1. **心跳消息大小**：每个节点在 Gossip 消息中携带自己负责的槽位位图。16384 位 = 2048 字节。如果用 65536 个槽，则每条消息的位图就需要 8KB，对于 Gossip 这种频繁发送的消息来说是很大开销。
2. **集群规模**：Redis Cluster 建议最大 1000 个节点。16384 个槽分配给 1000 个节点，每个节点约 16 个槽，足够用。65536 个槽纯属浪费。
3. **位图压缩**：消息中还会携带 `slots_info` 的压缩信息，16384 的压缩效果很好。

## 4. Gossip 协议实现

### 4.1 消息类型

```c
#define CLUSTERMSG_TYPE_PING 0          // 心跳检测
#define CLUSTERMSG_TYPE_PONG 1          // PING 响应
#define CLUSTERMSG_TYPE_MEET 2          // 节点加入
#define CLUSTERMSG_TYPE_FAIL 3          // 通知节点故障
#define CLUSTERMSG_TYPE_PUBLISH 4       // 发布订阅传播
#define CLUSTERMSG_TYPE_FAILOVER_AUTH_REQUEST 5  // 故障转移投票请求
#define CLUSTERMSG_TYPE_FAILOVER_AUTH_ACK 6      // 故障转移投票确认
#define CLUSTERMSG_TYPE_UPDATE 7        // 槽位配置更新
#define CLUSTERMSG_TYPE_MFSTART 8       // 手动故障转移开始
#define CLUSTERMSG_TYPE_MODULE 9        // 模块消息
#define CLUSTERMSG_TYPE_PUBLISHSHARD 10 // 分片发布
```

### 4.2 消息头结构

```c
typedef struct {
    char sig[4];                // "RCmb" 签名
    uint32_t totlen;            // 消息总长度
    uint16_t ver;               // 协议版本
    uint16_t port;              // 发送者端口
    uint16_t type;              // 消息类型
    uint16_t count;             // Gossip section 中携带的节点数
    uint64_t currentEpoch;      // 发送者的 currentEpoch
    uint64_t configEpoch;       // 发送者的 configEpoch
    uint64_t offset;            // 主节点的复制偏移量
    char sender[CLUSTER_NAMELEN]; // 发送者名称
    unsigned char myslots[CLUSTER_SLOTS/8]; // 发送者的槽位位图
    char slaveof[CLUSTER_NAMELEN];  // 如果是从节点，主节点名称
    char notused1[32];
    uint16_t cport;             // 集群总线端口
    uint16_t flags;             // 发送者状态标志
    unsigned char state;        // 发送者视角的集群状态
    unsigned char mflags[3];    // 消息级标志
} clusterMsg;
```

每次 PING/PONG 消息除了携带发送者自身信息，还会随机选取一部分已知节点信息放入 **Gossip Section**：

```c
typedef struct {
    char nodename[CLUSTER_NAMELEN];
    uint32_t ping_sent;
    uint32_t pong_received;
    char ip[NET_IP_STR_LEN];
    uint16_t port;
    uint16_t cport;
    uint16_t flags;
    uint16_t pport;
    char hostname[NET_HOSTNAME_LEN];
    // 不包含 slots 信息，减少消息体积
} clusterMsgDataGossip;
```

### 4.3 Gossip 传播策略

```c
// cluster.c - clusterCron 中每 100ms 执行
void clusterCron(void) {
    // ...
    di = dictGetSafeIterator(server.cluster->nodes);
    while((de = dictNext(di)) != NULL) {
        clusterNode *node = dictGetVal(de);
        // 选择需要发送 PING 的节点
        if (node->link && node->ping_sent == 0 &&
            time - node->ping_sent > server.cluster_node_timeout / 2) {
            // 发送 PING
            clusterSendPing(node->link, CLUSTERMSG_TYPE_PING);
        }
    }
}
```

Gossip 的核心逻辑：

1. **定时发送**：每个节点每隔 `cluster_node_timeout/2`（默认 7.5 秒）向部分节点发送 PING
2. **随机选取**：每次 PING 携带少量（默认最多 3 个）随机选取的节点信息
3. **增量更新**：收到 Gossip 信息后，更新本地节点字典
4. **收敛性**：经过 O(log N) 轮 Gossip，集群中所有节点最终看到一致的状态

### 4.4 PING 消息处理

```c
int clusterProcessPacket(clusterLink *link) {
    clusterMsg *hdr = (clusterMsg*) link->rcvbuf;
    uint16_t type = ntohs(hdr->type);

    // 1. 校验消息合法性
    if (!clusterSanityCheck(...)) return 0;

    // 2. 更新发送者信息
    clusterNode *sender = clusterLookupNode(hdr->sender);
    if (sender) {
        // 更新 configEpoch
        if (sender->configEpoch < ntohu64(hdr->configEpoch)) {
            sender->configEpoch = ntohu64(hdr->configEpoch);
            // 如果槽位归属有冲突，以更高的 configEpoch 为准
            clusterUpdateSlotsConfigWith(sender, ...);
        }
        sender->pong_received = now;
    }

    // 3. 处理 MEET 消息（新节点加入）
    if (type == CLUSTERMSG_TYPE_MEET) {
        if (!sender) {
            // 创建新节点并加入集群
            clusterNode *node = createClusterNode(hdr->sender, 0);
            clusterAddNode(node);
        }
    }

    // 4. 处理 PING/PONG：解析 Gossip Section
    if (type == CLUSTERMSG_TYPE_PING || type == CLUSTERMSG_TYPE_PONG) {
        for (int i = 0; i < count; i++) {
            clusterMsgDataGossip *g = &hdr->data.ping.gossip[i];
            // 更新本地节点信息
            clusterUpdateGossip(g);
        }
    }

    // 5. 如果是 PING，回复 PONG
    if (type == CLUSTERMSG_TYPE_PING) {
        clusterSendPing(link, CLUSTERMSG_TYPE_PONG);
    }

    // 6. 处理 FAIL 消息
    if (type == CLUSTERMSG_TYPE_FAIL) {
        clusterNode *failing = clusterLookupNode(hdr->data.fail.about.nodename);
        if (failing && !(failing->flags & CLUSTER_NODE_FAIL)) {
            failing->flags |= CLUSTER_NODE_FAIL;
            failing->fail_time = now;
            // 传播 FAIL 消息
            clusterSendFail(failing->name);
            // 触发故障转移
            clusterFailoverIfNeeded();
        }
    }

    return 1;
}
```

## 5. 节点握手与加入集群

### 5.1 MEET 命令

```c
// clusterCommand 处理 CLUSTER MEET
void clusterCommand(client *c) {
    if (!strcasecmp(c->argv[1]->ptr, "meet")) {
        char *ip = c->argv[2]->ptr;
        int port = atoi(c->argv[3]->ptr);
        int cport = port + 10000; // 集群总线端口

        // 查找或创建目标节点
        clusterNode *node = clusterLookupNodeByIp(ip);
        if (node == NULL) {
            node = createClusterNode(NULL, CLUSTER_NODE_HANDSHAKE);
            node->port = port;
            node->cport = cport;
            clusterAddNode(node);
        }

        // 发送 MEET 消息
        clusterSendPing(node->link, CLUSTERMSG_TYPE_MEET);

        addReply(c, shared.ok);
    }
}
```

### 5.2 加入流程

```
Node A              Node B (已在集群中)
  |                      |
  |--- CLUSTER MEET ---->|
  |                      |
  |<--- MEET msg --------| (B 通过 Gossip 通知其他节点 A 的存在)
  |                      |
  |---- PONG msg ------->|
  |                      |
  |<--- PING msg --------|
  |---- PONG msg ------->|
  |                      |
  |   A 通过 Gossip 逐步  |
  |   获知集群所有节点    |
  |                      |
```

新节点通过 MEET 加入后，需要等待一轮 Gossip 传播才能获知所有节点信息。新节点默认不负责任何槽位，需要通过 `CLUSTER SETSLOT` 手动分配或使用 `redis-cli --cluster reshard` 工具进行槽位迁移。

## 6. 槽位分配与迁移

### 6.1 槽位分配

```c
// CLUSTER ADDSLOTS
if (!strcasecmp(c->argv[1]->ptr, "addslots")) {
    for (int j = 2; j < c->argc; j++) {
        int slot = atoi(c->argv[j]->ptr);
        if (server.cluster->slots[slot] != NULL) {
            addReplyError(c, "Slot already busy");
            return;
        }
    }
    for (int j = 2; j < c->argc; j++) {
        int slot = atoi(c->argv[j]->ptr);
        clusterAddSlot(server.cluster->myself, slot);
    }
    clusterDoBeforeSleep(CLUSTER_TODO_UPDATE_STATE|CLUSTER_TODO_SAVE_CONFIG);
}
```

### 6.2 槽位迁移流程

```
源节点 A (Slot 100)          目标节点 B (Slot 100)
      |                            |
  CLUSTER SETSLOT 100 MIGRATING B
      |                            |
                                  CLUSTER SETSLOT 100 IMPORTING A
      |                            |
  MIGRATE 命令迁移 key ──────────>|
      |                            |
  迁移完成后:                      |
  CLUSTER SETSLOT 100 NODE B       |
      |                            |
  CLUSTER SETSLOT 100 NODE B (一致)
```

关键源码：

```c
// 处理客户端请求时检查槽位状态
int clusterRedirectClient(clusterNode *myself, ...) {
    int slot = keyHashSlot(key, keylen);

    if (server.cluster->migrating_slots_to[slot] != NULL) {
        // 正在迁出
        if (server.cluster->migrating_slots_to[slot] != myself) {
            // 键不存在，发送 ASK 重定向到目标节点
            if (lookupKeyRead(c->db, key) == NULL) {
                clusterRedirectClient(c, slot,
                    server.cluster->migrating_slots_to[slot],
                    CLUSTER_REDIR_ASK);
                return;
            }
        }
    }

    if (server.cluster->importing_slots_from[slot] != NULL) {
        // 正在导入，但不属于本节点正常处理范围
        // 只有收到 ASK 重定向的请求才处理
    }

    if (server.cluster->slots[slot] != myself) {
        // 不属于本节点，发送 MOVED 重定向
        clusterRedirectClient(c, slot,
            server.cluster->slots[slot],
            CLUSTER_REDIR_MOVED);
        return;
    }
}
```

## 7. MOVED 与 ASK 重定向

### 7.1 MOVED 重定向

```c
// cluster.c
void clusterRedirectClient(client *c, int slot, clusterNode *n, int redir) {
    if (redir == CLUSTER_REDIR_MOVED) {
        addReplyErrorFormat(c,
            "MOVED %d %s:%d", slot, n->ip, n->port);
    } else if (redir == CLUSTER_REDIR_ASK) {
        addReplyErrorFormat(c,
            "ASK %d %s:%d", slot, n->ip, n->port);
    }
}
```

**MOVED** 表示槽位已永久迁移到新节点，客户端应该更新本地路由表，后续请求直接发往新节点。

### 7.2 ASK 重定向

**ASK** 表示槽位正在迁移中，这是一个临时状态。客户端收到 ASK 后：
1. 临时打开 `ASKING` 标志
2. 向目标节点发送请求
3. 目标节点在 `ASKING` 标志下允许处理正在导入的槽位
4. 后续请求仍发往原节点（除非再次收到 ASK）

```c
// 客户端请求处理
int processCommand(client *c) {
    int slot = getNodeByQuery(...);

    if (slot == -1) return C_OK; // 无键命令

    clusterNode *n = server.cluster->slots[slot];

    if (n != myself) {
        // 不属于本节点
        if (c->flags & CLIENT_ASKING) {
            // 正在导入，允许处理
            return C_OK;
        }
        clusterRedirectClient(c, slot, n, CLUSTER_REDIR_MOVED);
        return C_ERR;
    }

    if (server.cluster->migrating_slots_to[slot] != NULL) {
        // 正在迁出
        if (c->cmd->proc != existsCommand &&
            lookupKeyRead(&server.db[0], ...) == NULL) {
            // 键不存在，说明已迁移走
            clusterRedirectClient(c, slot,
                server.cluster->migrating_slots_to[slot],
                CLUSTER_REDIR_ASK);
            return C_ERR;
        }
    }

    return C_OK;
}
```

### 7.3 MOVED vs ASK

| 特性 | MOVED | ASK |
|------|-------|-----|
| 场景 | 槽位已永久迁移 | 槽位正在迁移中 |
| 客户端行为 | 更新本地路由表 | 临时重定向，不更新路由表 |
| 后续请求 | 直接发往新节点 | 仍发往原节点 |
| 目标节点 | 正常处理 | 需要 ASKING 标志 |

## 8. 故障检测机制

### 8.1 PFAIL（疑似故障）

```c
// clusterCron 中每 100ms 执行
void clusterCron(void) {
    di = dictGetSafeIterator(server.cluster->nodes);
    while((de = dictNext(di)) != NULL) {
        clusterNode *node = dictGetVal(de);

        // 检查节点超时
        mstime_t now = mstime();
        if (node->flags & (CLUSTER_NODE_PFAIL|CLUSTER_NODE_FAIL)) continue;
        if (node->link && node->ping_sent != 0 &&
            (now - node->ping_sent) > server.cluster_node_timeout) {
            // 超时未收到 PONG
            node->flags |= CLUSTER_NODE_PFAIL; // 标记疑似故障
            // 记录故障报告
            clusterAddFailReport(node);
        }
    }
}
```

`cluster_node_timeout`（默认 15 秒）是核心超时参数。超过此时间未收到 PONG，节点被标记为 PFAIL。

### 8.2 故障报告传播

```c
void clusterAddFailReport(clusterNode *failing) {
    // 每个节点维护一个故障报告列表
    list *l = server.cluster->fail_reports;
    listNode *ln;
    listIter li;

    listRewind(l, &li);
    while ((ln = listNext(&li))) {
        clusterNodeFailReport *fr = listNodeValue(ln);
        if (fr->node == myself) {
            fr->time = mstime(); // 更新已有报告
            return;
        }
    }

    // 添加新报告
    clusterNodeFailReport *fr = zmalloc(sizeof(*fr));
    fr->node = myself;
    fr->time = mstime();
    listAddNodeTail(l, fr);
}
```

故障报告通过 Gossip PING/PONG 消息传播。当集群中 **过半数主节点** 都报告某节点 PFAIL 时，该节点被升级为 FAIL。

### 8.3 PFAIL 升级为 FAIL

```c
void clusterMarkNodeAsFailing(clusterNode *node) {
    int failures = 0;

    // 统计故障报告数
    if (node->flags & CLUSTER_NODE_MASTER) {
        // 需要过半数主节点确认
        int master_count = 0;
        dictIterator *di = dictGetIterator(server.cluster->nodes);
        dictEntry *de;
        while ((de = dictNext(di)) != NULL) {
            clusterNode *n = dictGetVal(de);
            if (n->flags & CLUSTER_NODE_MASTER) {
                master_count++;
                if (clusterNodeFailureReportsCount(n, node) > 0) {
                    failures++;
                }
            }
        }
        dictReleaseIterator(di);

        if (failures < master_count / 2) return; // 不足半数
    }

    // 升级为 FAIL
    node->flags &= ~CLUSTER_NODE_PFAIL;
    node->flags |= CLUSTER_NODE_FAIL;
    node->fail_time = mstime();

    // 广播 FAIL 消息
    clusterSendFail(node->name);

    // 触发故障转移
    clusterFailoverIfNeeded();
}
```

故障检测是一个 **两阶段确认** 过程：
1. **PFAIL**：单个节点通过超时检测，标记疑似故障
2. **FAIL**：过半数主节点确认 PFAIL，标记确认故障

## 9. 故障转移与选主

### 9.1 触发条件

```c
void clusterFailoverIfNeeded(void) {
    if (nodeIsMaster(myself)) return; // 不是从节点
    if (myself->slaveof == NULL) return; // 没有主节点

    clusterNode *master = myself->slaveof;

    // 主节点必须处于 FAIL 状态
    if (!(master->flags & CLUSTER_NODE_FAIL)) return;

    // 数据必须足够新（延迟不超过 10 倍超时）
    mstime_t data_age = now - myself->data_received;
    if (data_age > server.cluster_node_timeout * 10) return;

    // 等待一段时间，让其他从节点有机会参与竞选
    mstime_t auth_age = now - myself->fail_time;
    mstime_t auth_timeout = server.cluster_node_timeout * 2;
    if (auth_age < auth_timeout * (myself->slaves / 2)) return;

    // 发起选举
    clusterRequestFailoverAuth();
}
```

### 9.2 选举流程

```c
void clusterRequestFailoverAuth(void) {
    server.cluster->currentEpoch++;  // 增加纪元
    myself->lastVoteEpoch = server.cluster->currentEpoch;

    // 设置选举超时
    server.cluster->failover_auth_time =
        mstime() + random_retry_time; // 随机延迟避免冲突

    clusterSendFailoverAuthRequest(myself->name);
}
```

**Failever Auth Request** 广播到集群所有主节点：

```c
void clusterSendFailoverAuthRequest(char *name) {
    clusterMsg msg;
    msg.type = CLUSTERMSG_TYPE_FAILOVER_AUTH_REQUEST;
    msg.data.auth_request.nodename = name;
    clusterBroadcastMessage(&msg);
}
```

### 9.3 投票处理

```c
// 主节点收到投票请求
int clusterProcessPacket(clusterLink *link) {
    ...
    if (type == CLUSTERMSG_TYPE_FAILOVER_AUTH_REQUEST) {
        clusterSendFailoverAuthIfNeeded(sender, hdr);
    }
}

void clusterSendFailoverAuthIfNeeded(clusterNode *node, clusterMsg *request) {
    // 1. 当前节点必须是主节点
    if (!nodeIsMaster(myself)) return;

    // 2. 每个纪元只投一次票
    if (server.cluster->lastVoteEpoch == server.cluster->currentEpoch) return;

    // 3. 请求节点的 master 必须处于 FAIL 状态
    if (!(node->slaveof->flags & CLUSTER_NODE_FAIL)) return;

    // 4. 请求节点的复制偏移量必须是最新的
    if (request->offset < node->slaveof->repl_offset) return;

    // 5. 投票
    server.cluster->lastVoteEpoch = server.cluster->currentEpoch;
    node->flags |= CLUSTER_NODE_VOTED;

    clusterSendFailoverAuth(node->name);
}
```

### 9.4 Raft 变体选主

Redis Cluster 的选主算法是 Raft 的简化版本：

```c
// 从节点统计投票
void clusterUpdateMyselfEpoch(void) {
    ...
    int votes = 0;
    dictIterator *di = dictGetIterator(server.cluster->nodes);
    dictEntry *de;
    while ((de = dictNext(di)) != NULL) {
        clusterNode *n = dictGetVal(de);
        if (n->flags & CLUSTER_NODE_VOTED_FOR_ME) {
            votes++;
        }
    }
    dictReleaseIterator(di);

    // 获得过半数主节点投票
    if (votes >= (server.cluster->size / 2) + 1) {
        // 成为新主节点
        clusterFailoverReplaceMaster();
    }
}
```

选举关键点：
- **纪元递增**：每次选举递增 `currentEpoch`，防止旧消息干扰
- **随机延迟**：从节点发起选举前加入随机延迟，减少选主冲突
- **过半投票**：需要过半数主节点投票才能成为新主节点
- **数据优先**：复制偏移量更大的从节点优先（先到达先投票）

### 9.5 接管主节点

```c
void clusterFailoverReplaceMaster(void) {
    // 1. 变更自身身份
    myself->flags &= ~(CLUSTER_NODE_SLAVE);
    myself->flags |= CLUSTER_NODE_MASTER;
    myself->slaveof = NULL;

    // 2. 继承主节点的槽位
    for (int j = 0; j < CLUSTER_SLOTS; j++) {
        if (clusterNodeCoversNodeSlot(oldmaster, j)) {
            clusterDelSlot(j);
            clusterAddSlot(myself, j);
        }
    }

    // 3. 增加 configEpoch，使集群接受新配置
    myself->configEpoch = server.cluster->currentEpoch;
    server.cluster->currentEpoch++;

    // 4. 更新集群状态
    clusterUpdateState();

    // 5. 持久化配置
    clusterSaveConfigOrDie(1);

    // 6. 广播 PONG（通知所有节点新的角色和槽位）
    clusterBroadcastPong(CLUSTER_BROADCAST_ALL);

    // 7. 重置复制状态，成为新主节点
    replicationUnsetMaster();
}
```

新主节点通过广播 PONG 携带更新后的 `configEpoch` 和槽位位图，集群中其他节点收到后更新本地路由表。更高的 `configEpoch` 总是覆盖旧配置。

## 10. 集群更新与配置传播

### 10.1 configEpoch 冲突解决

```c
void clusterUpdateSlotsConfigWith(clusterNode *sender,
    uint64_t senderConfigEpoch, unsigned char *slots) {

    for (int j = 0; j < CLUSTER_SLOTS; j++) {
        if (bitmapTestBit(slots, j)) {
            clusterNode *current = server.cluster->slots[j];

            if (current == sender) continue; // 无变化

            if (current == NULL ||
                current->configEpoch < senderConfigEpoch) {
                // 发送者的 configEpoch 更高，接受其声明
                clusterDelSlot(j);
                clusterAddSlot(sender, j);
            } else if (current->configEpoch == senderConfigEpoch) {
                // configEpoch 冲突！
                // 使用节点名称字典序比较，较小者获胜
                if (memcmp(sender->name, current->name,
                          CLUSTER_NAMELEN) < 0) {
                    clusterDelSlot(j);
                    clusterAddSlot(sender, j);
                }
            }
            // 如果 current 的 configEpoch 更高，忽略发送者声明
        }
    }
}
```

**configEpoch 是 Redis Cluster 解决分布式冲突的核心机制**。当两个节点声明拥有同一个槽位时，以 configEpoch 更高者为准；如果相同（极少发生），以节点名称字典序较小者为准。这种确定性的冲突解决策略保证了集群最终一致性。

### 10.2 UPDATE 消息

当节点 A 收到节点 B 的 PING/PONG，发现 B 声明拥有某槽位，但 A 本地记录该槽位属于另一节点 C，且 C 的 configEpoch 更高时，A 会向 B 发送 UPDATE 消息：

```c
void clusterSendUpdate(clusterLink *link, clusterNode *node) {
    clusterMsg msg;
    msg.type = CLUSTERMSG_TYPE_UPDATE;
    msg.data.update.nodeinfo = *node; // 包含正确的 configEpoch 和 slots
    clusterSendMessage(link, &msg);
}
```

B 收到 UPDATE 后，用消息中的更高 configEpoch 更新本地配置。这是集群收敛的关键传播机制。

## 11. 面试题速查

**Q1: Redis Cluster 为什么用 16384 个槽而不是 65536？**
A: 三个原因：(1) Gossip 消息中需要携带槽位位图，16384 位 = 2KB，65536 位 = 8KB，前者开销更小；(2) Redis Cluster 建议最大 1000 个节点，16384 个槽足够分配；(3) 槽位信息在 Gossip 消息中会有压缩，16384 的压缩效果更好。

**Q2: MOVED 和 ASK 重定向有什么区别？**
A: MOVED 表示槽位已永久迁移，客户端应更新本地路由表；ASK 表示槽位正在迁移中（临时状态），客户端不更新路由表，只是临时向目标节点发送请求并带上 ASKING 标志。

**Q3: Redis Cluster 的故障检测流程是什么？**
A: 两阶段：(1) PFAIL（疑似故障）：节点超时未收到另一节点的 PONG，标记为 PFAIL；(2) FAIL（确认故障）：当过半数主节点都报告某节点 PFAIL，该节点被升级为 FAIL，并广播给全集群。

**Q4: Redis Cluster 的选主算法是什么？**
A: 基于 Raft 的简化版本。从节点发起选举请求（携带 currentEpoch），主节点投票（每个纪元只投一票），获得过半数主节点投票的从节点成为新主节点。复制偏移量更大的从节点优先发起选举。

**Q5: Hash Tag 是什么？有什么用？**
A: Hash Tag 是 `{}` 语法，Redis 只对 `{}` 中的内容做 CRC16 哈希。例如 `user:{1000}.name` 和 `user:{1000}.email` 会映射到同一个槽位，从而可以在同一节点上执行跨键操作（事务、Lua、MGET 等）。

**Q6: configEpoch 的作用是什么？**
A: 用于解决分布式冲突。当多个节点声明拥有同一槽位时，以 configEpoch 更高者为准。故障转移时新主节点会增加 configEpoch，确保其声明被全集群接受。configEpoch 相同时以节点名称字典序较小者为准。

**Q7: cluster_node_timeout 调大调小有什么影响？**
A: 调大：减少 Gossip 消息频率和故障误报，但故障发现更慢；调小：故障发现更快，但 Gossip 消息更频繁，网络开销更大。建议根据网络延迟设置，一般为节点间 RTT 的 5-10 倍。

**Q8: Redis Cluster 为什么不支持跨槽位的 MULTI/EXEC 事务？**
A: 因为事务需要所有涉及的键在同一节点上。如果跨槽位，请求会被重定向到不同节点，无法保证原子性。使用 Hash Tag 可以将相关键映射到同一槽位，从而支持事务。

**Q9: Gossip 协议的收敛速度如何？**
A: 每轮 Gossip 携带少量随机节点信息，理论上 O(log N) 轮可以覆盖所有节点。实际中，通过 `cluster_node_timeout` 控制发送频率，典型情况下几秒到十几秒可以收敛。

**Q10: Redis Cluster 和哨兵模式有什么区别？**
A: 哨兵（Sentinel）是主从复制 + 哨兵监控的方案，不支持数据分片，所有数据在一个主节点上；Redis Cluster 是分布式分片方案，数据分散到多个节点，内置故障转移，无需独立哨兵进程。Cluster 适合大数据量场景，Sentinel 适合单机容量足够但需要高可用的场景。

---

## 总结

Redis Cluster 的源码展现了一个生产级分布式系统的精巧设计。Gossip 协议实现了去中心化的状态传播，哈希槽实现了数据分片，configEpoch 解决了分布式冲突，Raft 变体实现了故障转移选主。每个机制都简洁而有效，体现了 antirez 一贯的设计哲学——在正确性和简洁性之间寻找最佳平衡。

深入理解 Redis Cluster 源码，不仅有助于面试，更能在实际运维中快速定位集群问题，做出合理的架构决策。对于大流量缓存场景，合理的 `cluster_node_timeout`、槽位分配、以及客户端重定向处理，是保证集群稳定性的关键。

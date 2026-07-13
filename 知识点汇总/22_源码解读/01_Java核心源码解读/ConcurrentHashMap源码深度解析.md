# ConcurrentHashMap源码深度解析

> ConcurrentHashMap是Java并发编程中最核心的线程安全哈希表实现。JDK 1.8彻底重构了它的实现，摒弃了分段锁（Segment），改用CAS + synchronized + Node数组 + 链表/红黑树的方案，在并发性能上实现了质的飞跃。本文基于JDK 1.8源码，深入剖析其初始化、put、get、扩容、计数等核心机制。

---

## 📋 目录

1. [JDK 1.7 vs JDK 1.8架构对比](#1-jdk-17-vs-jdk-18架构对比)
2. [核心属性与常量](#2-核心属性与常量)
3. [Node与TreeNode节点](#3-node与treenode节点)
4. [initTable初始化机制](#4-inittable初始化机制)
5. [put方法全流程解析](#5-put方法全流程解析)
6. [tabAt与casTabAt——内存可见性与原子操作](#6-tabat与castabat内存可见性与原子操作)
7. [get方法——无锁读取](#7-get方法无锁读取)
8. [transfer扩容机制——多线程协同迁移](#8-transfer扩容机制多线程协同迁移)
9. [addCount计数与触发扩容](#9-addcount计数与触发扩容)
10. [remove方法解析](#10-remove方法解析)
11. [面试题速查](#11-面试题速查)

---

## 1. JDK 1.7 vs JDK 1.8架构对比

### JDK 1.7：分段锁

JDK 1.7的ConcurrentHashMap采用**Segment + HashEntry**的二级哈希结构：

```
ConcurrentHashMap
├── Segment[0] (ReentrantLock)
│   └── HashEntry[]
│       └── HashEntry -> HashEntry -> ... (链表)
├── Segment[1] (ReentrantLock)
│   └── HashEntry[]
│       └── ...
├── ...
└── Segment[15] (ReentrantLock)
    └── HashEntry[]
        └── ...
```

- Segment继承ReentrantLock，每个Segment是一把锁
- 默认16个Segment，最多支持16线程并发写
- 先hash到Segment，再hash到Segment内的HashEntry数组
- 锁粒度：Segment级别

### JDK 1.8：CAS + synchronized

JDK 1.8废弃了Segment，回归HashMap类似的结构：

```
ConcurrentHashMap
├── Node[0]
│   └── Node -> Node -> ... (链表) 或 TreeNode (红黑树)
├── Node[1]
│   └── ...
├── ...
└── Node[n]
    └── ...
```

- 锁粒度：Node槽位级别（synchronized锁定链表头节点）
- CAS用于无锁写入空槽位
- 多线程扩容：多个线程协同迁移数据
- 并发度：理论上线程数等于数组长度

| 对比项 | JDK 1.7 | JDK 1.8 |
|--------|---------|---------|
| 数据结构 | Segment + HashEntry + 链表 | Node数组 + 链表 + 红黑树 |
| 锁实现 | ReentrantLock（Segment） | CAS + synchronized |
| 锁粒度 | Segment | Node槽位 |
| 并发度 | 默认16 | 等于数组长度 |
| 扩容 | 单线程扩容 | 多线程协同扩容 |
| 查询最坏复杂度 | O(n) | O(log n) |

---

## 2. 核心属性与常量

```java
public class ConcurrentHashMap<K,V> extends AbstractMap<K,V>
    implements ConcurrentMap<K,V>, Serializable {

    // 最大容量
    private static final int MAXIMUM_CAPACITY = 1 << 30;

    // 默认初始容量
    private static final int DEFAULT_CAPACITY = 16;

    // 最大可能（非2的幂）数组大小， toArray相关方法使用
    private static final int MAX_ARRAY_SIZE = Integer.MAX_VALUE - 8;

    // 默认并发级别（JDK 1.7遗留，1.8不再使用但保留兼容）
    private static final int DEFAULT_CONCURRENCY_LEVEL = 16;

    // 负载因子
    private static final float LOAD_FACTOR = 0.75f;

    // 链表转红黑树阈值
    static final int TREEIFY_THRESHOLD = 8;

    // 红黑树退化阈值
    static final int UNTREEIFY_THRESHOLD = 6;

    // 树化最小容量
    static final int MIN_TREEIFY_CAPACITY = 64;

    // 扩容线程的最小迁移步长：每个线程一次最少迁移16个桶
    private static final int MIN_TRANSFER_STRIDE = 16;

    // 生成扩容唯一戳的位数
    private static final int RESIZE_STAMP_BITS = 16;

    // 最大扩容线程数
    private static final int MAX_RESIZERS = (1 << (32 - RESIZE_STAMP_BITS)) - 1;

    // 扩容戳移位
    private static final int RESIZE_STAMP_SHIFT = 32 - RESIZE_STAMP_BITS;

    // ---------- 特殊节点标记 ----------

    // ForwardingNode的hash值：表示该桶正在迁移中
    static final int MOVED     = -1;

    // TreeBin的hash值：表示该桶是红黑树
    static final int TREEBIN   = -2;

    // ReservationNode的hash值：computeIfAbsent等方法的占位节点
    static final int RESERVED  = -3;

    // hash可用位
    static final int HASH_BITS = 0x7fffffff; // 正整数31位

    // Node数组，懒加载
    transient volatile Node<K,V>[] table;

    // 扩容时的新数组
    private transient volatile Node<K,V>[] nextTable;

    // 基础计数（无竞争时使用）
    private transient volatile long baseCount;

    // 初始化或扩容控制：
    // -1: 正在初始化
    // -(1 + N): 有N个线程正在扩容
    // 正数: 初始容量或下一次扩容的阈值
    private transient volatile int sizeCtl;

    // 计数单元格数组（高并发计数时使用，类似LongAdder的Cell）
    private transient volatile CounterCell[] counterCells;
}
```

**sizeCtl的状态机**：

| 值 | 含义 |
|----|------|
| 0 | 未初始化（默认） |
| -1 | 正在初始化 |
| -(1 + N) | 有N个线程正在扩容 |
| 正数 | 初始化阈值或扩容阈值 |

**counterCells与LongAdder**：ConcurrentHashMap的计数机制借鉴了LongAdder的设计思想。在高并发下，多个线程同时对baseCount做CAS操作会产生大量竞争。CounterCell将计数分散到多个Cell上，减少竞争，最后求和得到总数。

---

## 3. Node与TreeNode节点

### 3.1 Node

```java
static class Node<K,V> implements Map.Entry<K,V> {
    final int hash;
    final K key;
    // val和next用volatile修饰，保证多线程可见性
    volatile V val;
    volatile Node<K,V> next;

    Node(int hash, K key, V val, Node<K,V> next) {
        this.hash = hash;
        this.key = key;
        this.val = val;
        this.next = next;
    }

    public final V setValue(V value) {
        throw new UnsupportedOperationException();
    }

    // 用于find方法，子类TreeBin和ForwardingNode会重写
    Node<K,V> find(int h, Object k) {
        Node<K,V> e = this;
        do {
            K ek;
            if (e.hash == h &&
                ((ek = e.key) == k || (ek != null && k.equals(ek))))
                return e;
        } while ((e = e.next) != null);
        return null;
    }
}
```

**与HashMap的Node的区别**：
1. `val`和`next`是volatile的，保证内存可见性
2. `setValue`方法直接抛异常（不支持直接修改值）
3. 增加了`find`方法，子类可重写以实现特殊查找逻辑

### 3.2 ForwardingNode

```java
static final class ForwardingNode<K,V> extends Node<K,V> {
    final Node<K,V>[] nextTable;
    ForwardingNode(Node<K,V>[] tab) {
        // hash = MOVED (-1)
        super(MOVED, null, null, null);
        this.nextTable = tab;
    }

    // 在新表（nextTable）中查找
    Node<K,V> find(int h, Object k) {
        // 从外层重新开始查找，避免递归过深
        outer: for (Node<K,V>[] tab = nextTable;;) {
            Node<K,V> e; int n;
            if (k == null || tab == null || (n = tab.length) == 0 ||
                (e = tabAt(tab, (n - 1) & h)) == null)
                return null;
            for (;;) {
                int eh; K ek;
                if ((eh = e.hash) == h &&
                    ((ek = e.key) == k || (ek != null && k.equals(k))))
                    return e;
                if (eh < 0) {
                    if (e instanceof ForwardingNode) {
                        tab = ((ForwardingNode<K,V>)e).nextTable;
                        continue outer;
                    }
                    else
                        return e.find(h, k);
                }
                if ((e = e.next) == null)
                    return null;
            }
        }
    }
}
```

ForwardingNode是扩容期间的**占位节点**。当一个桶的数据迁移完成后，旧数组的该位置被替换为ForwardingNode。其他线程读写到该节点时，会通过find方法转发到新数组中查找。

### 3.3 TreeBin

```java
static final class TreeBin<K,V> extends Node<K,V> {
    TreeNode<K,V> root;          // 红黑树根节点
    volatile TreeNode<K,V> first;// 链表头节点（保留链表结构用于退化）
    volatile Thread waiter;      // 等待的线程
    volatile int lockState;      // 锁状态
    // lockState的bit含义：
    // bit 0: Writer（写锁）
    // bit 1: Writer等待
    // bit 2~: Reader（读锁）计数

    static final int WRITER = 1; // 写锁标志
    static final int WAITER = 2; // 等待标志
    static final int READER = 4; // 读锁基数（每个读线程增加4）

    TreeBin(TreeNode<K,V> b) {
        super(TREEBIN, null, null, null); // hash = TREEBIN (-2)
        this.first = b;
        // 构建红黑树
        TreeNode<K,V> r = null;
        for (TreeNode<K,V> x = b, next; x != null; x = next) {
            next = (TreeNode<K,V>)x.next;
            x.left = x.right = null;
            if (r == null) {
                x.parent = null;
                x.red = false;
                r = x;
            }
            else {
                K k = x.key;
                int h = x.hash;
                Class<?> kc = null;
                for (TreeNode<K,V> p = r;;) {
                    int dir, ph;
                    K pk = p.key;
                    if ((ph = p.hash) > h)
                        dir = -1;
                    else if (ph < h)
                        dir = 1;
                    else if ((kc == null &&
                              (kc = comparableClassFor(k)) == null) ||
                             (dir = compareComparables(kc, k, pk)) == 0)
                        dir = tieBreakOrder(k, pk);
                    TreeNode<K,V> xp = p;
                    if ((p = (dir <= 0) ? p.left : p.right) == null) {
                        x.parent = xp;
                        if (dir <= 0)
                            xp.left = x;
                        else
                            xp.right = x;
                        r = balanceInsertion(r, x);
                        break;
                    }
                }
            }
        }
        root = r;
        assert checkInvariants(root);
    }
}
```

TreeBin不直接存储key-value，而是作为红黑树的**代理节点**放在Node数组中。它的hash值为TREEBIN(-2)。TreeBin内部维护了一个读写锁机制，允许多个读线程并发读，写线程独占写。

---

## 4. initTable初始化机制

```java
private final Node<K,V>[] initTable() {
    Node<K,V>[] tab; int sc;
    while ((tab = table) == null || tab.length == 0) {
        // sizeCtl < 0 表示正在初始化或扩容
        if ((sc = sizeCtl) < 0)
            Thread.yield(); // 让出CPU，等待初始化完成
        else if (U.compareAndSwapInt(this, SIZECTL, sc, -1)) {
            // CAS成功，获得初始化资格
            try {
                if ((tab = table) == null || tab.length == 0) {
                    // sc > 0表示构造方法指定了初始容量
                    int n = (sc > 0) ? sc : DEFAULT_CAPACITY;
                    @SuppressWarnings("unchecked")
                    Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n];
                    table = tab = nt;
                    // sc = n - n/4 = 0.75n（即负载因子0.75对应的阈值）
                    sc = n - (n >>> 2);
                }
            } finally {
                sizeCtl = sc; // 设置扩容阈值
            }
            break;
        }
    }
    return tab;
}
```

**初始化过程**：
1. 检查table是否为null
2. 如果sizeCtl < 0（其他线程正在初始化），当前线程yield等待
3. CAS将sizeCtl从正数改为-1，竞争到初始化资格
4. 再次检查table是否为null（双重检查，防止重复初始化）
5. 创建Node数组，设置sizeCtl为扩容阈值（0.75 * capacity）

**为什么用CAS而不是synchronized？** 初始化只发生一次，用CAS更轻量。CAS失败说明有其他线程正在初始化，当前线程只需等待即可。

---

## 5. put方法全流程解析

```java
public V put(K key, V value) {
    return putVal(key, value, false);
}

final V putVal(K key, V value, boolean onlyIfAbsent) {
    // ConcurrentHashMap不允许null key和null value
    if (key == null || value == null) throw new NullPointerException();
    int hash = spread(key.hashCode()); // 扰动函数
    int binCount = 0;
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;

        // === 情况1：table未初始化 ===
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();

        // === 情况2：目标槽位为空，CAS插入 ===
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break; // CAS成功，插入完成
            // CAS失败（竞争），进入下次循环重试
        }

        // === 情况3：槽位是ForwardingNode，帮助扩容 ===
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);

        // === 情况4：槽位有节点，synchronized锁住头节点 ===
        else {
            Node<K,V> pred = null;
            synchronized (f) { // 锁住链表头节点
                if (tabAt(tab, i) == f) { // 再次确认头节点没变（防止其他线程已经修改了槽位）
                    if (fh >= 0) {
                        // fh >= 0 表示是普通链表节点
                        binCount = 1;
                        for (Node<K,V> e = f;; ++binCount) {
                            K ek;
                            // key相同，覆盖value
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                oldVal = e.val;
                                if (!onlyIfAbsent)
                                    e.val = value;
                                break;
                            }
                            pred = e;
                            // 到达链表尾部，尾插新节点
                            if ((e = e.next) == null) {
                                pred.next = new Node<K,V>(hash, key, value, null);
                                break;
                            }
                        }
                    }
                    else if (f instanceof TreeBin) {
                        // 红黑树节点
                        Node<K,V> p;
                        binCount = 2;
                        if ((p = ((TreeBin<K,V>)f).putTreeVal(hash, key, value)) != null) {
                            oldVal = p.val;
                            if (!onlyIfAbsent)
                                p.val = value;
                        }
                    }
                }
            }

            // === 情况4后续：检查是否需要树化 ===
            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i); // 链表转红黑树
                if (oldVal != null)
                    return oldVal; // 是覆盖操作，不需要增加count
                break;
            }
        }
    }
    // 增加元素计数，检查是否需要扩容
    addCount(1L, binCount);
    return null;
}
```

**put流程总结**：

| 情况 | 操作 | 同步机制 |
|------|------|----------|
| table未初始化 | initTable() | CAS（sizeCtl -1） |
| 槽位为空 | 创建Node放入 | CAS（casTabAt） |
| 槽位是ForwardingNode | helpTransfer | 协助扩容 |
| 槽位是链表 | 遍历链表插入/覆盖 | synchronized(头节点) |
| 槽位是红黑树 | putTreeVal | synchronized(头节点) |

**为什么用synchronized而不是ReentrantLock？**

JDK 1.8选择synchronized的原因：
1. **锁优化**：JDK 1.6后synchronized引入了偏向锁、轻量级锁、重量级锁等优化，在低竞争下性能不亚于ReentrantLock
2. **内存开销**：synchronized是JVM层面实现，不需要额外的对象头字段；ReentrantLock需要继承AQS，有额外内存开销
3. **锁粒度**：锁的是Node头节点，每个槽位一把锁，竞争很小，大部分情况下synchronized只会用到偏向锁或轻量级锁

---

## 6. tabAt与casTabAt——内存可见性与原子操作

```java
// 获取tab[i]的值，使用volatile语义读
static final <K,V> Node<K,V> tabAt(Node<K,V>[] tab, int i) {
    return (Node<K,V>)U.getReferenceAcquire(tab, ((long)i << ASHIFT) + ABASE);
}

// CAS设置tab[i]
static final <K,V> boolean casTabAt(Node<K,V>[] tab, int i,
                                    Node<K,V> c, Node<K,V> v) {
    return U.compareAndSetReference(tab, ((long)i << ASHIFT) + ABASE, c, v);
}

// 原子设置tab[i]
static final <K,V> void setTabAt(Node<K,V>[] tab, int i, Node<K,V> v) {
    U.putReferenceRelease(tab, ((long)i << ASHIFT) + ABASE, v);
}
```

**为什么不能直接用tab[i]访问数组元素？**

Java数组元素本身没有volatile语义。即使table引用是volatile的，`table[i]`的读取也不是volatile读。在多线程环境下，一个线程对`table[i]`的写入可能不会立即对其他线程可见。

通过Unsafe的`getReferenceAcquire`（等价于volatile读）和`compareAndSetReference`（CAS操作），保证了对数组元素的原子访问和内存可见性。

**spread方法（扰动函数）**：

```java
static final int spread(int h) {
    return (h ^ (h >>> 16)) & HASH_BITS;
}
```

与HashMap的hash方法类似，但额外做了`& HASH_BITS`（0x7fffffff）操作，确保hash值为非负数。因为负数hash有特殊含义（MOVED=-1, TREEBIN=-2, RESERVED=-3）。

---

## 7. get方法——无锁读取

```java
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());

    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {

        // 检查第一个节点
        if ((eh = e.hash) == h) {
            if ((ek = e.key) == key || (ek != null && key.equals(ek)))
                return e.val;
        }
        // hash为负数：ForwardingNode或TreeBin
        else if (eh < 0)
            return (p = e.find(h, key)) != null ? p.val : null;

        // 遍历链表
        while ((e = e.next) != null) {
            if (e.hash == h &&
                ((ek = e.key) == key || (ek != null && key.equals(ek))))
                return e.val;
        }
    }
    return null;
}
```

**get全程不加锁**，这是ConcurrentHashMap高性能的关键之一。它能做到无锁读取的原因：

1. **Node的val和next是volatile的**：保证一个线程写入的值对其他线程立即可见
2. **tabAt使用volatile读**：保证读取到的数组引用是最新的
3. **ForwardingNode的find方法**：扩容期间，如果读到的节点是ForwardingNode，会转发到新数组中查找
4. **TreeBin的find方法**：使用读写锁，允许多个读线程并发读

**get方法的容错设计**：

在扩容过程中，table和nextTable可能同时存在。get方法的设计确保在任何时刻都能正确找到数据：
- 如果目标桶尚未迁移：从旧表table中正常读取
- 如果目标桶已迁移：读到ForwardingNode，转发到nextTable中查找
- 如果nextTable也在扩容（极端情况）：ForwardingNode的find方法会递归转发

---

## 8. transfer扩容机制——多线程协同迁移

transfer是ConcurrentHashMap最复杂的方法，支持多个线程同时参与扩容。

```java
private final void transfer(Node<K,V>[] tab, Node<K,V>[] nextTab) {
    int n = tab.length, sc;

    // === 第一部分：初始化nextTab ===
    if (nextTab == null) {
        try {
            Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n << 1]; // 容量翻倍
            nextTab = nt;
        } catch (Throwable ex) {
            sizeCtl = Integer.MAX_VALUE; // 扩容失败，设置超大值阻止后续扩容
            return;
        }
        nextTable = nextTab;
        transferIndex = n; // 迁移从数组末尾开始
    }

    int nextn = nextTab.length;

    // ForwardingNode，迁移完成的桶会被设置为这个节点
    ForwardingNode<K,V> fwd = new ForwardingNode<K,V>(nextTab);

    // advance标记：当前桶是否已处理完，可以前进到下一个桶
    boolean advance = true;

    // finishing标记：扩容是否即将完成
    boolean finishing = false;

    // === 第二部分：循环迁移每个桶 ===
    for (int i = 0, bound = 0;;) {
        Node<K,V> f; int fh;

        // --- 2.1 领取任务区间 ---
        while (advance) {
            int nextIndex, nextBound;
            if (--i >= bound || finishing)
                advance = false;
            else if ((nextIndex = transferIndex) <= 0) {
                i = -1; // 所有桶已分配完
                advance = false;
            }
            else if (U.compareAndSwapInt
                     (this, TRANSFERINDEX, nextIndex,
                      nextBound = (nextIndex > stride ?
                                   nextIndex - stride : 0))) {
                bound = nextBound;
                i = nextIndex - 1;
                advance = false;
            }
        }

        // --- 2.2 检查是否扩容完成 ---
        if (i < 0 || i >= n || i + n >= nextn) {
            int sc;
            if (finishing) {
                // 最后一个线程完成迁移
                nextTable = null;
                table = nextTab; // 切换到新表
                sizeCtl = (n << 1) - (n >>> 1); // 新阈值 = 1.5 * 2n = 1.5n... 实际是 2n * 0.75
                return;
            }
            // CAS减少扩容线程数
            if (U.compareAndSwapInt(this, SIZECTL, sc = sizeCtl, sc - 1)) {
                if ((sc - 2) != resizeStamp(n) << RESIZE_STAMP_SHIFT)
                    return; // 还有其他线程在扩容，当前线程退出
                // 当前线程是最后一个扩容线程，设置finishing标记
                finishing = advance = true;
                i = n; // 重新遍历一遍检查所有桶都迁移完成
            }
        }

        // --- 2.3 目标桶为空，放置ForwardingNode ---
        else if ((f = tabAt(tab, i)) == null)
            advance = casTabAt(tab, i, null, fwd);

        // --- 2.4 目标桶已经是ForwardingNode，跳过 ---
        else if ((fh = f.hash) == MOVED)
            advance = true; // 已迁移

        // --- 2.5 执行实际的数据迁移 ---
        else {
            synchronized (f) { // 锁住头节点
                if (tabAt(tab, i) == f) {
                    Node<K,V> ln, hn;
                    if (fh >= 0) {
                        // === 链表迁移 ===
                        // 与HashMap类似，拆分为低位链表和高位链表
                        int runBit = fh & n;
                        Node<K,V> lastRun = f;
                        // 优化：找到链表尾部连续相同bit位的段
                        for (Node<K,V> p = f.next; p != null; p = p.next) {
                            int b = p.hash & n;
                            if (b != runBit) {
                                runBit = b;
                                lastRun = p;
                            }
                        }
                        if (runBit == 0) {
                            ln = lastRun;
                            hn = null;
                        }
                        else {
                            hn = lastRun;
                            ln = null;
                        }
                        // 遍历链表，构建两个子链表
                        for (Node<K,V> p = f; p != lastRun; p = p.next) {
                            int ph = p.hash;
                            if ((ph & n) == 0)
                                ln = new Node<K,V>(ph, p.key, p.val, ln);
                            else
                                hn = new Node<K,V>(ph, p.key, p.val, hn);
                        }
                        // 低位链表放到新表原位置
                        setTabAt(nextTab, i, ln);
                        // 高位链表放到新表原位置+n
                        setTabAt(nextTab, i + n, hn);
                        // 旧表标记为ForwardingNode
                        setTabAt(tab, i, fwd);
                        advance = true;
                    }
                    else if (f instanceof TreeBin) {
                        // === 红黑树迁移 ===
                        TreeBin<K,V> t = (TreeBin<K,V>)f;
                        TreeNode<K,V> lo = null, loTail = null;
                        TreeNode<K,V> hi = null, hiTail = null;
                        int lc = 0, hc = 0;
                        for (Node<K,V> e = t.first; e != null; e = e.next) {
                            int h = e.hash;
                            TreeNode<K,V> p = new TreeNode<K,V>
                                (h, e.key, e.val, null, null);
                            if ((h & n) == 0) {
                                if ((p.prev = loTail) == null)
                                    lo = p;
                                else
                                    loTail.next = p;
                                loTail = p;
                                ++lc;
                            }
                            else {
                                if ((p.prev = hiTail) == null)
                                    hi = p;
                                else
                                    hiTail.next = p;
                                hiTail = p;
                                ++hc;
                            }
                        }
                        // 迁移后如果节点数<=6，退化为链表
                        ln = (lc <= UNTREEIFY_THRESHOLD) ? untreeify(lo) :
                            (hc != 0) ? new TreeBin<K,V>(lo) : t;
                        hn = (hc <= UNTREEIFY_THRESHOLD) ? untreeify(hi) :
                            (lc != 0) ? new TreeBin<K,V>(hi) : t;
                        setTabAt(nextTab, i, ln);
                        setTabAt(nextTab, i + n, hn);
                        setTabAt(tab, i, fwd);
                        advance = true;
                    }
                }
            }
        }
    }
}
```

**多线程扩容的核心设计**：

1. **任务分配**：`transferIndex`从数组末尾开始，每个线程通过CAS领取一个stride（步长，最少16个桶）的迁移任务
2. **ForwardingNode标记**：迁移完成的桶被标记为ForwardingNode，其他线程读到时知道该桶已迁移
3. **协助扩容**：put线程遇到ForwardingNode时调用helpTransfer加入扩容
4. **完成检查**：最后一个扩容线程负责切换table引用和设置新的sizeCtl

**lastRun优化**：迁移链表时，先找到链表尾部连续属于同一侧（低位或高位）的最后一段（lastRun），这段不需要重新创建节点，直接复用。只有lastRun之前的节点需要重新创建。这减少了不必要的节点创建。

---

## 9. addCount计数与触发扩容

```java
private final void addCount(long x, int check) {
    CounterCell[] as; long b, s;

    // === 第一部分：更新计数 ===
    if ((as = counterCells) != null ||
        !U.compareAndSetLong(this, BASECOUNT, b = baseCount, s = b + x)) {
        // baseCount CAS失败或counterCells已存在，使用CounterCell
        CounterCell a; long v; int m;
        boolean uncontended = true;
        if (as == null || (m = as.length) < 1 ||
            (a = as[ThreadLocalRandom.getProbe() & m]) == null ||
            !(uncontended =
              U.compareAndSetLong(a, CELLVALUE, v = a.value, v + x))) {
            // CounterCell CAS也失败，调用fullAddCount（类似LongAdder的fullAdd）
            fullAddCount(x, uncontended);
            return;
        }
        if (check <= 1)
            return;
        s = sumCount(); // 求和得到总数
    }

    // === 第二部分：检查是否需要扩容 ===
    if (check >= 0) {
        Node<K,V>[] tab, nt; int n, sc;
        // s >= sizeCtl(阈值) 且 table非空 且 未达最大容量
        while (s >= (long)(sc = sizeCtl) && (tab = table) != null &&
               (n = tab.length) < MAXIMUM_CAPACITY) {
            // 生成扩容戳
            int rs = resizeStamp(n);
            if (sc < 0) {
                // 正在扩容
                if ((sc >>> RESIZE_STAMP_SHIFT) != rs || sc == rs + 1 ||
                    sc == rs + MAX_RESIZERS || (nt = nextTable) == null ||
                    transferIndex <= 0)
                    break; // 不满足协助扩容条件
                // CAS增加扩容线程数
                if (U.compareAndSwapInt(this, SIZECTL, sc, sc + 1))
                    transfer(tab, nt); // 协助扩容
            }
            else {
                // 触发扩容：sizeCtl = (rs << RESIZE_STAMP_SHIFT) + 2
                // +2表示第一个扩容线程
                if (U.compareAndSwapInt(this, SIZECTL, sc,
                                         (rs << RESIZE_STAMP_SHIFT) + 2))
                    transfer(tab, null); // 发起扩容
            }
            s = sumCount(); // 重新计算总数
        }
    }
}
```

**resizeStamp（扩容戳）**：

```java
static final int resizeStamp(int n) {
    return Integer.numberOfLeadingZeros(n) | (1 << (RESIZE_STAMP_BITS - 1));
}
```

扩容戳的作用是在多线程扩容时标识一次扩容操作。它由两部分组成：
- `numberOfLeadingZeros(n)`：n的前导零数，与n的容量相关
- `(1 << 15)`：第16位固定为1，确保扩容戳为负数

sizeCtl在扩容时的值为`(resizeStamp << 16) | 线程数`。由于最高位为1，整个值为负数。通过`sc >>> 16`可以取出扩容戳，与当前容量生成的戳比较，判断是否是同一次扩容。

**计数机制（LongAdder思想）**：

```
baseCount (volatile long)
   ↑ CAS（无竞争时）

CounterCell[0]  CounterCell[1]  CounterCell[2]  ...
   ↑ CAS             ↑ CAS           ↑ CAS
线程A            线程B            线程C

总数 = baseCount + sum(counterCells)
```

高并发下，多个线程对baseCount做CAS会严重竞争。CounterCell将计数分散到多个Cell上，每个线程通过ThreadLocalRandom选择一个Cell做CAS，减少竞争。这种设计源自LongAdder。

---

## 10. remove方法解析

```java
public V remove(Object key) {
    return replaceNode(key, null, null);
}

final V replaceNode(Object key, V value, Object cv) {
    int hash = spread(key.hashCode());
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;

        if (tab == null || (n = tab.length) == 0 ||
            (f = tabAt(tab, i = (n - 1) & hash)) == null)
            break; // table为空或槽位为空，直接返回

        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f); // 协助扩容

        else {
            V oldVal = null;
            boolean validated = false;
            synchronized (f) { // 锁住头节点
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {
                        // 链表节点
                        validated = true;
                        for (Node<K,V> e = f, pred = null;;) {
                            K ek;
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                V ev = e.val;
                                // cv为null表示无条件删除
                                // cv不为null需要验证旧值匹配
                                if (cv == null || cv == ev ||
                                    (ev != null && cv.equals(ev))) {
                                    oldVal = ev;
                                    if (value != null)
                                        e.val = value; // 替换值
                                    else if (pred != null)
                                        pred.next = e.next; // 删除中间节点
                                    else
                                        setTabAt(tab, i, e.next); // 删除头节点
                                }
                                break;
                            }
                            pred = e;
                            if ((e = e.next) == null)
                                break;
                        }
                    }
                    else if (f instanceof TreeBin) {
                        // 红黑树节点
                        validated = true;
                        TreeBin<K,V> t = (TreeBin<K,V>)f;
                        TreeNode<K,V> r, p;
                        if ((r = t.root) != null &&
                            (p = r.findTreeNode(hash, key, null)) != null) {
                            V pv = p.val;
                            if (cv == null || cv == pv ||
                                (pv != null && cv.equals(pv))) {
                                oldVal = pv;
                                if (value != null)
                                    p.val = value;
                                else
                                    t.removeTreeNode(p); // 从树中删除
                            }
                        }
                    }
                }
            }
            if (validated) {
                if (oldVal != null) {
                    if (value == null)
                        addCount(-1L, -1); // 删除操作，计数减1
                    return oldVal;
                }
                break;
            }
        }
    }
    return null;
}
```

remove方法与put方法类似，都是通过synchronized锁住槽位头节点来保证线程安全。删除后会通过addCount(-1L, -1)减少元素计数。删除红黑树节点后，如果节点数降到阈值以下，会在下一次操作时退化为链表。

---

## 11. 面试题速查

**Q1: ConcurrentHashMap在JDK 1.7和1.8中的区别？**
> JDK 1.7采用Segment + HashEntry + ReentrantLock，默认16个Segment，并发度16。JDK 1.8改为Node数组 + 链表/红黑树 + CAS + synchronized，锁粒度从Segment降到Node槽位，并发度等于数组长度。同时引入红黑树优化hash冲突时的查询性能。

**Q2: ConcurrentHashMap为什么不允许null key和null value？**
> 因为在并发环境下无法区分"值为null"和"不存在"。HashMap可以在get后用containsKey区分，但ConcurrentHashMap在get和containsKey之间可能被其他线程修改，产生二义性问题。Doug Lea在邮件列表中明确解释过这个设计决策。

**Q3: ConcurrentHashMap的put流程是什么？**
> ①计算hash；②table未初始化则initTable；③槽位为空用CAS插入；④遇到ForwardingNode则helpTransfer协助扩容；⑤否则synchronized锁住头节点，链表尾插或树节点插入；⑥addCount增加计数并检查扩容。

**Q4: ConcurrentHashMap的get需要加锁吗？**
> 不需要。get全程无锁。Node的val和next是volatile的，保证可见性。扩容期间通过ForwardingNode转发到新表查找。TreeBin使用读写锁支持并发读。

**Q5: ConcurrentHashMap的扩容是如何支持多线程的？**
> ①transferIndex从数组末尾开始分配任务，每个线程通过CAS领取stride个桶（最少16个）；②迁移完成的桶设为ForwardingNode；③put线程遇到ForwardingNode时通过helpTransfer加入扩容；④最后一个扩容线程负责切换table和设置新sizeCtl。

**Q6: ConcurrentHashMap的size()方法准确吗？**
> 不完全准确。size()通过sumCount()将baseCount和所有CounterCell的值求和。由于遍历CounterCell时其他线程可能正在修改，结果是一个近似值。在高并发场景下，size()返回的值可能与实际元素个数有微小偏差。

**Q7: ConcurrentHashMap为什么用synchronized而不是ReentrantLock？**
> ①JDK 1.6后synchronized经过优化（偏向锁、轻量级锁），低竞争下性能不亚于ReentrantLock；②synchronized是JVM层面实现，不需要额外对象头开销；③锁粒度细化到Node级别，竞争极小；④代码更简洁，不需要手动unlock。

**Q8: ForwardingNode的作用是什么？**
> ①标记该桶已迁移完成；②读线程遇到ForwardingNode时转发到nextTable查找；③写线程遇到时触发helpTransfer协助扩容。它是扩容期间协调读写操作的关键节点。

**Q9: ConcurrentHashMap如何保证并发扩容时数据不丢失？**
> ①迁移时synchronized锁住旧桶头节点，防止并发修改；②迁移完成后用ForwardingNode占位；③读操作通过ForwardingNode转发到新表；④多个线程通过CAS领取不同区间的桶，避免冲突；⑤最后完成检查确保所有桶都迁移完毕。

**Q10: ConcurrentHashMap和HashMap的hash方法有什么区别？**
> HashMap: `(h = key.hashCode()) ^ (h >>> 16)`，可能返回负数。ConcurrentHashMap: `(h ^ (h >>> 16)) & 0x7fffffff`，保证非负。因为ConcurrentHashMap中负数hash有特殊含义（MOVED=-1, TREEBIN=-2, RESERVED=-3）。

**Q11: ConcurrentHashMap的sizeCtl在不同状态下表示什么？**
> ①正数：未初始化时表示初始容量，已初始化时表示扩容阈值（0.75 * capacity）；②-1：正在初始化；③-(1+N)：有N个线程正在扩容。sizeCtl是一个多功能的状态变量，通过CAS操作实现线程安全的状态转换。

**Q12: ConcurrentHashMap的计数机制是怎样的？**
> 借鉴LongAdder设计。无竞争时直接CAS更新baseCount；有竞争时将计数分散到CounterCell数组中，每个线程通过ThreadLocalRandom选择一个Cell做CAS，减少竞争。size()通过sumCount()将baseCount和所有CounterCell求和得到总数，结果在高并发下是近似值。
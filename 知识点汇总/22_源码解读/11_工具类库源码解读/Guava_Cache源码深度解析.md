# Guava Cache 源码深度解析

> "缓存是计算机科学中两件难事之一。" —— 毫无疑问，Google Guava Cache 用极其优雅的并发设计将这件难事做到了极致。作为 Java 生态中使用最广泛的本地缓存库之一，它的源码蕴含了大量并发编程、内存管理、淘汰策略的精妙实现。

---

## 📋 目录

1. [整体架构概览](#1-整体架构概览)
2. [核心类与接口设计](#2-核心类与接口设计)
3. [LocalCache 继承体系](#3-localcache-继承体系)
4. [Segment 分段锁机制](#4-segment-分段锁机制)
5. [写入流程全链路解析](#5-写入流程全链路解析)
6. [读取流程与缓存加载](#6-读取流程与缓存加载)
7. [淘汰策略实现](#7-淘汰策略实现)
8. [过期机制与时间管理](#8-过期机制与时间管理)
9. [回调与移除通知](#9-回调与移除通知)
10. [并发安全与内存可见性](#10-并发安全与内存可见性)
11. [面试题速查](#11-面试题速查)

---

## 1. 整体架构概览

Guava Cache 的核心设计思想是 **分段锁 + 懒回收 + 引用监听**。它没有采用全局锁，而是借鉴了 `ConcurrentHashMap` 的分段设计，将缓存数据分散到多个 Segment 中，每个 Segment 独立加锁，从而实现高并发读写。

```
┌──────────────────────────────────────────────┐
│              CacheBuilder                    │
│   (构建器模式：配置过期、淘汰、加载器等)        │
└──────────────────┬───────────────────────────┘
                   │ build()
                   ▼
┌──────────────────────────────────────────────┐
│            LocalCache                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Segment0 │ │ Segment1 │ │ SegmentN │     │
│  │  ┌─────┐ │ │  ┌─────┐ │ │  ┌─────┐ │     │
│  │  │Entry│ │ │  │Entry│ │ │  │Entry│ │     │
│  │  └─────┘ │ │  └─────┘ │ │  └─────┘ │     │
│  └──────────┘ └──────────┘ └──────────┘     │
└──────────────────────────────────────────────┘
```

整个缓存的核心入口是 `LocalCache`，它实现了 `ConcurrentMap` 接口。每个 Segment 内部维护一个 `AtomicReferenceArray`，数组每个槽位存放一个链表头节点（或空），形成开链哈希表结构。

## 2. 核心类与接口设计

### 2.1 Cache 接口

```java
public interface Cache<K, V> {

  // 如果 key 不存在，通过 Callable 加载值
  V get(K key, Callable<? extends V> loader) throws ExecutionException;

  // 批量获取
  ImmutableMap<K, V> getAllPresent(Iterable<?> keys);

  // 获取已缓存的值（不触发加载）
  V getIfPresent(Object key);

  // 存入
  void put(K key, V value);

  // 失效
  void invalidate(Object key);
  void invalidateAll();

  // 统计
  CacheStats stats();

  // 清理
  void cleanUp();

  // 视图
  ConcurrentMap<K, V> asMap();
}
```

### 2.2 CacheBuilder 构建器

```java
public class CacheBuilder<K, V> {
  // 并发级别，决定 Segment 数量
  int concurrencyLevel = 16; // DEFAULT_CONCURRENCY_LEVEL

  // 最大容量
  long maximumSize = UNSET_INT;

  // 过期时间
  long expireAfterWriteNanos = UNSET_INT;
  long expireAfterAccessNanos = UNSET_INT;
  long refreshNanos = UNSET_INT;

  // 引用类型
  Strength keyStrength;
  Strength valueStrength;

  // 移除监听器
  RemovalListener<? super K, ? super V> removalListener;

  // 统计开关
  boolean recordStats;

  public <K1 extends K, V1 extends V> Cache<K1, V1> build(
      CacheLoader<? super K1, V1> loader) {
    return new LocalCache<>(this, loader);
  }
}
```

`CacheBuilder` 是典型的建造者模式，所有配置都在 build 时一次性传入 `LocalCache` 构造函数。值得注意的是 `concurrencyLevel` 直接决定了 Segment 数量（向上取整为 2 的幂）：

```java
int segmentShift = Integer.numberOfLeadingZeros(segmentCount);
int segmentMask = segmentCount - 1;
Segment<K, V, E>[] segments = newSegmentArray(segmentCount);
```

## 3. LocalCache 继承体系

```java
class LocalCache<K, V> extends AbstractMap<K, V> implements ConcurrentMap<K, V> {

  final Segment<K, V, E>[] segments;

  // 键值引用强度
  final Strength keyStrength;
  final Strength valueStrength;

  // 过期参数
  final long expireAfterWriteNanos;
  final long expireAfterAccessNanos;
  final long refreshNanos;

  // 淘汰参数
  final long maximumWeight;
  final Weigher<? super K, ? super V> weigher;

  // 等效比较器
  final Equivalence<Object> keyEquivalence;
  final Equivalence<Object> valueEquivalence;

  // 键值引用队列（配合 Soft/Weak 引用使用）
  final ReferenceQueue<K> keyReferenceQueue;
  final ReferenceQueue<V> valueReferenceQueue;

  // 移除监听队列
  final Queue<RemovalNotification<K, V>> removalNotificationQueue;
  final RemovalListener<? super K, ? super V> removalListener;

  // 统计计数器
  final StatsCounter globalStatsCounter;
}
```

`LocalCache` 持有所有全局配置和 Segment 数组。它本身不直接操作数据，所有读写都委托给对应的 Segment。

## 4. Segment 分段锁机制

Segment 是 Guava Cache 的并发控制核心，每个 Segment 是一个独立的迷你哈希表：

```java
abstract static class Segment<K, V, E extends InternalEntry<K, V, E>>
    extends ReentrantLock {

  // 存储条目的数组
  volatile AtomicReferenceArray<E> table;

  // 当前 Segment 中的条目数（含权重）
  volatile long count;
  volatile long totalWeight;

  // 统计计数器
  volatile long hitCount;
  volatile long missCount;
  volatile long loadSuccessCount;
  volatile long loadExceptionCount;
  volatile long totalLoadTime;

  // 最大容量限制（从全局按比例分配）
  long maxSegmentWeight;

  // 清理锁，避免并发清理
  volatile boolean strictlyExpired;
}
```

### 4.1 Segment 的定位

```java
// LocalCache 中定位 Segment
int hash = hash(key);
int segmentIndex = (hash >>> segmentShift) & segmentMask;
Segment<K, V, E> segment = segments[segmentIndex];
```

Segment 的数量在创建时就固定了，为 `concurrencyLevel` 的向上取整的 2 的幂。这意味着并发度为 16 时，最多 16 个线程可同时写入不同 Segment 而不互斥。

### 4.2 表内定位

```java
// Segment 内部定位槽位
int slot = hash & (table.length() - 1);
E first = table.get(slot);
```

每个 Segment 内部的哈希表也是 2 的幂长度，用位运算代替取模，性能更优。

## 5. 写入流程全链路解析

### 5.1 put 方法

```java
// LocalCache.put
@Override
public V put(K key, V value) {
  checkNotNull(key);
  checkNotNull(value);
  int hash = hash(key);
  return segmentFor(hash).put(key, hash, value, false);
}
```

### 5.2 Segment.put 深度解析

```java
@Nullable
V put(K key, int hash, V value, boolean onlyIfAbsent) {
  lock();  // 加 Segment 级别的锁
  try {
    // 1. 预清理：处理引用队列和过期条目
    preWriteCleanup();

    // 2. 计算当前 Segment 的新容量需求
    int newCount = this.count + 1;
    if (newCount > (threshold = (int) (table.length() * 0.75))) {
      // 触发扩容
      expand();
      newCount = this.count + 1;
    }

    // 3. 定位链表头
    AtomicReferenceArray<E> table = this.table;
    int slot = hash & (table.length() - 1);
    E first = table.get(slot);

    // 4. 在链表中查找是否已存在
    for (E e = first; e != null; e = e.getNext()) {
      K entryKey = e.getKey();
      if (e.getHash() == hash
          && entryKey != null
          && keyEquivalence.equivalent(key, entryKey)) {
        // 已存在，覆盖旧值
        V oldValue = e.getValue();
        if (!onlyIfAbsent) {
          setValue(e, key, value, now);
        }
        // 记录写操作
        recordWrite(e);
        return oldValue;
      }
    }

    // 5. 不存在，创建新条目并插入链表头
    E newEntry = newEntry(key, hash, first);
    setValue(newEntry, key, value, now);
    table.set(slot, newEntry);
    newCount = this.count + 1;
    this.count = newCount;
    this.totalWeight += weigher.weigh(key, value);

    // 6. 触发淘汰（如果超过最大容量）
    evictEntries(newEntry);
    return null;
  } finally {
    unlock();  // 释放锁
    postWriteCleanup();
  }
}
```

写入流程关键点：

1. **加锁粒度**：只锁当前 Segment，不影响其他 Segment
2. **预清理**：每次写操作前先处理引用队列和过期条目，这是懒清理策略的核心
3. **扩容**：当条目数超过阈值（容量的 75%）时，数组翻倍扩容
4. **头插法**：新条目插入到链表头部，最近写入的条目在最前面

### 5.3 扩容机制

```java
void expand() {
  AtomicReferenceArray<E> oldTable = this.table;
  int oldCapacity = oldTable.length();
  if (oldCapacity >= MAXIMUM_CAPACITY) return;

  int newCapacity = oldCapacity << 1;  // 翻倍
  threshold = (int) (newCapacity * 0.75);

  AtomicReferenceArray<E> newTable = newEntryArray(newCapacity);
  int newMask = newCapacity - 1;

  // 迁移数据
  for (int oldSlot = 0; oldSlot < oldCapacity; oldSlot++) {
    E head = oldTable.get(oldSlot);
    if (head != null) {
      E next = head.getNext();
      int newSlot = head.getHash() & newMask;

      // 如果链表只有一个节点，直接迁移
      if (next == null) {
        newTable.set(newSlot, head);
      } else {
        // 多节点链表：拆分到两个新槽位
        E tail = head;
        int tailSlot = newSlot;
        E e = next;
        while (e != null) {
          int nextSlot = e.getHash() & newMask;
          if (nextSlot != tailSlot) {
            // 链表断点
            tailSlot = nextSlot;
            tail = e;
          }
          tail = e;
          e = e.getNext();
        }
        newTable.set(tailSlot, tail);
        // 前半段
        E e2 = head;
        while (e2 != tail) {
          int nextSlot2 = e2.getHash() & newMask;
          if (nextSlot2 != newSlot) {
            // 属于另一个新槽位
          }
          E next2 = e2.getNext();
          if (next2 == tail) {
            e2.setNext(null);
          }
          e2 = next2;
        }
        newTable.set(newSlot, head);
      }
    }
  }
  this.table = newTable;
}
```

扩容策略与 JDK7 的 `ConcurrentHashMap` 非常相似——利用 2 的幂特性，将一条链表拆分为两条，分配到新数组的不同槽位。这种做法的精妙之处在于：因为数组长度翻倍，hash 的最高有效位变成了新的低位掩码参与运算，所以同一条链表的节点必然分到原位置或原位置+旧容量的两个位置之一。

## 6. 读取流程与缓存加载

### 6.1 getIfPresent

```java
// LocalCache
@Override
public V getIfPresent(Object key) {
  int hash = hash(key);
  V value = segmentFor(hash).get(key, hash);
  if (value == null) {
    globalStatsCounter.recordMisses(1);
  } else {
    globalStatsCounter.recordHits(1);
  }
  return value;
}

// Segment.get
@Nullable
V get(Object key, int hash) {
  // 不加锁的读操作
  try {
    if (count != 0) {
      E e = getEntry(key, hash);
      if (e != null) {
        long now = ticker.read();
        V value = e.getValue();
        if (value == null) {
          // 值被 GC 回收（Weak/Soft 引用）
          tryDrainReferenceQueue();
        } else if (isExpired(e, now)) {
          // 过期
          recordExpiredRead(e);
        } else {
          // 命中
          recordRead(e, now);
          return value;
        }
      }
    }
    return null;
  } finally {
    // 读后清理
    postReadCleanup();
  }
}
```

读取流程不加锁，依赖 `volatile` 保证可见性。如果值被 GC 回收或已过期，则返回 null 并记录 miss。

### 6.2 get(key, loader)

这是 Guava Cache 最强大的方法之一——原子性的"不存在则加载"：

```java
V get(K key, int hash, CacheLoader<? super K, V> loader)
    throws ExecutionException {
  checkNotNull(key);
  checkNotNull(loader);
  try {
    // 1. 先尝试不加锁读
    if (count != 0) {
      E e = getEntry(key, hash);
      if (e != null) {
        long now = ticker.read();
        V value = e.getValue();
        if (value != null) {
          if (!isExpired(e, now) && !needsRefresh(e, now)) {
            recordRead(e, now);
            return value;
          }
          // 值存在但需要刷新或已过期
        }
      }
    }

    // 2. 加锁处理
    return lockedGetOrLoad(key, hash, loader);
  } catch (...) {
    // 异常处理
  }
}
```

`lockedGetOrLoad` 方法会在 Segment 锁保护下再次检查（双重检查锁定模式），如果确实不存在则调用 `CacheLoader.load()` 加载值。**关键设计：同一个 key 的加载会被锁定在同一 Segment 上，其他线程会阻塞等待，避免缓存击穿。**

### 6.3 LoadingCache 的批量加载

```java
ImmutableMap<K, V> getAll(Iterable<? extends K> keys) throws ExecutionException {
  // 按 Segment 分组
  Map<Segment<K, V, E>, Map<K, E>> groups = new HashMap<>();
  for (K key : keys) {
    int hash = hash(key);
    Segment<K, V, E> segment = segmentFor(hash);
    Map<K, E> group = groups.get(segment);
    if (group == null) {
      group = new LinkedHashMap<>();
      groups.put(segment, group);
    }
    group.put(key, null); // 占位
  }

  // 每个 Segment 独立加锁处理
  // 未命中的 key 交给 CacheLoader.loadAll 批量加载
  // loadAll 默认实现是循环调用 load
  ...
}
```

这种按 Segment 分组的设计确保了批量操作时锁的粒度最小化。

## 7. 淘汰策略实现

Guava Cache 使用 **LRU 变体（被称为 LIRS 的简化版）** 进行容量淘汰。但与经典 LRU 不同，它并不维护全局 LRU 链表，而是在每个 Segment 内部维护一个 **访问顺序队列**。

### 7.1 容量分配

```java
// LocalCache 构造函数中
long maxSegmentWeight = maximumWeight / segmentCount + 1;
for (int i = 0; i < segments.length; i++) {
  segments[i] = createSegment(
      this, maxSegmentWeight);
}
```

全局最大容量被均匀分配到各 Segment。每个 Segment 独立维护自己的容量上限。

### 7.2 evictEntries

```java
void evictEntries(E newEntry) {
  // 仅当可能需要淘汰时才执行
  if (!evicts()) return;

  while (totalWeight > maxSegmentWeight) {
    // 找到最近最少访问的条目
    E evictable = getNextEvictable();
    if (evictable == null) break;

    // 不能淘汰刚写入的条目
    if (evictable == newEntry) break;

    // 执行淘汰
    removeEntry(evictable, evictable.getHash(), RemovalCause.SIZE);
  }
}
```

### 7.3 访问顺序维护

每个 Entry 维护了 `previousInAccessQueue` 和 `nextInAccessQueue` 指针，构成一个双向链表（Access Queue）。每次读/写操作都会将该条目移到队尾：

```java
void recordRead(E entry, long now) {
  // 更新访问时间
  entry.setAccessTime(now);

  // 移动到访问队列尾部
  accessQueue.add(entry);  // 实际是 remove + addLast

  // 处理可能的过期清理
  maybeClearReferenceQueues();
}
```

淘汰时从队头取出（最近最少访问），这就是 LRU 的核心。但由于每个 Segment 独立维护，全局来看并非严格的 LRU，而是一种 **近似 LRU**，这是并发性能和精确性之间的折中。

## 8. 过期机制与时间管理

### 8.1 两种过期策略

```java
// 写后过期：从写入时刻开始计时
final long expireAfterWriteNanos;

// 读后过期：从最近一次访问时刻开始计时
final long expireAfterAccessNanos;
```

### 8.2 过期判断

```java
boolean isExpired(E entry, long now) {
  checkNotNull(entry);
  if (expiresAfterAccess()
      && (now - entry.getAccessTime()) >= expireAfterAccessNanos) {
    return true;
  }
  if (expiresAfterWrite()
      && (now - entry.getWriteTime()) >= expireAfterWriteNanos) {
    return true;
  }
  return false;
}
```

### 8.3 懒过期清理

Guava Cache **不使用后台线程** 定期扫描过期条目，而是采用懒清理策略：

```java
void postReadCleanup() {
  if ((readCount.incrementAndGet() & DRAIN_THRESHOLD) == 0) {
    cleanUp();
  }
}

void cleanUp() {
  long now = ticker.read();
  runLockedCleanup(now);
  runUnlockedCleanup();
}
```

每 64 次读操作触发一次清理。清理时处理：
- 引用队列中被 GC 回收的条目
- 过期条目
- 触发移除监听器

这种设计避免了定时线程的开销，但代价是过期条目可能不会被立即清理，直到下次读操作触发。如果设置了 `CacheLoader`，可以在读取时通过 `needsRefresh` 检查是否需要异步刷新。

### 8.4 refresh 机制

```java
boolean needsRefresh(E entry, long now) {
  return refreshes()
      && (now - entry.getWriteTime()) >= refreshNanos;
}
```

`refresh` 与 `expire` 的关键区别：
- **expire**：条目被移除，下次访问触发同步加载（阻塞）
- **refresh**：条目仍然有效，下次访问触发异步刷新（旧值立即返回），新值加载完成后替换

## 9. 回调与移除通知

### 9.1 RemovalListener

```java
public interface RemovalListener<K, V> {
  void onRemoval(RemovalNotification<K, V> notification);
}

public enum RemovalCause {
  EXPLICIT,    // 用户主动调用 invalidate
  REPLACED,    // 被新值覆盖
  COLLECTED,   // 键或值被 GC 回收（Weak/Soft 引用）
  EXPIRED,     // 过期
  SIZE         // 容量淘汰
}
```

### 9.2 通知机制

为避免回调阻塞写入操作，移除通知默认是 **异步** 的：

```java
// LocalCache 构造函数中
if (removalListener != null) {
  this.removalListener = removalListener;
  this.removalNotificationQueue = new ConcurrentLinkedQueue<>();
}
```

移除事件被放入 `ConcurrentLinkedQueue`，在 `runUnlockedCleanup` 中 **不加锁** 地依次调用 listener。这样回调逻辑不会影响缓存的并发性能。

```java
void processPendingNotifications() {
  RemovalNotification<K, V> notification;
  while ((notification = removalNotificationQueue.poll()) != null) {
    removalListener.onRemoval(notification);
  }
}
```

## 10. 并发安全与内存可见性

### 10.1 volatile 的使用

```java
// Segment 中的核心字段都是 volatile
volatile AtomicReferenceArray<E> table;
volatile long count;
volatile long totalWeight;
volatile long hitCount;
```

`volatile` 确保了：
- 读线程不需要加锁就能看到最新状态
- 写线程释放锁前的修改对后续获取锁的线程可见（happens-before 语义）

### 10.2 Count 的语义

`count` 是 Segment 中的条目数。在读操作中，首先检查 `count != 0`，如果为 0 则直接返回 null，避免空表查找。这是一个 **快速失败** 优化。

但 `count` 的更新并不总是精确的——在读路径中为了不加锁，某些状态更新可能会被推迟。Guava Cache 接受这种弱一致性以换取读取性能。

### 10.3 引用类型与 GC 协同

```java
enum Strength {
  STRONG {
    <K, V> ValueReference<K, V> referenceValue(
        Segment<K, V, ?> segment, K key, V value, int weight) {
      return (weight == 1)
          ? new StrongValueReference<>(value)
          : new WeightedStrongValueReference<>(value, weight);
    }
  },
  SOFT { ... new SoftValueReference<>(value, keyReferenceQueue) ... },
  WEAK { ... new WeakValueReference<>(value, keyReferenceQueue) ... }
}
```

当使用 `weakKeys()`、`softValues()` 等配置时，键值被包装为 `WeakReference` / `SoftReference`，并与 `ReferenceQueue` 关联。当 GC 回收了引用对象，对应的引用会被放入队列，后续在清理流程中被移除。

**注意**：使用 `weakKeys()` 时，键的比较从 `equals` 变为引用相等（`==`），因为弱引用语义下不存在 equals 的对象。这是一个常见的坑。

```java
// keyEquivalence 根据 Strength 选择
this.keyEquivalence = keyStrength.defaultEquivalence();
// STRONG -> equals
// WEAK/SOFT -> identity (==)
```

## 11. 面试题速查

**Q1: Guava Cache 的并发模型是什么？**
A: 采用分段锁（Segment）模型，类似 JDK7 的 ConcurrentHashMap。全局缓存被分为 N 个 Segment（默认 16），每个 Segment 独立加锁，支持 N 个线程并发写入不同 Segment。读操作不加锁，依赖 volatile 保证可见性。

**Q2: Guava Cache 的过期清理策略是什么？为什么不用定时线程？**
A: 采用懒清理策略。不使用后台定时线程扫描，而是在每次读写操作时按概率触发清理（每 64 次读触发一次），处理引用队列和过期条目。好处是避免线程开销，坏处是过期条目不会被立即清理。

**Q3: expireAfterWrite 和 expireAfterAccess 的区别？**
A: expireAfterWrite 从写入时刻计时，到期后条目失效，无论期间是否被访问过；expireAfterAccess 从最近一次访问时刻计时，每次访问都会重置计时器。可以同时配置两者，满足任一条件即过期。

**Q4: refresh 和 expire 有什么区别？**
A: expire 会使条目失效，下次访问需要同步加载（阻塞当前线程）。refresh 不会使条目失效，条目仍然返回旧值，但在下次访问时异步触发刷新，新值加载完成后替换旧值。refresh 适合在后台自动更新缓存而不阻塞用户请求。

**Q5: Guava Cache 如何防止缓存击穿？**
A: 在 `get(key, loader)` 方法中，使用 Segment 级别的锁进行双重检查。同一 key 的加载请求会被串行化在同一个 Segment 上，只有一个线程执行加载，其他线程等待结果。这样避免了大量线程同时穿透到后端加载相同 key。

**Q6: weakKeys() 会带来什么影响？**
A: 使用 weakKeys 后，键的比较从 `equals()` 变为引用相等（`==`），因为 GC 可能在任意时刻回收弱引用键，无法保证 equals 语义。这会导致两个 equals 相同但不是同一对象的 key 被视为不同的 key。如果 key 是 String 或 Integer 等，这可能导致缓存命中率下降。

**Q7: Guava Cache 的淘汰策略是 LRU 吗？**
A: 是近似 LRU。每个 Segment 独立维护一个访问顺序双向链表，淘汰时从链表头部（最近最少访问）取出。但由于 Segment 独立维护，全局来看并非严格 LRU——一个 Segment 中频繁访问的条目可能被淘汰，而另一个 Segment 中很少访问的条目仍然存在。

**Q8: RemovalListener 是同步还是异步执行的？**
A: 默认异步。移除事件被放入 ConcurrentLinkedQueue，在不加锁的清理流程中执行回调，避免阻塞写入操作。如果需要在移除时同步执行，可以使用 `RemovalListeners.asynchronous()` 自定义线程池。

**Q9: CacheBuilder 的 concurrencyLevel 设成多少合适？**
A: 默认 16。一般设置为应用并发读写的线程数。如果并发量很高且 key 分布均匀，可以适当增大；如果内存敏感，可以减小以降低每个 Segment 的固定开销。注意 Segment 数量一旦创建就不可变。

**Q10: Guava Cache 和 Caffeine 有什么区别？**
A: Caffeine 是 Guava Cache 的继任者，由同一作者开发。主要改进：(1) 用 Window TinyLFU 替代 LRU，命中率更高；(2) 用异步调度替代同步 Segment 锁，读路径完全无锁；(3) 支持异步加载和异步刷新；(4) 性能全面优于 Guava Cache。新项目推荐使用 Caffeine。

---

## 总结

Guava Cache 的源码设计是 Java 并发编程的经典教材。它通过分段锁实现高并发、通过懒清理避免线程开销、通过引用队列协同 GC、通过访问队列实现近似 LRU。每一个设计决策都是并发性能与精确性之间的精心折中。

理解了 Guava Cache，不仅能在面试中游刃有余，更能在实际项目中做出更好的缓存选型和调优决策。对于新项目，建议直接使用 Caffeine；但 Guava Cache 的设计思想依然值得深入学习。

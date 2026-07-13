# HashMap源码深度解析

> HashMap是Java集合框架中最核心的数据结构之一，也是面试中出现频率最高的源码题。本文基于JDK 1.8源码，从数据结构、初始化、put/get流程、扩容机制、并发问题等维度，逐行拆解HashMap的内部实现，帮助你真正理解它的设计哲学。

---

## 📋 目录

1. [整体数据结构](#1-整体数据结构)
2. [核心属性与常量](#2-核心属性与常量)
3. [构造方法分析](#3-构造方法分析)
4. [put方法全流程解析](#4-put方法全流程解析)
5. [hash方法与扰动函数](#5-hash方法与扰动函数)
6. [resize扩容机制详解](#6-resize扩容机制详解)
7. [get方法流程解析](#7-get方法流程解析)
8. [remove方法流程解析](#8-remove方法流程解析)
9. [并发安全问题](#9-并发安全问题)
10. [面试题速查](#10-面试题速查)

---

## 1. 整体数据结构

JDK 1.8的HashMap采用**数组 + 链表 + 红黑树**的复合结构。最外层是一个Node数组（table），每个槽位（bucket）存放一个链表头节点；当链表长度超过阈值且数组容量达标时，链表转换为红黑树以提升查询效率。

```java
// Node是HashMap的内部类，实现了Map.Entry
static class Node<K,V> implements Map.Entry<K,V> {
    final int hash;
    final K key;
    V value;
    Node<K,V> next;

    Node(int hash, K key, V value, Node<K,V> next) {
        this.hash = hash;
        this.key = key;
        this.value = value;
        this.next = next;
    }

    public final K getKey()        { return key; }
    public final V getValue()      { return value; }
    public final String toString() { return key + "=" + value; }

    public final int hashCode() {
        return Objects.hashCode(key) ^ Objects.hashCode(value);
    }

    public final V setValue(V newValue) {
        V oldValue = value;
        value = newValue;
        return oldValue;
    }

    public final boolean equals(Object o) {
        if (o == this)
            return true;
        if (o instanceof Map.Entry) {
            Map.Entry<?,?> e = (Map.Entry<?,?>)o;
            if (Objects.equals(key, e.getKey()) &&
                Objects.equals(value, e.getValue()))
                return true;
        }
        return false;
    }
}
```

当链表转红黑树后，节点类型从Node变为TreeNode：

```java
static final class TreeNode<K,V> extends LinkedHashMap.Entry<K,V> {
    TreeNode<K,V> parent;  // 红黑树父节点
    TreeNode<K,V> left;    // 左子节点
    TreeNode<K,V> right;   // 右子节点
    TreeNode<K,V> prev;    // 链表前驱节点（用于在删除时快速断开）
    boolean red;           // 节点颜色
    TreeNode(int hash, K key, V val, Node<K,V> next) {
        super(hash, key, val, next);
    }
}
```

整个结构可以用下图理解：

```
table数组
[0] -> null
[1] -> Node -> Node -> Node -> null (链表)
[2] -> TreeNode (红黑树根节点)
[3] -> null
...
[n] -> Node -> null
```

**核心设计思想**：通过hash函数将key分散到数组的不同槽位，理想情况下每个槽位只有一个节点，查询时间复杂度为O(1)。当hash冲突时，同一个槽位上的节点以链表形式串联，查询退化为O(n)。为避免极端情况下链表过长导致性能下降，JDK 1.8引入了红黑树，将最坏查询复杂度从O(n)优化到O(log n)。

---

## 2. 核心属性与常量

```java
public class HashMap<K,V> extends AbstractMap<K,V>
    implements Map<K,V>, Cloneable, Serializable {

    // 默认初始容量：16
    static final int DEFAULT_INITIAL_CAPACITY = 1 << 4; // aka 16

    // 最大容量：2的30次方
    static final int MAXIMUM_CAPACITY = 1 << 30;

    // 默认负载因子：0.75
    static final float DEFAULT_LOAD_FACTOR = 0.75f;

    // 链表转红黑树的阈值：链表长度达到8时尝试树化
    static final int TREEIFY_THRESHOLD = 8;

    // 红黑树退化为链表的阈值：节点数降至6时退化
    static final int UNTREEIFY_THRESHOLD = 6;

    // 树化的最小数组容量要求：数组容量必须达到64才允许树化
    static final int MIN_TREEIFY_CAPACITY = 64;

    // 哈希桶数组，长度总是2的幂
    transient Node<K,V>[] table;

    // entry缓存，用于entrySet()遍历
    transient Set<Map.Entry<K,V>> entrySet;

    // 当前元素个数
    transient int size;

    // 扩容阈值 = capacity * loadFactor
    int threshold;

    // 负载因子
    final float loadFactor;

    // 修改次数，用于fail-fast机制
    transient int modCount;
}
```

**关键常量解读**：

| 常量 | 值 | 含义 |
|------|------|------|
| DEFAULT_INITIAL_CAPACITY | 16 | 默认数组大小，必须是2的幂 |
| DEFAULT_LOAD_FACTOR | 0.75f | 空间与时间的折中 |
| TREEIFY_THRESHOLD | 8 | 链表树化阈值 |
| UNTREEIFY_THRESHOLD | 6 | 树退化阈值 |
| MIN_TREEIFY_CAPACITY | 64 | 树化的最小数组容量 |

**为什么负载因子是0.75？** 这是空间和时间成本的折中。如果调大（如1.0），数组利用率高但hash冲突概率增大，链表变长，查询变慢；如果调小（如0.5），冲突少查询快，但空间浪费多，频繁扩容。0.75在统计学上使桶中节点数的期望值遵循泊松分布，大部分桶只有0或1个节点。

**为什么链表转红黑树阈值是8？** 根据泊松分布概率模型，当负载因子为0.75时，一个桶中节点数达到8的概率约为0.00000006，几乎不会发生。设为8是为了在极端hash冲突时提供兜底保护，同时避免频繁的树化/退化操作。选择8而非7或6，是因为8和6之间留有缓冲区间（避免在阈值边界反复转换）。

---

## 3. 构造方法分析

HashMap有四个构造方法：

```java
// 构造方法1：指定初始容量和负载因子
public HashMap(int initialCapacity, float loadFactor) {
    if (initialCapacity < 0)
        throw new IllegalArgumentException("Illegal initial capacity: " + initialCapacity);
    if (initialCapacity > MAXIMUM_CAPACITY)
        initialCapacity = MAXIMUM_CAPACITY;
    if (loadFactor <= 0 || Float.isNaN(loadFactor))
        throw new IllegalArgumentException("Illegal load factor: " + loadFactor);
    this.loadFactor = loadFactor;
    // tableSizeFor将输入值转换为最接近的大于等于它的2的幂
    this.threshold = tableSizeFor(initialCapacity);
}

// 构造方法2：指定初始容量，使用默认负载因子
public HashMap(int initialCapacity) {
    this(initialCapacity, DEFAULT_LOAD_FACTOR);
}

// 构造方法3：全默认
public HashMap() {
    this.loadFactor = DEFAULT_LOAD_FACTOR; // 其他字段使用默认值0
}

// 构造方法4：从已有Map构造
public HashMap(Map<? extends K, ? extends V> m) {
    this.loadFactor = DEFAULT_LOAD_FACTOR;
    putMapEntries(m, false);
}
```

关键方法 `tableSizeFor`：

```java
static final int tableSizeFor(int cap) {
    int n = cap - 1;
    n |= n >>> 1;
    n |= n >>> 2;
    n |= n >>> 4;
    n |= n >>> 8;
    n |= n >>> 16;
    return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
}
```

这个方法的作用是找到大于等于输入值的最小2的幂。例如输入13，返回16；输入17，返回32。

**原理**：通过5次右移和按位或操作，将最高位的1之后的所有位都填充为1，最后加1就得到2的幂。先减1是为了处理输入本身就是2的幂的情况（如输入16，减1后为15，经过运算后为15，加1后为16）。

**注意**：构造方法中并没有真正创建table数组，只是设置了threshold值。table数组的延迟创建发生在第一次put操作时的resize方法中。这是**延迟初始化**设计模式的应用。

---

## 4. put方法全流程解析

```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}

final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
               boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;

    // 步骤1：如果table为空或长度为0，则初始化table
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;

    // 步骤2：计算index，如果该位置为null，直接放入新节点
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);
    else {
        // 步骤3：该位置已有节点，处理hash冲突
        Node<K,V> e; K k;

        // 3.1：如果key完全相同（hash相等且key equals），准备覆盖
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;
        // 3.2：如果是红黑树节点，调用树节点的put方法
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
        // 3.3：是链表节点，遍历链表
        else {
            for (int binCount = 0; ; ++binCount) {
                if ((e = p.next) == null) {
                    // 到达链表尾部，插入新节点（尾插法）
                    p.next = newNode(hash, key, value, null);
                    // 链表长度达到树化阈值，尝试树化
                    if (binCount >= TREEIFY_THRESHOLD - 1) // -1 for 1st
                        treeifyBin(tab, hash);
                    break;
                }
                // 链表中找到相同key，准备覆盖
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    break;
                p = e;
            }
        }

        // 步骤4：如果找到了已存在的key，覆盖旧值并返回旧值
        if (e != null) { // existing mapping for key
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            afterNodeAccess(e); // LinkedHashMap的回调，HashMap中为空实现
            return oldValue;
        }
    }

    // 步骤5：修改次数+1
    ++modCount;

    // 步骤6：元素个数+1，如果超过阈值则扩容
    if (++size > threshold)
        resize();

    afterNodeInsertion(evict); // LinkedHashMap的回调，HashMap中为空实现
    return null;
}
```

**put流程总结**：

1. 检查table是否初始化，未初始化则调用resize()初始化
2. 通过 `(n-1) & hash` 计算槽位index，如果槽位为空，直接放入新节点
3. 如果槽位非空：
   - key相同 → 准备覆盖
   - 是红黑树 → 调用`putTreeVal`插入树节点
   - 是链表 → 尾插法插入，插入后检查是否需要树化
4. 如果找到已存在的key，覆盖旧值
5. size+1，检查是否需要扩容

**注意JDK 1.8使用尾插法而非JDK 1.7的头插法**。头插法在多线程扩容时可能导致链表成环，造成死循环。尾插法虽然不能完全解决并发问题，但避免了环形链表。

---

## 5. hash方法与扰动函数

```java
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}
```

这个方法叫做"扰动函数"。它将key的hashCode的高16位与低16位做异或运算。

**为什么需要扰动？** 计算数组下标的公式是 `(n-1) & hash`。当n较小时（如16），`n-1`的二进制只有低4位为1（1111），高位全是0，这意味着hashCode的高位完全被忽略了。如果多个key的hashCode仅在高位不同，它们的hash值虽然不同，但计算出的数组下标却相同，造成严重hash冲突。

扰动函数通过将高位"混合"到低位，让高位信息也参与下标计算，减少冲突概率。

**示例**：假设hashCode = 0x12345678，n = 16

```
hashCode:  0001 0010 0011 0100 0101 0110 0111 1000
h >>> 16:  0000 0000 0000 0000 0001 0010 0011 0100
异或结果:   0001 0010 0011 0100 0100 0100 0100 1100
& (n-1):   0000 0000 0000 0000 0000 0000 0000 1100  → index = 12
```

如果没有扰动，直接用原始hashCode & 15 = 1000 = 8。扰动后变为12，充分利用了高位信息。

---

## 6. resize扩容机制详解

resize方法是HashMap中最复杂的方法之一，它负责初始化table数组和扩容两个职责。

```java
final Node<K,V>[] resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;

    // === 第一部分：计算新容量和新阈值 ===

    if (oldCap > 0) {
        // 数组已经初始化
        if (oldCap >= MAXIMUM_CAPACITY) {
            // 已达最大容量，不再扩容，阈值设为Integer.MAX_VALUE
            threshold = Integer.MAX_VALUE;
            return oldTab;
        }
        // 正常扩容：容量翻倍
        else if ((newCap = oldCap << 1) < MAXIMUM_CAPACITY &&
                 oldCap >= DEFAULT_INITIAL_CAPACITY)
            newThr = oldThr << 1; // 阈值也翻倍
    }
    else if (oldThr > 0) // 初始容量通过构造方法设置了threshold
        newCap = oldThr;
    else {               // 全默认构造，第一次put时走到这里
        newCap = DEFAULT_INITIAL_CAPACITY;  // 16
        newThr = (int)(DEFAULT_LOAD_FACTOR * DEFAULT_INITIAL_CAPACITY); // 12
    }

    if (newThr == 0) {
        // 根据新容量计算新阈值
        float ft = (float)newCap * loadFactor;
        newThr = (newCap < MAXIMUM_CAPACITY && ft < MAXIMUM_CAPACITY ?
                  (int)ft : Integer.MAX_VALUE);
    }
    threshold = newThr;

    // === 第二部分：创建新数组并迁移数据 ===

    @SuppressWarnings({"rawtypes","unchecked"})
    Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
    table = newTab;

    if (oldTab != null) {
        for (int j = 0; j < oldCap; ++j) {
            Node<K,V> e;
            if ((e = oldTab[j]) != null) {
                oldTab[j] = null; // 帮助GC

                if (e.next == null)
                    // 槽位只有一个节点，直接重新计算位置
                    newTab[e.hash & (newCap - 1)] = e;
                else if (e instanceof TreeNode)
                    // 红黑树节点，调用split方法重新分配
                    ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
                else { // 链表节点，preserve order（保持原有顺序）
                    // 将链表拆分为两个子链表
                    Node<K,V> loHead = null, loTail = null; // 低位链表
                    Node<K,V> hiHead = null, hiTail = null; // 高位链表
                    Node<K,V> next;
                    do {
                        next = e.next;
                        // 关键判断：oldCap的bit位在hash中是否为1
                        if ((e.hash & oldCap) == 0) {
                            // 低位链表：新位置 = 原位置
                            if (loTail == null)
                                loHead = e;
                            else
                                loTail.next = e;
                            loTail = e;
                        }
                        else {
                            // 高位链表：新位置 = 原位置 + oldCap
                            if (hiTail == null)
                                hiHead = e;
                            else
                                hiTail.next = e;
                            hiTail = e;
                        }
                    } while ((e = next) != null);

                    // 低位链表放到 newTab[j]
                    if (loTail != null) {
                        loTail.next = null;
                        newTab[j] = loHead;
                    }
                    // 高位链表放到 newTab[j + oldCap]
                    if (hiTail != null) {
                        hiTail.next = null;
                        newTab[j + oldCap] = hiHead;
                    }
                }
            }
        }
    }
    return newTab;
}
```

**扩容时的链表拆分原理**：

这是JDK 1.8扩容最精妙的设计。扩容后数组容量翻倍，元素的新位置只有两种可能：

- **原位置**：`(e.hash & oldCap) == 0`，即hash在oldCap位为0
- **原位置 + oldCap**：`(e.hash & oldCap) != 0`，即hash在oldCap位为1

**推导**：假设oldCap = 16（0001 0000），扩容后newCap = 32（0010 0000）。
- 旧下标 = `hash & 15`（0000 1111），只看低4位
- 新下标 = `hash & 31`（0001 1111），看低5位
- 区别就在于第5位（即oldCap对应的那一位）
- 如果该位为0，新下标 = 旧下标；如果该位为1，新下标 = 旧下标 + 16

这个设计避免了重新计算每个元素的hash，只需判断一个bit位，效率极高。

---

## 7. get方法流程解析

```java
public V get(Object key) {
    Node<K,V> e;
    return (e = getNode(hash(key), key)) == null ? null : e.value;
}

final Node<K,V> getNode(int hash, Object key) {
    Node<K,V>[] tab; Node<K,V> first, e; int n; K k;

    // 步骤1：table非空且对应槽位有节点
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (first = tab[(n - 1) & hash]) != null) {

        // 步骤2：检查第一个节点是否就是目标
        if (first.hash == hash &&
            ((k = first.key) == key || (key != null && key.equals(k))))
            return first;

        // 步骤3：第一个节点不是目标，检查是否有后续节点
        if ((e = first.next) != null) {
            // 3.1：如果是红黑树，调用树查找
            if (first instanceof TreeNode)
                return ((TreeNode<K,V>)first).getTreeNode(hash, key);
            // 3.2：遍历链表查找
            do {
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    return e;
            } while ((e = e.next) != null);
        }
    }
    return null;
}
```

**get流程总结**：

1. 通过hash计算槽位index
2. 检查槽位第一个节点：hash相等且key equals → 返回
3. 第一个节点不是目标：
   - 红黑树 → `getTreeNode`查找，O(log n)
   - 链表 → 遍历链表，O(n)

注意比较时先比较hash（int比较，快），hash相等才调用equals方法（可能较慢，如String的equals需要逐字符比较）。这是一个常见的性能优化技巧。

---

## 8. remove方法流程解析

```java
public V remove(Object key) {
    Node<K,V> e;
    return (e = removeNode(hash(key), key, null, false, true)) == null ?
        null : e.value;
}

final Node<K,V> removeNode(int hash, Object key, Object value,
                           boolean matchValue, boolean movable) {
    Node<K,V>[] tab; Node<K,V> p; int n, index;

    // 步骤1：定位到槽位
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (p = tab[index = (n - 1) & hash]) != null) {
        Node<K,V> node = null, e; K k; V v;

        // 步骤2：检查第一个节点
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            node = p;
        else if ((e = p.next) != null) {
            // 步骤3：红黑树或链表查找
            if (p instanceof TreeNode)
                node = ((TreeNode<K,V>)p).getTreeNode(hash, key);
            else {
                do {
                    if (e.hash == hash &&
                        ((k = e.key) == key ||
                         (key != null && key.equals(k)))) {
                        node = e;
                        break;
                    }
                    p = e;
                } while ((e = e.next) != null);
            }
        }

        // 步骤4：找到节点后执行删除
        if (node != null && (!matchValue || (v = node.value) == value ||
                             (value != null && value.equals(v)))) {
            if (node instanceof TreeNode)
                // 红黑树删除
                ((TreeNode<K,V>)node).removeTreeNode(this, tab, movable);
            else if (node == p)
                // 删除的是链表头节点，直接将next设为槽位头
                tab[index] = node.next;
            else
                // 删除链表中间/尾部节点，修改前驱的next指针
                p.next = node.next;

            ++modCount;
            --size;
            afterNodeRemoval(node); // LinkedHashMap回调
            return node;
        }
    }
    return null;
}
```

remove方法在删除链表节点时，需要记录前驱节点（p），因为单链表删除需要修改前驱的next指针。如果删除的是头节点，直接将数组槽位指向第二个节点。

---

## 9. 并发安全问题

HashMap是**线程不安全**的。在多线程环境下使用HashMap可能出现以下问题：

### 9.1 JDK 1.7中的死循环

JDK 1.7在扩容时使用头插法迁移链表，多线程同时扩容可能导致链表形成环形结构，后续get操作陷入死循环。虽然JDK 1.8改为尾插法避免了这个问题，但HashMap仍然不适合多线程环境。

### 9.2 JDK 1.8中的数据丢失

两个线程同时执行putVal，可能同时判断槽位为null并同时写入，导致其中一个线程的数据被覆盖。

```java
// 两个线程同时执行到这一行
if ((p = tab[i = (n - 1) & hash]) == null)
    tab[i] = newNode(hash, key, value, null); // 可能覆盖另一个线程的写入
```

### 9.3 size统计不准确

size++不是原子操作，多线程下会导致计数不准确。

### 9.4 解决方案

| 方案 | 适用场景 | 性能 |
|------|----------|------|
| ConcurrentHashMap | 高并发读写 | 高（分段锁/CAS） |
| Collections.synchronizedMap | 低并发 | 低（全局锁） |
| Hashtable | 不推荐 | 低（全局锁） |

---

## 10. 面试题速查

**Q1: HashMap的底层数据结构是什么？**
> JDK 1.8采用数组 + 链表 + 红黑树。数组是Node[]，每个槽位是链表头节点。链表长度≥8且数组容量≥64时转为红黑树；节点数≤6时退化为链表。

**Q2: HashMap的默认初始容量为什么是16？**
> 16是2的幂，便于通过位运算`(n-1)&hash`计算下标。选择16而非8或32，是在内存占用和冲突概率间的平衡。太小容易频繁扩容，太大浪费内存。

**Q3: 为什么容量必须是2的幂？**
> 因为HashMap用`(n-1) & hash`替代`hash % n`来计算下标。当n是2的幂时，`hash % n == hash & (n-1)`，位运算比取模运算快得多。同时，`n-1`的二进制全为1，能保证hash的低位均匀参与计算。

**Q4: HashMap扩容机制是怎样的？**
> 当size > threshold时触发扩容。容量翻倍（oldCap << 1），阈值也翻倍。扩容时，通过判断`(e.hash & oldCap)`将链表拆分为两条：原位置链表和原位置+oldCap链表，无需重新计算hash。

**Q5: HashMap为什么线程不安全？**
> 多线程下可能出现数据覆盖（同时put到同一槽位）、size统计不准、扩容时数据丢失等问题。JDK 1.7还可能因头插法扩容导致死循环。应使用ConcurrentHashMap替代。

**Q6: HashMap的key可以是null吗？**
> 可以。null的hash值固定为0，所以null key总是存储在table[0]的位置。但只能有一个null key。

**Q7: HashMap和Hashtable的区别？**
> ①HashMap线程不安全，Hashtable线程安全（方法加synchronized）；②HashMap允许null key/value，Hashtable不允许；③HashMap初始容量16，Hashtable初始容量11；④HashMap扩容翻倍，Hashtable扩容为2n+1。

**Q8: HashMap的loadFactor能设为1吗？**
> 可以但不推荐。设为1意味着数组满了才扩容，hash冲突概率大幅增加，链表变长，查询性能下降。0.75是官方推荐的最佳实践。

**Q9: 为什么JDK 1.8把头插法改成尾插法？**
> 头插法在多线程扩容时可能导致链表成环，get时死循环。尾插法保持链表原有顺序，避免了环形链表问题。但HashMap仍非线程安全。

**Q10: HashMap遍历时有几种方式？哪种最高效？**
> 四种方式：①entrySet()遍历；②keySet()遍历；③forEach + Lambda；④Iterator遍历。entrySet()最高效，因为它一次取出key和value；keySet()需要额外调用get(value)方法，多一次hash查找。
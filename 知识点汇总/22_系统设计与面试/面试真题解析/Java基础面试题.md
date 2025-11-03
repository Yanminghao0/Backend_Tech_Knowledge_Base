# Java基础面试题

> 整理Java基础高频面试题及详细解答

## 📋 目录
- [集合框架](#集合框架)
- [并发编程](#并发编程)
- [JVM相关](#jvm相关)
- [Java8新特性](#java8新特性)
- [异常处理](#异常处理)
- [反射与动态代理](#反射与动态代理)
- [IO与NIO](#io与nio)
- [Java基础语法](#java基础语法)

---

## 集合框架

### Q1: HashMap的底层实现原理？（⭐⭐⭐⭐⭐）

**回答要点**：
```
数据结构（JDK 1.8）：
  数组 + 链表 + 红黑树

核心参数：
  - 初始容量：16
  - 负载因子：0.75
  - 树化阈值：8
  - 树退化阈值：6
  - 树化最小数组长度：64
  - 扩容阈值：容量 × 负载因子

put过程：
  1. 计算hash值：(key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16)
  2. 定位数组下标：(n - 1) & hash
  3. 处理冲突：
     - 链表长度 < 8：链表存储
     - 链表长度 >= 8 且数组长度 >= 64：转红黑树
     - 链表长度 >= 8 但数组长度 < 64：扩容
  4. 扩容：容量翻倍，重新hash
```

**详细解析**：

**1. 为什么使用 (h = key.hashCode()) ^ (h >>> 16)？**
```java
// 扰动函数
static final int hash(Object key) {
    int h;
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}

原因：
- hashCode是32位
- 数组长度通常不大（比如16、32）
- 直接用hashCode，高16位基本用不上
- 异或运算让高16位也参与运算
- 减少hash冲突 ✅
```

**2. 为什么数组长度必须是2的幂？**
```
优势：
1. 取模运算优化：
   hash % length  →  hash & (length - 1)
   位运算比取模快很多 ✅

2. 扩容优化：
   - 扩容后，元素位置要么不变
   - 要么移动到 原位置+oldCap
   - 不需要重新计算hash
   
示例（length=16扩容到32）：
  hash = 21 (10101)
  
  16-1 = 15 (01111)
  21 & 15 = 5
  
  32-1 = 31 (11111)
  21 & 31 = 21
  
  差值: 21 - 5 = 16 = oldCap
```

**3. 为什么负载因子是0.75？**
```
权衡：
- 负载因子太小（如0.5）：
  ✅ hash冲突少
  ❌ 空间利用率低
  ❌ 频繁扩容
  
- 负载因子太大（如1.0）：
  ✅ 空间利用率高
  ❌ hash冲突多
  ❌ 链表长，查询慢

0.75是权衡的结果：
  - 空间利用率75%
  - 冲突概率可接受
  - 泊松分布计算得出最优值
```

**4. JDK 1.7 vs JDK 1.8对比**：
```
JDK 1.7：
  - 数组 + 链表
  - 头插法（并发会导致循环链表）
  - 先扩容后插入
  
JDK 1.8：
  - 数组 + 链表 + 红黑树
  - 尾插法（避免循环链表）
  - 先插入后扩容
  - 链表长度>8且数组长度>=64时树化
```

**追问：为什么树化阈值是8？**
```
泊松分布计算：
- 在理想情况下（hash函数完美）
- 链表长度为8的概率是 0.00000006
- 几乎不可能出现
- 如果出现了，说明hash冲突严重
- 此时树化可以优化性能

为什么退化阈值是6？
- 避免频繁树化和退化
- 8和6之间有缓冲区
- 如果是7，可能来回转换
```

**代码示例**：
```java
public class HashMapDemo {
    public static void main(String[] args) {
        Map<String, Integer> map = new HashMap<>();
        
        // put操作
        map.put("apple", 1);
        map.put("banana", 2);
        
        // get操作
        Integer value = map.get("apple");  // 1
        
        // 遍历
        for (Map.Entry<String, Integer> entry : map.entrySet()) {
            System.out.println(entry.getKey() + " = " + entry.getValue());
        }
    }
}
```

---

### Q2: ConcurrentHashMap的实现原理？（⭐⭐⭐⭐⭐）

**JDK 1.7实现**：
```
数据结构：
  Segment数组 + HashEntry数组 + 链表

Segment：
  - 继承ReentrantLock
  - 分段锁机制
  - 默认16个Segment
  - 并发度 = Segment数量

特点：
  ✅ 锁粒度比Hashtable小
  ✅ 支持16个线程并发写
  ❌ Segment数组不可扩容
  ❌ 查询需要两次hash
```

**JDK 1.8实现**：
```
数据结构：
  数组 + 链表 + 红黑树（类似HashMap）

锁机制：
  - CAS + synchronized
  - 锁链表/红黑树的头节点
  - 锁粒度更小（Node级别）

put过程：
  1. 计算hash值
  2. 如果数组为空，初始化（CAS）
  3. 如果桶为空，CAS插入
  4. 如果桶不为空，synchronized加锁插入
  5. 如果链表长度>=8，树化
  6. 扩容

get过程：
  - 不加锁
  - volatile保证可见性
```

**详细源码分析**：
```java
// put方法核心逻辑
final V putVal(K key, V value, boolean onlyIfAbsent) {
    int hash = spread(key.hashCode());
    
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        
        // 1. 如果数组为空，初始化
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();
        
        // 2. 如果桶为空，CAS插入
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break;
        }
        
        // 3. 如果在扩容，帮助扩容
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);
        
        // 4. 否则，synchronized加锁插入
        else {
            V oldVal = null;
            synchronized (f) {  // 锁住头节点
                // 插入逻辑...
            }
        }
    }
    
    addCount(1L, binCount);
    return null;
}

// get方法（无锁）
public V get(Object key) {
    Node<K,V>[] tab; Node<K,V> e, p; int n, eh; K ek;
    int h = spread(key.hashCode());
    
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (e = tabAt(tab, (n - 1) & h)) != null) {
        
        // 直接读取（volatile）
        if ((eh = e.hash) == h) {
            if ((ek = e.key) == key || (ek != null && key.equals(ek)))
                return e.val;
        }
        // 树节点
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

**为什么get不需要加锁？**
```java
static class Node<K,V> implements Map.Entry<K,V> {
    final int hash;
    final K key;
    volatile V val;      // volatile保证可见性
    volatile Node<K,V> next;  // volatile保证可见性
}

原因：
1. val和next都是volatile
2. 写操作立即可见
3. 读操作能看到最新值
4. 不需要加锁 ✅
```

**size()方法如何实现？**
```java
// JDK 1.7：锁所有Segment统计
public int size() {
    final Segment<K,V>[] segments = this.segments;
    long sum = 0;
    
    // 尝试3次无锁统计
    for (int k = 0; k < RETRIES_BEFORE_LOCK; ++k) {
        sum = 0;
        int mcsum = 0;
        for (Segment<K,V> seg : segments) {
            sum += seg.count;
            mcsum += seg.modCount;
        }
        // 如果统计期间没有修改，返回
        if (mcsum == lastMcsum)
            return (int)sum;
        lastMcsum = mcsum;
    }
    
    // 否则锁住所有Segment统计
    for (Segment<K,V> seg : segments)
        seg.lock();
    try {
        for (Segment<K,V> seg : segments)
            sum += seg.count;
    } finally {
        for (Segment<K,V> seg : segments)
            seg.unlock();
    }
    return (int)sum;
}

// JDK 1.8：baseCount + CounterCell数组
private transient volatile long baseCount;
private transient volatile CounterCell[] counterCells;

public int size() {
    long n = sumCount();
    return ((n < 0L) ? 0 :
            (n > (long)Integer.MAX_VALUE) ? Integer.MAX_VALUE :
            (int)n);
}

final long sumCount() {
    CounterCell[] as = counterCells; CounterCell a;
    long sum = baseCount;
    if (as != null) {
        for (int i = 0; i < as.length; ++i) {
            if ((a = as[i]) != null)
                sum += a.value;
        }
    }
    return sum;
}
```

---

### Q3: HashMap vs ConcurrentHashMap vs Hashtable？（⭐⭐⭐⭐⭐）

**详细对比**：

| 特性 | HashMap | ConcurrentHashMap | Hashtable |
|------|---------|-------------------|-----------|
| 线程安全 | ❌ 否 | ✅ 是 | ✅ 是 |
| 性能 | 🚀 最快 | ⚡ 快 | 🐢 慢 |
| 锁机制 | 无锁 | CAS + synchronized（1.8） | synchronized锁整表 |
| null key | ✅ 允许1个 | ❌ 不允许 | ❌ 不允许 |
| null value | ✅ 允许 | ❌ 不允许 | ❌ 不允许 |
| 初始容量 | 16 | 16 | 11 |
| 扩容因子 | 0.75 | 0.75 | 0.75 |
| 扩容方式 | 2倍 | 2倍 | 2倍+1 |
| 迭代器 | fail-fast | 弱一致性 | fail-fast |

**为什么ConcurrentHashMap不允许null？**
```java
// Doug Lea的解释：
// null值的二义性问题

// HashMap：单线程，可以区分
map.put("key", null);  // 存null
map.get("key");        // 返回null：到底是存的null还是不存在？
map.containsKey("key"); // 可以判断 ✅

// ConcurrentHashMap：多线程，无法区分
map.get("key");  // 返回null
// 1. key对应的value是null？
// 2. key不存在？
// 3. 刚被其他线程删除？
// 无法判断！❌

// 如果允许null，需要：
if (map.containsKey("key")) {  // 线程A检查
    // 线程B此时删除了key
    Object value = map.get("key");  // 可能返回null
    // 产生歧义！
}

// 因此禁止null，避免二义性
```

**使用场景选择**：
```
HashMap：
  ✅ 单线程环境
  ✅ 无并发需求
  ✅ 性能要求高

ConcurrentHashMap：
  ✅ 多线程环境
  ✅ 高并发读写
  ✅ 无锁或细粒度锁

Hashtable：
  ❌ 不推荐使用
  ❌ 性能差
  ❌ 被ConcurrentHashMap替代
```

---

### Q4: ArrayList vs LinkedList？（⭐⭐⭐⭐）

**数据结构对比**：
```java
// ArrayList：动态数组
public class ArrayList<E> {
    transient Object[] elementData;  // 底层数组
    private int size;                // 元素个数
    
    private static final int DEFAULT_CAPACITY = 10;  // 默认容量
}

// LinkedList：双向链表
public class LinkedList<E> {
    transient int size = 0;
    transient Node<E> first;  // 头节点
    transient Node<E> last;   // 尾节点
    
    private static class Node<E> {
        E item;
        Node<E> next;
        Node<E> prev;
    }
}
```

**性能对比**：

| 操作 | ArrayList | LinkedList |
|------|-----------|------------|
| get(i) | O(1) ✅ | O(n) |
| add(e) | O(1)* | O(1) ✅ |
| add(i,e) | O(n) | O(n) |
| remove(i) | O(n) | O(n) |
| contains(e) | O(n) | O(n) |
| 内存占用 | 低 ✅ | 高（Node对象） |

*ArrayList的add(e)：
- 一般情况O(1)
- 扩容时O(n)
- 均摊复杂度O(1)

**ArrayList扩容机制**：
```java
// JDK 1.8
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);  // 1.5倍
    
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;
    
    if (newCapacity - MAX_ARRAY_SIZE > 0)
        newCapacity = hugeCapacity(minCapacity);
    
    elementData = Arrays.copyOf(elementData, newCapacity);
}

扩容过程：
1. 创建新数组（1.5倍）
2. 复制元素
3. 替换旧数组

为什么是1.5倍？
- 太小（如1.2倍）：频繁扩容
- 太大（如2倍）：空间浪费
- 1.5倍是权衡结果
```

**使用场景**：
```
ArrayList：
  ✅ 随机访问多
  ✅ 查询为主
  ✅ 内存敏感
  ❌ 插入删除少
  
LinkedList：
  ✅ 频繁插入删除
  ✅ 队列/栈操作
  ❌ 随机访问少
  
实际开发：
  - 90%场景用ArrayList
  - LinkedList用于特定场景（队列、LRU缓存等）
```

---

### Q5: HashSet vs TreeSet vs LinkedHashSet？（⭐⭐⭐）

**底层实现**：
```java
// HashSet：基于HashMap
public class HashSet<E> {
    private transient HashMap<E,Object> map;
    private static final Object PRESENT = new Object();
    
    public boolean add(E e) {
        return map.put(e, PRESENT) == null;
    }
}

// TreeSet：基于TreeMap（红黑树）
public class TreeSet<E> {
    private transient NavigableMap<E,Object> m;
}

// LinkedHashSet：基于LinkedHashMap
public class LinkedHashSet<E> {
    // 继承HashSet，但创建LinkedHashMap
}
```

**特性对比**：

| 特性 | HashSet | TreeSet | LinkedHashSet |
|------|---------|---------|---------------|
| 底层结构 | HashMap | 红黑树 | HashMap+双向链表 |
| 有序性 | ❌ 无序 | ✅ 排序 | ✅ 插入顺序 |
| 性能 | O(1) ✅ | O(log n) | O(1) |
| null元素 | ✅ 允许1个 | ❌ 不允许 | ✅ 允许1个 |
| 使用场景 | 去重 | 排序+去重 | 保序+去重 |

---

## 并发编程

### Q6: synchronized的实现原理？（⭐⭐⭐⭐⭐）

**三种使用方式**：
```java
// 1. 修饰实例方法（锁this对象）
public synchronized void instanceMethod() {
    // 业务逻辑
}

// 2. 修饰静态方法（锁Class对象）
public static synchronized void staticMethod() {
    // 业务逻辑
}

// 3. 修饰代码块（锁指定对象）
public void blockMethod() {
    synchronized (this) {
        // 业务逻辑
    }
}
```

**字节码层面**：
```java
public void method() {
    synchronized (this) {
        System.out.println("sync");
    }
}

// 字节码
public void method();
  Code:
    0: aload_0
    1: dup
    2: astore_1
    3: monitorenter        // 获取锁
    4: getstatic
    7: ldc
    9: invokevirtual
   12: aload_1
   13: monitorexit         // 释放锁
   14: goto 22
   17: astore_2
   18: aload_1
   19: monitorexit         // 异常也要释放锁
   20: aload_2
   21: athrow
   22: return
```

**锁升级过程**：
```
无锁 → 偏向锁 → 轻量级锁 → 重量级锁

偏向锁（Biased Locking）：
  - 大多数情况锁不存在竞争
  - 总是由同一线程获得
  - 在对象头记录线程ID
  - 下次该线程进入不需要CAS
  
轻量级锁（Lightweight Locking）：
  - 有竞争但竞争不激烈
  - 使用CAS避免使用互斥量
  - 自旋等待
  
重量级锁（Heavyweight Locking）：
  - 竞争激烈
  - 使用操作系统互斥量（Mutex）
  - 阻塞等待
```

**对象头结构**：
```
Hotspot虚拟机对象头（Mark Word）：

32位JVM：
|-----------------------------------------------------------------------|
|  锁状态     | 25bit | 4bit | 1bit(偏向锁) | 2bit(锁标志位) |
|-----------------------------------------------------------------------|
| 无锁       | hashcode      | age  |    0         |     01        |
| 偏向锁     | 线程ID   epoch | age  |    1         |     01        |
| 轻量级锁   |     指向栈中锁记录的指针        |     00        |
| 重量级锁   |     指向monitor的指针           |     10        |
| GC标记     |                 空              |     11        |
|-----------------------------------------------------------------------|
```

**锁优化技术**：
```
1. 锁消除（Lock Elimination）：
   - JIT编译时分析
   - 检测不可能存在竞争的锁
   - 消除锁

2. 锁粗化（Lock Coarsening）：
   - 连续加锁解锁合并
   - 减少加锁次数

3. 适应性自旋（Adaptive Spinning）：
   - 自旋次数动态调整
   - 根据历史记录预测

4. 锁分离：
   - ReadWriteLock
   - 读锁和写锁分离
```

---

### Q7: volatile的原理和使用？（⭐⭐⭐⭐⭐）

**两个特性**：
```
1. 可见性（Visibility）：
   - 写操作立即刷新到主内存
   - 读操作从主内存读取
   
2. 有序性（Ordering）：
   - 禁止指令重排序
   - 通过内存屏障实现
   
❌ 不保证原子性！
```

**内存屏障**：
```
volatile写操作：
  StoreStore屏障
  volatile写
  StoreLoad屏障   ← 最耗时的屏障

volatile读操作：
  volatile读
  LoadLoad屏障
  LoadStore屏障
```

**经典案例：双重检查锁（DCL）**：
```java
public class Singleton {
    // 必须volatile！
    private volatile static Singleton instance;
    
    public static Singleton getInstance() {
        if (instance == null) {          // 第一次检查（无锁）
            synchronized (Singleton.class) {
                if (instance == null) {  // 第二次检查（有锁）
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}

为什么需要volatile？

new Singleton()不是原子操作，分为3步：
  1. memory = allocate()   // 分配内存
  2. ctorInstance(memory)  // 初始化对象
  3. instance = memory     // 设置instance指向内存

可能重排序为：1 → 3 → 2

线程A执行 instance = new Singleton()
  1. 分配内存
  2. instance指向内存（此时对象未初始化！）
  3. 初始化对象 ← 还没执行

线程B执行 getInstance()
  - instance不为null（但未初始化）
  - 直接返回
  - 使用未初始化的对象 ❌

volatile禁止重排序：
  - 保证 1 → 2 → 3 的顺序
  - instance要么为null，要么是完整对象 ✅
```

**volatile vs synchronized**：

| 特性 | volatile | synchronized |
|------|----------|--------------|
| 原子性 | ❌ 不保证 | ✅ 保证 |
| 可见性 | ✅ 保证 | ✅ 保证 |
| 有序性 | ✅ 保证 | ✅ 保证 |
| 阻塞 | ❌ 不阻塞 | ✅ 可能阻塞 |
| 适用场景 | 状态标志 | 复合操作 |

**使用场景**：
```java
// ✅ 场景1：状态标志
private volatile boolean flag = false;

public void setFlag() {
    flag = true;
}

public void doSomething() {
    while (!flag) {
        // 等待
    }
}

// ✅ 场景2：单例DCL
private volatile static Singleton instance;

// ❌ 场景3：计数器（不适用）
private volatile int count = 0;

public void increment() {
    count++;  // 不是原子操作！
    // count++ = read + add + write
    // volatile不能保证原子性
}

// 应该用：
private AtomicInteger count = new AtomicInteger(0);
```

---

### Q8: synchronized vs Lock？（⭐⭐⭐⭐⭐）

**详细对比**：

|  | synchronized | ReentrantLock |
|--|--------------|---------------|
| 层面 | JVM层面（字节码monitorenter/monitorexit）| Java API层面（java.util.concurrent） |
| 加锁 | 自动 ✅ | 手动（lock/unlock）|
| 释放锁 | 自动 ✅ | 手动（finally中释放）|
| 锁类型 | 非公平锁 | 公平锁/非公平锁可选 |
| 中断 | ❌ 不可中断 | ✅ 可中断（lockInterruptibly）|
| 超时 | ❌ 不支持 | ✅ 支持（tryLock(timeout)）|
| 条件变量 | 1个（wait/notify）| 多个（Condition）|
| 锁状态 | 无法判断 | 可判断（isLocked）|
| 性能 | JDK 1.6后差不多 | JDK 1.6后差不多 |

**代码对比**：
```java
// synchronized
public class SyncDemo {
    public synchronized void method() {
        // 业务逻辑
        // 异常也会自动释放锁 ✅
    }
}

// Lock
public class LockDemo {
    private Lock lock = new ReentrantLock();
    
    public void method() {
        lock.lock();
        try {
            // 业务逻辑
        } finally {
            lock.unlock();  // 必须手动释放 ⚠️
        }
    }
}
```

**Lock的高级功能**：

**1. 可中断锁**：
```java
Lock lock = new ReentrantLock();

public void method() throws InterruptedException {
    lock.lockInterruptibly();  // 可响应中断
    try {
        // 业务逻辑
    } finally {
        lock.unlock();
    }
}

// 使用场景：
Thread t = new Thread(() -> {
    try {
        lock.lockInterruptibly();
        // 长时间运行的任务
    } catch (InterruptedException e) {
        // 被中断，清理资源
    }
});

t.start();
Thread.sleep(100);
t.interrupt();  // 中断等待锁的线程
```

**2. 超时锁**：
```java
Lock lock = new ReentrantLock();

public void method() {
    try {
        if (lock.tryLock(3, TimeUnit.SECONDS)) {  // 等待3秒
            try {
                // 业务逻辑
            } finally {
                lock.unlock();
            }
        } else {
            // 获取锁失败，执行备选方案
            System.out.println("无法获取锁，稍后重试");
        }
    } catch (InterruptedException e) {
        e.printStackTrace();
    }
}
```

**3. 公平锁**：
```java
// 非公平锁（默认）
Lock lock = new ReentrantLock();

// 公平锁
Lock fairLock = new ReentrantLock(true);

公平锁：
  ✅ 按请求顺序获取锁
  ✅ 避免饥饿
  ❌ 性能较差（需要维护队列）
  
非公平锁：
  ✅ 性能好
  ❌ 可能饥饿
  ✅ 吞吐量高
```

**4. 多个条件变量**：
```java
Lock lock = new ReentrantLock();
Condition notFull = lock.newCondition();
Condition notEmpty = lock.newCondition();

// 生产者
public void put(Object item) throws InterruptedException {
    lock.lock();
    try {
        while (queue.isFull()) {
            notFull.await();  // 等待非满
        }
        queue.add(item);
        notEmpty.signal();  // 通知非空
    } finally {
        lock.unlock();
    }
}

// 消费者
public Object take() throws InterruptedException {
    lock.lock();
    try {
        while (queue.isEmpty()) {
            notEmpty.await();  // 等待非空
        }
        Object item = queue.remove();
        notFull.signal();  // 通知非满
        return item;
    } finally {
        lock.unlock();
    }
}

对比synchronized：
  synchronized只有一个条件变量
  所有线程在同一个条件上等待
  notifyAll会唤醒所有线程（包括不该醒的）
  Lock可以精确控制 ✅
```

**选择建议**：
```
优先使用synchronized：
  ✅ 代码简洁
  ✅ 不会忘记释放锁
  ✅ JVM优化好
  ✅ 适合简单场景
  
使用Lock的场景：
  ✅ 需要中断
  ✅ 需要超时
  ✅ 需要公平锁
  ✅ 需要多个条件变量
  ✅ 需要尝试获取锁
```

---

### Q9: ThreadLocal的原理？（⭐⭐⭐⭐⭐）

**核心原理**：
```java
// Thread类
public class Thread {
    ThreadLocal.ThreadLocalMap threadLocals = null;
}

// ThreadLocal类
public class ThreadLocal<T> {
    public T get() {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = t.threadLocals;
        if (map != null) {
            Entry e = map.getEntry(this);
            if (e != null)
                return (T)e.value;
        }
        return setInitialValue();
    }
    
    public void set(T value) {
        Thread t = Thread.currentThread();
        ThreadLocalMap map = t.threadLocals;
        if (map != null)
            map.set(this, value);
        else
            createMap(t, value);
    }
}
```

**数据结构**：
```
Thread
  ↓
ThreadLocalMap (类似HashMap)
  ↓
Entry[] table
  - key: ThreadLocal对象（弱引用）
  - value: 线程本地值（强引用）
```

**内存泄漏问题**：
```
问题：
  1. ThreadLocalMap的key是弱引用
  2. 当ThreadLocal对象被回收
  3. key变为null
  4. 但value是强引用，无法回收
  5. 如果Thread长期存活（如线程池）
  6. value永远无法回收 → 内存泄漏 ❌

解决方案：
  1. 使用完后调用remove()  ← 推荐
  2. ThreadLocalMap会自动清理null key（但不及时）
```

**正确使用示例**：
```java
// ✅ 正确使用
public class UserContext {
    private static ThreadLocal<User> context = new ThreadLocal<>();
    
    public static void setUser(User user) {
        context.set(user);
    }
    
    public static User getUser() {
        return context.get();
    }
    
    public static void clear() {
        context.remove();  // 必须清理！
    }
}

// 在拦截器/过滤器中使用
public class UserFilter implements Filter {
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) {
        try {
            User user = getUserFromRequest(request);
            UserContext.setUser(user);
            chain.doFilter(request, response);
        } finally {
            UserContext.clear();  // 清理ThreadLocal ✅
        }
    }
}
```

**应用场景**：
```java
// 1. 存储用户信息

# Java基础核心原理详解

> 从底层原理深入理解Java基础，面向高级开发工程师

---

## 📚 目录

1. [Java语言特性](#1-java语言特性)
2. [面向对象核心](#2-面向对象核心)
3. [Java类型系统](#3-java类型系统)
4. [字符串深度解析](#4-字符串深度解析)
5. [集合框架核心原理](#5-集合框架核心原理)
6. [异常处理机制](#6-异常处理机制)
7. [Java IO体系](#7-java-io体系)
8. [反射机制](#8-反射机制)
9. [泛型原理](#9-泛型原理)
10. [注解与处理器](#10-注解与处理器)

---

## 1. Java语言特性

### 1.1 Java平台架构

```
┌─────────────────────────────────────┐
│      Java Application               │  应用程序
├─────────────────────────────────────┤
│      Java API (JDK)                 │  核心类库
├─────────────────────────────────────┤
│      JVM (Java Virtual Machine)     │  虚拟机
├─────────────────────────────────────┤
│      Operating System               │  操作系统
└─────────────────────────────────────┘
```

### 1.2 核心特性

**① Write Once, Run Anywhere（一次编写，到处运行）**
```java
// .java源文件 → javac编译 → .class字节码 → JVM执行
// 字节码是平台无关的，由不同平台的JVM解释执行
```

**② 自动内存管理（GC）**
- 程序员无需手动管理内存
- 垃圾回收器自动回收不再使用的对象
- 避免内存泄漏和野指针

**③ 面向对象**
- 封装、继承、多态
- 一切皆对象（除基本类型）

---

## 2. 面向对象核心

### 2.1 封装（Encapsulation）

**原理**：
- 隐藏对象的内部实现细节
- 通过访问控制符限制访问
- 提供公共接口操作对象

**访问控制符**：
```java
public    > protected > default(包级私有) > private
  ↓           ↓              ↓               ↓
所有类     子类+同包       同包内          仅本类
```

**实战示例**：
```java
public class BankAccount {
    // 私有字段，外部无法直接访问
    private String accountNumber;
    private double balance;
    
    // 公共接口，控制访问逻辑
    public void deposit(double amount) {
        if (amount > 0) {
            balance += amount;
        } else {
            throw new IllegalArgumentException("金额必须大于0");
        }
    }
    
    public boolean withdraw(double amount) {
        if (amount > 0 && balance >= amount) {
            balance -= amount;
            return true;
        }
        return false;
    }
    
    // 只读访问
    public double getBalance() {
        return balance;
    }
}
```

---

### 2.2 继承（Inheritance）

**原理**：
- 子类继承父类的属性和方法
- 实现代码复用
- 建立类型层次结构

**继承关系**：
```java
public class Animal {
    protected String name;
    
    public void eat() {
        System.out.println(name + " is eating");
    }
}

public class Dog extends Animal {
    // 继承了name字段和eat()方法
    
    // 扩展新方法
    public void bark() {
        System.out.println(name + " is barking");
    }
    
    // 方法重写（Override）
    @Override
    public void eat() {
        System.out.println(name + " is eating dog food");
    }
}
```

**关键点**：
- Java只支持单继承（extends一个类）
- 所有类都隐式继承`Object`类
- 构造方法不被继承，但子类构造会调用父类构造（super()）

---

### 2.3 多态（Polymorphism）

**原理**：
- 同一个引用类型，指向不同的对象，调用相同的方法，表现出不同的行为
- 编译时类型 vs 运行时类型

**实现方式**：
1. **方法重载（Overload）**：编译时多态
2. **方法重写（Override）**：运行时多态

**运行时多态示例**：
```java
public class PolymorphismDemo {
    public static void main(String[] args) {
        // 编译时类型：Animal，运行时类型：Dog
        Animal animal1 = new Dog();
        animal1.eat();  // 调用Dog的eat()方法
        
        // 编译时类型：Animal，运行时类型：Cat
        Animal animal2 = new Cat();
        animal2.eat();  // 调用Cat的eat()方法
        
        // 多态的好处：统一处理
        Animal[] animals = {new Dog(), new Cat(), new Bird()};
        for (Animal animal : animals) {
            animal.eat();  // 各自调用自己的eat()实现
        }
    }
}
```

**动态绑定原理**：
```java
// JVM在运行时根据对象的实际类型，动态绑定到对应的方法实现

// 查找顺序：
// 1. 先在运行时类型（实际对象类型）中查找方法
// 2. 找不到则在父类中查找
// 3. 一直向上查找到Object类

// 方法调用指令：invokevirtual（虚方法调用）
```

---

## 3. Java类型系统

### 3.1 基本类型（Primitive Types）

**8种基本类型**：
```java
byte    -128 ~ 127                     (1字节)
short   -32768 ~ 32767                 (2字节)
int     -2^31 ~ 2^31-1                 (4字节)
long    -2^63 ~ 2^63-1                 (8字节)

float   IEEE 754单精度                 (4字节)
double  IEEE 754双精度                 (8字节)

char    0 ~ 65535（Unicode字符）       (2字节)
boolean true/false                     (1位，但实际占用1字节)
```

**存储位置**：
- 基本类型变量存储在**栈**中
- 对象引用存储在**栈**中，对象本身存储在**堆**中

---

### 3.2 包装类（Wrapper Classes）

**基本类型 → 包装类**：
```java
byte    → Byte
short   → Short
int     → Integer
long    → Long
float   → Float
double  → Double
char    → Character
boolean → Boolean
```

**自动装箱/拆箱（AutoBoxing/Unboxing）**：
```java
// 自动装箱：基本类型 → 包装类
Integer i = 100;  // 等价于 Integer.valueOf(100)

// 自动拆箱：包装类 → 基本类型
int j = i;  // 等价于 i.intValue()

// 注意空指针异常
Integer num = null;
int value = num;  // NPE！拆箱时num.intValue()报错
```

**Integer缓存机制**：
```java
public static Integer valueOf(int i) {
    // -128 ~ 127 范围内，返回缓存对象
    if (i >= IntegerCache.low && i <= IntegerCache.high)
        return IntegerCache.cache[i + (-IntegerCache.low)];
    // 超出范围，创建新对象
    return new Integer(i);
}

// 示例
Integer a = 100;
Integer b = 100;
System.out.println(a == b);  // true（同一个缓存对象）

Integer c = 200;
Integer d = 200;
System.out.println(c == d);  // false（不同对象）

// 正确比较方式：使用equals()
System.out.println(c.equals(d));  // true
```

**缓存范围**：
- `Byte`, `Short`, `Integer`, `Long`：-128 ~ 127
- `Character`：0 ~ 127
- `Boolean`：TRUE, FALSE（只有两个对象）

---

## 4. 字符串深度解析

### 4.1 String核心特性

**① 不可变性（Immutable）**：
```java
public final class String {
    // 字符数组被final修饰（JDK 9+改为byte[]）
    private final char[] value;
    
    // 没有提供修改value的方法
}
```

**为什么设计成不可变**：
1. **线程安全**：多线程共享字符串无需同步
2. **字符串常量池**：相同内容的字符串复用同一个对象
3. **安全性**：作为参数传递时，不会被修改
4. **HashCode缓存**：计���一次后缓存，提高HashMap等性能

---

### 4.2 字符串常量池（String Pool）

**原理**：
```java
// 在堆内存中维护一个字符串常量池（JDK 7+）
// 相同内容的字符串字面量，指向同一个对象

String s1 = "hello";  // 在常量池中创建
String s2 = "hello";  // 复用常量池中的对象
System.out.println(s1 == s2);  // true

String s3 = new String("hello");  // 在堆中创建新对象
System.out.println(s1 == s3);  // false

String s4 = s3.intern();  // 将s3指向常量池中的对象
System.out.println(s1 == s4);  // true
```

**intern()方法原理**：
```java
// JDK 6：将字符串复制到永久代的常量池
// JDK 7+：如果常量池没有该字符串，将堆中字符串的引用放入常量池

String s1 = new String("a") + new String("b");  // 堆中创建"ab"
String s2 = s1.intern();  // 将s1的引用放入常量池
String s3 = "ab";  // 从常量池获取
System.out.println(s1 == s2);  // true（JDK 7+）
System.out.println(s2 == s3);  // true
```

---

### 4.3 String vs StringBuilder vs StringBuffer

**对比**：
```java
// String：不可变，线程安全
String str = "hello";
str = str + " world";  // 创建新对象，原对象变成垃圾

// StringBuilder：可变，非线程安全，性能最好
StringBuilder sb = new StringBuilder("hello");
sb.append(" world");  // 在原对象上修改，不创建新对象

// StringBuffer：可变，线程安全（方法加synchronized），性能较差
StringBuffer sbf = new StringBuffer("hello");
sbf.append(" world");  // 线程安全，但有同步开销
```

**使用场景**：
- **String**：字符串不变的场景
- **StringBuilder**：单线程中大量字符串拼接
- **StringBuffer**：多线程中大量字符串拼接

**性能对比**：
```java
// 循环拼接10000次
// String：创建10000个对象，性能极差
// StringBuilder：只有1个对象，性能最好
// StringBuffer：只有1个对象，但有同步开销

// StringBuilder扩容机制：
// 默认容量16，扩容为 (oldCapacity << 1) + 2
```

---

### 4.4 字符串常见操作的原理

**substring()原理（JDK 7+）**：
```java
public String substring(int beginIndex, int endIndex) {
    // JDK 6：共享原字符串的char[]，可能导致内存泄漏
    // JDK 7+：创建新的char[]，复制字符
    return new String(value, beginIndex, subLen);
}
```

**split()原理**：
```java
// 基于正则表达式分割
String[] parts = "a,b,c".split(",");  // ["a", "b", "c"]

// 注意：如果分隔符是正则特殊字符，需要转义
String[] parts2 = "a.b.c".split("\\.");  // ["a", "b", "c"]
```

**equals()原理**：
```java
public boolean equals(Object anObject) {
    if (this == anObject) {
        return true;  // 同一个对象
    }
    if (anObject instanceof String) {
        String anotherString = (String)anObject;
        int n = value.length;
        if (n == anotherString.value.length) {
            char v1[] = value;
            char v2[] = anotherString.value;
            int i = 0;
            // 逐字符比较
            while (n-- != 0) {
                if (v1[i] != v2[i])
                    return false;
                i++;
            }
            return true;
        }
    }
    return false;
}
```

---

## 5. 集合框架核心原理

### 5.1 集合框架体系

```
Collection（接口）
├── List（接口）：有序，可重复
│   ├── ArrayList：动态数组
│   ├── LinkedList：双向链表
│   └── Vector：线程安全的动态数组（已过时）
├── Set（接口）：无序，不可重复
│   ├── HashSet：基于HashMap
│   ├── LinkedHashSet：保持插入顺序
│   └── TreeSet：基于TreeMap，有序
└── Queue（接口）：队列
    ├── PriorityQueue：优先队列（堆）
    └── Deque（接口）：双端队列
        └── ArrayDeque：基于数组的双端队列

Map（接口）：键值对
├── HashMap：哈希表
├── LinkedHashMap：保持插入顺序
├── TreeMap：红黑树，有序
├── Hashtable：线程安全（已过时）
└── ConcurrentHashMap：线程安全，高并发
```

---

### 5.2 ArrayList核心原理

**底层结构**：
```java
public class ArrayList<E> {
    // 默认初始容量
    private static final int DEFAULT_CAPACITY = 10;
    
    // 底层数组
    transient Object[] elementData;
    
    // 实际元素个数
    private int size;
}
```

**扩容机制**：
```java
// 添加元素时，如果容量不足，触发扩容
public boolean add(E e) {
    ensureCapacityInternal(size + 1);  // 确保容量
    elementData[size++] = e;
    return true;
}

// 扩容为原来的1.5倍
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);  // 1.5倍
    if (newCapacity < minCapacity)
        newCapacity = minCapacity;
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

**时间复杂度**：
- `get(index)`：O(1)
- `add(E e)`：平均O(1)，扩容时O(n)
- `add(index, E e)`：O(n)，需要移动元素
- `remove(index)`：O(n)，需要移动元素

**适用场景**：
- ✅ 频繁随机访问
- ✅ 在末尾添加/删除
- ❌ 频繁在中间插入/删除

---

### 5.3 LinkedList核心原理

**底层结构**：
```java
public class LinkedList<E> {
    transient int size = 0;
    transient Node<E> first;  // 头节点
    transient Node<E> last;   // 尾节点
    
    // 节点定义
    private static class Node<E> {
        E item;
        Node<E> next;
        Node<E> prev;
        
        Node(Node<E> prev, E element, Node<E> next) {
            this.item = element;
            this.next = next;
            this.prev = prev;
        }
    }
}
```

**操作原理**：
```java
// 添加到末尾：O(1)
public boolean add(E e) {
    linkLast(e);
    return true;
}

void linkLast(E e) {
    final Node<E> l = last;
    final Node<E> newNode = new Node<>(l, e, null);
    last = newNode;
    if (l == null)
        first = newNode;
    else
        l.next = newNode;
    size++;
}

// 根据索引获取：O(n)
public E get(int index) {
    checkElementIndex(index);
    return node(index).item;
}

// 优化：根据index选择从前或从后遍历
Node<E> node(int index) {
    if (index < (size >> 1)) {  // 前半部分
        Node<E> x = first;
        for (int i = 0; i < index; i++)
            x = x.next;
        return x;
    } else {  // 后半部分
        Node<E> x = last;
        for (int i = size - 1; i > index; i--)
            x = x.prev;
        return x;
    }
}
```

**时间复杂度**：
- `get(index)`：O(n)
- `add(E e)`：O(1)
- `add(index, E e)`：O(n)，需要先定位
- `remove(index)`：O(n)，需要先定位

**适用场景**：
- ✅ 频繁在头尾添加/删除
- ✅ 队列、栈的实现
- ❌ 频繁随机访问

---


### 5.4 HashMap核心原理（⭐⭐⭐⭐⭐）

**底层结构（JDK 8+）**：
```
数组 + 链表 + 红黑树

┌────┬────┬────┬────┐
│  0 │ 1  │ 2  │... │  数组（Node[]）
└─┬──┴────┴────┴────┘
  │
  ├─> Node → Node → Node  (链表，长度<8)
  │
  └─> TreeNode → TreeNode  (红黑树，长度≥8且数组长度≥64)
```

**核心数据结构**：
```java
public class HashMap<K,V> {
    // 默认初始容量：16
    static final int DEFAULT_INITIAL_CAPACITY = 1 << 4;
    
    // 默认负载因子：0.75
    static final float DEFAULT_LOAD_FACTOR = 0.75f;
    
    // 链表转红黑树阈值：8
    static final int TREEIFY_THRESHOLD = 8;
    
    // 红黑树转链表阈值：6
    static final int UNTREEIFY_THRESHOLD = 6;
    
    // 转红黑树的最小数组容量：64
    static final int MIN_TREEIFY_CAPACITY = 64;
    
    // 数组
    transient Node<K,V>[] table;
    
    // 元素个数
    transient int size;
    
    // 扩容阈值：capacity * loadFactor
    int threshold;
    
    // 节点定义
    static class Node<K,V> implements Map.Entry<K,V> {
        final int hash;
        final K key;
        V value;
        Node<K,V> next;
    }
}
```

**Hash计算（扰动函数）**：
```java
static final int hash(Object key) {
    int h;
    // key的hashCode与其高16位异或
    // 目的：让高位也参与到hash计算，减少碰撞
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}

// 示例：
// hashCode = 0b 1111 1111 1111 1111 0000 1111 0000 1010
//         >>> 16 = 0b 0000 0000 0000 0000 1111 1111 1111 1111
//         异或后 = 0b 1111 1111 1111 1111 1111 0000 1111 0101
```

**put()原理**：
```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}

final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
               boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;
    
    // 1. 数组为空，初始化
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;
    
    // 2. 计算索引：(n - 1) & hash（等价于hash % n，但更快）
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);  // 直接放入
    else {
        // 3. 发生碰撞
        Node<K,V> e; K k;
        // 3.1 key相同，覆盖
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;
        // 3.2 红黑树节点
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
        // 3.3 链表节点
        else {
            for (int binCount = 0; ; ++binCount) {
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);
                    // 链表长度≥8，转红黑树
                    if (binCount >= TREEIFY_THRESHOLD - 1)
                        treeifyBin(tab, hash);
                    break;
                }
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    break;
                p = e;
            }
        }
        // 4. key存在，更新value
        if (e != null) {
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            return oldValue;
        }
    }
    ++modCount;
    // 5. 超过阈值，扩容
    if (++size > threshold)
        resize();
    return null;
}
```

**扩容机制（resize）**：
```java
final Node<K,V>[] resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;
    
    // 1. 计算新容量（2倍扩容）
    if (oldCap > 0) {
        if (oldCap >= MAXIMUM_CAPACITY) {
            threshold = Integer.MAX_VALUE;
            return oldTab;
        }
        // 扩容为原来的2倍
        else if ((newCap = oldCap << 1) < MAXIMUM_CAPACITY &&
                 oldCap >= DEFAULT_INITIAL_CAPACITY)
            newThr = oldThr << 1;  // 阈值也翻倍
    }
    
    // 2. 创建新数组
    Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
    table = newTab;
    
    // 3. 数据迁移
    if (oldTab != null) {
        for (int j = 0; j < oldCap; ++j) {
            Node<K,V> e;
            if ((e = oldTab[j]) != null) {
                oldTab[j] = null;
                // 3.1 单节点，直接迁移
                if (e.next == null)
                    newTab[e.hash & (newCap - 1)] = e;
                // 3.2 红黑树
                else if (e instanceof TreeNode)
                    ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
                // 3.3 链表
                else {
                    // 优化：根据hash值的高位，分成两条链表
                    // 低位链表：保持原索引
                    // 高位链表：索引 = 原索引 + oldCap
                    Node<K,V> loHead = null, loTail = null;
                    Node<K,V> hiHead = null, hiTail = null;
                    Node<K,V> next;
                    do {
                        next = e.next;
                        // (e.hash & oldCap) == 0 说明高位为0
                        if ((e.hash & oldCap) == 0) {
                            if (loTail == null)
                                loHead = e;
                            else
                                loTail.next = e;
                            loTail = e;
                        }
                        else {
                            if (hiTail == null)
                                hiHead = e;
                            else
                                hiTail.next = e;
                            hiTail = e;
                        }
                    } while ((e = next) != null);
                    if (loTail != null) {
                        loTail.next = null;
                        newTab[j] = loHead;
                    }
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

**为什么容量必须是2的幂**：
```java
// 1. 计算索引更高效：(n - 1) & hash 等价于 hash % n
// 例如：n = 16 = 0b 10000
//      n - 1 = 15 = 0b 01111
//      hash & 0b01111 = 取hash的低4位，等价于 hash % 16

// 2. 扩容时数据迁移更高效
// 容量扩大2倍，每个节点要么在原位置，要么在"原位置+oldCap"
```

**为什么负载因子是0.75**：
```
负载因子 = size / capacity

太小（如0.5）：空间利用率低，频繁扩容
太大（如1.0）：碰撞概率高，链表过长，性能下降

0.75：时间和空间的折中，泊松分布计算得出最优值
```

**时间复杂度**：
- `put()`：平均O(1)，最坏O(n)（JDK 8+红黑树优化为O(log n)）
- `get()`：平均O(1)，最坏O(n)（JDK 8+红黑树优化为O(log n)）

**线程安全问题**：
```java
// JDK 7：扩容时链表采用头插法，多线程可能形成环形链表，导致死循环
// JDK 8：改为尾插法，避免了环形链表，但仍不是线程安全的

// 解决方案：
// 1. Collections.synchronizedMap(new HashMap<>())
// 2. ConcurrentHashMap（推荐）
```

---

### 5.5 LinkedHashMap原理

**特点**：
- 继承HashMap
- 维护插入顺序或访问顺序

**底层结构**：
```java
static class Entry<K,V> extends HashMap.Node<K,V> {
    Entry<K,V> before, after;  // 双向链表，维护顺序
    Entry(int hash, K key, V value, Node<K,V> next) {
        super(hash, key, value, next);
    }
}

// 头尾指针
transient LinkedHashMap.Entry<K,V> head;
transient LinkedHashMap.Entry<K,V> tail;

// 访问顺序标志
final boolean accessOrder;  // true：访问顺序，false：插入顺序
```

**应用：实现LRU缓存**：
```java
class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private int capacity;
    
    public LRUCache(int capacity) {
        // 参数：初始容量、负载因子、true=访问顺序
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }
    
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        // 超过容量，删除最老的元素
        return size() > capacity;
    }
}

// 使用
LRUCache<Integer, String> cache = new LRUCache<>(3);
cache.put(1, "a");
cache.put(2, "b");
cache.put(3, "c");
cache.get(1);  // 访问1，1变成最新
cache.put(4, "d");  // 容量满，删除最久未访问的2
// 缓存：{3=c, 1=a, 4=d}
```

---

### 5.6 TreeMap原理

**特点**：
- 基于红黑树
- key有序（自然顺序或自定义比较器）

**底层结构**：
```java
static final class Entry<K,V> implements Map.Entry<K,V> {
    K key;
    V value;
    Entry<K,V> left;   // 左子节点
    Entry<K,V> right;  // 右子节点
    Entry<K,V> parent; // 父节点
    boolean color = BLACK;  // 红黑树节点颜色
}
```

**put()原理**：
```java
public V put(K key, V value) {
    Entry<K,V> t = root;
    if (t == null) {
        // 根节点
        root = new Entry<>(key, value, null);
        size = 1;
        return null;
    }
    int cmp;
    Entry<K,V> parent;
    // 1. 查找插入位置
    do {
        parent = t;
        cmp = compare(key, t.key);  // 比较key
        if (cmp < 0)
            t = t.left;
        else if (cmp > 0)
            t = t.right;
        else
            return t.setValue(value);  // key相同，更新value
    } while (t != null);
    
    // 2. 插入节点
    Entry<K,V> e = new Entry<>(key, value, parent);
    if (cmp < 0)
        parent.left = e;
    else
        parent.right = e;
    
    // 3. 红黑树平衡调整
    fixAfterInsertion(e);
    size++;
    return null;
}
```

**时间复杂度**：
- `put()`, `get()`, `remove()`：O(log n)

**适用场景**：
- ✅ 需要key有序
- ✅ 范围查询（firstKey, lastKey, subMap）

---

### 5.7 ConcurrentHashMap原理（JDK 8）

**JDK 7 vs JDK 8**：
```
JDK 7：Segment分段锁（16个段）
JDK 8：CAS + synchronized，锁粒度更小（锁到Node）
```

**JDK 8核心机制**：
```java
// 1. 数组初始化：CAS保证单次初始化
private final Node<K,V>[] initTable() {
    Node<K,V>[] tab; int sc;
    while ((tab = table) == null || tab.length == 0) {
        if ((sc = sizeCtl) < 0)
            Thread.yield();  // 其他线程在初始化，让出CPU
        // CAS设置sizeCtl为-1，表示正在初始化
        else if (U.compareAndSwapInt(this, SIZECTL, sc, -1)) {
            try {
                if ((tab = table) == null || tab.length == 0) {
                    int n = (sc > 0) ? sc : DEFAULT_CAPACITY;
                    Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n];
                    table = tab = nt;
                    sc = n - (n >>> 2);  // 0.75n
                }
            } finally {
                sizeCtl = sc;
            }
            break;
        }
    }
    return tab;
}

// 2. put()：CAS + synchronized
final V putVal(K key, V value, boolean onlyIfAbsent) {
    if (key == null || value == null) throw new NullPointerException();
    int hash = spread(key.hashCode());
    int binCount = 0;
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();  // 初始化
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            // 位置为空，CAS插入
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break;
        }
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);  // 正在扩容，帮助迁移
        else {
            V oldVal = null;
            // 锁住链表头节点或红黑树根节点
            synchronized (f) {
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {  // 链表
                        binCount = 1;
                        for (Node<K,V> e = f;; ++binCount) {
                            K ek;
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                oldVal = e.val;
                                if (!onlyIfAbsent)
                                    e.val = value;
                                break;
                            }
                            Node<K,V> pred = e;
                            if ((e = e.next) == null) {
                                pred.next = new Node<K,V>(hash, key,
                                                          value, null);
                                break;
                            }
                        }
                    }
                    else if (f instanceof TreeBin) {  // 红黑树
                        Node<K,V> p;
                        binCount = 2;
                        if ((p = ((TreeBin<K,V>)f).putTreeVal(hash, key,
                                                       value)) != null) {
                            oldVal = p.val;
                            if (!onlyIfAbsent)
                                p.val = value;
                        }
                    }
                }
            }
            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i);
                if (oldVal != null)
                    return oldVal;
                break;
            }
        }
    }
    addCount(1L, binCount);  // 计数（CAS）
    return null;
}
```

**优势**：
1. **锁粒度小**：只锁单个Node，不影响其他位置的操作
2. **CAS无锁**：数组为空时，CAS插入，无需加锁
3. **扩容并发**：支持多线程协助扩容

**size()实现**：
```java
// 使用CounterCell数组 + baseCount，类似LongAdder
// 高并发下分散计数，避免CAS失败
public int size() {
    long n = sumCount();
    return ((n < 0L) ? 0 :
            (n > (long)Integer.MAX_VALUE) ? Integer.MAX_VALUE :
            (int)n);
}
```

---

## 6. 异常处理机制

### 6.1 异常体系

```
Throwable
├── Error（错误，不可恢复）
│   ├── OutOfMemoryError
│   ├── StackOverflowError
│   └── VirtualMachineError
└── Exception（异常，可处理）
    ├── RuntimeException（运行时异常，unchecked）
    │   ├── NullPointerException
    │   ├── ArrayIndexOutOfBoundsException
    │   ├── ClassCastException
    │   └── IllegalArgumentException
    └── CheckedException（编译时异常，checked）
        ├── IOException
        ├── SQLException
        └── ClassNotFoundException
```

**Checked vs Unchecked**：
```java
// Checked：必须显式处理（try-catch或throws）
public void readFile() throws IOException {
    FileInputStream fis = new FileInputStream("file.txt");
    fis.read();
}

// Unchecked：可以不处理
public void divide(int a, int b) {
    int result = a / b;  // 可能抛出ArithmeticException
}
```

---

### 6.2 异常处理原理

**try-catch-finally执行顺序**：
```java
public class ExceptionTest {
    public static int test() {
        try {
            System.out.println("try");
            return 1;
        } catch (Exception e) {
            System.out.println("catch");
            return 2;
        } finally {
            System.out.println("finally");
            // finally中的return会覆盖try/catch中的return
            // return 3;
        }
    }
    
    public static void main(String[] args) {
        System.out.println(test());
    }
}
// 输出：
// try
// finally
// 1
```

**return在finally中的陷阱**：
```java
public static int test() {
    int i = 0;
    try {
        i = 1;
        return i;  // 返回1
    } finally {
        i = 2;  // 不影响返回值（已经保存了i=1）
    }
}
// 返回：1

public static int test2() {
    int i = 0;
    try {
        i = 1;
        return i;
    } finally {
        return 2;  // finally中的return会覆盖
    }
}
// 返回：2
```

---

### 6.3 try-with-resources

**自动资源管理**：
```java
// JDK 7+：自动关闭资源
try (FileInputStream fis = new FileInputStream("file.txt");
     BufferedReader br = new BufferedReader(new InputStreamReader(fis))) {
    String line = br.readLine();
    System.out.println(line);
}  // 自动调用close()

// 等价于：
FileInputStream fis = null;
BufferedReader br = null;
try {
    fis = new FileInputStream("file.txt");
    br = new BufferedReader(new InputStreamReader(fis));
    String line = br.readLine();
    System.out.println(line);
} finally {
    if (br != null) br.close();
    if (fis != null) fis.close();
}
```

**原理**：
```java
// 资源必须实现AutoCloseable接口
public interface AutoCloseable {
    void close() throws Exception;
}

// 示例
public class MyResource implements AutoCloseable {
    @Override
    public void close() throws Exception {
        System.out.println("资源关闭");
    }
}
```

---

### 6.4 最佳实践

**① 不要吞掉异常**：
```java
// ❌ 错误：吞掉异常
try {
    // ...
} catch (Exception e) {
    // 什么都不做
}

// ✅ 正确：至少记录日志
try {
    // ...
} catch (Exception e) {
    log.error("操作失败", e);
}
```

**② 不要捕获所有异常**：
```java
// ❌ 错误：捕获所有异常
try {
    // ...
} catch (Throwable t) {  // 包括Error
    // ...
}

// ✅ 正确：只捕获预期的异常
try {
    // ...
} catch (IOException e) {
    // 处理IO异常
} catch (SQLException e) {
    // 处理SQL异常
}
```

**③ 自定义异常**：
```java
// 业务异常
public class BusinessException extends RuntimeException {
    private int errorCode;
    
    public BusinessException(int errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }
}

// 使用
if (balance < amount) {
    throw new BusinessException(1001, "余额不足");
}
```

---

## 7. Java IO体系

### 7.1 IO分类

```
IO流分类：
├── 按数据流向
│   ├── 输入流（InputStream/Reader）
│   └── 输出流（OutputStream/Writer）
├── 按数据类型
│   ├── 字节流（Stream）：8位字节
│   └── 字符流（Reader/Writer）：16位字符
└── 按功能
    ├── 节点流：直接操作数据源
    └── 处理流：包装节点流，提供额外功能
```

**核心类**：
```
字节流：
├── InputStream
│   ├── FileInputStream：文件输入
│   ├── ByteArrayInputStream：字节数组输入
│   └── BufferedInputStream：缓冲输入（处理流）
└── OutputStream
    ├── FileOutputStream：文件输出
    ├── ByteArrayOutputStream：字节数组输出
    └── BufferedOutputStream：缓冲输出（处理流）

字符流：
├── Reader
│   ├── FileReader：文件读取
│   ├── CharArrayReader：字符数组读取
│   ├── BufferedReader：缓冲读取（处理流）
│   └── InputStreamReader：字节流→字符流转换
└── Writer
    ├── FileWriter：文件写入
    ├── CharArrayWriter：字符数组写入
    ├── BufferedWriter：缓冲写入（处理流）
    └── OutputStreamWriter：字符流→字节流转换
```

---

### 7.2 字节流 vs 字符流

**使用场景**：
```java
// 字节流：处理二进制数据（图片、视频、音频等）
try (FileInputStream fis = new FileInputStream("image.jpg");
     FileOutputStream fos = new FileOutputStream("copy.jpg")) {
    byte[] buffer = new byte[1024];
    int len;
    while ((len = fis.read(buffer)) != -1) {
        fos.write(buffer, 0, len);
    }
}

// 字符流：处理文本数据
try (FileReader fr = new FileReader("file.txt");
     FileWriter fw = new FileWriter("copy.txt")) {
    char[] buffer = new char[1024];
    int len;
    while ((len = fr.read(buffer)) != -1) {
        fw.write(buffer, 0, len);
    }
}
```

**字符流编码**：
```java
// 指定编码
try (InputStreamReader isr = new InputStreamReader(
        new FileInputStream("file.txt"), StandardCharsets.UTF_8);
     OutputStreamWriter osw = new OutputStreamWriter(
        new FileOutputStream("output.txt"), StandardCharsets.UTF_8)) {
    // ...
}
```

---

### 7.3 缓冲流原理

**为什么需要缓冲流**：
- 减少系统调用次数
- 批量读写，提高效率

**BufferedInputStream原理**：
```java
public class BufferedInputStream extends FilterInputStream {
    // 默认缓冲区大小：8KB
    private static int DEFAULT_BUFFER_SIZE = 8192;
    
    // 缓冲区
    protected volatile byte buf[];
    
    public synchronized int read() throws IOException {
        if (pos >= count) {
            fill();  // 缓冲区读完，重新填充
            if (pos >= count)
                return -1;
        }
        return getBufIfOpen()[pos++] & 0xff;
    }
    
    private void fill() throws IOException {
        // 一次性从底层流读取8KB数据到缓冲区
        int n = getInIfOpen().read(buf, pos, buf.length - pos);
        if (n > 0)
            count = pos + n;
    }
}
```

**性能对比**：
```java
// 不使用缓冲：每次read()都是系统调用，慢
try (FileInputStream fis = new FileInputStream("file.txt")) {
    int b;
    while ((b = fis.read()) != -1) {  // 每次读1字节
        // ...
    }
}

// 使用缓冲：8KB缓冲区，减少系统调用
try (BufferedInputStream bis = new BufferedInputStream(
        new FileInputStream("file.txt"))) {
    int b;
    while ((b = bis.read()) != -1) {  // 实际从缓冲区读
        // ...
    }
}
```

---

### 7.4 NIO（New IO）

**核心概念**：
```
传统IO（BIO）：面向流，阻塞IO
NIO：面向缓冲区（Buffer），非阻塞IO，选择器（Selector）
```

**核心组件**：
```java
// 1. Buffer：数据缓冲区
ByteBuffer buffer = ByteBuffer.allocate(1024);

// 2. Channel：数据通道
FileChannel channel = FileChannel.open(Paths.get("file.txt"));

// 3. Selector：选择器（多路复用）
Selector selector = Selector.open();
channel.register(selector, SelectionKey.OP_READ);
```

**Buffer核心操作**：
```java
ByteBuffer buffer = ByteBuffer.allocate(10);

// 写模式
buffer.put("hello".getBytes());  // position移动
buffer.flip();  // 切换到读模式：limit=position, position=0

// 读模式
byte[] data = new byte[buffer.remaining()];
buffer.get(data);  // position移动

// 清空
buffer.clear();  // 切换到写模式：position=0, limit=capacity
```

**Channel读写**：
```java
// 读取文件
try (FileChannel channel = FileChannel.open(Paths.get("file.txt"))) {
    ByteBuffer buffer = ByteBuffer.allocate(1024);
    int bytesRead = channel.read(buffer);  // 从Channel读到Buffer
    buffer.flip();
    while (buffer.hasRemaining()) {
        System.out.print((char) buffer.get());
    }
}

// 写入文件
try (FileChannel channel = FileChannel.open(Paths.get("output.txt"),
        StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
    ByteBuffer buffer = ByteBuffer.wrap("hello".getBytes());
    channel.write(buffer);  // 从Buffer写到Channel
}
```

---

## 8. 反射机制

### 8.1 什么是反射

**定义**：
- 在运行时动态获取类的信息（类名、方法、字段等）
- 在运行时动态调用对象的方法、访问字段

**核心类**：
```java
Class<?>        // 类对象
Field           // 字段
Method          // 方法
Constructor     // 构造方法
```

---

### 8.2 获取Class对象

**三种方式**：
```java
// 1. Class.forName()
Class<?> clazz1 = Class.forName("java.lang.String");

// 2. 类名.class
Class<?> clazz2 = String.class;

// 3. 对象.getClass()
String str = "hello";
Class<?> clazz3 = str.getClass();

// 三者相同
System.out.println(clazz1 == clazz2);  // true
System.out.println(clazz2 == clazz3);  // true
```

---

### 8.3 反射操作

**① 创建对象**：
```java
Class<?> clazz = Class.forName("com.example.User");

// 无参构造
Object obj = clazz.newInstance();  // JDK 9已过时

// 推荐方式
Constructor<?> constructor = clazz.getConstructor();
Object obj2 = constructor.newInstance();

// 有参构造
Constructor<?> constructor2 = clazz.getConstructor(String.class, int.class);
Object obj3 = constructor2.newInstance("张三", 20);
```

**② 访问字段**：
```java
Class<?> clazz = User.class;
User user = new User("张三", 20);

// 获取字段
Field field = clazz.getDeclaredField("name");  // 包括private
field.setAccessible(true);  // 绕过访问控制

// 读取字段值
String name = (String) field.get(user);

// 设置字段值
field.set(user, "李四");
```

**③ 调用方法**：
```java
Class<?> clazz = User.class;
User user = new User("张三", 20);

// 获取方法
Method method = clazz.getDeclaredMethod("setName", String.class);
method.setAccessible(true);

// 调用方法
method.invoke(user, "王五");  // user.setName("王五")
```

---

### 8.4 反射原理

**Method.invoke()原理**：
```java
public Object invoke(Object obj, Object... args) {
    // 1. 权限检查
    if (!override) {
        if (!Reflection.quickCheckMemberAccess(clazz, modifiers)) {
            checkAccess(...);
        }
    }
    
    // 2. 方法调用
    // 前15次：使用JNI（本地方法）
    // 第16次及以后：生成字节码，直接调用（性能提升）
    MethodAccessor ma = acquireMethodAccessor();
    return ma.invoke(obj, args);
}
```

**性能优化**：
- 缓存Method对象，避免重复查找
- setAccessible(true)，避免权限检查

---

### 8.5 反射应用场景

**① 框架开发**：
```java
// Spring IOC：反射创建Bean
Class<?> clazz = Class.forName(beanClassName);
Object bean = clazz.newInstance();

// Spring AOP：反射调用方法
Method method = target.getClass().getMethod(methodName, paramTypes);
method.invoke(target, args);
```

**② 动态代理**：
```java
// JDK动态代理基于反射实现
Object proxy = Proxy.newProxyInstance(
    classLoader,
    interfaces,
    new InvocationHandler() {
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) {
            // 反射调用原方法
            return method.invoke(target, args);
        }
    }
);
```

**③ 注解处理**：
```java
// 获取注解
if (method.isAnnotationPresent(MyAnnotation.class)) {
    MyAnnotation annotation = method.getAnnotation(MyAnnotation.class);
    String value = annotation.value();
}
```

---

## 9. 泛型原理

### 9.1 什么是泛型

**定义**：
- 参数化类型
- 编译时类型检查
- 避免类型转换

**泛型类**：
```java
public class Box<T> {
    private T data;
    
    public void set(T data) {
        this.data = data;
    }
    
    public T get() {
        return data;
    }
}

// 使用
Box<String> box = new Box<>();
box.set("hello");
String str = box.get();  // 无需强转
```

---

### 9.2 类型擦除

**原理**：
- 泛型只在编译期存在
- 编译后，泛型信息被擦除，替换为Object或上界类型

**示例**：
```java
// 编译前
public class Box<T> {
    private T data;
    public T get() { return data; }
}

// 编译后（类型擦除）
public class Box {
    private Object data;  // T被擦除为Object
    public Object get() { return data; }
}

// 使用泛型时，编译器自动插入强转
Box<String> box = new Box<>();
String str = box.get();
// 编译后：String str = (String) box.get();
```

**有上界的泛型**：
```java
// 编译前
public class Box<T extends Number> {
    private T data;
    public T get() { return data; }
}

// 编译后
public class Box {
    private Number data;  // T被擦除为Number
    public Number get() { return data; }
}
```

---

### 9.3 泛型通配符

**① 无界通配符 `<?>`**：
```java
public void print(List<?> list) {
    for (Object obj : list) {
        System.out.println(obj);
    }
}
```

**② 上界通配符 `<? extends T>`**：
```java
// 只能读取，不能写入（除了null）
public double sum(List<? extends Number> list) {
    double sum = 0;
    for (Number num : list) {
        sum += num.doubleValue();  // 可以读取
    }
    // list.add(1);  // 编译错误！不能写入
    return sum;
}

List<Integer> ints = Arrays.asList(1, 2, 3);
sum(ints);  // 可以传入List<Integer>
```

**③ 下界通配符 `<? super T>`**：
```java
// 可以写入T及其子类，读取只能用Object接收
public void addNumbers(List<? super Integer> list) {
    list.add(1);  // 可以写入Integer
    list.add(2);
    // Integer num = list.get(0);  // 编译错误！
    Object obj = list.get(0);  // 只能用Object接收
}

List<Number> numbers = new ArrayList<>();
addNumbers(numbers);  // 可以传入List<Number>
```

**PECS原则**：
```
Producer Extends, Consumer Super

- 如果只需要从集合读取，使用 <? extends T>（生产者）
- 如果只需要向集合写入，使用 <? super T>（消费者）
```

---

### 9.4 泛型方法

**定义**：
```java
public class GenericMethod {
    // 泛型方法：<T>声明类型参数
    public <T> T get(List<T> list, int index) {
        return list.get(index);
    }
    
    // 多个类型参数
    public <K, V> void print(Map<K, V> map) {
        for (Map.Entry<K, V> entry : map.entrySet()) {
            System.out.println(entry.getKey() + " = " + entry.getValue());
        }
    }
    
    // 有上界的泛型方法
    public <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) > 0 ? a : b;
    }
}
```

---

## 10. 注解与处理器

### 10.1 注解基础

**定义注解**：
```java
@Target(ElementType.METHOD)  // 作用目标：方法
@Retention(RetentionPolicy.RUNTIME)  // 保留到运行时
public @interface MyAnnotation {
    String value() default "";  // 注解属性
    int age() default 0;
}
```

**元注解**：
```java
@Target：指定注解作用目标
    - ElementType.TYPE：类、接口、枚举
    - ElementType.FIELD：字段
    - ElementType.METHOD：方法
    - ElementType.PARAMETER：参数
    - ElementType.CONSTRUCTOR：构造方法

@Retention：指定注解保留策略
    - RetentionPolicy.SOURCE：源码期（编译后丢弃）
    - RetentionPolicy.CLASS：字节码期（默认，运行时不可见）
    - RetentionPolicy.RUNTIME：运行时（可通过反射获取）

@Documented：生成JavaDoc时包含注解信息
@Inherited：注解可被子类继承
```

---

### 10.2 注解处理

**运行时处理**：
```java
@MyAnnotation(value = "test", age = 20)
public void myMethod() {
    // ...
}

// 反射获取注解
Method method = clazz.getMethod("myMethod");
if (method.isAnnotationPresent(MyAnnotation.class)) {
    MyAnnotation annotation = method.getAnnotation(MyAnnotation.class);
    String value = annotation.value();  // "test"
    int age = annotation.age();  // 20
}
```

**编译时处理（注解处理器）**：
```java
@SupportedAnnotationTypes("com.example.MyAnnotation")
@SupportedSourceVersion(SourceVersion.RELEASE_8)
public class MyProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations,
                          RoundEnvironment roundEnv) {
        // 编译时处理注解，生成代码
        for (Element element : roundEnv.getElementsAnnotatedWith(MyAnnotation.class)) {
            // 处理逻辑
        }
        return true;
    }
}
```

---

### 10.3 常见注解

**JDK内置注解**：
```java
@Override：标记方法覆盖父类方法
@Deprecated：标记过时的API
@SuppressWarnings：抑制编译警告
@FunctionalInterface：标记函数式接口（只有一个抽象方法）
```

**Spring注解**：
```java
@Component, @Service, @Repository, @Controller：组件注解
@Autowired：自动注入
@RequestMapping：请求映射
@Transactional：事务管理
```

**Lombok注解**：
```java
@Data：自动生成getter/setter/toString/equals/hashCode
@Getter/@Setter：生成getter/setter
@NoArgsConstructor/@AllArgsConstructor：生成构造方法
@Builder：生成Builder模式代码
```

---

## 📝 总结

### 核心要点

**1. 面向对象**：
- 封装：隐藏实现细节
- 继承：代码复用，类型层次
- 多态：动态绑定，统一处理

**2. 类型系统**：
- 基本类型 vs 包装类
- 自动装箱/拆箱
- Integer缓存机制

**3. String**：
- 不可变性
- 字符串常量池
- intern()方法

**4. 集合框架**：
- ArrayList：动态数组，扩容1.5倍
- LinkedList：双向链表
- HashMap：数组+链表+红黑树，容量2的幂
- ConcurrentHashMap：CAS + synchronized

**5. 异常处理**：
- Checked vs Unchecked
- try-catch-finally执行顺序
- try-with-resources

**6. IO**：
- 字节流 vs 字符流
- 缓冲流原理
- NIO：Buffer、Channel、Selector

**7. 反射**：
- 运行时动态操作类
- Method.invoke()原理
- 框架开发基础

**8. 泛型**：
- 类型擦除
- 泛型通配符（?, extends, super）
- PECS原则

**9. 注解**：
- 元注解（@Target, @Retention）
- 运行时处理（反射）
- 编译时处理（注解处理器）

---

**下一篇**：《JVM虚拟机详解》深入JVM底层原理

*最后更新：2025-10-27*

# ArrayList源码深度解析

> ArrayList是Java中最常用的动态数组实现，底层基于Object数组，支持随机访问、自动扩容和泛型安全。本文基于JDK 1.8源码，从数据结构、核心属性、构造方法、增删改查、扩容机制、迭代器实现、序列化等方面全面剖析ArrayList的内部实现。

---

## 📋 目录

1. [整体数据结构](#1-整体数据结构)
2. [核心属性与常量](#2-核心属性与常量)
3. [构造方法分析](#3-构造方法分析)
4. [add方法与扩容机制](#4-add方法与扩容机制)
5. [批量添加addAll方法](#5-批量添加addAll方法)
6. [get与set方法](#6-get与set方法)
7. [remove方法解析](#7-remove方法解析)
8. [迭代器与fail-fast机制](#8-迭代器与fail-fast机制)
9. [序列化机制](#9-序列化机制)
10. [subList与线程安全](#10-subList与线程安全)
11. [面试题速查](#11-面试题速查)

---

## 1. 整体数据结构

ArrayList的本质是一个可以动态增长的Object数组。它通过维护一个`elementData`数组来存储元素，用一个`size`变量记录实际存储的元素个数。当数组容量不足时，通过创建更大的数组并拷贝旧数据来实现扩容。

```java
public class ArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, java.io.Serializable {

    // 底层数组，非private为了内部类访问
    transient Object[] elementData;

    // 实际元素个数
    private int size;

    // ... 其他属性
}
```

ArrayList实现了以下接口：
- **RandomAccess**：标记接口，表示支持快速随机访问（O(1)）
- **Cloneable**：支持clone
- **Serializable**：支持序列化
- **List**：List接口的所有方法

数据结构示意：

```
elementData: [obj1, obj2, obj3, null, null, null, null, null, null, null]
              ↑                              ↑
             index 0                       index 3
                           size = 3       capacity = 10
```

`elementData`的长度（capacity）可能大于size，多余的空间是为了减少扩容次数。这是**空间换时间**策略的体现。

---

## 2. 核心属性与常量

```java
public class ArrayList<E> extends AbstractList<E>
        implements List<E>, RandomAccess, Cloneable, java.io.Serializable {

    // 默认初始容量
    private static final int DEFAULT_CAPACITY = 10;

    // 空数组常量，用于指定初始容量为0时的初始化
    private static final Object[] EMPTY_ELEMENTDATA = {};

    // 默认空数组常量，用于无参构造时的延迟初始化
    // 与EMPTY_ELEMENTDATA区分，是为了在第一次add时知道该扩容到多少
    private static final Object[] DEFAULTCAPACITY_EMPTY_ELEMENTDATA = {};

    // 底层数组
    transient Object[] elementData;

    // 实际元素个数
    private int size;

    // 数组最大容量
    // 减去8是因为某些VM会在数组头保留一些信息
    // OOM时尝试分配Integer.MAX_VALUE可能导致某些VM崩溃
    private static final int MAX_ARRAY_SIZE = Integer.MAX_VALUE - 8;
}
```

**两个空数组常量的区别**：

| 常量 | 用途 |
|------|------|
| EMPTY_ELEMENTDATA | 用户明确指定容量为0时使用 |
| DEFAULTCAPACITY_EMPTY_ELEMENTDATA | 无参构造时使用，首次add时扩容到10 |

这个区分的意义在于：当用户调用`new ArrayList<>(0)`时，elementData被赋值为EMPTY_ELEMENTDATA，首次add时扩容到容量1；而调用`new ArrayList<>()`时，elementData被赋值为DEFAULTCAPACITY_EMPTY_ELEMENTDATA，首次add时扩容到默认容量10。

---

## 3. 构造方法分析

```java
// 构造方法1：指定初始容量
public ArrayList(int initialCapacity) {
    if (initialCapacity > 0) {
        this.elementData = new Object[initialCapacity];
    } else if (initialCapacity == 0) {
        this.elementData = EMPTY_ELEMENTDATA;
    } else {
        throw new IllegalArgumentException("Illegal Capacity: " + initialCapacity);
    }
}

// 构造方法2：无参构造，延迟初始化
public ArrayList() {
    this.elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA;
}

// 构造方法3：从已有集合构造
public ArrayList(Collection<? extends E> c) {
    elementData = c.toArray();
    if ((size = elementData.length) != 0) {
        // c.toArray()可能返回的不是Object[]类型（某些集合的实现问题）
        // 需要通过Arrays.copyOf转换类型
        if (elementData.getClass() != Object[].class)
            elementData = Arrays.copyOf(elementData, size, Object[].class);
    } else {
        // 空集合
        this.elementData = EMPTY_ELEMENTDATA;
    }
}
```

**延迟初始化**：无参构造方法不会立即创建容量为10的数组，而是使用一个共享的空数组。只有在第一次add时才创建实际数组。这是Java 8引入的优化，减少了空ArrayList的内存占用。在创建大量空ArrayList的场景下，这个优化可以节省显著的内存。

```java
// 构造方法3中的类型检查解释
// 某些集合的toArray()返回的数组类型不是Object[]
// 例如：
List<String> list = Arrays.asList("a", "b");
Object[] arr = list.toArray();
// arr的实际运行时类型可能是String[]，不是Object[]
// 后续如果往arr中放入非String对象会抛ArrayStoreException
```

---

## 4. add方法与扩容机制

```java
public boolean add(E e) {
    // 确保容量足够，minCapacity = size + 1
    ensureCapacityInternal(size + 1);

    // 将元素放入数组末尾，size加1
    elementData[size++] = e;
    return true;
}

private void ensureCapacityInternal(int minCapacity) {
    // 如果是默认空数组（无参构造首次add），取DEFAULT_CAPACITY和minCapacity的较大值
    if (elementData == DEFAULTCAPACITY_EMPTY_ELEMENTDATA) {
        minCapacity = Math.max(DEFAULT_CAPACITY, minCapacity);
    }

    ensureExplicitCapacity(minCapacity);
}

private void ensureExplicitCapacity(int minCapacity) {
    modCount++; // 修改次数+1，用于fail-fast

    // 如果需要的最小容量大于当前数组长度，执行扩容
    if (minCapacity - elementData.length > 0)
        grow(minCapacity);
}

// 核心扩容方法
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    // 新容量 = 旧容量的1.5倍
    int newCapacity = oldCapacity + (oldCapacity >> 1);

    // 如果新容量仍小于所需最小容量，直接使用最小容量
    if (newCapacity - minCapacity < 0)
        newCapacity = minCapacity;

    // 如果新容量超过最大限制，调用hugeCapacity处理
    if (newCapacity - MAX_ARRAY_SIZE > 0)
        newCapacity = hugeCapacity(minCapacity);

    // 将旧数组数据复制到新数组
    elementData = Arrays.copyOf(elementData, newCapacity);
}

private static int hugeCapacity(int minCapacity) {
    if (minCapacity < 0) // 溢出
        throw new OutOfMemoryError();
    return (minCapacity > MAX_ARRAY_SIZE) ?
        Integer.MAX_VALUE :
        MAX_ARRAY_SIZE;
}
```

**扩容流程详解**：

1. `add(e)` → `ensureCapacityInternal(size + 1)`
2. 如果是空数组首次add，minCapacity取max(10, 1) = 10
3. `ensureExplicitCapacity`：modCount++，判断是否需要扩容
4. 需要扩容时调用`grow`：新容量 = 旧容量 + 旧容量/2（即1.5倍）
5. 如果1.5倍仍不够（如addAll大量元素），直接使用minCapacity
6. `Arrays.copyOf`创建新数组并拷贝数据

**扩容过程示例**：

```
初始：elementData = DEFAULTCAPACITY_EMPTY_ELEMENTDATA, size = 0
add(1): grow(10) → elementData = new Object[10], size = 1
add(2)~add(10): 不扩容, size = 10
add(11): grow(11) → newCapacity = 10 + 5 = 15, elementData = new Object[15], size = 11
add(16): grow(16) → newCapacity = 15 + 7 = 22, elementData = new Object[22], size = 16
```

**为什么扩容1.5倍而不是2倍？**

- 1.5倍扩容：浪费的内存空间最多为33%，且每次扩容的增量不会太大
- 2倍扩容：浪费的内存空间最多为50%，内存消耗更大
- 1.5倍使得垃圾回收的旧数组可以被更好地复用（如果连续扩容，旧的2倍数组无法复用，而1.5倍的可以部分复用）
- 1.5是一个工程实践中的经验值，在内存利用率和扩容频率之间取得了较好的平衡

**为什么不用System.arraycopy而用Arrays.copyOf？**

`Arrays.copyOf`内部其实也调用了`System.arraycopy`：

```java
public static <T,U> T[] copyOf(U[] original, int newLength, Class<? extends T[]> newType) {
    @SuppressWarnings("unchecked")
    T[] copy = ((Object)newType == (Object)Object[].class)
        ? (T[]) new Object[newLength]
        : (T[]) Array.newInstance(newType.getComponentType(), newLength);
    System.arraycopy(original, 0, copy, 0, Math.min(original.length, newLength));
    return copy;
}
```

`Arrays.copyOf`封装了新数组创建和数据拷贝两步操作，代码更简洁。`System.arraycopy`是native方法，使用高效的内存拷贝实现。

---

## 5. 批量添加addAll方法

```java
public boolean addAll(Collection<? extends E> c) {
    Object[] a = c.toArray();
    int numNew = a.length;
    ensureCapacityInternal(size + numNew);  // 确保容量足够
    System.arraycopy(a, 0, elementData, size, numNew);  // 批量拷贝
    size += numNew;
    return numNew != 0;
}

public boolean addAll(int index, Collection<? extends E> c) {
    rangeCheckForAdd(index);

    Object[] a = c.toArray();
    int numNew = a.length;
    ensureCapacityInternal(size + numNew);

    // 计算需要移动的元素数量
    int numMoved = size - index;
    if (numMoved > 0)
        // 先把index位置及之后的元素往后移
        System.arraycopy(elementData, index, elementData, index + numNew, numMoved);

    // 再把新元素插入到index位置
    System.arraycopy(a, 0, elementData, index, numNew);
    size += numNew;
    return numNew != 0;
}
```

`addAll(int index, Collection c)`的插入过程示意（假设size=5，index=2，插入3个元素）：

```
操作前: [A, B, C, D, E, null, null, null]
                  ↑ index=2

步骤1: 移动C,D,E到index+3位置
       [A, B, C, D, E, C, D, E]
              ↑ index=2

步骤2: 将新元素X,Y,Z插入index位置
       [A, B, X, Y, Z, C, D, E]

size变为8
```

---

## 6. get与set方法

```java
// get方法：直接数组下标访问，O(1)
public E get(int index) {
    rangeCheck(index);  // 检查下标越界
    return elementData(index);
}

E elementData(int index) {
    return (E) elementData[index];
}

// set方法：替换指定位置的元素，返回旧值
public E set(int index, E element) {
    rangeCheck(index);
    E oldValue = elementData(index);
    elementData[index] = element;
    return oldValue;
}

private void rangeCheck(int index) {
    if (index >= size)
        throw new IndexOutOfBoundsException(outOfBoundsMsg(index));
}
```

**注意rangeCheck只检查上界不检查下界**。因为index如果为负数，`elementData[index]`会抛出`ArrayIndexOutOfBoundsException`（属于IndexOutOfBoundsException的子类），所以不需要额外检查。

get和set的时间复杂度都是O(1)，这也是RandomAccess标记接口的意义——表示这个集合支持高效的随机访问。

---

## 7. remove方法解析

### 7.1 按下标删除

```java
public E remove(int index) {
    rangeCheck(index);

    modCount++;
    E oldValue = elementData(index);

    // 计算需要移动的元素数量
    int numMoved = size - index - 1;
    if (numMoved > 0)
        // 将index后面的元素整体左移一位
        System.arraycopy(elementData, index + 1, elementData, index, numMoved);

    // 将最后一个元素置null，帮助GC回收
    elementData[--size] = null;

    return oldValue;
}
```

删除过程示意（删除index=2的元素）：

```
操作前: [A, B, C, D, E, null, null], size=5
                   ↑ index=2

arraycopy左移: [A, B, D, E, E, null, null], size仍为5
置null: [A, B, D, E, null, null, null], size=4
```

**为什么删除是O(n)？** 因为删除后需要将后续元素左移填补空缺，移动的元素数量平均为n/2。这也是ArrayList和LinkedList的核心区别之一——ArrayList查询快但增删慢（在中间位置时）。

### 7.2 按对象删除

```java
public boolean remove(Object o) {
    if (o == null) {
        // 遍历找第一个null元素
        for (int index = 0; index < size; index++)
            if (elementData[index] == null) {
                fastRemove(index);
                return true;
            }
    } else {
        // 遍历找第一个equals的元素
        for (int index = 0; index < size; index++)
            if (o.equals(elementData[index])) {
                fastRemove(index);
                return true;
            }
    }
    return false;
}

private void fastRemove(int index) {
    modCount++;
    int numMoved = size - index - 1;
    if (numMoved > 0)
        System.arraycopy(elementData, index + 1, elementData, index, numMoved);
    elementData[--size] = null;
}
```

`remove(Object o)`只删除**第一个**匹配的元素。注意它使用equals方法比较，所以自定义对象需要正确实现equals方法。

`fastRemove`和`remove(int index)`的区别在于：fastRemove不返回被删除的值，也不做rangeCheck（因为调用前已经通过遍历确认了index有效），性能略高。

### 7.3 clear方法

```java
public void clear() {
    modCount++;

    // 将所有元素置null，帮助GC
    for (int i = 0; i < size; i++)
        elementData[i] = null;

    size = 0;
}
```

clear方法将数组清空但**不缩小数组容量**。如果需要释放内存，可以调用`trimToSize()`方法：

```java
public void trimToSize() {
    modCount++;
    if (size < elementData.length) {
        elementData = (size == 0)
            ? EMPTY_ELEMENTDATA
            : Arrays.copyOf(elementData, size);
    }
}
```

---

## 8. 迭代器与fail-fast机制

### 8.1 modCount与fail-fast

ArrayList中有一个`modCount`字段（继承自AbstractList），记录集合被结构修改（增删）的次数。迭代器在创建时会记录当前的modCount（赋值给`expectedModCount`），每次迭代时检查两者是否一致，不一致则抛出`ConcurrentModificationException`。

```java
private class Itr implements Iterator<E> {
    int cursor;       // 下一个要返回的元素的index
    int lastRet = -1; // 上一次返回的元素的index，-1表示没有
    int expectedModCount = modCount; // 创建迭代器时的modCount快照

    public boolean hasNext() {
        return cursor != size;
    }

    @SuppressWarnings("unchecked")
    public E next() {
        checkForComodification();  // 检查是否被并发修改
        int i = cursor;
        if (i >= size)
            throw new NoSuchElementException();
        Object[] elementData = ArrayList.this.elementData;
        if (i >= elementData.length)
            throw new ConcurrentModificationException();
        cursor = i + 1;
        return (E) elementData[lastRet = i];
    }

    public void remove() {
        if (lastRet < 0)
            throw new IllegalStateException();
        checkForComodification();

        try {
            ArrayList.this.remove(lastRet);  // 调用外部类的remove
            cursor = lastRet;
            lastRet = -1;
            expectedModCount = modCount;  // 同步modCount
        } catch (IndexOutOfBoundsException ex) {
            throw new ConcurrentModificationException();
        }
    }

    // 检查并发修改
    final void checkForComodification() {
        if (modCount != expectedModCount)
            throw new ConcurrentModificationException();
    }
}
```

### 8.2 为什么迭代器remove不会抛异常？

迭代器的remove方法在调用外部类remove后，会同步更新`expectedModCount = modCount`，所以不会触发fail-fast检查。这也是为什么"遍历时删除元素必须使用迭代器的remove方法"的原因。

### 8.3 ListIterator

ArrayList还提供了ListIterator，支持双向遍历、添加和修改：

```java
private class ListItr extends Itr implements ListIterator<E> {
    ListItr(int index) {
        super();
        cursor = index;
    }

    public boolean hasPrevious() {
        return cursor != 0;
    }

    public int nextIndex() {
        return cursor;
    }

    public int previousIndex() {
        return cursor - 1;
    }

    @SuppressWarnings("unchecked")
    public E previous() {
        checkForComodification();
        int i = cursor - 1;
        if (i < 0)
            throw new NoSuchElementException();
        Object[] elementData = ArrayList.this.elementData;
        if (i >= elementData.length)
            throw new ConcurrentModificationException();
        cursor = i;
        return (E) elementData[lastRet = i];
    }

    public void set(E e) {
        if (lastRet < 0)
            throw new IllegalStateException();
        checkForComodification();
        try {
            ArrayList.this.set(lastRet, e);
        } catch (IndexOutOfBoundsException ex) {
            throw new ConcurrentModificationException();
        }
    }

    public void add(E e) {
        checkForComodification();
        try {
            int i = cursor;
            ArrayList.this.add(i, e);
            cursor = i + 1;
            lastRet = -1;
            expectedModCount = modCount;
        } catch (IndexOutOfBoundsException ex) {
            throw new ConcurrentModificationException();
        }
    }
}
```

### 8.4 fail-fast的局限

fail-fast机制是**尽力检测**而非**保证安全**的策略。它不能保证在所有并发修改场景下都抛出异常，只是作为一种诊断手段。它不能替代真正的线程安全方案。

---

## 9. 序列化机制

ArrayList实现了Serializable接口，但`elementData`被标记为`transient`：

```java
transient Object[] elementData;
```

**为什么elementData是transient？** 因为elementData数组可能包含大量未使用的空间（容量 > size），序列化这些null是浪费。ArrayList自定义了序列化逻辑，只序列化实际存储的元素。

```java
private void writeObject(java.io.ObjectOutputStream s)
    throws java.io.IOException{
    int expectedModCount = modCount;
    s.defaultWriteObject();  // 写入非transient字段（如size）

    // 写入数组容量（兼容性考虑）
    s.writeInt(size);

    // 只写入实际元素，不写null
    for (int i = 0; i < size; i++) {
        s.writeObject(elementData[i]);
    }

    if (modCount != expectedModCount) {
        throw new ConcurrentModificationException();
    }
}

private void readObject(java.io.ObjectInputStream s)
    throws java.io.IOException, ClassNotFoundException {
    s.defaultReadObject();  // 读取非transient字段

    // 读取容量（虽然不直接使用，但需要消费这个值）
    s.readInt();

    if (size > 0) {
        Object[] elements = new Object[size];  // 创建刚好size大小的数组
        for (int i = 0; i < size; i++) {
            elements[i] = s.readObject();
        }
        elementData = elements;
    } else {
        elementData = EMPTY_ELEMENTDATA;
    }
}
```

**序列化过程**：
1. `defaultWriteObject()`写入size等非transient字段
2. 写入size（作为容量信息）
3. 逐个写入`elementData[0]`到`elementData[size-1]`

**反序列化过程**：
1. `defaultReadObject()`读取size等字段
2. 读取容量值（忽略）
3. 创建size大小的数组，逐个读取元素

---

## 10. subList与线程安全

### 10.1 subList方法

```java
public List<E> subList(int fromIndex, int toIndex) {
    subListRangeCheck(fromIndex, toIndex, size);
    return new SubList(this, 0, fromIndex, toIndex);
}
```

**关键点**：subList返回的视图不是独立的ArrayList，而是原ArrayList的一个视图。对subList的修改会影响原List，反之亦然。

```java
// SubList类（简化版）
private class SubList extends AbstractList<E> implements RandomAccess {
    private final ArrayList<E> parent;
    private final int parentOffset;
    private final int offset;
    int size;

    SubList(ArrayList<E> parent, int offset, int fromIndex, int toIndex) {
        this.parent = parent;
        this.parentOffset = fromIndex;
        this.offset = offset + fromIndex;
        this.size = toIndex - fromIndex;
        this.modCount = ArrayList.this.modCount;
    }

    public E set(int index, E e) {
        rangeCheck(index);
        checkForComodification();
        E oldValue = ArrayList.this.elementData(offset + index);
        ArrayList.this.elementData[offset + index] = e;
        return oldValue;
    }

    public E get(int index) {
        rangeCheck(index);
        checkForComodification();
        return ArrayList.this.elementData(offset + index);
    }

    // ... 其他方法都是直接操作原ArrayList的elementData
}
```

**使用陷阱**：

```java
List<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5));
List<Integer> sub = list.subList(1, 4); // [2, 3, 4]

// 陷阱1：修改subList会影响原List
sub.set(0, 20);
// list变为 [1, 20, 3, 4, 5]

// 陷阱2：结构性修改原List后使用subList会抛ConcurrentModificationException
list.add(6);
sub.get(0); // 抛异常！因为modCount不一致

// 陷阱3：subList的remove会影响原List
sub.clear();
// list变为 [1, 5, 6]
```

### 10.2 线程安全

ArrayList是**线程不安全**的。多线程下的问题包括：

1. **数据覆盖**：两个线程同时执行`elementData[size++] = e`，可能写入同一个位置
2. **size不准**：size++不是原子操作
3. **扩容竞态**：多线程同时触发扩容，可能导致数据丢失

**线程安全方案**：

```java
// 方案1：Collections.synchronizedList
List<String> syncList = Collections.synchronizedList(new ArrayList<>());

// 方案2：CopyOnWriteArrayList（读多写少场景）
List<String> cowList = new CopyOnWriteArrayList<>();

// 方案3：手动加锁
synchronized (list) {
    // 操作
}
```

**CopyOnWriteArrayList**的原理：写操作时复制整个数组，读操作不加锁。适合读多写少的场景，但写操作开销大。

---

## 11. 面试题速查

**Q1: ArrayList的默认容量是多少？**
> JDK 1.7中无参构造直接创建容量为10的数组。JDK 1.8中无参构造使用空数组，首次add时才扩容到10（延迟初始化优化）。

**Q2: ArrayList的扩容机制是什么？**
> 每次扩容为原来的1.5倍（oldCapacity + oldCapacity >> 1）。如果1.5倍仍不够（如addAll大量元素），直接使用所需的最小容量。扩容通过Arrays.copyOf创建新数组并拷贝数据。

**Q3: ArrayList和LinkedList的区别？**
> ①底层结构：ArrayList是数组，LinkedList是双向链表；②随机访问：ArrayList O(1)，LinkedList O(n)；③增删：ArrayList中间增删O(n)（需移动元素），LinkedList头尾增删O(1)；④内存：ArrayList连续内存，LinkedList每个节点额外存储前后指针。

**Q4: ArrayList为什么是线程不安全的？**
> 多线程下size++不是原子操作，可能导致数据覆盖或size统计不准。多线程扩容可能产生竞态条件。解决方案：CopyOnWriteArrayList、Collections.synchronizedList或手动加锁。

**Q5: ArrayList的elementData为什么用transient修饰？**
> elementData数组的容量可能远大于实际元素个数，序列化大量null浪费空间。ArrayList自定义了writeObject/readObject方法，只序列化size范围内的实际元素。

**Q6: 遍历ArrayList时删除元素有哪些方式？**
> ①迭代器的remove方法（推荐）；②从后往前遍历+remove(index)；③Java 8的removeIf方法。**不能**使用for-each + list.remove()，会抛ConcurrentModificationException。

**Q7: ArrayList的fail-fast机制是什么？**
> ArrayList维护modCount记录结构修改次数。迭代器创建时记录expectedModCount=modCount。每次迭代检查两者是否一致，不一致则抛ConcurrentModificationException。这是尽力检测机制，不保证所有并发修改都能被检测到。

**Q8: ArrayList和Vector的区别？**
> ①线程安全：Vector线程安全（方法加synchronized），ArrayList不安全；②扩容：ArrayList扩容1.5倍，Vector扩容2倍（可配置increment）；③性能：Vector性能差于ArrayList。Vector已不推荐使用。

**Q9: randomAccess接口有什么作用？**
> 这是一个标记接口（无方法），表示实现类支持快速随机访问。工具方法（如Collections.binarySearch）会根据是否实现此接口选择不同的遍历策略：实现了用索引遍历，没实现用迭代器遍历。

**Q10: ArrayList的subList有什么坑？**
> subList返回的是原List的视图而非副本。①修改subList会影响原List；②结构性修改原List后再操作subList会抛ConcurrentModificationException；③subList的增删也会反映到原List。如果需要独立副本，应`new ArrayList<>(list.subList(...))`。

**Q11: ArrayList为什么扩容1.5倍而不是2倍？**
> 1.5倍在内存利用率和扩容频率间取得平衡。2倍扩容虽然减少扩容次数，但内存浪费大（最多50%），且旧数组难以被复用。1.5倍扩容下，连续扩容产生的旧数组可以被部分复用，减少GC压力。

**Q12: new ArrayList<>(0)和new ArrayList<>()有什么区别？**
> 前者使用EMPTY_ELEMENTDATA，首次add时扩容到容量1；后者使用DEFAULTCAPACITY_EMPTY_ELEMENTDATA，首次add时扩容到容量10。这个区分是为了让用户精确控制空集合的首次扩容行为。
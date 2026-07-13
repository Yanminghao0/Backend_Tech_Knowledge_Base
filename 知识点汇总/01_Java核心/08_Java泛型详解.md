# Java泛型详解

> 泛型是Java 5引入的重要特性，它提供了编译时类型安全检查机制，允许开发者在编译期检测到类型错误，而非运行时抛出ClassCastException。泛型的本质是参数化类型——将类型作为参数传递给类、接口和方法，从而实现代码的复用性与类型安全性的统一。理解泛型的底层原理（类型擦除）、通配符机制（PECS原则）以及泛型在反射中的表现，是Java工程师从"会用"到"精通"的必经之路。

---

## 📋 目录

1. [泛型概述](#1-泛型概述)
2. [泛型类、接口与方法](#2-泛型类接口与方法)
3. [类型擦除原理](#3-类型擦除原理)
4. [通配符与PECS原则](#4-通配符与pecs原则)
5. [泛型的约束与限制](#5-泛型的约束与限制)
6. [类型令牌Class\<T\>](#6-类型令牌classt)
7. [泛型与反射](#7-泛型与反射)
8. [实战场景](#8-实战场景)
9. [面试题速查](#9-面试题速查)

---

## 1. 泛型概述

### 1.1 为什么需要泛型

在Java 5之前，集合框架中的元素类型是`Object`，这意味着你可以往集合中放入任何类型的对象，但在取出时必须强制类型转换，这种转换在编译期无法检查，极易引发运行时`ClassCastException`。

```java
// 泛型之前的写法——隐患重重
List list = new ArrayList();
list.add("hello");
list.add(100);        // 编译通过，运行时也不报错

String str = (String) list.get(1);  // 运行时抛出 ClassCastException
```

引入泛型后：

```java
// 泛型写法——编译期即可发现错误
List<String> list = new ArrayList<>();
list.add("hello");
list.add(100);        // 编译错误：不兼容的类型

String str = list.get(0);  // 无需强制转换
```

### 1.2 泛型的核心价值

| 特性 | 说明 |
|------|------|
| **类型安全** | 编译期检查类型，消除运行时ClassCastException |
| **消除强制转换** | 取出元素时无需显式cast，代码更简洁 |
| **代码复用** | 一套逻辑适用于多种类型，避免重复编写 |
| **可读性增强** | 类型参数本身就是一种文档，`List<String>`一目了然 |

### 1.3 泛型的命名约定

按照惯例，类型参数使用单个大写字母：

| 标识 | 含义 | 常见场景 |
|------|------|----------|
| `T` | Type（类型） | 通用类型参数 |
| `E` | Element（元素） | 集合中的元素类型 |
| `K` | Key（键） | 映射的键类型 |
| `V` | Value（值） | 映射的值类型 |
| `R` | Result（结果） | 方法返回值类型 |
| `S`、`U` | 第二、第三类型 | 多类型参数场景 |

---

## 2. 泛型类、接口与方法

### 2.1 泛型类

泛型类是在类名后使用尖括号声明类型参数的类。类型参数可以在整个类中使用。

```java
/**
 * 通用的键值对容器
 * @param <K> 键的类型
 * @param <V> 值的类型
 */
public class Pair<K, V> {
    private final K key;
    private final V value;

    public Pair(K key, V value) {
        this.key = key;
        this.value = value;
    }

    public K getKey() { return key; }
    public V getValue() { return value; }

    @Override
    public String toString() {
        return "(" + key + ", " + value + ")";
    }
}

// 使用
Pair<String, Integer> pair = new Pair<>("age", 25);
Pair<String, String> namePair = new Pair<>("name", "张三");
```

### 2.2 泛型接口

泛型接口的定义方式与泛型类类似。实现类可以选择指定具体类型，也可以继续保留类型参数。

```java
// 泛型接口定义
public interface Repository<T, ID> {
    T findById(ID id);
    List<T> findAll();
    T save(T entity);
    void deleteById(ID id);
}

// 方式一：实现时指定具体类型
public class UserRepository implements Repository<User, Long> {
    @Override
    public User findById(Long id) { /* ... */ return null; }

    @Override
    public List<User> findAll() { /* ... */ return null; }

    @Override
    public User save(User entity) { /* ... */ return null; }

    @Override
    public void deleteById(Long id) { /* ... */ }
}

// 方式二：实现时保留类型参数
public abstract class AbstractRepository<T, ID> implements Repository<T, ID> {
    // 子类再指定具体类型
    protected abstract Class<T> getEntityClass();

    @Override
    public T findById(ID id) {
        // 通用实现逻辑
        return null;
    }
}
```

### 2.3 泛型方法

泛型方法是在返回值前使用`<T>`声明类型参数的方法。泛型方法所在的类可以是普通类，不需要是泛型类。

```java
public class GenericUtils {

    // 基本泛型方法
    public static <T> T getFirst(List<T> list) {
        if (list == null || list.isEmpty()) {
            return null;
        }
        return list.get(0);
    }

    // 多类型参数的泛型方法
    public static <K, V> Map<K, V> zip(K[] keys, V[] values) {
        Map<K, V> map = new HashMap<>();
        int len = Math.min(keys.length, values.length);
        for (int i = 0; i < len; i++) {
            map.put(keys[i], values[i]);
        }
        return map;
    }

    // 带上限约束的泛型方法
    public static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    // 可变参数 + 泛型
    @SafeVarargs
    public static <T> List<T> of(T... elements) {
        List<T> list = new ArrayList<>();
        Collections.addAll(list, elements);
        return list;
    }
}

// 使用
String first = GenericUtils.getFirst(List.of("a", "b", "c"));
Integer maxVal = GenericUtils.max(3, 7);
List<Integer> nums = GenericUtils.of(1, 2, 3, 4, 5);
```

### 2.4 类型参数的边界

Java泛型支持上限边界（`extends`）和多重边界：

```java
// 单一上限：T必须是Number或其子类
public class NumberBox<T extends Number> {
    private T value;
    public double doubleValue() {
        return value.doubleValue();
    }
}

// 多重上限：T必须同时继承Number并实现Comparable
public static <T extends Number & Comparable<T>> T findMax(List<T> list) {
    T max = list.get(0);
    for (T item : list) {
        if (item.compareTo(max) > 0) {
            max = item;
        }
    }
    return max;
}

// 注意：多重边界中，类必须放在第一位
// <T extends Comparable<T> & Number>  // 编译错误，类不在首位
// <T extends Number & Comparable<T> & Serializable>  // 正确
```

> ⚠️ Java泛型不支持下限边界（`super`）用于类型参数声明，下限仅用于通配符。

---

## 3. 类型擦除原理

### 3.1 什么是类型擦除

类型擦除是Java泛型最核心的底层机制。Java在编译期使用泛型进行类型检查，但在生成的字节码中，泛型类型信息会被擦除，替换为其上界（默认为`Object`）。这意味着泛型是编译期机制，运行时不存在泛型类型信息。

```java
// 你写的代码
List<String> stringList = new ArrayList<>();
List<Integer> intList = new ArrayList<>();

// 编译后的字节码等价于
List stringList = new ArrayList();
List intList = new ArrayList();

// 运行时两者类型相同
System.out.println(stringList.getClass() == intList.getClass());  // true
```

### 3.2 擦除规则

| 原始类型 | 擦除后类型 |
|----------|------------|
| `T`（无边界） | `Object` |
| `T extends Number` | `Number` |
| `T extends Comparable<T>` | `Comparable` |
| `List<String>` | `List` |
| `Map<K, V>` | `Map` |

### 3.3 擦除过程详解

编译器在擦除泛型时，主要做以下三件事：

1. **替换类型参数**：将所有类型参数替换为其上界（无上界则为`Object`）
2. **插入强制转换**：在调用处自动插入checkcast指令
3. **生成桥接方法**：在继承泛型类/接口时，保持多态正确性

```java
// 原始代码
public class Container<T> {
    private T value;
    public T getValue() { return value; }
    public void setValue(T value) { this.value = value; }
}

// 擦除后等价代码
public class Container {
    private Object value;
    public Object getValue() { return value; }
    public void setValue(Object value) { this.value = value; }
}

// 使用时编译器自动插入强制转换
Container<String> c = new Container<>();
c.setValue("hello");
String s = c.getValue();
// 编译后等价于：
// String s = (String) c.getValue();
```

### 3.4 桥接方法

当子类泛型类指定具体类型并覆盖父类方法时，由于类型擦除，父类方法的签名与子类不同。编译器会自动生成桥接方法来维持多态。

```java
// 父类
public class Node<T> {
    private T value;
    public void setValue(T value) { this.value = value; }
}

// 子类指定具体类型
public class StringNode extends Node<String> {
    @Override
    public void setValue(String value) {
        System.out.println("Setting: " + value);
        super.setValue(value);
    }
}

// 擦除后，父类Node的setValue参数为Object
// 子类StringNode的setValue参数为String
// 多态调用时：Node node = new StringNode(); node.setValue(object);
// 需要桥接方法来转发

// 编译器为StringNode生成的桥接方法：
// public void setValue(Object value) {
//     setValue((String) value);  // 转发给真正的setValue
// }
```

验证桥接方法的存在：

```java
import java.lang.reflect.Method;

public class BridgeMethodDemo {
    public static void main(String[] args) {
        for (Method m : StringNode.class.getMethods()) {
            if (m.getName().equals("setValue")) {
                System.out.println(m + " — bridge: " + m.isBridge());
            }
        }
        // 输出：
        // public void StringNode.setValue(java.lang.String) — bridge: false
        // public void StringNode.setValue(java.lang.Object) — bridge: true
    }
}
```

### 3.5 类型擦除的副作用

```java
// 1. 运行时无法获取泛型类型
if (list instanceof List<String>) { }  // 编译错误

// 2. 无法创建泛型数组
List<String>[] array = new List<String>[10];  // 编译错误

// 3. 无法重载仅泛型参数不同的方法
public void process(List<String> list) { }
public void process(List<Integer> list) { }  // 编译错误：方法签名相同（擦除后都是process(List)）

// 4. 静态上下文中不能使用类的类型参数
public class GenericClass<T> {
    private static T instance;  // 编译错误
    public static T getInstance() { return null; }  // 编译错误
}
```

---

## 4. 通配符与PECS原则

### 4.1 无界通配符 `?`

无界通配符`<?>`表示未知类型，适用于不关心具体类型参数的场景。

```java
// 打印任意类型的List
public static void printList(List<?> list) {
    for (Object item : list) {
        System.out.println(item);
    }
}

// List<?> 与 List<Object> 的区别
List<Object> objList = new ArrayList<>();
List<?> wildcardList = new ArrayList<>();

// objList.add("string");  // 可以，String是Object子类
// wildcardList.add("string");  // 编译错误：无法添加（null除外）
// wildcardList.add(null);  // 唯一例外
```

### 4.2 上界通配符 `? extends T`

`? extends T`表示T或T的子类型。用于只读场景（生产者）。

```java
// 读取Number及其子类的集合
public static double sum(List<? extends Number> numbers) {
    double total = 0;
    for (Number n : numbers) {
        total += n.doubleValue();  // 可以安全读取
    }
    return total;
}

// 使用
List<Integer> ints = List.of(1, 2, 3);
List<Double> doubles = List.of(1.0, 2.0, 3.0);
System.out.println(sum(ints));    // 6.0
System.out.println(sum(doubles)); // 6.0

// 但不能写入
// numbers.add(1);     // 编译错误
// numbers.add(1.0);   // 编译错误
// numbers.add(null);  // 仅null可以
```

**为什么不能写入？** 因为编译器只知道集合中存放的是Number的某个子类型，但不知道具体是哪个子类型。如果允许添加Integer，但实际集合是`List<Double>`，就会破坏类型安全。

### 4.3 下界通配符 `? super T`

`? super T`表示T或T的父类型。用于只写场景（消费者）。

```java
// 向集合中添加Integer及其父类型可接受的元素
public static void addNumbers(List<? super Integer> list) {
    list.add(1);
    list.add(2);
    list.add(3);
    // 可以写入Integer（及其子类，但Integer是final的）

    // 读取时只能得到Object
    Object obj = list.get(0);  // 安全但不太有用
}

// 使用
List<Number> numberList = new ArrayList<>();
addNumbers(numberList);  // OK，Number是Integer的父类

List<Object> objectList = new ArrayList<>();
addNumbers(objectList);  // OK，Object是Integer的父类

// List<Double> doubleList = new ArrayList<>();
// addNumbers(doubleList);  // 编译错误：Double不是Integer的父类
```

### 4.4 PECS原则

**PECS = Producer Extends, Consumer Super**

- 如果你需要从集合**读取**数据（集合是生产者），使用`? extends T`
- 如果你需要向集合**写入**数据（集合是消费者），使用`? super T`
- 如果既需要读又需要写，不使用通配符

```java
// 经典示例：将src中的元素复制到dest
public static <T> void copy(List<? super T> dest, List<? extends T> src) {
    for (T item : src) {       // src是生产者，用extends
        dest.add(item);        // dest是消费者，用super
    }
}

// JDK中Collections.copy的签名正是如此：
// public static <T> void copy(List<? super T> dest, List<? extends T> src)

// 另一个经典例子：JDK的Comparable/Comparator
// Collections.sort 方法：
// public static <T> Comparable<? super T> ...
// T的比较器可以是T的父类实现的比较器
```

### 4.5 通配符捕获

有时候编译器能够推断出通配符的实际类型，这称为通配符捕获。

```java
// 交换List中两个元素的位置
public static void swap(List<?> list, int i, int j) {
    // list.set(i, list.get(j));  // 编译错误：?类型不匹配
    swapHelper(list, i, j);
}

// 辅助方法利用类型推断捕获通配符
private static <T> void swapHelper(List<T> list, int i, int j) {
    T temp = list.get(i);
    list.set(i, list.get(j));
    list.set(j, temp);
}
```

---

## 5. 泛型的约束与限制

### 5.1 不能实例化类型参数

```java
public class GenericFactory<T> {
    // 编译错误：不能直接 new T()
    // public T create() { return new T(); }

    // 正确做法：通过Class<T> + 反射
    private Class<T> clazz;
    public GenericFactory(Class<T> clazz) { this.clazz = clazz; }
    public T create() throws Exception {
        return clazz.getDeclaredConstructor().newInstance();
    }
}
```

### 5.2 不能使用基本类型作为类型参数

```java
// List<int> list = new ArrayList<>();    // 编译错误
List<Integer> list = new ArrayList<>();   // 正确，使用包装类
```

这是因为类型擦除后类型参数变为`Object`，而基本类型不是`Object`的子类。Java自动装箱/拆箱会在`int`和`Integer`之间转换。

### 5.3 不能声明泛型静态字段

```java
public class Singleton<T> {
    // private static T instance;  // 编译错误

    // 泛型类的静态方法也不能使用类的类型参数
    // public static T getInstance() { ... }  // 编译错误

    // 但静态方法可以有自己的类型参数
    public static <E> List<E> singletonList(E element) {
        List<E> list = new ArrayList<>();
        list.add(element);
        return list;
    }
}
```

### 5.4 不能创建泛型数组

```java
// List<String>[] array = new List<String>[10];  // 编译错误

// 原因：数组是协变的，泛型是不变的，两者冲突
// 如果允许，会引发类型安全问题：
// List<String>[] array = new List<String>[10];
// Object[] objArray = array;          // 数组是协变的，编译通过
// objArray[0] = new List<Integer>();  // 运行时ArrayStoreException不会触发
// String s = array[0].get(0);         // ClassCastException

// 替代方案：使用List<List<String>> 或 Object[] + cast
@SuppressWarnings("unchecked")
List<String>[] array = (List<String>[]) new List[10];  // 不推荐，有警告
```

### 5.5 不能catch泛型异常类

```java
// 不能定义泛型异常类
// public class MyException<T> extends Exception { }  // 编译错误

// 不能catch泛型类型
// try { ... } catch (T e) { }  // 编译错误

// 但可以catch具体异常类型
try {
    // ...
} catch (SQLException e) {
    // ...
}
```

### 5.6 instanceof 与泛型

```java
List<String> list = new ArrayList<>();

// if (list instanceof List<String>) { }  // 编译错误：运行时无泛型信息
if (list instanceof List<?>) { }          // 正确
if (list instanceof ArrayList) { }        // 正确（原始类型）
```

---

## 6. 类型令牌Class\<T\>

类型令牌（Type Token）是解决类型擦除导致运行时无法获取泛型类型信息的经典模式。通过传递`Class<T>`对象，在运行时保留类型信息。

### 6.1 基本用法

```java
public class TypeSafeContainer {
    private Map<Class<?>, Object> container = new HashMap<>();

    // 存储时记录类型
    public <T> void put(Class<T> type, T instance) {
        container.put(type, instance);
    }

    // 取出时安全转换
    public <T> T get(Class<T> type) {
   
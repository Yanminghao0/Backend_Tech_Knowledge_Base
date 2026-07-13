# Java泛型详解

> 泛型是Java 5引入的最重要特性之一，它让集合API从"万能Object"进化为"类型安全"的利器。然而泛型的实现机制——类型擦除，又让它区别于C++模板和C#泛型，产生了诸多"坑"和"奇技淫巧"。本文从语法到原理、从约束到实战，全面剖析Java泛型。

---

## 📋 目录

1. [泛型概述与设计动机](#1-泛型概述与设计动机)
2. [泛型类与泛型接口](#2-泛型类与泛型接口)
3. [泛型方法](#3-泛型方法)
4. [类型擦除原理深度剖析](#4-类型擦除原理深度剖析)
5. [通配符与PECS原则](#5-通配符与pecs原则)
6. [泛型约束与限制](#6-泛型约束与限制)
7. [类型令牌与Super Type Token](#7-类型令牌与super-type-token)
8. [泛型与反射](#8-泛型与反射)
9. [实战场景：泛型DAO模式](#9-实战场景泛型dao模式)
10. [实战场景：泛型Builder模式](#10-实战场景泛型builder模式)
11. [面试题速查](#11-面试题速查)

---

## 1. 泛型概述与设计动机

### 1.1 没有泛型的时代

在Java 5之前，集合框架只能存储`Object`类型，使用时需要强制类型转换：

```java
// Java 5 之前的写法
List list = new ArrayList();
list.add("hello");
list.add(123); // 编译通过，但运行时取出来就是个坑

String str = (String) list.get(0); // 正常
String str2 = (String) list.get(1); // ClassCastException！
```

这种写法的问题显而易见：
- **类型不安全**：编译器无法阻止你往List里塞任何对象
- **需要强转**：每次取出都要强制类型转换，代码冗余
- **错误延迟**：类型错误在运行时才暴露，而不是编译期

### 1.2 泛型带来的好处

```java
// 使用泛型
List<String> list = new ArrayList<>();
list.add("hello");
list.add(123); // 编译错误！编译期就能发现问题

String str = list.get(0); // 无需强转
```

泛型的核心价值：
1. **编译期类型检查**：将运行时的`ClassCastException`前移到编译期
2. **消除强制转换**：代码更简洁、更安全
3. **代码复用**：一套逻辑适用于多种类型

### 1.3 泛型的本质

Java泛型是**编译时特性**（compile-time feature），也叫"伪泛型"。编译器在编译时做类型检查，然后在字节码中擦除泛型信息。这与C#的"真泛型"（运行时也存在类型信息）有本质区别。

```java
// 编译后，以下两个方法签名完全相同——都是 erase(List)
// 这就是"类型擦除"导致的"方法签名冲突"
// public void process(List<String> list) {}
// public void process(List<Integer> list) {} // 编译错误！
```

---

## 2. 泛型类与泛型接口

### 2.1 泛型类基本语法

泛型类在类名后用尖括号声明类型参数：

```java
/**
 * 一个简单的泛型容器
 * @param <T> 存储的元素类型
 */
public class Box<T> {
    private T value;

    public Box(T value) {
        this.value = value;
    }

    public T getValue() {
        return value;
    }

    public void setValue(T value) {
        this.value = value;
    }

    public <U> void inspect(U other) {
        System.out.println("T: " + value.getClass().getName());
        System.out.println("U: " + other.getClass().getName());
    }
}
```

使用方式：

```java
Box<String> stringBox = new Box<>("Hello");
Box<Integer> intBox = new Box<>(42);

// 菱形语法（Diamond），Java 7+
Box<Double> doubleBox = new Box<>(3.14);
```

### 2.2 多类型参数

```java
public class Pair<K, V> {
    private final K key;
    private final V value;

    public Pair(K key, V value) {
        this.key = key;
        this.value = value;
    }

    public K getKey() { return key; }
    public V getValue() { return value; }
}

Pair<String, Integer> person = new Pair<>("Alice", 30);
```

### 2.3 泛型接口

```java
public interface Comparable<T> {
    int compareTo(T o);
}

public interface Repository<T, ID> {
    T findById(ID id);
    List<T> findAll();
    T save(T entity);
    void delete(ID id);
}

// 实现方式1：指定具体类型
public class UserRepository implements Repository<User, Long> {
    @Override
    public User findById(Long id) { /* ... */ }

    @Override
    public List<User> findAll() { /* ... */ }

    @Override
    public User save(User entity) { /* ... */ }

    @Override
    public void delete(Long id) { /* ... */ }
}

// 实现方式2：保留泛型参数
public abstract class AbstractRepository<T, ID> implements Repository<T, ID> {
    // 子类再指定具体类型
}
```

### 2.4 类型参数命名约定

Java社区约定类型参数使用单个大写字母：

| 类型参数 | 含义 | 常见场景 |
|---------|------|---------|
| `T` | Type | 通用类型 |
| `E` | Element | 集合元素类型 |
| `K` | Key | 映射的键类型 |
| `V` | Value | 映射的值类型 |
| `N` | Number | 数字类型 |
| `R` | Result | 返回值类型 |
| `S`, `U`, `V` | 第二、三、四类型 | 多类型参数 |

---

## 3. 泛型方法

### 3.1 泛型方法语法

泛型方法独立于类，可以在普通类中定义。关键是在返回值前用`<T>`声明类型参数：

```java
public class GenericMethods {

    // 泛型方法：<T> 声明类型参数，T 是返回类型
    public static <T> T getFirst(List<T> list) {
        if (list == null || list.isEmpty()) {
            return null;
        }
        return list.get(0);
    }

    // 多类型参数的泛型方法
    public static <K, V> void printPair(K key, V value) {
        System.out.println(key + " = " + value);
    }

    // 带上界的泛型方法
    public static <T extends Comparable<T>> T max(List<T> list) {
        if (list.isEmpty()) {
            throw new IllegalArgumentException("List is empty");
        }
        T result = list.get(0);
        for (T item : list) {
            if (item.compareTo(result) > 0) {
                result = item;
            }
        }
        return result;
    }
}
```

### 3.2 类型推断

Java编译器能根据上下文推断类型参数，大多数情况下无需显式指定：

```java
// Java 7 之前需要显式指定
String first = GenericMethods.<String>getFirst(stringList);

// Java 7+ 自动推断
String first = GenericMethods.getFirst(stringList);

// Java 8+ 更强的类型推断
Map<String, List<Integer>> map = new HashMap<>(); // 菱形推断
List<Integer> numbers = Arrays.asList(1, 2, 3); // 自动推断T=Integer
```

### 3.3 可变参数与泛型方法

```java
@SafeVarargs // 抑制堆污染警告（Java 7+）
public static <T> List<T> of(T... elements) {
    List<T> list = new ArrayList<>();
    for (T element : elements) {
        list.add(element);
    }
    return list;
}

// 使用
List<String> names = of("Alice", "Bob", "Charlie");
List<Integer> nums = of(1, 2, 3);
```

> ⚠️ **注意**：泛型可变参数存在"堆污染"（Heap Pollution）风险，因为Java泛型是类型擦除的，可变参数实际上是一个`Object[]`。

---

## 4. 类型擦除原理深度剖析

### 4.1 什么是类型擦除

类型擦除（Type Erasure）是Java泛型的核心机制。编译器在编译时：

1. 检查泛型类型的使用是否正确
2. 将泛型类型参数擦除为其上界（默认为`Object`）
3. 在需要类型转换的地方自动插入checkcast指令

```java
// 你写的代码
public class Box<T> {
    private T value;
    public T getValue() { return value; }
    public void setValue(T value) { this.value = value; }
}

// 编译器擦除后的等效代码（伪代码）
public class Box {
    private Object value;
    public Object getValue() { return value; }
    public void setValue(Object value) { this.value = value; }
}
```

### 4.2 擦除规则

```java
// 带上界的情况
public class NumberBox<T extends Number> {
    private T value;
    public T getValue() { return value; }
}

// 擦除后 —— T被替换为上界Number
public class NumberBox {
    private Number value;
    public Number getValue() { return value; }
}
```

擦除规则总结：
- 无上界的类型参数 → 擦除为`Object`
- 有上界的类型参数 → 擦除为第一个上界
- 多上界（`T extends A & B`）→ 擦除为第一个上界A

### 4.3 桥接方法

当泛型类被继承且类型参数被具体化时，编译器会生成"桥接方法"来保证多态正确：

```java
class Node<T> {
    private T value;
    public void setValue(T value) { this.value = value; }
}

class StringNode extends Node<String> {
    @Override
    public void setValue(String value) { super.setValue(value); }
}
```

编译后，`StringNode`实际上有两个方法：

```java
// 擦除后父类的方法签名是 setValue(Object)
// 子类Override的方法签名是 setValue(String)
// 为了多态，编译器生成桥接方法：
public void setValue(Object value) {
    setValue((String) value); // 调用真正的setValue(String)
}
```

### 4.4 类型擦除的证据

```java
List<String> strings = new ArrayList<>();
List<Integer> integers = new ArrayList<>();

// 运行时两者的class完全相同
System.out.println(strings.getClass());  // class java.util.ArrayList
System.out.println(integers.getClass()); // class java.util.ArrayList
System.out.println(strings.getClass() == integers.getClass()); // true

// 以下操作在运行时是等价的（类型信息已擦除）
// strings.getClass().getMethod("add", Object.class);
```

### 4.5 类型擦除带来的后果

```java
// 后果1：不能使用基本类型作为类型参数（需用包装类）
// List<int> list; // 编译错误
List<Integer> list = new ArrayList<>(); // 正确

// 后果2：不能new类型参数
public class Factory<T> {
    // T item = new T(); // 编译错误
    // 不能创建泛型数组：T[] arr = new T[10]; // 编译错误
}

// 后果3：不能使用instanceof泛型类型
// if (list instanceof List<String>) {} // 编译错误
if (list instanceof List<?>) {} // 正确

// 后果4：不能声明泛型静态字段/方法
public class Container<T> {
    // private static T instance; // 编译错误：T是实例级别的
    // public static T getInstance() {} // 编译错误

    // 但泛型静态方法可以——它有自己的类型参数声明
    public static <U> U create(Supplier<U> supplier) {
        return supplier.get();
    }
}
```

---

## 5. 通配符与PECS原则

### 5.1 无界通配符 `<?>`

```java
// 打印任意类型的List
public static void printList(List<?> list) {
    for (Object item : list) {
        System.out.println(item);
    }
}

printList(Arrays.asList(1, 2, 3));   // ✅
printList(Arrays.asList("a", "b"));  // ✅
```

`List<?>`与`List<Object>`的区别：
- `List<Object>`：只能接收`List<Object>`，不能接收`List<String>`
- `List<?>`：可以接收任何类型的List

### 5.2 上界通配符 `<? extends T>`

```java
// 接受Number及其子类型的List
public static double sum(List<? extends Number> list) {
    double total = 0;
    for (Number num : list) {
        total += num.doubleValue();
    }
    return total;
}

sum(Arrays.asList(1, 2, 3));       // List<Integer>
sum(Arrays.asList(1.0, 2.0));      // List<Double>
sum(Arrays.asList(1L, 2L));        // List<Long>
```

**关键限制**：`<? extends T>`的List是**只读的**（不能添加元素）：

```java
public static void addNumber(List<? extends Number> list) {
    // list.add(1);    // 编译错误！
    // list.add(1.0);  // 编译错误！
    // list.add(null); // 唯一能添加的

    Number n = list.get(0); // ✅ 可以读取，返回Number
}
```

### 5.3 下界通配符 `<? super T>`

```java
// 向List中添加Integer
public static void addNumbers(List<? super Integer> list) {
    list.add(1);
    list.add(2);
    list.add(3);
}

addNumbers(new ArrayList<Integer>()); // ✅
addNumbers(new ArrayList<Number>());  // ✅
addNumbers(new ArrayList<Object>());  // ✅
// addNumbers(new ArrayList<Double>()); // 编译错误！
```

**关键限制**：`<? super T>`的List**只能写入，不能安全读取**（读出来是Object）：

```java
public static void readNumbers(List<? super Integer> list) {
    // Integer i = list.get(0); // 编译错误！
    Object o = list.get(0); // ✅ 只能读成Object
}
```

### 5.4 PECS原则

**PECS = Producer Extends, Consumer Super**

- 如果你需要从集合**读取**数据（生产者），使用`<? extends T>`
- 如果你需要向集合**写入**数据（消费者），使用`<? super T>`
- 如果既要读又要写，不要用通配符

```java
// 经典案例：copy方法
public static <T> void copy(List<? super T> dest, List<? extends T> src) {
    for (int i = 0; i < src.size(); i++) {
        dest.set(i, src.get(i));
    }
}

// JDK中Collections.copy的签名正是如此
// src是生产者（提供数据，用extends）
// dest是消费者（接收数据，用super）
```

### 5.5 通配符捕获

```java
public static void swap(List<?> list, int i, int j) {
    // list.set(i, list.get(j)); // 编译错误！

    // 通过通配符捕获辅助方法解决
    swapHelper(list, i, j);
}

private static <T> void swapHelper(List<T> list, int i, int j) {
    T temp = list.get(i);
    list.set(i, list.get(j));
    list.set(j, temp);
}
```

编译器能将`<?>`捕获为某个确定的类型`T`，这就是"通配符捕获"（Wildcard Capture）。

---

## 6. 泛型约束与限制

### 6.1 泛型类型的限制一览

| 限制 | 示例 | 原因 |
|------|------|------|
| 不能用基本类型 | `List<int>` ❌ | 类型擦除后是Object，无法存基本类型 |
| 不能实例化类型参数 | `new T()` ❌ | 擦除后不知道T是什么 |
| 不能实例化泛型数组 | `new T[10]` ❌ | 类型安全无法保证 |
| 不能用instanceof泛型 | `obj instanceof List<String>` ❌ | 运行时无泛型信息 |
| 不能用泛型类做静态字段 | `static T field` ❌ | T属于实例级别 |
| 不能catch泛型异常 | `catch(T e)` ❌ | 异常类型在编译时必须确定 |
| 不能定义泛型异常类 | `class MyEx<T> extends Exception` ❌ | 异常机制要求类型在编译时确定 |

### 6.2 类型参数的上界

```java
// 单上界
public class NumberBox<T extends Number> {
    private T value;
    public double doubleValue() {
        return value.doubleValue(); // 可以调用Number的方法
    }
}

// 多上界（交集类型）
public class MultiBound<T extends Number & Comparable<T>> {
    private T value;

    public boolean isGreaterThan(T other) {
        return value.compareTo(other) > 0; // 可以调用Comparable的方法
    }
}
```

### 6.3 绕过限制的技巧

```java
// 不能new T()？用Class对象 + 反射
public class Factory<T> {
    private final Class<T> type;

    public Factory(Class<T> type) {
        this.type = type;
    }

    public T newInstance() throws Exception {
        return type.getDeclaredConstructor().newInstance();
    }
}

// 不能new T[]？用Array.newInstance
@SuppressWarnings("unchecked")
public static <T> T[] createArray(Class<T> type, int size) {
    return (T[]) Array.newInstance(type, size);
}

// 不能new T[10]，但可以 new Object[10] 然后强转（不安全但合法）
@SuppressWarnings("unchecked")
public class GenericArray<T> {
    private final T[] array;

    @SuppressWarnings("unchecked")
    public GenericArray(int size) {
        // this.array = new T[size]; // 编译错误
        this.array = (T[]) new Object[size]; // 合法但类型不安全
    }

    public T get(int i) { return array[i]; }
    public void set(int i, T item) { array[i] = item; }
}
```

---

## 7. 类型令牌与Super Type Token

### 7.1 类型令牌（Type Token）

由于类型擦除，`List<String>.class`不存在。但通过传入`Class<T>`对象，可以在运行时保留类型信息：

```java
public class TypeTokenExample {

    // 用Class<T>传递类型信息
    public static <T> T parse(String json, Class<T> type) {
        // 模拟JSON解析
        // 实际中使用Jackson/Gson
        if (type == String.class) {
            return type.cast(json);
        } else if (type == Integer.class) {
            return type.cast(Integer.parseInt(json));
        }
        throw new IllegalArgumentException("Unsupported type: " + type);
    }

    public static void main(String[] args) {
        String str = parse("hello", String.class);
        Integer num = parse("42", Integer.class);
    }
}
```

### 7.2 Super Type Token（超类型令牌）

类型令牌的局限是无法表达泛型类型（如`List<String>.class`不存在）。超类型令牌通过匿名内部类来捕获泛型类型信息：

```java
// 超类型令牌基础类
public abstract class TypeReference<T> {
    private final Type type;

    protected TypeReference() {
        // 获取泛型父类的实际类型参数
        Type superClass = getClass().getGenericSuperclass();
        if (superClass instanceof ParameterizedType) {
            this.type = ((ParameterizedType) superClass).getActualTypeArguments()[0];
        } else {
            throw new RuntimeException("Missing type parameter");
        }
    }

    public Type getType() {
        return type;
    }
}

// 使用——通过匿名内部类
TypeReference<List<String>> typeRef = new TypeReference<List<String>>() {};

// typeRef.getType() 返回 List<String>
// Jackson/Gson的TypeReference就是这个原理
```

### 7.3 实际应用

```java
// 模拟Jackson的用法
public class JsonUtils {
    public static <T> T fromJson(String json, TypeReference<T> typeRef) {
        Type type = typeRef.getType();
        System.out.println("Deserializing to: " + type);
        // type 是 List<User>，包含了完整泛型信息
        // ... 实际反序列化逻辑
        return null;
    }
}

// 使用
List<User> users = JsonUtils.fromJson(jsonStr,
    new TypeReference<List<User>>() {});
```

---

## 8. 泛型与反射

### 8.1 反射获取泛型信息

虽然类型擦除在运行时擦除了泛型信息，但**类的元数据**（字段、方法签名、类继承关系）中仍然保留了泛型信息：

```java
public class GenericReflection {

    public static void inspectClass(Class<?> clazz) {
        // 获取父类的泛型
        Type superType = clazz.getGenericSuperclass();
        if (superType instanceof ParameterizedType) {
            ParameterizedType pt = (ParameterizedType) superType;
            Type[] args = pt.getActualTypeArguments();
            for (Type arg : args) {
                System.out.println("Type arg: " + arg.getTypeName());
            }
        }

        // 获取字段的泛型
        for (Field field : clazz.getDeclaredFields()) {
            Type genericType = field.getGenericType();
            System.out.println(field.getName() + " : " + genericType.getTypeName());
        }

        // 获取方法的泛型返回值
        for (Method method : clazz.getDeclaredMethods()) {
            Type returnType = method.getGenericReturnType();
            System.out.println(method.getName() + "() returns: " + returnType.getTypeName());
        }
    }
}
```

### 8.2 运行时获取泛型类型参数

```java
public abstract class GenericDAO<T> {
    private final Class<T> entityClass;

    @SuppressWarnings("unchecked")
    public GenericDAO() {
        // 通过反射获取实际类型参数
        Type superType = getClass().getGenericSuperclass();
        if (superType instanceof ParameterizedType) {
            ParameterizedType pt = (ParameterizedType) superType;
            this.entityClass = (Class<T>) pt.getActualTypeArguments()[0];
        } else {
            throw new IllegalStateException("Subclass must specify type parameter");
        }
    }

    public Class<T> getEntityClass() {
        return entityClass;
    }
}

// 子类
public class UserDAO extends GenericDAO<User> {}

// 使用
UserDAO dao = new UserDAO();
// dao.getEntityClass() 返回 User.class
// 这就是Spring Data JPA等框架的基础
```

### 8.3 ParameterizedType详解

```java
// ParameterizedType 接口
public interface ParameterizedType extends Type {
    Type getRawType();        // 原始类型，如 List.class
    Type[] getActualTypeArguments(); // 类型参数，如 [String.class]
    Type getOwnerType();      // 所属类型（嵌套泛型时使用）
}

// 示例：解析复杂泛型
// Map<String, List<Integer>> 的结构
// getRawType() → Map.class
// getActualTypeArguments() → [String.class, ParameterizedType(List<Integer>)]
```

---

## 9. 实战场景：泛型DAO模式

### 9.1 泛型DAO接口

```java
public interface GenericDAO<T, ID> {
    T findById(ID id);
    List<T> findAll();
    List<T> findByCondition(Map<String, Object> conditions);
    T save(T entity);
    T update(T entity);
    void delete(ID id);
    long count();
    boolean exists(ID id);
}
```

### 9.2 泛型DAO抽象实现

```java
public abstract class AbstractGenericDAO<T, ID> implements GenericDAO<T, ID> {

    protected final Class<T> entityClass;
    protected final Connection connection;

    @SuppressWarnings("unchecked")
    protected AbstractGenericDAO(Connection connection) {
        this.connection = connection;
        Type superType = getClass().getGenericSuperclass();
        this.entityClass = (Class<T>) ((ParameterizedType) superType)
            .getActualTypeArguments()[0];
    }

    @Override
    public T findById(ID id) {
        String sql = "SELECT * FROM " + getTableName() + " WHERE id = ?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setObject(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return mapRow(rs);
                }
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return null;
    }

    @Override
    public List<T> findAll() {
        String sql = "SELECT * FROM " + getTableName();
        List<T> results = new ArrayList<>();
        try (PreparedStatement ps = connection.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            while (rs.next()) {
                results.add(mapRow(rs));
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        return results;
    }

    @Override
    public T save(T entity) {
        String sql = buildInsertSql();
        try (PreparedStatement ps = connection.prepareStatement(sql,
                Statement.RETURN_GENERATED_KEYS)) {
            setInsertParameters(ps, entity);
            ps.executeUpdate();
            try (ResultSet keys = ps.getGeneratedKeys()) {
                if (keys.next()) {
                    setGeneratedId(entity, keys.getLong(1));
                }
            }
            return entity;
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }

    // 模板方法——由子类实现
    protected abstract String getTableName();
    protected abstract T mapRow(ResultSet rs) throws SQLException;
    protected abstract String buildInsertSql();
    protected abstract void setInsertParameters(PreparedStatement ps, T entity)
            throws SQLException;
    protected abstract void setGeneratedId(T entity, Long id);
}
```

### 9.3 具体DAO实现

```java
public class UserDAO extends AbstractGenericDAO<User, Long> {

    public UserDAO(Connection connection) {
        super(connection);
    }

    @Override
    protected String getTableName() {
        return "users";
    }

    @Override
    protected User mapRow(ResultSet rs) throws SQLException {
        User user = new User();
        user.setId(rs.getLong("id"));
        user.setUsername(rs.getString("username"));
        user.setEmail(rs.getString("email"));
        user.setCreatedAt(rs.getTimestamp("created_at").toLocalDateTime());
        return user;
    }

    @Override
    protected String buildInsertSql() {
        return "INSERT INTO users (username, email, created_at) VALUES (?, ?, ?)";
    }

    @Override
    protected void setInsertParameters(PreparedStatement ps, User user)
            throws SQLException {
        ps.setString(1, user.getUsername());
        ps.setString(2, user.getEmail());
        ps.setTimestamp(3, Timestamp.valueOf(user.getCreatedAt()));
    }

    @Override
    protected void setGeneratedId(User user, Long id) {
        user.setId(id);
    }

    // User特有的查询方法
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = ?";
        try (PreparedStatement ps = connection.prepareStatement(sql)) {
            ps.setString(1, username);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? mapRow(rs) : null;
            }
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
    }
}
```

---

## 10. 实战场景：泛型Builder模式

### 10.1 问题引入

Builder模式中，子类Builder的链式调用会返回父类Builder类型，导致类型丢失：

```java
// 有问题的Builder
public class Animal {
    private String name;
    public static class Builder {
        public Builder name(String name) { this.name = name; return this; }
        public Animal build() { return new Animal(this); }
    }
}

public class Dog extends Animal {
    private String breed;
    public static class Builder extends Animal.Builder {
        public Builder breed(String breed) { this.breed = breed; return this; }
        // 问题：name()返回Animal.Builder，不是Dog.Builder
        // new Dog.Builder().name("Rex").breed("Lab")  // 编译错误！
    }
}
```

### 10.2 递归泛型解决

```java
public abstract class Animal {
    protected String name;

    protected Animal() {}

    public static abstract class Builder<T extends Builder<T>> {
        protected String name;

        public T name(String name) {
            this.name = name;
            return self();
        }

        // 子类必须实现self()，返回自身类型
        protected abstract T self();

        public abstract Animal build();
    }
}

public class Dog extends Animal {
    private String breed;

    private Dog() {}

    public static class Builder extends Animal.Builder<Builder> {
        private String breed;

        @Override
        protected Builder self() {
            return this;
        }

        public Builder breed(String breed) {
            this.breed = breed;
            return this;
        }

        @Override
        public Dog build() {
            Dog dog = new Dog();
            dog.name = this.name;
            dog.breed = this.breed;
            return dog;
        }
    }
}
```

### 10.3 使用效果

```java
// 现在链式调用完美工作
Dog dog = new Dog.Builder()
    .name("Rex")      // 返回Dog.Builder
    .breed("Labrador") // 返回Dog.Builder
    .build();

// 也可以反过来
Dog dog2 = new Dog.Builder()
    .breed("Poodle")   // 返回Dog.Builder
    .name("Buddy")     // 返回Dog.Builder
    .build();
```

### 10.4 Lombok的@Builder与泛型

```java
// Lombok的@Builder注解会自动生成Builder
@Builder
public class Cat extends Animal {
    private boolean indoor;
    // Lombok生成的Builder也需要处理递归泛型问题
    // 实际项目中可考虑手写Builder或使用@SuperBuilder
}

// @SuperBuilder（Lombok 1.18+）
@SuperBuilder
public class Cat extends Animal {
    private boolean indoor;
}

@SuperBuilder
public class Animal {
    private String name;
}

// 使用
Cat cat = Cat.builder().name("Whiskers").indoor(true).build();
```

---

## 11. 面试题速查

### Q1: Java泛型与C++模板有什么区别？

**Java泛型**是编译时类型擦除（伪泛型），运行时无类型信息；**C++模板**在编译时为每种类型生成独立代码（真泛型）。Java泛型不支持基本类型，C++模板支持。Java泛型不能在静态上下文中使用类型参数的实例，C++可以。

### Q2: 什么是类型擦除？有哪些副作用？

类型擦除是编译器将泛型类型参数替换为其上界（默认Object）的过程。副作用包括：不能使用基本类型、不能new T()、不能new T[]、不能用instanceof泛型类型、运行时获取不到泛型参数类型、方法签名冲突等。

### Q3: `List<?>`、`List<Object>`、`List`有什么区别？

- `List`：原始类型，不推荐使用，没有类型安全检查
- `List<Object>`：只能装Object，不能接收`List<String>`
- `List<?>`：可以接收任意类型的List，但只能读不能写（除null外）

### Q4: PECS原则是什么？

Producer Extends, Consumer Super。从集合读取数据用`<? extends T>`，向集合写入数据用`<? super T>`。JDK的`Collections.copy(List<? super T> dest, List<? extends T> src)`就是典型案例。

### Q5: 如何在运行时获取泛型类型信息？

通过反射的`getGenericSuperclass()`和`ParameterizedType`接口获取类的泛型参数信息。超类型令牌（Super Type Token）利用匿名内部类来捕获完整的泛型类型信息，如`new TypeReference<List<String>>(){}`。

### Q6: 什么是桥接方法？

当子类具体化泛型类型参数时，编译器自动生成的方法，用于保证多态正确性。例如子类override`setValue(String)`，但父类擦除后是`setValue(Object)`，编译器生成`setValue(Object)`桥接方法来调用`setValue(String)`。

### Q7: 为什么`List<int>`不行但`List<Integer>`可以？

因为类型擦除后类型参数变为Object，而Java的基本类型不是Object的子类型。Integer是Object的子类所以可以。这也是Java泛型与C#泛型的重要区别之一。

### Q8: 泛型DAO模式如何获取实体类类型？

在抽象DAO构造器中通过`getClass().getGenericSuperclass()`获取ParameterizedType，然后`getActualTypeArguments()[0]`获取第一个类型参数的Class。这要求子类必须具体化类型参数（不能再次泛化）。

### Q9: 递归泛型`<T extends Builder<T>>`解决了什么问题？

解决了Builder模式中子类Builder链式调用返回父类类型的问题。通过递归泛型约束，`self()`方法返回子类Builder类型，保证了链式调用的类型安全。

### Q10: 什么是堆污染（Heap Pollution）？

当泛型类型与原始类型混用时，可能导致类型不匹配的对象进入泛型集合。例如将`List<String>`赋值给`List`，再往里加Integer，运行时取出时才会抛出ClassCastException。`@SafeVarargs`注解用于声明不会导致堆污染。

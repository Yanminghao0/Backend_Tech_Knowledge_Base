# Java Stream 流式编程详解

> Stream 是 Java 8 引入的函数式数据处理 API，它以声明式的方式对集合、数组等数据源进行过滤、映射、归约等操作。Stream 不是数据结构，而是对数据源的一系列流水线操作，支持串行和并行执行。掌握 Stream 是写出简洁、高效 Java 代码的关键技能。

---

## 📋 目录

1. [Stream 概述与核心概念](#1-stream-概述与核心概念)
2. [Stream 的创建方式](#2-stream-的创建方式)
3. [中间操作详解](#3-中间操作详解)
4. [终端操作详解](#4-终端操作详解)
5. [Collectors 收集器全览](#5-collectors-收集器全览)
6. [并行流与并发编程](#6-并行流与并发编程)
7. [实战场景与代码示例](#7-实战场景与代码示例)
8. [性能注意事项与最佳实践](#8-性能注意事项与最佳实践)
9. [面试题速查](#9-面试题速查)

---

## 1. Stream 概述与核心概念

### 1.1 什么是 Stream

Stream 是 Java 8 中 `java.util.stream` 包引入的一组 API，用于对数据源进行批量处理。它的核心特点包括：

- **声明式编程**：描述"做什么"而非"怎么做"，代码更简洁
- **链式操作**：支持流水线（Pipeline）风格的链式调用
- **惰性求值**：中间操作不会立即执行，只有终端操作触发时才真正计算
- **不修改数据源**：Stream 操作不会改变原始数据源，每次都产生新的 Stream
- **可消费一次**：一个 Stream 实例只能被终端操作消费一次

### 1.2 操作分类

Stream 操作分为两大类：

| 类别 | 说明 | 是否触发执行 | 示例 |
|------|------|-------------|------|
| 中间操作（Intermediate） | 返回新的 Stream，可继续链式调用 | 否（惰性） | `filter`、`map`、`sorted` |
| 终端操作（Terminal） | 返回结果或产生副作用，关闭 Stream | 是 | `collect`、`forEach`、`count` |

### 1.3 三步流水线模型

```java
// 数据源 → 中间操作链 → 终端操作
List<String> result = list.stream()          // 1. 创建 Stream
    .filter(s -> s.startsWith("A"))           // 2. 中间操作：过滤
    .map(String::toUpperCase)                 // 3. 中间操作：映射
    .collect(Collectors.toList());            // 4. 终端操作：收集
```

### 1.4 Stream 与 Collection 的区别

| 维度 | Collection | Stream |
|------|-----------|--------|
| 本质 | 数据存储结构 | 数据计算视图 |
| 操作 | 外部迭代（for-each） | 内部迭代（自动） |
| 消费 | 可多次遍历 | 只能消费一次 |
| 惰性 | 即时执行 | 中间操作惰性求值 |
| 并行 | 需手动管理 | 内置 `parallelStream` |

---

## 2. Stream 的创建方式

### 2.1 通过集合创建

集合是 Stream 最常见的数据源，`Collection` 接口提供了 `stream()` 和 `parallelStream()` 方法。

```java
// 串行流
List<String> list = Arrays.asList("Java", "Python", "Go");
Stream<String> stream = list.stream();

// 并行流
Stream<String> parallelStream = list.parallelStream();
```

### 2.2 通过数组创建

`Arrays.stream()` 方法可以将数组转换为 Stream。

```java
// 基本类型数组 → IntStream
int[] intArray = {1, 2, 3, 4, 5};
IntStream intStream = Arrays.stream(intArray);

// 对象数组 → Stream<T>
String[] strArray = {"a", "b", "c"};
Stream<String> strStream = Arrays.stream(strArray);

// 指定范围 [1, 4)
IntStream rangeStream = Arrays.stream(intArray, 1, 4);
```

### 2.3 通过值创建

`Stream.of()` 方法可以直接用一组值创建 Stream。

```java
// 创建包含多个元素的 Stream
Stream<String> stream = Stream.of("Java", "Kotlin", "Scala");

// 创建空 Stream
Stream<String> emptyStream = Stream.empty();

// 创建单个元素的 Stream
Stream<String> singleStream = Stream.of("Hello");
```

### 2.4 通过文件创建

`Files.lines()` 可以将文件每一行作为 Stream 元素，实现惰性读取。

```java
// 读取文件每行，惰性加载，自动关闭资源
try (Stream<String> lines = Files.lines(Paths.get("data.txt"), StandardCharsets.UTF_8)) {
    lines.filter(line -> line.contains("ERROR"))
         .forEach(System.out::println);
} catch (IOException e) {
    e.printStackTrace();
}

// Files.walk() 递归遍历目录
try (Stream<Path> paths = Files.walk(Paths.get("/project"))) {
    paths.filter(Files::isRegularFile)
         .filter(p -> p.toString().endsWith(".java"))
         .forEach(System.out::println);
} catch (IOException e) {
    e.printStackTrace();
}
```

### 2.5 通过函数创建（无限流）

`Stream.iterate()` 和 `Stream.generate()` 可以创建无限流，必须配合 `limit()` 截断。

```java
// iterate：种子 + 函数（类似 reduce）
// 生成 0, 1, 2, 3, 4
Stream<Integer> iterateStream = Stream.iterate(0, n -> n + 1).limit(5);

// Java 9 增强：增加终止条件（hasNext 谓词）
// 生成 0, 1, 2, 3, 4（n < 5 时继续）
Stream<Integer> iterateStream2 = Stream.iterate(0, n -> n < 5, n -> n + 1);

// generate：供应器 Supplier
// 生成 5 个随机数
Stream<Double> randomStream = Stream.generate(Math::random).limit(5);

// 生成自定义对象
Stream<UUID> uuidStream = Stream.generate(UUID::randomUUID).limit(3);
```

### 2.6 基本类型流

Java 提供了三种基本类型 Stream，避免装箱拆箱开销。

```java
// IntStream：int 元素
IntStream intStream = IntStream.range(1, 10);         // [1, 10)
IntStream intStream2 = IntStream.rangeClosed(1, 10);  // [1, 10]
IntStream intStream3 = IntStream.of(1, 2, 3, 4, 5);

// LongStream：long 元素
LongStream longStream = LongStream.range(1, 100);

// DoubleStream：double 元素
DoubleStream doubleStream = DoubleStream.of(1.0, 2.0, 3.0);

// 基本类型流与对象流互转
Stream<Integer> boxed = intStream.boxed();  // IntStream → Stream<Integer>
IntStream unboxed = Stream.of(1, 2, 3).mapToInt(Integer::intValue);  // Stream → IntStream
```

---

## 3. 中间操作详解

中间操作是惰性的，只有终端操作触发时才执行。多个中间操作会形成一个操作链，在终端操作时一次性执行，这允许某些操作短路。

### 3.1 filter —— 过滤

```java
// 筛选偶数
List<Integer> evens = Stream.of(1, 2, 3, 4, 5, 6)
    .filter(n -> n % 2 == 0)
    .collect(Collectors.toList());
// 结果: [2, 4, 6]

// 过滤非空字符串
List<String> nonNull = Stream.of("a", null, "b", "", "c")
    .filter(Objects::nonNull)
    .filter(s -> !s.isEmpty())
    .collect(Collectors.toList());
// 结果: ["a", "b", "c"]
```

### 3.2 map —— 映射

`map` 对每个元素应用函数，生成一对一的映射。

```java
// 提取对象属性
List<Person> persons = getPersons();
List<String> names = persons.stream()
    .map(Person::getName)
    .collect(Collectors.toList());

// 类型转换
List<String> upperNames = Stream.of("alice", "bob", "charlie")
    .map(String::toUpperCase)
    .collect(Collectors.toList());
// 结果: ["ALICE", "BOB", "CHARLIE"]

// 基本类型映射
int[] lengths = Stream.of("Java", "Go", "Rust")
    .mapToInt(String::length)
    .toArray();
// 结果: [4, 2, 4]
```

### 3.3 flatMap —— 扁平化映射

`flatMap` 将流中每个元素映射为另一个流，然后将所有流"扁平化"合并为一个流（一对多→一）。

```java
// 将嵌套 List 拍平
List<List<Integer>> nested = Arrays.asList(
    Arrays.asList(1, 2, 3),
    Arrays.asList(4, 5),
    Arrays.asList(6, 7, 8, 9)
);
List<Integer> flat = nested.stream()
    .flatMap(Collection::stream)
    .collect(Collectors.toList());
// 结果: [1, 2, 3, 4, 5, 6, 7, 8, 9]

// 分割字符串并去重
List<String> words = Stream.of("hello world", "world java")
    .flatMap(line -> Arrays.stream(line.split(" ")))
    .distinct()
    .collect(Collectors.toList());
// 结果: ["hello", "world", "java"]

// 基本类型 flatMap
int[] merged = Stream.of(new int[]{1, 2}, new int[]{3, 4})
    .flatMapToInt(Arrays::stream)
    .toArray();
// 结果: [1, 2, 3, 4]
```

### 3.4 sorted —— 排序

```java
// 自然排序
List<Integer> sorted = Stream.of(3, 1, 4, 1, 5, 9, 2, 6)
    .sorted()
    .collect(Collectors.toList());

// 逆序
List<Integer> desc = Stream.of(3, 1, 4, 1, 5)
    .sorted(Comparator.reverseOrder())
    .collect(Collectors.toList());

// 自定义排序：按年龄升序，年龄相同按姓名
List<Person> sortedPersons = persons.stream()
    .sorted(Comparator.comparing(Person::getAge)
        .thenComparing(Person::getName))
    .collect(Collectors.toList());

// 自定义排序：按年龄降序
List<Person> descAge = persons.stream()
    .sorted(Comparator.comparing(Person::getAge).reversed())
    .collect(Collectors.toList());
```

### 3.5 peek —— 查看元素

`peek` 主要用于调试，对每个元素执行操作但不改变流。由于中间操作是惰性的，`peek` 只有在终端操作触发时才执行。

```java
// 调试流处理过程
List<String> result = Stream.of("a", "b", "c", "d")
    .peek(s -> System.out.println("before map: " + s))
    .map(String::toUpperCase)
    .peek(s -> System.out.println("after map: " + s))
    .filter(s -> s.equals("B"))
    .collect(Collectors.toList());
// 输出: before map: a / after map: A / before map: b / after map: B ...

// ⚠️ 注意：不要用 peek 修改状态，它不应该有副作用
// 错误用法（反模式）：
// stream.peek(item -> list.add(item))  // 不要这样做！
```

### 3.6 distinct —— 去重

```java
// 基本类型去重
List<Integer> unique = Stream.of(1, 2, 2, 3, 3, 3, 4)
    .distinct()
    .collect(Collectors.toList());
// 结果: [1, 2, 3, 4]

// 对象去重（需重写 equals/hashCode）
List<Person> distinctPersons = persons.stream()
    .distinct()
    .collect(Collectors.toList());

// 按属性去重（Java 8 经典技巧：使用 TreeSet）
List<Person> uniqueByName = persons.stream()
    .collect(Collectors.collectingAndThen(
        Collectors.toCollection(() -> new TreeSet<>(Comparator.comparing(Person::getName))),
        ArrayList::new
    ));
```

### 3.7 limit 与 skip —— 截断与跳过

```java
// limit：取前 N 个
List<Integer> first3 = Stream.of(1, 2, 3, 4, 5).limit(3).collect(Collectors.toList());
// 结果: [1, 2, 3]

// skip：跳过前 N 个
List<Integer> afterSkip = Stream.of(1, 2, 3, 4, 5).skip(2).collect(Collectors.toList());
// 结果: [3, 4, 5]

// 分页：第 3 页，每页 10 条（skip=20, limit=10）
List<Person> page3 = persons.stream()
    .skip(20)
    .limit(10)
    .collect(Collectors.toList());

// takeWhile（Java 9+）：取满足条件的前缀
List<Integer> taken = Stream.of(1, 2, 3, 4, 1, 2)
    .takeWhile(n -> n < 4)
    .collect(Collectors.toList());
// 结果: [1, 2, 3]

// dropWhile（Java 9+）：丢弃满足条件的前缀
List<Integer> dropped = Stream.of(1, 2, 3, 4, 1, 2)
    .dropWhile(n -> n < 4)
    .collect(Collectors.toList());
// 结果: [4, 1, 2]
```

---

## 4. 终端操作详解

终端操作会触发流水线的实际执行，产生一个结果或副作用。一个 Stream 只能有一个终端操作。

### 4.1 forEach —— 遍历

```java
// 遍历打印
Stream.of("Java", "Python", "Go").forEach(System.out::println);

// 有序遍历（即使并行流也保证顺序）
Stream.of("a", "b", "c").forEachOrdered(System.out::println);
```

### 4.2 collect —— 收集

`collect` 是最强大的终端操作，配合 `Collectors` 可以将流收集为各种容器。

```java
// 收集为 List
List<String> list = stream.collect(Collectors.toList());

// 收集为 Set
Set<String> set = stream.collect(Collectors.toSet());

// 收集为指定类型集合
LinkedList<String> linkedList = stream.collect(Collectors.toCollection(LinkedList::new));

// 收集为 Map
Map<String, Integer> map = persons.stream()
    .collect(Collectors.toMap(Person::getName, Person::getAge));
```

### 4.3 reduce —— 归约

`reduce` 将流中元素反复结合，得到一个值。

```java
// 求和
int sum = Stream.of(1, 2, 3, 4, 5)
    .reduce(0, Integer::sum);
// 结果: 15

// 无初始值（返回 Optional）
Optional<Integer> sumOpt = Stream.of(1, 2, 3).reduce(Integer::sum);

// 求最大值
Optional<Integer> max = Stream.of(3, 1, 4, 1, 5).reduce(Integer::max);

// 字符串拼接
String concatenated = Stream.of("H", "e", "l", "l", "o")
    .reduce("", (s1, s2) -> s1 + s2);
// 结果: "Hello"

// 复杂归约：计算总金额
// identity, accumulator, combiner（并行流必须提供 combiner）
int totalAmount = orders.stream()
    .reduce(0,
        (sum2, order) -> sum2 + order.getAmount(),
        Integer::sum);
```

### 4.4 count / min / max —— 聚合

```java
// 计数
long count = Stream.of("a", "b", "c").count();
// 结果: 3

// 最小值
Optional<Integer> min = Stream.of(3, 1, 4, 1, 5).min(Integer::compareTo);
// 结果: Optional[1]

// 最大值
Optional<Integer> max = Stream.of(3, 1, 4, 1, 5).max(Integer::compareTo);
// 结果: Optional[5]

// 基本类型流内置聚合
IntSummaryStatistics stats = IntStream.of(1, 2, 3, 4, 5).summaryStatistics();
// stats.getCount()=5, stats.getSum()=15, stats.getAverage()=3.0
// stats.getMin()=1, stats.getMax()=5
```

### 4.5 匹配与查找

```java
// anyMatch：任一匹配
boolean hasEven = Stream.of(1, 3, 5, 6).anyMatch(n -> n % 2 == 0);
// 结果: true

// allMatch：全部匹配
boolean allPositive = Stream.of(1, 2, 3).allMatch(n -> n > 0);
// 结果: true

// noneMatch：全不匹配
boolean noNegative = Stream.of(1, 2, 3).noneMatch(n -> n < 0);
// 结果: true

// findFirst：找到第一个元素
Optional<Integer> first = Stream.of(1, 2, 3).filter(n -> n > 1).findFirst();
// 结果: Optional[2]

// findAny：找到任意元素（并行流中性能更好）
Optional<Integer> any = Stream.of(1, 2, 3).filter(n -> n > 1).findAny();
```

### 4.6 聚合收集器 reduce vs collect

```java
// 用 collect 做字符串拼接（比 reduce + 字符串拼接更高效）
String result = Stream.of("a", "b", "c", "d")
    .collect(Collectors.joining(", ", "[", "]"));
// 结果: "[a, b, c, d]"
```

---

## 5. Collectors 收集器全览

`Collectors` 工具类提供了丰富的预定义收集器，是 `collect` 操作的核心。

### 5.1 toList / toSet / toCollection

```java
List<String> list = stream.collect(Collectors.toList());
Set<String> set = stream.collect(Collectors.toSet());
TreeSet<String> treeSet = stream.collect(Collectors.toCollection(TreeSet::new));
```

### 5.2 toMap —— 收集为 Map

```java
// 基本用法
Map<Long, String> idToName = persons.stream()
    .collect(Collectors.toMap(Person::getId, Person::getName));

// 处理键冲突（默认会抛异常，需指定合并函数）
Map<String, Integer> nameToAge = persons.stream()
    .collect(Collectors.toMap(
        Person::getName,
        Person::getAge,
        (existing, replacement) -> existing  // 保留已存在的值
    ));

// 指定 Map 实现
LinkedHashMap<String, Integer> linkedMap = persons.stream()
    .collect(Collectors.toMap(
        Person::getName,
        Person::getAge,
        (old, now) -> old,
        LinkedHashMap::new
    ));
```

### 5.3 groupingBy —— 分组

`groupingBy` 按分类函数对元素分组，等价于 SQL 的 `GROUP BY`。

```java
// 按单个字段分组
Map<String, List<Person>> byCity = persons.stream()
    .collect(Collectors.groupingBy(Person::getCity));

// 多级分组：先按城市，再按性别
Map<String, Map<String, List<Person>>> byCityAndGender = persons.stream()
    .collect(Collectors.groupingBy(
        Person::getCity,
        Collectors.groupingBy(Person::getGender)
    ));

// 分组并计数
Map<String, Long> countByCity = persons.stream()
    .collect(Collectors.groupingBy(Person::getCity, Collectors.counting()));

// 分组并求和
Map<String, Integer> totalAgeByCity = persons.stream()
    .collect(Collectors.groupingBy(
        Person::getCity,
        Collectors.summingInt(Person::getAge)
    ));

// 分组并取每组最大值
Map<String, Optional<Person>> oldestByCity = persons.stream()
    .collect(Collectors.groupingBy(
        Person::getCity,
        Collectors.maxBy(Comparator.comparing(Person::getAge))
    ));

// 分组并映射属性
Map<String, Set<String>> namesByCity = persons.stream()
    .collect(Collectors.groupingBy(
        Person::getCity,
        Collectors.mapping(Person::getName, Collectors.toSet())
    ));

// 分组并求平均值
Map<String, Double> avgAgeByCity = persons.stream()
    .collect(Collectors.groupingBy(
        Person::getCity,
        Collectors.averagingInt(Person::getAge)
    ));
```

### 5.4 partitioningBy —— 分区

`partitioningBy` 是 `groupingBy` 的特例，按布尔条件分为两组（true/false）。

```java
// 按是否成年分区
Map<Boolean, List<Person>> partition = persons.stream()
    .collect(Collectors.partitioningBy(p -> p.getAge() >= 18));

// 分区并计数
Map<Boolean, Long> partitionCount = persons.stream()
    .collect(Collectors.partitioningBy(
        p -> p.getAge() >= 18,
        Collectors.counting()
    ));

// 分区并收集属性
Map<Boolean, List<String>> partitionNames = persons.stream()
    .collect(Collectors.partitioningBy(
        p -> p.getAge() >= 18,
        Collectors.mapping(Person::getName, Collectors.toList())
    ));
```

### 5.5 joining —— 字符串拼接

```java
// 简单拼接
String s1 = Stream.of("a", "b", "c").collect(Collectors.joining());
// 结果: "abc"

// 带分隔符
String s2 = Stream.of("a", "b", "c").collect(Collectors.joining(", "));
// 结果: "a, b, c"

// 带分隔符、前缀、后缀
String s3 = Stream.of("a", "b", "c").collect(Collectors.joining(", ", "[", "]"));
// 结果: "[a, b, c]"
```

### 5.6 counting / summing / averaging —— 统计

```java
// 计数
Long count = stream.collect(Collectors.counting());

// 求和
IntSummingStatistics stats = persons.stream()
    .collect(Collectors.summarizingInt(Person::getAge));
// stats.getCount(), getSum(), getMin(), getMax(), getAverage()

// 求平均值
Double avg = persons.stream().collect(Collectors.averagingInt(Person::getAge));
```

### 5.7 collectingAndThen —— 收集后转换

```java
// 收集后包装为不可变列表
List<String> unmodifiable = stream.collect(
    Collectors.collectingAndThen(
        Collectors.toList(),
        Collections::unmodifiableList
    )
);

// 收集后取最大值并提取
Person oldest = persons.stream()
    .collect(Collectors.collectingAndThen(
        Collectors.maxBy(Comparator.comparing(Person::getAge)),
        opt -> opt.orElse(null)
    ));
```

### 5.8 reducing —— 归约收集器

```java
// 按城市分组，求每人年龄的最大值
Map<String, Integer> maxAgeByCity = persons.stream()
    .collect(Collectors.groupingBy(
        Person::getCity,
        Collectors.reducing(0, Person::getAge, Integer::max)
    ));
```

---

## 6. 并行流与并发编程

### 6.1 并行流基本用法

```java
// 方式一：直接创建并行流
List<Integer> list = Arrays.asList(1, 2, 3, 4, 5);
list.parallelStream().forEach(System.out::println);

// 方式二：串行流转并行流
list.stream().parallel().forEach(System.out::println);

// 转回串行流
list.parallelStream().sequential().forEach(System.out::println);
```

### 6.2 底层线程池

并行流默认使用 `ForkJoinPool.commonPool()`，默认线程数为 `CPU核心数 - 1`。

```java
// 查看默认并行度
System.out.println(ForkJoinPool.commonPool().getParallelism());
// 输出: CPU核心数 - 1

// 自定义并行度
System.setProperty("java.util.concurrent.ForkJoinPool.common.parallelism", "8");

// 使用自定义线程池（避免阻塞公共池）
ForkJoinPool customPool = new ForkJoinPool(4);
customPool.submit(() ->
    list.parallelStream()
        .map(this::expensiveOperation)
        .collect(Collectors.toList())
).get();
customPool.shutdown();
```

### 6.3 顺序性保证

```java
// forEach 在并行流中不保证顺序
list.parallelStream().forEach(System.out::println);  // 顺序不确定

// forEachOrdered 保证顺序（但牺牲并行优势）
list.parallelStream().forEachOrdered(System.out::println);

// limit/skip 在并行流中可能性能较差（需要缓冲全部元素）
list.parallelStream().limit(3).collect(Collectors.toList());
```

### 6.4 线程安全注意事项

```java
// ❌ 错误：使用非线程安全容器
ArrayList<Integer> unsafeList = new ArrayList<>();
list.parallelStream().forEach(unsafeList::add);  // 可能丢失数据

// ✅ 正确：使用线程安全容器
List<Integer> safeList = Collections.synchronizedList(new ArrayList<>());
list.parallelStream().forEach(safeList::add);

// ✅ 最佳：使用 collect（线程安全）
List<Integer> collected = list.parallelStream()
    .map(n -> n * 2)
    .collect(Collectors.toList());

// ✅ 使用 ConcurrentHashMap 等线程安全操作
Map<Integer, Integer> map = new ConcurrentHashMap<>();
list.parallelStream().forEach(n -> map.put(n, n * n));
```

### 6.5 并行流适用场景

| 适合并行 | 不适合并行 |
|---------|-----------|
| 数据量大（>10000） | 数据量小 |
| 计算密集型任务 | IO 密集型任务 |
| 元素间无依赖关系 | 元素间有顺序依赖 |
| 操作无副作用 | 操作有共享可变状态 |
| 源易于拆分（ArrayList/数组） | 源难以拆分（LinkedList） |

```java
// 并行流性能对比示例
// 串行：约 1000ms
long serialTime = measure(() ->
    IntStream.range(0, 10_000_000)
        .map(n -> n * n)
        .sum()
);

// 并行：约 300ms（数据量大时并行优势明显）
long parallelTime = measure(() ->
    IntStream.range(0, 10_000_000)
        .parallel()
        .map(n -> n * n)
        .sum()
);
```

---

## 7. 实战场景与代码示例

### 7.1 数据转换：对象 DTO 转换

```java
// Entity → DTO 转换
List<UserDTO> dtos = users.stream()
    .map(user -> UserDTO.builder()
        .id(user.getId())
        .displayName(user.getFirstName() + " " + user.getLastName())
        .email(user.getEmail().toLowerCase())
        .role(user.getRole().name())
        .build())
    .collect(Collectors.toList());

// 分页查询结果转换
Page<UserDTO> pageResult = userPage.map(user -> UserDTO.builder()
    .id(user.getId())
    .displayName(user.getName())
    .build());
```

### 7.2 分组统计：报表生成

```java
// 按部门和职位分组，统计每组平均薪资
Map<String, Map<String, Double>> salaryReport = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::getDepartment,
        Collectors.groupingBy(
            Employee::getPosition,
            Collectors.averagingDouble(Employee::getSalary)
        )
    ));

// 按月份分组统计订单数量和总金额
Map<YearMonth, OrderStats> monthlyStats = orders.stream()
    .collect(Collectors.groupingBy(
        order -> YearMonth.from(order.getCreatedAt()),
        Collectors.collectingAndThen(
            Collectors.summarizingDouble(Order::getAmount),
            stats -> new OrderStats(stats.getCount(), stats.getSum())
        )
    ));

// 找出每个部门薪资最高的员工
Map<String, Employee> topEarnerByDept = employees.stream()
    .collect(Collectors.toMap(
        Employee::getDepartment,
        Function.identity(),
        BinaryOperator.maxBy(Comparator.comparing(Employee::getSalary))
    ));
```

### 7.3 批处理：大数据量分批

```java
// 将大列表按固定大小分批
int batchSize = 100;
List<List<Order>> batches = IntStream.range(0, (orders.size() + batchSize - 1) / batchSize)
    .mapToObj(i -> orders.subList(
        i * batchSize,
        Math.min((i + 1) * batchSize, orders.size())
    ))
    .collect(Collectors.toList());

// 批量插入数据库
batches.forEach(batch -> {
    orderMapper.batchInsert(batch);
});

// 使用 Stream 批量处理
List<List<Integer>> chunks = IntStream.range(0, 1000)
    .boxed()
    .collect(Collectors.groupingBy(i -> i / 100))
    .values()
    .stream()
    .sorted(Comparator.comparingInt(List::get))
    .collect(Collectors.toList());
```

### 7.4 多数据源合并与去重

```java
// 合并多个数据源并去重
List<Product> merged = Stream.concat(
        Stream.concat(
            localProducts.stream(),
            remoteProducts.stream()
        ),
        cachedProducts.stream()
    )
    .distinct()
    .sorted(Comparator.comparing(Product::getPriority).reversed())
    .limit(100)
    .collect(Collectors.toList());
```

### 7.5 复杂业务逻辑：Top-N 推荐

```java
// 为每个用户推荐 Top-3 商品
Map<Long, List<Product>> recommendations = userHistory.stream()
    .collect(Collectors.groupingBy(
        UserHistory::getUserId,
        Collectors.collectingAndThen(
            Collectors.toList(),
            history -> history.stream()
                .map(h -> findSimilarProducts(h.getProductId()))
                .flatMap(List::stream)
                .distinct()
                .sorted(Comparator.comparing(Product::getScore).reversed())
                .limit(3)
                .collect(Collectors.toList())
        )
    ));
```

---

## 8. 性能注意事项与最佳实践

### 8.1 惰性求值的性能影响

```java
// 中间操作不执行，直到终端操作触发
Stream<Integer> stream = Stream.of(1, 2, 3)
    .filter(n -> { System.out.println("filter: " + n); return n > 1; });
// 此时无输出

stream.count();
// 输出: filter: 1, filter: 2, filter: 3

// 短路操作：找到第一个匹配后立即停止
Optional<Integer> first = Stream.of(1, 2, 3, 4, 5)
    .peek(n -> System.out.println("processing: " + n))
    .filter(n -> n > 3)
    .findFirst();
// 输出: processing: 1, 2, 3, 4（不会处理 5）
```

### 8.2 避免装箱拆箱

```java
// ❌ 装箱开销大
int sum = Stream.of(1, 2, 3, 4, 5)
    .mapToInt(Integer::intValue)
    .sum();

// ✅ 直接使用基本类型流
int sum2 = IntStream.of(1, 2, 3, 4, 5).sum();

// ✅ 使用 mapToInt 避免 Stream<Integer>
int totalAge = persons.stream()
    .mapToInt(Person::getAge)
    .sum();
```

### 8.3 流的复用问题

```java
// ❌ 流不能复用
Stream<String> stream = Stream.of("a", "b", "c");
stream.forEach(System.out::println);
stream.forEach(System.out::println);  // IllegalStateException: stream has already been operated upon

// ✅ 使用 Supplier 创建可复用的流
Supplier<Stream<String>> streamSupplier = () -> Stream.of("a", "b", "c");
streamSupplier.get().forEach(System.out::println);
streamSupplier.get().filter(s -> s.equals("b")).forEach(System.out::println);
```

### 8.4 并行流性能陷阱

```java
// ❌ 数据源不易拆分：LinkedList 对并行不友好
LinkedList<Integer> linkedList = new LinkedList<>(IntStream.range(0, 1000000).boxed().collect(Collectors.toList()));
long sum1 = linkedList.parallelStream().mapToInt(Integer::intValue).sum();  // 可能比串行还慢

// ✅ 使用 ArrayList 或数组
List<Integer> arrayList = new ArrayList<>(linkedList);
long sum2 = arrayList.parallelStream().mapToInt(Integer::intValue).sum();  // 并行优势明显

// ❌ 并行流中使用 limit/skip 性能差
list.parallelStream().limit(10).collect(Collectors.toList());

// ❌ 并行流中使用有状态操作（sorted/distinct）性能差
list.parallelStream().sorted().collect(Collectors.toList());

// ⚠️ 避免在并行流中使用 IO 操作
files.parallelStream().forEach(this::readFile);  // 阻塞公共线程池
```

### 8.5 常见反模式

```java
// ❌ 反模式1：用 forEach 修改外部状态
List<String> results = new ArrayList<>();
stream.forEach(results::add);  // 并行流下不安全

// ✅ 正确做法
List<String> results = stream.collect(Collectors.toList());

// ❌ 反模式2：用 peek 产生副作用
stream.peek(s -> saveToDB(s)).collect(Collectors.toList());

// ✅ 正确做法
stream.forEach(this::saveToDB);

// ❌ 反模式3：嵌套 Stream（降低可读性）
list1.stream()
    .map(e1 -> list2.stream()
        .filter(e2 -> e2.getId().equals(e1.getId()))
        .findFirst()
        .orElse(null))
    .collect(Collectors.toList());

// ✅ 改用 Map 查找
Map<Long, E2> map2 = list2.stream().collect(Collectors.toMap(E2::getId, Function.identity()));
list1.stream()
    .map(e1 -> map2.get(e1.getId()))
    .collect(Collectors.toList());
```

---

## 9. 面试题速查

### Q1: Stream 和 Collection 有什么区别？

Stream 是数据计算视图，Collection 是数据存储结构。Stream 支持内部迭代、惰性求值、一次性消费，而 Collection 需要外部迭代、可多次遍历。Stream 操作不修改数据源，每次产生新的 Stream。

### Q2: 中间操作和终端操作的区别？

中间操作返回 Stream，是惰性的，不会立即执行；终端操作返回结果或产生副作用，触发整个流水线的执行。中间操作可以链式调用多个，但终端操作只能有一个。

### Q3: map 和 flatMap 的区别？

`map` 是一对一映射，每个元素转换为另一个元素；`flatMap` 是一对多映射，将每个元素展开为流后合并为一个流。例如 `map(line -> Arrays.asList(line.split(" ")))` 返回 `Stream<List<String>>`，而 `flatMap(line -> Arrays.stream(line.split(" ")))` 返回 `Stream<String>`。

### Q4: Stream 的惰性求值有什么好处？

惰性求值允许 Stream 进行优化：1) 多个操作可以融合为单次遍历；2) 短路操作（如 findFirst、anyMatch）找到结果后立即停止；3) 无限流可以配合 limit 使用。所有中间操作在终端操作触发前都不会执行。

### Q5: 并行流的实现原理是什么？

并行流底层使用 `ForkJoinPool.commonPool()`，采用分治策略将数据源拆分为多个子任务并行执行，最后合并结果。数据源需要支持高效拆分（如 ArrayList、数组），元素间操作需要无状态、无副作用。

### Q6: parallelStream 什么时候比 stream 快？

当数据量大（通常 >10000）、计算密集型任务、元素间无依赖、数据源易于拆分（ArrayList > HashSet > LinkedList）时，并行流才有优势。小数据量、IO 密集型、有顺序依赖的场景下，并行流可能更慢（线程切换开销）。

### Q7: reduce 和 collect 有什么区别？

`reduce` 创建新值，不适合可变累加（如字符串拼接性能差）；`collect` 使用可变容器（如 StringBuilder），更适合可变归约。`reduce` 语义是"归约为一个值"，`collect` 语义是"收集到容器"。

### Q8: Collectors.groupingBy 的分类器（classifier）必须返回什么类型？

分类器可以是任何类型的函数 `Function<T, K>`，返回值作为 Map 的 key。常用分类器包括：`Person::getCity`（按字段分组）、`p -> p.getAge() >= 18 ? "成年" : "未成年"`（按条件分组）、`String::length`（按属性分组）。

### Q9: Stream 如何实现分页？

使用 `skip(n).limit(m)` 实现分页。第 `page` 页，每页 `size` 条：`skip((page-1) * size).limit(size)`。但注意 Stream 分页不高效（需要遍历跳过的元素），数据库层面分页（SQL LIMIT OFFSET）更优。

### Q10: Stream 中 peek 的作用和注意事项？

`peek` 是中间操作，用于调试流处理过程，对每个元素执行 Consumer 但不改变元素。注意：1) peek 是惰性的，只有终端操作触发时才执行；2) 不要用 peek 修改状态或产生副作用；3) 在 Java 9+ 中，peek 在某些场景下可能不会被调用（如 size 已知的流中 count 操作可能跳过 peek）。

### Q11: 什么是短路操作？

短路操作指不需要处理所有元素就能得出结果的操作。中间短路操作：`limit`、`takeWhile`；终端短路操作：`findFirst`、`findAny`、`anyMatch`、`allMatch`、`noneMatch`。例如 `Stream.of(1,2,3,4,5).anyMatch(n -> n > 3)` 找到 4 后立即返回 true，不会处理 5。

### Q12: 如何安全地使用并行流？

1) 不修改共享状态，使用 collect 而非 forEach+外部容器；2) 避免在并行流中使用 IO 操作（会阻塞公共线程池）；3) 使用自定义 ForkJoinPool 处理耗时任务；4) 确保数据源易于拆分；5) 避免有状态中间操作（sorted、distinct）。

*最后更新：2026-07-13*
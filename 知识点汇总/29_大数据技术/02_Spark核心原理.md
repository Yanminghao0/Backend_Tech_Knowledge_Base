# Spark核心原理

> RDD弹性分布式数据集、内存计算、DAG调度、Shuffle机制、Spark SQL与性能调优

---

## 📋 目录

1. [Spark概述](#1-spark概述)
2. [RDD弹性分布式数据集](#2-rdd弹性分布式数据集)
3. [DataFrame与Dataset](#3-dataframe与dataset)
4. [Spark SQL](#4-spark-sql)
5. [DAG调度与Shuffle](#5-dag调度与shuffle)
6. [性能调优](#6-性能调优)
7. [面试题速查](#7-面试题速查)

---

## 1. Spark概述

```
Spark vs MapReduce：

  ┌──────────────────────────────────────────────┐
  │  MapReduce         │  Spark                  │
  │  ──────────        │  ──────                 │
  │  磁盘IO为主        │  内存计算为主            │
  │  每步落盘           │  中间结果内存缓存         │
  │  适合批处理         │  批处理+流处理+ML+图计算  │
  │  延迟高(分钟级)     │  延迟低(秒级)            │
  │  开发复杂(Java API) │  开发简洁(Scala/Python)  │
  └──────────────────────────────────────────────┘

Spark四大模块：
  Spark Core    — RDD API，任务调度
  Spark SQL     — 结构化数据处理(DataFrame/Dataset)
  Spark Streaming / Structured Streaming — 流计算
  MLlib         — 机器学习库
  GraphX        — 图计算

Spark运行模式：
  Local       — 本地调试
  Standalone  — Spark自带集群
  YARN        — Hadoop YARN调度(生产推荐)
  K8s         — Kubernetes部署
```

```xml
<!-- Maven依赖 -->
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-core_2.12</artifactId>
    <version>3.5.0</version>
</dependency>
<dependency>
    <groupId>org.apache.spark</groupId>
    <artifactId>spark-sql_2.12</artifactId>
    <version>3.5.0</version>
</dependency>
```

---

## 2. RDD弹性分布式数据集

### 2.1 RDD核心概念

```
RDD (Resilient Distributed Dataset) 特性：

  ┌──────────────────────────────────────────────────┐
  │  弹性       │  内存不够可落磁盘，自动重算恢复      │
  │  分布式     │  数据分布在集群多个节点               │
  │  数据集     │  只读分区的记录集合                   │
  │  不可变     │  每次转换生成新RDD                    │
  │  延迟计算   │  Action触发才真正执行                 │
  │  血缘关系   │  记录依赖链，故障可重算               │
  │  缓存       │  可手动persist/cache到内存            │
  │  分区       │  数据分片，并行处理单元               │
  └──────────────────────────────────────────────────┘

RDD五要素：
  1. 分区列表 (partitions)
  2. 每个分区的计算函数 (compute)
  3. 依赖列表 (dependencies)
  4. [可选] 分区器 (partitioner) — 仅KV类型RDD
  5. [可选] 分区优先位置 (preferredLocations)
```

### 2.2 算子分类

```java
// Spark Java API示例
public class SparkRDDExample {

    public static void main(String[] args) {
        SparkConf conf = new SparkConf()
            .setAppName("RDD-Example")
            .setMaster("local[*]");
        JavaSparkContext sc = new JavaSparkContext(conf);

        List<String> data = List.of(
            "spark is fast", "spark is easy", "spark is powerful"
        );

        // ===== Transformation (转换，延迟计算) =====
        JavaRDD<String> lines = sc.parallelize(data);

        // flatMap: 一对多映射
        JavaRDD<String> words = lines.flatMap(
            line -> Arrays.asList(line.split(" ")).iterator()
        );

        // map: 一对一转换
        JavaRDD<Tuple2<String, Integer>> pairs = words.map(
            word -> new Tuple2<>(word, 1)
        );

        // filter: 过滤
        JavaRDD<String> longWords = words.filter(w -> w.length() > 3);

        // reduceByKey: 按Key聚合
        JavaPairRDD<String, Integer> counts = JavaPairRDD.fromJavaRDD(pairs)
            .reduceByKey(Integer::sum);

        // groupByKey: 按Key分组(性能差，慎用)
        // JavaPairRDD<String, Iterable<Integer>> grouped =
        //     JavaPairRDD.fromJavaRDD(pairs).groupByKey();

        // sortBy: 排序
        JavaPairRDD<String, Integer> sorted = counts
            .sortBy(Tuple2::_2, false, 2);  // 按count降序

        // distinct: 去重
        JavaRDD<String> unique = words.distinct();

        // ===== Action (行动，触发计算) =====

        // collect: 收集到Driver
        List<Tuple2<String, Integer>> result = sorted.collect();
        result.forEach(System.out::println);

        // count: 计数
        long totalWords = words.count();
        System.out.println("Total words: " + totalWords);

        // take: 取前N个
        List<String> top3 = words.take(3);

        // reduce: 聚合
        int totalLen = words.map(String::length)
            .reduce(Integer::sum);

        // saveAsTextFile: 保存到HDFS
        sorted.saveAsTextFile("hdfs://nn:9000/output/wordcount");

        sc.close();
    }
}
```

```
常见算子分类：

  Transformation (转换):
    map        — 一对一转换
    flatMap    — 一对多展开
    filter     — 过滤
    distinct   — 去重
    union      — 合并
    intersection — 交集
    subtract   — 差集
    groupByKey — 分组(慎用)
    reduceByKey — 分组聚合(推荐)
    sortBy     — 排序
    join       — 关联
    mapValues  — 只转Value

  Action (行动):
    collect    — 收集到Driver
    count      — 计数
    take(n)    — 取前N个
    first      — 取第一个
    reduce     — 聚合
    foreach    — 遍历
    saveAsTextFile — 保存文件
    countByKey — 按Key计数
```

---

## 3. DataFrame与Dataset

### 3.1 DataFrame

```java
public class SparkDataFrameExample {

    public static void main(String[] args) {
        SparkSession spark = SparkSession.builder()
            .appName("DataFrame-Example")
            .master("local[*]")
            .getOrCreate();

        // 从JSON创建DataFrame
        Dataset<Row> df = spark.read()
            .json("hdfs://nn:9000/data/users.json");

        // 打印Schema
        df.printSchema();
        // root
        //  |-- name: string
        //  |-- age: long
        //  |-- city: string

        // DSL风格查询
        Dataset<Row> result = df
            .filter(col("age").gt(18))          // WHERE age > 18
            .groupBy(col("city"))                // GROUP BY city
            .agg(
                count("name").as("user_count"),  // COUNT(*) AS user_count
                avg("age").as("avg_age")         // AVG(age) AS avg_age
            )
            .orderBy(col("user_count").desc());  // ORDER BY user_count DESC

        result.show();

        // SQL风格查询
        df.createOrReplaceTempView("users");
        Dataset<Row> sqlResult = spark.sql(
            "SELECT city, COUNT(*) AS cnt, AVG(age) AS avg_age " +
            "FROM users WHERE age > 18 " +
            "GROUP BY city ORDER BY cnt DESC"
        );
        sqlResult.show();

        // 写入Hive表
        result.write()
            .mode(SaveMode.Overwrite)
            .saveAsTable("dws.user_city_stats");

        spark.close();
    }
}
```

### 3.2 Dataset类型安全

```java
// Dataset = DataFrame + 编译时类型检查
public class User implements Serializable {
    private String name;
    private int age;
    private String city;
    // getter/setter...
}

// Dataset<Row> = DataFrame (无类型)
// Dataset<User> = Dataset (有类型)
Dataset<User> userDS = spark.read()
    .json("hdfs://nn:9000/data/users.json")
    .as(Encoders.bean(User.class));

// 类型安全的操作
Dataset<User> adults = userDS.filter(u -> u.getAge() > 18);
// 编译时检查，运行时无序列化开销

// DataFrame vs Dataset:
//   DataFrame = Dataset<Row>，无类型检查，性能好
//   Dataset<T> = 有类型检查，编码/解码有开销
//   Java推荐: DataFrame + SQL (最简洁)
//   Scala推荐: Dataset (类型安全 + 性能)
```

---

## 4. Spark SQL

### 4.1 Catalyst优化器

```
Catalyst优化流程：

  SQL/DataFrame API
       ↓
  ┌────────────┐
  │ Unresolved │  未解析的逻辑计划
  │ Logic Plan │  (表名/列名未绑定)
  └─────┬──────┘
        ↓ Analyzer (结合Catalog解析)
  ┌────────────┐
  │ Resolved   │  解析后的逻辑计划
  │ Logic Plan │  (表名/列名绑定)
  └─────┬──────┘
        ↓ Optimizer (RBO + CBO)
  ┌────────────┐
  │ Optimized  │  优化后的逻辑计划
  │ Logic Plan │  (谓词下推/列裁剪/常量折叠)
  └─────┬──────┘
        ↓ Physical Planner
  ┌────────────┐
  │ Physical   │  物理计划
  │ Plan       │  (选择Join策略/Shuffle)
  └─────┬──────┘
        ↓ Code Generation (Whole-Stage CodeGen)
  ┌────────────┐
  │ RDD执行     │  生成Java字节码
  └────────────┘

  优化规则(RBO):
    谓词下推(Predicate Pushdown) — WHERE提前过滤
    列裁剪(Column Pruning) — 只读需要的列
    常量折叠(Constant Folding) — 1+1=2提前计算
    Join重排 — 小表驱动大表
    Broadcast Join — 小表广播避免Shuffle
```

```sql
-- 谓词下推示例
-- 优化前逻辑:
SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.age > 18;

-- 优化后:
SELECT * FROM (SELECT * FROM users WHERE age > 18) u  -- 先过滤
JOIN orders o ON u.id = o.user_id;

-- Spark自动做谓词下推，无需手动改SQL
```

### 4.2 Adaptive Query Execution (AQE)

```scala
// Spark 3.0+ AQE自适应查询
// spark.sql.adaptive.enabled = true

// AQE三大优化:

// 1. 动态合并Shuffle分区
//    运行时发现小分区合并，减少Task数
//    spark.sql.adaptive.coalescePartitions.enabled = true

// 2. 动态切换Join策略
//    运行时发现某表变小 → 切换到Broadcast Join
//    spark.sql.adaptive.localShuffleReader.enabled = true

// 3. 动态优化Skew Join
//    运行时发现数据倾斜 → 拆分大分区
//    spark.sql.adaptive.skewJoin.enabled = true
//    spark.sql.adaptive.skewJoin.skewedPartitionFactor = 5
```

---

## 5. DAG调度与Shuffle

### 5.1 宽窄依赖

```
窄依赖 (Narrow Dependency):
  父RDD一个分区 → 子RDD一个分区
  不需要Shuffle
  例: map, filter, union

  ┌─────┐     ┌─────┐
  │ P1  │────→│ P1' │
  ├─────┤     ├─────┤
  │ P2  │────→│ P2' │
  ├─────┤     ├─────┤
  │ P3  │────→│ P3' │
  └─────┘     └─────┘
  父RDD       子RDD

宽依赖 (Wide/Shuffle Dependency):
  父RDD一个分区 → 子RDD多个分区
  需要Shuffle
  例: groupByKey, reduceByKey, join, repartition

  ┌─────┐     ┌─────┐
  │ P1  │──╲──→│ P1' │
  ├─────┤  ╲  ├─────┤
  │ P2  │──╳──→│ P2' │
  ├─────┤  ╱  ├─────┤
  │ P3  │──╱──→│ P3' │
  └─────┘     └─────┘
  父RDD       子RDD

  宽窄依赖的作用:
  1. 划分Stage — 宽依赖切分Stage
  2. 故障恢复 — 窄依赖可并行重算，宽依赖需Checkpoint
  3. Stage内管道化 — 窄依赖可流水线执行
```

### 5.2 Stage划分

```
DAG → Stage划分过程：

  数据流: source → map → filter → reduceByKey → map → save

  DAG:
  [source] →narrow→ [map] →narrow→ [filter] →wide→ [reduceByKey] →narrow→ [map] →narrow→ [save]

  Stage划分: 在宽依赖处切断

  Stage 0: source → map → filter (窄依赖链，管道执行)
           ↓ Shuffle
  Stage 1: reduceByKey → map → save (窄依赖链，管道执行)

  ┌─────────────────┐    Shuffle    ┌──────────────────┐
  │    Stage 0       │ ──────────→  │    Stage 1        │
  │ source→map→filter│              │ reduceByKey→map→save│
  │ Task x N (并行)  │              │ Task x M (并行)   │
  └─────────────────┘              └──────────────────┘

  Stage内: 多个窄依赖算子融合(fusion)，一个Task执行整条链
  Stage间: Shuffle，写磁盘+网络传输
```

### 5.3 Shuffle机制

```
Spark Shuffle演进:

  Hash Shuffle (Spark 1.0-1.4):
    每个Map Task为每个Reduce Task写一个文件
    M * R 个文件 → 文件数爆炸
    ↓
  Sort Shuffle (Spark 1.1+, 默认):
    每个Map Task写一个数据文件+一个索引文件
    M 个数据文件 + M 个索引文件
    ↓
  Tungsten Sort Shuffle (Spark 1.4+):
    直接操作序列化数据，堆外内存
    性能提升但有些限制

  Shuffle Write:
    1. Map输出到内存缓冲区
    2. 按Partition ID排序
    3. Spill到磁盘(如果内存不够)
    4. Merge所有spill文件
    5. 生成数据文件 + 索引文件

  Shuffle Read:
    1. Reduce Task拉取自己Partition的数据
    2. 从各Map节点的数据文件中读取
    3. 反序列化+Merge
    4. 传给Reduce函数

  Shuffle参数调优:
    spark.sql.shuffle.partitions = 200  (默认, 调大可并行更多)
    spark.shuffle.file.buffer = 32KB    (增大可减少IO)
    spark.shuffle.io.retryWait = 5s     (拉取失败重试)
    spark.shuffle.memoryFraction = 0.2  (Shuffle内存占比)
```

---

## 6. 性能调优

### 6.1 数据倾斜

```java
// 问题: 某个Key数据量远超其他Key → 某个Task极慢
// 症状: 大部分Task很快完成，少数Task卡住

// 方案1: 增加Shuffle分区数
spark.conf.set("spark.sql.shuffle.partitions", "1000");

// 方案2: 盐化(Salting) — 给倾斜Key加随机前缀
// 原始: reduceByKey → Key="beijing"有1亿条
// 盐化: Key="0_beijing" ~ "9_beijing"，每个1000万条
Dataset<Row> salted = df.withColumn(
    "salt_key",
    concat(lit(new Random().nextInt(10) + "_"), col("city"))
);
// 先按salt_key聚合
Dataset<Row> partial = salted.groupBy("salt_key")
    .agg(sum("amount").as("partial_sum"));
// 再去掉盐前缀，二次聚合
Dataset<Row> finalResult = partial
    .withColumn("city", regexp_replace(col("salt_key"), "^\\d+_", ""))
    .groupBy("city")
    .agg(sum("partial_sum").as("total"));

// 方案3: Spark 3.0+ AQE自动处理
// spark.sql.adaptive.skewJoin.enabled = true
```

### 6.2 内存调优

```
Spark内存模型:

  ┌──────────────────────────────────────────────┐
  │               Executor内存                    │
  │  spark.executor.memory (如4GB)               │
  ├───────────────────────┬──────────────────────┤
  │   Reserved Memory 300MB │   统一内存管理        │
  │                       │  spark.memory.fraction│
  │                       │  = 0.6                │
  │                       ├──────────┬───────────┤
  │                       │ Storage  │  Execution │
  │                       │ (缓存)   │  (执行)    │
  │                       │ 可互相借  │  可互相借   │
  └───────────────────────┴──────────┴───────────┘

  关键参数:
    spark.executor.memory = 4g        (每个Executor内存)
    spark.executor.cores = 2          (每个Executor核数)
    spark.executor.instances = 10     (Executor数量)
    spark.memory.fraction = 0.6       (统一内存占比)
    spark.memory.storageFraction = 0.5 (Storage在统一内存中占比)

  调优经验:
    1. 每个Executor 2-5个Core (多了GC压力大)
    2. 每个Executor 4-8GB内存 (太大GC暂停长)
    3. 数据量大时增加Executor数而非单Executor内存
    4. 使用Kryo序列化代替Java序列化
       spark.serializer = org.apache.spark.serializer.KryoSerializer
```

```java
// 数据缓存
// cache() = persist(MEMORY_ONLY)
// persist(StorageLevel.MEMORY_AND_DISK_SER)

JavaRDD<String> cached = lines.persist(StorageLevel.MEMORY_AND_DISK_SER());
// 多次使用时缓存，避免重复计算

// 广播变量
Broadcast<Map<String, String>> cityMap = sc.broadcast(
    Map.of("1", "北京", "2", "上海", "3", "广州")
);
// 小表广播到每个Executor，避免每条数据拉取

// 累加器
LongAccumulator errorCount = sc.sc().longAccumulator("errorCount");
lines.foreach(line -> {
    try {
        process(line);
    } catch (Exception e) {
        errorCount.add(1);
    }
});
System.out.println("Errors: " + errorCount.value());
```

---

## 7. 面试题速查

**Q1: Spark为什么比MapReduce快？**

```
1. 内存计算 — 中间结果在内存，减少磁盘IO
2. DAG — 多个操作融合为Stage，减少Shuffle次数
3. 多线程模型 — Executor内多Task共享JVM，而MR每个Task一个JVM
4. 缓存 — persist/cache避免重复计算
5. Whole-Stage CodeGen — 生成优化字节码
```

**Q2: RDD的宽窄依赖？**

```
窄依赖: 父分区→子分区一对一，无Shuffle (map/filter)
宽依赖: 父分区→子分区一对多，有Shuffle (groupByKey/reduceByKey)
划分Stage: 宽依赖切断DAG，Stage内窄依赖管道化执行
```

**Q3: reduceByKey和groupByKey的区别？**

```
reduceByKey: Map端预聚合(Combiner)，减少Shuffle数据量，推荐
groupByKey: 不预聚合，所有数据Shuffle，性能差
例: word count用reduceByKey比groupByKey快10x+
```

**Q4: 如何处理数据倾斜？**

```
1. 增加分区数 spark.sql.shuffle.partitions
2. 盐化倾斜Key + 二次聚合
3. Spark 3.0 AQE自适应Skew Join
4. 过滤异常Key(如null/空字符串)
5. Broadcast Join避免Shuffle
```

**Q5: Spark的Shuffle过程？**

```
Write: Map输出→内存缓冲→排序→Spill磁盘→Merge
Read: Reduce拉取→反序列化→Merge→Reduce函数
优化: 压缩(spark.shuffle.compress)、增大缓冲、调整分区数
```

**Q6: Spark内存模型？**

```
Executor内存 = Reserved(300MB) + User(40%) + Unified(60%)
Unified = Storage(缓存) + Execution(执行)，可互相借用
关键: spark.executor.memory, spark.memory.fraction
```

---

*最后更新：2026-07-13*

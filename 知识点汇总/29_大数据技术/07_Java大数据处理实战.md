# Java大数据处理实战

> Flink Java API、Table API&SQL、UDF自定义函数、Kafka/Redis连接器与部署调优

---

## 📋 目录

1. [Flink Java API详解](#1-flink-java-api详解)
2. [Table API与SQL](#2-table-api与sql)
3. [UDF自定义函数](#3-udf自定义函数)
4. [连接器实战](#4-连接器实战)
5. [部署模式](#5-部署模式)
6. [Checkpoint调优](#6-checkpoint调优)
7. [面试题速查](#7-面试题速查)

---

## 1. Flink Java API详解

### 1.1 DataStream转换操作

```java
public class FlinkTransformExample {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(4);

        DataStream<Order> orders = env.fromElements(
            new Order(1L, "electronics", 100.0, 1001L),
            new Order(2L, "clothing", 50.0, 1002L),
            new Order(3L, "electronics", 200.0, 1001L),
            new Order(4L, "food", 10.0, 1003L),
            new Order(5L, "electronics", 150.0, 1002L)
        );

        // 1. map — 一对一转换
        DataStream<String> categories = orders.map(Order::getCategory);

        // 2. flatMap — 一对多
        DataStream<String> words = orders.flatMap(
            (Order o, Collector<String> out) -> {
                out.collect(o.getCategory());
                out.collect("user:" + o.getUserId());
            }
        ).returns(Types.STRING);

        // 3. filter — 过滤
        DataStream<Order> expensive = orders
            .filter(o -> o.getAmount() > 100);

        // 4. keyBy — 分组
        KeyedStream<Order, String> byCategory = orders
            .keyBy(Order::getCategory);

        // 5. reduce — 滚动聚合
        DataStream<Order> reduced = byCategory
            .reduce((o1, o2) -> {
                o1.setAmount(o1.getAmount() + o2.getAmount());
                return o1;
            });

        // 6. 富函数(RichFunction) — 可获取运行时上下文
        DataStream<Tuple2<String, Double>> enriched = orders
            .keyBy(Order::getCategory)
            .process(new RichProcessFunction<String, Order, Tuple2<String, Double>>() {
                private transient ValueState<Double> maxAmount;

                @Override
                public void open(Configuration parameters) {
                    ValueStateDescriptor<Double> desc =
                        new ValueStateDescriptor<>("maxAmount", Double.class);
                    maxAmount = getRuntimeContext().getState(desc);
                }

                @Override
                public void processElement(Order order, Context ctx,
                        Collector<Tuple2<String, Double>> out) throws Exception {
                    Double currentMax = maxAmount.value();
                    if (currentMax == null || order.getAmount() > currentMax) {
                        maxAmount.update(order.getAmount());
                        out.collect(Tuple2.of(order.getCategory(), order.getAmount()));
                    }
                }
            });

        // 7. 分区操作
        DataStream<Order> shuffled = orders.shuffle();     // 随机
        DataStream<Order> rebalanced = orders.rebalance();  // 轮询
        DataStream<Order> rescaled = orders.rescale();     // 本地轮询
        DataStream<Order> broadcasted = orders.broadcast(); // 广播

        // 8. 多流操作
        DataStream<Order> connected = orders
            .keyBy(Order::getUserId)
            .connect(otherStream.keyBy(OtherEvent::getUserId))
            .map(new CoMapFunction<Order, OtherEvent, Order>() {
                @Override public Order map1(Order value) { return value; }
                @Override public Order map2(OtherEvent value) {
                    return new Order(value.getId(), "other", 0.0, value.getUserId());
                }
            });

        // 9. 分流 — 侧路输出
        OutputTag<Order> bigOrderTag = new OutputTag<Order>("big"){};
        OutputTag<Order> smallOrderTag = new OutputTag<Order>("small"){};

        SingleOutputStreamOperator<Order> splitStream = orders
            .process(new ProcessFunction<Order, Order>() {
                @Override
                public void processElement(Order order, Context ctx,
                        Collector<Order> out) {
                    if (order.getAmount() > 100) {
                        ctx.output(bigOrderTag, order);
                    } else {
                        ctx.output(smallOrderTag, order);
                    }
                }
            });

        DataStream<Order> bigOrders = splitStream.getSideOutput(bigOrderTag);
        DataStream<Order> smallOrders = splitStream.getSideOutput(smallOrderTag);

        env.execute("FlinkTransformExample");
    }
}
```

### 1.2 窗口聚合

```java
// 增量聚合 — 高性能
orders
    .keyBy(Order::getCategory)
    // 滚动窗口: 1分钟
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    // 方式1: reduce — 增量聚合
    .reduce((o1, o2) -> {
        o1.setAmount(o1.getAmount() + o2.getAmount());
        return o1;
    })
    // 方式2: aggregate — 增量聚合(更灵活)
    .aggregate(new AggregateFunction<Order, Tuple2<Integer, Double>, String>() {
        @Override
        public Tuple2<Integer, Double> createAccumulator() {
            return Tuple2.of(0, 0.0);
        }
        @Override
        public Tuple2<Integer, Double> add(Order o, Tuple2<Integer, Double> acc) {
            return Tuple2.of(acc.f0 + 1, acc.f1 + o.getAmount());
        }
        @Override
        public String getResult(Tuple2<Integer, Double> acc) {
            return "count=" + acc.f0 + ", total=" + acc.f1;
        }
        @Override
        public Tuple2<Integer, Double> merge(Tuple2<Integer, Double> a, Tuple2<Integer, Double> b) {
            return Tuple2.of(a.f0 + b.f0, a.f1 + b.f1);
        }
    });

// 全量聚合 — 可访问窗口全部数据
orders
    .keyBy(Order::getCategory)
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .process(new ProcessWindowFunction<Order, String, String, TimeWindow>() {
        @Override
        public void process(String key, Context ctx,
                Iterable<Order> allOrders, Collector<String> out) {
            int count = 0;
            double max = 0;
            double sum = 0;
            for (Order o : allOrders) {
                count++;
                sum += o.getAmount();
                max = Math.max(max, o.getAmount());
            }
            out.collect(String.format("[%s] window=[%d,%d] count=%d sum=%.2f max=%.2f",
                key, ctx.window().getStart(), ctx.window().getEnd(),
                count, sum, max));
        }
    });
```

---

## 2. Table API与SQL

### 2.1 Table API

```java
public class TableApiExample {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);

        // 1. 从DataStream创建Table
        DataStream<Order> orderStream = env.fromElements(
            new Order(1L, "electronics", 100.0, 1001L),
            new Order(2L, "clothing", 50.0, 1002L)
        );

        Table orderTable = tableEnv.fromDataStream(orderStream);
        tableEnv.createTemporaryView("orders", orderTable);

        // 2. Table API查询
        Table result = tableEnv.from("orders")
            .filter($("amount").isGreater(30))
            .groupBy($("category"))
            .select(
                $("category"),
                $("amount").count().as("order_count"),
                $("amount").sum().as("total_amount")
            );

        // 3. SQL查询
        Table sqlResult = tableEnv.sqlQuery(
            "SELECT " +
            "  category, " +
            "  COUNT(*) AS order_count, " +
            "  SUM(amount) AS total_amount, " +
            "  AVG(amount) AS avg_amount, " +
            "  MAX(amount) AS max_amount " +
            "FROM orders " +
            "WHERE amount > 30 " +
            "GROUP BY category " +
            "ORDER BY total_amount DESC"
        );

        // 4. 转回DataStream
        tableEnv.toDataStream(sqlResult, OrderStats.class)
            .print();

        // 5. 写入Kafka
        tableEnv.executeSql(
            "CREATE TABLE kafka_output (" +
            "  category STRING, " +
            "  order_count BIGINT, " +
            "  total_amount DOUBLE " +
            ") WITH (" +
            "  'connector' = 'kafka', " +
            "  'topic' = 'order_stats', " +
            "  'properties.bootstrap.servers' = 'kafka:9092', " +
            "  'format' = 'json'" +
            ")"
        );

        sqlResult.executeInsert("kafka_output");

        env.execute("TableApiExample");
    }
}
```

### 2.2 窗口SQL

```sql
-- 滚动窗口聚合
SELECT
    category,
    TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
FROM orders
GROUP BY
    category,
    TUMBLE(event_time, INTERVAL '1' MINUTE);

-- 滑动窗口聚合
SELECT
    category,
    HOP_START(event_time, INTERVAL '30' SECOND, INTERVAL '2' MINUTE) AS window_start,
    HOP_END(event_time, INTERVAL '30' SECOND, INTERVAL '2' MINUTE) AS window_end,
    COUNT(*) AS cnt
FROM orders
GROUP BY
    category,
    HOP(event_time, INTERVAL '30' SECOND, INTERVAL '2' MINUTE);

-- TVF (Table-Valued Function, 推荐, Flink 1.18+)
SELECT
    category,
    window_start,
    window_end,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
FROM TABLE(
    TUMBLE(TABLE orders, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
)
GROUP BY category, window_start, window_end;

-- TopN
SELECT
    category,
    order_count,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY order_count DESC) AS rn
FROM order_stats
WHERE ROW_NUMBER() OVER (PARTITION BY category ORDER BY order_count DESC) <= 3;
```

---

## 3. UDF自定义函数

### 3.1 ScalarFunction

```java
// ScalarFunction — 一进一出
public class HashFunction extends ScalarFunction {

    // 每条数据调用一次
    public String eval(String input) {
        return DigestUtils.md5Hex(input).substring(0, 8);
    }

    public String eval(String input, int length) {
        return DigestUtils.md5Hex(input).substring(0, length);
    }
}

// 注册使用
tableEnv.createTemporarySystemFunction("hash_md5", HashFunction.class);

// SQL中使用
// SELECT hash_md5(user_id, 8) AS user_hash FROM orders;

// 脱敏UDF
public class MaskFunction extends ScalarFunction {
    public String eval(String phone) {
        if (phone == null || phone.length() < 7) return phone;
        return phone.substring(0, 3) + "****" + phone.substring(7);
    }
}
// SELECT mask(phone) FROM users;
```

### 3.2 TableFunction

```java
// TableFunction — 一进多出(类似flatMap)
public class SplitFunction extends TableFunction<String> {

    public void eval(String str) {
        if (str != null) {
            for (String s : str.split(",")) {
                collect(s.trim());
            }
        }
    }

    public void eval(String str, String delimiter) {
        if (str != null) {
            for (String s : str.split(delimiter)) {
                collect(s.trim());
            }
        }
    }
}

// 注册
tableEnv.createTemporarySystemFunction("split", SplitFunction.class);

// SQL中使用 — LATERAL TABLE
// SELECT user_id, tag
// FROM users,
// LATERAL TABLE(split(tags, ',')) AS tag;
// 一个用户有多个tag → 展开成多行

// 解析JSON数组UDF
public class JsonArrayExtractFunction extends TableFunction<Row> {
    public void eval(String jsonStr) {
        try {
            JSONArray arr = new JSONArray(jsonStr);
            for (int i = 0; i < arr.length(); i++) {
                JSONObject obj = arr.getJSONObject(i);
                collect(Row.of(
                    obj.optString("name"),
                    obj.optDouble("value")
                ));
            }
        } catch (Exception e) {
            // ignore
        }
    }

    @Override
    public TypeInformation<Row> getResultType() {
        return Types.ROW(Types.STRING, Types.DOUBLE);
    }
}
```

### 3.3 AggregateFunction

```java
// AggregateFunction — 多进一出(聚合)
public class WeightedAvgFunction extends AggregateFunction<Double, WeightedAvgAccum> {

    // 累加器
    public static class WeightedAvgAccum {
        public double sum = 0;
        public int count = 0;
    }

    @Override
    public WeightedAvgAccum createAccumulator() {
        return new WeightedAvgAccum();
    }

    // 每条数据调用
    public void accumulate(WeightedAvgAccum acc, Double value, Integer weight) {
        if (value != null && weight != null) {
            acc.sum += value * weight;
            acc.count += weight;
        }
    }

    // 撤回(Retract流)
    public void retract(WeightedAvgAccum acc, Double value, Integer weight) {
        if (value != null && weight != null) {
            acc.sum -= value * weight;
            acc.count -= weight;
        }
    }

    @Override
    public Double getValue(WeightedAvgAccum acc) {
        return acc.count == 0 ? null : acc.sum / acc.count;
    }

    // 合并(用于Session Window等)
    public void merge(WeightedAvgAccum acc, Iterable<WeightedAvgAccum> it) {
        for (WeightedAvgAccum other : it) {
            acc.sum += other.sum;
            acc.count += other.count;
        }
    }
}

// 注册使用
tableEnv.createTemporarySystemFunction("weighted_avg", WeightedAvgFunction.class);
// SELECT category, weighted_avg(amount, quantity) FROM orders GROUP BY category;
```

---

## 4. 连接器实战

### 4.1 Kafka连接器

```sql
-- Kafka Source
CREATE TABLE kafka_source (
    order_id BIGINT,
    user_id BIGINT,
    category STRING,
    amount DOUBLE,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'orders',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'flink-processor',
    'scan.startup.mode' = 'group-offsets',
    'scan.startup.specific-offsets' = '',  -- 或 specific-offsets
    'format' = 'json',
    'json.fail-on-missing-field' = 'false',
    'json.ignore-parse-errors' = 'true'
);

-- Kafka Sink
CREATE TABLE kafka_sink (
    category STRING,
    order_count BIGINT,
    total_amount DOUBLE,
    window_end TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'order_stats',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'sink.delivery-guarantee' = 'exactly-once',
    'sink.transactional-id-prefix' = 'order-stats-tx'
);

-- 多Topic消费
CREATE TABLE kafka_multi_topic (
    topic STRING METADATA FROM TOPIC,
    partition INT METADATA FROM PARTITION,
    `offset` BIGINT METADATA FROM OFFSET,
    `timestamp` TIMESTAMP(3) METADATA FROM TIMESTAMP,
    `key` STRING METADATA FROM KEY,
    value STRING
) WITH (
    'connector' = 'kafka',
    'topic' = 'orders;payments;refunds',  -- 分号分隔多Topic
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'raw'
);
```

### 4.2 Redis连接器

```java
// Redis Sink — 自定义
public class RedisSink extends RichSinkFunction<AggResult> {

    private transient JedisCluster jedis;

    @Override
    public void open(Configuration parameters) throws Exception {
        Set<HostAndPort> nodes = new HashSet<>();
        nodes.add(new HostAndPort("redis-node1", 6379));
        nodes.add(new HostAndPort("redis-node2", 6379));
        jedis = new JedisCluster(nodes);
    }

    @Override
    public void invoke(AggResult result, Context context) throws Exception {
        String key = "realtime:stats:" + result.getCategory();
        String field = String.valueOf(result.getWindowEnd());
        String value = result.getTotalAmount() + ":" + result.getOrderCount();

        // Hash结构: key=分类, field=窗口结束时间, value=金额:数量
        jedis.hset(key, field, value);
        // 设置过期时间
        jedis.expire(key, 86400);  // 24小时
    }

    @Override
    public void close() throws Exception {
        if (jedis != null) jedis.close();
    }
}

// Redis Source — 维表查询(异步)
public class RedisAsyncLookup extends RichAsyncFunction<String, Tuple2<String, String>> {

    private transient JedisPool jedisPool;

    @Override
    public void open(Configuration parameters) throws Exception {
        JedisPoolConfig config = new JedisPoolConfig();
        config.setMaxTotal(100);
        config.setMaxIdle(20);
        jedisPool = new JedisPool(config, "redis-host", 6379);
    }

    @Override
    public void asyncInvoke(String key, ResultFuture<Tuple2<String, String>> future) {
        CompletableFuture.supplyAsync(() -> {
            try (Jedis jedis = jedisPool.getResource()) {
                String value = jedis.get("dim:" + key);
                return Tuple2.of(key, value != null ? value : "unknown");
            }
        }).thenAccept(result -> {
            future.complete(Collections.singletonList(result));
        }).exceptionally(e -> {
            future.completeExceptionally(e);
            return null;
        });
    }
}
```

### 4.3 JDBC连接器

```sql
-- JDBC Source (维表)
CREATE TABLE dim_product (
    product_id BIGINT,
    product_name STRING,
    category STRING,
    price DECIMAL(10, 2)
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://mysql:3306/ecommerce',
    'table-name' = 'products',
    'username' = 'root',
    'password' = 'xxx',
    'lookup.cache.max-rows' = '10000',   -- 缓存行数
    'lookup.cache.ttl' = '5min',         -- 缓存TTL
    'lookup.max-retries' = '3'
);

-- Temporal Table Join (维表关联)
SELECT
    o.order_id,
    o.user_id,
    o.amount,
    p.product_name,
    p.category
FROM orders AS o
LEFT JOIN dim_product FOR SYSTEM_TIME AS OF o.proctime AS p
ON o.product_id = p.product_id;

-- JDBC Sink
CREATE TABLE jdbc_sink (
    category STRING,
    order_count BIGINT,
    total_amount DOUBLE,
    dt DATE
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:mysql://mysql:3306/report',
    'table-name' = 'daily_category_stats',
    'username' = 'root',
    'password' = 'xxx',
    'sink.buffer-flush.max-rows' = '500',   -- 批量写入行数
    'sink.buffer-flush.interval' = '2s',    -- 刷新间隔
    'sink.max-retries' = '3'
);
```

---

## 5. 部署模式

```
Flink部署模式:

  ┌──────────────────────────────────────────────────┐
  │  模式          │  说明                            │
  │  ─────        │  ──────                         │
  │  Local        │  本地调试，单JVM                  │
  │  Standalone   │  Flink自带集群                    │
  │  YARN         │  Hadoop YARN调度(生产推荐)        │
  │  K8s          │  Kubernetes原生部署               │
  │  Docker       │  Docker容器部署                   │
  └──────────────────────────────────────────────────┘

  YARN部署两种模式:

  1. Session Mode — 共享集群
     预先启动YARN Session → 多个Job共享
     优点: 资源共享，启动快
     缺点: Job间互相影响，资源隔离差
     适合: 短任务、开发测试

  2. Per-Job Mode — 独立集群(已废弃)
     每个Job启动独立YARN Application
     优点: 资源隔离好
     缺点: 启动慢，资源利用率低

  3. Application Mode — 每应用一集群(推荐)
     main()在集群中执行
     每个Application独立Cluster
     优点: 资源隔离 + 启动快
     适合: 生产环境
```

```bash
# YARN Application Mode部署
/flink/bin/flink run-application \
    -t yarn-application \
    -Djobmanager.memory.process.size=2048m \
    -Dtaskmanager.memory.process.size=4096m \
    -Dtaskmanager.numberOfTaskSlots=2 \
    -Dparallelism.default=4 \
    -Dyarn.application.name="order-processor" \
    -Dyarn.application.queue="production" \
    -c com.example.OrderProcessor \
    ./flink-jobs.jar \
    --config /path/to/config.yaml

# K8s Application Mode部署
/flink/bin/flink run-application \
    -t kubernetes-application \
    -Dkubernetes.cluster-id=order-processor \
    -Dkubernetes.container.image=flink:1.18 \
    -Dkubernetes.namespace=flink \
    -Djobmanager.memory.process.size=2048m \
    -Dtaskmanager.memory.process.size=4096m \
    -Dkubernetes.taskmanager.replicas=4 \
    -c com.example.OrderProcessor \
    ./flink-jobs.jar

# 作业取消与Savepoint
# 取消并保存Savepoint
/flink/bin/flink cancel --withSavepoint hdfs:///savepoints/ <jobId>

# 从Savepoint恢复
/flink/bin/flink run -s hdfs:///savepoints/savepoint-xxx \
    -c com.example.OrderProcessor ./flink-jobs.jar
```

---

## 6. Checkpoint调优

```
Checkpoint关键参数:

  ┌──────────────────────────────────────────────────┐
  │  参数                     │  推荐值               │
  │  ────────                │  ──────              │
  │  间隔                     │  1-5分钟(非越短越好)  │
  │  超时                     │  10分钟              │
  │  最小间隔                 │  30秒               │
  │  最大并发                 │  1                   │
  │  对齐模式                 │  非对齐(大状态)       │
  │  状态后端                 │  RocksDB(大状态)     │
  │  增量Checkpoint           │  开启(大状态)        │
  └──────────────────────────────────────────────────┘

  间隔不要太短!
    - 间隔太短 → 频繁快照 → 影响吞吐
    - 间隔太长 → 故障恢复数据多
    - 经验: 间隔 = 可接受的恢复重放时间
```

```java
// Checkpoint优化配置
public class CheckpointConfigExample {

    public static void config(StreamExecutionEnvironment env) {
        // 1. 基础配置
        env.enableCheckpointing(120_000);  // 2分钟
        CheckpointConfig config = env.getCheckpointConfig();

        // 2. 模式选择
        config.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);

        // 3. 非对齐Checkpoint(解决反压下Checkpoint对齐慢)
        config.enableUnalignedCheckpoints(true);
        // 非对齐只在EXACTLY_ONCE模式生效
        // 适合: 有反压的大状态作业

        // 4. 超时与间隔
        config.setCheckpointTimeout(600_000);        // 10分钟超时
        config.setMinPauseBetweenCheckpoints(60_000); // 最小间隔1分钟
        config.setMaxConcurrentCheckpoints(1);        // 不并发

        // 5. 外部化Checkpoint
        config.setExternalizedCheckpointCleanup(
            CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);

        // 6. 容忍失败
        config.setTolerableCheckpointFailureNumber(3);

        // 7. 状态后端 — RocksDB
        env.setStateBackend(new EmbeddedRocksDBStateBackend());

        // 8. 增量Checkpoint
        config.setIncrementalCheckpointing(true,
            new RocksDBStateBackend.RocksDBOptionsFactory() {
                @Override
                public RocksDBOptionsBuilder createOptions(
                        RocksDBOptionsBuilder currentOptions) {
                    return currentOptions
                        .setMaxBackgroundThreads(4)
                        .setWriteBufferSize("64MB");
                }
            });

        // 9. Checkpoint存储位置
        config.setCheckpointStorage("hdfs:///checkpoints/order-processor");

        // 10. 本地恢复(从本地磁盘恢复, 减少网络传输)
        config.setLocalRecoveryEnabled(true);
    }
}
```

```
大作业调优经验:

  1. 并行度
     - 按Kafka分区数: parallelism = partition数 或 其整数倍
     - 按数据量: 每个TaskManager处理 100-500MB/秒
     - 按Slot: TM的Slot数 × TM数 ≥ 并行度

  2. 内存
     - TM内存: 4-8GB(太大GC长)
     - 状态: RocksDB + 堆外内存
     - 网络缓冲: taskmanager.network.memory.fraction = 0.15

  3. 序列化
     - 用Flink自带TypeSerializer(不开箱)
     - 注册子类: env.registerType(MyClass.class)
     - 避免Java序列化(性能差10x)

  4. 状态TTL
     - 设置状态TTL防止状态无限增长
     - StateTtlConfig.newBuilder(Time.days(7)).cleanupInRocksdbCompactBackend()

  5. Operator Chain
     - 默认开启operator chaining(窄依赖融合)
     - 窄依赖不用disableChaining
     - 调试时可用startNewChain()
```

---

## 7. 面试题速查

**Q1: Flink的RichFunction和普通Function的区别？**

```
RichFunction有生命周期方法:
  open() — 初始化(可获取RuntimeContext、创建状态)
  close() — 清理资源
  getRuntimeContext() — 获取运行时上下文(状态、累加器)
普通Function只有纯计算逻辑
需要状态/缓存/初始化 → 用RichFunction
```

**Q2: Flink Table API和DataStream API怎么选？**

```
DataStream API: 灵活、底层、适合复杂逻辑(CEP/状态管理)
Table API/SQL: 声明式、简洁、适合ETL/聚合/JOIN
选择: 简单ETL用SQL，复杂逻辑用DataStream，可混用
```

**Q3: Flink的UDF有哪几种？**

```
ScalarFunction: 一进一出(如脱敏、格式转换)
TableFunction: 一进多出(如分词、JSON展开)
AggregateFunction: 多进一出(如自定义加权平均)
TableAggregateFunction: 多进多出(如TopN)
```

**Q4: Flink on YARN的部署模式？**

```
Session: 共享集群，多Job复用，适合测试
Per-Job: 每Job独立(已废弃)
Application: 每应用独立集群，main在集群执行，生产推荐
```

**Q5: Flink大作业Checkpoint如何调优？**

```
1. 间隔2-5分钟(不要太短)
2. 非对齐Checkpoint(反压场景)
3. RocksDB状态后端 + 增量Checkpoint
4. 设置TTL控制状态增长
5. 设置可容忍失败次数(3次)
6. 合理设置超时(10分钟)和最小间隔(1分钟)
```

---

*最后更新：2026-07-13*

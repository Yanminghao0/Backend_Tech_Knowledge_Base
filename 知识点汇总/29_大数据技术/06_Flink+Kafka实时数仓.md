# Flink+Kafka实时数仓

> Lambda/Kappa架构、Flink+Kafka分层实时数仓、Exactly-Once保证与反压处理

---

## 📋 目录

1. [实时数仓概述](#1-实时数仓概述)
2. [Lambda与Kappa架构](#2-lambda与kappa架构)
3. [实时数仓分层架构](#3-实时数仓分层架构)
4. [Flink+Kafka实现](#4-flinkkafka实现)
5. [Exactly-Once保证](#5-exactly-once保证)
6. [反压处理](#6-反压处理)
7. [面试题速查](#7-面试题速查)

---

## 1. 实时数仓概述

```
离线数仓 vs 实时数仓:

  ┌──────────────────────────────────────────────────┐
  │  离线数仓          │  实时数仓                    │
  │  ──────────       │  ──────────                  │
  │  T+1延迟           │  秒级延迟                     │
  │  Hive/Spark        │  Flink/Kafka/ClickHouse      │
  │  全量批处理        │  增量流处理                   │
  │  数据一致性好      │  数据一致性挑战大             │
  │  计算资源固定      │  常驻计算资源                 │
  │  成本低            │  成本高                       │
  └──────────────────────────────────────────────────┘

  实时数仓价值:
    - 实时大屏(双十一GMV)
    - 实时风控(欺诈检测)
    - 实时推荐(用户行为实时反馈)
    - 实时监控(系统/业务告警)
    - 实时报表(当日数据实时看)
```

---

## 2. Lambda与Kappa架构

### 2.1 Lambda架构

```
Lambda架构 — 批流并存:

  ┌──────────────────────────────────────────────────────┐
  │                    Batch Layer (批处理层)              │
  │  HDFS + Hive/Spark                                    │
  │  全量数据，离线计算，T+1                               │
  │  → Batch View                                        │
  ├──────────────────────────────────────────────────────┤
  │                    Speed Layer (速度层)               │
  │  Kafka + Storm/Flink                                 │
  │  增量数据，实时计算，秒级                              │
  │  → Real-time View                                    │
  ├──────────────────────────────────────────────────────┤
  │                    Serving Layer (服务层)             │
  │  HBase/ClickHouse/Redis                              │
  │  合并Batch View + Real-time View                     │
  │  → 查询结果                                           │
  └──────────────────────────────────────────────────────┘

  查询 = Batch View + Real-time View

  优点: 兼顾实时性和准确性
  缺点: 两套代码(批+流)，维护成本高，口径可能不一致
```

### 2.2 Kappa架构

```
Kappa架构 — 只有流处理:

  ┌──────────────────────────────────────────────────────┐
  │                    Speed Layer (流处理层)              │
  │  Kafka (消息队列，保留全部历史数据)                    │
  │       ↓                                               │
  │  Flink (流处理引擎)                                   │
  │       ↓                                               │
  │  ClickHouse/HBase (实时结果存储)                      │
  └──────────────────────────────────────────────────────┘

  核心: Kafka作为唯一数据源，保留足够长的历史数据
  需要重算 → 从Kafka更早的Offset重新消费

  优点: 一套代码，口径统一，维护简单
  缺点: Kafka存储全量历史数据成本高，重算时间长

  实际选择: 大多数公司用Lambda(批保证准确+流保证实时)
  Flink批流统一推动Kappa落地
```

---

## 3. 实时数仓分层架构

```
实时数仓分层(对标离线数仓):

  ┌──────────────────────────────────────────────────────┐
  │                    ADS (应用层)                       │
  │  ClickHouse/Redis — 实时大屏/报表/接口                │
  │  如: 实时GMV、实时UV、实时TopN                        │
  ├──────────────────────────────────────────────────────┤
  │                    DWS (汇总层)                       │
  │  Flink窗口聚合 — Kafka Topic                         │
  │  如: 用户分钟级汇总、商品分钟级汇总                   │
  ├──────────────────────────────────────────────────────┤
  │                    DWD (明细层)                       │
  │  Flink清洗+维度关联 — Kafka Topic                    │
  │  如: 订单明细(标准化+维度补充)                        │
  ├──────────────────────────────────────────────────────┤
  │                    ODS (贴源层)                       │
  │  Kafka原始Topic — CDC/日志采集                        │
  │  如: MySQL binlog、Nginx日志、业务日志                │
  └──────────────────────────────────────────────────────┘

  数据流:
    MySQL → Flink CDC → Kafka(ODS) → Flink → Kafka(DWD)
    → Flink → Kafka(DWS) → ClickHouse(ADS)

  核心思路: 每层用Kafka Topic存储，Flink做层间处理
```

---

## 4. Flink+Kafka实现

### 4.1 ODS层 — CDC数据采集

```java
// Flink CDC — MySQL binlog实时同步到Kafka
public class ODS_CDC_Sync {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(4);
        env.enableCheckpointing(60_000);

        // MySQL CDC Source
        MySqlSource<String> mySqlSource = MySqlSource.<String>builder()
            .hostname("mysql-host")
            .port(3306)
            .databaseList("ecommerce")
            .tableList("ecommerce.orders", "ecommerce.order_items")
            .username("flink")
            .password("xxx")
            .deserializer(new JsonDebeziumDeserializationSchema())
            .build();

        // CDC数据流
        DataStreamSource<String> cdcStream = env.fromSource(
            mySqlSource,
            WatermarkStrategy.noWatermarks(),
            "mysql-cdc"
        );

        // 写入Kafka ODS Topic
        cdcStream.sinkTo(KafkaSink.<String>builder()
            .setBootstrapServers("kafka:9092")
            .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                .setTopic("ods_order_cdc")
                .setValueSerializationSchema(new SimpleStringSchema())
                .build())
            .setDeliveryGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
            .build()
        );

        env.execute("ODS-CDC-Sync");
    }
}
```

### 4.2 DWD层 — 清洗+维度关联

```java
// DWD层: 消费ODS Topic → 清洗+维度关联 → 写入DWD Topic
public class DWD_OrderProcess {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(4);
        env.enableCheckpointing(60_000);

        // 1. 消费ODS Kafka
        KafkaSource<String> odsSource = KafkaSource.<String>builder()
            .setBootstrapServers("kafka:9092")
            .setTopics("ods_order_cdc")
            .setGroupId("dwd-order-process")
            .setStartingOffsets(OffsetsInitializer.earliest())
            .setValueOnlyDeserializer(new SimpleStringSchema())
            .build();

        DataStream<String> odsStream = env.fromSource(
            odsSource,
            WatermarkStrategy.forBoundedOutOfOrderness(Duration.ofSeconds(5)),
            "ods-source"
        );

        // 2. 解析CDC JSON → 订单对象
        DataStream<OrderEvent> orders = odsStream
            .map(this::parseOrder)
            .filter(Objects::nonNull)
            .filter(o -> o.getAmount() != null && o.getAmount().compareTo(BigDecimal.ZERO) > 0);

        // 3. 维度关联 — 异步查维表
        DataStream<EnrichedOrder> enriched = AsyncDataStream
            .unorderedWait(
                orders,
                new DimAsyncFunction(),   // 异步查Redis维表
                3, TimeUnit.SECONDS,      // 超时
                100                        // 并发
            );

        // 4. 写入DWD Kafka
        enriched
            .map(this::toJson)
            .sinkTo(KafkaSink.<String>builder()
                .setBootstrapServers("kafka:9092")
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                    .setTopic("dwd_order_enriched")
                    .setValueSerializationSchema(new SimpleStringSchema())
                    .build())
                .setDeliveryGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
                .build()
            );

        env.execute("DWD-Order-Process");
    }
}

// 异步维表查询
public class DimAsyncFunction extends RichAsyncFunction<OrderEvent, EnrichedOrder> {

    private transient JedisPool jedisPool;

    @Override
    public void open(Configuration parameters) {
        jedisPool = new JedisPool("redis-host", 6379);
    }

    @Override
    public void asyncInvoke(OrderEvent order, ResultFuture<EnrichedOrder> future) {
        // 异步查Redis维表
        CompletableFuture.supplyAsync(() -> {
            try (Jedis jedis = jedisPool.getResource()) {
                String userInfo = jedis.get("dim_user:" + order.getUserId());
                String productInfo = jedis.get("dim_product:" + order.getProductId());
                return new EnrichedOrder(order, userInfo, productInfo);
            }
        }).thenAccept(result -> {
            if (result != null) {
                future.complete(Collections.singletonList(result));
            } else {
                future.complete(Collections.emptyList());
            }
        });
    }
}
```

### 4.3 DWS层 — 窗口聚合

```java
// DWS层: 消费DWD → 窗口聚合 → 写入DWS Topic
public class DWS_UserAgg {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(4);
        env.enableCheckpointing(60_000);

        // 1. 消费DWD Kafka
        DataStream<EnrichedOrder> dwdStream = env.fromSource(
            KafkaSource.<EnrichedOrder>builder()
                .setBootstrapServers("kafka:9092")
                .setTopics("dwd_order_enriched")
                .setGroupId("dws-user-agg")
                .setValueOnlyDeserializer(new EnrichedOrderDeserializer())
                .build(),
            WatermarkStrategy.<EnrichedOrder>forBoundedOutOfOrderness(
                Duration.ofSeconds(10))
                .withTimestampAssigner((e, t) -> e.getEventTime()),
            "dwd-source"
        );

        // 2. 按用户分组 + 1分钟滚动窗口聚合
        dwdStream
            .keyBy(EnrichedOrder::getUserId)
            .window(TumblingEventTimeWindows.of(Time.minutes(1)))
            .aggregate(new UserAggFunction())
            .sinkTo(KafkaSink.<UserAggResult>builder()
                .setBootstrapServers("kafka:9092")
                .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                    .setTopic("dws_user_minute_agg")
                    .setValueSerializationSchema(new UserAggSerializer())
                    .build())
                .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)
                .build()
            );

        env.execute("DWS-User-Agg");
    }
}

// 聚合函数
public class UserAggFunction
        implements AggregateFunction<EnrichedOrder, UserAggState, UserAggResult> {

    @Override
    public UserAggState createAccumulator() {
        return new UserAggState();
    }

    @Override
    public UserAggState add(EnrichedOrder order, UserAggState acc) {
        acc.userId = order.getUserId();
        acc.orderCount++;
        acc.totalAmount = acc.totalAmount.add(order.getAmount());
        if (acc.firstOrderTime == null) {
            acc.firstOrderTime = order.getEventTime();
        }
        acc.lastOrderTime = order.getEventTime();
        return acc;
    }

    @Override
    public UserAggResult getResult(UserAggState acc) {
        return new UserAggResult(
            acc.userId,
            acc.orderCount,
            acc.totalAmount,
            acc.firstOrderTime,
            acc.lastOrderTime,
            System.currentTimeMillis()
        );
    }

    @Override
    public UserAggState merge(UserAggState a, UserAggState b) {
        a.orderCount += b.orderCount;
        a.totalAmount = a.totalAmount.add(b.totalAmount);
        return a;
    }
}
```

### 4.4 ADS层 — 写入ClickHouse

```java
// ADS层: 消费DWS → 写入ClickHouse
public class ADS_ClickHouseSink {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();

        // 消费DWS Kafka
        DataStream<UserAggResult> dwsStream = env.fromSource(
            KafkaSource.<UserAggResult>builder()
                .setBootstrapServers("kafka:9092")
                .setTopics("dws_user_minute_agg")
                .setGroupId("ads-clickhouse-sink")
                .setValueOnlyDeserializer(new UserAggDeserializer())
                .build(),
            WatermarkStrategy.noWatermarks(),
            "dws-source"
        );

        // 写入ClickHouse
        dwsStream.addSink(new ClickHouseSink(
            "jdbc:clickhouse://ch-host:8123/default",
            "INSERT INTO ads_user_realtime " +
            "(user_id, order_count, total_amount, window_start, window_end, ts) " +
            "VALUES (?, ?, ?, ?, ?, ?)"
        ));

        // ClickHouse建表
        // CREATE TABLE ads_user_realtime (
        //     user_id UInt64,
        //     order_count UInt32,
        //     total_amount Decimal(10,2),
        //     window_start DateTime,
        //     window_end DateTime,
        //     ts DateTime
        // ) ENGINE = MergeTree()
        // ORDER BY (ts, user_id);

        env.execute("ADS-ClickHouse-Sink");
    }
}
```

---

## 5. Exactly-Once保证

```
端到端Exactly-Once = Source可重放 + Checkpoint + Sink两阶段提交

  ┌──────────────────────────────────────────────────┐
  │  Source (Kafka)     │  可重放(offset存入Checkpoint)│
  │  Flink处理          │  Checkpoint快照状态          │
  │  Sink (Kafka/CH)    │  两阶段提交(2PC)             │
  └──────────────────────────────────────────────────┘

  两阶段提交(2PC)流程:
    1. Checkpoint开始 → Source记录offset
    2. 数据处理 → Sink预提交(写入临时事务)
    3. Checkpoint完成 → JobManager通知各Operator
    4. Sink收到通知 → 正式提交事务
    5. 如果失败 → 回滚预提交的数据

  Kafka Sink两阶段提交:
    开启事务 → 写数据(未提交) → Checkpoint成功 → 提交事务
    消费者需设置isolation.level=read_committed
```

```java
// Flink Kafka Exactly-Once配置
KafkaSink.<String>builder()
    .setBootstrapServers("kafka:9092")
    .setRecordSerializer(...)
    .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)  // 端到端精确一次
    .setProperty("transaction.timeout.ms", "900000")  // 事务超时15分钟
    .build();

// Kafka消费者端配置
KafkaSource.<String>builder()
    .setProperty("isolation.level", "read_committed")  // 只读已提交的消息
    ...
    .build();

// 注意事项:
// 1. Kafka事务超时 < broker transaction.max.timeout.ms(默认15分钟)
// 2. Checkpoint间隔 < 事务超时
// 3. Exactly-Once有额外开销，At-Least-Once性能更好
// 4. 下游需幂等消费(At-Least-Once + 幂等 = Exactly-Once效果)
```

---

## 6. 反压处理

```
反压(Backpressure) — 消费速度 < 生产速度，数据积压

  症状:
    - Kafka消费lag持续增长
    - Checkpoint超时/失败
    - 部分Task处理极慢
    - 作业延迟飙升

  ┌──────────────────────────────────────────────────┐
  │  反压诊断:                                         │
  │  1. Flink Web UI → BackPressure标签页              │
  │     High: 反压严重                                 │
  │     Low: 正常                                      │
  │  2. 检查各Operator处理速率                         │
  │  3. 检查Kafka消费Lag                               │
  └──────────────────────────────────────────────────┘

  常见原因及解决:

  1. 数据倾斜
     症状: 某些Task极慢，其他空闲
     解决: 盐化Key + 二次聚合 / AQE

  2. 外部调用慢(维表查询/DB写入)
     症状: Sink或AsyncIO慢
     解决: 异步IO + 批量操作 + 缓存

  3. GC频繁
     症状: TaskManager GC日志频繁Full GC
     解决: 增大TM内存 / 优化对象创建 / 用RocksDB

  4. Checkpoint瓶颈
     症状: Checkpoint对齐慢/状态大
     解决: 非对齐Checkpoint / 增量Checkpoint / 减少状态

  5. 下游能力不足
     症状: Sink写入慢
     解决: 增加并行度 / 批量写入 / 换更快的存储
```

```java
// 反压优化实践

// 1. 异步维表查询 + 缓存
AsyncDataStream.unorderedWait(
    stream,
    new CachedAsyncFunction(),  // 带Guava Cache
    3, TimeUnit.SECONDS,
    100
);

// 2. 批量Sink — 减少IO次数
public class BatchClickHouseSink extends RichSinkFunction<EnrichedOrder> {
    private List<EnrichedOrder> buffer = new ArrayList<>();
    private static final int BATCH_SIZE = 1000;

    @Override
    public void invoke(EnrichedOrder value, Context context) throws Exception {
        buffer.add(value);
        if (buffer.size() >= BATCH_SIZE) {
            flush();
        }
    }

    private void flush() throws Exception {
        if (buffer.isEmpty()) return;
        // 批量写入
        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            for (EnrichedOrder e : buffer) {
                ps.setLong(1, e.getUserId());
                ps.addBatch();
            }
            ps.executeBatch();
        }
        buffer.clear();
    }
}

// 3. 动态资源调整(Flink 1.18+ Adaptive Scheduler)
// adaptive-batch.scheduler-mode: ADAPTIVE
// 根据数据量自动调整并行度
```

---

## 7. 面试题速查

**Q1: Lambda和Kappa架构的区别？**

```
Lambda: 批+流两套代码，Serving层合并结果，维护复杂但准确
Kappa: 只有流，Kafka存全量，重算回溯，维护简单但存储成本高
趋势: Flink批流统一推动Kappa
```

**Q2: 实时数仓分层设计？**

```
ODS: Kafka原始Topic(CDC/日志)
DWD: Flink清洗+维度关联 → Kafka
DWS: Flink窗口聚合 → Kafka
ADS: ClickHouse/Redis → 实时大屏/接口
每层用Kafka Topic存储，Flink做层间处理
```

**Q3: Flink如何保证端到端Exactly-Once？**

```
Source可重放(Kafka offset入Checkpoint)
+ Flink Checkpoint(状态快照)
+ Sink两阶段提交(Kafka事务)
下游设置read_committed隔离级别
```

**Q4: 反压如何诊断和解决？**

```
诊断: Flink Web UI BackPressure页 + Kafka消费Lag
原因: 数据倾斜/外部调用慢/GC频繁/下游能力不足
解决: 盐化/异步缓存/增内存/批量写入/增加并行度
```

**Q5: 实时数仓中维表关联怎么做？**

```
1. 异步查询 — AsyncDataStream + Redis/HBase维表
2. 广播流 — 维表小数据广播到各TaskManager
3. 临时表 — Flink SQL JOIN维表(Temporal Table Join)
4. 预加载 — 状态缓存维表数据，定时刷新
```

---

*最后更新：2026-07-13*

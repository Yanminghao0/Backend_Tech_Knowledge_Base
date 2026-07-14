# Flink流计算实战

> DataStream API、窗口机制、水位线Watermark、状态管理、Checkpoint与CEP复杂事件处理

---

## 📋 目录

1. [Flink概述](#1-flink概述)
2. [DataStream API](#2-datastream-api)
3. [窗口机制](#3-窗口机制)
4. [水位线Watermark](#4-水位线watermark)
5. [状态管理](#5-状态管理)
6. [Checkpoint机制](#6-checkpoint机制)
7. [CEP复杂事件处理](#7-cep复杂事件处理)
8. [面试题速查](#8-面试题速查)

---

## 1. Flink概述

```
Flink vs Spark Streaming:

  ┌──────────────────────────────────────────────────┐
  │  Spark Streaming      │  Flink                   │
  │  ──────────────       │  ─────                   │
  │  微批处理(Micro-Batch)│  真正流处理(Event-at-a-time)│
  │  RDD序列化处理         │  逐条处理                  │
  │  延迟秒级              │  延迟毫秒级                │
  │  吞吐量高              │  吞吐量高                  │
  │  Exactly-Once(有限)   │  Exactly-Once(原生)       │
  │  SQL成熟              │  SQL完善                   │
  │  生态好(背靠Spark)     │  流计算领域首选             │
  └──────────────────────────────────────────────────┘

Flink核心特性:
  - 真正流处理: 逐条处理，毫秒级延迟
  - Exactly-Once: 端到端精确一次语义
  - 有状态计算: 支持丰富的状态管理
  - Event Time: 基于事件时间处理
  - CEP: 复杂事件处理引擎
  - 批流统一: DataStream API统一处理批和流
  - Checkpoint: 分布式快照容错机制
```

```xml
<!-- Maven依赖 -->
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-java</artifactId>
    <version>1.18.0</version>
</dependency>
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-streaming-java</artifactId>
    <version>1.18.0</version>
</dependency>
<dependency>
    <groupId>org.apache.flink</groupId>
    <artifactId>flink-connector-kafka</artifactId>
    <version>1.18.0</version>
</dependency>
```

---

## 2. DataStream API

### 2.1 基本流程

```java
public class FlinkWordCount {

    public static void main(String[] args) throws Exception {
        // 1. 创建执行环境
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();
        env.setParallelism(4);
        env.enableCheckpointing(60000);  // 60秒一次Checkpoint

        // 2. 数据源 — Kafka
        KafkaSource<String> kafkaSource = KafkaSource.<String>builder()
            .setBootstrapServers("kafka1:9092,kafka2:9092")
            .setTopics("user-action")
            .setGroupId("flink-wordcount")
            .setStartingOffsets(OffsetsInitializer.earliest())
            .setValueOnlyDeserializer(new SimpleStringSchema())
            .build();

        DataStream<String> stream = env.fromSource(
            kafkaSource,
            WatermarkStrategy.noWatermarks(),
            "kafka-source"
        );

        // 3. 数据转换
        DataStream<Tuple2<String, Integer>> counts = stream
            // flatMap: 分词
            .flatMap((String line, Collector<Tuple2<String, Integer>> out) -> {
                for (String word : line.split("\\s+")) {
                    out.collect(Tuple2.of(word, 1));
                }
            })
            .returns(Types.TUPLE(Types.STRING, Types.INT))

            // keyBy: 按word分组
            .keyBy(t -> t.f0)

            // sum: 聚合
            .sum(1);

        // 4. 输出 — Kafka
        counts.map(t -> t.f0 + ":" + t.f1)
            .sinkTo(KafkaSink.<String>builder()
                .setBootstrapServers("kafka1:9092")
                .setRecordSerializer(new SimpleStringSchema())
                .setDeliveryGuarantee(DeliveryGuarantee.AT_LEAST_ONCE)
                .build()
            );

        // 5. 执行
        env.execute("WordCount");
    }
}
```

### 2.2 常用算子

```java
// Transformations
DataStream<Event> events = source
    // map: 一对一
    .map(line -> parseEvent(line))

    // filter: 过滤
    .filter(e -> e.getUserId() != null)

    // flatMap: 一对多
    .flatMap((Event e, Collector<String> out) -> {
        out.collect(e.getAction());
        if (e.getAmount() != null) {
            out.collect("amount:" + e.getAmount());
        }
    })
    .returns(Types.STRING)

    // keyBy: 分组(返回KeyedStream)
    // process: 自定义处理(可访问状态和定时器)
    ;

KeyedStream<Event, String> keyed = events
    .keyBy(Event::getUserId);

// 窗口聚合
keyed
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new MyAggregateFunction())
    .sinkTo(kafkaSink);

// Connect: 连接两个流
DataStream<String> connected = stream1
    .connect(stream2)
    .map(new CoMapFunction<String, Integer, String>() {
        @Override public String map1(String value) { return "s1:" + value; }
        @Override public String map2(Integer value) { return "s2:" + value; }
    });

// Side Output: 侧路输出
OutputTag<Event> lateTag = new OutputTag<Event>("late-data"){};
SingleOutputStreamOperator<Event> mainStream = events
    .process(new ProcessFunction<Event, Event>() {
        @Override
        public void processElement(Event e, Context ctx, Collector<Event> out) {
            if (e.getTs() < 0) {
                ctx.output(lateTag, e);  // 侧路输出
            } else {
                out.collect(e);  // 主流
            }
        }
    });
DataStream<Event> lateStream = mainStream.getSideOutput(lateTag);
```

---

## 3. 窗口机制

### 3.1 窗口类型

```
Flink四大窗口:

  1. Tumbling Window (滚动窗口)
     |---W1---|---W2---|---W3---|
     不重叠，不遗漏，窗口固定大小

  2. Sliding Window (滑动窗口)
     |---W1-----|
        |---W2-----|
           |---W3-----|
     可重叠，窗口大小 > 滑动步长

  3. Session Window (会话窗口)
     |--W1--|  -gap-  |--W2--|
     按Session gap分组，无固定边界

  4. Global Window (全局窗口)
     所有数据一个窗口，需自定义Trigger
     一般不直接用
```

```java
// 滚动窗口 — 每5分钟统计一次
keyed
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .sum("amount");

// 滑动窗口 — 窗口10分钟，每2分钟滑动一次
keyed
    .window(SlidingEventTimeWindows.of(Time.minutes(10), Time.minutes(2)))
    .sum("amount");

// 会话窗口 — 10分钟无活动则关闭会话
keyed
    .window(EventTimeSessionWindows.withGap(Time.minutes(10)))
    .sum("amount");

// 窗口函数
keyed
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    // reduce: 增量聚合(性能好)
    .reduce((e1, e2) -> {
        e1.setAmount(e1.getAmount() + e2.getAmount());
        return e1;
    });

keyed
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    // process: 全量聚合(可访问窗口所有数据)
    .process(new ProcessWindowFunction<Event, Result, String, TimeWindow>() {
        @Override
        public void process(String key,
                          ProcessWindowFunction<Event, Result, String, TimeWindow>.Context ctx,
                          Iterable<Event> events,
                          Collector<Result> out) {
            long count = 0;
            double sum = 0;
            for (Event e : events) {
                count++;
                sum += e.getAmount();
            }
            out.collect(new Result(key, count, sum,
                ctx.window().getStart(), ctx.window().getEnd()));
        }
    });

// 增量+全量混合: 先aggregate预聚合，再process补窗口信息
keyed
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(
        new MyAggregateFunction(),   // 增量聚合
        new MyWindowFunction()        // 补充窗口信息
    );
```

---

## 4. 水位线Watermark

### 4.1 概念

```
Watermark(水位线) — 解决乱序数据问题

  问题: 网络延迟导致数据到达顺序≠事件发生顺序
    事件时间: 10:01 → 10:02 → 10:03 → 10:01(迟到的!)

  Watermark = 当前最大事件时间 - 允许延迟
    Watermark = MaxEventTime - MaxOutOfOrderness

  作用: 告诉系统"时间T之前的数据不会再来了"
    Watermark ≥ 窗口结束时间 → 窗口触发计算

  时间线:
  Event:  10:01  10:03  10:02  10:05  10:04(late)
  WM:     10:01  10:03  10:03  10:05  10:05
                       ↑
                  窗口[10:00, 10:05)在WM=10:05时触发

  ┌──────────────────────────────────────────────────┐
  │  Watermark策略选择:                               │
  │  1. 有序场景: Watermark = EventTime               │
  │  2. 乱序场景: Watermark = MaxEventTime - Delay    │
  │  3. 严格限制: Watermark = EventTime - Delay       │
  │  Delay取P99/P99.9的延迟                           │
  └──────────────────────────────────────────────────┘
```

### 4.2 代码实现

```java
// 水位线策略
WatermarkStrategy<Event> watermarkStrategy = WatermarkStrategy
    // 乱序等待3秒
    .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(3))
    // 从Event中提取事件时间
    .withTimestampAssigner((event, timestamp) -> event.getTs());

// 应用水位线
DataStream<Event> withWatermark = source
    .assignTimestampsAndWatermarks(watermarkStrategy);

// 空闲Source处理(防止无数据导致Watermark停滞)
WatermarkStrategy<Event> idleStrategy = WatermarkStrategy
    .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(3))
    .withTimestampAssigner((event, timestamp) -> event.getTs())
    .withIdleness(Duration.ofMinutes(1));  // 1分钟无数据标记空闲

// 多流Watermark: 取各流最小的Watermark
// 流1 WM=10:05, 流2 WM=10:03 → 合并后WM=10:03

// 迟到数据处理
OutputTag<Event> lateTag = new OutputTag<Event>("late"){};
events
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    // 允许迟到1分钟(窗口已关闭但仍可更新)
    .allowedLateness(Time.minutes(1))
    // 超过允许延迟 → 侧路输出
    .sideOutputLateData(lateTag)
    .sum("amount")
    .getSideOutput(lateTag)
    .sinkTo(lateDataSink);  // 迟到数据单独处理
```

---

## 5. 状态管理

### 5.1 状态类型

```
Flink状态分类:

  ┌──────────────────────────────────────────────────┐
  │  Keyed State (只能用于KeyedStream)                │
  │  ├── ValueState<T>      — 单值                    │
  │  ├── ListState<T>       — 列表                    │
  │  ├── MapState<K,V>      — Map                     │
  │  ├── ReducingState<T>   — 聚合(每次add自动reduce) │
  │  └── AggregatingState<IN,OUT> — 聚合(类型可不同)  │
  │                                                  │
  │  Operator State (非Keyed)                         │
  │  ├── ListState<T>       — 列表                    │
  │  └── BroadcastState    — 广播(规则下发)           │
  └──────────────────────────────────────────────────┘

  State Backend (状态后端):
    HashMapStateBackend — 内存(JVM Heap), 适合小状态
    EmbeddedRocksDBStateBackend — RocksDB(磁盘), 适合大状态
```

### 5.2 代码实现

```java
public class StatefulProcess extends KeyedProcessFunction<String, Event, Result> {

    // ValueState — 记录用户上次访问时间
    private ValueState<Long> lastVisitState;

    // MapState — 记录用户每个action的次数
    private MapState<String, Integer> actionCountState;

    @Override
    public void open(Configuration parameters) {
        ValueStateDescriptor<Long> lastDesc =
            new ValueStateDescriptor<>("lastVisit", Long.class);
        // 设置TTL: 24小时过期
        lastDesc.enableTimeToLive(
            StateTtlConfig.newBuilder(Time.hours(24))
                .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
                .setStateVisibility(
                    StateTtlConfig.StateVisibility.NeverReturnExpired)
                .build()
        );
        lastVisitState = getRuntimeContext().getState(lastDesc);

        actionCountState = getRuntimeContext().getMapState(
            new MapStateDescriptor<>("actionCount", String.class, Integer.class)
        );
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<Result> out)
            throws Exception {
        Long lastVisit = lastVisitState.value();
        long now = event.getTs();

        if (lastVisit != null) {
            long gap = now - lastVisit;
            // 间隔超过1小时 → 回归用户
            if (gap > 3600_000L) {
                out.collect(new Result(event.getUserId(), "returning_user", now));
            }
        }

        lastVisitState.update(now);

        // 更新action计数
        String action = event.getAction();
        int count = actionCountState.contains(action) ?
            actionCountState.get(action) : 0;
        actionCountState.put(action, count + 1);

        // 注册定时器 — 10秒后触发
        ctx.timerService().registerEventTimeTimer(now + 10_000L);
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Result> out)
            throws Exception {
        // 定时器回调
        int totalActions = 0;
        for (int cnt : actionCountState.values()) {
            totalActions += cnt;
        }
        out.collect(new Result(ctx.getCurrentKey(), "total:" + totalActions, timestamp));
    }
}
```

---

## 6. Checkpoint机制

### 6.1 分布式快照

```
Flink Checkpoint = Chandy-Lamport分布式快照算法

  核心思想: 在数据流中注入Barrier(屏障)，Barrier随数据流动
  Barrier到达各Operator时触发状态快照

  数据流:
  ┌─────┬─────┬─────┬─────┬─────┐
  │ D1  │ D2  │ B   │ D3  │ D4  │  B = Checkpoint Barrier
  └─────┴─────┴─────┴─────┴─────┘
                   ↓
  Operator收到Barrier → 对齐 → 保存状态 → 广播Barrier

  ┌──────────────────────────────────────────────────┐
  │  Barrier对齐(Exactly-Once):                      │
  │  多输入Operator收到一个输入的Barrier后           │
  │  暂停该输入的处理，等所有输入的Barrier都到达     │
  │  → 保存状态 → 继续处理                           │
  │                                                  │
  │  Barrier不对齐(At-Least-Once):                   │
  │  不等待，直接保存状态，可能多算                   │
  │  → 性能更好但有重复                               │
  └──────────────────────────────────────────────────┘

  Checkpoint流程:
  1. JobManager定期向Source注入Barrier
  2. Barrier随数据流向下游传播
  3. 每个Operator收到Barrier → 对齐 → 存状态
  4. 所有Operator都完成 → JobManager确认 → Checkpoint成功
  5. 故障时从最近成功的Checkpoint恢复
```

### 6.2 配置

```java
// Checkpoint配置
env.enableCheckpointing(60_000);  // 60秒间隔

CheckpointConfig config = env.getCheckpointConfig();

// 模式: EXACTLY_ONCE(默认) 或 AT_LEAST_ONCE
config.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);

// 超时: Checkpoint超过2分钟未完成则放弃
config.setCheckpointTimeout(120_000);

// 两次Checkpoint间最小间隔: 30秒(防止堆积)
config.setMinPauseBetweenCheckpoints(30_000);

// 最大并发Checkpoint数
config.setMaxConcurrentCheckpoints(1);

// 保留外部Checkpoint(取消任务不删除)
config.setExternalizedCheckpointCleanup(
    CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);

// 容忍Checkpoint失败次数
config.setTolerableCheckpointFailureNumber(3);

// 状态后端: RocksDB(大状态)
env.setStateBackend(new EmbeddedRocksDBStateBackend());

// 增量Checkpoint(只传变化部分)
config.enableUnalignedCheckpoints(true);  // 非对齐Checkpoint(更快)
```

---

## 7. CEP复杂事件处理

```java
// CEP: 复杂事件处理 — 检测事件序列模式
// 场景: 5秒内连续3次登录失败 → 触发告警

public class LoginAlertCEP {

    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env =
            StreamExecutionEnvironment.getExecutionEnvironment();

        DataStream<LoginEvent> logins = env
            .fromSource(kafkaSource, WatermarkStrategy.forBoundedOutOfOrderness(
                Duration.ofSeconds(5)), "logins")
            .keyBy(LoginEvent::getUserId);

        // 定义模式: 3次失败登录，5秒内
        Pattern<LoginEvent, LoginEvent> pattern = Pattern
            .<LoginEvent>begin("first_fail")
            .where(e -> "fail".equals(e.getType()))
            .timesOrMore(3)
            .consecutive()  // 连续失败(中间不能有成功)
            .within(Time.seconds(5));

        // 应用模式
        PatternStream<LoginEvent> patternStream = CEP.pattern(logins, pattern);

        // 处理匹配结果
        DataStream<Alert> alerts = patternStream.process(
            new PatternProcessFunction<LoginEvent, Alert>() {
                @Override
                public void processMatch(
                        Map<String, List<LoginEvent>> match,
                        Context ctx,
                        Collector<Alert> out) {
                    List<LoginEvent> fails = match.get("first_fail");
                    if (fails.size() >= 3) {
                        LoginEvent first = fails.get(0);
                        out.collect(new Alert(
                            first.getUserId(),
                            "连续登录失败告警",
                            fails.size()
                        ));
                    }
                }
            });

        // 更复杂模式示例:
        Pattern<Transaction, ?> fraudPattern = Pattern
            .<Transaction>begin("normal")
            .where(t -> t.getAmount() < 100)
            .times(3)
            .followedBy("large")  // 之后
            .where(t -> t.getAmount() > 10000)
            .within(Time.minutes(10));
        // 10分钟内: 3笔小额消费后一笔大额 → 可能盗刷

        alerts.sinkTo(alertSink);
        env.execute("Login Alert CEP");
    }
}
```

```
CEP模式量词:
  times(n)       — 恰好n次
  timesOrMore(n) — 至少n次
  times(n, m)    — n到m次
  oneOrMore()    — 1次或多次
  optional()     — 0次或1次

CEP模式连续性:
  next()         — 严格连续(中间无其他事件)
  followedBy()   — 松散连续(中间可有其他事件)
  notNext()      — 严格不连续
  notFollowedBy()— 松散不连续

CEP时间约束:
  within(Time)   — 整个模式的时间窗口
```

---

## 8. 面试题速查

**Q1: Flink的Watermark机制？**

```
Watermark = 当前最大事件时间 - 允许乱序延迟
作用: 衡量事件时间进展，决定窗口何时触发
Watermark ≥ 窗口结束时间 → 触发窗口计算
允许迟到(allowedLateness): 窗口关闭后仍接受迟到数据并更新结果
```

**Q2: Flink的Checkpoint原理？**

```
基于Chandy-Lamport分布式快照:
1. JobManager注入Barrier到Source
2. Barrier随数据流向下游
3. Operator收到Barrier → 对齐 → 存状态 → 广播Barrier
4. 全部完成 → Checkpoint成功
故障时从最近Checkpoint恢复，保证Exactly-Once
```

**Q3: Flink的窗口有哪些？**

```
Tumbling(滚动): 不重叠，固定大小
Sliding(滑动): 可重叠，大小>步长
Session(会话): 按gap分组，动态边界
Global(全局): 需自定义Trigger
```

**Q4: Keyed State有哪些类型？**

```
ValueState: 单值
ListState: 列表
MapState: 键值对
ReducingState: 自动聚合
AggregatingState: 聚合(输入输出类型可不同)
State Backend: HashMap(内存) / RocksDB(磁盘)
```

**Q5: Flink如何保证Exactly-Once？**

```
1. Checkpoint: 状态快照(Barrier对齐)
2. Source: 可重放(Kafka offset存入Checkpoint)
3. Sink: 两阶段提交(2PC) — 先预写，Checkpoint成功后提交
端到端Exactly-Once = Source可重放 + Checkpoint + Sink两阶段提交
```

---

*最后更新：2026-07-13*

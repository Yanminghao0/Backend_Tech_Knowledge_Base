# Apache Pulsar核心机制

> 计算存储分离的新一代消息队列，多租户原生支持，统一消息与流处理的云原生平台

---

## 📋 目录

1. [Pulsar概述](#1-pulsar概述)
2. [架构设计](#2-架构设计)
3. [核心特性](#3-核心特性)
4. [消息模型与订阅模式](#4-消息模型与订阅模式)
5. [Schema Registry](#5-schema-registry)
6. [Pulsar IO连接器](#6-pulsar-io连接器)
7. [Pulsar Functions流处理](#7-pulsar-functions流处理)
8. [分层存储](#8-分层存储)
9. [生产环境部署](#9-生产环境部署)
10. [Pulsar vs Kafka](#10-pulsar-vs-kafka)
11. [面试要点](#11-面试要点)

---

## 1. Pulsar概述

```
Apache Pulsar = Yahoo开源的分布式消息+流处理平台

核心定位：
  - 统一消息队列+流处理
  - 计算存储分离架构
  - 多租户原生支持
  - 跨地域复制

应用场景：
  - 消息队列（队列模式+流模式）
  - 事件流处理
  - 跨地域数据同步
```

Pulsar最初由Yahoo于2016年开源，2018年成为Apache顶级项目。其设计目标是为大规模、多租户场景提供统一的消息传递和流处理能力。与传统消息队列不同，Pulsar从设计之初就将计算层（Broker）与存储层（BookKeeper）分离，使得两层可以独立扩展、独立运维，这为云原生环境下的弹性伸缩奠定了架构基础。

Pulsar的统一消息模型意味着它可以同时支持队列消费（如RabbitMQ）和流式消费（如Kafka），开发者无需在不同中间件之间做选择。

---

## 2. 架构设计

### 计算存储分离

```
┌─────────────────────────────────────────┐
│           Pulsar Proxy / Client          │
├─────────────────────────────────────────┤
│           Broker层（计算）                │
│  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │Broker│  │Broker│  │Broker│  无状态   │
│  │  1   │  │  2   │  │  3   │  可扩缩   │
│  └──┬───┘  └──┬───┘  └──┬───┘         │
├─────┼─────────┼─────────┼──────────────┤
│     │  BookKeeper层（存储）  │           │
│  ┌──┴──┐  ┌───┴─┐  ┌────┴┐            │
│  │Bookie│  │Bookie│  │Bookie│  持久化    │
│  │  1   │  │  2   │  │  3   │  可扩缩    │
│  └─────┘  └─────┘  └─────┘            │
├─────────────────────────────────────────┤
│           ZooKeeper（元数据）             │
└─────────────────────────────────────────┘

优势：
  - Broker无状态 → 水平扩展无需数据迁移
  - Bookie独立扩缩 → 存储按需扩容
  - 故障恢复快 → Broker重启后从Bookie加载
```

### Producer（生产者）

```
Producer工作流程：
  1. 连接Broker → 获取Topic的元数据
  2. ZooKeeper查找Topic所属的Broker
  3. 发送消息到Broker → Broker写入BookKeeper
  4. BookKeeper多数Bookie确认后 → 返回ACK
  5. Producer支持同步/异步发送

发送模式：
  - 同步发送：等待持久化确认，可靠性高
  - 异步发送：批量发送，吞吐高
  - 跨地域发送：写入本地集群后自动复制

消息路由策略：
  - SinglePartition：固定分区
  - RoundRobinPartition：轮询分区
  - CustomPartition：自定义分区（按Key哈希）

Java示例：
  Producer<byte[]> producer = client.newProducer()
      .topic("persistent://tenant/ns/topic")
      .enableBatching(true)
      .batchingMaxMessages(1000)
      .batchingMaxPublishDelay(10, TimeUnit.MILLISECONDS)
      .compressionType(CompressionType.LZ4)
      .sendTimeout(10, TimeUnit.SECONDS)
      .create();
  producer.send("Hello Pulsar".getBytes());
```

### Broker（计算层）

```
Broker职责：
  - 接收Producer消息 → 写入BookKeeper
  - 读取BookKeeper → 投递给Consumer
  - 管理Topic元数据
  - 处理订阅和消费确认
  - 消息分发和负载均衡

Broker无状态特性：
  - 不存储消息数据 → 数据全在BookKeeper
  - Topic的owner Broker可动态迁移
  - Broker宕机 → Topic由其他Broker接管
  - 扩容秒级生效，无需数据迁移

Broker负载均衡：
  - 基于Bundle的负载均衡（Namespace Bundle）
  - 每个Bundle包含一部分Topic
  - Broker负载不均时，Bundle可迁移到其他Broker
  - 负载指标：消息速率、连接数、资源使用率
```

### BookKeeper（存储层）

```
BookKeeper = 分布式WAL（Write-Ahead Log）日志存储

核心概念：
  - Ledger：一次性写入的日志序列（不可修改）
  - Bookie：BookKeeper存储节点
  - Ensemble：写入的Bookie集合（通常3个）
  - Write Quorum (Qw)：每条消息写入的Bookie数量
  - Ack Quorum (Qa)：确认写入成功的最小Bookie数量

写入流程：
  Producer → Broker → 选择Ensemble(Qw=3) → 写入3个Bookie
  当Qa=2时，2个Bookie确认即返回ACK → 保证持久性

  示例配置：Ensemble=3, Qw=3, Qa=2
  → 容忍1个Bookie故障，写入仍然成功

读取流程：
  Consumer → Broker → 从任意Bookie读取 → 投递给Consumer
  读取可从多个Bookie并行 → 提升读取吞吐

Ledger特性：
  - 只追加（Append-Only），不可修改
  - 关闭后不可再写入
  - Ledger ID全局唯一
  - 旧Ledger可被压缩/归档（分层存储）
```

### ZooKeeper（元数据协调）

```
ZooKeeper存储的元数据：
  - Topic元数据：所属Bundle、Owner Broker
  - 订阅信息：订阅模式、消费位置（Cursor）
  - BookKeeper Ledger信息
  - 集群配置：Broker列表、命名空间策略
  - 跨地域复制配置

高可用：
  - ZooKeeper集群通常3或5节点
  - ZooKeeper故障 → Broker可继续服务已有连接
  - 新Topic创建/订阅需等ZooKeeper恢复

注意：Pulsar 2.x+支持将元数据存储迁移到更轻量的方案
```

---

## 3. 核心特性

### 多租户

```
租户(Tenant) → 偢名空间(Namespace) → 主题(Topic)

层级隔离：
  - 租户级：配额、认证、授权
  - 命名空间级：策略、复制、保留
  - 主题级：分区、订阅模式

示例：
  tenant: company-a
    namespace: production
      topic: persistent://company-a/production/orders
    namespace: staging
      topic: persistent://company-a/staging/orders
```

多租户是Pulsar的核心设计理念。每个租户可以配置独立的认证授权策略、消息配额、存储限制和TTL。命名空间级别可以设置消息保留策略、延迟投递、死信队列等。这种原生多租户支持使得Pulsar非常适合SaaS平台和大规模企业级应用。

### 跨地域复制

```java
// 跨地域复制配置
admin.namespaces().setNamespaceReplicationClusters(
    "tenant/namespace",
    Set.of("us-east", "us-west", "eu-central")
);
// 消息写入任一集群 → 自动复制到其他集群
```

跨地域复制（Geo-Replication）是Pulsar的内置特性，无需额外的MirrorMaker工具。消息写入任一集群后会异步复制到其他配置的集群。支持全连接（all-to-all）和星型拓扑。每个集群有独立的Producer和Consumer，复制是透明的。

---

## 4. 消息模型与订阅模式

### 订阅模式详解

```
1. Exclusive：独占（一个消费者）
   - 只有一个Consumer消费Topic
   - 适合顺序处理场景

2. Shared：共享（多个消费者轮询）
   - 消息轮询分发给多个Consumer
   - 消费者可动态加入/退出
   - 消息不保证顺序
   - 适合任务分发场景

3. Failover：故障转移（主备）
   - 一个主Consumer消费，其他为备
   - 主Consumer宕机 → 备Consumer接管
   - 适合高可用消费场景

4. Key_Shared：按Key有序（同一Key到同一消费者）
   - 同一Key的消息始终路由到同一Consumer
   - 兼顾并行消费和Key内有序
   - 适合需要分区有序但又要并行的场景
```

### 消息确认机制

```java
// Pulsar支持单条确认和累积确认
Consumer<byte[]> consumer = client.newConsumer()
    .topic("my-topic")
    .subscriptionName("my-sub")
    .subscriptionType(SubscriptionType.Shared)
    .ackTimeout(30, TimeUnit.SECONDS)
    .negativeAckRedeliveryDelay(1, TimeUnit.SECONDS)
    .subscribe();

// 单条确认（精确控制）
Message<byte[]> msg = consumer.receive();
consumer.acknowledge(msg);       // 确认单条消息

// 累积确认（确认该消息之前的所有消息）
consumer.acknowledgeCumulative(msg);

// 否定确认（消息处理失败，重新投递）
consumer.negativeAcknowledge(msg);

// 重试死信队列
// 超过最大重试次数的消息自动进入死信队列
```

### 消息回溯

```
Pulsar支持消息回溯（Message Replay）：
  - 按时间戳回溯：回到指定时间点重新消费
  - 按位置回溯：回到指定Message ID重新消费

  // 回溯到1小时前
  consumer.seek(Time.from(1, TimeUnit.HOURS));

  // 回溯到指定Message ID
  consumer.seek(MessageId.earliest);

原因：Pulsar的消息存储在BookKeeper中，
      即使Consumer已确认，消息不会立即删除
      （根据保留策略保留一段时间）
```

---

## 5. Schema Registry

```
Schema Registry = 内置的Schema注册中心

Pulsar内置Schema Registry，支持结构化消息：

支持的Schema类型：
  - Primitive：String、Byte、Int、Long、Float、Double
  - Structured：Avro、JSON、Protobuf
  - 自定义：实现Schema接口

优势：
  - Producer和Consumer的Schema自动校验
  - Schema演进（兼容性检查）
  - 无需额外部署Schema Registry服务（Kafka需要Confluent Schema Registry）
```

```java
// Avro Schema示例
Schema<User> schema = Schema.AVRO(User.class);

Producer<User> producer = client.newProducer(schema)
    .topic("user-events")
    .create();
producer.send(new User("Alice", 30));

Consumer<User> consumer = client.newConsumer(schema)
    .topic("user-events")
    .subscriptionName("user-sub")
    .subscribe();

// Schema兼容性策略：
// - BACKWARD：新Schema可以读旧数据（添加可选字段）
// - FORWARD：旧Schema可以读新数据（删除可选字段）
// - FULL：双向兼容
admin.topic().setSchemaCompatibility("topic",
    SchemaCompatibilityStrategy.BACKWARD);
```

---

## 6. Pulsar IO连接器

```
Pulsar IO = 内置的数据集成连接器框架

无需额外部署Kafka Connect，Pulsar IO直接内置连接器：

Source连接器（外部 → Pulsar）：
  - Kafka Source：从Kafka读取数据写入Pulsar
  - Debezium MySQL：CDC变更数据捕获
  - MongoDB Source：实时同步MongoDB变更
  - Kinesis Source：AWS Kinesis数据流入
  - File Source：监听文件变更

Sink连接器（Pulsar → 外部）：
  - Elasticsearch Sink：写入ES用于搜索
  - JDBC Sink：写入关系型数据库
  - MongoDB Sink：写入MongoDB
  - HDFS Sink：写入Hadoop
  - Redis Sink：写入Redis缓存
```

```bash
# 部署一个MySQL CDC Source连接器
pulsar-admin source create \
  --name mysql-cdc-source \
  --source-type debezium-mysql \
  --tenant public \
  --namespace default \
  --destination-topic-name mysql-events \
  --source-config '{"hostname":"mysql.host","port":"3306","user":"root","password":"***","database":"mydb"}'

# 部署一个Elasticsearch Sink连接器
pulsar-admin sink create \
  --name es-sink \
  --sink-type elastic_search \
  --tenant public \
  --namespace default \
  --inputs mysql-events \
  --sink-config '{"elasticSearchUrl":"http://es:9200","indexName":"mysql_index"}'
```

---

## 7. Pulsar Functions流处理

```
Pulsar Functions = 轻量级流处理引擎

无需部署Flink/Spark，直接在Pulsar上运行计算函数：

特点：
  - 轻量：单个函数就是一个计算单元
  - 部署简单：无需独立集群
  - 状态管理：支持有状态计算
  - 多语言：Java、Python、Go
  - At-least-once语义

应用场景：
  - 简单ETL转换
  - 实时过滤和路由
  - 聚合统计
  - 异常检测
```

```java
// Java Function示例：单词计数
public class WordCountFunction implements Function<String, Void> {
    @Override
    public Void process(String input, Context context) {
        String[] words = input.split("\\s+");
        for (String word : words) {
            // 有状态计数
            long count = context.incrCounter(word, 1);
            context.getLogger().info("Word: " + word + " count: " + count);
        }
        return null;
    }
}
```

```bash
# 部署Function
pulsar-admin functions create \
  --jar wordcount.jar \
  --classname WordCountFunction \
  --name word-count \
  --inputs sentences \
  --output word-counts \
  --parallelism 4
```

---

## 8. 分层存储

```
分层存储（Tiered Storage）= 热数据Bookie + 冷数据对象存储

┌──────────────────────────────────────┐
│  热数据层：BookKeeper（SSD）           │
│  - 最近写入的数据                     │
│  - 高频读取                           │
│  - 低延迟                             │
├──────────────────────────────────────┤
│  冷数据层：S3/Azure Blob/GCS          │
│  - 历史数据                           │
│  - 低频读取                           │
│  - 低成本                             │
└──────────────────────────────────────┘

工作原理：
  1. 消息先写入BookKeeper（热层）
  2. Ledger关闭后，异步上传到对象存储（冷层）
  3. 读取历史数据时，从对象存储拉取
  4. Bookie上的旧Ledger可被清理，释放空间

优势：
  - 存储成本降低10-100倍（S3 vs SSD）
  - BookKeeper容量不再限制数据保留时间
  - 历史数据可长期保留，支持消息回溯
```

```yaml
# 分层存储配置（broker.conf）
managedLedgerDataBacklog=true
s3ManagedLedgerOffloadRegion=us-east-1
s3ManagedLedgerOffloadBucket=pulsar-tiered-storage
managedLedgerOffloadDeletionLagMs=86400000  # 24小时后删除Bookie上的Ledger
managedLedgerOffloadAutoTriggerSizeThresholdBytes=10737418240  # 10GB触发offload
```

---

## 9. 生产环境部署

### 集群部署架构

```
生产环境推荐架构：

  ┌──────────────────────────────────────────────────┐
  │  Pulsar Proxy层（2+ 节点，负载均衡+TLS终止）        │
  │  - 客户端通过Proxy访问，不直连Broker               │
  │  - 支持TLS加密、认证、跨集群路由                   │
  ├──────────────────────────────────────────────────┤
  │  Broker层（3+ 节点，水平扩展）                     │
  │  - 每个Broker承担部分Topic（Bundle分配）            │
  │  - 建议每Broker处理数千Topic                      │
  ├──────────────────────────────────────────────────┤
  │  BookKeeper层（5+ 节点，数据持久化）               │
  │  - 每个Bookie使用独立磁盘（journal + storage）     │
  │  - Journal用NVMe SSD，Storage用SATA SSD/HDD       │
  │  - 建议Ensemble=3, WriteQuorum=2, AckQuorum=2     │
  ├──────────────────────────────────────────────────┤
  │  ZooKeeper层（3或5 节点，元数据一致性）            │
  │  - 独立部署，不与Broker混部                       │
  │  - SSD存储，至少4GB内存                          │
  ├──────────────────────────────────────────────────┤
  │  监控层：Prometheus + Grafana                     │
  │  - Broker/Bookie/ZooKeeper指标                   │
  │  - 消息积压、延迟、吞吐告警                       │
  └──────────────────────────────────────────────────┘
```

### 关键配置

```properties
# broker.conf 关键参数
brokerDeleteInactiveTopicsEnabled=false
maxConcurrentLookupRequest=50000
maxConcurrentTopicLoadRequest=5000
brokerPublisherThrottlingTickTimeMillis=10
brokerPublisherThrottlingMaxMessageRate=10000

# bookkeeper.conf 关键参数
journalDirectory=/data/journal
ledgerDirectories=/data/ledger
journalSyncData=true
journalFlushWhenQueueEmpty=true
numAddWorkerThreads=8
numReadWorkerThreads=8

# 容量规划
# 每Bookie建议存储：1-10TB
# Bookie数量 = 总数据量 / 单Bookie容量 × 副本数
# 示例：10TB数据，3副本 → 30TB存储 → 3台10TB Bookie（或6台5TB）
```

### 运维要点

```
1. 监控关键指标：
   - Broker：消息入队/出队速率、连接数、Backlog积压
   - Bookie：磁盘使用率、读写延迟、Journal写入速率
   - ZooKeeper：请求延迟、Watch数量

2. 扩缩容：
   - Broker扩容：启动新Broker → Bundle自动迁移
   - Bookie扩容：启动新Bookie → 数据自动rebalance
   - 无需停机，在线操作

3. 故障处理：
   - Broker宕机 → Topic自动迁移到其他Broker（秒级）
   - Bookie宕机 → 数据从其他Bookie恢复（Ledger恢复）
   - ZooKeeper宕机 → 已有连接不受影响，新连接等待恢复

4. 安全配置：
   - 启用TLS加密（Broker-Bookie、Broker-Client）
   - 启用认证（JWT、Kerberos、OAuth2）
   - 授权：租户级、命名空间级ACL
```

---

## 10. Pulsar vs Kafka

| 维度 | Pulsar | Kafka |
|------|--------|-------|
| 架构 | 计算存储分离 | Broker存储一体 |
| 扩展 | Broker无状态，秒级扩缩 | 需数据迁移 |
| 多租户 | 原生支持 | 弱 |
| 消息模型 | 队列+流 | 流 |
| 订阅模式 | 4种 | Consumer Group |
| 消息回溯 | 按时间/位置 | 按Offset |
| 跨地域复制 | 内置 | MirrorMaker |
| 延迟消息 | 内置 | 需自实现 |
| 生态 | 成长中 | 成熟 |
| 存储成本 | 分层存储（S3冷数据） | 全量Broker磁盘 |
| 消息确认 | 单条+累积 | Offset提交 |
| Schema管理 | 内置Registry | 需Confluent |
| 流处理 | Pulsar Functions | Kafka Streams |

### 选型建议

```
选Kafka：生态成熟，大数据场景，团队熟悉
选Pulsar：多租户SaaS，跨地域，计算存储分离需求

详细决策：
  选Kafka：
  - 大数据生态（Spark/Flink/数据湖深度集成）
  - 团队已有Kafka运维经验
  - 单租户场景，不需要复杂隔离
  - 流式消费为主

  选Pulsar：
  - 多租户SaaS平台
  - 需要队列+流混合消费模式
  - 跨地域复制为核心需求
  - 希望弹性扩缩Broker不影响存储
  - 长期数据保留（分层存储降本）
  - 需要延迟消息、Schema Registry等内置功能
```

---

## 11. 面试要点

### Q1: Pulsar计算存储分离的优势？

```
1. Broker无状态 → 扩缩容无需数据迁移（秒级）
2. 存储独立扩缩 → 按需扩展存储不影响计算
3. 故障恢复快 → Broker重启不丢数据（在Bookie）
4. 灵活部署 → Broker和Bookie可独立配置硬件

对比Kafka：
  Kafka Broker重启需同步副本数据，恢复慢
  Pulsar Broker重启从Bookie加载元数据即可
```

### Q2: Pulsar的多租户怎么实现？

```
三层隔离：
  1. 租户级：认证授权、配额限制
  2. 命名空间级：策略隔离（保留/复制/TTL）
  3. 主题级：分区和订阅模式独立

资源隔离：
  - Broker资源配额（CPU/内存/带宽）
  - Bookie存储配额
  - Topic级限流
```

### Q3: Pulsar的四种订阅模式分别适用什么场景？

```
Exclusive：单消费者顺序处理，适合严格顺序场景
Shared：多消费者并行处理，适合高吞吐任务分发
Failover：主备消费，适合高可用需求
Key_Shared：按Key分区+并行消费，兼顾顺序和吞吐

对比Kafka：
  Kafka只有Consumer Group模式（类似Shared/Key_Shared）
  Pulsar更灵活，可以同一Topic多订阅模式并存
```

### Q4: BookKeeper的写入确认机制？

```
BookKeeper使用Quorum写入：

  Ensemble = 3 (3个Bookie组成写入集合)
  Write Quorum (Qw) = 3 (写入3个Bookie)
  Ack Quorum (Qa) = 2 (2个确认即成功)

  容忍故障数 = Qw - Qa = 1
  → 1个Bookie故障不影响写入

  持久性保证：
  - Qa=2 → 至少2份副本，保证数据不丢
  - 读取可从任意Bookie → 高可用读取

  对比Kafka：
  - Kafka: 副本同步是异步的（ISR机制）
  - BookKeeper: 写入时同步多副本，更强一致性
```

### Q5: Pulsar分层存储如何降低成本？

```
传统方案（Kafka）：
  所有数据存储在Broker磁盘 → 存储成本高
  保留7天日志可能需要数TB SSD

Pulsar分层存储：
  热数据 → BookKeeper（SSD，毫秒级访问）
  冷数据 → S3/GCS（对象存储，低成本）
  成本降低10-100倍

  数据生命周期：
  1. 写入BookKeeper（热层）
  2. Ledger关闭后异步上传S3
  3. BookKeeper上旧数据可清理
  4. 消费者读历史数据 → 从S3拉取
```

---

## 📚 相关阅读

- [01_Kafka核心机制详解](./01_Kafka核心机制详解.md)
- [03_RocketMQ核心机制详解](./03_RocketMQ核心机制详解.md)
- [04_消息队列选型对比](./04_消息队列选型对比.md)

# Apache Pulsar核心机制

> 计算存储分离的新一代消息队列，多租户原生支持

---

## 📋 目录

1. [Pulsar概述](#1-pulsar概述)
2. [架构设计](#2-架构设计)
3. [核心特性](#3-核心特性)
4. [Pulsar vs Kafka](#4-pulsar-vs-kafka)
5. [面试要点](#5-面试要点)

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

---

## 3. 核心特性

### 多租户

```
租户(Tenant) → 命名空间(Namespace) → 主题(Topic)

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

### 订阅模式

```
1. Exclusive：独占（一个消费者）
2. Shared：共享（多个消费者轮询）
3. Failover：故障转移（主备）
4. Key_Shared：按Key有序（同一Key到同一消费者）
```

### 跨地域复制

```java
// 跨地域复制配置
admin.namespaces().setNamespaceReplicationClusters(
    "tenant/namespace",
    Set.of("us-east", "us-west", "eu-central")
);
// 消息写入任一集群 → 自动复制到其他集群
```

---

## 4. Pulsar vs Kafka

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

### 选型建议

```
选Kafka：生态成熟，大数据场景，团队熟悉
选Pulsar：多租户SaaS，跨地域，计算存储分离需求
```

---

## 5. 面试要点

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

---

## 📚 相关阅读

- [01_Kafka核心机制详解](./01_Kafka核心机制详解.md)
- [03_RocketMQ核心机制详解](./03_RocketMQ核心机制详解.md)
- [04_消息队列选型对比](./04_消息队列选型对比.md)

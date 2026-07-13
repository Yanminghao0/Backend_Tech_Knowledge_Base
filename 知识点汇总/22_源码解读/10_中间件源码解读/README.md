# 中间件源码解读

> 消息队列、搜索引擎、缓存框架核心源码解析

---

## 📋 文档列表

### 消息队列（3篇）

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 17.1_RocketMQ源码解析.md | NameServer/Broker/Producer/Consumer、顺序消息、事务消息 | ⭐⭐⭐⭐⭐ | 📄 待补充 |
| 17.2_Kafka源码解析.md | 分区副本、ISR机制、消费者组Rebalance、零拷贝 | ⭐⭐⭐⭐⭐ | 📄 待补充 |
| 17.3_RabbitMQ源码解析.md | AMQP协议、Exchange路由、消息确认、镜像队列 | ⭐⭐⭐ | 📄 待补充 |

### 搜索引擎（2篇）

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 17.4_Elasticsearch源码解析.md | 倒排索引、分片路由、Segment合并、集群发现 | ⭐⭐⭐⭐ | 📄 待补充 |
| 17.5_Lucene源码解析.md | Segment结构、FST、DocValues、查询打分 | ⭐⭐⭐ | 📄 待补充 |

### 缓存框架（3篇）

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 17.6_Caffeine源码解析.md | W-TinyLFU算法、异步刷新、过期策略 | ⭐⭐⭐⭐ | 📄 待补充 |
| 17.7_Guava_Cache源码解析.md | LRU实现、LoadingCache、自动加载 | ⭐⭐⭐ | 📄 待补充 |
| 17.8_Ehcache源码解析.md | 多级缓存、持久化、集群同步 | ⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **理解MQ存储模型**：CommitLog、ConsumeQueue、分区日志
2. **掌握ES核心原理**：倒排索引、分片分配、写入流程（refresh/flush/merge）
3. **理解缓存淘汰算法**：LRU vs LFU vs W-TinyLFU

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- RocketMQ如何保证消息不丢？事务消息原理？
- Kafka高吞吐的原因？零拷贝？顺序写？
- Kafka的Rebalance过程？消费者组协调？
- ES的倒排索引原理？写入流程？

⭐⭐⭐⭐ 高频：
- Caffeine的W-TinyLFU算法？
- RocketMQ vs Kafka选型？
- ES的refresh和flush区别？
```

---

*最后更新：2026-07-13*

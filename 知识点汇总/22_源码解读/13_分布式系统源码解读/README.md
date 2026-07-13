# 分布式系统源码解读

> 分布式协调服务核心源码解析：Zookeeper、Etcd、Consul

---

## 📋 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 20.1_Zookeeper源码解析.md | ZAB协议、Leader选举、Watcher机制、数据树 | ⭐⭐⭐⭐ | 📄 待补充 |
| 20.2_Etcd源码解析.md | Raft协议实现、MVCC存储、Lease租约、Watch | ⭐⭐⭐⭐ | 📄 待补充 |
| 20.3_Consul源码解析.md | Gossip协议、Raft、服务注册、健康检查 | ⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **理解ZAB协议**：Zookeeper原子广播、崩溃恢复、Leader选举流程
2. **掌握Raft实现**：Etcd的Raft日志复制、Term机制、Split Brain处理
3. **理解Gossip协议**：Consul的成员管理、故障检测、最终一致性

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐ 高频：
- ZAB协议和Raft的区别？
- Zookeeper的Watcher机制？为什么是一次性的？
- Etcd为什么选Raft而不是ZAB？
- Zookeeper如何实现分布式锁？羊群效应？
- CAP理论在ZK/Etcd中的体现？
```

---

## 📊 三者对比

| 维度 | Zookeeper | Etcd | Consul |
|------|-----------|------|--------|
| 一致性协议 | ZAB | Raft | Raft |
| 数据模型 | 树形节点 | KV | KV + 服务 |
| 语言 | Java | Go | Go |
| 典型用途 | 配置/锁/注册中心 | K8s配置存储 | 服务发现/网格 |
| Watch | 一次性 | 持续 | 持续 |

---

*最后更新：2026-07-13*

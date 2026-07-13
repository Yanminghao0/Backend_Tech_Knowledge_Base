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

1. **理解ZAB协议**：Zookeeper原子广播（Atomic Broadcast）、崩溃恢复、Leader选举流程（FastLeaderElection）、ZXID（epoch+counter）的设计
2. **掌握Raft实现**：Etcd的Raft日志复制、Term机制、Split Brain处理、Leader选举（随机超时）、日志压缩（Snapshot）
3. **理解Gossip协议**：Consul的成员管理（SWIM算法）、故障检测（间接探测）、最终一致性、LAN/WAN两种Gossip池
4. **对比三种一致性协议**：ZAB vs Raft vs Gossip的适用场景与权衡

---

## 📊 ZAB vs Raft 对比表

| 维度 | ZAB (Zookeeper) | Raft (Etcd/Consul) |
|------|-----------------|---------------------|
| **选举** | 选举优先看ZXID(数据新) | 选举优先看Term+Index |
| **Leader唯一性** | 选举周期内Leader唯一 | 同一Term内Leader唯一 |
| **日志** | 条带式(zxid有序) | 日志条目按Index有序 |
| **一致性** | 顺序一致性(Linearizable) | Linearizable(强一致) |
| **日志复制** | Leader推(push)给Follower | Leader等Follower拉(pull) |
| **恢复** | 崩溃恢复选新Leader后同步 | 日志匹配+AppendEntries |
| **成员变更** | 不支持动态变更 | 支持Joint Consensus |
| **性能** | 写吞吐高(批量Pipeline) | 写延迟低(串行确认) |
| **实现复杂度** | 高(恢复流程复杂) | 中(流程清晰易理解) |
| **脑裂处理** | 过半机制 | 过半机制 |

### 三者适用场景对比

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 分布式锁(强一致) | Zookeeper | 临时顺序节点，Watch羊群可优化 |
| 配置中心 | Etcd | KV模型轻量，Watch持续推送，gRPC高性能 |
| 服务发现 | Consul | 健康检查内置，Gossip去中心化，多DC支持 |
| K8s存储 | Etcd | K8s原生集成，Raft稳定，Watch机制 |
| 选主 | Etcd/ZK | Lease/TTL + 临时节点，比自研可靠 |
| 大规模集群成员管理 | Consul | Gossip最终一致性，O(logN)传播 |

---

## 📐 核心原理图

### Zookeeper Watcher 机制

```
┌──────────── Client ────────────┐         ┌──────── ZK Server ────────┐
│                                │         │                           │
│  ZooKeeper zk = new ...        │         │   DataTree                │
│                                │         │   ┌──────────────────┐    │
│  zk.getData("/config",         │──①─────│   │ /config = "v1"   │    │
│    new Watcher() {             │  注册    │   │ WatchManager:    │    │
│      @Override                 │  Watch  │   │  /config→[client1]│   │
│      void process(WatchedEvent │         │   └──────────────────┘    │
│        e) { ... }              │         │                           │
│    });                         │         │   ② 数据变更触发           │
│                                │         │   /config = "v2"          │
│  // Watcher是一次性的！         │         │   ③ 通知所有Watcher       │
│  // 触发后需重新注册            │←③─────│   → WatchedEvent           │
│                                │  通知    │   ④ 清除该路径Watcher      │
│  // 3.6+ 支持持续Watch         │         │   (addWatch with mode)    │
│  // AddWatchMode.PERSISTENT    │         │                           │
│                                │         │                           │
└────────────────────────────────┘         └───────────────────────────┘

⚠ 一次性Watcher的问题：
  事件丢失 — Watch触发和重新注册之间如果有变更，Client感知不到
  解决方案(3.6+): Persistent Watch / Persistent Recursive Watch
```

### Etcd MVCC 原理

```
┌─────────────────── Etcd MVCC Storage ──────────────────────┐
│                                                            │
│   BoltDB (持久化, B+Tree)                                  │
│   ┌──────────────────────────────────────────┐            │
│   │ Key(修订版本号) │ Value(实际key-value)     │            │
│   ├──────────────────────────────────────────┤            │
│   │ rev=5          │ key="/a", val="x"        │ ← 历史版本 │
│   │ rev=8          │ key="/a", val="y"        │ ← 当前版本 │
│   │ rev=8          │ key="/b", val="1"        │            │
│   └──────────────────────────────────────────┘            │
│                                                            │
│   Key Index (内存, B+Tree)                                 │
│   ┌──────────────────────────────────────────┐            │
│   │ "/a" → generations:                      │            │
│   │   gen0: {created=3, mod=3, ver=1}        │ ← 已删除   │
│   │   gen1: {created=5, mod=8, ver=2}        │ ← 当前     │
│   │          versions: [5, 8]                │            │
│   └──────────────────────────────────────────┘            │
│                                                            │
│   Compact(100) → 删除 revision < 100 的所有历史版本         │
│   Watch(/a, fromRev=8) → 持续推送 /a 的变更事件            │
│                                                            │
│   优势: ① 历史版本查询 ② Watch不丢事件 ③ 事务隔离          │
│   代价: ① 磁盘占用大 ② 需定期Compact ③ 写放大              │
└────────────────────────────────────────────────────────────┘
```

---

## 📖 学习路径

```
阶段一: Raft协议（Etcd实现）
  ↓  先理解Raft，它是现代分布式共识的基础（比Paxos易懂）
阶段二: Zookeeper ZAB
  ↓  对比Raft理解ZAB的差异，重点看选举恢复流程
阶段三: Consul Gossip
  ↓  理解Gossip作为AP系统的补充，以及Raft+Gossip混合架构
阶段四: 分布式锁/选主实战
  ↓  Redlock争议、ZK临时顺序节点、Etcd Lease选主
```

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐ 高频：
- ZAB协议和Raft的区别？（选举优先级、日志复制方向、恢复流程）
- Zookeeper的Watcher机制？为什么是一次性的？3.6+如何改进？
- Etcd为什么选Raft而不是ZAB？（工程清晰性、动态成员变更、社区生态）
- Zookeeper如何实现分布式锁？羊群效应如何解决？（顺序节点+Watch前一个节点）
- CAP理论在ZK/Etcd中的体现？（两者都是CP，但Etcd的Watch是最终一致）
- Etcd的MVCC如何实现？（BoltDB存储revision→kv，内存B+Tree索引）

⭐⭐⭐ 中频：
- Raft的日志压缩（Snapshot）如何工作？
- Etcd的Lease机制？如何实现TTL？
- Consul的Gossip和Raft如何协作？（Gossip做成员管理，Raft做强一致存储）
- ZK的Session过期机制？长Session和短Session的选择？
```

---

## 📊 三者对比

| 维度 | Zookeeper | Etcd | Consul |
|------|-----------|------|--------|
| 一致性协议 | ZAB | Raft | Raft |
| 数据模型 | 树形节点 | KV | KV + 服务 |
| 语言 | Java | Go | Go |
| 典型用途 | 配置/锁/注册中心 | K8s配置存储 | 服务发现/网格 |
| Watch | 一次性(3.6+持续) | 持续(MVCC) | 持续(Long Poll) |
| 多数据中心 | 不支持 | 不支持 | 原生支持(WAN Gossip) |
| 健康检查 | 需自己实现 | 需自己实现 | 内置多种检查 |

---

*最后更新：2026-07-13*

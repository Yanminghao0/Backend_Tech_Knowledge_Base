# 一致性算法：Paxos与Raft

> 分布式一致性算法的核心原理与实现，从Paxos到Raft的演进

---

## 📋 目录

1. [一致性算法概述](#1-一致性算法概述)
2. [Paxos算法](#2-paxos算法)
3. [Raft算法](#3-raft算法)
4. [ZAB协议](#4-zab协议)
5. [算法对比](#5-算法对比)
6. [面试要点](#6-面试要点)

---

## 1. 一致性算法概述

### 为什么需要一致性算法

```
分布式系统中的核心问题：多个节点如何对某个值达成一致？

场景：
1. Leader选举：集群中选出一个主节点
2. 日志复制：所有节点保持相同的操作日志
3. 配置变更：集群成员变更时保持一致

挑战：
- 节点可能宕机
- 网络可能分区
- 消息可能丢失、乱序、重复
```

### FLP不可能定理

```
Fischer, Lynch, Paterson (1985) 证明：
  在异步网络中，即使只有一个节点故障，也不存在总能达成一致的确定性算法。

实际影响：
  - 实际系统通过放宽假设来解决：
    - 放宽时间假设（加入超时机制）
    - 放宽故障模型（假设故障可恢复）
  - Paxos/Raft都通过"多数派"来达成一致
```

---

## 2. Paxos算法

### 角色定义

```
Proposer（提议者）：发起提案
Acceptor（接受者）：对提案投票
Learner（学习者）：学习已达成一致的提案
```

### Basic Paxos

```
两阶段协议：

阶段1: Prepare（准备）
  1. Proposer生成全局唯一编号N，发送Prepare(N)给所有Acceptor
  2. Acceptor收到Prepare(N)：
     - 如果N > 已承诺的最大编号，承诺不再接受<N的提案，返回已接受的提案
     - 否则拒绝

阶段2: Accept（接受）
  1. Proposer收到多数Acceptor的承诺：
     - 如果有已接受的提案，使用编号最大的那个值
     - 如果没有，使用自己的值
     - 发送Accept(N, Value)
  2. Acceptor收到Accept(N, Value)：
     - 如果N >= 已承诺的最大编号，接受该提案
     - 否则拒绝
  3. Proposer收到多数接受 → 达成一致，通知Learner
```

### Multi-Paxos

```
Basic Paxos每次确定一个值，Multi-Paxos优化：

1. 选出一个Leader，由Leader发起所有提案
2. Leader确定后，跳过Prepare阶段（只需一次）
3. 后续每个提案直接进入Accept阶段
4. Leader故障时，重新选举并执行一次Prepare

优化效果：
  - 消除Prepare阶段的往返（2次RTT → 1次RTT）
  - Leader顺序处理，保证日志顺序
```

### Paxos的难点

```
1. 难以理解：论文用数学证明，抽象程度高
2. 难以实现：缺少工程细节（如日志管理、成员变更、快照）
3. 没有标准实现：每个系统实现都不同

Google Chubby作者Mike Burrows：
  "这个世界上只有一种一致性算法，就是Paxos"
```

---

## 3. Raft算法

### 设计目标

```
Raft由Stanford于2014年提出，目标：
  - 易于理解（Understandable）
  - 易于实现（Implementable）
  - 正确性可证明

核心思想：分解问题 + 状态简化
```

### 三个子问题

```
1. Leader选举：选出一个Leader管理日志复制
2. 日志复制：Leader接收请求，复制到所有Follower
3. 安全性：保证已提交的日志不会被覆盖
```

### 节点状态

```
┌──────────────────────────────────────┐
│                                      │
│    ┌──────────┐                      │
│    │ Follower │ ← 启动状态            │
│    └────┬─────┘                      │
│         │ 选举超时                    │
│         ▼                            │
│    ┌──────────┐   获得多数票          │
│    │ Candidate├──────────┐           │
│    └────┬─────┘          ▼           │
│         │         ┌──────────┐       │
│         │         │  Leader  │       │
│         │         └────┬─────┘       │
│         │              │ 发现更高Term │
│         │              ▼             │
│         └──────────────┘             │
│                                      │
└──────────────────────────────────────┘
```

### Leader选举

```
1. 初始所有节点是Follower
2. 选举超时（150-300ms随机）→ Follower变为Candidate
3. Candidate自增Term，投票给自己，发送RequestVote RPC
4. 收到多数票 → 成为Leader
5. Leader定期发送心跳（AppendEntries）维持地位

关键机制：
  - 随机超时时间：避免多个节点同时发起选举
  - 任期（Term）：单调递增，防止过期Leader干扰
  - 每个Term每个节点只能投一票：防止多个Candidate同时获多数票
```

### 日志复制

```
1. 客户端发送命令给Leader
2. Leader将命令追加到本地日志（Uncommitted状态）
3. Leader发送AppendEntries RPC给所有Follower
4. Follower追加日志后回复ACK
5. Leader收到多数ACK → 标记为Committed
6. Leader回复客户端成功
7. Leader在下一个心跳中通知Follower已提交

                        客户端
                          │ 命令
                          ▼
    ┌──────────────────────────────────┐
    │           Leader                  │
    │  日志: [1] [2] [3*]  (*=未提交)  │
    └──────┬───────────┬──────────────┘
           │           │
    ┌──────▼─────┐ ┌───▼──────┐ ┌──────────┐
    │ Follower 1 │ │Follower 2│ │Follower 3│
    │ [1] [2] [3]│ │[1] [2] [3]│ │[1] [2]   │
    └────────────┘ └──────────┘ └──────────┘
    
    Follower 1,2 已复制 → Leader提交 → 回复客户端
```

### 安全性保证

```
选举限制：
  Candidate的日志必须至少和多数节点一样新（up-to-date）
  → 保证了已提交的日志一定在新Leader的日志中

提交规则：
  Leader只提交当前Term的日志条目
  → 旧Term的日志通过"间接提交"（当前Term日志提交时一起提交）

日志匹配：
  如果两条日志在同一Index且Term相同，则之前所有日志也相同
  → 保证了日志的一致性
```

### 成员变更

```
单步成员变更（Raft论文推荐的简化方案）：
  1. 每次只增减一个节点
  2. Leader提交配置变更日志
  3. 新配置生效

联合一致（Joint Consensus，原论文方案）：
  1. 创建C_old,new配置（新旧配置的并集）
  2. 提交C_old,new
  3. 创建C_new配置
  4. 提交C_new
```

---

## 4. ZAB协议

### 概述

```
ZAB (Zookeeper Atomic Broadcast) = 原子广播协议

用于Zookeeper，与Raft类似但有差异：
  - 崩溃恢复模式 + 消息广播模式
  - 顺序一致性（ZXID单调递增）
  - Leader选举基于ZXID（最新数据优先）
```

### ZXID结构

```
ZXID = epoch(32位) + counter(32位)

epoch：Leader任期（相当于Raft的Term）
counter：当前epoch内的事务序号

ZXID比较规则：
  1. epoch大的ZXID更大
  2. epoch相同，counter大的ZXID更大
```

### 消息广播（类似Raft日志复制）

```
1. Leader收到写请求，分配ZXID
2. Leader生成Proposal（含ZXID），发送给所有Follower
3. Follower收到Proposal，写入本地日志，回复ACK
4. Leader收到多数ACK，发送COMMIT
5. Follower收到COMMIT，应用变更

与Raft的区别：
  - ZAB先发Proposal再发COMMIT（两步）
  - Raft在AppendEntries中包含commitIndex
```

### 崩溃恢复

```
Leader故障时：
1. Follower进入选举模式
2. 各节点交换自己的ZXID
3. 选择ZXID最大的节点作为新Leader
4. 新Leader同步数据到所有Follower
5. 同步完成，进入广播模式

关键：ZXID最大的节点拥有最完整的数据
```

---

## 5. 算法对比

| 维度 | Paxos | Raft | ZAB |
|------|-------|------|-----|
| 角色 | Proposer/Acceptor/Learner | Leader/Follower/Candidate | Leader/Follower/Observer |
| 选举 | 无明确Leader（Multi-Paxos优化） | 随机超时+多数票 | ZXID最大优先 |
| 日志 | 不保证顺序 | 顺序日志 | 顺序日志（ZXID） |
| 复杂度 | ⭐⭐⭐⭐⭐ 极难 | ⭐⭐ 较易 | ⭐⭐⭐ 中等 |
| 工程实现 | 少（Chubby/Spanner） | 多（etcd/Consul/TiKV） | Zookeeper |
| 成员变更 | 未定义 | 单步变更 | 动态重新配置 |

### Raft vs Paxos核心差异

```
Paxos：
  - 面向"值"的一致性（Value）
  - 不假设Leader存在
  - 日志顺序由Leader在运行时决定

Raft：
  - 面向"日志"的一致性（Log Entry）
  - 强Leader模型
  - 日志顺序由Leader追加时决定
  - 更容易理解和实现
```

---

## 6. 面试要点

### Q1: Raft和Paxos的区别？

```
1. 可理解性：Raft设计目标就是易懂，Paxos以数学证明为主
2. Leader角色：Raft强Leader，Paxos的Multi-Paxos可选Leader
3. 日志管理：Raft有明确的日志匹配规则，Paxos不涉及
4. 成员变更：Raft有明确的单步变更方案，Paxos未定义
5. 工程实现：Raft有完整工程描述，Paxos缺少实现细节
```

### Q2: Raft如何保证已提交的日志不被覆盖？

```
1. 选举限制：Candidate的日志必须至少和多数节点一样新
2. 如果一条日志已提交，说明多数节点有该日志
3. 新Leader的日志至少和多数节点一样新 → 一定包含已提交的日志
4. Leader不会删除或覆盖自己的日志 → 已提交日志安全
```

### Q3: Raft的脑裂问题如何解决？

```
脑裂场景：网络分区，原Leader与部分Follower隔离

解决：多数派机制
  - 分区后，原Leader所在的少数派分区无法提交日志（凑不齐多数ACK）
  - 另一个分区选出新Leader（拥有多数节点）
  - 原Leader的Term < 新Leader的Term
  - 网络恢复后，原Leader退化为Follower，日志被新Leader覆盖
```

### Q4: ZAB和Raft的区别？

```
1. 选举依据：ZAB选ZXID最大（数据最新），Raft选日志最长
2. 提交机制：ZAB两步(Proposal+COMMIT)，Raft一步(AppendEntries含commitIndex)
3. 数据顺序：ZAB用ZXID保证全局顺序，Raft用LogIndex
4. 适用场景：ZAB用于ZK配置管理，Raft用于通用KV存储
```

### Q5: 为什么需要多数派（Quorum）？

```
1. 容错性：N个节点，多数派=N/2+1，可容忍N/2个节点故障
2. 一致性：多数派一定有交集 → 保证了信息传递
3. 可用性：少数节点故障不影响系统运行

3节点集群：容忍1个故障，多数=2
5节点集群：容忍2个故障，多数=3
7节点集群：容忍3个故障，多数=4
```

---

## 📚 相关阅读

- [04_Zookeeper核心原理](./04_Zookeeper核心原理.md)
- [06_CAP与BASE理论详解](./06_CAP与BASE理论详解.md)
- [02_分布式事务详解](./02_分布式事务详解.md)
- [Nacos核心机制详解](../06_微服务/核心组件/02_Nacos核心机制详解.md)

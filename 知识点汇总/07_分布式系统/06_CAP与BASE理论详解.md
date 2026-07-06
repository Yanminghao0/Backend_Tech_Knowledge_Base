# CAP与BASE理论详解

> 分布式系统两大基石理论：CAP的取舍智慧与BASE的最终一致性哲学

---

## 📋 目录

1. [CAP理论](#1-cap理论)
2. [CAP的证明](#2-cap的证明)
3. [CP vs AP vs CA选择](#3-cp-vs-ap-vs-ca选择)
4. [BASE理论](#4-base理论)
5. [最终一致性实现方案](#5-最终一致性实现方案)
6. [CAP在架构选型中的应用](#6-cap在架构选型中的应用)
7. [面试要点](#7-面试要点)

---

## 1. CAP理论

### 定义

CAP由Eric Brewer于2000年提出，2002年Gilbert和Lynch证明：

- **C (Consistency) 一致性**：所有节点同一时刻看到相同数据
- **A (Availability) 可用性**：每个请求都能收到响应（不保证是最新数据）
- **P (Partition Tolerance) 分区容错性**：网络分区时系统仍能运行

### 核心定理

```
CAP定理：分布式系统最多同时满足C、A、P中的两个，不可能三者兼顾。

    C (一致性)
   / \
  /   \
 /     \
A-------P
(可用性) (分区容错)
```

### 精确理解

```
一致性(C) ≠ 强一致性
  - 强一致性：写完成后，后续读一定能读到最新值
  - 弱一致性：写完成后，不保证后续读能读到最新值
  - 最终一致性：弱一致性的特例，最终会一致

可用性(A) ≠ 永远可用
  - 非故障节点必须在有限时间内返回合理响应（不能无限等待或报错）
  - 返回旧数据也算可用

分区容错性(P) ≠ 网络分区发生时才考虑
  - 分布式系统网络分区必然可能发生
  - P是前提，不是选择
```

---

## 2. CAP的证明

### 反证法

```
假设系统同时满足CAP：

节点A ←→ 节点B

1. 发生网络分区，A和B无法通信 (P成立)

2. 客户端向A写入数据v1
   - A必须返回成功响应 (A成立)
   - A的数据变为v1

3. 客户端向B读取数据
   - B必须返回响应 (A成立)
   - B无法从A同步，数据还是v0
   - 返回了旧数据 → C不成立！

结论：P成立时，A和C不能同时满足
```

### 实际含义

```
网络分区发生时：
  选择C：拒绝响应（牺牲A），等数据同步完成
  选择A：返回可能过期的数据（牺牲C）

网络正常时：
  C和A可以同时满足（P不触发）
```

---

## 3. CP vs AP vs CA选择

### CP系统（一致性 + 分区容错）

```
特点：网络分区时，拒绝服务，保证数据一致

代表系统：
  - Zookeeper：写操作需要半数以上节点确认
  - Redis（主从模式+WAIT命令）：等待同步完成
  - MongoDB（Write Concern=majority）
  - etcd：Raft协议保证强一致

适用场景：
  - 分布式锁（必须强一致）
  - 配置中心（数据不能错）
  - 金融交易（数据不能有歧义）
```

### AP系统（可用性 + 分区容错）

```
特点：网络分区时，继续服务，允许数据短暂不一致

代表系统：
  - Eureka：节点间异步复制，分区时各自服务
  - Cassandra：可调一致性级别
  - DynamoDB：最终一致性
  - Redis（默认主从）：异步复制，从库可读旧数据

适用场景：
  - 服务注册发现（短暂不一致可接受）
  - 社交媒体（内容延迟可见可接受）
  - 缓存系统
```

### CA系统（一致性 + 可用性）

```
特点：单机系统，无网络分区问题

代表系统：
  - MySQL单机
  - PostgreSQL单机

注意：分布式系统中CA不可选，因为P必然存在
```

### 选择对比

| 维度 | CP | AP |
|------|-----|-----|
| 分区时响应 | 拒绝服务 | 返回（可能旧）数据 |
| 数据一致性 | 强一致 | 最终一致 |
| 可用性 | 降低 | 保证 |
| 典型场景 | 分布式锁、金融 | 注册中心、社交 |

---

## 4. BASE理论

### BASE是CAP的补充

```
CAP告诉我们：分布式系统分区时必须在C和A之间选一个
BASE告诉我们：选择AP后，如何让数据最终一致

BASE = Basically Available + Soft State + Eventually Consistent
```

### Basically Available（基本可用）

```
允许损失部分可用性：
  - 响应时间增加（降级处理）
  - 非核心功能降级（如电商大促时关闭评论）

示例：
  正常：订单查询 RT < 100ms
  大促：订单查询 RT < 2s（允许慢，但不拒绝）
  降级：关闭推荐功能，保障下单
```

### Soft State（软状态）

```
允许系统中存在中间状态，不影响系统整体可用性

示例：
  - 订单状态：待支付 → 支付中 → 已支付
    "支付中"就是软状态，数据在变化中
  
  - 数据库主从复制：
    主库写入，从库还没同步 → 从库数据是软状态
  
  - 消息队列：
    生产者发送消息，消费者还没消费 → 消息处于软状态
```

### Eventually Consistent（最终一致性）

```
系统保证最终数据会达到一致状态，但不需要实时一致

时间窗口：
  - 最终一致 ≠ 立即一致
  - 延迟取决于：网络延迟、复制策略、负载

一致性变体：
  - 读己之所写：客户端能看到自己写入的数据
  - 会话一致性：同一会话内一致
  - 单调读一致性：不会读到比之前更旧的数据
  - 单调写一致性：同一客户端的写操作按顺序执行
```

---

## 5. 最终一致性实现方案

### 方案一：消息队列

```java
// 订单服务 → MQ → 库存服务
@Service
public class OrderService {
    
    @Transactional
    public void createOrder(Order order) {
        orderMapper.insert(order);
        // 发送消息，异步扣减库存
        rocketMQTemplate.asyncSend("order-topic", 
            new OrderMessage(order.getId(), order.getProductId()), 
            callback);
    }
}

// 库存服务消费消息
@RocketMQMessageListener(topic = "order-topic")
public class StockConsumer implements RocketMQListener<OrderMessage> {
    @Override
    public void onMessage(OrderMessage message) {
        stockMapper.deduct(message.getProductId());
    }
}
```

### 方案二：定时任务补偿

```java
// 定时检查不一致数据并补偿
@Scheduled(fixedDelay = 60000)
public void compensate() {
    // 查找5分钟前创建但库存未扣减的订单
    List<Order> orders = orderMapper.findUncompensatedOrders();
    for (Order order : orders) {
        try {
            stockService.deduct(order.getProductId());
            orderMapper.markCompensated(order.getId());
        } catch (Exception e) {
            log.error("补偿失败: {}", order.getId(), e);
        }
    }
}
```

### 方案三：CDC（变更数据捕获）

```
MySQL Binlog → Canal → Kafka → 下游服务

优势：
  - 对业务代码零侵入
  - 实时捕获数据变更
  - 顺序保证
```

### 方案四：TCC事务补偿

```java
// TCC模式
public class OrderTccAction {
    
    // Try：预留资源
    public boolean tryCreateOrder(Order order) {
        // 冻结库存
        stockService.freeze(order.getProductId(), order.getQuantity());
        return true;
    }
    
    // Confirm：确认执行
    public boolean confirmCreateOrder(Order order) {
        // 扣减冻结的库存
        stockService.deductFrozen(order.getProductId(), order.getQuantity());
        orderMapper.updateStatus(order.getId(), "CONFIRMED");
        return true;
    }
    
    // Cancel：取消预留
    public boolean cancelCreateOrder(Order order) {
        // 解冻库存
        stockService.unfreeze(order.getProductId(), order.getQuantity());
        orderMapper.updateStatus(order.getId(), "CANCELLED");
        return true;
    }
}
```

---

## 6. CAP在架构选型中的应用

### 注册中心选型

| 注册中心 | CAP | 说明 |
|---------|-----|------|
| Zookeeper | CP | 写需半数确认，分区时不可用 |
| Eureka | AP | 节点独立服务，分区时不影响 |
| Nacos | AP/CP可切换 | 默认AP，可切换CP |
| Consul | CP | Raft协议 |

```
注册中心应该选AP还是CP？
  答案：AP
  原因：
  - 注册中心数据不一致的后果：请求发到已下线实例 → 重试即可
  - 注册中心不可用的后果：所有服务发现失败 → 系统瘫痪
  - 权衡：短暂不一致远比不可用可接受
```

### 分布式锁选型

| 方案 | CAP | 说明 |
|------|-----|------|
| Redis(Redlock) | AP | 异步复制，故障时可能丢锁 |
| Zookeeper | CP | 写需半数确认，强一致 |
| etcd | CP | Raft协议，强一致 |

```
分布式锁应该选CP还是AP？
  答案：CP
  原因：
  - 锁不一致的后果：两个客户端同时持有锁 → 数据损坏
  - 锁服务不可用的后果：请求失败 → 可重试或降级
  - 权衡：数据安全比可用性更重要
```

### 消息队列选型

| MQ | CAP | 说明 |
|----|-----|------|
| Kafka | CP | 副本同步，Leader选举 |
| RocketMQ | CP | 同步刷盘+同步复制 |
| RabbitMQ | AP | 镜像队列异步复制 |

---

## 7. 面试要点

### Q1: CAP三者能同时满足吗？

```
不能。在网络分区(P)发生时，必须在C和A之间做选择。

但注意：网络正常时（P不触发），C和A可以同时满足。
CAP说的是"分区时"的取舍，不是"始终"的取舍。
```

### Q2: 为什么注册中心选AP而不是CP？

```
1. 注册中心短暂不一致 → 请求到已下线实例 → 重试解决
2. 注册中心不可用 → 所有服务发现失败 → 系统瘫痪
3. 可用性的损失远大于短暂不一致的损失
4. Eureka的设计理念就是AP，Nacos默认也是AP
```

### Q3: BASE理论和CAP的关系？

```
CAP是理论：分区时选C或A
BASE是实践：选了A之后如何让数据最终一致

CAP → 选择AP
BASE → 基本可用 + 软状态 + 最终一致性

两者结合：放弃强一致，追求高可用+最终一致
```

### Q4: 强一致性和最终一致性的区别？

```
强一致性：
  写完成后，任何后续读都能读到最新值
  实现：同步复制、两阶段提交
  性能：低（需要协调）

最终一致性：
  写完成后，不保证立即读到，但最终会一致
  实现：异步复制、消息队列
  性能：高（无需等待同步）
```

### Q5: 如何实现数据的最终一致性？

```
1. 消息队列：业务事件驱动，异步同步
2. 定时补偿：定时检查不一致并修复
3. CDC：捕获数据库变更，实时同步
4. TCC：Try-Confirm-Cancel补偿模式
5. Saga：长事务拆分为多个本地事务+补偿

选择依据：
  - 延迟要求：CDC < MQ < 定时补偿
  - 实现复杂度：定时补偿 < MQ < TCC < CDC
  - 可靠性：TCC > MQ > 定时补偿
```

---

## 📚 相关阅读

- [02_分布式事务详解](./02_分布式事务详解.md)
- [03_分布式锁详解](./03_分布式锁详解.md)
- [04_Zookeeper核心原理](./04_Zookeeper核心原理.md)
- [Nacos核心机制详解](../06_微服务/核心组件/02_Nacos核心机制详解.md)

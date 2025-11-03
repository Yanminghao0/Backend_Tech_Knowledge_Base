# 消息队列核心机制详解

> 深入理解消息队列的架构设计、高可用方案、性能优化

---

## 📋 文档列表

### 1. RocketMQ核心机制详解
📄 [RocketMQ核心机制详解.md](./RocketMQ核心机制详解.md)

**核心内容**：
- ✅ **架构设计**：NameServer、Broker、Producer、Consumer
- ✅ **消息存储**：CommitLog、ConsumeQueue、IndexFile
- ✅ **高可用方案**：主从复制、Dledger高可用
- ✅ **消息可靠性**：发送确认、消费确认、事务消息
- ✅ **顺序消息**：全局顺序、分区顺序实现
- ✅ **延迟消息**：18个延迟级别实现原理

**核心特性**：
- 🚀 高性能：单机支持万级TPS
- 💯 高可靠：消息零丢失
- 📊 大容量：支持亿级消息堆积
- 🔄 分布式：支持集群部署
- 🎯 多场景：普通消息、顺序消息、事务消息、延迟消息

**适合场景**：
- 系统解耦
- 异步处理
- 流量削峰
- 分布式事务
- 日志收集

---

## 🎯 消息队列使用场景

### 1️⃣ 异步处理
```java
// 订单创建后异步发送通知
@Service
public class OrderService {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    public void createOrder(Order order) {
        // 1. 保存订单到数据库
        orderMapper.insert(order);
        
        // 2. 异步发送消息（不阻塞主流程）
        rocketMQTemplate.asyncSend("order-topic", order, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("消息发送成功");
            }
            
            @Override
            public void onException(Throwable e) {
                log.error("消息发送失败", e);
            }
        });
    }
}
```

### 2️⃣ 系统解耦
```java
// 订单服务不需要关心下游服务
// 发送消息到消息队列
rocketMQTemplate.convertAndSend("order-created-topic", orderEvent);

// 多个下游服务独立消费
// 1. 库存服务：扣减库存
// 2. 积分服务：增加积分
// 3. 短信服务：发送短信
// 4. 推荐服务：更新推荐模型
```

### 3️⃣ 流量削峰
```java
// 秒杀场景：将请求先放入消息队列
@PostMapping("/seckill")
public Result seckill(Long productId, Long userId) {
    // 发送到消息队列
    SeckillOrder order = new SeckillOrder(productId, userId);
    rocketMQTemplate.convertAndSend("seckill-topic", order);
    
    return Result.success("排队中，请稍候查询结果");
}

// 消费者慢慢处理，避免数据库压力过大
@RocketMQMessageListener(topic = "seckill-topic", consumerGroup = "seckill-consumer")
public class SeckillConsumer implements RocketMQListener<SeckillOrder> {
    @Override
    public void onMessage(SeckillOrder order) {
        // 处理秒杀逻辑
        seckillService.processSeckill(order);
    }
}
```

### 4️⃣ 分布式事务
```java
// 使用RocketMQ事务消息保证分布式事务一致性
@Service
public class OrderService {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    public void createOrderWithTransaction(Order order) {
        // 发送事务消息
        rocketMQTemplate.sendMessageInTransaction(
            "order-topic",
            MessageBuilder.withPayload(order).build(),
            order
        );
    }
    
    // 事务监听器
    @RocketMQTransactionListener
    public class OrderTransactionListener implements RocketMQLocalTransactionListener {
        
        @Override
        public RocketMQLocalTransactionState executeLocalTransaction(Message msg, Object arg) {
            try {
                // 执行本地事务（创建订单）
                Order order = (Order) arg;
                orderMapper.insert(order);
                
                return RocketMQLocalTransactionState.COMMIT;
            } catch (Exception e) {
                return RocketMQLocalTransactionState.ROLLBACK;
            }
        }
        
        @Override
        public RocketMQLocalTransactionState checkLocalTransaction(Message msg) {
            // 回查本地事务状态
            // ...
            return RocketMQLocalTransactionState.COMMIT;
        }
    }
}
```

### 5️⃣ 延迟任务
```java
// 订单超时自动取消（30分钟后）
Message<Order> message = MessageBuilder
    .withPayload(order)
    .build();

// RocketMQ支持18个延迟级别
// 1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h
rocketMQTemplate.syncSend(
    "order-timeout-topic",
    message,
    3000, // 超时时间
    16    // 延迟级别：30分钟
);

// 消费者处理超时订单
@RocketMQMessageListener(topic = "order-timeout-topic", consumerGroup = "timeout-consumer")
public class TimeoutConsumer implements RocketMQListener<Order> {
    @Override
    public void onMessage(Order order) {
        // 检查订单状态，如果未支付则取消
        if (order.getStatus() == OrderStatus.UNPAID) {
            orderService.cancelOrder(order.getId());
        }
    }
}
```

---

## 🔄 消息队列选型对比

| 特性 | RocketMQ | Kafka | RabbitMQ |
|------|----------|-------|----------|
| **吞吐量** | 10万级/秒 | 百万级/秒 | 万级/秒 |
| **延迟** | 毫秒级 | 毫秒级 | 微秒级 |
| **可靠性** | 很高 | 很高 | 高 |
| **顺序消息** | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **事务消息** | ✅ 支持 | ❌ 不支持 | ✅ 支持 |
| **延迟消息** | ✅ 支持 | ❌ 不支持 | ✅ 需插件 |
| **消息堆积** | 支持亿级 | 支持万亿级 | 支持百万级 |
| **适用场景** | 业务消息 | 日志/大数据 | 实时性要求高 |

### 选型建议

**选择RocketMQ**：
- ✅ 金融支付、电商交易等核心业务
- ✅ 需要事务消息
- ✅ 需要延迟消息
- ✅ 需要消息回溯

**选择Kafka**：
- ✅ 大数据场景
- ✅ 日志收集
- ✅ 流式处理
- ✅ 对吞吐量要求极高

**选择RabbitMQ**：
- ✅ 实时性要求高
- ✅ 需要复杂路由
- ✅ 中小规模应用
- ✅ 对延迟敏感

---

## 🚨 常见问题与解决方案

### 1️⃣ 消息丢失

**原因**：
- 生产者发送失败未重试
- Broker宕机数据未持久化
- 消费者处理异常自动ACK

**解决方案**：
```java
// 1. 生产者同步发送 + 重试
SendResult result = rocketMQTemplate.syncSend("topic", message);
if (result.getSendStatus() != SendStatus.SEND_OK) {
    // 重试或记录日志
}

// 2. Broker配置刷盘策略
// flushDiskType=SYNC_FLUSH（同步刷盘）

// 3. 消费者手动ACK
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-consumer",
    consumeMode = ConsumeMode.ORDERLY
)
public class OrderConsumer implements RocketMQListener<Order> {
    @Override
    public void onMessage(Order order) {
        try {
            // 处理业务逻辑
            orderService.process(order);
        } catch (Exception e) {
            // 返回RECONSUME_LATER，消息会重新投递
            throw new RuntimeException(e);
        }
    }
}
```

### 2️⃣ 消息重复消费

**原因**：
- 网络抖动导致ACK未收到
- 消费者宕机重启
- 消息重试

**解决方案**：
```java
// 1. 幂等性设计（数据库唯一索引）
@Transactional
public void processOrder(Order order) {
    try {
        orderMapper.insert(order); // 主键冲突会抛异常
    } catch (DuplicateKeyException e) {
        log.warn("订单已存在，忽略重复消息: {}", order.getId());
        return;
    }
}

// 2. 使用Redis记录已处理的消息ID
public void processOrder(Order order) {
    String key = "processed:order:" + order.getMessageId();
    
    // 检查是否已处理
    if (redisTemplate.hasKey(key)) {
        log.warn("消息已处理，忽略: {}", order.getMessageId());
        return;
    }
    
    // 处理业务
    orderService.process(order);
    
    // 记录已处理（设置过期时间）
    redisTemplate.opsForValue().set(key, "1", 24, TimeUnit.HOURS);
}
```

### 3️⃣ 消息积压

**原因**：
- 消费速度慢于生产速度
- 消费者宕机或处理异常
- 消费者数量不足

**解决方案**：
```java
// 1. 增加消费者数量（扩容）
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-consumer",
    consumeThreadMax = 64 // 增加消费线程
)

// 2. 批量消费
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-consumer",
    consumeMode = ConsumeMode.CONCURRENTLY,
    messageModel = MessageModel.CLUSTERING,
    consumeThreadMax = 64,
    maxReconsumeTimes = 3
)
public class OrderBatchConsumer implements RocketMQListener<List<Order>> {
    @Override
    public void onMessage(List<Order> orders) {
        // 批量处理
        orderService.batchProcess(orders);
    }
}

// 3. 优化消费逻辑（异步处理）
@Override
public void onMessage(Order order) {
    // 快速ACK，避免阻塞
    CompletableFuture.runAsync(() -> {
        orderService.process(order);
    }, executor);
}
```

### 4️⃣ 顺序消息乱序

**原因**：
- 并发消费
- 消息重试
- 队列重新分配

**解决方案**：
```java
// 发送顺序消息（按订单ID分区）
rocketMQTemplate.syncSendOrderly(
    "order-topic",
    order,
    order.getId().toString() // 相同orderId的消息发到同一队列
);

// 顺序消费
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-consumer",
    consumeMode = ConsumeMode.ORDERLY // 顺序消费模式
)
public class OrderConsumer implements RocketMQListener<Order> {
    @Override
    public void onMessage(Order order) {
        // 单线程顺序处理
        orderService.process(order);
    }
}
```

---

## 📊 性能优化

### 生产者优化

```java
// 1. 异步发送
rocketMQTemplate.asyncSend("topic", message, new SendCallback() {
    @Override
    public void onSuccess(SendResult sendResult) {}
    
    @Override
    public void onException(Throwable e) {}
});

// 2. 批量发送
List<Message> messages = new ArrayList<>();
// ... 添加消息
rocketMQTemplate.syncSend("topic", messages);

// 3. 消息压缩
Message message = MessageBuilder
    .withPayload(data)
    .setHeader(MessageConst.PROPERTY_COMPRESS_TYPE, "ZLIB")
    .build();
```

### 消费者优化

```java
// 1. 增加消费线程
consumeThreadMax = 64

// 2. 批量消费
@RocketMQMessageListener(
    topic = "topic",
    consumerGroup = "group",
    consumeMode = ConsumeMode.CONCURRENTLY,
    maxReconsumeTimes = 3
)

// 3. 过滤消息
@RocketMQMessageListener(
    topic = "order-topic",
    selectorExpression = "type == 'VIP'" // 只消费VIP订单
)
```

---

## 🔗 相关资源

- 📚 [RocketMQ官方文档](https://rocketmq.apache.org/docs/quick-start/)
- 📚 [Kafka官方文档](https://kafka.apache.org/documentation/)
- 📚 [RabbitMQ官方文档](https://www.rabbitmq.com/documentation.html)

---

## 🔄 持续更新

- [ ] Kafka核心机制详解
- [ ] RabbitMQ核心机制详解
- [ ] Pulsar核心机制详解
- [ ] 消息队列架构设计实战

---

*最后更新：2025-10-27*


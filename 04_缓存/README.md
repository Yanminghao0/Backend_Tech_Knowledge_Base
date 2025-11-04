# 缓存核心机制详解

> 深入理解缓存系统的原理、架构设计、高可用方案

---

## 📋 文档列表

### 1. 缓存架构设计与实战 ⭐ 新增
📄 [缓存架构设计与实战.md](./缓存架构设计与实战.md)

**核心内容**：
- ✅ **缓存使用时机**：QPS、数据量、场景判断
- ✅ **缓存选型决策**：本地缓存 vs Redis vs 多级缓存
- ✅ **本地缓存实战**：Caffeine、过期策略、统计监控
- ✅ **Redis分布式缓存**：数据类型、序列化、批量操作
- ✅ **多级缓存架构**：L1本地+L2分布式+L3数据库
- ✅ **缓存设计模式**：Cache-Aside、Read-Through、Write-Through
- ✅ **缓存问题解决**：穿透、击穿、雪崩、一致性
- ✅ **性能优化**：Pipeline、Lua脚本、压缩
- ✅ **实战案例**：电商、秒杀、排行榜、Session共享

**核心特性**：
- 📊 **明确指标**：QPS、数据量阈值，决策流程图
- 🎯 **选型决策**：详细对比，适用场景分析
- 💡 **实战导向**：5个完整案例，拿来即用
- 🔍 **问题排查**：常见问题诊断与解决
- 📈 **演进路线**：从无缓存到百万QPS

**适合场景**：
- 系统架构设计
- 缓存选型决策
- 性能优化
- 面试准备

---

### 2. Redis核心机制详解
📄 [Redis核心机制详解.md](./Redis核心机制详解.md)

**核心内容**：
- ✅ **数据结构**：String、List、Hash、Set、ZSet底层实现
- ✅ **持久化机制**：RDB快照、AOF日志、混合持久化
- ✅ **高可用方案**：主从复制、哨兵模式、集群模式
- ✅ **缓存策略**：缓存穿透、缓存击穿、缓存雪崩解决方案
- ✅ **内存管理**：过期策略、淘汰策略、内存优化

**核心特性**：
- ⚡ 单线程模型 + IO多路复用
- 📦 丰富的数据结构
- 💾 多种持久化方案
- 🔄 主从复制与集群
- 🎯 高性能缓存方案

**适合场景**：
- 缓存架构设计
- 高并发系统优化
- 分布式锁实现
- 实时排行榜
- 消息队列

---

## 🎯 Redis使用场景

### 1️⃣ 缓存加速
```java
// 热点数据缓存
String userJson = redisTemplate.opsForValue().get("user:" + userId);
if (userJson == null) {
    User user = userMapper.selectById(userId);
    redisTemplate.opsForValue().set("user:" + userId, JSON.toJSONString(user), 1, TimeUnit.HOURS);
}
```

### 2️⃣ 分布式锁
```java
// 基于Redis实现分布式锁
Boolean success = redisTemplate.opsForValue().setIfAbsent(
    "lock:order:" + orderId,
    "locked",
    30, TimeUnit.SECONDS
);
```

### 3️⃣ 计数器/限流
```java
// 接口限流（令牌桶算法）
Long count = redisTemplate.opsForValue().increment("rate:limit:" + userId);
redisTemplate.expire("rate:limit:" + userId, 1, TimeUnit.SECONDS);
if (count > 100) {
    throw new RateLimitException("请求过于频繁");
}
```

### 4️⃣ 排行榜
```java
// 游戏积分排行榜
redisTemplate.opsForZSet().add("rank:score", "player1", 1000);
Set<String> top10 = redisTemplate.opsForZSet().reverseRange("rank:score", 0, 9);
```

### 5️⃣ 消息队列
```java
// 发布订阅模式
redisTemplate.convertAndSend("channel:order", orderMessage);

// 消费者
redisTemplate.execute((RedisCallback<Long>) connection -> {
    connection.subscribe((message, pattern) -> {
        // 处理消息
    }, "channel:order".getBytes());
    return null;
});
```

---

## 🔄 缓存设计模式

### Cache-Aside Pattern（旁路缓存）
```
读取：先查缓存 → 缓存未命中 → 查数据库 → 写入缓存
写入：先写数据库 → 删除缓存
```

### Read-Through Pattern（读穿透）
```
应用层 → 缓存层（自动加载数据）→ 数据库
```

### Write-Through Pattern（写穿透）
```
应用层 → 缓存层（同步写数据库）→ 数据库
```

### Write-Behind Pattern（异步写回）
```
应用层 → 缓存层 → 异步批量写数据库
```

---

## 🚨 常见问题与解决方案

### 1️⃣ 缓存穿透
**问题**：查询不存在的数据，缓存和数据库都没有，导致每次都打到数据库

**解决方案**：
- ✅ 布隆过滤器（Bloom Filter）
- ✅ 缓存空值（设置短过期时间）
- ✅ 接口校验（参数合法性检查）

### 2️⃣ 缓存击穿
**问题**：热点数据过期，大量请求同时打到数据库

**解决方案**：
- ✅ 互斥锁（只有一个线程查数据库）
- ✅ 热点数据永不过期
- ✅ 提前异步刷新缓存

### 3️⃣ 缓存雪崩
**问题**：大量缓存同时过期，数据库承受不住压力

**解决方案**：
- ✅ 过期时间加随机值
- ✅ 多级缓存（本地缓存+Redis）
- ✅ 限流降级
- ✅ Redis集群高可用

### 4️⃣ 缓存一致性
**问题**：缓存和数据库数据不一致

**解决方案**：
- ✅ 先更新数据库，再删除缓存
- ✅ 延迟双删（删除缓存→更新DB→再删除缓存）
- ✅ 订阅Binlog更新缓存（Canal）
- ✅ 设置合理的过期时间

---

## 📊 性能优化

### 优化策略

| 优化点 | 方案 | 效果 |
|--------|------|------|
| **网络优化** | Pipeline批量操作 | 减少网络往返 |
| **数据结构** | 选择合适的数据类型 | 节省内存 |
| **序列化** | 使用高效序列化方式 | 减少数据大小 |
| **过期策略** | 合理设置TTL | 避免内存溢出 |
| **集群模式** | 数据分片 | 提高吞吐量 |

---

## 🔗 相关资源

- 📚 [Redis官方文档](https://redis.io/documentation)
- 📚 [Redis设计与实现](https://book.douban.com/subject/25900156/)
- 📚 [Redis开发与运维](https://book.douban.com/subject/26971561/)

---

## 🔄 持续更新

- [x] **缓存架构设计与实战** ✅ 已完成
- [ ] Memcached核心机制
- [ ] 缓存监控与运维深入
- [ ] 大Key问题排查与优化

---

*最后更新：2025-10-27*


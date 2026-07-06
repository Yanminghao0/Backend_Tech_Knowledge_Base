# MySQL分库分表实战

> 从单库单表到千库万表，海量数据架构演进之路

---

## 📋 目录

- [1. 为什么要分库分表](#1-为什么要分库分表)
- [2. 拆分策略](#2-拆分策略)
- [3. 分片算法](#3-分片算法)
- [4. Sharding-JDBC实战](#4-sharding-jdbc实战)
- [5. 分布式ID](#5-分布式id)
- [6. 数据迁移](#6-数据迁移)
- [7. 跨库查询](#7-跨库查询)
- [8. 分布式事务](#8-分布式事务)
- [9. 扩容缩容](#9-扩容缩容)
- [10. 实战案例](#10-实战案例)

---

## 🎯 学习目标

通过本文档，你将掌握：
- ✅ 分库分表的时机与策略
- ✅ 垂直拆分与水平拆分
- ✅ 分片算法（Range、Hash、一致性Hash）
- ✅ Sharding-JDBC核心原理与实战
- ✅ 分布式ID生成方案（雪花算法、数据库、Redis）
- ✅ 数据迁移方案（双写、灰度、回滚）
- ✅ 跨库查询解决方案
- ✅ 分布式事务（Seata）
- ✅ 扩容缩容方案
- ✅ 从单库到1024张表的实战

---

## 1. 为什么要分库分表

### 1.1 单库单表的问题

**性能瓶颈**：
```
订单表：1亿条数据

问题：
1. 索引膨胀：B+树高度增加，查询变慢
2. 单表太大：扫描、统计慢
3. 锁竞争：并发写入等待
4. 连接数限制：单库连接数有上限
```

**数据量与性能关系**：

| 数据量 | 查询性能 | 写入性能 | 索引大小 |
|--------|---------|---------|---------|
| 100万 | 优秀 | 优秀 | 20MB |
| 1000万 | 良好 | 良好 | 200MB |
| 5000万 | 一般 | 一般 | 1GB |
| 1亿 | 差 | 差 | 2GB |
| 5亿+ | 很差 | 很差 | 10GB+ |

**建议**：
- 单表数据量 **< 500万**
- 单库数据量 **< 2000万**
- 单表文件大小 **< 2GB**

### 1.2 什么时候分库分表

**分表时机**：
```
✅ 单表数据量 > 500万
✅ 单表文件大小 > 2GB
✅ 查询变慢（P99 > 1秒）
✅ 写入TPS下降
```

**分库时机**：
```
✅ 单库连接数不够（> 1000）
✅ 单库TPS达到瓶颈（> 5000）
✅ 单库磁盘IO达到瓶颈
✅ 单库CPU/内存达到瓶颈
```

**不建议分库分表的场景**：
```
❌ 数据量小（< 100万）
❌ 增长缓慢（年增长 < 100万）
❌ 查询简单（主键查询为主）
❌ 团队经验不足
```

### 1.3 分库分表的收益与代价

**收益**：
- ✅ **性能提升**：单表数据量减少，查询更快
- ✅ **水平扩展**：增加服务器，提升并发
- ✅ **高可用**：单库故障影响范围小

**代价**：
- ❌ **复杂度提升**：路由、聚合、事务
- ❌ **跨库查询困难**：JOIN、聚合、排序
- ❌ **数据迁移成本**：历史数据迁移
- ❌ **运维成本**：多库管理

---

## 2. 拆分策略

### 2.1 垂直拆分

**垂直分库**：按业务模块拆分

```
单体数据库：
┌─────────────────┐
│   MySQL (All)   │
│ ┌─────────────┐ │
│ │ 订单表       │ │
│ │ 用户表       │ │
│ │ 商品表       │ │
│ │ 库存表       │ │
│ └─────────────┘ │
└─────────────────┘

垂直分库后：
┌──────────┐  ┌──────────┐  ┌──────────┐
│订单库     │  │用户库     │  │商品库     │
│┌────────┐│  │┌────────┐│  │┌────────┐│
││订单表   ││  ││用户表   ││  ││商品表   ││
││        ││  ││        ││  ││库存表   ││
│└────────┘│  │└────────┘│  │└────────┘│
└──────────┘  └──────────┘  └──────────┘
```

**优点**：
- ✅ 业务隔离，互不影响
- ✅ 微服务化，独立部署
- ✅ 降低单库连接数

**缺点**：
- ❌ 跨库JOIN困难
- ❌ 分布式事务

**垂直分表**：按字段拆分

```
订单表（大字段）：
┌──────┬──────┬───────┬────────┐
│ ID   │ 用户  │ 商品   │ 备注    │
│      │      │       │(TEXT)  │
└──────┴──────┴───────┴────────┘

垂直分表后：
订单主表：                  订单扩展表：
┌──────┬──────┬───────┐  ┌──────┬────────┐
│ ID   │ 用户  │ 商品   │  │ ID   │ 备注    │
└──────┴──────┴───────┘  └──────┴────────┘
```

**适用场景**：
- 大字段（TEXT、BLOB）
- 冷热数据分离
- 字段数 > 50个

### 2.2 水平拆分

**水平分库**：按数据拆分到多个库

```
订单表（1亿条）
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│ DB0     │ DB1     │ DB2     │ DB3     │
│2500万   │2500万   │2500万   │2500万   │
└─────────┴─────────┴─────────┴─────────┘
```

**水平分表**：按数据拆分到多张表

```
订单表（1亿条）
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│order_0  │order_1  │order_2  │order_3  │
│2500万   │2500万   │2500万   │2500万   │
└─────────┴─────────┴─────────┴─────────┘
```

**水平分库分表**：库 × 表

```
4个库 × 256张表 = 1024个分片

DB0:
  order_0_0, order_0_1, ..., order_0_255
DB1:
  order_1_0, order_1_1, ..., order_1_255
DB2:
  order_2_0, order_2_1, ..., order_2_255
DB3:
  order_3_0, order_3_1, ..., order_3_255
```

### 2.3 拆分维度选择

**按用户ID拆分（推荐）**：
```
优点：
✅ 同一用户数据在同一库（JOIN方便）
✅ 用户维度查询不跨库
✅ 负载均衡（用户分布均匀）

缺点：
❌ 大V用户可能数据倾斜
```

**按时间拆分**：
```
优点：
✅ 冷热数据分离
✅ 历史数据归档方便

缺点：
❌ 最新数据压力大
❌ 跨时间查询困难
```

**按地区拆分**：
```
优点：
✅ 地域查询不跨库
✅ 符合数据主权要求

缺点：
❌ 地域数据不均匀
```

---

## 3. 分片算法

### 3.1 Range（范围）分片

**原理**：按字段范围划分

```java
// 订单ID范围分片
if (orderId >= 0 && orderId < 10000000) {
    return "order_0";
} else if (orderId >= 10000000 && orderId < 20000000) {
    return "order_1";
} else if (orderId >= 20000000 && orderId < 30000000) {
    return "order_2";
}
```

**优点**：
- ✅ 扩容方便（增加新范围）
- ✅ 范围查询不跨片

**缺点**：
- ❌ 数据分布不均匀
- ❌ 最新数据压力大

**适用场景**：
- 按时间拆分（历史数据归档）
- 数据增长可预测

### 3.2 Hash（哈希）分片

**取模分片**：
```java
// 用户ID取模分片（256张表）
int tableIndex = userId % 256;
String tableName = "order_" + tableIndex;

示例：
userId = 123456 → 123456 % 256 = 64 → order_64
userId = 789012 → 789012 % 256 = 148 → order_148
```

**优点**：
- ✅ 数据分布均匀
- ✅ 实现简单

**缺点**：
- ❌ 扩容困难（需要重新Hash）
- ❌ 范围查询需要全表扫描

**适用场景**：
- 数据分布均匀
- 主键查询为主

### 3.3 一致性Hash

**原理**：Hash环

```
Hash环（0 ~ 2^32-1）：
                 0
           ┌─────────┐
      DB3 │         │ DB0
          │         │
    2^30  │  Hash   │  2^30
          │  环     │
      DB2 │         │ DB1
           └─────────┘
                2^31

用户ID Hash到环上：
userId = 123456
hash(123456) = 123456789 → 落在DB1
```

**虚拟节点**：
```
每个物理节点对应多个虚拟节点（提升均匀性）

DB0 → [DB0-0, DB0-1, ..., DB0-99]
DB1 → [DB1-0, DB1-1, ..., DB1-99]
DB2 → [DB2-0, DB2-1, ..., DB2-99]
DB3 → [DB3-0, DB3-1, ..., DB3-99]
```

**Java实现**：
```java
public class ConsistentHash {
    
    private final SortedMap<Long, String> virtualNodes = new TreeMap<>();
    private final int virtualNodeCount = 100;
    
    public void addNode(String node) {
        for (int i = 0; i < virtualNodeCount; i++) {
            long hash = hash(node + "#" + i);
            virtualNodes.put(hash, node);
        }
    }
    
    public String getNode(long key) {
        long hash = hash(key);
        SortedMap<Long, String> tailMap = virtualNodes.tailMap(hash);
        
        if (tailMap.isEmpty()) {
            return virtualNodes.get(virtualNodes.firstKey());
        }
        return tailMap.get(tailMap.firstKey());
    }
    
    private long hash(Object key) {
        return Hashing.murmur3_32().hashString(
            key.toString(), StandardCharsets.UTF_8
        ).asInt() & 0xFFFFFFFFL;
    }
}
```

**优点**：
- ✅ 扩容时只影响部分数据
- ✅ 数据分布相对均匀

**缺点**：
- ❌ 实现复杂
- ❌ 范围查询需要全表扫描

### 3.4 自定义分片

**多维度分片**：
```java
public class CustomShardingAlgorithm implements PreciseShardingAlgorithm<Long> {
    
    @Override
    public String doSharding(Collection<String> availableTargetNames, 
                             PreciseShardingValue<Long> shardingValue) {
        Long userId = shardingValue.getValue();
        
        // 1. 大V用户单独分片
        if (isVip(userId)) {
            return "order_vip";
        }
        
        // 2. 普通用户Hash分片
        int tableIndex = (int) (userId % 256);
        return "order_" + tableIndex;
    }
    
    private boolean isVip(Long userId) {
        // 从Redis查询VIP用户
        return redisTemplate.opsForSet().isMember("vip:users", userId);
    }
}
```

---

## 4. Sharding-JDBC实战

### 4.1 简介

**Sharding-JDBC**：Apache ShardingSphere的JDBC实现

**特点**：
- ✅ **轻量级**：作为JDBC驱动，无需额外部署
- ✅ **兼容性好**：兼容MySQL、PostgreSQL、Oracle等
- ✅ **无侵入**：业务代码无感知
- ✅ **性能高**：无中间层，直连数据库

**架构**：
```
应用
  │
  ▼
Sharding-JDBC (SQL路由)
  │
  ├──→ DB0 → order_0_0, order_0_1, ...
  ├──→ DB1 → order_1_0, order_1_1, ...
  └──→ DB2 → order_2_0, order_2_1, ...
```

### 4.2 快速开始

**依赖**：
```xml
<dependency>
    <groupId>org.apache.shardingsphere</groupId>
    <artifactId>shardingsphere-jdbc-core-spring-boot-starter</artifactId>
    <version>5.3.0</version>
</dependency>
```

**配置**：
```yaml
spring:
  shardingsphere:
    # 数据源配置
    datasource:
      names: ds0, ds1, ds2, ds3
      
      ds0:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/order_db_0
        username: root
        password: 123456
      
      ds1:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/order_db_1
        username: root
        password: 123456
      
      ds2:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/order_db_2
        username: root
        password: 123456
      
      ds3:
        type: com.zaxxer.hikari.HikariDataSource
        driver-class-name: com.mysql.cj.jdbc.Driver
        jdbc-url: jdbc:mysql://localhost:3306/order_db_3
        username: root
        password: 123456
    
    # 分片规则
    rules:
      sharding:
        tables:
          # 订单表
          t_order:
            actual-data-nodes: ds$->{0..3}.t_order_$->{0..255}
            
            # 分库策略
            database-strategy:
              standard:
                sharding-column: user_id
                sharding-algorithm-name: database-inline
            
            # 分表策略
            table-strategy:
              standard:
                sharding-column: user_id
                sharding-algorithm-name: table-inline
            
            # 主键生成策略
            key-generate-strategy:
              column: order_id
              key-generator-name: snowflake
        
        # 分片算法
        sharding-algorithms:
          # 分库算法
          database-inline:
            type: INLINE
            props:
              algorithm-expression: ds$->{user_id % 4}
          
          # 分表算法
          table-inline:
            type: INLINE
            props:
              algorithm-expression: t_order_$->{user_id % 256}
        
        # 主键生成器
        key-generators:
          snowflake:
            type: SNOWFLAKE
            props:
              worker-id: 1
    
    # 属性配置
    props:
      sql-show: true  # 打印SQL
```

### 4.3 代码示例

**实体类**：
```java
@Data
@TableName("t_order")
public class Order {
    private Long orderId;    // 分布式ID
    private Long userId;     // 分片键
    private Long productId;
    private BigDecimal amount;
    private LocalDateTime createTime;
}
```

**Mapper**：
```java
@Mapper
public interface OrderMapper extends BaseMapper<Order> {
    
    // 根据用户ID查询（单库单表）
    List<Order> selectByUserId(@Param("userId") Long userId);
    
    // 范围查询（可能跨库跨表）
    List<Order> selectByUserIdRange(@Param("start") Long start, 
                                     @Param("end") Long end);
}
```

**Service**：
```java
@Service
public class OrderService {
    
    @Autowired
    private OrderMapper orderMapper;
    
    // 插入订单（自动路由到对应分片）
    public void createOrder(Order order) {
        orderMapper.insert(order);
        // SQL: INSERT INTO t_order_64 (user_id=123456 % 256=64)
    }
    
    // 查询订单（自动路由）
    public List<Order> getByUserId(Long userId) {
        return orderMapper.selectByUserId(userId);
        // SQL: SELECT * FROM t_order_64 WHERE user_id = 123456
    }
    
    // 范围查询（全表扫描）
    public List<Order> getByUserIdRange(Long start, Long end) {
        return orderMapper.selectByUserIdRange(start, end);
        // SQL: SELECT * FROM t_order_0,t_order_1,...,t_order_255 
        //      WHERE user_id BETWEEN start AND end
    }
}
```

### 4.4 SQL路由原理

**单表查询**：
```sql
-- 原始SQL
SELECT * FROM t_order WHERE user_id = 123456;

-- Sharding-JDBC路由
1. 解析SQL，提取分片键：user_id = 123456
2. 计算分库：123456 % 4 = 0 → ds0
3. 计算分表：123456 % 256 = 64 → t_order_64
4. 路由到：ds0.t_order_64
5. 执行SQL：SELECT * FROM t_order_64 WHERE user_id = 123456
```

**范围查询**：
```sql
-- 原始SQL
SELECT * FROM t_order WHERE user_id BETWEEN 1 AND 1000;

-- Sharding-JDBC路由
1. 无法精确路由（分片键是范围）
2. 广播到所有分片：
   ds0: t_order_0 ~ t_order_255
   ds1: t_order_0 ~ t_order_255
   ds2: t_order_0 ~ t_order_255
   ds3: t_order_0 ~ t_order_255
3. 合并结果
```

**聚合查询**：
```sql
-- 原始SQL
SELECT COUNT(*) FROM t_order WHERE user_id BETWEEN 1 AND 1000;

-- Sharding-JDBC路由
1. 广播到所有分片
2. 每个分片返回count
3. Sharding-JDBC合并：sum(count1, count2, ...)
```

### 4.5 读写分离

**配置**：
```yaml
spring:
  shardingsphere:
    datasource:
      names: master0, slave0-0, slave0-1
      
      master0:
        jdbc-url: jdbc:mysql://master:3306/order_db_0
      
      slave0-0:
        jdbc-url: jdbc:mysql://slave1:3306/order_db_0
      
      slave0-1:
        jdbc-url: jdbc:mysql://slave2:3306/order_db_0
    
    rules:
      readwrite-splitting:
        data-sources:
          ds0:
            static-strategy:
              write-data-source-name: master0
              read-data-source-names: slave0-0, slave0-1
            load-balancer-name: round-robin
        
        load-balancers:
          round-robin:
            type: ROUND_ROBIN
```

**原理**：
```
写操作 → Master
读操作 → Slave（轮询）

@Transactional
public void updateOrder() {
    orderMapper.update(order);  → Master
    orderMapper.select(order);  → Master（事务内强制走主库）
}

public Order getOrder() {
    return orderMapper.select(order);  → Slave
}
```

---

## 5. 分布式ID

### 5.1 为什么需要分布式ID

**自增ID的问题**：
```
单库：AUTO_INCREMENT（没问题）

分库分表后：
ds0.t_order_0: id=1, 2, 3
ds1.t_order_0: id=1, 2, 3  ← ID冲突！
```

**分布式ID要求**：
- ✅ **全局唯一**
- ✅ **趋势递增**（利于索引）
- ✅ **高性能**（百万/秒）
- ✅ **高可用**

### 5.2 雪花算法（Snowflake）

**结构**（64位）：
```
0 - 0000000000 0000000000 0000000000 0000000000 0 - 00000 - 00000 - 000000000000
│   └─────────────── 41位时间戳 ──────────────┘   └5位─┘ └5位─┘ └─── 12位 ───┘
│                                                数据中心  机器ID   序列号
└─ 符号位（固定0）

字段说明：
- 时间戳：41位，精确到毫秒，可用69年
- 数据中心ID：5位，最多32个数据中心
- 机器ID：5位，每个数据中心最多32台机器
- 序列号：12位，每毫秒最多4096个ID
```

**吞吐量**：
```
单机：4096 * 1000 = 409万/秒
32个数据中心 × 32台机器 = 1024台
总吞吐量：409万 × 1024 ≈ 42亿/秒
```

**Java实现**：
```java
public class SnowflakeIdWorker {
    
    // 起始时间戳（2020-01-01）
    private final long twepoch = 1577808000000L;
    
    // 机器ID所占位数
    private final long workerIdBits = 5L;
    private final long datacenterIdBits = 5L;
    
    // 序列号所占位数
    private final long sequenceBits = 12L;
    
    // 最大值
    private final long maxWorkerId = -1L ^ (-1L << workerIdBits);  // 31
    private final long maxDatacenterId = -1L ^ (-1L << datacenterIdBits);  // 31
    
    // 位移
    private final long workerIdShift = sequenceBits;  // 12
    private final long datacenterIdShift = sequenceBits + workerIdBits;  // 17
    private final long timestampLeftShift = sequenceBits + workerIdBits + datacenterIdBits;  // 22
    
    // 序列号掩码
    private final long sequenceMask = -1L ^ (-1L << sequenceBits);  // 4095
    
    private long workerId;
    private long datacenterId;
    private long sequence = 0L;
    private long lastTimestamp = -1L;
    
    public SnowflakeIdWorker(long workerId, long datacenterId) {
        if (workerId > maxWorkerId || workerId < 0) {
            throw new IllegalArgumentException("worker Id错误");
        }
        if (datacenterId > maxDatacenterId || datacenterId < 0) {
            throw new IllegalArgumentException("datacenter Id错误");
        }
        this.workerId = workerId;
        this.datacenterId = datacenterId;
    }
    
    public synchronized long nextId() {
        long timestamp = timeGen();
        
        // 时钟回拨
        if (timestamp < lastTimestamp) {
            throw new RuntimeException("时钟回拨，拒绝生成ID");
        }
        
        // 同一毫秒内
        if (lastTimestamp == timestamp) {
            sequence = (sequence + 1) & sequenceMask;
            // 序列号溢出
            if (sequence == 0) {
                timestamp = tilNextMillis(lastTimestamp);
            }
        } else {
            sequence = 0L;
        }
        
        lastTimestamp = timestamp;
        
        // 组装ID
        return ((timestamp - twepoch) << timestampLeftShift)
                | (datacenterId << datacenterIdShift)
                | (workerId << workerIdShift)
                | sequence;
    }
    
    private long tilNextMillis(long lastTimestamp) {
        long timestamp = timeGen();
        while (timestamp <= lastTimestamp) {
            timestamp = timeGen();
        }
        return timestamp;
    }
    
    private long timeGen() {
        return System.currentTimeMillis();
    }
}
```

**Sharding-JDBC集成**：
```yaml
spring:
  shardingsphere:
    rules:
      sharding:
        key-generators:
          snowflake:
            type: SNOWFLAKE
            props:
              worker-id: 1  # 机器ID（需要唯一）
              max-vibration-offset: 1  # 最大容忍时钟回拨毫秒数
```

**使用**：
```java
@Data
@TableName("t_order")
public class Order {
    @TableId(type = IdType.ASSIGN_ID)  // MyBatis-Plus雪花算法
    private Long orderId;
    
    // 或者使用Sharding-JDBC
    // private Long orderId;  // 自动填充
}
```

### 5.3 数据库号段模式

**原理**：
```
数据库存储当前ID段：
┌──────────┬────────────┬────────────┐
│ biz_type │ max_id     │ step       │
├──────────┼────────────┼────────────┤
│ order    │ 1000       │ 1000       │
└──────────┴────────────┴────────────┘

应用启动时：
1. SELECT max_id FROM id_generator WHERE biz_type='order' FOR UPDATE
2. UPDATE id_generator SET max_id = max_id + step WHERE biz_type='order'
3. 缓存ID段：[1000, 2000)
4. 每次获取ID从缓存中取（无需访问DB）
5. ID段用完后再次获取新段
```

**实现**：
```java
@Component
public class SegmentIdGenerator {
    
    @Autowired
    private IdGeneratorMapper mapper;
    
    private long currentId;
    private long maxId;
    private final int step = 1000;
    
    public synchronized long nextId(String bizType) {
        if (currentId >= maxId) {
            // 获取新号段
            IdSegment segment = mapper.getAndIncrement(bizType, step);
            currentId = segment.getMaxId() - step;
            maxId = segment.getMaxId();
        }
        return ++currentId;
    }
}
```

**优点**：
- ✅ 简单易用
- ✅ 高性能（批量获取）

**缺点**：
- ❌ 依赖数据库
- ❌ ID不严格递增（分段跳跃）

### 5.4 Redis实现

**INCR方式**：
```java
public class RedisIdGenerator {
    
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    public long nextId(String bizType) {
        String key = "id:generator:" + bizType;
        return redisTemplate.opsForValue().increment(key);
    }
}
```

**Lua脚本（号段模式）**：
```lua
-- 获取号段
local key = KEYS[1]
local step = tonumber(ARGV[1])

local current = redis.call('GET', key)
if not current then
    current = 0
end

local max = current + step
redis.call('SET', key, max)

return {current, max}
```

**优点**：
- ✅ 高性能
- ✅ 集中管理

**缺点**：
- ❌ 依赖Redis
- ❌ 需要持久化

### 5.5 对比

| 方案 | 性能 | 可用性 | 趋势递增 | 部署复杂度 |
|------|------|--------|---------|-----------|
| **雪花算法** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | 低 |
| **数据库号段** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 中 |
| **Redis** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | 中 |
| **UUID** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | 低 |

**推荐**：雪花算法（高性能 + 趋势递增 + 简单）

---

## 6. 数据迁移

### 6.1 迁移方案

**方案1：停机迁移**
```
1. 停止应用
2. 导出数据
3. 导入新库
4. 切换配置
5. 启动应用

优点：简单可靠
缺点：需要停机（不可接受）
```

**方案2：双写迁移**（推荐）
```
阶段1：双写
应用 → 旧库（主）+ 新库（从）

阶段2：数据校验
对比旧库和新库数据

阶段3：切换读
应用 → 旧库（写）+ 新库（读）

阶段4：完全切换
应用 → 新库（读写）

阶段5：下线旧库
删除旧库
```

**方案3：灰度迁移**
```
1. 1%流量 → 新库
2. 5%流量 → 新库
3. 10%流量 → 新库
4. 50%流量 → 新库
5. 100%流量 → 新库
```

### 6.2 双写方案实现

**代码实现**：
```java
@Service
public class OrderService {
    
    @Autowired
    private OrderMapper oldOrderMapper;  // 旧库
    
    @Autowired
    private OrderMapper newOrderMapper;  // 新库
    
    @Value("${migration.phase}")
    private String phase;  // current, dual-write, dual-read, new
    
    public void createOrder(Order order) {
        switch (phase) {
            case "current":
                // 阶段1：只写旧库
                oldOrderMapper.insert(order);
                break;
                
            case "dual-write":
                // 阶段2：双写（旧库为主）
                oldOrderMapper.insert(order);
                try {
                    newOrderMapper.insert(order);
                } catch (Exception e) {
                    log.error("新库写入失败", e);
                    // 不影响主流程
                }
                break;
                
            case "dual-read":
                // 阶段3：写新库，双读校验
                newOrderMapper.insert(order);
                try {
                    oldOrderMapper.insert(order);
                } catch (Exception e) {
                    log.error("旧库写入失败", e);
                }
                break;
                
            case "new":
                // 阶段4：只写新库
                newOrderMapper.insert(order);
                break;
        }
    }
    
    public Order getOrder(Long orderId) {
        switch (phase) {
            case "current":
                return oldOrderMapper.selectById(orderId);
                
            case "dual-write":
                return oldOrderMapper.selectById(orderId);
                
            case "dual-read":
                // 双读校验
                Order oldOrder = oldOrderMapper.selectById(orderId);
                Order newOrder = newOrderMapper.selectById(orderId);
                
                // 异步校验数据一致性
                CompletableFuture.runAsync(() -> {
                    if (!Objects.equals(oldOrder, newOrder)) {
                        log.error("数据不一致: orderId={}", orderId);
                    }
                });
                
                return newOrder;  // 返回新库数据
                
            case "new":
                return newOrderMapper.selectById(orderId);
                
            default:
                throw new IllegalStateException("未知阶段: " + phase);
        }
    }
}
```

### 6.3 历史数据迁移

**工具**：
```bash
# 使用DataX
{
  "job": {
    "content": [{
      "reader": {
        "name": "mysqlreader",
        "parameter": {
          "username": "root",
          "password": "123456",
          "connection": [{
            "jdbcUrl": ["jdbc:mysql://old:3306/order_db"],
            "querySql": ["SELECT * FROM t_order WHERE id BETWEEN ? AND ?"]
          }]
        }
      },
      "writer": {
        "name": "mysqlwriter",
        "parameter": {
          "username": "root",
          "password": "123456",
          "connection": [{
            "jdbcUrl": "jdbc:mysql://new:3306/order_db_${user_id % 4}",
            "table": ["t_order_${user_id % 256}"]
          }]
        }
      }
    }]
  }
}
```

**分批迁移**：
```java
@Service
public class DataMigrationService {
    
    public void migrate() {
        long batchSize = 10000;
        long maxId = oldOrderMapper.selectMaxId();
        
        for (long offset = 0; offset < maxId; offset += batchSize) {
            List<Order> orders = oldOrderMapper.selectByIdRange(
                offset, offset + batchSize
            );
            
            for (Order order : orders) {
                try {
                    newOrderMapper.insert(order);
                } catch (DuplicateKeyException e) {
                    // 已存在，跳过
                    log.warn("订单已存在: orderId={}", order.getOrderId());
                }
            }
            
            log.info("已迁移: {} / {}", offset + batchSize, maxId);
        }
    }
}
```

---

## 7. 跨库查询

### 7.1 问题

**JOIN查询**：
```sql
-- 单库：
SELECT o.*, u.name 
FROM t_order o 
JOIN t_user u ON o.user_id = u.id;

-- 分库分表后：
t_order → 分散在ds0, ds1, ds2, ds3
t_user → 分散在user_ds0, user_ds1
→ 无法JOIN！
```

### 7.2 解决方案

**方案1：应用层JOIN**
```java
// 1. 查询订单
List<Order> orders = orderMapper.selectAll();

// 2. 提取用户ID
Set<Long> userIds = orders.stream()
    .map(Order::getUserId)
    .collect(Collectors.toSet());

// 3. 批量查询用户
Map<Long, User> userMap = userMapper.selectByIds(userIds)
    .stream()
    .collect(Collectors.toMap(User::getId, u -> u));

// 4. 组装数据
List<OrderVO> result = orders.stream()
    .map(order -> {
        OrderVO vo = new OrderVO(order);
        vo.setUser(userMap.get(order.getUserId()));
        return vo;
    })
    .collect(Collectors.toList());
```

**方案2：数据冗余**
```java
// 订单表冗余用户信息
@Data
public class Order {
    private Long orderId;
    private Long userId;
    private String userName;  // 冗余
    private String userPhone;  // 冗余
}

// 插入订单时同步冗余
public void createOrder(Order order) {
    User user = userService.getById(order.getUserId());
    order.setUserName(user.getName());
    order.setUserPhone(user.getPhone());
    orderMapper.insert(order);
}
```

**方案3：ES聚合**
```
MySQL → Binlog → Canal → ES

ES中存储宽表：
{
  "orderId": 123,
  "userId": 456,
  "userName": "张三",
  "userPhone": "138****1234",
  "productId": 789,
  "productName": "iPhone"
}

查询：直接查ES（支持复杂查询）
```

### 7.3 分页查询

**问题**：
```sql
-- 查询第2页（每页10条）
SELECT * FROM t_order ORDER BY create_time DESC LIMIT 10, 10;

-- 分库分表后：
ds0.t_order_0: 查询LIMIT 0, 20（前20条）
ds0.t_order_1: 查询LIMIT 0, 20
...
ds3.t_order_255: 查询LIMIT 0, 20

→ 总共查询：256 * 20 = 5120条
→ 内存排序
→ 取第11-20条
```

**优化：禁止深分页**
```
限制：只允许查前100页
或：使用游标分页（上次最后一条ID）
```

**游标分页**：
```sql
-- 第一页
SELECT * FROM t_order WHERE id > 0 ORDER BY id LIMIT 10;
-- 返回：id=1~10

-- 第二页
SELECT * FROM t_order WHERE id > 10 ORDER BY id LIMIT 10;
-- 返回：id=11~20
```

---

## 8. 分布式事务

### 8.1 问题

**跨库事务**：
```java
@Transactional
public void createOrder(Order order) {
    // DB0
    orderMapper.insert(order);
    
    // DB1
    inventoryMapper.deduct(order.getProductId(), order.getQuantity());
    
    → 无法保证原子性！
}
```

### 8.2 Seata AT模式

**依赖**：
```xml
<dependency>
    <groupId>io.seata</groupId>
    <artifactId>seata-spring-boot-starter</artifactId>
    <version>1.6.0</version>
</dependency>
```

**配置**：
```yaml
seata:
  application-id: order-service
  tx-service-group: default_tx_group
  registry:
    type: nacos
    nacos:
      server-addr: 127.0.0.1:8848
      group: SEATA_GROUP
  config:
    type: nacos
    nacos:
      server-addr: 127.0.0.1:8848
      group: SEATA_GROUP
```

**使用**：
```java
@Service
public class OrderService {
    
    @Autowired
    private OrderMapper orderMapper;
    
    @Autowired
    private InventoryClient inventoryClient;
    
    @GlobalTransactional  // Seata全局事务
    public void createOrder(Order order) {
        // 1. 插入订单
        orderMapper.insert(order);
        
        // 2. 扣减库存（跨库）
        inventoryClient.deduct(order.getProductId(), order.getQuantity());
        
        // 3. 发生异常，自动回滚
        if (order.getAmount().compareTo(new BigDecimal("10000")) > 0) {
            throw new RuntimeException("金额超限");
        }
    }
}
```

**原理**：
```
1. 开启全局事务
2. 各分支执行（记录undo_log）
3. 提交阶段：
   - 成功：删除undo_log
   - 失败：根据undo_log回滚
```

### 8.3 TCC模式

**接口定义**：
```java
@LocalTCC
public interface InventoryService {
    
    @TwoPhaseBusinessAction(name = "deduct", commitMethod = "commit", rollbackMethod = "rollback")
    boolean deduct(@BusinessActionContextParameter(paramName = "productId") Long productId,
                   @BusinessActionContextParameter(paramName = "quantity") Integer quantity);
    
    boolean commit(BusinessActionContext context);
    
    boolean rollback(BusinessActionContext context);
}
```

**实现**：
```java
@Service
public class InventoryServiceImpl implements InventoryService {
    
    @Override
    public boolean deduct(Long productId, Integer quantity) {
        // Try：冻结库存
        inventoryMapper.freeze(productId, quantity);
        return true;
    }
    
    @Override
    public boolean commit(BusinessActionContext context) {
        // Confirm：扣减冻结库存
        Long productId = context.getActionContext("productId", Long.class);
        Integer quantity = context.getActionContext("quantity", Integer.class);
        inventoryMapper.deductFrozen(productId, quantity);
        return true;
    }
    
    @Override
    public boolean rollback(BusinessActionContext context) {
        // Cancel：释放冻结库存
        Long productId = context.getActionContext("productId", Long.class);
        Integer quantity = context.getActionContext("quantity", Integer.class);
        inventoryMapper.unfreeze(productId, quantity);
        return true;
    }
}
```

---

## 9. 扩容缩容

### 9.1 扩容方案

**水平扩容（增加库）**：
```
原：4个库（ds0 ~ ds3）
扩容：8个库（ds0 ~ ds7）

问题：
userId=123456 % 4 = 0 → ds0
userId=123456 % 8 = 0 → ds0（不变，OK）

userId=123457 % 4 = 1 → ds1
userId=123457 % 8 = 1 → ds1（不变，OK）

userId=123458 % 4 = 2 → ds2
userId=123458 % 8 = 2 → ds2（不变，OK）

但：
userId=123460 % 4 = 0 → ds0
userId=123460 % 8 = 4 → ds4（变了，需要迁移）

结论：2^N倍扩容，50%数据需要迁移
```

**解决：2倍扩容 + 一致性Hash**

**垂直扩容（增加表）**：
```
原：256张表（t_order_0 ~ t_order_255）
扩容：512张表（t_order_0 ~ t_order_511）

问题：所有数据需要重新Hash（不推荐）
```

### 9.2 缩容方案

**场景**：业务量下降，节省成本

**方案**：
```
8个库 → 4个库

迁移：
ds4 → ds0
ds5 → ds1
ds6 → ds2
ds7 → ds3

步骤：
1. 双写（ds4 + ds0）
2. 迁移历史数据（ds4 → ds0）
3. 切换读（ds0）
4. 下线ds4
```

---

## 10. 实战案例

### 10.1 从单库到1024分片

**业务背景**：
- 订单表：每天100万订单
- 保留3年：1亿+订单
- 单表性能下降

**拆分方案**：
```
4个库 × 256张表 = 1024个分片

分片键：user_id

分库：user_id % 4
分表：user_id % 256

单分片数据量：1亿 / 1024 ≈ 10万（合理）
```

**配置**：
```yaml
spring:
  shardingsphere:
    datasource:
      names: ds0, ds1, ds2, ds3
    
    rules:
      sharding:
        tables:
          t_order:
            actual-data-nodes: ds$->{0..3}.t_order_$->{0..255}
            
            database-strategy:
              standard:
                sharding-column: user_id
                sharding-algorithm-name: db-mod
            
            table-strategy:
              standard:
                sharding-column: user_id
                sharding-algorithm-name: table-mod
        
        sharding-algorithms:
          db-mod:
            type: MOD
            props:
              sharding-count: 4
          
          table-mod:
            type: MOD
            props:
              sharding-count: 256
```

**性能对比**：
```
单库单表：
- 数据量：1亿
- 查询P99：2秒
- 写入TPS：500

分库分表后：
- 单分片数据量：10万
- 查询P99：50ms
- 写入TPS：20000
```

### 10.2 电商订单分库分表

**架构**：
```
订单服务
  │
  ├─ 订单主表（t_order）
  │   分片键：user_id
  │   4库 × 256表
  │
  ├─ 订单详情表（t_order_detail）
  │   分片键：order_id
  │   绑定表（与订单主表绑定）
  │
  └─ 订单快照表（t_order_snapshot）
      单表（ES聚合查询）
```

**绑定表配置**：
```yaml
spring:
  shardingsphere:
    rules:
      sharding:
        tables:
          t_order:
            actual-data-nodes: ds$->{0..3}.t_order_$->{0..255}
          
          t_order_detail:
            actual-data-nodes: ds$->{0..3}.t_order_detail_$->{0..255}
        
        binding-tables:
          - t_order, t_order_detail  # 绑定表（相同分片策略）
```

**效果**：
```sql
-- JOIN查询不跨库
SELECT o.*, d.* 
FROM t_order o 
JOIN t_order_detail d ON o.order_id = d.order_id
WHERE o.user_id = 123456;

→ 路由到同一分片：ds0.t_order_64 JOIN ds0.t_order_detail_64
```

---

## 🎯 总结

### 核心要点

**拆分策略**：
- ✅ 垂直拆分：业务隔离、微服务化
- ✅ 水平拆分：数据分散、性能提升

**分片算法**：
- ✅ Range：范围查询友好，数据倾斜
- ✅ Hash：分布均匀，扩容困难
- ✅ 一致性Hash：扩容友好，实现复杂

**核心问题**：
- ✅ 分布式ID：雪花算法（推荐）
- ✅ 数据迁移：双写方案
- ✅ 跨库查询：冗余、ES、应用层JOIN
- ✅ 分布式事务：Seata AT/TCC

### 面试高频

1. **什么时候需要分库分表**？
   - 单表 > 500万、单库 > 2000万
   - 查询变慢、写入TPS下降

2. **分片键如何选择**？
   - 用户ID（推荐）：负载均匀、同用户数据不跨库
   - 时间：冷热分离、最新数据压力大

3. **如何解决分布式ID**？
   - 雪花算法（高性能、趋势递增）

4. **如何进行数据迁移**？
   - 双写方案（不停机）

5. **如何解决跨库查询**？
   - 数据冗余、ES、应用层JOIN

### 最佳实践

1. **分片数量**：
   - 库：2^N倍（2、4、8、16）
   - 表：256、512、1024

2. **分片键**：
   - 优先用户ID
   - 避免热点数据

3. **ID生成**：
   - 雪花算法（推荐）

4. **迁移方案**：
   - 双写 + 灰度

5. **监控告警**：
   - 单表数据量
   - 慢查询
   - 跨库查询比例

---

*最后更新：2025-10-27*  
*文档状态：v1.0 完成*  
*作者：技术知识库团队*

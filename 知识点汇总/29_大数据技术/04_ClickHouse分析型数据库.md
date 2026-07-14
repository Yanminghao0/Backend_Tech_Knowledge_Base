# ClickHouse分析型数据库

> 列式存储、MergeTree引擎、物化视图、分布式表与OLAP实时分析

---

## 📋 目录

1. [ClickHouse概述](#1-clickhouse概述)
2. [列式存储原理](#2-列式存储原理)
3. [MergeTree引擎家族](#3-mergetree引擎家族)
4. [物化视图](#4-物化视图)
5. [分布式架构](#5-分布式架构)
6. [Java集成实战](#6-java集成实战)
7. [面试题速查](#7-面试题速查)

---

## 1. ClickHouse概述

```
ClickHouse — 开源列式OLAP数据库(俄罗斯Yandex开发)

  ┌──────────────────────────────────────────────────┐
  │  特性                  │  说明                    │
  │  ──────────           │  ──────                  │
  │  列式存储              │  按列存，高压缩比         │
  │  向量化执行            │  SIMD批量处理             │
  │  实时写入              │  支持高吞吐写入           │
  │  SQL支持               │  标准SQL + 扩展函数       │
  │  实时查询              │  亿级数据秒级聚合         │
  │  分布式                │  分片+复制                │
  │  PB级                  │  支持PB级数据分析         │
  └──────────────────────────────────────────────────┘

ClickHouse vs MySQL vs HBase:

  维度        ClickHouse    MySQL       HBase
  ────────    ──────────    ──────      ─────
  存储方式    列式           行式        列族(行式)
  查询类型    OLAP聚合       OLTP事务    KV查询
  写入        批量写入好     单行写好    单行写好
  查询        聚合极快       点查快      点查极快
  事务        不支持         ACID        单行ACID
  JOIN        弱(大表JOIN差) 强          不支持
  数据量      PB级           GB~TB       TB级
  场景        实时分析        业务系统    在线服务
```

```xml
<!-- Maven依赖 -->
<dependency>
    <groupId>com.clickhouse</groupId>
    <artifactId>clickhouse-jdbc</artifactId>
    <version>0.6.0</version>
</dependency>
```

---

## 2. 列式存储原理

### 2.1 行式 vs 列式

```
行式存储(MySQL):
  数据按行存储，一行所有列连续存放

  Row1: [id=1, name="Alice", age=25, city="Beijing"]
  Row2: [id=2, name="Bob",   age=30, city="Shanghai"]
  Row3: [id=3, name="Carol", age=28, city="Guangzhou"]

  磁盘: |Row1|Row2|Row3|
  查SELECT age FROM users → 读取所有行，只取age列(浪费IO)

列式存储(ClickHouse):
  数据按列存储，每列单独存放

  id:   [1, 2, 3]
  name: ["Alice", "Bob", "Carol"]
  age:  [25, 30, 28]
  city: ["Beijing", "Shanghai", "Guangzhou"]

  磁盘: |id|name|age|city|
  查SELECT age FROM users → 只读age列(高效)
  查SELECT COUNT(*) FROM users → 用列存元数据(极快)
```

### 2.2 压缩

```
列式存储压缩优势:

  同列数据类型一致 → 压缩率极高
  age: [25, 25, 30, 28, 25, 30, 25] → RLE: 25x3, 30x1, 28x1, 30x1, 25x1
  city: ["Beijing", "Beijing", "Shanghai"] → 字典编码: 0, 0, 1

  ClickHouse压缩算法:
    LZ4    — 默认，速度快(500MB/s)
    ZSTD   — 压缩率高(但慢一点)
    Delta  — 差值编码(时间序列数据)

  压缩比: 通常5-10倍
  原始10TB数据 → ClickHouse存储约1-2TB
```

---

## 3. MergeTree引擎家族

### 3.1 MergeTree(基础引擎)

```sql
-- 创建MergeTree表
CREATE TABLE user_action (
    user_id UInt64,
    action String,
    amount Decimal(10,2),
    event_time DateTime,
    dt Date  -- 分区字段
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(dt)  -- 按月分区
ORDER BY (user_id, event_time)  -- 排序键(也是主键)
SETTINGS index_granularity = 8192;  -- 索引粒度

-- MergeTree特点:
-- 1. 按ORDER BY排序存储
-- 2. 数据分Part存储，后台合并
-- 3. 支持稀疏索引(每8192行一个索引)
-- 4. 支持分区剪裁
```

### 3.2 ReplacingMergeTree

```sql
-- ReplacingMergeTree — 去重(按ORDER BY键去重)
CREATE TABLE user_info (
    user_id UInt64,
    name String,
    phone String,
    update_time DateTime
) ENGINE = ReplacingMergeTree(update_time)  -- 保留update_time最大的
ORDER BY user_id;

-- 注意: 去重只在合并时发生，不保证实时
-- 查询时需要FINAL关键字强制去重:
SELECT * FROM user_info FINAL WHERE user_id = 1001;
-- FINAL性能差，生产中常用视图或聚合替代
```

### 3.3 SummingMergeTree

```sql
-- SummingMergeTree — 预聚合(自动SUM)
CREATE TABLE order_stats (
    dt Date,
    user_id UInt64,
    city String,
    order_count UInt32,
    total_amount Decimal(10,2)
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(dt)
ORDER BY (dt, user_id, city);

-- 合并时对相同ORDER BY键的行，数值列自动SUM
-- 非数值列取第一行
-- 查询时仍需SUM()聚合(合并是异步的):
SELECT dt, user_id, SUM(order_count), SUM(total_amount)
FROM order_stats
WHERE dt = '2026-07-13'
GROUP BY dt, user_id;
```

### 3.4 AggregatingMergeTree

```sql
-- AggregatingMergeTree — 更灵活的预聚合
CREATE TABLE uv_stats (
    dt Date,
    page String,
    uv AggregateFunction(uniq, UInt64),    -- UV去重
    pv AggregateFunction(sum, UInt32)      -- PV累加
) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(dt)
ORDER BY (dt, page);

-- 插入时使用聚合函数
INSERT INTO uv_stats
SELECT
    dt,
    page,
    uniqState(user_id) AS uv,  -- uniqState生成AggregateFunction
    sumState(pv) AS pv
FROM raw_log
WHERE dt = '2026-07-13'
GROUP BY dt, page;

-- 查询时用对应的Merge后缀函数
SELECT
    dt,
    page,
    uniqMerge(uv) AS uv,   -- uniqMerge解 AggregateFunction
    sumMerge(pv) AS pv
FROM uv_stats
WHERE dt = '2026-07-13'
GROUP BY dt, page;
```

### 3.5 CollapsingMergeTree

```sql
-- CollapsingMergeTree — 折叠(用sign标记插入/删除)
CREATE TABLE user_balance (
    user_id UInt64,
    balance Decimal(10,2),
    sign Int8  -- 1=插入, -1=取消
) ENGINE = CollapsingMergeTree(sign)
ORDER BY user_id;

-- 场景: 数据修正
-- 先插入: (1001, 100.00, 1)
-- 发现错误，取消: (1001, 100.00, -1)
-- 再插入正确值: (1001, 200.00, 1)
-- 合并后: (1001, 200.00)  — 正负抵消

-- 查询:
SELECT user_id, SUM(balance * sign) AS balance
FROM user_balance
GROUP BY user_id;
```

---

## 4. 物化视图

```sql
-- 物化视图 — 自动预聚合，写入时触发

-- 原始表
CREATE TABLE raw_events (
    dt Date,
    event_time DateTime,
    user_id UInt64,
    event_type String,
    city String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(dt)
ORDER BY (event_time, user_id);

-- 物化视图: 按天+城市聚合UV/PV
CREATE MATERIALIZED VIEW mv_daily_city
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(dt)
ORDER BY (dt, city)
AS SELECT
    dt,
    city,
    count() AS pv,
    uniqState(user_id) AS uv_state  -- 使用AggregateFunction
FROM raw_events
GROUP BY dt, city;

-- 插入原始数据时，物化视图自动更新
INSERT INTO raw_events VALUES
    ('2026-07-13', '2026-07-13 10:00:00', 1001, 'click', 'Beijing'),
    ('2026-07-13', '2026-07-13 10:01:00', 1002, 'click', 'Beijing'),
    ('2026-07-13', '2026-07-13 10:02:00', 1001, 'view', 'Shanghai');

-- 查询物化视图(极快)
SELECT dt, city, pv, uniqMerge(uv_state) AS uv
FROM mv_daily_city
WHERE dt = '2026-07-13'
GROUP BY dt, city, pv
ORDER BY pv DESC;
```

---

## 5. 分布式架构

### 5.1 分片与复制

```
ClickHouse分布式架构:

  ┌──────────────────────────────────────────────┐
  │              Distributed Table                │
  │         (逻辑表，路由查询到各分片)              │
  └───────┬──────────┬──────────┬───────────────┘
          ↓          ↓          ↓
     ┌────Shard1────┬────Shard2────┬────Shard3────┐
     │  Replica1   │  Replica1   │  Replica1   │
     │  Replica2   │  Replica2   │  Replica2   │
     └─────────────┴─────────────┴─────────────┘

  Shard(分片): 水平拆分数据
  Replica(副本): 同一分片的数据复制(高可用)

  分片策略:
    随机: rand()
    哈希: hash(user_id) % shard_count
    范围: 按日期/ID范围
```

```sql
-- 1. 在每个分片创建本地表
CREATE TABLE IF NOT EXISTS user_action_local ON CLUSTER cluster_name (
    user_id UInt64,
    action String,
    event_time DateTime,
    dt Date
) ENGINE = ReplicatedMergeTree(
    '/clickhouse/tables/{shard}/user_action_local',
    '{replica}'
)
PARTITION BY toYYYYMM(dt)
ORDER BY (user_id, event_time);

-- 2. 创建分布式表(逻辑表)
CREATE TABLE IF NOT EXISTS user_action ON CLUSTER cluster_name (
    user_id UInt64,
    action String,
    event_time DateTime,
    dt Date
) ENGINE = Distributed(
    cluster_name,       -- 集群名
    default,            -- 数据库
    user_action_local,  -- 本地表
    rand()              -- 分片键(可换hash(user_id))
);

-- 3. 写入分布式表(自动路由到分片)
INSERT INTO user_action VALUES
    (1001, 'click', '2026-07-13 10:00:00', '2026-07-13');

-- 4. 查询分布式表(自动并行扫描各分片)
SELECT action, count() FROM user_action
WHERE dt = '2026-07-13'
GROUP BY action;
```

### 5.2 集群配置

```xml
<!-- /etc/clickhouse-server/config.d/cluster.xml -->
<clickhouse>
    <remote_servers>
        <cluster_name>
            <shard>
                <internal_replication>true</internal_replication>
                <replica>
                    <host>ch-node-1</host>
                    <port>9000</port>
                </replica>
                <replica>
                    <host>ch-node-2</host>
                    <port>9000</port>
                </replica>
            </shard>
            <shard>
                <internal_replication>true</internal_replication>
                <replica>
                    <host>ch-node-3</host>
                    <port>9000</port>
                </replica>
                <replica>
                    <host>ch-node-4</host>
                    <port>9000</port>
                </replica>
            </shard>
        </cluster_name>
    </remote_servers>

    <zookeeper>
        <node>
            <host>zk-1</host>
            <port>2181</port>
        </node>
        <node>
            <host>zk-2</host>
            <port>2181</port>
        </node>
        <node>
            <host>zk-3</host>
            <port>2181</port>
        </node>
    </zookeeper>

    <macros>
        <shard>01</shard>
        <replica>ch-node-1</replica>
    </macros>
</clickhouse>
```

---

## 6. Java集成实战

```java
public class ClickHouseExample {

    private static Connection getConnection() throws SQLException {
        String url = "jdbc:ch://clickhouse-host:8123/default";
        Properties props = new Properties();
        props.setProperty("user", "default");
        props.setProperty("password", "password");
        return DriverManager.getConnection(url, props);
    }

    // 批量写入
    public static void batchInsert() throws SQLException {
        String sql = "INSERT INTO user_action " +
            "(user_id, action, amount, event_time, dt) VALUES (?, ?, ?, ?, ?)";

        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {

            for (int i = 0; i < 10000; i++) {
                ps.setLong(1, 1000 + i % 100);
                ps.setString(2, i % 3 == 0 ? "click" : "view");
                ps.setBigDecimal(3, BigDecimal.valueOf(Math.random() * 100));
                ps.setTimestamp(4, Timestamp.valueOf(
                    "2026-07-13 " + (10 + i % 12) + ":00:00"));
                ps.setDate(5, Date.valueOf("2026-07-13"));
                ps.addBatch();

                if (i % 1000 == 0) {
                    ps.executeBatch();
                }
            }
            ps.executeBatch();
        }
    }

    // 聚合查询
    public static void aggregateQuery() throws SQLException {
        String sql =
            "SELECT " +
            "  action, " +
            "  count() AS pv, " +
            "  uniq(user_id) AS uv, " +
            "  sum(amount) AS total_amount, " +
            "  avg(amount) AS avg_amount " +
            "FROM user_action " +
            "WHERE dt = '2026-07-13' " +
            "GROUP BY action " +
            "ORDER BY pv DESC";

        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(sql)) {

            while (rs.next()) {
                System.out.printf("%s: pv=%d uv=%d total=%.2f avg=%.2f%n",
                    rs.getString("action"),
                    rs.getLong("pv"),
                    rs.getLong("uv"),
                    rs.getBigDecimal("total_amount"),
                    rs.getBigDecimal("avg_amount")
                );
            }
        }
    }

    // 使用ClickHouse JDBC + Spring Boot
    // application.yml
    // spring:
    //   datasource:
    //     url: jdbc:ch://clickhouse:8123/default
    //     driver-class-name: com.clickhouse.jdbc.ClickHouseDriver
    //     username: default
    //     password: password
}
```

```
ClickHouse使用注意事项:

  1. 批量写入 — 不要单行写，至少1000行一批
  2. 避免高并发写 — 合并写入(缓冲表/异步)
  3. 不适合点查 — 用MySQL/HBase做点查
  4. JOIN弱 — 用物化视图预聚合代替JOIN
  5. 分区设计 — 按天/月分区，太细太多Part
  6. 排序键 — 常用过滤条件放前面
  7. 避免SELECT * — 只查需要的列
  8. 不支持事务 — OLAP场景不需要
```

---

## 7. 面试题速查

**Q1: ClickHouse为什么快？**

```
1. 列式存储 — 只读需要的列，减少IO
2. 高压缩比 — 同列同类型，LZ4/ZSTD压缩5-10倍
3. 向量化执行 — SIMD指令批量处理
4. 稀疏索引 — 每8192行一个索引，索引小常驻内存
5. 分区剪裁 — 只扫描相关分区
6. 并行处理 — 多线程+多分片并行扫描
```

**Q2: MergeTree引擎家族有哪些？**

```
MergeTree — 基础引擎，按ORDER BY排序
ReplacingMergeTree — 按ORDER BY去重
SummingMergeTree — 数值列自动SUM
AggregatingMergeTree — 自定义聚合函数
CollapsingMergeTree — sign标记正负抵消
```

**Q3: ClickHouse和MySQL的区别？**

```
ClickHouse: 列存，OLAP聚合快，不支持事务，不适合点查
MySQL: 行存，OLTP事务，点查快，聚合慢
选择: 实时分析用CH，业务系统用MySQL，经常混用
```

**Q4: ClickHouse的物化视图？**

```
自动维护的预聚合表，写入触发更新
本质是插入触发器 + 目标表
常用SummingMergeTree/AggregatingMergeTree做物化视图
查询物化视图替代查询原始表 → 极快
```

**Q5: ClickHouse分布式表原理？**

```
Distributed引擎 = 逻辑表，路由查询
写入: 按分片键路由到各分片本地表
查询: 并行发送到各分片，合并结果
ReplicatedMergeTree: 副本同步通过ZooKeeper
```

---

*最后更新：2026-07-13*

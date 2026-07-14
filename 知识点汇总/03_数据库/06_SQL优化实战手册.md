# SQL优化实战手册

> 从执行计划到索引策略，MySQL性能优化全链路实战指南

---

## 📋 目录

1. [执行计划详解](#1-执行计划详解)
2. [索引优化策略](#2-索引优化策略)
3. [SQL编写优化](#3-sql编写优化)
4. [慢查询分析](#4-慢查询分析)
5. [分页查询优化](#5-分页查询优化)
6. [JOIN优化](#6-join优化)
7. [面试要点](#7-面试要点)

---

## 1. 执行计划详解

### EXPLAIN关键字段

```sql
EXPLAIN SELECT * FROM orders WHERE user_id = 100 AND status = 'PAID';
```

| 字段 | 说明 | 关注点 |
|------|------|--------|
| id | 查询序号 | id相同从上往下执行，id不同先执行大ID |
| select_type | 查询类型 | SIMPLE/PRIMARY/SUBQUERY/DERIVED |
| table | 表名 | - |
| type | 访问类型 | **最关键**，性能从好到差 |
| possible_keys | 可能用到的索引 | - |
| key | 实际使用的索引 | NULL表示没走索引 |
| key_len | 索引使用长度 | 判断联合索引用了几个字段 |
| ref | 索引比较来源 | const/func/字段名 |
| rows | 预估扫描行数 | **越小越好** |
| Extra | 额外信息 | **重点关注** |

### type性能排序

```
性能从好到差：
  system > const > eq_ref > ref > range > index > ALL

const:  主键或唯一索引等值查询
  SELECT * FROM orders WHERE id = 1;

eq_ref: JOIN时被关联表用主键/唯一索引关联
  SELECT * FROM orders o JOIN users u ON o.user_id = u.id;

ref:    非唯一索引等值查询
  SELECT * FROM orders WHERE user_id = 100;

range:  索引范围查询
  SELECT * FROM orders WHERE id > 100;

index:  扫描整个索引树（不回表）
  SELECT COUNT(*) FROM orders;

ALL:    全表扫描（最差）
  SELECT * FROM orders WHERE status = 'PAID';  -- status无索引
```

### Extra关键字段

```
Using index:        覆盖索引，不回表 ✅
Using where:        需要回表过滤
Using temporary:    使用临时表 ⚠️
Using filesort:     文件排序 ⚠️（需优化）
Using join buffer:  JOIN无索引使用Buffer ⚠️
```

---

## 2. 索引优化策略

### 联合索引与最左前缀

```sql
-- 联合索引 (user_id, status, create_time)
-- 最左前缀原则：查询条件必须从索引最左列开始

-- ✅ 走索引
SELECT * FROM orders WHERE user_id = 100;
SELECT * FROM orders WHERE user_id = 100 AND status = 'PAID';
SELECT * FROM orders WHERE user_id = 100 AND status = 'PAID' AND create_time > '2026-01-01';

-- ⚠️ 部分走索引（只走user_id，跳过status后create_time不走索引）
SELECT * FROM orders WHERE user_id = 100 AND create_time > '2026-01-01';

-- ❌ 不走索引（跳过了user_id）
SELECT * FROM orders WHERE status = 'PAID';
SELECT * FROM orders WHERE create_time > '2026-01-01';

-- ❌ 不走索引（跳过了status）
SELECT * FROM orders WHERE user_id = 100 AND create_time > '2026-01-01';
-- 实际：走了user_id，但create_time未走索引（中间跳了status）
```

### 覆盖索引

```sql
-- 覆盖索引：查询字段都在索引中，不需要回表

-- 索引: idx_user_status (user_id, status)

-- ❌ 需要回表（查询了*）
SELECT * FROM orders WHERE user_id = 100;

-- ✅ 覆盖索引（只查索引字段）
SELECT user_id, status FROM orders WHERE user_id = 100;

-- ✅ 覆盖索引
SELECT COUNT(*) FROM orders WHERE user_id = 100;
```

### 索引失效场景

```sql
-- 1. 函数操作
-- ❌ 索引失效
SELECT * FROM orders WHERE DATE(create_time) = '2026-07-05';
-- ✅ 改为范围查询
SELECT * FROM orders WHERE create_time >= '2026-07-05' 
  AND create_time < '2026-07-06';

-- 2. 隐式类型转换
-- ❌ 字符串字段用数字查询（隐式转换导致索引失效）
SELECT * FROM orders WHERE order_no = 123456;        -- order_no是varchar
-- ✅ 用字符串查询
SELECT * FROM orders WHERE order_no = '123456';

-- 3. LIKE以通配符开头
-- ❌ 索引失效
SELECT * FROM products WHERE name LIKE '%手机%';
-- ✅ 后缀匹配走索引
SELECT * FROM products WHERE name LIKE '手机%';

-- 4. OR连接非索引列
-- ❌ 如果status没有索引，整个查询不走索引
SELECT * FROM orders WHERE user_id = 100 OR status = 'PAID';
-- ✅ 两者都有索引时可用UNION ALL
SELECT * FROM orders WHERE user_id = 100
UNION ALL
SELECT * FROM orders WHERE status = 'PAID' AND user_id != 100;

-- 5. NOT IN / NOT EXISTS
-- ❌ 通常不走索引
SELECT * FROM orders WHERE status NOT IN ('CANCELLED');
-- ✅ 改为IN
SELECT * FROM orders WHERE status IN ('PENDING', 'PAID', 'SHIPPED');

-- 6. 计算操作
-- ❌ 索引失效
SELECT * FROM orders WHERE user_id + 1 = 101;
-- ✅ 改为
SELECT * FROM orders WHERE user_id = 100;
```

### 索引设计原则

```
1. 区分度高的字段建索引（性别字段不适合，状态字段看情况）
2. 频繁查询的字段建索引
3. 联合索引顺序：等值条件在前，范围条件在后
4. 避免过多索引（每加一个索引，写入成本增加）
5. 单表索引数量建议不超过5个
6. 字符串字段考虑前缀索引
```

---

## 3. SQL编写优化

### 避免SELECT *

```sql
-- ❌ 查询所有列（浪费IO、无法用覆盖索引）
SELECT * FROM orders WHERE user_id = 100;

-- ✅ 只查需要的列
SELECT id, order_no, amount, status FROM orders WHERE user_id = 100;
```

### 批量操作

```sql
-- ❌ 循环单条插入
INSERT INTO logs (user_id, action) VALUES (1, 'login');
INSERT INTO logs (user_id, action) VALUES (2, 'login');
INSERT INTO logs (user_id, action) VALUES (3, 'login');

-- ✅ 批量插入
INSERT INTO logs (user_id, action) VALUES 
  (1, 'login'), (2, 'login'), (3, 'login');

-- ✅ MyBatis批量插入
INSERT INTO logs (user_id, action) VALUES
  <foreach collection="list" item="item" separator=",">
    (#{item.userId}, #{item.action})
  </foreach>
```

### 避免子查询

```sql
-- ❌ 子查询效率低（产生临时表）
SELECT * FROM orders 
WHERE user_id IN (SELECT id FROM users WHERE vip = 1);

-- ✅ 改为JOIN
SELECT o.* FROM orders o
INNER JOIN users u ON o.user_id = u.id
WHERE u.vip = 1;
```

### COUNT优化

```sql
-- ❌ COUNT(*) 全表扫描（无索引时）
SELECT COUNT(*) FROM orders WHERE status = 'PENDING';

-- ✅ 如果只需判断是否存在
SELECT EXISTS(SELECT 1 FROM orders WHERE status = 'PENDING' LIMIT 1);

-- ✅ 总数缓存到Redis
-- 定时更新 Redis count:orders:pending
```

---

## 4. 慢查询分析

### 开启慢查询日志

```sql
-- 查看慢查询配置
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- 开启慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;  -- 超过1秒记录
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- 记录不走索引的查询
SET GLOBAL log_queries_not_using_indexes = 'ON';
```

### 分析慢查询

```bash
# 使用mysqldumpslow分析
mysqldumpslow -s t -t 10 /var/log/mysql/slow.log

# 参数：
# -s t: 按时间排序
# -s c: 按次数排序
# -s r: 按返回行数排序
# -t 10: 显示前10条
```

### SHOW PROFILE

```sql
-- 开启Profile
SET profiling = 1;

-- 执行查询
SELECT * FROM orders WHERE user_id = 100;

-- 查看Profile
SHOW PROFILE;
-- 查看详细开销
SHOW PROFILE ALL FOR QUERY 1;
```

---

## 5. 分页查询优化

### 深分页问题

```sql
-- ❌ 深分页：LIMIT 1000000, 20
-- 扫描100万+20行，丢弃前100万行
SELECT * FROM orders ORDER BY id LIMIT 1000000, 20;

-- ✅ 方案1: 子查询优化（先查ID再关联）
SELECT * FROM orders o
INNER JOIN (SELECT id FROM orders ORDER BY id LIMIT 1000000, 20) t
ON o.id = t.id;

-- ✅ 方案2: 游标分页（记录上一页最后ID）
SELECT * FROM orders WHERE id > 1000000 ORDER BY id LIMIT 20;

-- ✅ 方案3: search_after（ES方式）
SELECT * FROM orders 
WHERE (create_time, id) < ('2026-07-05 10:00:00', 1000000)
ORDER BY create_time DESC, id DESC 
LIMIT 20;
```

### Java实现游标分页

```java
@RestController
public class OrderController {
    
    @GetMapping("/orders")
    public PageResult<Order> list(
            @RequestParam(required = false) Long lastId,
            @RequestParam(defaultValue = "20") int size) {
        
        LambdaQueryWrapper<Order> wrapper = new LambdaQueryWrapper<>();
        if (lastId != null) {
            wrapper.lt(Order::getId, lastId);  // 查询ID小于lastId的
        }
        wrapper.orderByDesc(Order::getId).last("LIMIT " + size);
        
        List<Order> orders = orderMapper.selectList(wrapper);
        return PageResult.of(orders, size);
    }
}
```

---

## 6. JOIN优化

### 驱动表选择

```sql
-- 小表驱动大表（MySQL优化器通常自动选择）

-- ✅ 小表JOIN大表
SELECT * FROM small_table s
INNER JOIN big_table b ON s.id = b.small_id
WHERE s.status = 'ACTIVE';

-- JOIN字段必须有索引
-- 被驱动表的关联字段必须有索引
ALTER TABLE big_table ADD INDEX idx_small_id (small_id);
```

### Nested Loop Join算法

```
MySQL JOIN算法：

1. Simple Nested Loop Join（基本算法）：
   for (r in 驱动表) {
     for (s in 被驱动表) {
       if (r.id == s.r_id) 返回结果
     }
   }
   → 效率最低，MySQL不使用

2. Index Nested Loop Join（索引关联）：
   被驱动表关联字段有索引
   for (r in 驱动表) {
     通过索引直接查找被驱动表 → O(1)
   }
   → 效率高，推荐

3. Block Nested Loop Join（块关联）：
   被驱动表无索引时使用
   把驱动表数据放入Join Buffer，批量匹配
   → 效率低，应避免
```

### Straight Join强制驱动表

```sql
-- 强制t1为驱动表（仅当优化器选择错误时使用）
SELECT STRAIGHT_JOIN * FROM t1 
INNER JOIN t2 ON t1.id = t2.t1_id;
```

---

## 7. 面试要点

### Q1: 索引失效的场景有哪些？

```
1. 对索引字段使用函数或计算
2. 隐式类型转换（字符串字段用数字查）
3. LIKE以%开头
4. OR连接中有非索引列
5. NOT IN / NOT EXISTS
6. 联合索引不满足最左前缀
7. 优化器认为全表扫描更快（小表或索引区分度低）
```

### Q2: 如何优化深分页？

```
方案1: 游标分页（记录上次最大ID，WHERE id > last_id）
方案2: 子查询（先查ID再JOIN回表）
方案3: 覆盖索引（只查索引列，不回表）
方案4: 业务限制（限制最大翻页数，如100页）
方案5: ES/Redis缓存（适合固定排序的分页）
```

### Q3: 联合索引(a,b,c)，以下查询哪些走索引？

```sql
WHERE a = 1                    -- ✅ 走a
WHERE a = 1 AND b = 2          -- ✅ 走a,b
WHERE a = 1 AND b = 2 AND c=3  -- ✅ 走a,b,c
WHERE b = 2                    -- ❌ 不走（跳过a）
WHERE a = 1 AND c = 3          -- ⚠️ 只走a（跳过b）
WHERE a > 1 AND b = 2          -- ⚠️ 只走a（范围后断）
WHERE a = 1 AND b > 2 AND c=3  -- ⚠️ 走a,b（b范围后c不走）
```

### Q4: 如何排查慢SQL？

```
1. 开启慢查询日志（slow_query_log）
2. 用mysqldumpslow分析Top N慢SQL
3. 用EXPLAIN分析执行计划
4. 检查：是否走索引、扫描行数、Extra信息
5. 优化：加索引、改SQL、改架构（缓存/分库分表）
6. 验证：EXPLAIN确认优化效果
```

### Q5: 覆盖索引和回表是什么？

```
回表：通过二级索引找到主键 → 再通过主键索引找到完整行数据
  二级索引 → 主键ID → 主键索引 → 完整数据

覆盖索引：查询的字段都在索引中，不需要回表
  二级索引(含查询字段) → 直接返回

覆盖索引性能高的原因：
  - 减少一次IO（不需要回表）
  - 索引体积小，缓存命中率高

示例：
  索引: idx_user_status (user_id, status)
  ✅ SELECT user_id, status FROM orders WHERE user_id = 1; -- 覆盖索引
  ❌ SELECT * FROM orders WHERE user_id = 1;               -- 需要回表
```

---

## 📚 相关阅读

- [04_MySQL核心机制详解](./04_MySQL核心机制详解.md)
- [03_MySQL查询核心机制详解](./03_MySQL查询核心机制详解.md)
- [02_MySQL分库分表实战](./02_MySQL分库分表实战.md)
- [性能监控与系统优化](../11_性能优化/02_性能监控与系统优化.md)

# MongoDB核心原理与实战

> 深入理解文档数据库的设计理念、查询优化与分布式架构

## 📋 目录

1. [MongoDB核心概念](#1-mongodb核心概念)
2. [数据模型设计](#2-数据模型设计)
3. [查询操作详解](#3-查询操作详解)
4. [索引机制](#4-索引机制)
5. [事务与并发控制](#5-事务与并发控制)
6. [分布式部署](#6-分布式部署)
7. [性能优化实践](#7-性能优化实践)
8. [与关系型数据库对比](#8-与关系型数据库对比)

---

## 1. MongoDB核心概念

### 1.1 数据模型

MongoDB采用文档模型存储数据，使用BSON（Binary JSON）格式：

```json
// 示例文档
{
  "_id": ObjectId("60d21b4667d0d8992e610c85"),
  "name": "MongoDB实战指南",
  "author": {
    "firstName": "张",
    "lastName": "三"
  },
  "tags": ["数据库", "NoSQL", "MongoDB"],
  "price": 79.0,
  "publicationDate": ISODate("2023-06-15T00:00:00Z"),
  "isAvailable": true,
  "ratings": [4.5, 5.0, 4.8]
}
```

### 1.2 核心组件

| 组件 | 说明 | 与MySQL对比 |
|------|------|------------|
| Database | 数据库 | Database |
| Collection | 集合（文档组） | Table |
| Document | 文档（数据记录） | Row |
| Field | 字段 | Column |
| Index | 索引 | Index |
| ObjectId | 文档唯一标识 | Primary Key |
| Embedded Document | 嵌入式文档 | Join查询结果 |
| Array | 数组类型 | 无直接对应 |

---

## 2. 数据模型设计

### 2.1 文档设计原则

1. **嵌入式文档适用场景**：
   - 一对一关系
   - 数据经常一起查询
   - 数据量不大

   ```json
   // 嵌入式设计示例
   {
     "_id": ObjectId("..."),
     "userName": "johndoe",
     "address": {
       "street": "Main St",
       "city": "Beijing",
       "zipCode": "100000"
     }
   }
   ```

2. **引用式设计适用场景**：
   - 一对多或多对多关系
   - 数据经常单独查询
   - 数据量大

   ```json
   // 用户集合
   {
     "_id": ObjectId("user1"),
     "name": "John Doe"
   }
   
   // 订单集合（引用用户）
   {
     "_id": ObjectId("order1"),
     "userId": ObjectId("user1"),
     "products": ["apple", "banana"]
   }
   ```

### 2.2 反范式设计

MongoDB鼓励适度反范式化以减少JOIN操作：

```json
// 反范式设计示例（订单包含产品详情）
{
  "_id": ObjectId("order1"),
  "userId": ObjectId("user1"),
  "items": [
    {
      "productId": ObjectId("prod1"),
      "name": "iPhone 15", // 冗余存储
      "price": 7999,       // 冗余存储
      "quantity": 1
    }
  ]
}
```

---

## 3. 查询操作详解

### 3.1 基础查询

```javascript
// 查询所有文档
db.products.find()

// 条件查询
db.products.find({ price: { $lt: 100 } })

// 投影（只返回指定字段）
db.products.find({ price: { $lt: 100 } }, { name: 1, price: 1, _id: 0 })

// 排序
db.products.find().sort({ price: 1 }) // 升序

db.products.find().sort({ price: -1 }) // 降序

// 分页
db.products.find().skip(10).limit(20)
```

### 3.2 高级查询操作

#### 数组查询

```javascript
// 匹配数组包含元素
db.products.find({ tags: "database" })

// 匹配数组所有元素
db.products.find({ ratings: { $all: [4.5, 5.0] } })

// 数组长度匹配
db.products.find({ tags: { $size: 3 } })
```

#### 聚合查询

```javascript
// 计算每个分类的平均价格
db.products.aggregate([
  { $group: { _id: "$category", avgPrice: { $avg: "$price" } } },
  { $sort: { avgPrice: -1 } }
])

// 关联查询（类似JOIN）

db.orders.aggregate([
  { $lookup: {
      from: "users",
      localField: "userId",
      foreignField: "_id",
      as: "userInfo"
    }
  },
  { $unwind: "$userInfo" },
  { $project: {
      orderId: "$_id",
      userName: "$userInfo.name",
      products: 1
    }
  }
])
```

---

## 4. 索引机制

### 4.1 索引类型

MongoDB支持多种索引类型：

```javascript
// 单字段索引
db.products.createIndex({ name: 1 })

// 复合索引
db.products.createIndex({ category: 1, price: -1 })

// 多键索引（用于数组）
db.products.createIndex({ tags: 1 })

// 地理空间索引
db.stores.createIndex({ location: "2dsphere" })

// 文本索引
db.articles.createIndex({ content: "text", title: "text" })

// 哈希索引（用于分片）
db.users.createIndex({ email: "hashed" })
```

### 4.2 索引优化

使用`explain()`分析查询性能：

```javascript
db.products.find({ category: "books", price: { $lt: 50 } })
  .sort({ publicationDate: -1 })
  .explain("executionStats")
```

**索引设计原则**：
- 最左前缀匹配原则
- 避免过度索引
- 考虑索引选择性
- 监控索引使用情况

---

## 5. 事务与并发控制

### 5.1 事务支持

MongoDB 4.0+支持多文档事务：

```javascript
// 事务示例
const session = db.getMongo().startSession();
session.startTransaction();

try {
  db.orders.insertOne({
    _id: "order1001",
    userId: "user123",
    total: 99.99
  }, { session });

  db.users.updateOne(
    { _id: "user123" },
    { $inc: { orderCount: 1 } },
    { session }
  );

  session.commitTransaction();
} catch (error) {
  session.abortTransaction();
  throw error;
} finally {
  session.endSession();
}
```

### 5.2 并发控制

MongoDB使用多版本并发控制（MVCC）：

- 读操作不阻塞写操作
- 写操作不阻塞读操作
- 支持读已提交（Read Committed）隔离级别

---

## 6. 分布式部署

### 6.1 副本集（Replica Set）

副本集提供高可用性和数据冗余：

```
[主节点(Primary)] ←→ [从节点(Secondary)] ←→ [仲裁节点(Arbiter)]
   ↑                        ↑
   └── 数据复制            └── 故障转移时参与投票
```

**部署命令**：
```bash
mongod --replSet rs0 --port 27017 --dbpath /data/db1
mongod --replSet rs0 --port 27018 --dbpath /data/db2
mongod --replSet rs0 --port 27019 --dbpath /data/db3

# 初始化副本集
rs.initiate({
  _id: "rs0",
  members: [
    {_id: 0, host: "localhost:27017"},
    {_id: 1, host: "localhost:27018"},
    {_id: 2, host: "localhost:27019", arbiterOnly: true}
  ]
})
```

### 6.2 分片集群（Sharded Cluster）

分片集群支持水平扩展：

```
[路由节点(Mongos)] → [分片节点(Shard)] → [副本集]
       ↑                   ↑
       └── 元数据节点(Config Server) ───┘
```

**分片策略**：
- 范围分片（Range-based）
- 哈希分片（Hash-based）
- 区域分片（Zone-based）

---

## 7. 性能优化实践

### 7.1 查询优化

- 创建合适的索引
- 使用投影减少数据传输
- 避免全集合扫描
- 限制返回文档数量

### 7.2 写入优化

- 使用批量写入（bulkWrite）
- 调整写入关注级别（Write Concern）
- 合理设置Journal提交间隔

### 7.3 内存优化

- 确保工作集（Working Set）适合内存
- 使用WiredTiger存储引擎的压缩功能
- 监控页面错误率

---

## 8. 与关系型数据库对比

| 特性 | MongoDB | MySQL |
|------|---------|-------|
| 数据模型 | 文档模型 | 关系模型 |
| 模式灵活性 | 动态模式 | 固定模式 |
| 查询语言 | MongoDB查询语言 | SQL |
| JOIN操作 | 有限支持（$lookup） | 原生支持 |
| 事务 | 支持多文档事务 | 完善的事务支持 |
| 扩展性 | 水平扩展友好 | 垂直扩展为主 |
| 适用场景 | 非结构化/半结构化数据 | 结构化数据 |

---

## 📚 参考资源

- [MongoDB官方文档](https://www.mongodb.com/docs/)
- [MongoDB University](https://learn.mongodb.com/)
- 《MongoDB权威指南》（O'Reilly）
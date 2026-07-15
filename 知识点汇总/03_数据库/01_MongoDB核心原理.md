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

---

## 9. WiredTiger存储引擎

自MongoDB 3.2起，WiredTiger成为默认存储引擎，相比早期的MMAPv1在性能与压缩率上均有显著提升。

### 9.1 核心特性

| 特性 | 说明 |
|------|------|
| 文档级并发控制 | 写操作只锁定文档本身，并发度远高于MMAPv1的集合级锁 |
| 闪存友好 | 针对SSD优化，使用B-tree + 缓存设计 |
| 数据压缩 | 支持Snappy（默认）、Zlib、Zstd压缩算法，节省约50%-80%存储空间 |
| Checkpoint机制 | 默认每60秒或日志达2GB时将内存脏页刷盘，保证持久性 |
| MVCC | 读取某一快照版本数据，读写互不阻塞 |

### 9.2 缓存与I/O模型

```
应用请求
   ↓
WiredTiger Cache（默认 (RAM-1GB)*50%，上限约几百MB～几GB）
   ├── 命中缓存 → 直接返回
   └── 未命中 → 从磁盘加载到缓存
        ↓
   数据文件（B-Tree）  +  Journal日志文件（WAL）
```

**关键参数**：

```yaml
# mongod.conf
storage:
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4          # 缓存大小，生产环境一般设为物理内存的50%-60%
      journalCompressor: snappy
    collectionConfig:
      blockCompressor: snappy # 集合数据压缩
    indexConfig:
      prefixCompression: true # 索引前缀压缩
```

### 9.3 Journal持久化

- 写操作先写入Journal日志（Write-Ahead Log），再异步刷盘到数据文件
- `j: true` 写关注保证Journal落盘后才返回成功，避免断电丢数据
- 默认`journalCommitInterval`为100ms，故障恢复最坏丢失100ms数据

---

## 10. 副本集选举原理

### 10.1 选举触发场景

- 副本集初始化
- Primary节点宕机或网络分区
- 人为执行`rs.stepDown()`主动降级
- 新节点加入或优先级调整

### 10.2 Raft协议实现

MongoDB副本集选举基于Raft协议变种，核心规则：

1. **多数派投票**：新Primary必须获得超过半数节点（N/2+1）赞成票
2. **优先级**：优先级高的节点更有可能被选为Primary（默认1，可设0-1000）
3. **选举任期（term）**：每次选举term递增，防止过期投票
4. **心跳检测**：成员间每2s互发心跳，超过10s未响应判定为失联

```javascript
// 调整优先级，让某节点更可能成为Primary
cfg = rs.conf()
cfg.members[0].priority = 2    // 节点0优先级提高
cfg.members[1].priority = 1
cfg.members[2].priority = 0    // 永不成为Primary（如隐藏节点）
rs.reconfig(cfg)

// 隐藏节点（只做数据备份，不接收读请求）
cfg.members[2].hidden = true
cfg.members[2].priority = 0
```

### 10.3 故障转移过程

```
Primary宕机
   ↓ (10s心跳超时)
从节点发起选举
   ↓
候选节点向其他从节点请求投票
   ↓
获得多数票(N/2+1) → 升级为Primary
   ↓
客户端自动重连新Primary（通过mongos或驱动层）
```

**选举耗时**：通常10-12秒，期间集群只读不可写。可配置`electionTimeoutMillis`调整心跳超时：

```javascript
cfg = rs.conf()
cfg.settings.electionTimeoutMillis = 5000  // 5秒超时，加快故障检测
rs.reconfig(cfg)
```

### 10.4 读关注与读偏好

```javascript
// 读偏好：将读请求路由到从节点
db.collection.find().readPref("secondaryPreferred")

// 读关注：保证读到已提交的数据
db.collection.find().readConcern("majority")
```

| 读偏好模式 | 说明 |
|-----------|------|
| primary（默认） | 只从主节点读 |
| primaryPreferred | 优先主节点，主不可用时读从节点 |
| secondary | 只读从节点 |
| secondaryPreferred | 优先从节点，分担主节点压力 |
| nearest | 读取网络延迟最低的节点 |

---

## 11. 分片集群深入

### 11.1 架构组件

```
                    客户端
                      ↓
                ┌──────────┐
                │  Mongos  │ ← 路由进程（可部署多个，无状态）
                └────┬─────┘
                     ↓
            ┌────────────────┐
            │ Config Server  │ ← 存储集群元数据（chunk分布、shard信息）
            └────────┬───────┘
                     ↓
   ┌─────────┬───────┴───────┬─────────┐
   ↓         ↓               ↓         ↓
Shard1      Shard2         Shard3    ShardN
(副本集)   (副本集)        (副本集)  (副本集)
```

### 11.2 分片键（Shard Key）

分片键决定了数据在shard间的分布，**选择后不可更改**（5.0+支持`reshardCollection`）：

```javascript
// 启用分片
sh.enableSharding("mydb")

// 对集合分片（必须先在分片键上建索引）
db.orders.createIndex({ userId: 1, createdAt: 1 })
sh.shardCollection("mydb.orders", { userId: 1, createdAt: 1 })

// 哈希分片（数据分布均匀，适合等值查询）
sh.shardCollection("mydb.users", { _id: "hashed" })
```

**分片键选择原则**：
- **基数高**：取值范围大，避免数据倾斜（如userId优于status）
- **写分布均匀**：避免热点，单调递增字段（如ObjectId）不适合范围分片
- **查询隔离**：常用查询条件应包含分片键，让mongos精准路由到单shard

### 11.3 Chunk与均衡器

- **Chunk**：数据逻辑分片单位，默认64MB（可调），超过阈值自动分裂
- **Balancer**：后台进程，自动迁移chunk使各shard数据量均衡
- 迁移过程对业务透明，通过`moveChunk`实现

```javascript
// 查看chunk分布
sh.status()

// 手动设置chunk大小
db.settings.save({ _id: "chunksize", value: 32 }) // 32MB

// 暂停均衡器（如批量导入时）
sh.stopBalancer()
sh.startBalancer()
```

### 11.4 分片策略对比

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 范围分片 | 范围查询多 | 范围查询高效 | 单调递增键易产生热点 |
| 哈希分片 | 等值查询、数据均匀 | 分布均匀无热点 | 范围查询需广播所有shard |
| 区域分片 | 数据本地化（如按地域） | 满足合规与低延迟 | 配置复杂 |

---

## 12. 索引类型详解与实战

### 12.1 单字段索引

```javascript
// 升序索引
db.products.createIndex({ price: 1 })

// 降序索引
db.products.createIndex({ createdAt: -1 })

// 查看索引
db.products.getIndexes()
```

适用场景：单字段等值查询或排序。

### 12.2 复合索引

```javascript
// 复合索引遵循ESR原则：Equality(等值) → Sort(排序) → Range(范围)
db.orders.createIndex({ status: 1, createdAt: -1, amount: 1 })

// 查询命中
db.orders.find({ status: "paid" })                          // ✅ 命中
db.orders.find({ status: "paid" }).sort({ createdAt: -1 })  // ✅ 命中
db.orders.find({ status: "paid", amount: { $gt: 100 } })    // ✅ 命中
db.orders.find({ amount: { $gt: 100 } })                    // ❌ 不命中（违反最左前缀）
```

**ESR规则**：复合索引字段顺序应遵循 **Equality → Sort → Range**，能最大化索引利用率。

### 12.3 文本索引

```javascript
// 创建文本索引（一个集合只能有一个文本索引）
db.articles.createIndex({ title: "text", content: "text" })

// 全文检索
db.articles.find({ $text: { $search: "MongoDB 索引优化" } })

// 按相关度排序
db.articles.find(
  { $text: { $search: "MongoDB" } },
  { score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } })

// 指定权重（title权重高于content）
db.articles.createIndex(
  { title: "text", content: "text" },
  { weights: { title: 10, content: 1 } }
)
```

### 12.4 地理空间索引

```javascript
// 2dsphere索引（支持GeoJSON点、线、面）
db.restaurants.createIndex({ location: "2dsphere" })

// 插入地理位置数据
db.restaurants.insertOne({
  name: "川菜馆",
  location: {
    type: "Point",
    coordinates: [116.404, 39.915]  // [经度, 纬度]
  }
})

// 查找附近3公里内的餐厅
db.restaurants.find({
  location: {
    $near: {
      $geometry: { type: "Point", coordinates: [116.404, 39.915] },
      $maxDistance: 3000  // 单位：米
    }
  }
})

// 2d索引（传统平面坐标，适合游戏地图等）
db.places.createIndex({ coords: "2d" })
```

---

## 13. 聚合管道实战

### 13.1 管道操作符速查

| 操作符 | 作用 | 类比SQL |
|--------|------|---------|
| `$match` | 过滤文档 | WHERE |
| `$group` | 分组聚合 | GROUP BY |
| `$project` | 字段投影 | SELECT |
| `$sort` | 排序 | ORDER BY |
| `$limit` / `$skip` | 分页 | LIMIT / OFFSET |
| `$lookup` | 关联查询 | LEFT JOIN |
| `$unwind` | 数组展开 | 无 |
| `$bucket` | 分桶统计 | 无 |
| `$facet` | 多管道并行 | 无 |

### 13.2 电商订单分析实战

场景：统计各品类月销售额Top3商品及用户复购率。

```javascript
db.orders.aggregate([
  // 1. 过滤已完成订单
  { $match: { status: "completed", createdAt: { $gte: ISODate("2024-01-01") } } },

  // 2. 展开商品数组
  { $unwind: "$items" },

  // 3. 关联商品集合获取品类
  {
    $lookup: {
      from: "products",
      localField: "items.productId",
      foreignField: "_id",
      as: "productInfo"
    }
  },
  { $unwind: "$productInfo" },

  // 4. 按品类+商品分组，计算销售额
  {
    $group: {
      _id: {
        category: "$productInfo.category",
        productId: "$items.productId",
        productName: "$items.name"
      },
      totalSales: { $sum: { $multiply: ["$items.price", "$items.quantity"] } },
      orderCount: { $sum: 1 }
    }
  },

  // 5. 按品类分组，取销售额Top3
  {
    $group: {
      _id: "$_id.category",
      topProducts: {
        $push: {
          productId: "$_id.productId",
          productName: "$_id.productName",
          totalSales: "$totalSales"
        }
      }
    }
  },
  {
    $project: {
      category: "$_id",
      topProducts: { $slice: [{ $sortArray: { input: "$topProducts", sortBy: { totalSales: -1 } } }, 3] }
    }
  },

  // 6. 排序输出
  { $sort: { "topProducts.totalSales": -1 } }
], { allowDiskUse: true })  // 大数据集允许落盘
```

### 13.3 优化建议

- **`$match`前置**：尽早过滤，减少后续管道处理数据量
- **索引利用**：`$match`和`$sort`能命中索引
- **`$project`减少字段**：降低中间文档体积
- **`allowDiskUse: true`**：单阶段超过100MB内存限制时启用
- **`$facet`一次多维度聚合**：避免多次全表扫描

---

## 14. Java集成（Spring Data MongoDB）

### 14.1 依赖配置

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  data:
    mongodb:
      uri: mongodb://user:pass@host1:27017,host2:27017,host3:27017/mydb?replicaSet=rs0&readPreference=secondaryPreferred
```

### 14.2 实体与Repository

```java
@Document(collection = "users")
public class User {
    @Id
    private String id;

    @Indexed(unique = true)
    private String email;

    @Field("userName")
    private String name;

    private Address address;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;

    // getter/setter...
}

public interface UserRepository extends MongoRepository<User, String> {
    List<User> findByEmail(String email);

    @Query("{ 'age': { $gt: ?0 } }")
    List<User> findAdults(int minAge);

    @Query(value = "{ 'address.city': ?0 }", fields = "{ 'name': 1, 'email': 1 }")
    List<User> findByCity(String city);
}
```

### 14.3 MongoTemplate高级操作

```java
@Service
public class UserService {

    @Autowired
    private MongoTemplate mongoTemplate;

    // 条件查询 + 分页
    public List<User> searchUsers(String keyword, int page, int size) {
        Query query = new Query();
        query.addCriteria(Criteria.where("name").regex(keyword, "i"));
        query.with(Sort.by(Sort.Direction.DESC, "createdAt"));
        query.skip((long) page * size).limit(size);
        return mongoTemplate.find(query, User.class);
    }

    // 聚合管道
    public List<Document> aggregateSalesByCategory() {
        Aggregation agg = Aggregation.newAggregation(
            Aggregation.match(Criteria.where("status").is("completed")),
            Aggregation.group("category").sum("amount").as("totalSales"),
            Aggregation.sort(Sort.Direction.DESC, "totalSales")
        );
        return mongoTemplate.aggregate(agg, "orders", Document.class)
                            .getMappedResults();
    }

    // 批量写入
    public void bulkInsert(List<User> users) {
        List<BulkWriteOperation> ops = new ArrayList<>();
        BulkOperations bulkOps = mongoTemplate.bulkOps(BulkOperations.BulkMode.UNORDERED, User.class);
        bulkOps.insert(users);
        bulkOps.execute();
    }
}
```

### 14.4 事务支持（4.0+副本集）

```java
@Configuration
public class MongoConfig {
    @Bean
    public MongoTransactionManager transactionManager(MongoDbFactory factory) {
        return new MongoTransactionManager(factory);
    }
}

@Service
public class OrderService {

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private OrderRepository orderRepository;

    @Transactional
    public void createOrder(Order order) {
        orderRepository.save(order);
        userRepository.updateOrderCount(order.getUserId(), 1);
    }
}
```

---

## 15. 面试要点（5问）

**Q1：MongoDB为什么选择BSON而不是JSON？**

BSON是JSON的二进制编码格式，相比JSON额外支持日期（Date）、二进制（BinData）、ObjectId等扩展类型，且通过记录每个字段长度实现更高效的反序列化——无需逐字符扫描即可跳过不需要的字段，对索引和聚合查询性能至关重要。

**Q2：副本集中如何避免脑裂（Split-Brain）？**

MongoDB通过**多数派写确认**避免脑裂：Primary必须将写操作同步到多数节点后才确认成功（`w: majority`）。发生网络分区时，少数派分区无法选出新Primary（票数不足N/2+1），因此不会出现两个Primary。即使旧Primary仍接受写入，这些写操作无法达成多数确认，故障恢复后会被回滚。

**Q3：分片键如何选择？选择错误有什么后果？**

理想分片键应满足**高基数、低频率、非单调递增、查询隔离**。若选错：基数低会导致数据集中在少数chunk，无法水平扩展；单调递增键（如ObjectId、时间戳）做范围分片会导致所有写请求打到最后一个shard形成热点；不含查询字段的分片键会导致每次查询广播到所有shard（scatter-gather），性能急剧下降。MongoDB 5.0+支持`reshardCollection`重新选择分片键，但代价高昂。

**Q4：WiredTiger的Cache与MySQL InnoDB Buffer Pool有何异同？**

相同点：都是将热数据缓存在内存、采用LRU变体淘汰算法、通过WAL保证持久性。不同点：WiredTiger默认占用 `(RAM-1GB)*50%` 而InnoDB默认75%；WiredTiger支持文档级并发（MVCC快照）而InnoDB是行级锁；WiredTiger内置Snappy压缩而InnoDB需靠页压缩；WiredTiger的Checkpoint是B-tree级别的全量刷盘，InnoDB的Checkpoint是增量刷脏页。

**Q5：MongoDB的索引为什么遵循ESR规则？**

ESR（Equality-Sort-Range）规则确定复合索引字段顺序：等值字段放最前可快速缩小扫描范围；排序字段放中间可利用索引有序性避免filesort；范围字段放最后避免排序字段无法利用索引有序性。若范围字段在排序字段之前，范围查询会产生多段不连续索引区间，每段内部需要单独排序再归并，导致无法利用索引顺序，必须额外内存排序。

---

## 📖 相关阅读

- [MongoDB官方文档 - WiredTiger](https://www.mongodb.com/docs/manual/core/wiredtiger/)
- [MongoDB官方文档 - Replication](https://www.mongodb.com/docs/manual/replication/)
- [MongoDB官方文档 - Sharding](https://www.mongodb.com/docs/manual/sharding/)
- [Spring Data MongoDB Reference](https://docs.spring.io/spring-data/mongodb/reference/)
- [MongoDB索引策略最佳实践](https://www.mongodb.com/docs/manual/core/data-model-design/)
- [Raft一致性算法论文](https://raft.github.io/)
- 《MongoDB实战》（Kristina Chodorow）
- 《MongoDB权威指南》（O'Reilly）
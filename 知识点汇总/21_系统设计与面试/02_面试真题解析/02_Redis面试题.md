# Redis面试题

> Redis高频面试题及详细解答

## 📋 目录
- [数据结构](#数据结构)
- [持久化机制](#持久化机制)
- [高可用方案](#高可用方案)
- [缓存问题](#缓存问题)
- [分布式锁](#分布式锁)
- [实战应用](#实战应用)

---

## 数据结构

### Q1: 5种基本类型及底层实现？（⭐⭐⭐⭐⭐）

**Redis数据类型**：

**1. String（字符串）**：
```redis
# 基本操作
SET key value
GET key
INCR key
DECR key
APPEND key value

# 底层实现
SDS（Simple Dynamic String）

结构：
struct sdshdr {
    int len;       // 字符串长度
    int free;      // 未使用空间
    char buf[];    // 字符数组
}

示例：
SET name "Redis"
→ len=5, free=0, buf="Redis\0"

优势vs C字符串：
  ✅ O(1)获取长度（len字段）
  ✅ 防止缓冲区溢出（free字段）
  ✅ 减少内存重分配（预分配）
  ✅ 二进制安全（可存图片等）

应用场景：
  - 缓存对象（JSON）
  - 计数器（INCR）
  - 分布式锁（SETNX）
  - Session共享
```

**2. Hash（哈希）**：
```redis
# 基本操作
HSET user:1 name "张三"
HSET user:1 age 20
HGET user:1 name
HGETALL user:1
HINCRBY user:1 age 1

# 底层实现
1. ZipList（压缩列表）- 数据量小时
   条件：
     - 元素数量 < 512（hash-max-ziplist-entries）
     - 单个值 < 64字节（hash-max-ziplist-value）
   
   结构：连续内存
   [key1][value1][key2][value2]...
   
   优点：节省内存
   缺点：查询O(n)

2. HashTable（哈希表）- 数据量大时
   结构：
   typedef struct dict {
       dictht ht[2];      // 两个哈希表（渐进式rehash）
       long rehashidx;    // rehash进度
   }
   
   渐进式rehash：
     - 创建新哈希表（2倍大小）
     - 每次操作时迁移一部分数据
     - 避免一次性rehash阻塞

应用场景：
  - 存储对象（用户信息）
  - 购物车（user_id → {product_id: count}）
```

**3. List（列表）**：
```redis
# 基本操作
LPUSH list 1 2 3     # 左插入
RPUSH list 4 5 6     # 右插入
LPOP list            # 左弹出
RPOP list            # 右弹出
LRANGE list 0 -1     # 范围查询

# 底层实现
1. ZipList（压缩列表）- 数据量小时
   条件：
     - 元素数量 < 512
     - 单个值 < 64字节

2. LinkedList（双向链表）- 数据量大时
   结构：
   [prev][value][next] ↔ [prev][value][next]
   
   优点：插入删除O(1)
   缺点：内存不连续

3. QuickList（快速列表）- Redis 3.2+
   结构：LinkedList + ZipList
   [ZipList] ↔ [ZipList] ↔ [ZipList]
   
   优点：节省内存 + 快速插入删除

应用场景：
  - 消息队列（LPUSH + BRPOP）
  - 最新列表（LPUSH + LRANGE）
  - 评论列表
```

**4. Set（集合）**：
```redis
# 基本操作
SADD set 1 2 3
SISMEMBER set 1       # 是否存在
SMEMBERS set          # 所有成员
SINTER set1 set2      # 交集
SUNION set1 set2      # 并集
SDIFF set1 set2       # 差集

# 底层实现
1. IntSet（整数集合）- 元素都是整数且数量少
   条件：
     - 元素都是整数
     - 元素数量 < 512
   
   结构：
   typedef struct intset {
       uint32_t encoding;  // 编码方式
       uint32_t length;    // 元素数量
       int8_t contents[];  // 元素数组
   }
   
   编码升级：
     int16 → int32 → int64

2. HashTable（哈希表）- 其他情况
   key: 元素值
   value: NULL

应用场景：
  - 标签（tag）
  - 共同好友（SINTER）
  - 抽奖（SRANDMEMBER）
  - 去重
```

**5. ZSet（有序集合）**：
```redis
# 基本操作
ZADD rank 100 "张三"
ZADD rank 95 "李四"
ZADD rank 90 "王五"
ZRANGE rank 0 -1 WITHSCORES     # 按分数升序
ZREVRANGE rank 0 -1             # 按分数降序
ZRANK rank "张三"                # 排名

# 底层实现
1. ZipList（压缩列表）- 数据量小时
   结构：
   [member1][score1][member2][score2]...

2. SkipList + HashTable（跳表+哈希表）
   
   跳表：
     L3: 1 -----------------> 7
     L2: 1 ------> 4 ------> 7 ------> 10
     L1: 1 -> 2 -> 4 -> 5 -> 7 -> 8 -> 10
     
     查找：从高层开始，逐层下降
     时间复杂度：O(log n)
     
     为什么不用平衡树？
       ✅ 实现简单
       ✅ 范围查询快（链表遍历）
       ✅ 支持并发（无需旋转）
   
   HashTable：
     member → score（O(1)查询分数）

应用场景：
  - 排行榜
  - 延迟队列（score=时间戳）
  - 优先级队列
```

---

### Q2: SDS vs C字符串？（⭐⭐⭐⭐）

**对比**：

| 对比项 | C字符串 | SDS |
|--------|---------|-----|
| 获取长度 | O(n) 遍历 | O(1) len字段 |
| 缓冲区溢出 | ❌ 可能溢出 | ✅ 检查free |
| 内存重分配 | 每次修改都重分配 | 预分配+惰性释放 |
| 二进制安全 | ❌ 遇\0结束 | ✅ 用len判断 |
| 兼容C函数 | ✅ | ✅ buf是C字符串 |

**SDS详解**：
```c
// SDS结构
struct sdshdr {
    int len;       // 已使用长度
    int free;      // 未使用长度
    char buf[];    // 字符数组
}

// 示例
SET key "hello"
→ len=5, free=0, buf="hello\0"

APPEND key " world"
→ len=11, free=11, buf="hello world\0          "
              ↑                    ↑
            已使用               预分配

// 预分配策略
if (len < 1MB) {
    free = len;  // 加倍分配
} else {
    free = 1MB;  // 最多1MB
}

// 惰性释放
SETRANGE key 0 "hi"  // 缩短字符串
→ len=2, free=9, buf="hi\0lo world          "
                          ↑
                       未释放

优势：
  1. 快速获取长度：
     STRLEN key  // O(1)
     
  2. 防止溢出：
     修改前检查：len + addlen <= len + free
     不够就扩容
     
  3. 减少重分配：
     - 预分配：减少扩容次数
     - 惰性释放：减少缩容次数
     
  4. 二进制安全：
     可存储图片、音频等二进制数据
```

---

## 持久化机制

### Q2: RDB和AOF的区别及优缺点？（⭐⭐⭐⭐⭐）

**RDB（Redis Database）**：
```redis
# RDB配置
save 900 1        # 900秒内至少1个key变化则持久化
save 300 10       # 300秒内至少10个key变化则持久化
save 60 10000     # 60秒内至少10000个key变化则持久化
stop-writes-on-bgsave-error yes  # 持久化出错是否停止写入
rdbcompression yes               # 是否压缩RDB文件
rdbchecksum yes                  # 是否校验RDB文件
dbfilename dump.rdb              # RDB文件名
dir ./                           # RDB文件存储路径

# 手动触发RDB
SAVE       # 同步，阻塞Redis服务器
BGSAVE     # 异步，fork子进程执行
```

**工作原理**：
```
1. Redis调用fork()，创建子进程
2. 子进程将数据写入临时RDB文件
3. 写入完成后，替换旧RDB文件
4. 整个过程主进程不阻塞（BGSAVE）

示意图：
[Redis主进程] → fork() → [子进程] → 写入临时文件 → 替换旧文件
    ↑                               ↓
  处理命令                        完成持久化
```

**AOF（Append Only File）**：
```redis
# AOF配置
appendonly yes             # 开启AOF
appendfilename "appendonly.aof"   # AOF文件名
dir ./                           # AOF文件存储路径

# 同步策略
appendfsync everysec             # 每秒同步（默认）
# appendfsync always             # 每次写入都同步
# appendfsync no                 # 由操作系统决定

# 重写配置
auto-aof-rewrite-percentage 100  # AOF文件增长百分比
auto-aof-rewrite-min-size 64mb   # AOF文件最小重写大小

# 手动触发重写
BGREWRITEAOF
```

**工作原理**：
```
1. 所有写命令追加到aof_buf缓冲区
2. 根据同步策略将缓冲区内容写入AOF文件
3. AOF文件过大时，触发重写（BGREWRITEAOF）
4. 重写过程与RDB类似，生成优化后的新AOF文件

示意图：
写命令 → aof_buf → [everysec/always/no] → AOF文件 → 重写优化
```

**RDB vs AOF 详细对比**：
| 特性 | RDB | AOF |
|------|-----|-----|
| 数据完整性 | 差（可能丢失几分钟数据） | 好（最多丢失1秒数据） |
| 文件大小 | 小（压缩二进制） | 大（文本命令） |
| 恢复速度 | 快 | 慢 |
| 写入性能 | 好（fork子进程，主进程不阻塞） | 一般（频繁IO操作） |
| 重写机制 | SAVE/BGSAVE | BGREWRITEAOF |
| 数据格式 | 二进制 | 文本命令 |
| 兼容性 | 低（版本间不兼容） | 高（命令兼容） |

**最佳实践**：
```
# 生产环境推荐配置
1. 同时开启RDB和AOF
   - RDB用于快速恢复
   - AOF用于保证数据完整性

2. 同步策略选择everysec
   - 平衡性能和安全性

3. 定期备份RDB文件
   - 防止AOF文件损坏

4. 监控AOF文件大小
   - 及时处理重写
```

**故障恢复流程**：
```
1. Redis启动时，优先加载AOF文件
2. 如果AOF文件不存在，加载RDB文件
3. 如果两者都存在，以AOF为准（数据更完整）

命令验证：
redis-server --appendonly yes --dbfilename dump.rdb
```

---

### Q4: 持久化如何选择？（⭐⭐⭐⭐）

**选择策略**：
```
1. 只做缓存（可丢数据）：
   - 不开启持久化
   - 或只开RDB做备份

2. 数据重要（不能丢）：
   - AOF + 混合持久化
   - appendfsync everysec
   
3. 兼顾性能和安全：
   - 混合持久化（推荐）
   - RDB做全量备份（定期）
   - AOF保证数据不丢失

4. 数据量特别大：
   - 主库：关闭持久化
   - 从库：开启RDB或AOF
   - 保证性能 + 数据安全

推荐配置：
# 混合持久化
appendonly yes
aof-use-rdb-preamble yes
appendfsync everysec

# RDB备份
save 900 1
save 300 10
save 60 10000

# AOF重写
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
```

---

## 高可用方案

### Q5: 主从复制原理？（⭐⭐⭐⭐⭐）

**复制流程**：
```
1. 从库连接主库：
   SLAVEOF 127.0.0.1 6379

2. 从库发送PSYNC命令：
   PSYNC <runid> <offset>
   
   runid：主库ID
   offset：复制偏移量

3. 主库判断：
   - 第一次复制：全量复制
   - 部分数据：增量复制

4. 全量复制：
   ① 主库BGSAVE生成RDB
   ② 主库发送RDB给从库
   ③ 从库清空数据，加载RDB
   ④ 主库发送复制缓冲区的命令
   
5. 增量复制：
   ① 主库发送复制缓冲区的命令
   ② 从库执行命令

6. 心跳检测：
   从库每秒发送：REPLCONF ACK <offset>
```

**复制模式**：
```
1. 全量复制：
   触发条件：
     - 首次连接
     - runid不匹配
     - offset不在复制缓冲区
   
   缺点：
     - RDB生成耗时
     - 网络传输耗时
     - 从库清空数据风险

2. 增量复制（PSYNC）：
   触发条件：
     - 从库短暂断开重连
     - offset在复制缓冲区内
   
   复制缓冲区（Replication Backlog）：
     - 环形缓冲区
     - 默认1MB
     - 保存最近的写命令
   
   优点：
     - 只传输增量数据
     - 快速恢复
```

**复制延迟**：
```
原因：
  1. 主库写入压力大
  2. 网络延迟
  3. 从库机器性能差
  4. 大key复制慢

解决方案：
  1. 升级从库配置
  2. 优化网络
  3. 避免大key
  4. 限流（主库）
  5. 读写分离策略（允许延迟）
```

---

### Q6: 哨兵模式？（⭐⭐⭐⭐⭐）

**哨兵（Sentinel）**：
```
定义：
  - 监控主从节点
  - 自动故障转移
  - 通知客户端新的主节点

架构：
  Master
    ↓
  Slave1  Slave2
    ↓        ↓
  Sentinel1 Sentinel2 Sentinel3

功能：
  1. 监控：检查主从节点是否正常
  2. 通知：节点故障时通知
  3. 故障转移：主库挂了，选举新主库
  4. 配置中心：客户端连接哨兵获取主库地址
```

**故障转移流程**：
```
1. 主观下线（Subjectively Down）：
   - 某个哨兵认为主库挂了
   - 超时未响应PING（30秒）

2. 客观下线（Objectively Down）：
   - 多个哨兵认为主库挂了
   - 达到quorum数量（如2/3）

3. 选举Leader哨兵：
   - Raft算法
   - 多数派投票
   - 执行故障转移

4. 从库选举：
   优先级：
     ① slave-priority（优先级）
     ② 复制偏移量（最接近主库）
     ③ runid（最小）

5. 切换主库：
   ① 对选中的从库执行SLAVEOF NO ONE
   ② 其他从库执行SLAVEOF new_master
   ③ 更新配置
   ④ 通知客户端

6. 旧主库恢复：
   - 变成新主库的从库
```

**配置示例**：
```bash
# sentinel.conf
port 26379
sentinel monitor mymaster 127.0.0.1 6379 2  # 2个哨兵同意才客观下线
sentinel down-after-milliseconds mymaster 30000  # 30秒超时
sentinel parallel-syncs mymaster 1  # 同时同步的从库数
sentinel failover-timeout mymaster 180000  # 故障转移超时

# 启动
redis-sentinel sentinel.conf
```

**客户端连接**：
```java
// Jedis示例
Set<String> sentinels = new HashSet<>();
sentinels.add("127.0.0.1:26379");
sentinels.add("127.0.0.1:26380");
sentinels.add("127.0.0.1:26381");

JedisSentinelPool pool = new JedisSentinelPool(
    "mymaster",  // 主库名称
    sentinels
);

Jedis jedis = pool.getResource();
jedis.set("key", "value");
```

---

### Q7: Redis Cluster？（⭐⭐⭐⭐）

**集群（Cluster）**：
```
定义：
  - 数据分片（Sharding）
  - 去中心化
  - 无需哨兵
  - 支持水平扩展

架构：
  Master1 → Slave1
  Master2 → Slave2
  Master3 → Slave3

特点：
  - 16384个槽位（slot）
  - 数据根据key分布到不同节点
  - 节点间通过Gossip协议通信
  - 自动故障转移
```

**槽位分配**：
```
槽位数：16384（0-16383）

分配算法：
  slot = CRC16(key) % 16384

示例：
  Master1: 0-5460    (5461个槽)
  Master2: 5461-10922 (5462个槽)
  Master3: 10923-16383 (5461个槽)

Hash Tag：
  key={user}:name  → 只对user计算CRC16
  key={user}:age
  
  作用：相关数据存储到同一节点
```

**重定向**：
```
客户端访问：
  GET key

节点判断：
  if (key的slot在本节点) {
      返回数据
  } else {
      返回 MOVED slot ip:port  // 重定向
  }

客户端：
  1. 收到MOVED
  2. 缓存slot → node映射
  3. 直接访问正确节点

示例：
  客户端 → Master1: GET user:100
  Master1: MOVED 5500 192.168.1.2:6379
  客户端 → Master2: GET user:100  // 直接访问
```

**扩容缩容**：
```
扩容（添加节点）：
  1. 启动新节点Master4
  2. 加入集群：CLUSTER MEET ip port
  3. 分配槽位：
     Master1: 0-4095   (减少)
     Master2: 5461-10922
     Master3: 10923-16383
     Master4: 4096-5460 (新增)
  4. 迁移数据：
     Master1 → Master4 (slot 4096-5460)

缩容（删除节点）：
  1. 迁移槽位到其他节点
  2. 删除节点：CLUSTER FORGET node_id
```

**故障转移**：
```
类似哨兵：
  1. 主观下线：某节点认为Master挂了
  2. 客观下线：多数节点认为Master挂了
  3. 从库选举：
     - 复制偏移量最大
     - 优先级
  4. 切换：Slave变成Master
  5. 广播：通知其他节点
```

**集群限制**：
```
❌ 不支持多键操作：
   MGET key1 key2  // key1和key2可能在不同节点

✅ Hash Tag解决：
   MGET {user}:name {user}:age  // 都在同一节点

❌ 不支持多数据库：
   只有db0

❌ 不支持事务：
   事务中的key可能在不同节点
```

---

## 缓存问题

### Q8: 缓存穿透？（⭐⭐⭐⭐⭐）

**定义**：
```
缓存穿透（Cache Penetration）：
  - 查询不存在的数据
  - 缓存没有
  - 数据库也没有
  - 大量请求打到数据库

示例：
  恶意攻击：查询id=-1的用户
  → Redis没有
  → 查数据库，也没有
  → 每次都查数据库
  → 数据库崩溃
```

**解决方案**：

**1. 布隆过滤器（Bloom Filter）**：
```
原理：
  - 位数组 + 多个哈希函数
  - 判断元素可能存在或一定不存在

结构：
  [0][0][0][0][0][0][0][0][0][0]
   0  1  2  3  4  5  6  7  8  9

添加元素"user:1"：
  hash1("user:1") = 2 → [0][0][1][0][0][0][0][0][0][0]
  hash2("user:1") = 5 → [0][0][1][0][0][1][0][0][0][0]
  hash3("user:1") = 7 → [0][0][1][0][0][1][0][1][0][0]

查询"user:1"：
  hash1("user:1") = 2 → bit[2]=1 ✓
  hash2("user:1") = 5 → bit[5]=1 ✓
  hash3("user:1") = 7 → bit[7]=1 ✓
  → 可能存在（需要继续查Redis/DB）

查询"user:99"：
  hash1("user:99") = 1 → bit[1]=0 ✗
  → 一定不存在（直接返回）

实现（Redisson）：
@Service
public class UserService {
    
    @Autowired
    private RedissonClient redisson;
    
    private RBloomFilter<String> bloomFilter;
    
    @PostConstruct
    public void init() {
        bloomFilter = redisson.getBloomFilter("user:bloom");
        // 预期元素数量10万，误判率1%
        bloomFilter.tryInit(100000L, 0.01);
        
        // 初始化：添加所有用户ID
        List<Long> userIds = userDao.getAllUserIds();
        for (Long id : userIds) {
            bloomFilter.add("user:" + id);
        }
    }
    
    public User getById(Long id) {
        String key = "user:" + id;
        
        // 1. 布隆过滤器判断
        if (!bloomFilter.contains(key)) {
            return null;  // 一定不存在
        }
        
        // 2. 查Redis
        User user = redisTemplate.opsForValue().get(key);
        if (user != null) {
            return user;
        }
        
        // 3. 查数据库
        user = userDao.selectById(id);
        if (user != null) {
            redisTemplate.opsForValue().set(key, user);
        }
        
        return user;
    }
}

优点：
  ✅ 内存占用小
  ✅ 查询速度快O(k)
  
缺点：
  ❌ 有误判率（false positive）
  ❌ 不支持删除（可用Counting Bloom Filter）
```

**2. 缓存空对象**：
```java
public User getById(Long id) {
    String key = "user:" + id;
    
    // 1. 查Redis
    User user = redisTemplate.opsForValue().get(key);
    if (user != null) {
        if (user == NULL_USER) {  // 空对象标记
            return null;
        }
        return user;
    }
    
    // 2. 查数据库
    user = userDao.selectById(id);
    
    if (user != null) {
        // 缓存正常数据
        redisTemplate.opsForValue().set(key, user, 1, TimeUnit.HOURS);
    } else {
        // 缓存空对象（短过期时间）
        redisTemplate.opsForValue().set(key, NULL_USER, 5, TimeUnit.MINUTES);
    }
    
    return user;
}

优点：
  ✅ 实现简单
  ✅ 无误判
  
缺点：
  ❌ 占用内存（大量空对象）
  ❌ 短期内数据不一致（空对象未过期，数据库新增了）
```

**3. 参数校验**：
```java
public User getById(Long id) {
    // 参数校验
    if (id == null || id <= 0) {
        throw new IllegalArgumentException("id不合法");
    }
    
    // 业务规则校验
    if (id > MAX_USER_ID) {
        return null;  // 超出范围，直接返回
    }
    
    // ...
}
```

---

### Q9: 缓存击穿？（⭐⭐⭐⭐⭐）

**定义**：
```
缓存击穿（Hotspot Invalid）：
  - 热点key过期
  - 大量并发请求
  - 同时打到数据库

示例：
  商品详情页缓存过期
  → 瞬间10000个请求
  → Redis没有
  → 10000个请求查数据库
  → 数据库崩溃
```

**解决方案**：

**1. 互斥锁（Mutex Lock）**：
```java
public User getById(Long id) {
    String key = "user:" + id;
    
    // 1. 查Redis
    User user = redisTemplate.opsForValue().get(key);
    if (user != null) {
        return user;
    }
    
    // 2. 加锁
    String lockKey = "lock:user:" + id;
    boolean locked = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);
    
    if (locked) {
        try {
            // 3. 再次查Redis（双重检查）
            user = redisTemplate.opsForValue().get(key);
            if (user != null) {
                return user;
            }
            
            // 4. 查数据库
            user = userDao.selectById(id);
            
            // 5. 写Redis
            if (user != null) {
                redisTemplate.opsForValue().set(key, user, 1, TimeUnit.HOURS);
            }
            
            return user;
        } finally {
            // 6. 释放锁
            redisTemplate.delete(lockKey);
        }
    } else {
        // 7. 未获取锁，等待后重试
        try {
            Thread.sleep(50);
            return getById(id);  // 递归重试
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }
}

优点：
  ✅ 一致性好
  ✅ 数据库压力小
  
缺点：
  ❌ 性能略差（等待锁）
  ❌ 可能死锁（需要超时时间）
```

**2. 热点数据不过期**：
```java
// 逻辑过期
public class CacheData<T> {
    private T data;
    private LocalDateTime expireTime;  // 逻辑过期时间
}

public User getById(Long id) {
    String key = "user:" + id;
    
    // 1. 查Redis
    CacheData<User> cacheData = redisTemplate.opsForValue().get(key);
    
    if (cacheData == null) {
        // 2. 缓存未命中，查数据库
        User user = userDao.selectById(id);
        if (user != null) {
            CacheData<User> newData = new CacheData<>();
            newData.setData(user);
            newData.setExpireTime(LocalDateTime.now().plusHours(1));
            redisTemplate.opsForValue().set(key, newData);  // 永不过期
        }
        return user;
    }
    
    // 3. 判断逻辑过期
    if (LocalDateTime.now().isAfter(cacheData.getExpireTime())) {
        // 4. 异步更新缓存
        threadPool.execute(() -> {
            User user = userDao.selectById(id);
            if (user != null) {
                CacheData<User> newData = new CacheData<>();
                newData.setData(user);
                newData.setExpireTime(LocalDateTime.now().plusHours(1));
                redisTemplate.opsForValue().set(key, newData);
            }
        });
    }
    
    // 5. 返回旧数据（即使过期）
    return cacheData.getData();
}

优点：
  ✅ 性能好（无等待）
  ✅ 无缓存击穿
  
缺点：
  ❌ 短期数据不一致（返回旧数据）
  ❌ 额外内存（逻辑过期时间）
```

**3. 提前更新**：
```java
// 定时任务
@Scheduled(fixedRate = 30 * 60 * 1000)  // 30分钟
public void refreshHotKey() {
    List<Long> hotUserIds = getHotUserIds();  // 获取热点用户
    
    for (Long id : hotUserIds) {
        User user = userDao.selectById(id);
        if (user != null) {
            String key = "user:" + id;
            redisTemplate.opsForValue().set(key, user, 1, TimeUnit.HOURS);
        }
    }
}
```

---

### Q10: 缓存雪崩？（⭐⭐⭐⭐⭐）

**定义**：
```
缓存雪崩（Cache Avalanche）：
  - 大量缓存同时过期
  - 或Redis宕机
  - 大量请求打到数据库
  - 数据库崩溃

示例：
  凌晨1点，10万个商品缓存同时过期
  → 早上8点，用户开始访问
  → Redis没有
  → 10万个请求查数据库
  → 数据库崩溃
```

**解决方案**：

**1. 过期时间打散**：
```java
// ❌ 错误：统一过期时间
redisTemplate.opsForValue().set(key, value, 1, TimeUnit.HOURS);

// ✅ 正确：随机过期时间
int expire = 3600 + new Random().nextInt(300);  // 3600~3900秒
redisTemplate.opsForValue().set(key, value, expire, TimeUnit.SECONDS);
```

**2. 热点数据不过期**：
```java
// 热点数据永不过期（后台定时更新）
@Scheduled(fixedRate = 30 * 60 * 1000)
public void refreshHotData() {
    // 更新热点数据
}
```

**3. 限流降级**：
```java
// Sentinel限流
@SentinelResource(value = "getUser", 
                  blockHandler = "blockHandler",
                  fallback = "fallback")
public User getById(Long id) {
    // 查询逻辑
}

// 限流降级处理
public User blockHandler(Long id, BlockException ex) {
    return new User();  // 返回默认值
}

public User fallback(Long id, Throwable ex) {
    return getCached DefaultUser();  // 返回缓存的默认值
}
```

**4. 多级缓存**：
```
架构：
  客户端
    ↓
  本地缓存（Caffeine）
    ↓
  Redis缓存
    ↓
  数据库

好处：
  - Redis挂了，本地缓存还能用
  - 部分请求不打到Redis
```

**5. Redis集群**：
```
高可用：
  - 主从 + 哨兵
  - Redis Cluster
  
避免单点故障：
  - 主库挂了，从库顶上
  - 某个节点挂了，其他节点服务
```

**6. 熔断机制**：
```java
// Hystrix熔断
@HystrixCommand(fallbackMethod = "fallback",
                commandProperties = {
                    @HystrixProperty(name = "circuitBreaker.enabled", value = "true"),
                    @HystrixProperty(name = "circuitBreaker.requestVolumeThreshold", value = "10"),
                    @HystrixProperty(name = "circuitBreaker.errorThresholdPercentage", value = "50")
                })
public User getById(Long id) {
    return userDao.selectById(id);
}

public User fallback(Long id) {
    return getDefaultUser();  // 降级
}
```

---

## 分布式锁

### Q11: Redis分布式锁实现？（⭐⭐⭐⭐⭐）

**基础实现（SETNX）**：
```java
// ❌ 版本1：简单SETNX（有问题）
public boolean lock(String key) {
    Boolean success = redisTemplate.opsForValue().setIfAbsent(key, "1");
    return Boolean.TRUE.equals(success);
}

public void unlock(String key) {
    redisTemplate.delete(key);
}

问题：
  1. 死锁：加锁后程序崩溃，锁永不释放
  2. 误删：A的锁被B删除
```

**改进版本**：
```java
// ✅ 版本2：添加过期时间 + 唯一标识
public boolean lock(String key, String value, long timeout) {
    // SETNX + EXPIRE必须原子操作
    Boolean success = redisTemplate.opsForValue()
        .setIfAbsent(key, value, timeout, TimeUnit.SECONDS);
    return Boolean.TRUE.equals(success);
}

public void unlock(String key, String value) {
    // Lua脚本保证原子性
    String script = 
        "if redis.call('get', KEYS[1]) == ARGV[1] then " +
        "    return redis.call('del', KEYS[1]) " +
        "else " +
        "    return 0 " +
        "end";
    
    redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList(key),
        value
    );
}

// 使用
String value = UUID.randomUUID().toString();
if (lock("product:1", value, 10)) {
    try {
        // 业务逻辑
    } finally {
        unlock("product:1", value);
    }
}

改进：
  ✅ 过期时间防止死锁
  ✅ 唯一标识防止误删
  ✅ Lua脚本保证原子性
```

**Redlock算法（多节点）**：
```java
// Redisson实现
@Bean
public RedissonClient redissonClient() {
    Config config = new Config();
    config.useSingleServer()
        .setAddress("redis://127.0.0.1:6379");
    return Redisson.create(config);
}

@Service
public class OrderService {
    
    @Autowired
    private RedissonClient redisson;
    
    public void createOrder() {
        RLock lock = redisson.getLock("order:lock");
        
        try {
            // 尝试加锁：等待100秒，锁10秒后自动释放
            boolean locked = lock.tryLock(100, 10, TimeUnit.SECONDS);
            
            if (locked) {
                // 业务逻辑
                System.out.println("创建订单");
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            // 释放锁
            if (lock.isLocked() && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}

特性：
  ✅ 自动续期（watchdog）
  ✅ 可重入
  ✅ 公平锁
  ✅ 读写锁
```

**看门狗机制（Watchdog）**：
```
问题：
  业务执行时间超过锁过期时间
  → 锁自动释放
  → 其他线程获取锁
  → 数据冲突

Redisson解决：
  1. 加锁成功后，启动watchdog线程
  2. watchdog每10秒检查锁
  3. 如果业务未完成，续期30秒
  4. 业务完成，停止watchdog

流程：
  t=0s:  加锁，过期时间30秒
  t=10s: watchdog续期，过期时间30秒（总40秒）
  t=20s: watchdog续期，过期时间30秒（总50秒）
  t=25s: 业务完成，释放锁，停止watchdog
```

**Redis分布式锁问题**：
```
1. Redis宕机：
   - 主从切换时，锁丢失
   - A在主库加锁
   - 主库挂了，从库升级（还未同步锁）
   - B在新主库加锁成功
   
   解决：Redlock（多个独立Redis节点）

2. 时钟跳跃：
   - Redis过期时间依赖系统时间
   - 时钟回拨，锁提前过期
   
   解决：NTP同步时钟

3. 长时间GC：
   - A持有锁，发生Full GC（暂停30秒）
   - 锁过期释放
   - B获取锁
   - A从GC恢复，继续执行
   
   解决：
     - watchdog自动续期
     - 业务幂等性

推荐：
  - 简单场景：Redisson
  - 强一致性：Zookeeper（CP）
  - Redis适合：AP（可用性 > 一致性）
```

---

## 实战应用

### Q12: 延迟队列实现？（⭐⭐⭐⭐）

**使用ZSet实现**：
```java
@Service
public class DelayQueue {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    // 添加任务
    public void addTask(String task, long delaySeconds) {
        long executeTime = System.currentTimeMillis() + delaySeconds * 1000;
        redisTemplate.opsForZSet().add("delay:queue", task, executeTime);
    }
    
    // 消费任务
    @Scheduled(fixedRate = 1000)  // 每秒执行
    public void consumeTask() {
        long now = System.currentTimeMillis();
        
        // 查询到期的任务（score <= now）
        Set<String> tasks = redisTemplate.opsForZSet()
            .rangeByScore("delay:queue", 0, now);
        
        if (tasks != null && !tasks.isEmpty()) {
            for (String task : tasks) {
                // 处理任务
                System.out.println("执行任务：" + task);
                
                // 删除任务
                redisTemplate.opsForZSet().remove("delay:queue", task);
            }
        }
    }
}

// 使用
delayQueue.addTask("order:timeout:123", 300);  // 5分钟后超时

应用场景：
  - 订单超时取消
  - 定时发送消息
  - 延迟任务调度
```

---

### Q13: 排行榜实现？（⭐⭐⭐⭐）

**使用ZSet实现**：
```java
@Service
public class RankService {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    // 更新分数
    public void updateScore(String userId, double score) {
        redisTemplate.opsForZSet().add("rank:score", userId, score);
    }
    
    // 增加分数
    public void incrScore(String userId, double delta) {
        redisTemplate.opsForZSet().incrementScore("rank:score", userId, delta);
    }
    
    // 获取排名（从0开始）
    public Long getRank(String userId) {
        // 降序排名
        return redisTemplate.opsForZSet().reverseRank("rank:score", userId);
    }
    
    // 获取分数
    public Double getScore(String userId) {
        return redisTemplate.opsForZSet().score("rank:score", userId);
    }
    
    // 获取Top N
    public List<ZSetOperations.TypedTuple<String>> getTopN(int n) {
        return new ArrayList<>(redisTemplate.opsForZSet()
            .reverseRangeWithScores("rank:score", 0, n - 1));
    }
    
    // 获取范围排名
    public List<ZSetOperations.TypedTuple<String>> getRangeRank(long start, long end) {
        return new ArrayList<>(redisTemplate.opsForZSet()
            .reverseRangeWithScores("rank:score", start, end));
    }
}

// 使用
rankService.updateScore("user:1", 100);
rankService.incrScore("user:1", 10);  // 110分

Long rank = rankService.getRank("user:1");  // 排名
List<TypedTuple<String>> top10 = rankService.getTopN(10);  // Top 10

应用场景：
  - 游戏排行榜
  - 热门文章
  - 销量排行
```

---

## 💡 面试技巧

### 高频考点
```
⭐⭐⭐⭐⭐（必考）：
  - 5种数据类型底层实现
  - RDB vs AOF
  - 主从复制原理
  - 缓存穿透/击穿/雪崩
  - Redis分布式锁

⭐⭐⭐⭐（高频）：
  - SDS vs C字符串
  - 跳表原理
  - 哨兵模式
  - Redis Cluster

⭐⭐⭐（中频）：
  - ZipList
  - 混合持久化
  - 延迟队列
  - 排行榜
```

---

**最后更新**: 2025-10-29  
**文档状态**: ✅ 完整内容（850+行）

💡 **记住**: Redis是后端开发必备技能，数据结构和缓存问题是核心！

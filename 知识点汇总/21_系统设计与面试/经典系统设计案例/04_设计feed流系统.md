# 设计feed流系统

> 高频面试题：设计一个类似微博/朋友圈的feed流系统

## 📋 面试题目

```
设计一个社交媒体feed流系统，支持以下功能：
1. 发布动态（文字、图片、视频）
2. 查看关注人动态流
3. 点赞、评论、转发
4. 热门内容推荐
5. 支持千万级用户，低延迟
```

---

## 一、需求澄清

### 功能需求

**核心功能**：
- [x] 内容发布：支持文字、图片、视频等多媒体内容
- [x] feed流展示：关注人动态聚合排序
- [x] 互动功能：点赞、评论、转发、收藏
- [x] 内容推荐：热门/推荐feed流
- [x] 内容搜索：按关键词查找内容
- [x] 通知系统：新动态、互动提醒

### 非功能需求

- **性能**：feed流加载延迟<200ms，支持10万QPS
- **可用性**：99.9%服务可用性
- **一致性**：最终一致性，允许短暂数据不一致
- **可扩展性**：支持用户从千万到亿级扩展
- **存储**：支持PB级内容存储

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     客户端应用层                          │
│  - iOS/Android App  - Web客户端  - 小程序                 │
└───────────────────────────┬─────────────────────────────┘
                            ↓
┌───────────────────────────┴─────────────────────────────┐
│                     负载均衡层                           │
│  - LVS/NGINX  - API Gateway  - 限流/熔断                 │
└───────────────────────────┬─────────────────────────────┘
                            ↓
┌───────────────────────────┴─────────────────────────────┐
│                     应用服务层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │发布服务  │  │feed流服务│  │互动服务  │  │推荐服务  │  │
│  │(发布内容)│  │(内容聚合)│  │(点赞评论)│  │(个性化)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└───────────────────────────┬─────────────────────────────┘
                            ↓
┌───────────────────────────┴─────────────────────────────┐
│                     数据存储层                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  MySQL   │  │  Redis   │  │ MongoDB  │  │  Kafka   │  │
│  │用户关系  │  │缓存feed  │  │内容存储  │  │消息队列  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐                             │
│  │  ES      │  │ 对象存储 │                             │
│  │内容搜索  │  │图片/视频 │                             │
│  └──────────┘  └──────────┘                             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 feed流类型与加载策略

**feed流类型**：
- **Timeline feed**：按时间倒序展示关注人动态
- **Algorithmic feed**：基于用户兴趣个性化推荐
- **Hybrid feed**：时间+算法混合排序

**加载策略**：
- **拉模式(Pull)**：用户主动刷新时拉取最新内容
- **推模式(Push)**：新内容实时推送到粉丝timeline
- **推拉结合**：活跃用户用推模式，非活跃用户用拉模式

---

## 三、详细设计

### 3.1 数据模型

**MySQL核心表**：
```sql
-- 用户表
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    avatar_url VARCHAR(255),
    follower_count INT DEFAULT 0,
    following_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 关注关系表
CREATE TABLE follow_relations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '关注者',
    followee_id BIGINT NOT NULL COMMENT '被关注者',
    status TINYINT DEFAULT 1 COMMENT '1-正常,0-取消关注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_followee (user_id, followee_id)
);

-- 内容表
CREATE TABLE posts (
    post_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    content TEXT,
    media_type TINYINT DEFAULT 0 COMMENT '0-文字,1-图片,2-视频',
    media_urls VARCHAR(1024),
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    repost_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, created_at)
);
```

**Redis数据结构**：
```
-- 用户timeline (推拉结合模式)
-- 推模式: 粉丝timeline缓存
ZADD timeline:{user_id} {timestamp} {post_id}

-- 拉模式: 用户发布的内容
ZADD user_posts:{user_id} {timestamp} {post_id}

-- 内容点赞集合
SADD post_likes:{post_id} {user_id}

-- 热门内容排行
ZADD hot_posts {score} {post_id}
```

**MongoDB集合**：
```javascript
// 评论集合
{
  _id: ObjectId("..."),
  post_id: 123456,
  user_id: 789,
  content: "这条内容很棒！",
  parent_id: null, // 父评论ID，用于回复
  created_at: ISODate("..."),
  like_count: 10
}

// 用户行为日志
{
  _id: ObjectId("..."),
  user_id: 789,
  action: "like", // view, like, comment, share
  target_id: 123456, // post_id
  timestamp: ISODate("..."),
  device: "android"
}
```

### 3.2 核心流程

**发布流程**：
```
1. 用户发布内容 → API Gateway → 发布服务
2. 发布服务：
   - 保存内容到MySQL posts表
   - 保存媒体文件到对象存储
   - 生成post_id并返回
3. 推送内容到粉丝timeline：
   - 拉取该用户的粉丝列表
   - 对活跃粉丝：推送post_id到其timeline缓存
   - 对非活跃粉丝：仅更新user_posts:{user_id}
4. 发送消息到Kafka，触发后续处理：
   - 更新用户发布计数
   - 推送通知给在线粉丝
   - 内容推荐系统处理
```

**Feed流加载流程**：
```
1. 用户请求feed流 → feed流服务
2. 服务处理：
   - 检查缓存：是否有现成的timeline
   - 缓存命中：直接返回ZREVRANGE timeline:{user_id} 0 20
   - 缓存未命中/需要更新：
     a. 拉取用户关注列表
     b. 批量获取每个关注者的最新posts
     c. 合并排序后返回
3. 返回结果给客户端
4. 异步更新timeline缓存
```

### 3.3 核心代码实现

**发布服务**：
```java
@Service
public class PublishService {
    @Autowired private PostMapper postMapper;
    @Autowired private RedisTemplate<String, Object> redisTemplate;
    @Autowired private KafkaTemplate<String, String> kafkaTemplate;
    @Autowired private ObjectStorageClient objectStorageClient;
    
    public PostVO publishPost(PostDTO postDTO) {
        // 1. 保存媒体文件
        List<String> mediaUrls = new ArrayList<>();
        if (CollectionUtils.isNotEmpty(postDTO.getMediaFiles())) {
            for (MultipartFile file : postDTO.getMediaFiles()) {
                String url = objectStorageClient.uploadFile(file);
                mediaUrls.add(url);
            }
        }
        
        // 2. 保存内容到数据库
        Post post = new Post();
        post.setUserId(postDTO.getUserId());
        post.setContent(postDTO.getContent());
        post.setMediaType(postDTO.getMediaType());
        post.setMediaUrls(String.join(",", mediaUrls));
        postMapper.insert(post);
        
        // 3. 更新用户发布列表 (拉模式基础)
        String userPostsKey = "user_posts:" + post.getUserId();
        redisTemplate.opsForZSet().add(userPostsKey, post.getId(), System.currentTimeMillis());
        // 设置过期时间，实际项目中可根据业务调整
        redisTemplate.expire(userPostsKey, 30, TimeUnit.DAYS);
        
        // 4. 推送内容到粉丝timeline (推模式)
        pushToFollowers(post);
        
        // 5. 发送Kafka消息，异步处理后续任务
        kafkaTemplate.send("post_published_topic", String.valueOf(post.getId()));
        
        // 6. 构建并返回结果
        PostVO postVO = convertToVO(post);
        return postVO;
    }
    
    // 推送内容到粉丝timeline
    private void pushToFollowers(Post post) {
        // 获取粉丝列表（实际项目中会分页处理）
        List<Long> followers = followerService.getActiveFollowers(post.getUserId());
        
        long timestamp = System.currentTimeMillis();
        String postId = String.valueOf(post.getId());
        
        // 批量推送（实际项目中会用pipeline优化）
        for (Long followerId : followers) {
            String timelineKey = "timeline:" + followerId;
            redisTemplate.opsForZSet().add(timelineKey, postId, timestamp);
            // 限制timeline长度，防止过大
            redisTemplate.opsForZSet().removeRange(timelineKey, 0, -1001);
        }
    }
}
```

**Feed流服务**：
```java
@Service
public class FeedService {
    @Autowired private RedisTemplate<String, Object> redisTemplate;
    @Autowired private PostMapper postMapper;
    @Autowired private FollowerService followerService;
    
    public PageResult<PostVO> getTimeline(Long userId, int page, int size) {
        String timelineKey = "timeline:" + userId;
        int start = (page - 1) * size;
        int end = start + size - 1;
        
        // 1. 尝试从缓存获取
        Set<ZSetOperations.TypedTuple<Object>> cachedPosts = redisTemplate.opsForZSet()
            .reverseRangeWithScores(timelineKey, start, end);
        
        if (CollectionUtils.isNotEmpty(cachedPosts)) {
            // 缓存命中，转换结果
            return convertCachedResult(cachedPosts);
        }
        
        // 2. 缓存未命中，执行拉模式获取
        return pullTimeline(userId, page, size);
    }
    
    // 拉模式获取timeline
    private PageResult<PostVO> pullTimeline(Long userId, int page, int size) {
        // 获取关注列表
        List<Long> followees = followerService.getFollowees(userId);
        if (CollectionUtils.isEmpty(followees)) {
            return new PageResult<>(Collections.emptyList(), 0);
        }
        
        // 构建查询参数
        TimelineQuery query = new TimelineQuery();
        query.setUserIds(followees);
        query.setPage(page);
        query.setSize(size);
        
        // 从数据库查询并排序
        List<Post> posts = postMapper.queryTimeline(query);
        long total = postMapper.countTimeline(query);
        
        // 转换结果
        List<PostVO> postVOs = posts.stream()
            .map(this::convertToVO)
            .collect(Collectors.toList());
        
        // 异步更新缓存
        asyncUpdateTimelineCache(userId, followees);
        
        return new PageResult<>(postVOs, total);
    }
    
    // 异步更新timeline缓存
    @Async
    public void asyncUpdateTimelineCache(Long userId, List<Long> followees) {
        String timelineKey = "timeline:" + userId;
        
        // 合并关注者的posts
        ZSetOperations<String, Object> zSetOps = redisTemplate.opsForZSet();
        
        for (Long followeeId : followees) {
            String userPostsKey = "user_posts:" + followeeId;
            // 获取该用户最近100条posts
            Set<ZSetOperations.TypedTuple<Object>> userPosts = zSetOps.reverseRangeWithScores(userPostsKey, 0, 99);
            
            if (CollectionUtils.isNotEmpty(userPosts)) {
                // 批量添加到timeline
                Map<Object, Double> scoreMembers = new HashMap<>();
                for (ZSetOperations.TypedTuple<Object> tuple : userPosts) {
                    scoreMembers.put(tuple.getValue(), tuple.getScore());
                }
                zSetOps.add(timelineKey, scoreMembers);
            }
        }
        
        // 对timeline排序并限制长度
        zSetOps.removeRange(timelineKey, 0, -1001);
        // 设置缓存过期时间
        redisTemplate.expire(timelineKey, 1, TimeUnit.HOURS);
    }
}
```

---

## 四、关键技术挑战

### 4.1 热点内容处理

**1. 热点用户发帖**
```java
/**
 * 热点用户识别与处理
 */
@Service
public class HotUserService {
    @Autowired
    private RedisTemplate redisTemplate;
    @Autowired
    private KafkaTemplate kafkaTemplate;
    
    // 判断是否为热点用户
    public boolean isHotUser(Long userId) {
        return redisTemplate.opsForSet().isMember("hot_users", userId);
    }
    
    // 热点用户发帖处理
    public void handleHotUserPost(Post post) {
        // 1. 写入数据库
        postMapper.insert(post);
        
        // 2. 发送到Kafka热点队列
        kafkaTemplate.send("hot_post_topic", JSON.toJSONString(post));
        
        // 3. 预热本地缓存
        localCache.put("post:" + post.getPostId(), post, 3600);
    }
}
```

**2. 热点内容缓存策略**
```
// 多级缓存架构
客户端缓存 → CDN → 应用本地缓存 → Redis集群 → 数据库

// 热点内容缓存更新策略
1. 主动更新：发布时更新缓存
2. 超时剔除：设置合理TTL
3. 主动预热：热门事件前预热
4. 降级熔断：缓存不可用时降级
```

### 4.2 feed流一致性与实时性

**1. 推拉结合的混合策略**
```java
/**
 * 动态推送服务
 */
@Service
public class FeedPushService {
    @Autowired
    private RedisTemplate redisTemplate;
    @Autowired
    private UserService userService;
    
    public void pushPostToFollowers(Long userId, Post post) {
        // 获取粉丝列表
        List<Long> followers = followerService.getFollowers(userId);
        
        // 分离活跃粉丝与普通粉丝
        List<Long> activeFollowers = new ArrayList<>();
        List<Long> normalFollowers = new ArrayList<>();
        
        for (Long follower : followers) {
            // 判断是否为活跃用户
            if (isActiveUser(follower)) {
                activeFollowers.add(follower);
            } else {
                normalFollowers.add(follower);
            }
        }
        
        // 活跃粉丝：同步推送timeline
        pushToActiveFollowers(activeFollowers, post);
        
        // 普通粉丝：异步处理或拉取时合并
        asyncPushToNormalFollowers(normalFollowers, post);
    }
}
```

**2. 缓存一致性保障**
```java
/**
 * 延迟双删保证缓存一致性
 */
public void updatePost(Post post) {
    // 1. 更新数据库
    postMapper.updateById(post);
    
    // 2. 删除缓存
    redisTemplate.delete("post:" + post.getPostId());
    
    // 3. 延迟再次删除
    scheduler.schedule(() -> {
        redisTemplate.delete("post:" + post.getPostId());
    }, 500, TimeUnit.MILLISECONDS);
}
```

### 4.3 海量数据存储与查询

**1. 数据分片策略**
```
// 内容表分片
分片键：user_id
分片算法：一致性哈希
分片数量：32片
扩容策略：翻倍扩容

// 历史数据归档
- 近期数据：MongoDB热数据区
- 历史数据：MongoDB冷数据区
- 归档策略：按时间范围自动迁移
```

**2. 分页加载优化**
```java
/**
 * 基于游标(Cursor)的分页查询
 */
public PageResult<Post> getPostsByCursor(Long userId, Long cursor, int pageSize) {
    // 游标为空，查最新数据
    if (cursor == null) {
        return postMapper.queryLatestPosts(userId, pageSize);
    }
    
    // 基于游标查询
    return postMapper.queryPostsByCursor(userId, cursor, pageSize);
}
```

## 五、容量规划

### 5.1 用户规模估算

```
假设条件：
- 总用户：5000万
- 日活用户：1000万
- 月活用户：3000万
- 人均发帖：1条/天
- 人均查看feed：100条/天
```

### 5.2 存储计算

| 数据类型 | 单条大小 | 日产生量 | 年存储量 | 存储介质 |
|---------|---------|---------|---------|---------|
| 文字动态 | 1KB | 1000万条 | 3.65TB | MongoDB |
| 图片动态 | 2MB | 200万条 | 1.46PB | 对象存储 |
| 视频动态 | 20MB | 10万条 | 73TB | 对象存储 |
| 互动数据 | 500B | 1亿条 | 1.825TB | MySQL+Redis |
| 用户关系 | 100B | 5亿关系 | 0.5TB | MySQL |

### 5.3 性能指标

```
- 读QPS：峰值5万/秒
- 写QPS：峰值1万/秒
- 动态加载延迟：P99 < 200ms
- 热门内容响应时间：<50ms
- 数据可靠性：99.99% (4个9)
```

## 六、监控与运维

### 6.1 核心监控指标

| 指标类别 | 具体指标 | 阈值 | 监控频率 |
|---------|---------|------|---------|
| 系统指标 | CPU使用率 | <80% | 5秒 |
| 系统指标 | 内存使用率 | <85% | 5秒 |
| 系统指标 | 磁盘IO | <90% | 10秒 |
| 应用指标 | 接口响应时间 | P99 < 200ms | 1秒 |
| 应用指标 | 接口错误率 | <0.1% | 1秒 |
| 业务指标 | feed流加载成功率 | >99.9% | 5秒 |
| 业务指标 | 动态发布成功率 | >99.9% | 5秒 |
| 缓存指标 | 缓存命中率 | >95% | 10秒 |
| 缓存指标 | 缓存穿透率 | <0.1% | 1分钟 |
| 数据库指标 | 慢查询数 | <5个/分钟 | 1分钟 |

### 6.2 告警机制

**三级告警体系**:
1. **P0级（紧急）**: 电话+短信+邮件，5分钟内响应
   - feed流加载成功率<99%
   - 动态发布失败率>1%
   - 服务节点宕机

2. **P1级（重要）**: 短信+邮件，30分钟内响应
   - 接口响应时间P99>500ms
   - 缓存命中率<90%
   - 数据库连接数>80%

3. **P2级（一般）**: 邮件，2小时内响应
   - 系统资源使用率超阈值
   - 热点内容缓存命中率低
   - 非核心接口错误率上升

### 6.3 运维工具

**1. 热点内容管理平台**:
- 热点内容实时监控
- 手动干预与降级
- 缓存预热操作

**2. 数据迁移工具**:
- 历史数据归档脚本
- 跨存储系统迁移
- 数据一致性校验

---

## 📚 扩展阅读

1. [Twitter的Timeline架构演进](https://blog.twitter.com/engineering/en_us/a/2010/announcing-twitter-timeline-architecture.html)
2. [Facebook的Feed流系统设计](https://www.infoq.cn/article/facebook-feed-architecture)
3. [Instagram的Feed优化实践](https://instagram-engineering.com/instagram-architecture-878d75fa9727)
4. [Redis在Feed流中的应用](https://redis.io/docs/manual/patterns/twitter-clone/)
5. [Kafka在实时数据处理中的最佳实践](https://docs.confluent.io/platform/current/kafka/best-practices.html)
6. [Feed流系统的缓存设计](https://highscalability.com/blog/2016/1/25/designing-a-scalable-feed-system.html)
7. [分布式系统中的一致性模型](https://jepsen.io/consistency)
8. [大规模推荐系统架构设计](https://www.manning.com/books/building-recommender-systems-with-machine-learning-and-ai)
# Elasticsearch深度实战

> 从倒排索引原理到生产集群调优，ES全链路实战指南

---

## 📋 目录

1. [倒排索引原理深入](#1-倒排索引原理深入)
2. [分词器详解](#2-分词器详解)
3. [聚合查询实战](#3-聚合查询实战)
4. [集群规划与调优](#4-集群规划与调优)
5. [与数据库同步方案](#5-与数据库同步方案)
6. [面试要点](#6-面试要点)

---

## 1. 倒排索引原理深入

### 正排索引 vs 倒排索引

```
正排索引（MySQL B+Tree）:
  DocID → 文档内容
  查询：扫描所有文档，逐个匹配 → 慢

倒排索引（Elasticsearch）:
  词项(Term) → DocID列表
  查询：先查词项，直接得到文档列表 → 快
```

### 倒排索引结构

```
┌─────────────────────────────────────────┐
│              Term Dictionary             │  ← 词典（FST压缩）
│  "java" → [1, 3, 7, 12]                │
│  "spring" → [1, 5, 8]                  │
│  "redis" → [3, 7, 9]                   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│              Posting List               │  ← 文档列表（Roaring Bitmap压缩）
│  Doc1: [java, spring, boot]             │
│  Doc3: [java, redis, cache]             │
│  Doc7: [java, redis, cluster]           │
└─────────────────────────────────────────┘
```

### FST（Finite State Transducer）

```
FST是一种前缀树压缩算法，用于存储Term Dictionary

优势：
- 极高的压缩比（TB级词典压缩到GB级内存）
- O(len(term))的查询复杂度
- 前缀查询天然支持

示例：
  词汇: cat, can, dog
  FST: c→a→{t|n}, d→o→g
  内存占用从15字节压缩到7字节
```

### Segment（段）机制

```
ES索引由多个Segment组成（不可变）

写入流程：
1. 文档写入Indexing Buffer
2. 刷新(refresh)到磁盘 → 生成新Segment（1秒一次）
3. 合并(merge)小Segment → 大Segment

特性：
- Segment不可变 → 查询时无需加锁
- 删除标记：.del文件记录已删除文档
- 近实时搜索：refresh_interval控制可见性（默认1秒）
```

---

## 2. 分词器详解

### 分词器组成

```
Analyzer = Character Filter + Tokenizer + Token Filter

Character Filter: 字符过滤（HTML标签去除、正则替换）
Tokenizer: 分词（按空格/标点/中文分词）
Token Filter: 词项过滤（小写、停用词、同义词、词干提取）
```

### 中文分词器

| 分词器 | 特点 | 适用场景 |
|--------|------|---------|
| IK Analyzer | 细粒度+智能分词两种模式 | 通用中文搜索 |
| SmartCN | Lucene内置中文分词 | 简单场景 |
| Pinyin Analysis | 拼音分词 | 拼音搜索 |
| ICU Analysis | 多语言支持 | 多语言场景 |

### IK分词器配置

```json
// IK分词器两种模式
// ik_smart: 粗粒度分词（适合索引）
// ik_max_word: 细粒度分词（适合搜索）

PUT /articles {
  "settings": {
    "analysis": {
      "analyzer": {
        "ik_smart_analyzer": {
          "type": "custom",
          "tokenizer": "ik_smart",
          "filter": ["lowercase", "stop"]
        },
        "ik_max_analyzer": {
          "type": "custom",
          "tokenizer": "ik_max_word",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "ik_max_analyzer",      // 索引时细粒度
        "search_analyzer": "ik_smart_analyzer" // 搜索时粗粒度
      },
      "content": {
        "type": "text",
        "analyzer": "ik_max_analyzer"
      }
    }
  }
}
```

### 自定义词典

```xml
<!-- IK自定义词典 ext.dic -->
Spring Boot
虚拟线程
结构化并发
领域驱动设计
```

---

## 3. 聚合查询实战

### 聚合类型

| 类型 | 说明 | 示例 |
|------|------|------|
| Bucket聚合 | 按条件分组 | 按分类分组统计 |
| Metric聚合 | 计算指标 | 平均值、最大值、百分位 |
| Pipeline聚合 | 基于其他聚合结果 | 移动平均、累计求和 |

### 实战：商品搜索+聚合

```json
// 搜索"Java"相关商品，按分类聚合，计算平均价格
POST /products/_search {
  "query": {
    "match": { "title": "Java" }
  },
  "aggs": {
    "by_category": {
      "terms": { "field": "category.keyword", "size": 10 },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } },
        "price_stats": { "stats": { "field": "price" } },
        "price_range": {
          "range": {
            "field": "price",
            "ranges": [
              { "to": 50 },
              { "from": 50, "to": 100 },
              { "from": 100 }
            ]
          }
        }
      }
    }
  }
}
```

### Java代码示例

```java
// Spring Data ES 聚合查询
@Autowired
private ElasticsearchOperations esOperations;

public SearchHits<Product> searchWithAggregation(String keyword) {
    NativeSearchQuery query = NativeSearchQueryBuilder.builder()
        .withQuery(QueryBuilders.matchQuery("title", keyword))
        .addAggregation(AggregationBuilders.terms("by_category")
            .field("category.keyword")
            .size(10)
            .subAggregation(AggregationBuilders.avg("avg_price").field("price"))
            .subAggregation(AggregationBuilders.stats("price_stats").field("price")))
        .build();
    
    return esOperations.search(query, Product.class);
}

// 解析聚合结果
SearchHits<Product> hits = searchWithAggregation("Java");
Aggregations aggs = hits.getAggregations();
if (aggs != null) {
    ParsedStringTerms byCategory = aggs.get("by_category");
    for (Terms.Bucket bucket : byCategory.getBuckets()) {
        String category = bucket.getKeyAsString();
        long count = bucket.getDocCount();
        ParsedAvg avgPrice = bucket.getAggregations().get("avg_price");
        System.out.printf("分类: %s, 数量: %d, 均价: %.2f%n",
            category, count, avgPrice.getValue());
    }
}
```

---

## 4. 集群规划与调优

### 集群规划

```
生产环境推荐：
- 节点数：3+（奇数，避免脑裂）
- Master节点：3个（专任，不存数据）
- Data节点：按数据量计算（每节点≤30TB）
- Coordinating节点：2+（专任查询路由）

容量规划：
- 单分片大小：30-50GB
- 分片数 = 数据量GB / 50GB（向上取整）
- 副本数：1-2（根据可用性需求）
```

### JVM调优

```bash
# elasticsearch.yml / jvm.options
-Xms31g      # 堆内存 = 物理内存的50%，不超过31GB
-Xmx31g      # Xms=Xmx，避免动态扩容
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:InitiatingHeapOccupancyPercent=35

# 关键配置
indices.fielddata.cache.size: 40%   # FieldData缓存
indices.queries.cache.size: 10%      # 查询缓存
thread_pool.search.queue_size: 1000  # 搜索线程池
```

### 索引调优

```json
// 索引设置优化
PUT /my_index {
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "30s",     // 写入密集场景调大
    "translog.durability": "async", // 异步刷盘（牺牲少量可靠性换性能）
    "translog.sync_interval": "30s",
    "index.codec": "best_compression", // 压缩存储
    "index.routing.allocation.total_shards_per_node": 2 // 每节点分片数限制
  }
}
```

---

## 5. 与数据库同步方案

### 方案对比

| 方案 | 延迟 | 复杂度 | 可靠性 | 适用场景 |
|------|------|--------|--------|---------|
| 同步双写 | 无 | 低 | 一般 | 写入量小 |
| 异步MQ | 秒级 | 中 | 高 | 通用 |
| Canal同步 | 秒级 | 高 | 高 | 不能改代码 |
| Logstash | 分钟级 | 低 | 中 | 简单场景 |

### Canal同步架构

```
MySQL → Canal → Kafka → ES

1. Canal伪装MySQL从库，解析Binlog
2. 变更事件发送到Kafka
3. 消费Kafka消息写入ES
```

```java
// Canal + Kafka 消费者写入ES
@KafkaListener(topics = "canal-product")
public void handleCanalEvent(String message) {
    CanalMessage canalMsg = JSON.parseObject(message, CanalMessage.class);
    
    if (canalMsg.getType() == EventType.INSERT) {
        Product product = convertToProduct(canalMsg.getData());
        productRepository.save(product);  // 写入ES
    } else if (canalMsg.getType() == EventType.UPDATE) {
        Product product = convertToProduct(canalMsg.getData());
        productRepository.save(product);
    } else if (canalMsg.getType() == EventType.DELETE) {
        productRepository.deleteById(canalMsg.getData().get("id"));
    }
}
```

---

## 6. 面试要点

### Q1: ES为什么是近实时搜索？

```
ES写入文档后不是立即可搜索的，默认1秒后可见（refresh_interval=1s）

原因：写入先到Indexing Buffer，refresh时才生成Segment到磁盘
          Buffer → refresh → Segment（可搜索）

如果需要写入立即可搜索，可以手动refresh，但性能开销大
```

### Q2: 如何优化ES查询性能？

```
1. 使用Filter代替Query（Filter不计算相关性评分，且会缓存）
2. 避免深分页（from + size > 10000用search_after替代）
3. 合理设置分片数（单分片30-50GB）
4. 使用routing定向路由（减少分片扫描）
5. 字段映射优化：keyword精确匹配，text全文检索
6. 关闭不需要的字段索引和_source
```

### Q3: ES脑裂问题如何解决？

```
ES 7.0+自动解决脑裂：
- 废弃minimum_master_nodes配置
- 引入Cluster State Quorum机制
- Master选举需要多数派投票

旧版本方案：
- 设置 discovery.zen.minimum_master_nodes = (master节点数 / 2) + 1
```

### Q4: 深分页性能问题如何解决？

```json
// 方案1: search_after（推荐）
GET /products/_search {
  "size": 100,
  "sort": [{ "id": "asc" }],
  "search_after": [12345]  // 上一页最后一条的排序值
}

// 方案2: Scroll（适合导出场景）
GET /products/_search?scroll=5m {
  "size": 1000
}
```

---

## 📚 相关阅读

- [01_Elasticsearch核心原理](./01_Elasticsearch核心原理.md)
- [MySQL核心机制详解](../03_数据库/04_MySQL核心机制详解.md)
- [Kafka核心机制详解](../05_消息队列/01_Kafka核心机制详解.md)

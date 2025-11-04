# Spring AI智能推荐系统实战

> Spring AI + Milvus向量数据库构建电商智能推荐系统

---

## 📋 概述

**Spring AI智能推荐系统**是基于Spring AI框架和Milvus向量数据库构建的电商智能推荐解决方案，实现了基于用户行为的个性化商品推荐功能。

### 核心功能
- ✅ 用户兴趣建模
- ✅ 商品向量生成
- ✅ 向量相似度计算
- ✅ 实时推荐服务
- ✅ 热门商品推荐

### 技术栈
- **Spring AI**: AI应用开发框架
- **Milvus**: 向量数据库
- **Spring Boot**: 应用框架
- **Redis**: 缓存服务
- **MySQL**: 关系型数据库

---

## 📁 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     应用层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  前端应用   │  │  移动端APP  │  │  管理后台   │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │             │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────┐
│                     服务层                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │                 RecommendationService             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │  商品向量化 │  │ 用户兴趣建模│  │  推荐算法   │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└─────────┬─────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────┐
│                     数据层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Milvus    │  │    Redis    │  │   MySQL     │      │
│  │  向量存储   │  │  缓存服务   │  │  关系数据   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 核心代码实现

### 1. 推荐服务核心类

```java
@Service
public class RecommendationService {
    private static final String BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    private static final int SHORT_URL_LENGTH = 6;
    private final AiClient aiClient;
    private final MilvusClient milvusClient;
    private final ProductRepository productRepository;
    private final UserBehaviorRepository userBehaviorRepository;
    
    @Value("${milvus.collection.name}")
    private String collectionName;
    
    public RecommendationService(AiClient aiClient, MilvusClient milvusClient, 
                               ProductRepository productRepository, UserBehaviorRepository userBehaviorRepository) {
        this.aiClient = aiClient;
        this.milvusClient = milvusClient;
        this.productRepository = productRepository;
        this.userBehaviorRepository = userBehaviorRepository;
    }
    
    // 生成商品向量
    public void generateProductEmbeddings() {
        List<Product> products = productRepository.findAll();
        for (Product product : products) {
            String prompt = String.format("生成商品向量: %s, 类别: %s, 描述: %s",
                product.getName(), product.getCategory(), product.getDescription());
            String embedding = aiClient.embed(prompt);
            product.setEmbedding(embedding);
            productRepository.save(product);
            // 插入Milvus向量库
            insertIntoMilvus(product.getId(), embedding);
        }
    }
    
    // 获取推荐商品
    public List<Product> getRecommendations(String userId, int topK) {
        // 获取用户历史交互商品
        List<String> productIds = userBehaviorRepository.findProductIdsByUserId(userId);
        if (productIds.isEmpty()) {
            return getPopularProducts(topK);
        }
        
        // 计算用户兴趣向量
        String userEmbedding = calculateUserEmbedding(productIds);
        
        // Milvus向量相似度搜索
        SearchParam searchParam = SearchParam.newBuilder()
            .withCollectionName(collectionName)
            .withVectorFieldName("embedding")
            .withVectors(List.of(parseEmbedding(userEmbedding)))
            .withTopK(topK)
            .withMetricType(MetricType.COSINE)
            .build();
        
        SearchResults results = milvusClient.search(searchParam);
        return extractProductIds(results);
    }
    
    // 计算用户兴趣向量
    private String calculateUserEmbedding(List<String> productIds) {
        List<Product> products = productRepository.findAllById(productIds);
        List<double[]> embeddings = products.stream()
            .map(product -> parseEmbedding(product.getEmbedding()))
            .collect(Collectors.toList());
        
        // 简单平均用户所有交互商品的向量
        double[] userVector = new double[embeddings.get(0).length];
        for (double[] embedding : embeddings) {
            for (int i = 0; i < embedding.length; i++) {
                userVector[i] += embedding[i];
            }
        }
        for (int i = 0; i < userVector.length; i++) {
            userVector[i] /= embeddings.size();
        }
        
        return Arrays.toString(userVector);
    }
    
    // 将字符串格式的向量解析为double数组
    private double[] parseEmbedding(String embeddingStr) {
        return Arrays.stream(embeddingStr.replaceAll("\\[|\\]", "").split(","))
            .mapToDouble(Double::parseDouble)
            .toArray();
    }
    
    // 插入向量到Milvus
    private void insertIntoMilvus(Long productId, String embedding) {
        List<InsertParam.Field> fields = new ArrayList<>();
        fields.add(new InsertParam.Field("product_id", Collections.singletonList(productId)));
        fields.add(new InsertParam.Field("embedding", Collections.singletonList(parseEmbedding(embedding))));
        
        InsertParam insertParam = InsertParam.newBuilder()
            .withCollectionName(collectionName)
            .withFields(fields)
            .build();
        
        milvusClient.insert(insertParam);
    }
    
    // 从搜索结果中提取商品ID
    private List<Product> extractProductIds(SearchResults results) {
        List<String> productIds = new ArrayList<>();
        for (SearchResults.QueryResult queryResult : results.getQueryResults()) {
            for (SearchResults.SearchResult searchResult : queryResult.getSearchResults()) {
                productIds.add(searchResult.getID());
            }
        }
        return productRepository.findAllById(productIds);
    }
    
    // 获取热门商品（基于点击量）
    private List<Product> getPopularProducts(int topK) {
        return productRepository.findTopKByViewCount(topK);
    }
}
```

### 2. 实体类定义

```java
@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String name;
    private String category;
    private String description;
    private double price;
    private String embedding; // 商品向量
    private int viewCount; // 点击量
    
    // getter and setter methods
}

@Entity
@Table(name = "user_behavior")
public class UserBehavior {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String userId;
    private String productId;
    private String behaviorType; // view, click, purchase, etc.
    private long timestamp;
    
    // getter and setter methods
}
```

### 3. Repository层

```java
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findTop10ByOrderByViewCountDesc(); // 获取热门商品
}

@Repository
public interface UserBehaviorRepository extends JpaRepository<UserBehavior, Long> {
    List<String> findProductIdsByUserId(String userId); // 获取用户历史交互商品ID
}
```

---

## 🎯 应用场景

1. **电商平台个性化推荐**：为用户推荐感兴趣的商品
2. **内容平台推荐**：推荐文章、视频、音乐等内容
3. **社交平台推荐**：推荐好友、群组、动态等
4. **企业内部知识推荐**：推荐文档、专家、培训课程等

---

## 🔧 配置与部署

### 1. Milvus向量数据库配置

```yaml
spring:
  milvus:
    host: localhost
    port: 19530
    collection-name: product_embeddings
    vector-field-name: embedding
    vector-dimension: 1536 # 根据使用的模型调整
```

### 2. Spring AI配置

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      embedding:
        model: text-embedding-ada-002
```

### 3. 部署方式

- **Docker部署**：使用Docker Compose一键部署Spring Boot应用、Milvus向量数据库和Redis
- **Kubernetes部署**：将应用打包为Docker镜像，使用Kubernetes进行容器化部署

---

## 📊 性能优化

1. **向量缓存**：将热门商品向量缓存到Redis，减少Milvus查询压力
2. **批量处理**：批量生成商品向量，减少API调用次数
3. **异步处理**：使用Spring Async异步生成商品向量
4. **索引优化**：为Milvus向量字段创建合适的索引

---

## 🔍 监控与维护

1. **日志监控**：使用ELK Stack收集和分析应用日志
2. **性能监控**：使用Prometheus和Grafana监控系统性能
3. **向量更新策略**：定期更新商品向量，确保推荐准确性
4. **A/B测试**：通过A/B测试评估推荐算法效果

---

## 📚 相关文档

- [Spring AI详解.md](./Spring AI详解.md)
- [Java AI开发实战.md](./Java AI开发实战.md)
- [LangChain4j详解.md](./LangChain4j详解.md)

---

> 🎉 **Spring AI智能推荐系统实战** - 让你的应用拥有AI大脑！
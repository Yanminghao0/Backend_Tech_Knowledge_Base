# RAG进阶优化

> Query改写、HyDE、重排序、多路召回、RAGAS评估，从60%到95%准确率

---

## 📋 目录

1. [RAG痛点分析](#1-rag痛点分析)
2. [Query改写与扩展](#2-query改写与扩展)
3. [HyDE假设性文档嵌入](#3-hyde假设性文档嵌入)
4. [重排序（Reranking）](#4-重排序reranking)
5. [多路召回](#5-多路召回)
6. [RAGAS评估体系](#6-ragas评估体系)
7. [Java实现](#7-java实现)
8. [面试要点](#8-面试要点)

---

## 1. RAG痛点分析

| 痛点 | 原因 | 优化方向 |
|------|------|---------|
| 召回率低 | 向量检索语义偏差 | Query改写+多路召回 |
| 精确度低 | 检索结果排序不准 | 重排序（Reranking） |
| 上下文不足 | Chunk切分不合理 | 上下文扩展+父子文档 |
| 幻觉 | 检索结果无关 | 相似度阈值+Prompt约束 |
| 延迟高 | 多步处理 | 异步并行+缓存 |

---

## 2. Query改写与扩展

### Query改写

```java
@Service
public class QueryRewriter {
    
    @Autowired private ChatClient chatClient;
    
    // 1. 多查询生成（Multi-Query）
    public List<String> multiQuery(String originalQuery) {
        String prompt = """
            将以下问题改写为3个不同角度的等价问题，用于检索：
            原始问题：%s
            
            输出JSON数组，如：["改写1", "改写2", "改写3"]
            """.formatted(originalQuery);
        
        String response = chatClient.prompt().user(prompt).call().content();
        return parseJsonArray(response);
    }
    
    // 2. 子问题分解（Decomposition）
    public List<String> decompose(String complexQuery) {
        String prompt = """
            将以下复杂问题分解为多个简单子问题：
            复杂问题：%s
            
            输出JSON数组。
            示例：
            问题："对比Java和Go在高并发场景的优劣"
            分解：["Java高并发性能如何", "Go高并发性能如何", "Java和Go并发模型差异"]
            """.formatted(complexQuery);
        
        return parseJsonArray(chatClient.prompt().user(prompt).call().content());
    }
    
    // 3. 对话上下文改写（Contextual Query）
    public String rewriteWithContext(String currentQuery, List<String> history) {
        String prompt = """
            根据对话历史，将当前问题改写为独立的检索query：
            
            对话历史：
            %s
            
            当前问题：%s
            
            改写后的query（包含完整上下文，可直接用于检索）：
            """.formatted(String.join("\n", history), currentQuery);
        
        return chatClient.prompt().user(prompt).call().content().trim();
    }
}
```

### 同义词扩展

```java
@Service
public class QueryExpander {
    
    // 同义词扩展：增加检索覆盖
    public String expand(String query) {
        Map<String, List<String>> synonyms = Map.of(
            "部署", List.of("上线", "发布", "deploy"),
            "性能", List.of("效率", "速度", "performance"),
            "架构", List.of("设计", "结构", "architecture")
        );
        
        String expanded = query;
        for (var entry : synonyms.entrySet()) {
            if (query.contains(entry.getKey())) {
                expanded += " " + String.join(" ", entry.getValue());
            }
        }
        return expanded;
    }
}
```

---

## 3. HyDE假设性文档嵌入

### 原理

```
HyDE (Hypothetical Document Embeddings)：

普通检索：query向量化 → 检索文档
问题：query是短文本，文档是长文本，向量空间不对齐

HyDE检索：
  1. LLM根据query生成一个"假设性回答"（假文档）
  2. 将假文档向量化 → 检索真实文档
  3. 假文档与真实文档在同一个语义空间 → 检索更准

效果：召回率提升10-20%
```

### Java实现

```java
@Service
public class HydeRetriever {
    
    @Autowired private ChatClient chatClient;
    @Autowired private VectorStore vectorStore;
    
    public List<Document> retrieve(String query, int topK) {
        // 1. LLM生成假设性回答
        String hypotheticalDoc = chatClient.prompt()
            .user("请用2-3句话简要回答以下问题（不需要完全准确，用于检索）：\n" + query)
            .call()
            .content();
        
        // 2. 用假设性回答向量化检索
        return vectorStore.similaritySearch(
            SearchRequest.builder()
                .query(hypotheticalDoc)  // 用假文档而非原始query
                .topK(topK)
                .similarityThreshold(0.6)
                .build());
    }
}
```

---

## 4. 重排序（Reranking）

### 为什么需要重排序

```
向量检索（Bi-Encoder）：
  Query和Document独立编码 → 余弦相似度
  速度快，但精度有限（不理解Query-Doc交互）

重排序（Cross-Encoder）：
  Query和Document拼接后一起编码 → 相关性分数
  精度高，但速度慢（每对Query-Doc都要计算）

策略：向量检索召回Top-50 → Cross-Encoder重排取Top-5
```

### Java实现

```java
@Service
public class RerankingService {
    
    @Autowired private ChatClient chatClient;
    
    // LLM重排序：让LLM对检索结果打分
    public List<Document> rerank(String query, List<Document> candidates, int topK) {
        String prompt = """
            对以下文档按与问题的相关性打分（1-10分），输出JSON：
            问题：%s
            
            文档列表：
            %s
            
            输出格式：[{"index": 0, "score": 9}, {"index": 1, "score": 5}]
            """.formatted(query, formatDocuments(candidates));
        
        String response = chatClient.prompt().user(prompt).call().content();
        List<ScoreItem> scores = parseScores(response);
        
        // 按分数排序取TopK
        return scores.stream()
            .sorted((a, b) -> Integer.compare(b.score, a.score))
            .limit(topK)
            .map(s -> candidates.get(s.index))
            .collect(Collectors.toList());
    }
    
    // 使用专门的Reranker模型（BGE-Reranker等）
    public List<Document> rerankWithModel(String query, List<Document> candidates, int topK) {
        // 调用BGE-Reranker API
        List<RerankResult> results = rerankerApi.rerank(query, 
            candidates.stream().map(Document::getText).toList());
        
        return results.stream()
            .sorted(Comparator.comparingDouble(RerankResult::getScore).reversed())
            .limit(topK)
            .map(r -> candidates.get(r.getIndex()))
            .collect(Collectors.toList());
    }
}
```

---

## 5. 多路召回

### 架构

```
              Query
               │
    ┌──────────┼──────────┐
    │          │          │
  向量检索   BM25检索   HyDE检索
  (语义)    (关键词)   (假设文档)
    │          │          │
    └──────────┼──────────┘
               │
         RRF融合排序
               │
          重排序Rerank
               │
           Top-K结果
```

### Java实现

```java
@Service
public class MultiRetrievalService {
    
    @Autowired private VectorStore vectorStore;
    @Autowired private ElasticsearchClient esClient;
    @Autowired private HydeRetriever hydeRetriever;
    @Autowired private RerankingService reranker;
    
    public List<Document> search(String query, int topK) {
        // 并行多路召回
        CompletableFuture<List<Document>> vectorFuture = CompletableFuture.supplyAsync(
            () -> vectorStore.similaritySearch(
                SearchRequest.builder().query(query).topK(topK * 3).build()));
        
        CompletableFuture<List<Document>> bm25Future = CompletableFuture.supplyAsync(
            () -> esClient.searchByKeyword(query, topK * 3));
        
        CompletableFuture<List<Document>> hydeFuture = CompletableFuture.supplyAsync(
            () -> hydeRetriever.retrieve(query, topK * 3));
        
        // 等待全部完成
        CompletableFuture.allOf(vectorFuture, bm25Future, hydeFuture).join();
        
        // RRF融合
        List<Document> merged = rrfFusion(
            vectorFuture.join(), bm25Future.join(), hydeFuture.join(), topK * 2);
        
        // 重排序取TopK
        return reranker.rerank(query, merged, topK);
    }
    
    // RRF (Reciprocal Rank Fusion)
    private List<Document> rrfFusion(List<Document>... lists) {
        int k = 60;
        Map<String, Double> scores = new HashMap<>();
        Map<String, Document> docMap = new HashMap<>();
        
        for (List<Document> list : lists) {
            for (int i = 0; i < list.size(); i++) {
                String id = list.get(i).getId();
                scores.merge(id, 1.0 / (k + i + 1), Double::sum);
                docMap.putIfAbsent(id, list.get(i));
            }
        }
        
        return scores.entrySet().stream()
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .map(e -> docMap.get(e.getKey()))
            .collect(Collectors.toList());
    }
}
```

---

## 6. RAGAS评估体系

### 评估指标

```
RAGAS (RAG Assessment)：

检索质量：
  - Context Precision: 检索结果中相关文档的比例
  - Context Recall: 相关文档被检索到的比例

生成质量：
  - Faithfulness: 回答是否忠于上下文（不幻觉）
  - Answer Relevancy: 回答与问题的相关性
```

### Java实现

```java
@Service
public class RagEvaluator {
    
    @Autowired private ChatClient chatClient;
    
    public RagEvaluation evaluate(String question, String answer, 
            List<String> contexts, String groundTruth) {
        
        // 1. Faithfulness：回答是否忠于上下文
        double faithfulness = evaluateFaithfulness(answer, contexts);
        
        // 2. Answer Relevancy：回答与问题的相关性
        double relevancy = evaluateRelevancy(question, answer);
        
        // 3. Context Precision：检索结果精确度
        double precision = evaluatePrecision(question, contexts);
        
        // 4. Context Recall：检索结果召回率
        double recall = evaluateRecall(groundTruth, contexts);
        
        return new RagEvaluation(faithfulness, relevancy, precision, recall);
    }
    
    private double evaluateFaithfulness(String answer, List<String> contexts) {
        String prompt = """
            判断以下回答是否完全基于给定上下文（不包含上下文外的信息）。
            
            上下文：%s
            回答：%s
            
            输出0-1之间的分数（1=完全忠于上下文，0=完全无关）
            """.formatted(String.join("\n", contexts), answer);
        
        return Double.parseDouble(chatClient.prompt().user(prompt).call().content().trim());
    }
}
```

---

## 7. 完整进阶RAG流水线

```java
@Service
public class AdvancedRagService {
    
    @Autowired private QueryRewriter queryRewriter;
    @Autowired private MultiRetrievalService retrievalService;
    @Autowired private RerankingService reranker;
    @Autowired private RagEvaluator evaluator;
    @Autowired private ChatClient chatClient;
    
    public RagResponse ask(String question, List<String> chatHistory) {
        // 1. Query改写（结合对话上下文）
        String rewrittenQuery = queryRewriter.rewriteWithContext(question, chatHistory);
        
        // 2. 多路召回 + 重排序
        List<Document> docs = retrievalService.search(rewrittenQuery, 5);
        
        // 3. 组装Prompt
        String context = docs.stream()
            .map(d -> d.getText())
            .collect(Collectors.joining("\n---\n"));
        
        String prompt = buildPrompt(question, context);
        
        // 4. LLM生成
        String answer = chatClient.prompt().user(prompt).call().content();
        
        // 5. 评估（可选，离线评估）
        // RagEvaluation eval = evaluator.evaluate(question, answer, ...);
        
        return new RagResponse(answer, docs.stream().map(d -> 
            new Citation(d.getMetadata().get("source"))).toList());
    }
}
```

---

## 8. 面试要点

### Q1: RAG的检索准确率怎么提升？

```
1. Query改写：多Query生成/子问题分解/对话上下文改写
2. HyDE：生成假设性文档→用假文档检索（对齐语义空间）
3. 多路召回：向量+BM25+HyDE，RRF融合
4. 重排序：Cross-Encoder对Top-50重排取Top-5
5. Chunk优化：合理大小+重叠+父子文档
6. 评估：RAGAS持续评估迭代
```

### Q2: HyDE为什么有效？

```
问题：Query是短文本，Document是长文本，向量空间不对齐
HyDE：LLM生成假设性回答（长文本）→ 向量化检索

假文档与真文档在相同语义空间 → 检索更准
代价：多一次LLM调用（~500ms延迟）
```

### Q3: 重排序为什么用Cross-Encoder？

```
Bi-Encoder（向量检索）：Query和Doc独立编码，速度快但精度低
Cross-Encoder（重排序）：Query+Doc拼接编码，精度高但速度慢

策略：Bi-Encoder召回Top-50 → Cross-Encoder重排Top-5
效果：精度提升15-25%，延迟增加~200ms
```

### Q4: RAGAS评估体系有哪些指标？

```
1. Faithfulness：回答是否忠于上下文（防幻觉）
2. Answer Relevancy：回答与问题的相关性
3. Context Precision：检索结果中相关的比例
4. Context Recall：相关文档被检索到的比例

目标：Faithfulness > 0.9, Relevancy > 0.85
```

---

## 📚 相关阅读

- [08_RAG架构深度实战](./08_RAG架构深度实战.md)
- [09_向量数据库选型](./09_向量数据库选型.md)
- [11_Prompt工程进阶](./11_Prompt工程进阶.md)
- [02_Elasticsearch深度实战](../09_搜索引擎/02_Elasticsearch深度实战.md)

# RAG架构深度实战

> 从文档切分到混合检索，构建企业级RAG检索增强生成系统

---

## 📋 目录

1. [RAG概述](#1-rag概述)
2. [文档处理流水线](#2-文档处理流水线)
3. [向量化与Embedding](#3-向量化与embedding)
4. [检索策略](#4-检索策略)
5. [Prompt工程与生成](#5-prompt工程与生成)
6. [Spring Boot实现](#6-spring-boot实现)
7. [评估与优化](#7-评估与优化)
8. [面试要点](#8-面试要点)

---

## 1. RAG概述

### 什么是RAG

```
RAG (Retrieval-Augmented Generation) 检索增强生成：

传统LLM问题：
  - 知识截止日期（训练数据有时效性）
  - 无法访问企业私有数据
  - 容易产生幻觉（编造事实）
  - 无法引用信息来源

RAG解决方案：
  1. 检索：从知识库中检索相关文档片段
  2. 增强：将检索结果作为上下文注入Prompt
  3. 生成：LLM基于上下文生成回答

流程：
  用户问题 → 向量检索 → 相关文档片段 → 组装Prompt → LLM生成 → 回答+引用
```

### RAG vs Fine-tuning

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| 知识更新 | 实时（更新知识库即可） | 需重新训练 |
| 成本 | 低（无需训练） | 高（GPU训练） |
| 准确性 | 高（有据可查） | 中（可能遗忘） |
| 可解释性 | 高（可引用来源） | 低 |
| 适用场景 | 知识库问答、文档助手 | 风格学习、领域适应 |

---

## 2. 文档处理流水线

### 处理流程

```
原始文档 → 加载 → 切分 → 清洗 → 向量化 → 存储

  PDF/Word/HTML/Markdown
       ↓
  文档加载器（解析为纯文本）
       ↓
  文本切分（Chunking）
       ↓
  文本清洗（去噪、标准化）
       ↓
  Embedding模型向量化
       ↓
  向量数据库存储
```

### 文档切分策略

```java
// 切分策略对比
// 1. 固定长度切分：简单但可能截断语义
// 2. 递归字符切分：按段落→句子→字符递归切分（推荐）
// 3. 语义切分：按语义边界切分（效果最好但成本高）

// LangChain4j 递归切分
DocumentSplitter splitter = DocumentSplitters.recursive(800, 100);
// 参数：targetSize=800(每段800字符), overlap=100(重叠100字符)

// 切分效果
// 原文：Spring Boot是Spring家族的框架，它简化了Spring应用的初始搭建和开发过程...
// Chunk 1: "Spring Boot是Spring家族的框架，它简化了Spring应用的初始搭建和开发过程..." (800字符)
// Chunk 2: "...开发过程。Spring Boot通过自动配置机制..." (重叠100字符 + 新内容)
```

### Chunk大小选择

```
Chunk太小（<200字符）：
  - 语义不完整
  - 检索到碎片化信息
  - 生成回答缺乏上下文

Chunk太大（>2000字符）：
  - 向量稀释（关键信息被淹没）
  - 检索精度下降
  - Token消耗增加

推荐：
  - 通用场景：500-1000字符
  - 代码文档：按函数/类切分
  - FAQ场景：按问答对切分
  - 重叠：10-20%的chunk大小
```

### 文档加载

```java
// LangChain4j 多格式文档加载
// PDF
Document pdfDoc = FileSystemDocumentLoader.load("guide.pdf", 
    new ApacheTikaDocumentParser());

// Word
Document wordDoc = FileSystemDocumentLoader.load("spec.docx",
    new ApacheTikaDocumentParser());

// Markdown
Document mdDoc = FileSystemDocumentLoader.load("readme.md");

// URL
Document webDoc = UrlDocumentLoader.load("https://example.com/doc",
    new ApacheTikaDocumentParser());

// 批量加载
List<Document> docs = FileSystemDocumentLoader.loadAll(
    Path.of("/data/docs/"), 
    new ApacheTikaDocumentParser());
```

---

## 3. 向量化与Embedding

### Embedding模型选择

| 模型 | 维度 | 特点 | 适用 |
|------|------|------|------|
| OpenAI text-embedding-3-small | 1536 | 性价比高 | 通用 |
| OpenAI text-embedding-3-large | 3072 | 精度高 | 高精度场景 |
| BGE-large-zh | 1024 | 中文优化 | 中文知识库 |
| M3E-base | 768 | 中文开源 | 本地部署 |
| 通义千问Embedding | 1536 | 阿里云 | 国内云服务 |

### Spring AI Embedding

```java
// Spring AI + OpenAI Embedding
@Configuration
public class EmbeddingConfig {
    
    @Bean
    public EmbeddingModel embeddingModel() {
        return new OpenAiEmbeddingModel(
            OpenAiApi.builder()
                .apiKey("sk-xxx")
                .baseUrl("https://api.openai.com/v1")
                .build(),
            MetadataMode.EMBED,
            OpenAiEmbeddingOptions.builder()
                .model("text-embedding-3-small")
                .build()
        );
    }
}

// 批量向量化
@Autowired
private EmbeddingModel embeddingModel;

public List<float[]> embedDocuments(List<String> texts) {
    EmbeddingResponse response = embeddingModel.embedForResponse(texts);
    return response.getResults().stream()
        .map(Embedding::getOutput)
        .collect(Collectors.toList());
}
```

---

## 4. 检索策略

### 向量检索

```java
// Spring AI + 向量数据库检索
@Autowired
private VectorStore vectorStore;

public List<Document> retrieve(String query, int topK) {
    // 语义检索：query向量化 → 在向量库中找最相似的文档
    SearchRequest request = SearchRequest.builder()
        .query(query)
        .topK(topK)           // 返回Top K个结果
        .similarityThreshold(0.7)  // 相似度阈值
        .build();
    
    return vectorStore.similaritySearch(request);
}
```

### 混合检索（向量 + 关键词）

```java
// 混合检索：语义检索 + BM25关键词检索
@Service
public class HybridRetrievalService {
    
    @Autowired
    private VectorStore vectorStore;  // 向量检索
    
    @Autowired
    private ElasticsearchClient esClient;  // BM25关键词检索
    
    public List<Document> hybridSearch(String query, int topK) {
        // 1. 向量检索（语义相似）
        List<Document> vectorResults = vectorStore.similaritySearch(
            SearchRequest.builder().query(query).topK(topK * 2).build());
        
        // 2. BM25检索（关键词匹配）
        List<Document> keywordResults = esClient.searchByKeyword(query, topK * 2);
        
        // 3. 融合排序（RRF: Reciprocal Rank Fusion）
        return reciprocalRankFusion(vectorResults, keywordResults, topK);
    }
    
    // RRF融合算法
    private List<Document> reciprocalRankFusion(
            List<Document> vectorResults, 
            List<Document> keywordResults, 
            int topK) {
        Map<String, Double> scores = new HashMap<>();
        int k = 60; // RRF常数
        
        for (int i = 0; i < vectorResults.size(); i++) {
            String id = vectorResults.get(i).getId();
            scores.merge(id, 1.0 / (k + i + 1), Double::sum);
        }
        for (int i = 0; i < keywordResults.size(); i++) {
            String id = keywordResults.get(i).getId();
            scores.merge(id, 1.0 / (k + i + 1), Double::sum);
        }
        
        // 按融合分数排序，取TopK
        return scores.entrySet().stream()
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .limit(topK)
            .map(e -> findById(e.getKey(), vectorResults, keywordResults))
            .collect(Collectors.toList());
    }
}
```

### 检索策略对比

| 策略 | 优势 | 劣势 | 适用 |
|------|------|------|------|
| 纯向量检索 | 语义理解强 | 关键词匹配弱 | 概念性问答 |
| 纯BM25 | 关键词精确 | 无法理解语义 | 精确匹配 |
| 混合检索 | 两者优势 | 实现复杂 | 企业级RAG |
| 重排序 | 精度高 | 增加延迟 | 高精度场景 |

---

## 5. Prompt工程与生成

### Prompt模板

```java
@Service
public class RagService {
    
    private static final String RAG_PROMPT = """
        你是一个专业的技术文档助手。请基于以下检索到的上下文回答问题。
        如果上下文中没有相关信息，请回答"根据现有文档无法回答此问题"。
        回答时请标注信息来源。
        
        ## 上下文
        {context}
        
        ## 问题
        {question}
        
        ## 回答
        """;
    
    @Autowired
    private ChatClient chatClient;
    
    @Autowired
    private HybridRetrievalService retrievalService;
    
    public String ask(String question) {
        // 1. 检索相关文档
        List<Document> docs = retrievalService.hybridSearch(question, 5);
        
        // 2. 组装上下文
        String context = docs.stream()
            .map(d -> String.format("【来源: %s】\n%s", d.getMetadata().get("source"), d.getText()))
            .collect(Collectors.joining("\n\n---\n\n"));
        
        // 3. 构建Prompt
        String prompt = RAG_PROMPT
            .replace("{context}", context)
            .replace("{question}", question);
        
        // 4. LLM生成
        return chatClient.prompt(prompt).call().content();
    }
}
```

### 引用来源

```java
// 返回带引用的回答
public RagResponse askWithCitations(String question) {
    List<Document> docs = retrievalService.hybridSearch(question, 5);
    String context = buildContext(docs);
    String answer = chatClient.prompt(buildPrompt(context, question)).call().content();
    
    // 提取引用来源
    List<Citation> citations = docs.stream()
        .map(d -> new Citation(
            d.getMetadata().get("source"),
            d.getMetadata().get("page"),
            d.getText().substring(0, 100) + "..."
        ))
        .collect(Collectors.toList());
    
    return new RagResponse(answer, citations);
}
```

---

## 6. Spring Boot实现

### 完整RAG系统

```java
@Configuration
public class RagConfig {
    
    @Bean
    public VectorStore vectorStore(EmbeddingModel embeddingModel) {
        return PgVectorStore.builder(jdbcTemplate, embeddingModel)
            .dimensions(1536)
            .distanceType(CosineDistance)
            .build();
    }
    
    @Bean
    public ChatClient chatClient(ChatClient.Builder builder) {
        return builder.build();
    }
}

@RestController
@RequestMapping("/api/rag")
public class RagController {
    
    @Autowired
    private RagService ragService;
    
    @PostMapping("/ask")
    public RagResponse ask(@RequestBody QuestionRequest request) {
        return ragService.askWithCitations(request.getQuestion());
    }
    
    @PostMapping("/upload")
    public UploadResponse upload(@RequestParam MultipartFile file) {
        // 1. 解析文档
        Document doc = parseDocument(file);
        // 2. 切分
        List<Document> chunks = splitter.split(doc, 800, 100);
        // 3. 向量化+存储
        vectorStore.add(chunks);
        return UploadResponse.success(chunks.size());
    }
}
```

---

## 7. 评估与优化

### RAG评估指标

```
检索质量：
  - Recall@K: Top K结果中包含正确答案的比例
  - MRR (Mean Reciprocal Rank): 正确答案的平均排名倒数
  - NDCG: 归一化折损累计增益

生成质量：
  - Faithfulness: 回答是否忠于上下文（不幻觉）
  - Answer Relevance: 回答与问题的相关性
  - Context Relevance: 检索上下文与问题的相关性
```

### 常见优化方向

```
检索优化：
  1. Query改写：将用户问题改写为更适合检索的形式
  2. Query扩展：同义词扩展、HyDE（假设性文档嵌入）
  3. 重排序：用Cross-Encoder对初步检索结果重排序
  4. 元数据过滤：按文档类型、时间等过滤

生成优化：
  1. Prompt优化：调整上下文格式、指令
  2. Chain of Thought：引导LLM逐步推理
  3. 自我验证：让LLM验证回答是否忠于上下文
  4. 多轮对话：支持上下文追问
```

---

## 8. 面试要点

### Q1: RAG的原理是什么？

```
RAG = 检索 + 增强 + 生成

1. 检索：用户问题向量化，在向量数据库中检索相关文档片段
2. 增强：将检索到的文档作为上下文注入Prompt
3. 生成：LLM基于上下文生成回答

核心价值：让LLM能访问最新/私有数据，减少幻觉
```

### Q2: 如何选择Chunk大小？

```
Chunk太小：语义不完整，检索碎片化
Chunk太大：向量稀释，检索精度下降

选择依据：
  - 通用场景：500-1000字符
  - 代码文档：按函数/类切分
  - FAQ：按问答对切分
  - 重叠：10-20%避免语义截断
```

### Q3: 向量检索和关键词检索有什么区别？

```
向量检索（语义）：
  - 理解语义："如何部署应用" 能匹配到 "应用上线流程"
  - 不依赖关键词完全匹配
  - 适合概念性问答

关键词检索（BM25）：
  - 精确匹配关键词
  - 适合专有名词、代码、错误码
  - 不理解语义

混合检索（推荐）：两者结合，RRF融合排序
```

### Q4: 如何减少RAG的幻觉？

```
1. Prompt明确要求："如果上下文中没有相关信息，请回答'无法回答'"
2. 相似度阈值：过滤掉低相关性的检索结果
3. 引用来源：要求LLM标注信息来源
4. 自我验证：生成后再验证是否忠于上下文
5. 多路召回：混合检索提高召回率
```

### Q5: RAG和Fine-tuning怎么选？

```
选RAG：
  - 知识需要频繁更新
  - 需要引用来源
  - 数据量大（TB级）
  - 成本敏感

选Fine-tuning：
  - 需要学习特定风格/格式
  - 领域知识相对固定
  - 对延迟要求高（减少检索环节）

两者可结合：Fine-tune模型能力 + RAG提供知识
```

---

## 📚 相关阅读

- [03_Java AI开发实战](./03_Java AI开发实战.md)
- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [06_Spring AI详解](./06_Spring AI详解.md)
- [MCP协议核心原理与实战](../15_MCP协议/03_MCP协议核心原理与实战.md)

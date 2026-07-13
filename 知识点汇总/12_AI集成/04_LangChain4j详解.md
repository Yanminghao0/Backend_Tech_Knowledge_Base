# LangChain4j详解

> 深入理解LangChain4j框架：Java生态最强大的AI应用开发框架

---

## 📋 目录

1. [LangChain4j概述](#1-langchain4j概述)
2. [核心架构](#2-核心架构)
3. [快速开始](#3-快速开始)
4. [LLM集成](#4-llm集成)
5. [向量存储](#5-向量存储)
6. [RAG实现](#6-rag实现)
7. [Function Calling](#7-function-calling)
8. [AI Agent](#8-ai-agent)
9. [对话记忆](#9-对话记忆)
10. [高级特性](#10-高级特性)
11. [最佳实践](#11-最佳实践)

---

## 1. LangChain4j概述

### 1.1 什么是LangChain4j

```
LangChain4j：
- Java版本的LangChain框架
- 专为Java开发者设计的AI应用开发框架
- 支持多种LLM（OpenAI、Claude、通义千问等）
- 提供RAG、Agent、Function Calling等高级功能
- 与Spring Boot无缝集成
```

### 1.2 核心特性

```
✅ 多LLM支持：
   - OpenAI（GPT-4、GPT-3.5）
   - Anthropic Claude
   - 通义千问、文心一言
   - 本地模型（Ollama）

✅ 向量数据库集成：
   - Milvus、Pinecone、Weaviate
   - Qdrant、Elasticsearch
   - 内存向量存储

✅ RAG支持：
   - 文档加载和切分
   - 向量化和检索
   - 上下文管理

✅ Function Calling：
   - 工具调用
   - 多工具协调
   - 参数验证

✅ AI Agent：
   - 多步推理
   - 自主决策
   - 记忆管理

✅ Spring Boot集成：
   - 自动配置
   - 依赖注入
   - 配置管理
```

---

## 2. 核心架构

### 2.1 架构设计

LangChain4j采用分层架构设计：

```
应用层
  ↓
LangChain4j Core（核心层）
  ↓
├── LLM集成层（OpenAI、Claude等）
├── 向量存储层（Milvus、Pinecone等）
├── 文档处理层（加载、切分、向量化）
└── Agent层（推理、工具调用、记忆管理）
```

### 2.2 核心组件

```
1. ChatLanguageModel：
   - 对话模型接口
   - 支持流式和非流式响应
   - 统一API调用不同LLM

2. EmbeddingModel：
   - 向量化模型
   - 文本转向量
   - 支持多种Embedding模型

3. VectorStore：
   - 向量存储接口
   - 支持多种向量数据库
   - 统一检索API

4. DocumentLoader：
   - 文档加载器
   - 支持多种格式（PDF、TXT、Markdown等）
   - 自动解析和提取

5. TextSplitter：
   - 文档切分器
   - 支持多种切分策略
   - 语义边界切分

6. Agent：
   - AI智能体
   - 工具调用
   - 多步推理
```

---

## 3. 快速开始

### 3.1 Maven依赖

```xml
<dependencies>
    <!-- LangChain4j核心 -->
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j</artifactId>
        <version>0.28.0</version>
    </dependency>
    
    <!-- OpenAI集成 -->
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-open-ai</artifactId>
        <version>0.28.0</version>
    </dependency>
    
    <!-- Spring Boot集成 -->
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-spring-boot-starter</artifactId>
        <version>0.28.0</version>
    </dependency>
    
    <!-- 向量存储（Milvus） -->
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-milvus</artifactId>
        <version>0.28.0</version>
    </dependency>
</dependencies>
```

### 3.2 配置文件

```yaml
langchain4j:
  open-ai:
    api-key: ${OPENAI_API_KEY}
    model-name: gpt-4
    temperature: 0.7
    timeout: 60s
    max-retries: 3
    log-requests: true
    log-responses: true
```

### 3.3 基础使用

```java
@RestController
@RequestMapping("/ai")
public class AIController {
    
    @Autowired
    private ChatLanguageModel chatModel;
    
    @PostMapping("/chat")
    public String chat(@RequestBody ChatRequest request) {
        return chatModel.generate(request.getMessage());
    }
    
    @PostMapping("/chat/stream")
    public Flux<String> chatStream(@RequestBody ChatRequest request) {
        return Flux.create(sink -> {
            chatModel.generateStream(request.getMessage())
                .forEach(token -> sink.next(token));
            sink.complete();
        });
    }
}
```

---

## 4. LLM集成

### 4.1 OpenAI集成

```java
// 创建OpenAI模型
OpenAiChatModel model = OpenAiChatModel.builder()
    .apiKey("sk-xxx")
    .modelName("gpt-4")
    .temperature(0.7)
    .maxTokens(1000)
    .timeout(Duration.ofSeconds(60))
    .maxRetries(3)
    .logRequests(true)
    .logResponses(true)
    .build();

// 使用
String response = model.generate("你好");
```

### 4.2 Claude集成

```java
// Maven依赖
<dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-anthropic</artifactId>
    <version>0.28.0</version>
</dependency>

// 创建Claude模型
AnthropicChatModel model = AnthropicChatModel.builder()
    .apiKey("sk-ant-xxx")
    .modelName("claude-3-5-sonnet-20241022")
    .temperature(0.7)
    .maxTokens(1000)
    .build();
```

### 4.3 通义千问集成

```java
// Maven依赖
<dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-qianfan</artifactId>
    <version>0.28.0</version>
</dependency>

// 创建通义千问模型
QianfanChatModel model = QianfanChatModel.builder()
    .apiKey("xxx")
    .secretKey("xxx")
    .modelName("qwen-plus")
    .temperature(0.7)
    .build();
```

### 4.4 本地模型（Ollama）

```java
// Maven依赖
<dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-ollama</artifactId>
    <version>0.28.0</version>
</dependency>

// 创建Ollama模型
OllamaChatModel model = OllamaChatModel.builder()
    .baseUrl("http://localhost:11434")
    .modelName("llama2")
    .temperature(0.7)
    .build();
```

---

## 5. 向量存储

### 5.1 Milvus集成

```java
// 创建Milvus向量存储
MilvusEmbeddingStore<TextSegment> embeddingStore = MilvusEmbeddingStore.builder()
    .host("localhost")
    .port(19530)
    .collectionName("documents")
    .dimension(1536) // OpenAI embedding维度
    .build();

// 存储向量
String id = embeddingStore.add(embedding, segment);

// 检索相似向量
List<EmbeddingMatch<TextSegment>> matches = embeddingStore.findRelevant(
    queryEmbedding, 
    10,  // top-k
    0.7  // 最小相似度
);
```

### 5.2 Pinecone集成

```java
// Maven依赖
<dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-pinecone</artifactId>
    <version>0.28.0</version>
</dependency>

// 创建Pinecone向量存储
PineconeEmbeddingStore<TextSegment> embeddingStore = PineconeEmbeddingStore.builder()
    .apiKey("xxx")
    .environment("us-west1-gcp")
    .indexName("documents")
    .dimension(1536)
    .build();
```

### 5.3 内存向量存储

```java
// 内存向量存储（适合开发测试）
InMemoryEmbeddingStore<TextSegment> embeddingStore = 
    new InMemoryEmbeddingStore<>();

// 存储
embeddingStore.add(id, embedding, segment);

// 检索
List<EmbeddingMatch<TextSegment>> matches = embeddingStore.findRelevant(
    queryEmbedding, 
    10
);
```

---

## 6. RAG实现

### 6.1 完整RAG流程

```java
@Service
public class RAGService {
    
    @Autowired
    private EmbeddingModel embeddingModel;
    
    @Autowired
    private EmbeddingStore<TextSegment> embeddingStore;
    
    @Autowired
    private ChatLanguageModel chatModel;
    
    // 1. 文档加载和切分
    public void loadDocuments(String documentPath) {
        DocumentLoader loader = new FileSystemDocumentLoader();
        Document document = loader.load(documentPath);
        
        TextSplitter splitter = DocumentSplitters.recursive(
            1000,  // chunk size
            200    // chunk overlap
        );
        
        List<TextSegment> segments = splitter.split(document);
        
        // 2. 向量化并存储
        for (TextSegment segment : segments) {
            Embedding embedding = embeddingModel.embed(segment).content();
            embeddingStore.add(embedding, segment);
        }
    }
    
    // 3. 检索和生成
    public String query(String question) {
        // 查询向量化
        Embedding queryEmbedding = embeddingModel.embed(question).content();
        
        // 检索相关文档
        List<EmbeddingMatch<TextSegment>> matches = embeddingStore.findRelevant(
            queryEmbedding, 
            5,     // top-5
            0.7    // 最小相似度
        );
        
        // 构建上下文
        StringBuilder context = new StringBuilder();
        for (EmbeddingMatch<TextSegment> match : matches) {
            context.append(match.embedded().text()).append("\n\n");
        }
        
        // 构建Prompt
        String prompt = String.format(
            "基于以下上下文回答问题：\n\n%s\n\n问题：%s\n\n答案：",
            context.toString(),
            question
        );
        
        // 生成答案
        return chatModel.generate(prompt);
    }
}
```

---

## 7. Function Calling

### 7.1 定义工具

```java
// 定义工具接口
public interface WeatherTool {
    @Tool("获取指定城市的天气信息")
    String getWeather(
        @P("城市名称") String city,
        @P("温度单位，celsius或fahrenheit") String unit
    );
}

// 实现工具
@Component
public class WeatherToolImpl implements WeatherTool {
    @Override
    public String getWeather(String city, String unit) {
        // 调用天气API
        return "北京：25°C，晴天";
    }
}
```

### 7.2 使用Function Calling

```java
@Service
public class FunctionCallingService {
    
    @Autowired
    private ChatLanguageModel chatModel;
    
    @Autowired
    private WeatherTool weatherTool;
    
    public String chatWithTools(String userMessage) {
        // 创建工具列表
        List<ChatMemoryMessage> tools = List.of(
            AiMessage.from(weatherTool)
        );
        
        // 创建带工具的对话
        ChatMemory memory = MessageWindowChatMemory.withMaxMessages(10);
        memory.add(UserMessage.from(userMessage));
        
        // 调用模型（支持Function Calling）
        AiMessage aiMessage = chatModel.generate(
            memory.messages(),
            tools
        );
        
        // 检查是否有工具调用
        if (aiMessage.hasToolExecutions()) {
            // 执行工具调用
            for (ToolExecution toolExecution : aiMessage.toolExecutions()) {
                String result = executeTool(toolExecution);
                memory.add(AiMessage.from(result));
            }
            
            // 再次调用模型生成最终答案
            aiMessage = chatModel.generate(memory.messages());
        }
        
        memory.add(aiMessage);
        return aiMessage.text();
    }
}
```

---

## 8. AI Agent

### 8.1 基础Agent

```java
@Service
public class BasicAgentService {
    
    @Autowired
    private ChatLanguageModel chatModel;
    
    public String agentChat(String userMessage) {
        // 创建Agent
        Agent agent = Agent.builder()
            .chatLanguageModel(chatModel)
            .tools(createTools())
            .memory(MessageWindowChatMemory.withMaxMessages(20))
            .systemMessage("你是一个智能助手，可以帮助用户完成各种任务。")
            .build();
        
        // Agent对话
        return agent.chat(userMessage);
    }
    
    private List<Object> createTools() {
        return List.of(
            new WeatherTool(),
            new CalculatorTool(),
            new SearchTool()
        );
    }
}
```

---

## 9. 对话记忆

### 9.1 内存记忆

```java
// 窗口记忆（固定消息数）
ChatMemory memory = MessageWindowChatMemory.withMaxMessages(10);

// 时间窗口记忆
ChatMemory memory = MessageWindowChatMemory.withMaxTokens(
    1000,  // 最大token数
    Duration.ofHours(1)  // 时间窗口
);
```

### 9.2 持久化记忆

```java
// Redis记忆存储
ChatMemory memory = RedisChatMemory.builder()
    .redisClient(redisClient)
    .sessionId("user-123")
    .maxMessages(20)
    .build();

// 数据库记忆存储
ChatMemory memory = JdbcChatMemory.builder()
    .dataSource(dataSource)
    .sessionId("user-123")
    .maxMessages(20)
    .build();
```

---

## 10. 高级特性

### 10.1 流式响应

```java
@GetMapping("/stream")
public Flux<ServerSentEvent<String>> streamChat(String message) {
    return Flux.create(sink -> {
        chatModel.generateStream(message)
            .forEach(token -> {
                sink.next(ServerSentEvent.<String>builder()
                    .data(token)
                    .build());
            });
        sink.complete();
    });
}
```

### 10.2 错误处理和重试

```java
@Service
public class RobustAIService {
    
    @Retryable(
        value = {Exception.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2)
    )
    public String chatWithRetry(String message) {
        try {
            return chatModel.generate(message);
        } catch (Exception e) {
            log.error("AI调用失败", e);
            throw e;
        }
    }
}
```

---

## 11. 最佳实践

### 11.1 配置管理

```yaml
# application.yml
langchain4j:
  open-ai:
    api-key: ${OPENAI_API_KEY}
    model-name: gpt-4
    temperature: 0.7
    timeout: 60s
    max-retries: 3
    log-requests: ${LOG_AI_REQUESTS:false}
    log-responses: ${LOG_AI_RESPONSES:false}
```

### 11.2 成本控制

```java
@Service
public class CostOptimizedService {
    
    // 缓存常见问题
    @Cacheable(value = "ai-responses", key = "#message")
    public String chat(String message) {
        return chatModel.generate(message);
    }
    
    // 使用更便宜的模型处理简单问题
    public String smartChat(String message) {
        if (isSimpleQuestion(message)) {
            return cheapModel.generate(message);
        } else {
            return expensiveModel.generate(message);
        }
    }
}
```

### 11.3 安全性

```java
@Service
public class SecureAIService {
    
    // 输入验证
    public String safeChat(String message) {
        // 1. 内容审核
        if (containsSensitiveContent(message)) {
            throw new IllegalArgumentException("输入包含敏感内容");
        }
        
        // 2. 长度限制
        if (message.length() > 10000) {
            throw new IllegalArgumentException("输入过长");
        }
        
        // 3. 调用AI
        String response = chatModel.generate(message);
        
        // 4. 输出过滤
        return filterOutput(response);
    }
}
```

---

## 📚 参考资源

- 🔗 [LangChain4j官方文档](https://docs.langchain4j.dev/)
- 🔗 [GitHub仓库](https://github.com/langchain4j/langchain4j)
- 🔗 [示例代码](https://github.com/langchain4j/langchain4j-examples)

---

*最后更新：2025-11-04*

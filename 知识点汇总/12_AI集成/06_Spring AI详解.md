# Spring AI详解

> Spring官方AI框架：与Spring生态深度集成的AI应用开发框架

---

## 📋 目录

1. [Spring AI概述](#1-spring-ai概述)
2. [核心架构](#2-核心架构)
3. [快速开始](#3-快速开始)
4. [LLM集成](#4-llm集成)
5. [向量数据库](#5-向量数据库)
6. [RAG实现](#6-rag实现)
7. [Function Calling](#7-function-calling)
8. [AI Agent](#8-ai-agent)
9. [Prompt管理](#9-prompt管理)
10. [最佳实践](#10-最佳实践)

---

## 1. Spring AI概述

### 1.1 什么是Spring AI

```
Spring AI：
- Spring官方推出的AI应用开发框架
- 与Spring Boot、Spring Cloud深度集成
- 提供统一的AI抽象接口
- 支持多种LLM和向量数据库
- 简化AI应用开发流程
```

### 1.2 核心特性

```
✅ Spring生态集成：
   - Spring Boot自动配置
   - Spring Cloud服务发现
   - Spring Data数据访问
   - Spring Security安全控制

✅ 多LLM支持：
   - OpenAI（GPT-4、GPT-3.5）
   - Anthropic Claude
   - 通义千问、文心一言
   - 本地模型（Ollama）

✅ 向量数据库：
   - Milvus、Pinecone、Weaviate
   - PostgreSQL（pgvector）
   - Redis（RediSearch）
   - 内存向量存储

✅ RAG支持：
   - 文档加载和切分
   - 向量化和检索
   - 上下文管理

✅ Function Calling：
   - 工具调用
   - 多工具协调

✅ Prompt管理：
   - 提示词模板
   - 版本控制
   - A/B测试
```

### 1.3 与其他框架对比

| 框架 | Spring集成 | LLM支持 | RAG | Agent | 推荐度 |
|------|-----------|---------|-----|-------|--------|
| Spring AI | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| LangChain4j | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Agent-Flex | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 2. 核心架构

### 2.1 架构设计

Spring AI采用分层架构：

```
应用层（Controller、Service）
  ↓
Spring AI抽象层
  ↓
├── ChatClient（对话接口）
├── EmbeddingClient（向量化接口）
├── VectorStore（向量存储接口）
├── DocumentReader（文档读取接口）
└── PromptTemplate（提示词模板）
  ↓
具体实现层（OpenAI、Claude、Milvus等）
```

### 2.2 核心组件

```
1. ChatClient：
   - 对话客户端接口
   - 支持流式和非流式响应
   - 统一API调用不同LLM

2. EmbeddingClient：
   - 向量化客户端接口
   - 文本转向量
   - 支持批量向量化

3. VectorStore：
   - 向量存储接口
   - 支持多种向量数据库
   - 统一检索API

4. DocumentReader：
   - 文档读取接口
   - 支持多种格式（PDF、TXT、Markdown等）
   - 自动解析和提取

5. TextSplitter：
   - 文档切分器
   - 支持多种切分策略
   - 语义边界切分

6. PromptTemplate：
   - 提示词模板
   - 变量替换
   - 版本管理
```

---

## 3. 快速开始

### 3.1 Maven依赖

```xml
<dependencies>
    <!-- Spring AI核心 -->
    <dependency>
        <groupId>org.springframework.ai</groupId>
        <artifactId>spring-ai-core</artifactId>
        <version>1.0.0</version>
    </dependency>
    
    <!-- OpenAI集成 -->
    <dependency>
        <groupId>org.springframework.ai</groupId>
        <artifactId>spring-ai-openai-spring-boot-starter</artifactId>
        <version>1.0.0</version>
    </dependency>
    
    <!-- Spring Boot -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

### 3.2 配置文件

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: gpt-4
          temperature: 0.7
          max-tokens: 1000
      embedding:
        options:
          model: text-embedding-3-small
```

### 3.3 基础使用

```java
@RestController
@RequestMapping("/ai")
public class AIController {
    
    @Autowired
    private ChatClient chatClient;
    
    @PostMapping("/chat")
    public String chat(@RequestBody ChatRequest request) {
        return chatClient.call(request.getMessage());
    }
    
    @PostMapping("/chat/stream")
    public Flux<String> chatStream(@RequestBody ChatRequest request) {
        return Flux.create(sink -> {
            chatClient.stream(request.getMessage())
                .subscribe(
                    token -> sink.next(token),
                    error -> sink.error(error),
                    () -> sink.complete()
                );
        });
    }
}
```

---

## 4. LLM集成

### 4.1 OpenAI集成

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: gpt-4
          temperature: 0.7
          max-tokens: 1000
          top-p: 1.0
          frequency-penalty: 0.0
          presence-penalty: 0.0
```

```java
@Service
public class OpenAIService {
    
    @Autowired
    private ChatClient chatClient;
    
    public String chat(String message) {
        return chatClient.call(message);
    }
    
    public Flux<String> streamChat(String message) {
        return chatClient.stream(message);
    }
}
```

### 4.2 Claude集成

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-anthropic-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
spring:
  ai:
    anthropic:
      api-key: ${ANTHROPIC_API_KEY}
      chat:
        options:
          model: claude-3-5-sonnet-20241022
          temperature: 0.7
          max-tokens: 1000
```

### 4.3 通义千问集成

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-alibaba-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
spring:
  ai:
    alibaba:
      dashscope:
        api-key: ${DASHSCOPE_API_KEY}
        chat:
          options:
            model: qwen-plus
            temperature: 0.7
```

### 4.4 本地模型（Ollama）

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-ollama-spring-boot-starter</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
spring:
  ai:
    ollama:
      base-url: http://localhost:11434
      chat:
        options:
          model: llama2
          temperature: 0.7
```

---

## 5. 向量数据库

### 5.1 Milvus集成

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-milvus-store</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
spring:
  ai:
    vectorstore:
      milvus:
        host: localhost
        port: 19530
        collection-name: documents
        dimension: 1536
```

```java
@Configuration
public class MilvusConfig {
    
    @Bean
    public VectorStore vectorStore(MilvusClient milvusClient) {
        return new MilvusVectorStore(milvusClient, "documents", 1536);
    }
}
```

### 5.2 PostgreSQL（pgvector）

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-pgvector-store</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/vectordb
    username: postgres
    password: postgres
  
  ai:
    vectorstore:
      pgvector:
        index-type: HNSW
        dimensions: 1536
```

### 5.3 Redis（RediSearch）

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-redis-store</artifactId>
    <version>1.0.0</version>
</dependency>
```

```yaml
spring:
  ai:
    vectorstore:
      redis:
        index-name: documents
        dimensions: 1536
```

---

## 6. RAG实现

### 6.1 文档加载和切分

```java
@Service
public class DocumentService {
    
    @Autowired
    private ResourceLoader resourceLoader;
    
    @Autowired
    private TextSplitter textSplitter;
    
    public List<Document> loadAndSplit(String filePath) throws IOException {
        // 加载文档
        Resource resource = resourceLoader.getResource("file:" + filePath);
        DocumentReader reader = new TikaDocumentReader(resource);
        Document document = reader.get();
        
        // 切分文档
        return textSplitter.apply(document);
    }
}
```

### 6.2 向量化和存储

```java
@Service
public class RAGService {
    
    @Autowired
    private EmbeddingClient embeddingClient;
    
    @Autowired
    private VectorStore vectorStore;
    
    public void loadDocuments(List<Document> documents) {
        for (Document doc : documents) {
            // 向量化
            List<Double> embedding = embeddingClient.embed(doc.getContent());
            
            // 存储
            vectorStore.add(
                List.of(new org.springframework.ai.document.Document(
                    doc.getContent(),
                    doc.getMetadata()
                ))
            );
        }
    }
}
```

### 6.3 检索和生成

```java
@Service
public class RAGService {
    
    @Autowired
    private EmbeddingClient embeddingClient;
    
    @Autowired
    private VectorStore vectorStore;
    
    @Autowired
    private ChatClient chatClient;
    
    public String query(String question) {
        // 1. 查询向量化
        List<Double> queryEmbedding = embeddingClient.embed(question);
        
        // 2. 检索相关文档
        List<org.springframework.ai.document.Document> documents = 
            vectorStore.similaritySearch(
                SearchRequest.builder()
                    .query(question)
                    .topK(5)
                    .similarityThreshold(0.7)
                    .build()
            );
        
        // 3. 构建上下文
        StringBuilder context = new StringBuilder();
        for (org.springframework.ai.document.Document doc : documents) {
            context.append(doc.getContent()).append("\n\n");
        }
        
        // 4. 构建Prompt
        PromptTemplate template = new PromptTemplate(
            "基于以下上下文回答问题：\n\n{{context}}\n\n问题：{{question}}\n\n答案："
        );
        
        Prompt prompt = template.create(
            Map.of(
                "context", context.toString(),
                "question", question
            )
        );
        
        // 5. 生成答案
        return chatClient.call(prompt.getContents());
    }
}
```

---

## 7. Function Calling

### 7.1 定义工具

```java
@Component
public class WeatherTool {
    
    public String getWeather(String city) {
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
    private ChatClient chatClient;
    
    @Autowired
    private WeatherTool weatherTool;
    
    public String chatWithTools(String userMessage) {
        // 创建工具列表
        List<Function> functions = List.of(
            Function.builder()
                .name("getWeather")
                .description("获取指定城市的天气信息")
                .parameters(Map.of(
                    "type", "object",
                    "properties", Map.of(
                        "city", Map.of(
                            "type", "string",
                            "description", "城市名称"
                        )
                    )
                ))
                .build()
        );
        
        // 调用模型（支持Function Calling）
        ChatResponse response = chatClient.call(
            ChatRequest.builder()
                .messages(List.of(
                    new UserMessage(userMessage)
                ))
                .functions(functions)
                .build()
        );
        
        // 检查是否有工具调用
        if (response.getResult().getOutput().getToolCalls() != null) {
            // 执行工具调用
            for (ToolCall toolCall : response.getResult().getOutput().getToolCalls()) {
                if ("getWeather".equals(toolCall.getName())) {
                    String city = toolCall.getArguments().get("city");
                    String result = weatherTool.getWeather(city);
                    
                    // 再次调用模型生成最终答案
                    response = chatClient.call(
                        ChatRequest.builder()
                            .messages(List.of(
                                new UserMessage(userMessage),
                                new AssistantMessage(result)
                            ))
                            .build()
                    );
                }
            }
        }
        
        return response.getResult().getOutput().getContent();
    }
}
```

---

## 8. AI Agent

### 8.1 基础Agent

```java
@Service
public class AgentService {
    
    @Autowired
    private ChatClient chatClient;
    
    @Autowired
    private List<Function> tools;
    
    public String agentChat(String userMessage) {
        // 创建Agent
        Agent agent = Agent.builder()
            .chatClient(chatClient)
            .tools(tools)
            .systemMessage("你是一个智能助手，可以帮助用户完成各种任务。")
            .build();
        
        // Agent对话
        return agent.chat(userMessage);
    }
}
```

### 8.2 ReAct Agent

```java
@Service
public class ReActAgentService {
    
    public String reactAgent(String userMessage) {
        // ReAct Agent：推理-行动-观察循环
        ReActAgent agent = ReActAgent.builder()
            .chatClient(chatClient)
            .tools(tools)
            .maxIterations(10)
            .build();
        
        return agent.chat(userMessage);
    }
}
```

---

## 9. Prompt管理

### 9.1 Prompt模板

```java
@Service
public class PromptService {
    
    public String generatePrompt(String template, Map<String, Object> variables) {
        PromptTemplate promptTemplate = new PromptTemplate(template);
        Prompt prompt = promptTemplate.create(variables);
        return prompt.getContents();
    }
}
```

### 9.2 提示词版本管理

```java
@Service
public class PromptVersionService {
    
    @Autowired
    private PromptRepository promptRepository;
    
    public String getPrompt(String name, String version) {
        Prompt prompt = promptRepository.findByNameAndVersion(name, version);
        return prompt.getContent();
    }
    
    public void createPrompt(String name, String content) {
        Prompt prompt = new Prompt();
        prompt.setName(name);
        prompt.setContent(content);
        prompt.setVersion("1.0");
        promptRepository.save(prompt);
    }
}
```

### 9.3 A/B测试

```java
@Service
public class PromptABTestService {
    
    public String chatWithABTest(String message) {
        // 随机选择Prompt版本
        Prompt promptA = getPrompt("chat", "1.0");
        Prompt promptB = getPrompt("chat", "2.0");
        
        Prompt selectedPrompt = Math.random() < 0.5 ? promptA : promptB;
        
        // 记录使用的版本
        logABTestResult(selectedPrompt.getVersion());
        
        return chatClient.call(selectedPrompt.getContent() + "\n\n" + message);
    }
}
```

---

## 10. 最佳实践

### 10.1 配置管理

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: ${AI_MODEL:gpt-4}
          temperature: ${AI_TEMPERATURE:0.7}
          max-tokens: ${AI_MAX_TOKENS:1000}
      embedding:
        options:
          model: ${EMBEDDING_MODEL:text-embedding-3-small}
```

### 10.2 成本控制

```java
@Service
public class CostOptimizedService {
    
    @Cacheable(value = "ai-responses", key = "#message")
    public String chat(String message) {
        return chatClient.call(message);
    }
    
    public String smartChat(String message) {
        if (isSimpleQuestion(message)) {
            return cheapModel.call(message);
        } else {
            return expensiveModel.call(message);
        }
    }
}
```

### 10.3 错误处理

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
            return chatClient.call(message);
        } catch (Exception e) {
            log.error("AI调用失败", e);
            throw e;
        }
    }
    
    @Recover
    public String recover(Exception e, String message) {
        return "抱歉，系统暂时无法处理您的请求，请稍后重试。";
    }
}
```

### 10.4 监控和日志

```java
@Aspect
@Component
public class AILoggingAspect {
    
    @Around("execution(* org.springframework.ai..*.*(..))")
    public Object logAICalls(ProceedingJoinPoint joinPoint) throws Throwable {
        long startTime = System.currentTimeMillis();
        try {
            Object result = joinPoint.proceed();
            long duration = System.currentTimeMillis() - startTime;
            log.info("AI调用成功: {}ms", duration);
            return result;
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("AI调用失败: {}ms", duration, e);
            throw e;
        }
    }
}
```

---

## 📚 参考资源

- 🔗 [Spring AI官方文档](https://docs.spring.io/spring-ai/reference/)
- 🔗 [GitHub仓库](https://github.com/spring-projects/spring-ai)
- 🔗 [Spring AI示例](https://github.com/spring-projects/spring-ai-examples)

---

*最后更新：2025-11-04*

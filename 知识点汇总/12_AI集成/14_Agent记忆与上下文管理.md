# Agent记忆与上下文管理

> 短期记忆、长期记忆、向量记忆、总结压缩，构建Agent的记忆系统

---

## 📋 目录

1. [记忆系统概述](#1-记忆系统概述)
2. [短期记忆](#2-短期记忆)
3. [长期记忆](#3-长期记忆)
4. [记忆压缩策略](#4-记忆压缩策略)
5. [Java实现](#5-java实现)
6. [面试要点](#6-面试要点)

---

## 1. 记忆系统概述

### 为什么Agent需要记忆

```
无记忆Agent：每次对话独立，无法理解上下文
有记忆Agent：记住历史对话、用户偏好、任务进度

人类记忆类比：
  短期记忆 → 工作记忆（当前对话上下文）
  长期记忆 → 长期记忆（历史信息、知识库）
  检索记忆 → 回忆（从长期记忆中检索相关信息）
```

### 记忆类型

| 类型 | 存储 | 容量 | 持久性 | 检索方式 |
|------|------|------|--------|---------|
| 短期记忆 | 内存 | 最近N轮 | 会话级 | 顺序读取 |
| 长期记忆 | 向量DB | 无限 | 持久 | 语义检索 |
| 摘要记忆 | 内存/DB | 压缩后 | 会话/持久 | 直接读取 |
| 实体记忆 | 图DB | 无限 | 持久 | 实体查询 |

---

## 2. 短期记忆

### 滑动窗口

```java
@Service
public class SlidingWindowMemory {
    
    private final int maxSize;
    private final LinkedList<ChatMessage> messages = new LinkedList<>();
    
    public SlidingWindowMemory(int maxSize) {
        this.maxSize = maxSize;
    }
    
    public void add(ChatMessage message) {
        messages.addLast(message);
        // 超过窗口大小，移除最旧的消息
        while (messages.size() > maxSize) {
            messages.removeFirst();
        }
    }
    
    public List<ChatMessage> getMessages() {
        return new ArrayList<>(messages);
    }
}
```

### Token感知窗口

```java
@Service
public class TokenAwareMemory {
    
    private final int maxTokens;
    private final LinkedList<ChatMessage> messages = new LinkedList<>();
    private int currentTokens = 0;
    
    public void add(ChatMessage message) {
        int tokens = estimateTokens(message.getContent());
        messages.addLast(message);
        currentTokens += tokens;
        
        // 超过Token限制时移除最旧消息
        while (currentTokens > maxTokens && messages.size() > 2) {
            ChatMessage removed = messages.removeFirst();
            currentTokens -= estimateTokens(removed.getContent());
        }
    }
    
    private int estimateTokens(String text) {
        return text.length() / 4;  // 粗略估算
    }
}
```

---

## 3. 长期记忆

### 向量记忆

```java
@Service
public class VectorLongTermMemory {
    
    @Autowired private VectorStore vectorStore;
    @Autowired private ChatClient chatClient;
    
    // 存储记忆（自动提取关键信息）
    public void remember(String userId, String content, String type) {
        // LLM提取关键信息
        String summary = chatClient.prompt()
            .user("提取以下内容的关键信息（简洁）：\n" + content)
            .call()
            .content();
        
        // 向量化存储
        vectorStore.add(List.of(
            new Document(summary, Map.of(
                "userId", userId,
                "type", type,           // preference / fact / event
                "time", System.currentTimeMillis(),
                "original", content
            ))
        ));
    }
    
    // 检索相关记忆
    public String recall(String userId, String query) {
        List<Document> memories = vectorStore.similaritySearch(
            SearchRequest.builder()
                .query(query)
                .topK(5)
                .similarityThreshold(0.7)
                .build());
        
        // 过滤当前用户的记忆
        List<Document> userMemories = memories.stream()
            .filter(d -> userId.equals(d.getMetadata().get("userId")))
            .toList();
        
        if (userMemories.isEmpty()) return "";
        
        return userMemories.stream()
            .map(d -> "- " + d.getText())
            .collect(Collectors.joining("\n"));
    }
}
```

### 实体记忆

```java
@Service
public class EntityMemory {
    
    // 存储实体关系（用户提到的关键实体）
    private final Map<String, Map<String, String>> entityStore = new ConcurrentHashMap<>();
    
    public void rememberEntity(String userId, String entity, String attribute, String value) {
        entityStore.computeIfAbsent(userId + ":" + entity, k -> new HashMap<>())
            .put(attribute, value);
    }
    
    public String getEntity(String userId, String entity, String attribute) {
        return entityStore.getOrDefault(userId + ":" + entity, Map.of())
            .get(attribute);
    }
    
    // LLM自动提取实体
    public void extractAndStore(String userId, String conversation) {
        String prompt = """
            从以下对话中提取关键实体信息，输出JSON：
            对话：%s
            
            格式：[{"entity": "张三", "attributes": {"职业": "工程师", "喜好": "Java"}}]
            """.formatted(conversation);
        
        String response = chatClient.prompt().user(prompt).call().content();
        List<EntityExtraction> entities = parseEntities(response);
        
        for (EntityExtraction e : entities) {
            for (var attr : e.getAttributes().entrySet()) {
                rememberEntity(userId, e.getEntity(), attr.getKey(), attr.getValue());
            }
        }
    }
}
```

---

## 4. 记忆压缩策略

### 对话摘要压缩

```java
@Service
public class MemoryCompressor {
    
    @Autowired private ChatClient chatClient;
    
    // 当短期记忆超过限制时，压缩为摘要
    public String compress(List<ChatMessage> messages) {
        String dialog = messages.stream()
            .map(m -> m.getRole() + ": " + m.getContent())
            .collect(Collectors.joining("\n"));
        
        String prompt = """
            请总结以下对话的关键信息，保留：
            1. 用户的核心需求
            2. 已达成的共识
            3. 待解决的问题
            4. 关键技术决策
            
            对话：
            %s
            
            总结（200字以内）：
            """.formatted(dialog);
        
        return chatClient.prompt().user(prompt).call().content();
    }
}
```

### 分层记忆管理

```java
@Service
public class HierarchicalMemory {
    
    private final Queue<ChatMessage> recentMessages = new LinkedList<>();  // 最近5轮
    private String sessionSummary = "";  // 会话摘要
    @Autowired private VectorLongTermMemory longTermMemory;
    
    private static final int RECENT_LIMIT = 10;  // 最近10条消息
    
    public void add(String userId, ChatMessage message) {
        recentMessages.add(message);
        
        // 超过限制时压缩
        if (recentMessages.size() > RECENT_LIMIT) {
            // 将旧消息压缩为摘要
            List<ChatMessage> toCompress = new ArrayList<>();
            while (recentMessages.size() > RECENT_LIMIT / 2) {
                toCompress.add(recentMessages.poll());
            }
            
            String newSummary = compressor.compress(toCompress);
            sessionSummary = sessionSummary.isEmpty() 
                ? newSummary 
                : sessionSummary + "\n" + newSummary;
            
            // 重要信息存入长期记忆
            longTermMemory.remember(userId, 
                formatMessages(toCompress), "conversation");
        }
    }
    
    // 组装上下文：摘要 + 最近对话 + 检索的长期记忆
    public String buildContext(String userId, String query) {
        StringBuilder ctx = new StringBuilder();
        
        // 1. 会话摘要
        if (!sessionSummary.isEmpty()) {
            ctx.append("## 会话摘要\n").append(sessionSummary).append("\n\n");
        }
        
        // 2. 检索长期记忆
        String recalled = longTermMemory.recall(userId, query);
        if (!recalled.isEmpty()) {
            ctx.append("## 相关历史信息\n").append(recalled).append("\n\n");
        }
        
        // 3. 最近对话
        ctx.append("## 最近对话\n");
        for (ChatMessage msg : recentMessages) {
            ctx.append(msg.getRole()).append(": ").append(msg.getContent()).append("\n");
        }
        
        return ctx.toString();
    }
}
```

---

## 5. LangChain4j记忆实现

```java
// LangChain4j内置记忆
@AiService
public interface ChatAgent {
    
    String chat(@MemoryId String userId, @UserMessage String message);
}

// 配置
@Bean
public ChatMemory chatMemory() {
    return MessageWindowChatMemory.builder()
        .maxMessages(20)  // 短期记忆窗口
        .build();
}

@Bean
public ChatMemoryStore chatMemoryStore() {
    // 自定义持久化（Redis/DB）
    return new RedisChatMemoryStore(redisTemplate);
}

// 记忆提供者
@Bean
public ChatMemoryProvider chatMemoryProvider(ChatMemoryStore store) {
    return memoryId -> MessageWindowChatMemory.builder()
        .id(memoryId)
        .maxMessages(20)
        .chatMemoryStore(store)
        .build();
}
```

---

## 6. 面试要点

### Q1: Agent的记忆系统怎么设计？

```
三层记忆架构：
  1. 短期记忆：最近N轮对话（内存，滑动窗口）
  2. 会话摘要：旧对话压缩为摘要（节省Token）
  3. 长期记忆：向量化存储历史信息（向量DB，语义检索）

上下文组装：摘要 + 检索的长期记忆 + 最近对话
```

### Q2: 记忆压缩什么时候做？

```
触发条件：
  1. Token数超过限制（如4000 Token）
  2. 消息数超过窗口（如20条）
  3. 对话阶段切换（如从需求讨论转到方案设计）

压缩策略：
  1. LLM摘要：将旧对话总结为关键信息
  2. 实体提取：提取关键实体和属性
  3. 分层压缩：保留最近5轮原文 + 更早的摘要
```

### Q3: 长期记忆用向量DB还是图DB？

```
向量DB（推荐）：
  - 语义检索（"用户之前问过什么关于Java的问题"）
  - 实现简单（Spring AI + pgvector）
  - 适合大多数场景

图DB（高级）：
  - 实体关系查询（"用户的同事是谁"）
  - 复杂关联推理
  - 实现复杂（Neo4j）

推荐：先用向量DB，需要复杂关系再引入图DB
```

---

## 📚 相关阅读

- [12_Agent设计模式](./12_Agent设计模式.md)
- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [08_RAG架构深度实战](./08_RAG架构深度实战.md)
- [11_Prompt工程进阶](./11_Prompt工程进阶.md)

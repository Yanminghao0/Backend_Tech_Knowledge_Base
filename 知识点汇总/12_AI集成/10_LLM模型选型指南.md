# LLM模型选型指南

> GPT vs Claude vs Qwen vs DeepSeek，大模型选型决策矩阵

---

## 📋 目录

1. [主流大模型概览](#1-主流大模型概览)
2. [能力对比](#2-能力对比)
3. [成本分析](#3-成本分析)
4. [选型决策矩阵](#4-选型决策矩阵)
5. [Java集成示例](#5-java集成示例)
6. [面试要点](#6-面试要点)

---

## 1. 主流大模型概览

| 模型 | 厂商 | 上下文窗口 | 特点 | 开源 |
|------|------|-----------|------|------|
| GPT-5 | OpenAI | 1M(推测) | 多模态推理最强 | ❌ |
| Claude 4 | Anthropic | 200K token | 代码生成/长文分析 | ❌ |
| Qwen2.5 | 阿里 | 128K token | 中文优化/开源 | ✅(72B) |
| DeepSeek-V3 | 深度求索 | 128K token | MoE架构/低成本 | ✅ |
| Llama 3.1 | Meta | 128K token | 开源生态最大 | ✅(405B) |
| GLM-4 | 智谱 | 128K token | 国产/Function Calling | ✅ |

---

## 2. 能力对比

### 综合能力评分

| 维度 | GPT-5 | Claude 4 | Qwen3 | DeepSeek-V3 | Llama 4 |
|------|-------|----------|-------|-------------|---------|
| 推理能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 代码生成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 中文能力 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 多模态 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| Function Calling | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 长上下文 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 场景推荐

```
代码开发助手 → Claude 4 / GPT-5
中文知识库问答 → Qwen3 / DeepSeek-V3
多模态应用 → GPT-5
低成本批量处理 → DeepSeek-V3（推理成本最低）
本地部署 → Qwen2.5-72B / Llama 3.1-70B
Function Calling → GPT-5 / Claude 4
```

---

## 3. 成本分析

### API价格对比（2026年）

| 模型 | 输入($/1M token) | 输出($/1M token) | 相对成本 |
|------|-----------------|-----------------|---------|
| GPT-4 Turbo | $10 | $30 | 1.0x |
| GPT-4 | $5 | $15 | 0.5x |
| Claude 3.5 Sonnet | $3 | $15 | 0.3x |
| Qwen-Plus | $0.5 | $1.5 | 0.05x |
| DeepSeek-V3 | $0.14 | $0.28 | 0.01x |

### 成本优化策略

```java
// 模型路由：简单问题用便宜模型，复杂问题用强模型
@Service
public class ModelRouter {
    
    public String selectModel(String prompt, int estimatedTokens) {
        // 1. 简单问答 → 便宜模型
        if (estimatedTokens < 500 && !isComplex(prompt)) {
            return "deepseek-v3";  // 成本最低
        }
        
        // 2. 代码相关 → Claude
        if (containsCode(prompt)) {
            return "claude-4-sonnet";
        }
        
        // 3. 中文知识库 → Qwen
        if (isChinese(prompt) && isKnowledgeQuery(prompt)) {
            return "qwen3-plus";
        }
        
        // 4. 复杂推理 → GPT-5
        return "gpt-5";
    }
}

// 语义缓存：相同语义的问题直接返回缓存
@Service
public class SemanticCache {
    
    @Autowired
    private VectorStore vectorStore;
    
    public Optional<String> getCachedResponse(String query) {
        // 向量检索相似问题
        List<Document> similar = vectorStore.similaritySearch(
            SearchRequest.builder().query(query).topK(1)
                .similarityThreshold(0.95).build());
        
        if (!similar.isEmpty()) {
            return Optional.of(similar.get(0).getText());
        }
        return Optional.empty();
    }
    
    public void cacheResponse(String query, String response) {
        vectorStore.add(List.of(new Document(response, 
            Map.of("query", query, "time", System.currentTimeMillis()))));
    }
}
```

---

## 4. 选型决策矩阵

| 场景 | 首选 | 备选 | 选择理由 |
|------|------|------|---------|
| 代码助手 | Claude 4 | GPT-5 | 代码准确率最高 |
| 中文客服 | Qwen3 | DeepSeek | 中文理解最优 |
| RAG知识库 | GPT-5 | Claude 4 | 上下文理解最强 |
| 批量数据处理 | DeepSeek-V3 | Qwen3 | 成本最低 |
| 多模态应用 | GPT-5 | Qwen3 | 图片/视频理解 |
| 本地私有部署 | Qwen2.5-72B | Llama 4 | 开源+中文优化 |
| Function Calling | GPT-5 | Claude 4 | 工具调用最稳定 |
| 长文档分析 | Claude 4 | GPT-5 | 200K上下文 |

---

## 5. Java集成示例

### 多模型统一接口

```java
// 统一LLM接口
public interface LlmService {
    String chat(String model, List<ChatMessage> messages);
    Flux<String> streamChat(String model, List<ChatMessage> messages);
}

// OpenAI实现
@Component("openai")
public class OpenAiLlmService implements LlmService {
    @Override
    public String chat(String model, List<ChatMessage> messages) {
        ChatClient client = ChatClient.builder(openAiApi)
            .defaultOptions(OpenAiChatOptions.builder().model(model).build())
            .build();
        return client.prompt().messages(messages).call().content();
    }
}

// 通义千问实现（兼容OpenAI接口）
@Component("qwen")
public class QwenLlmService implements LlmService {
    @Override
    public String chat(String model, List<ChatMessage> messages) {
        // 阿里云DashScope兼容OpenAI接口格式
        return openAiCompatibleClient.chat(model, messages);
    }
}

// DeepSeek实现
@Component("deepseek")
public class DeepSeekLlmService implements LlmService {
    @Override
    public String chat(String model, List<ChatMessage> messages) {
        return openAiCompatibleClient.chat("deepseek-chat", messages);
    }
}

// 模型路由 + 缓存
@Service
public class AiService {
    
    @Autowired private Map<String, LlmService> llmServices;
    @Autowired private ModelRouter router;
    @Autowired private SemanticCache cache;
    
    public String ask(String prompt) {
        // 1. 语义缓存
        Optional<String> cached = cache.getCachedResponse(prompt);
        if (cached.isPresent()) return cached.get();
        
        // 2. 路由选择模型
        String model = router.selectModel(prompt, estimateTokens(prompt));
        String provider = getProvider(model);
        
        // 3. 调用LLM
        String response = llmServices.get(provider)
            .chat(model, List.of(new UserMessage(prompt)));
        
        // 4. 缓存结果
        cache.cacheResponse(prompt, response);
        
        return response;
    }
}
```

---

## 6. 面试要点

### Q1: 如何选择LLM？

```
选型维度：
1. 能力：推理/代码/中文/多模态
2. 成本：输入输出token价格
3. 延迟：首token延迟/吞吐量
4. 上下文窗口：长文档需要大窗口
5. 开源：是否需要本地部署
6. Function Calling：工具调用稳定性

策略：模型路由 + 语义缓存
  - 简单问题用便宜模型
  - 复杂问题用强模型
  - 相似问题返回缓存
```

### Q2: 如何降低LLM调用成本？

```
1. 模型路由：简单→DeepSeek，复杂→GPT-5
2. 语义缓存：相似问题直接返回缓存（节省90%+）
3. Prompt压缩：精简上下文，减少token
4. 批量处理：Batch API享受50%折扣
5. 流式响应：减少超时等待
6. 降级策略：LLM不可用时返回模板回复
```

### Q3: 开源模型和闭源模型的区别？

```
闭源(GPT/Claude)：能力最强，但数据出境/成本高/依赖厂商
开源(Qwen/Llama)：可本地部署，数据安全，但需要GPU资源

选择：
  - 对外服务 → 闭源API（能力强，免运维）
  - 数据敏感 → 开源本地部署（安全合规）
  - 成本敏感 → 开源（无API费用，但有GPU成本）
```

---

## 📚 相关阅读

- [03_Java AI开发实战](./03_Java AI开发实战.md)
- [08_RAG架构深度实战](./08_RAG架构深度实战.md)
- [11_Prompt工程进阶](./11_Prompt工程进阶.md)
- [MCP协议核心原理与实战](../15_MCP协议/03_MCP协议核心原理与实战.md)

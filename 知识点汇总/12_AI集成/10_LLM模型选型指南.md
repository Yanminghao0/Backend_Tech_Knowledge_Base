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
7. [开源vs闭源详细对比](#7-开源vs闭源详细对比)
8. [本地部署模型选型](#8-本地部署模型选型)
9. [模型路由实现代码](#9-模型路由实现代码)
10. [Token计算与上下文管理](#10-token计算与上下文管理)
11. [面试要点补充](#11-面试要点补充)

---

## 1. 主流大模型概览

| 模型 | 厂商 | 上下文窗口 | 特点 | 开源 |
|------|------|-----------|------|------|
| GPT-5 | OpenAI | 100万token | 多模态推理最强 | ❌ |
| Claude 4 | Anthropic | 200K token | 代码生成/长文分析 | ❌ |
| Qwen3 | 阿里 | 128K token | 中文优化/开源 | ✅(72B) |
| DeepSeek V4 | 深度求索 | 128K token | MoE架构/低成本 | ✅ |
| Llama 4 | Meta | 128K token | 开源生态最大 | ✅(405B) |
| GLM-5 | 智谱 | 128K token | 国产/Function Calling | ✅ |

---

## 2. 能力对比

### 综合能力评分

| 维度 | GPT-5 | Claude 4 | Qwen3 | DeepSeek V4 | Llama 4 |
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
中文知识库问答 → Qwen3 / DeepSeek V4
多模态应用 → GPT-5
低成本批量处理 → DeepSeek V4（推理成本最低）
本地部署 → Qwen3-72B / Llama 4-70B
Function Calling → GPT-5 / Claude 4
```

---

## 3. 成本分析

### API价格对比（2026年）

| 模型 | 输入($/1M token) | 输出($/1M token) | 相对成本 |
|------|-----------------|-----------------|---------|
| GPT-5 | $5 | $15 | 1.0x |
| GPT-5 Turbo | $2 | $6 | 0.4x |
| Claude 4 Sonnet | $3 | $15 | 0.8x |
| Qwen3-Plus | $0.5 | $1.5 | 0.1x |
| DeepSeek V4 | $0.3 | $0.6 | 0.05x |

### 成本优化策略

```java
// 模型路由：简单问题用便宜模型，复杂问题用强模型
@Service
public class ModelRouter {
    
    public String selectModel(String prompt, int estimatedTokens) {
        // 1. 简单问答 → 便宜模型
        if (estimatedTokens < 500 && !isComplex(prompt)) {
            return "deepseek-v4";  // 成本最低
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
| 批量数据处理 | DeepSeek V4 | Qwen3 | 成本最低 |
| 多模态应用 | GPT-5 | Qwen3 | 图片/视频理解 |
| 本地私有部署 | Qwen3-72B | Llama 4 | 开源+中文优化 |
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

## 7. 开源vs闭源详细对比

### 核心维度对比

| 维度 | 闭源模型 (GPT/Claude/GLM) | 开源模型 (Qwen/Llama/DeepSeek) |
|------|--------------------------|-------------------------------|
| 模型能力 | 推理/多模态领先，迭代快 | 头部开源已接近GPT-4水平，差距缩小 |
| 数据安全 | 数据出境，需脱敏/合规审查 | 可本地部署，数据不出内网 |
| 成本结构 | 按token计费，量大成本高 | 一次性GPU投入，边际成本趋近于0 |
| 运维门槛 | 零运维，API即用 | 需GPU集群、推理框架、监控 |
| 定制能力 | 仅Prompt/微调API，无法改权重 | 支持全参微调/LoRA/量化蒸馏 |
| 可用性 | 依赖厂商SLA，存在限流/宕机 | 自主可控，但需自建高可用 |
| 合规审计 | 难以满足金融/政务数据合规 | 满足等保/信创/数据本地化要求 |
| 生态工具 | 厂商生态绑定（Assistants API） | HuggingFace/vLLM生态开放 |

### 决策流程图

```
是否涉及敏感数据？ ──是──→ 是否有GPU预算？ ──是──→ 开源本地部署
        │否                         │否
        ↓                           ↓
  调用量是否大？ ──是──→ 开源自托管/私有化API    闭源API（快速启动）
        │否
        ↓
   闭源API（能力优先）
```

### 混合架构推荐

```
对外客服/通用问答   → 闭源API（GPT-5/Qwen-Plus）能力强、免运维
内部知识库/代码助手 → 开源本地（Qwen3-72B）数据安全、可微调
批量数据处理       → 开源API（DeepSeek V4）成本最低
高敏感场景        → 开源本地 + 私有化向量库，全链路数据不出域
```

---

## 8. 本地部署模型选型

### 硬件需求参考

| 模型规模 | 显存需求(FP16) | 显存需求(INT4量化) | 推荐显卡 |
|---------|---------------|-------------------|---------|
| 7B-8B | 16GB | 6-8GB | RTX 4090 / A10 |
| 14B-32B | 60GB | 12-20GB | A100 40G / 双4090 |
| 70B-72B | 140GB | 40-48GB | A100 80G ×2 / H100 |
| 405B | 800GB+ | 200GB+ | H100集群 ×8 |

### 推理框架对比

| 框架 | 特点 | 适用场景 |
|------|------|---------|
| vLLM | PagedAttention，高吞吐 | 生产环境高并发服务 |
| Ollama | 一键部署，简单易用 | 开发测试/个人使用 |
| TGI (HuggingFace) | 支持流式/量化，生态好 | 中小规模服务 |
| TensorRT-LLM | NVIDIA官方，极致性能 | 追求最低延迟 |
| LMDeploy | 国产，支持国产GPU | 昇腾/海光等信创场景 |

### 本地部署选型建议

```bash
# 开发环境：Ollama 一键拉起
ollama pull qwen3:32b
ollama run qwen3:32b

# 生产环境：vLLM 提供OpenAI兼容API
python -m vllm.entrypoints.openai.api_server \
    --model qwen/Qwen3-72B-Instruct \
    --tensor-parallel-size 2 \
    --quantization awq \
    --max-model-len 32768 \
    --port 8000
```

```
选型决策：
  GPU充足 + 追求性能    → vLLM + AWQ量化
  快速验证/原型         → Ollama
  信创/国产芯片         → LMDeploy
  极致延迟             → TensorRT-LLM
```

---

## 9. 模型路由实现代码

### 基于规则的智能路由

```java
@Service
public class SmartModelRouter {

    @Autowired private VectorStore vectorStore;

    // 路由策略：综合判断复杂度、领域、语言、token量
    public RouteResult route(String prompt, List<ChatMessage> history) {
        int tokens = estimateTokens(prompt, history);
        String domain = detectDomain(prompt);
        Complexity complexity = assessComplexity(prompt, history);

        // 1. 命中语义缓存，直接返回（不调用任何模型）
        Optional<String> cached = checkSemanticCache(prompt);
        if (cached.isPresent()) {
            return RouteResult.cached(cached.get());
        }

        // 2. 简单闲聊/翻译 → 最低成本
        if (complexity == Complexity.SIMPLE && tokens < 500) {
            return RouteResult.of("deepseek-v4", "deepseek");
        }

        // 3. 代码生成 → Claude
        if (domain.equals("code")) {
            return RouteResult.of("claude-4-sonnet", "anthropic");
        }

        // 4. 中文知识问答 → Qwen
        if (isChinese(prompt) && domain.equals("knowledge")) {
            return RouteResult.of("qwen3-plus", "qwen");
        }

        // 5. 多模态（含图片）→ GPT-5
        if (hasImageInput(history)) {
            return RouteResult.of("gpt-5", "openai");
        }

        // 6. 超长上下文 → Claude 4 (200K)
        if (tokens > 120_000) {
            return RouteResult.of("claude-4-opus", "anthropic");
        }

        // 7. 默认复杂推理 → GPT-5
        return RouteResult.of("gpt-5", "openai");
    }

    // 复杂度评估：关键词 + 历史轮数 + 推理链特征
    private Complexity assessComplexity(String prompt, List<ChatMessage> history) {
        if (history.size() > 10) return Complexity.COMPLEX;          // 多轮深聊
        if (prompt.contains("分析") || prompt.contains("推导")) return Complexity.COMPLEX;
        if (prompt.length() > 2000) return Complexity.COMPLEX;        // 长输入
        return Complexity.SIMPLE;
    }

    // 降级策略：主模型失败时自动切换
    public String callWithFallback(RouteResult route, List<ChatMessage> msgs) {
        List<String> fallbackChain = List.of(
            route.getProvider() + ":" + route.getModel(),
            "openai:gpt-5-turbo",      // 降级到更快版本
            "deepseek:deepseek-v4"      // 最终兜底，成本最低
        );
        for (String target : fallbackChain) {
            try {
                return invoke(target, msgs);
            } catch (Exception e) {
                log.warn("模型调用失败，降级: {}", target, e);
            }
        }
        throw new LlmUnavailableException("所有模型均不可用");
    }
}
```

### 路由效果监控

```java
// 记录每次路由决策，用于效果分析
@Aspect
@Component
public class RouterMetricAspect {
    @Autowired private MeterRegistry registry;

    @AfterReturning(value = "execution(* SmartModelRouter.route(..))",
                    returning = "result")
    public void recordRoute(JoinPoint jp, RouteResult result) {
        registry.counter("llm.route.count",
            "model", result.getModel(),
            "reason", result.getReason()
        ).increment();
    }
}
```

---

## 10. Token计算与上下文管理

### Token估算

```java
@Component
public class TokenEstimator {

    // 粗略估算：中文约1字=1.5token，英文约4字符=1token
    public int estimate(String text) {
        int cjk = countCjk(text);
        int other = text.length() - cjk;
        return (int)(cjk * 1.5 + other / 4.0) + 10; // +10为格式开销
    }

    private int countCjk(String text) {
        int n = 0;
        for (char c : text.toCharArray()) {
            if (c >= 0x4E00 && c <= 0x9FFF) n++;
        }
        return n;
    }

    // 精确计算：使用tiktoken（需引入jtokkit库）
    public int exactTokens(String text, String model) {
        Encoding enc = Encodings.newDefaultEncodingRegistry()
            .getEncodingForModel(ModelRevision.GPT_5).getEncoding();
        return enc.countTokens(text);
    }
}
```

### 上下文窗口管理策略

```java
@Service
public class ContextManager {

    private static final int MAX_TOKENS = 120_000;  // 预留缓冲，不用满128K
    private static final int RESERVED_FOR_REPLY = 4_000;

    public List<ChatMessage> trim(List<ChatMessage> history, String newQuery) {
        int used = tokenEstimator.estimate(newQuery);
        int budget = MAX_TOKENS - RESERVED_FOR_REPLY - used;

        // 策略1：保留系统提示 + 最近N轮
        List<ChatMessage> result = new ArrayList<>();
        if (!history.isEmpty() && history.get(0) instanceof SystemMessage) {
            result.add(history.get(0));       // 系统提示永远保留
            budget -= tokenEstimator.estimate(history.get(0).getText());
        }

        // 策略2：从最近的对话向前回溯，直到预算耗尽
        for (int i = history.size() - 1; i >= 1; i--) {
            int t = tokenEstimator.estimate(history.get(i).getText());
            if (budget - t < 0) break;
            result.add(1, history.get(i));    // 插在system之后
            budget -= t;
        }
        return result;
    }

    // 超长文档处理：Map-Reduce摘要压缩
    public String compressLongDoc(String doc, int targetTokens) {
        if (tokenEstimator.estimate(doc) <= targetTokens) return doc;
        List<String> chunks = splitByTokens(doc, 4000);
        List<String> summaries = chunks.stream()
            .map(c -> llm.chat("deepseek-v4", summarizePrompt(c)))  // 用便宜模型做摘要
            .toList();
        return String.join("\n", summaries);
    }
}
```

### 上下文管理要点

```
1. 永远预留输出token空间（输出常被截断导致JSON解析失败）
2. 系统提示放最前且固定，便于KV Cache复用，降低推理成本
3. 超长文档优先做Map-Reduce摘要，而非直接塞满上下文
4. 多轮对话采用滑动窗口+摘要：近3轮原文 + 更早的摘要
5. 注意不同模型token计算器不同，跨模型迁移需重新估算
```

---

## 11. 面试要点补充

### Q4: 本地部署大模型需要考虑哪些因素？

```
1. 硬件：显存决定可部署模型规模，量化(INT4/AWQ)可降4-8倍
2. 框架：vLLM(高并发) / Ollama(易用) / TensorRT-LLM(低延迟)
3. 量化：精度损失vs显存节省的权衡，AWQ优于GPTQ
4. 并发：PagedAttention提升吞吐，连续批处理降低延迟
5. 监控：GPU利用率、首token延迟、排队长度、OOM风险
6. 高可用：多副本负载均衡，模型热更新，故障自动转移
```

### Q5: 如何设计一个模型路由系统？

```
核心目标：在效果与成本间取得最优平衡

路由信号：
  - 输入特征：token数、语言、领域、是否含图片
  - 复杂度评估：关键词、历史轮数、prompt长度
  - 历史反馈：该类问题的历史满意度/重试率

路由策略：
  - 规则路由：简单可解释，适合初期
  - 学习路由：训练小模型预测最优模型，适合规模化
  - 级联路由：先用便宜模型，置信度低再升级强模型

必备能力：
  - 语义缓存（命中即返回，零成本）
  - 降级链（主模型失败自动切换）
  - 效果监控（按模型统计成本/延迟/满意度）
```

### Q6: Token超限怎么处理？长文档如何分析？

```
预防：TokenEstimator预估算，ContextManager滑动窗口裁剪
处理：
  1. 滑动窗口：保留system + 最近N轮，丢弃最早对话
  2. 摘要压缩：用便宜模型对历史/长文做Map-Reduce摘要
  3. RAG检索：长文档不入上下文，改用向量检索相关片段
  4. 分块处理：超长任务拆分为子任务分别处理再合并
关键：始终为输出预留token空间，避免响应被截断
```

### Q7: 模型量化对效果影响多大？何时该用？

```
常见量化：FP16 → INT8 → INT4，显存依次减半
效果损失：INT8几乎无损；INT4约损失2-5%基准分数
适用场景：
  - 显存不足时被迫量化（如单卡跑72B）
  - 边缘部署/成本敏感，可接受轻微精度下降
  - 推理吞吐优先于极致精度的场景
不适用：数学推理、代码生成等精度敏感任务建议FP16/INT8
推荐：AWQ量化，相比GPTQ在推理速度和精度上更均衡
```

### Q8: 如何评估一个LLM是否适合你的业务？

```
1. 离线评测：构建业务测试集(100-500条)，跑准确率/满意度
2. 在线A/B：新旧模型灰度对比，关注用户反馈和重试率
3. 成本核算：单次调用成本 × 日调用量，对比预算
4. 延迟测试：P50/P99首token延迟，是否满足交互要求
5. 边界测试：对抗样本/越狱/幻觉率，评估安全风险
6. 长期监控：模型版本升级后回归测试，防止能力退化
避免仅看榜单分数，业务真实表现才是唯一标准
```

---

## 📚 相关阅读

- [03_Java AI开发实战](./03_Java AI开发实战.md)
- [08_RAG架构深度实战](./08_RAG架构深度实战.md)
- [11_Prompt工程进阶](./11_Prompt工程进阶.md)
- [MCP协议核心原理与实战](../15_MCP协议/03_MCP协议核心原理与实战.md)

### 延伸阅读

- vLLM 官方文档：https://docs.vllm.ai （高吞吐推理引擎）
- HuggingFace TGI：https://huggingface.co/docs/text-generation-inference
- OpenAI Pricing：https://openai.com/pricing （API成本对比）
- LMSYS Chatbot Arena：https://chat.lmsys.org （模型能力排行榜）
- Qwen 技术报告：https://qwenlm.github.io （开源模型细节）
- jtoktoken 库：https://github.com/jtokkit/jtokkit （Java Token计算）

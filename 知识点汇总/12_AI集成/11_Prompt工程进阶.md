# Prompt工程进阶

> 从基础提示到CoT、Few-shot、Self-consistency，系统化Prompt优化方法论

---

## 📋 目录

1. [Prompt工程概述](#1-prompt工程概述)
2. [基础技巧](#2-基础技巧)
3. [Chain of Thought](#3-chain-of-thought)
4. [Few-shot Learning](#4-few-shot-learning)
5. [Self-Consistency](#5-self-consistency)
6. [结构化输出](#6-结构化输出)
7. [Java实现](#7-java实现)
8. [面试要点](#8-面试要点)

---

## 1. Prompt工程概述

```
Prompt工程 = 通过设计提示词来引导LLM输出期望结果的技术

核心原则：
  1. 明确角色：给LLM一个角色定位
  2. 明确任务：具体说明要做什么
  3. 明确格式：指定输出格式
  4. 提供示例：用例子说明期望
  5. 逐步推理：引导分步思考
```

---

## 2. 基础技巧

### 角色设定

```java
// ❌ 模糊Prompt
String prompt = "分析这段代码";

// ✅ 角色设定 + 明确任务 + 输出格式
String prompt = """
    你是一个资深Java架构师，拥有15年经验。
    请分析以下代码的：
    1. 设计模式使用
    2. 潜在的性能问题
    3. 改进建议
    
    输出格式：JSON，包含 pattern, issues, suggestions 三个字段
    
    代码：
    %s
    """.formatted(code);
```

### Prompt结构化

```
推荐Prompt结构：
  [角色] + [任务] + [上下文] + [约束] + [输出格式] + [示例]
```

---

## 3. Chain of Thought

### 原理

```
CoT：让LLM逐步推理，而非直接给出答案

普通Prompt：
  Q: 一个商店有15个苹果，卖了8个，又进了12个，现在有多少？
  A: 19

CoT Prompt：
  Q: 一个商店有15个苹果，卖了8个，又进了12个，现在有多少？
  让我们一步步思考：
  A: 起始有15个苹果，卖了8个后剩15-8=7个，又进了12个所以7+12=19个。答案是19。
```

### Java实现

```java
// Zero-shot CoT
String cotPrompt = """
    问题：%s
    
    让我们一步步思考：
    """.formatted(question);

// Few-shot CoT（带示例）
String fewShotCot = """
    示例1：
    Q: 小明有10元，买了3个本子每个2元，还剩多少钱？
    思考：3个本子花费3×2=6元，剩余10-6=4元。
    A: 4元
    
    示例2：
    Q: 一列火车3小时行驶了360公里，求速度。
    思考：速度=距离÷时间=360÷3=120公里/小时。
    A: 120公里/小时
    
    现在请回答：
    Q: %s
    思考：
    """.formatted(question);
```

### CoT适用场景

```
✅ 适合：数学计算、逻辑推理、多步骤决策、代码分析
❌ 不适合：简单事实查询、翻译、分类
```

---

## 4. Few-shot Learning

### 原理

```
Few-shot：在Prompt中提供几个示例，让LLM学习输出模式

Zero-shot: "判断情感：今天天气真好" → LLM可能输出格式不一致
Few-shot: 
  "今天天气真好 → 积极
   今天下雨了 → 消极
   这个产品一般 → 中性
   今天心情不错 →"
  → LLM输出 "积极"（格式一致）
```

### Java实现

```java
// 情感分类Few-shot
String sentimentPrompt = """
    判断文本的情感倾向，只输出"积极"、"消极"或"中性"。
    
    示例：
    文本：这个产品质量很好，推荐购买
    情感：积极
    
    文本：物流太慢了，等了一周
    情感：消极
    
    文本：产品收到了，还在试用
    情感：中性
    
    现在判断：
    文本：%s
    情感：
    """.formatted(inputText);
```

### 示例选择策略

```java
// 动态选择示例（基于相似度）
@Service
public class DynamicFewShot {
    
    @Autowired
    private VectorStore vectorStore;
    
    public String buildPrompt(String query) {
        // 1. 从向量库检索最相似的3个示例
        List<Document> examples = vectorStore.similaritySearch(
            SearchRequest.builder().query(query).topK(3).build());
        
        // 2. 组装Few-shot Prompt
        StringBuilder prompt = new StringBuilder("根据示例输出：\n\n");
        for (Document doc : examples) {
            prompt.append(doc.getMetadata().get("input"))
                  .append(" → ")
                  .append(doc.getText())
                  .append("\n\n");
        }
        prompt.append(query).append(" → ");
        
        return prompt.toString();
    }
}
```

---

## 5. Self-Consistency

### 原理

```
Self-Consistency：多次生成 + 投票选最优

1. 用CoT生成N个不同的推理路径
2. 从N个答案中选出现频率最高的
3. 比单次推理准确率提升5-15%
```

### Java实现

```java
@Service
public class SelfConsistencyService {
    
    @Autowired
    private ChatClient chatClient;
    
    public String solveWithConsistency(String problem, int attempts) {
        // 1. 生成多个答案（设置temperature=0.7增加多样性）
        List<String> answers = IntStream.range(0, attempts)
            .parallel()
            .mapToObj(i -> chatClient.prompt()
                .user(buildCotPrompt(problem))
                .options(OpenAiChatOptions.builder()
                    .temperature(0.7)  // 增加多样性
                    .build())
                .call()
                .content())
            .toList();
        
        // 2. 提取最终答案并投票
        Map<String, Long> voteCount = answers.stream()
            .map(this::extractAnswer)
            .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));
        
        // 3. 选票数最多的
        return voteCount.entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey)
            .orElse(answers.get(0));
    }
}
```

---

## 6. 结构化输出

### JSON输出

```java
// 方式1：Prompt约束
String prompt = """
    分析以下用户评价，输出JSON格式：
    {
      "sentiment": "积极|消极|中性",
      "keywords": ["关键词1", "关键词2"],
      "score": 1-10,
      "summary": "一句话总结"
    }
    
    评价：%s
    只输出JSON，不要其他内容。
    """.formatted(review);

// 方式2：Spring AI结构化输出（推荐）
@Bean
public ChatClient chatClient(ChatClient.Builder builder) {
    return builder.build();
}

// 直接映射到Java对象
public record SentimentAnalysis(
    String sentiment,
    List<String> keywords,
    int score,
    String summary
) {}

// 调用
SentimentAnalysis result = chatClient.prompt()
    .user("分析评价: " + review)
    .call()
    .entity(SentimentAnalysis.class);  // 自动解析为对象
```

### LangChain4j结构化输出

```java
// LangChain4j @AiService自动结构化
@AiService
public interface SentimentAnalyzer {
    
    @SystemMessage("你是一个情感分析专家，分析用户评价的情感倾向")
    @UserMessage("分析以下评价：{{review}}")
    SentimentAnalysis analyze(@V("review") String review);
}

// 使用
SentimentAnalysis result = sentimentAnalyzer.analyze(review);
// result.sentiment(), result.score(), result.keywords()
```

---

## 7. Prompt模板管理

```java
// Prompt模板管理（可持久化到数据库）
@Service
public class PromptTemplateService {
    
    private final Map<String, PromptTemplate> templates = new ConcurrentHashMap<>();
    
    public String render(String templateName, Map<String, Object> variables) {
        PromptTemplate template = templates.get(templateName);
        if (template == null) {
            throw new IllegalArgumentException("模板不存在: " + templateName);
        }
        return template.render(variables);
    }
    
    // 注册模板
    @PostConstruct
    public void init() {
        templates.put("code_review", PromptTemplate.from("""
            你是一个资深代码审查专家。
            
            审查以下代码，关注：
            1. 安全漏洞
            2. 性能问题
            3. 代码规范
            4. 改进建议
            
            代码语言：{language}
            代码内容：{code}
            
            输出JSON格式：{issues, suggestions, severity}
            """));
        
        templates.put("summary", PromptTemplate.from("""
            请总结以下内容，不超过{maxWords}字。
            
            内容：{content}
            """));
    }
}
```

---

## 8. 面试要点

### Q1: 什么是Prompt工程？

```
通过设计提示词引导LLM输出期望结果的技术。

核心：
  - 角色设定：给LLM专业角色
  - 任务明确：具体说明做什么
  - 格式约束：指定输出格式
  - 示例引导：Few-shot学习
  - 逐步推理：CoT引导分步思考
```

### Q2: CoT为什么有效？

```
1. LLM是自回归模型，每个token基于前面所有token
2. 直接输出答案时，中间推理过程被压缩为一个token
3. CoT让LLM生成中间推理步骤，每个步骤都作为后续推理的上下文
4. 相当于给LLM更多的"思考空间"

效果：数学推理准确率提升10-30%
```

### Q3: Few-shot的示例数量怎么选？

```
1-2个：简单任务（分类、格式转换）
3-5个：中等任务（分析、总结）
5-10个：复杂任务（代码生成、推理）

注意：
  - 示例太多会消耗token
  - 示例要有多样性（覆盖不同情况）
  - 动态选择（基于相似度检索最相关示例）
```

### Q4: 如何保证LLM输出结构化数据？

```
1. Prompt明确要求输出JSON格式
2. 提供JSON Schema示例
3. 设置temperature=0（减少随机性）
4. 使用框架支持（Spring AI的entity()方法）
5. 后处理：正则提取JSON + JSON解析验证
6. 重试机制：解析失败时重试
```

### Q5: Self-Consistency的代价是什么？

```
代价：调用N次LLM，成本和延迟增加N倍

权衡：
  - N=3-5：成本增加3-5倍，准确率提升5-15%
  - 适合高精度要求场景（金融/医疗）
  - 不适合实时性要求高的场景

优化：并行调用 + 缓存
```

---

## 📚 相关阅读

- [10_LLM模型选型指南](./10_LLM模型选型指南.md)
- [08_RAG架构深度实战](./08_RAG架构深度实战.md)
- [03_Java AI开发实战](./03_Java AI开发实战.md)
- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [06_Spring AI详解](./06_Spring AI详解.md)

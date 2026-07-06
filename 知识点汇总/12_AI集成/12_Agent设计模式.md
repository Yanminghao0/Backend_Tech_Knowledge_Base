# Agent设计模式

> ReAct、Plan-and-Execute、Reflection，构建智能Agent的架构模式

---

## 📋 目录

1. [Agent概述](#1-agent概述)
2. [ReAct模式](#2-react模式)
3. [Plan-and-Execute模式](#3-plan-and-execute模式)
4. [Reflection模式](#4-reflection模式)
5. [工具链设计](#5-工具链设计)
6. [Java实现](#6-java实现)
7. [面试要点](#7-面试要点)

---

## 1. Agent概述

### 什么是Agent

```
Agent = LLM + 工具 + 记忆 + 规划

普通LLM：接收问题 → 生成回答（无状态，无工具）
Agent：接收目标 → 规划步骤 → 调用工具 → 观察结果 → 继续推理 → 完成目标

核心能力：
  1. 自主规划：将复杂目标拆解为步骤
  2. 工具调用：搜索/计算/查询数据库/执行代码
  3. 观察反馈：根据工具返回调整策略
  4. 记忆管理：维护上下文和历史
```

### Agent核心循环

```
Thought → Action → Observation → Thought → Action → ... → Final Answer

  Thought: 我需要查一下用户订单状态
  Action: queryOrder(userId=12345)
  Observation: 订单状态为"已发货"，物流单号SF123456
  Thought: 我需要查物流轨迹
  Action: queryLogistics(trackingNo="SF123456")
  Observation: 包裹已到达北京分拣中心
  Thought: 用户问的是预计到达时间，我已有足够信息
  Final Answer: 您的订单已发货，包裹在北京分拣中心，预计明天送达
```

---

## 2. ReAct模式

### 原理

```
ReAct = Reasoning + Acting

循环：Thought → Action → Observation

优势：
  - 推理和行动交替进行
  - 每步都基于前一步的观察
  - 适合需要多步推理+工具调用的场景
```

### Java实现

```java
@Service
public class ReActAgent {
    
    @Autowired private ChatClient chatClient;
    @Autowired private Map<String, AgentTool> tools;
    
    private static final String REACT_PROMPT = """
        你是一个智能助手，可以通过调用工具来回答问题。
        
        可用工具：
        %s
        
        格式：
        Thought: 你的思考
        Action: 工具名(参数=值)
        Observation: 工具返回结果
        ...（重复Thought/Action/Observation）
        Thought: 我现在可以回答了
        Final Answer: 最终回答
        
        问题：%s
        """;
    
    public String execute(String question, int maxSteps) {
        StringBuilder trace = new StringBuilder();
        trace.append("问题：").append(question).append("\n\n");
        
        for (int step = 0; step < maxSteps; step++) {
            // 1. LLM生成下一步Thought + Action
            String llmOutput = chatClient.prompt()
                .user(String.format(REACT_PROMPT, formatTools(), trace.toString()))
                .call()
                .content();
            
            trace.append(llmOutput).append("\n");
            
            // 2. 检查是否完成
            if (llmOutput.contains("Final Answer:")) {
                return extractFinalAnswer(llmOutput);
            }
            
            // 3. 解析Action并执行工具
            AgentAction action = parseAction(llmOutput);
            if (action != null) {
                String observation = executeTool(action);
                trace.append("Observation: ").append(observation).append("\n\n");
            }
        }
        
        return "达到最大步数，无法完成任务";
    }
    
    private String executeTool(AgentAction action) {
        AgentTool tool = tools.get(action.getToolName());
        if (tool == null) return "工具不存在: " + action.getToolName();
        return tool.execute(action.getParams());
    }
}
```

---

## 3. Plan-and-Execute模式

### 原理

```
Plan-and-Execute = 先规划再执行

1. Planner：LLM将目标拆解为步骤列表
2. Executor：逐步执行每个步骤
3. Re-planner：根据执行结果动态调整计划

优势（vs ReAct）：
  - 减少LLM调用次数（规划一次，执行多次）
  - 全局视角更好（先有完整计划）
  - 适合复杂多步骤任务
```

### Java实现

```java
@Service
public class PlanExecuteAgent {
    
    public String execute(String goal) {
        // 1. 规划
        List<String> plan = createPlan(goal);
        
        // 2. 逐步执行
        StringBuilder context = new StringBuilder();
        for (int i = 0; i < plan.size(); i++) {
            String step = plan.get(i);
            String result = executeStep(step, context.toString());
            context.append("步骤").append(i+1).append(": ").append(step)
                   .append("\n结果: ").append(result).append("\n\n");
            
            // 3. 判断是否需要重新规划
            if (needsReplan(result)) {
                plan = replan(goal, context.toString(), plan, i + 1);
            }
        }
        
        // 4. 总结
        return summarize(goal, context.toString());
    }
    
    private List<String> createPlan(String goal) {
        String prompt = """
            将以下目标拆解为具体的执行步骤（JSON数组）：
            目标：%s
            
            要求：
            - 每步明确可执行
            - 步骤之间有逻辑顺序
            - 输出JSON数组格式
            """.formatted(goal);
        
        String response = chatClient.prompt().user(prompt).call().content();
        return parsePlan(response);
    }
}
```

---

## 4. Reflection模式

### 原理

```
Reflection = 自我反思 + 改进

1. 生成初始答案
2. LLM自我评估答案质量
3. 根据评估改进答案
4. 重复直到满意

效果：代码生成准确率提升15-25%
```

### Java实现

```java
@Service
public class ReflectionAgent {
    
    public String generateWithReflection(String task, int maxRounds) {
        // 1. 生成初始结果
        String result = generate(task);
        
        for (int i = 0; i < maxRounds; i++) {
            // 2. 自我评估
            String critique = critique(task, result);
            
            // 3. 如果评估通过，返回
            if (critique.contains("无需改进") || critique.contains("质量良好")) {
                return result;
            }
            
            // 4. 根据评估改进
            result = improve(task, result, critique);
        }
        
        return result;
    }
    
    private String critique(String task, String result) {
        String prompt = """
            请评估以下回答的质量：
            
            任务：%s
            回答：%s
            
            评估维度：
            1. 正确性：是否准确
            2. 完整性：是否遗漏
            3. 清晰性：是否易懂
            4. 代码可运行性（如适用）
            
            如果质量良好，回答"无需改进"。
            否则，指出具体问题和改进建议。
            """.formatted(task, result);
        
        return chatClient.prompt().user(prompt).call().content();
    }
    
    private String improve(String task, String result, String critique) {
        String prompt = """
            根据以下评估意见改进回答：
            
            任务：%s
            原回答：%s
            评估意见：%s
            
            请输出改进后的回答。
            """.formatted(task, result, critique);
        
        return chatClient.prompt().user(prompt).call().content();
    }
}
```

---

## 5. 工具链设计

### 自定义工具开发

```java
// 工具接口
public interface AgentTool {
    String getName();
    String getDescription();
    String getParametersSchema();
    String execute(Map<String, Object> params);
}

// 数据库查询工具
@Component
public class DatabaseQueryTool implements AgentTool {
    
    @Autowired private JdbcTemplate jdbcTemplate;
    
    @Override
    public String getName() { return "queryDatabase"; }
    
    @Override
    public String getDescription() { 
        return "查询数据库，执行SQL并返回结果"; 
    }
    
    @Override
    public String getParametersSchema() {
        return """
            {"sql": "string", "limit": "int"}
            """;
    }
    
    @Override
    public String execute(Map<String, Object> params) {
        String sql = (String) params.get("sql");
        int limit = (int) params.getOrDefault("limit", 10);
        
        // 安全检查：只允许SELECT
        if (!sql.trim().toUpperCase().startsWith("SELECT")) {
            return "错误：只允许SELECT查询";
        }
        
        List<Map<String, Object>> results = jdbcTemplate.queryForList(
            sql + " LIMIT " + limit);
        return JSON.toJSONString(results);
    }
}

// HTTP请求工具
@Component
public class HttpRequestTool implements AgentTool {
    
    @Override
    public String getName() { return "httpRequest"; }
    
    @Override
    public String getDescription() { return "发送HTTP请求获取数据"; }
    
    @Override
    public String execute(Map<String, Object> params) {
        String url = (String) params.get("url");
        String method = (String) params.getOrDefault("method", "GET");
        
        // 发送请求
        HttpResponse<String> response = httpClient.send(
            HttpRequest.newBuilder(URI.create(url))
                .method(method, BodyPublishers.noBody())
                .build(),
            BodyHandlers.ofString());
        
        return response.body();
    }
}
```

### LangChain4j工具注册

```java
// LangChain4j @Tool注解自动注册
@AiService
public interface SmartAgent {
    
    @SystemMessage("你是一个智能助手，可以查询数据库、发送HTTP请求")
    String ask(String question);
}

@Component
public class AgentTools {
    
    @Autowired private OrderService orderService;
    
    @Tool("根据订单ID查询订单状态")
    public String queryOrder(Long orderId) {
        Order order = orderService.getOrder(orderId);
        return String.format("订单%s，状态：%s，金额：%s", 
            orderId, order.getStatus(), order.getAmount());
    }
    
    @Tool("查询当前天气")
    public String queryWeather(String city) {
        return weatherService.getWeather(city);
    }
}
```

---

## 6. Agent记忆管理

```java
@Service
public class AgentMemory {
    
    // 短期记忆：当前对话上下文
    private final List<ChatMessage> shortTermMemory = new ArrayList<>();
    
    // 长期记忆：向量存储
    @Autowired
    private VectorStore longTermMemory;
    
    // 添加记忆
    public void remember(String content, String type) {
        // 短期记忆
        shortTermMemory.add(new UserMessage(content));
        
        // 重要信息存入长期记忆
        if ("important".equals(type)) {
            longTermMemory.add(List.of(
                new Document(content, Map.of("type", type, 
                    "time", System.currentTimeMillis()))));
        }
        
        // 短期记忆超过20条时压缩
        if (shortTermMemory.size() > 20) {
            compressMemory();
        }
    }
    
    // 检索相关记忆
    public String recall(String query) {
        // 1. 检索长期记忆
        List<Document> relevant = longTermMemory.similaritySearch(
            SearchRequest.builder().query(query).topK(3).build());
        
        // 2. 组装上下文
        StringBuilder context = new StringBuilder("相关历史信息：\n");
        for (Document doc : relevant) {
            context.append(doc.getText()).append("\n");
        }
        
        return context.toString();
    }
    
    // 压缩记忆（总结历史对话）
    private void compressMemory() {
        String summary = chatClient.prompt()
            .user("总结以下对话要点：\n" + formatMessages(shortTermMemory))
            .call()
            .content();
        
        shortTermMemory.clear();
        shortTermMemory.add(new SystemMessage("之前的对话总结：" + summary));
    }
}
```

---

## 7. 面试要点

### Q1: Agent和普通LLM调用的区别？

```
普通LLM：输入 → 输出（无状态，无工具）
Agent：目标 → 规划 → 工具调用 → 观察 → 推理 → 完成

Agent核心：
  - 自主规划：拆解复杂任务
  - 工具调用：与外部世界交互
  - 观察反馈：根据结果调整策略
  - 记忆管理：维护上下文
```

### Q2: ReAct模式是什么？

```
ReAct = Reasoning + Acting

循环：Thought → Action → Observation

Thought：LLM思考下一步做什么
Action：调用工具
Observation：观察工具返回结果
→ 继续下一个Thought

优势：推理和行动交替，适合需要多步推理+工具的场景
```

### Q3: Agent的工具怎么设计？

```
1. 工具粒度：一个工具做一件事
2. 参数明确：清晰的参数Schema
3. 安全限制：SQL只允许SELECT，HTTP限制域名
4. 错误处理：工具失败返回友好错误信息
5. 工具描述：让LLM理解何时用哪个工具
6. 组合能力：工具之间可以组合使用
```

### Q4: Agent如何管理记忆？

```
短期记忆：
  - 当前对话上下文
  - 超过限制时压缩（LLM总结）
  - 最近N轮对话

长期记忆：
  - 向量数据库存储
  - 按相关性检索
  - 重要信息持久化

记忆策略：
  - 摘要压缩：定期总结历史
  - 实体检索：按实体/时间检索
  - 遗忘机制：过期信息删除
```

### Q5: Agent的局限性是什么？

```
1. 可靠性：LLM可能产生幻觉，导致错误工具调用
2. 成本：多轮LLM调用，成本高
3. 延迟：多步推理，响应时间长
4. 安全性：工具执行可能产生副作用
5. 调试困难：Agent行为不确定，难以复现

应对：
  - 工具安全限制
  - 最大步数限制
  - 人工审核关键操作
  - 详细日志记录
```

---

## 📚 相关阅读

- [01_Agent-Flex详解](./01_Agent-Flex详解.md)
- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [06_Spring AI详解](./06_Spring AI详解.md)
- [11_Prompt工程进阶](./11_Prompt工程进阶.md)
- [MCP协议核心原理与实战](../15_MCP协议/03_MCP协议核心原理与实战.md)

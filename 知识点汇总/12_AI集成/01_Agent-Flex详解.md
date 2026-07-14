# Agent-Flex详解

> Noear(MyBatis-Flex作者)开源的轻量级Java AI Agent框架：专注于构建强大的AI智能体应用

---

## 📋 目录

1. [Agent-Flex概述](#1-agent-flex概述)
2. [核心架构](#2-核心架构)
3. [快速开始](#3-快速开始)
4. [Agent开发](#4-agent开发)
5. [工具系统](#5-工具系统)
6. [记忆管理](#6-记忆管理)
7. [多Agent协同](#7-多agent协同)
8. [最佳实践](#8-最佳实践)

---

## 1. Agent-Flex概述

### 1.1 什么是Agent-Flex

```
Agent-Flex：
- Noear(MyBatis-Flex作者)开源的轻量级Java AI Agent框架
- 专注于构建强大的AI智能体应用
- 支持多种LLM（通义千问、OpenAI等）
- 提供完整的Agent开发工具链
- 与Spring Boot深度集成
```

### 1.2 核心特性

```
✅ 强大的Agent能力：
   - 多步推理
   - 自主决策
   - 工具调用
   - 记忆管理

✅ 多LLM支持：
   - 通义千问（DashScope）
   - OpenAI
   - 本地模型（Ollama）

✅ 工具系统：
   - 丰富的内置工具
   - 自定义工具开发
   - 工具链编排

✅ 记忆管理：
   - 短期记忆
   - 长期记忆
   - 上下文管理

✅ 多Agent协同：
   - Agent之间通信
   - 任务分工
   - 结果聚合

✅ Spring Boot集成：
   - 自动配置
   - 依赖注入
   - 配置管理
```

### 1.3 与其他框架对比

| 框架 | Agent能力 | LLM支持 | 工具系统 | Spring集成 | 推荐度 |
|------|----------|---------|---------|-----------|--------|
| Agent-Flex | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| LangChain4j | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Spring AI | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 2. 核心架构

### 2.1 架构设计

Agent-Flex采用分层架构：

```
应用层（Controller、Service）
  ↓
Agent-Flex Core
  ↓
├── Agent引擎（推理、决策）
├── 工具系统（工具调用、编排）
├── 记忆系统（短期、长期记忆）
└── LLM适配层（通义千问、OpenAI等）
```

### 2.2 核心组件

```
1. Agent：
   - AI智能体核心
   - 多步推理能力
   - 自主决策能力
   - 工具调用能力

2. Tool：
   - 工具接口
   - 工具注册和发现
   - 工具执行

3. Memory：
   - 记忆管理
   - 短期记忆（对话上下文）
   - 长期记忆（知识库）

4. LLM：
   - 大语言模型适配
   - 统一API接口
   - 多模型切换

5. Planner：
   - 任务规划
   - 步骤分解
   - 执行顺序

6. Executor：
   - 任务执行
   - 工具调用
   - 结果收集
```

---

## 3. 快速开始

### 3.1 Maven依赖

```xml
<dependencies>
    <!-- Agent-Flex核心 -->
    <dependency>
        <groupId>com.agentsflex</groupId>
        <artifactId>agent-flex-spring-boot-starter</artifactId>
        <version>1.0.0</version>
    </dependency>
    
    <!-- 通义千问集成 -->
    <dependency>
        <groupId>com.agentsflex</groupId>
        <artifactId>agent-flex-dashscope</artifactId>
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
agent-flex:
  dashscope:
    api-key: ${DASHSCOPE_API_KEY}
    chat:
      model: qwen-plus
      temperature: 0.7
      max-tokens: 2000
  agent:
    max-iterations: 10
    enable-memory: true
```

### 3.3 基础使用

```java
@RestController
@RequestMapping("/agent")
public class AgentController {
    
    @Autowired
    private AgentService agentService;
    
    @PostMapping("/chat")
    public String chat(@RequestBody ChatRequest request) {
        return agentService.chat(request.getMessage());
    }
}
```

---

## 4. Agent开发

### 4.1 基础Agent

```java
@Service
public class BasicAgentService {
    
    @Autowired
    private AgentFactory agentFactory;
    
    public String chat(String message) {
        // 创建Agent
        Agent agent = agentFactory.createAgent()
            .systemMessage("你是一个智能助手，可以帮助用户完成各种任务。")
            .tools(createTools())
            .memory(new ConversationMemory())
            .build();
        
        // Agent对话
        return agent.chat(message);
    }
    
    private List<Tool> createTools() {
        return List.of(
            new WeatherTool(),
            new CalculatorTool(),
            new SearchTool()
        );
    }
}
```

### 4.2 ReAct Agent

```java
@Service
public class ReActAgentService {
    
    public String reactChat(String message) {
        // ReAct Agent：推理-行动-观察循环
        ReActAgent agent = agentFactory.createReActAgent()
            .systemMessage("你是一个智能助手，可以帮助用户完成各种任务。")
            .tools(createTools())
            .maxIterations(10)
            .memory(new ConversationMemory())
            .build();
        
        return agent.chat(message);
    }
}
```

### 4.3 Plan-and-Execute Agent

```java
@Service
public class PlanExecuteAgentService {
    
    public String planExecute(String goal) {
        // Plan-and-Execute Agent：先规划后执行
        PlanExecuteAgent agent = agentFactory.createPlanExecuteAgent()
            .systemMessage("你是一个任务规划专家，可以将复杂任务分解为多个步骤。")
            .tools(createTools())
            .planner(new LLMPlanner())
            .executor(new ToolExecutor())
            .build();
        
        return agent.execute(goal);
    }
}
```

### 4.4 自定义Agent

```java
@Component
public class CustomAgent extends BaseAgent {
    
    @Autowired
    private ChatClient chatClient;
    
    @Autowired
    private List<Tool> tools;
    
    @Override
    public String chat(String message) {
        // 自定义Agent逻辑
        // 1. 分析用户意图
        String intent = analyzeIntent(message);
        
        // 2. 选择工具
        Tool selectedTool = selectTool(intent);
        
        // 3. 执行工具
        String toolResult = selectedTool.execute(message);
        
        // 4. 生成回复
        String response = chatClient.call(
            "基于工具执行结果：" + toolResult + "\n\n用户问题：" + message
        );
        
        return response;
    }
    
    private String analyzeIntent(String message) {
        // 意图分析逻辑
        return "query";
    }
    
    private Tool selectTool(String intent) {
        // 工具选择逻辑
        return tools.get(0);
    }
}
```

---

## 5. 工具系统

### 5.1 定义工具

```java
@Component
public class WeatherTool implements Tool {
    
    @Override
    public String getName() {
        return "getWeather";
    }
    
    @Override
    public String getDescription() {
        return "获取指定城市的天气信息";
    }
    
    @Override
    public ToolParameter getParameters() {
        return ToolParameter.builder()
            .type("object")
            .properties(Map.of(
                "city", ToolParameter.builder()
                    .type("string")
                    .description("城市名称")
                    .required(true)
                    .build()
            ))
            .build();
    }
    
    @Override
    public String execute(Map<String, Object> parameters) {
        String city = (String) parameters.get("city");
        // 调用天气API
        return "北京：25°C，晴天";
    }
}
```

### 5.2 工具注册

```java
@Configuration
public class ToolConfig {
    
    @Bean
    public ToolRegistry toolRegistry() {
        ToolRegistry registry = new ToolRegistry();
        registry.register(new WeatherTool());
        registry.register(new CalculatorTool());
        registry.register(new SearchTool());
        return registry;
    }
}
```

### 5.3 工具链编排

```java
@Service
public class ToolChainService {
    
    @Autowired
    private ToolRegistry toolRegistry;
    
    public String executeToolChain(String task) {
        // 定义工具链
        ToolChain chain = ToolChain.builder()
            .addStep("search", "搜索相关信息")
            .addStep("analyze", "分析搜索结果")
            .addStep("generate", "生成最终答案")
            .build();
        
        // 执行工具链
        return chain.execute(task);
    }
}
```

### 5.4 工具组合

```java
@Service
public class ToolCompositionService {
    
    public String composeTools(String task) {
        // 工具组合：并行执行多个工具
        List<Tool> tools = List.of(
            toolRegistry.get("weather"),
            toolRegistry.get("stock"),
            toolRegistry.get("news")
        );
        
        // 并行执行
        List<String> results = tools.parallelStream()
            .map(tool -> tool.execute(Map.of("query", task)))
            .collect(Collectors.toList());
        
        // 聚合结果
        return aggregateResults(results);
    }
}
```

---

## 6. 记忆管理

### 6.1 短期记忆（对话上下文）

```java
@Service
public class ConversationMemoryService {
    
    @Autowired
    private MemoryStore memoryStore;
    
    public String chatWithMemory(String sessionId, String message) {
        // 获取或创建记忆
        ConversationMemory memory = memoryStore.getOrCreate(
            sessionId,
            ConversationMemory::new
        );
        
        // 添加用户消息
        memory.addUserMessage(message);
        
        // 生成回复
        String response = agent.chat(message, memory);
        
        // 添加助手回复
        memory.addAssistantMessage(response);
        
        // 保存记忆
        memoryStore.save(sessionId, memory);
        
        return response;
    }
}
```

### 6.2 长期记忆（知识库）

```java
@Service
public class LongTermMemoryService {
    
    @Autowired
    private KnowledgeBase knowledgeBase;
    
    public void storeKnowledge(String key, String content) {
        // 存储知识
        knowledgeBase.store(key, content);
    }
    
    public String retrieveKnowledge(String query) {
        // 检索相关知识
        return knowledgeBase.retrieve(query);
    }
    
    public String chatWithKnowledge(String message) {
        // 1. 检索相关知识
        String knowledge = retrieveKnowledge(message);
        
        // 2. 结合知识生成回复
        String prompt = String.format(
            "基于以下知识回答问题：\n\n%s\n\n问题：%s\n\n答案：",
            knowledge,
            message
        );
        
        return chatClient.call(prompt);
    }
}
```

### 6.3 记忆检索

```java
@Service
public class MemoryRetrievalService {
    
    @Autowired
    private MemoryStore memoryStore;
    
    public List<String> retrieveRelevantMemories(String sessionId, String query) {
        // 获取记忆
        ConversationMemory memory = memoryStore.get(sessionId);
        
        if (memory == null) {
            return Collections.emptyList();
        }
        
        // 检索相关记忆
        return memory.retrieveRelevant(query, 5); // top-5
    }
}
```

---

## 7. 多Agent协同

### 7.1 Agent通信

```java
@Service
public class MultiAgentService {
    
    @Autowired
    private AgentFactory agentFactory;
    
    public String multiAgentChat(String task) {
        // 创建多个Agent
        Agent researchAgent = agentFactory.createAgent()
            .systemMessage("你是一个研究专家，负责收集和分析信息。")
            .build();
        
        Agent analysisAgent = agentFactory.createAgent()
            .systemMessage("你是一个分析专家，负责分析数据和得出结论。")
            .build();
        
        Agent writerAgent = agentFactory.createAgent()
            .systemMessage("你是一个写作专家，负责撰写报告。")
            .build();
        
        // Agent协作流程
        // 1. 研究Agent收集信息
        String research = researchAgent.chat(task);
        
        // 2. 分析Agent分析信息
        String analysis = analysisAgent.chat(research);
        
        // 3. 写作Agent生成报告
        String report = writerAgent.chat(analysis);
        
        return report;
    }
}
```

### 7.2 任务分工

```java
@Service
public class TaskDivisionService {
    
    public String divideAndConquer(String complexTask) {
        // 任务分解
        List<String> subtasks = decomposeTask(complexTask);
        
        // 分配给不同的Agent
        Map<String, Agent> agents = Map.of(
            "research", createResearchAgent(),
            "analysis", createAnalysisAgent(),
            "writing", createWritingAgent()
        );
        
        // 并行执行
        Map<String, String> results = subtasks.parallelStream()
            .collect(Collectors.toMap(
                subtask -> subtask,
                subtask -> {
                    Agent agent = selectAgent(subtask, agents);
                    return agent.chat(subtask);
                }
            ));
        
        // 聚合结果
        return aggregateResults(results);
    }
}
```

### 7.3 Agent编排

```java
@Service
public class AgentOrchestrationService {
    
    public String orchestrateAgents(String task) {
        // 定义Agent编排流程
        AgentWorkflow workflow = AgentWorkflow.builder()
            .addStep("research", researchAgent)
            .addStep("analysis", analysisAgent)
            .addStep("review", reviewAgent)
            .addStep("writing", writingAgent)
            .build();
        
        // 执行工作流
        return workflow.execute(task);
    }
}
```

---

## 8. 最佳实践

### 8.1 配置管理

```yaml
agent-flex:
  dashscope:
    api-key: ${DASHSCOPE_API_KEY}
    chat:
      model: qwen-plus
      temperature: 0.7
      max-tokens: 2000
  agent:
    max-iterations: 10
    enable-memory: true
    memory-size: 20
  tool:
    timeout: 30s
    max-retries: 3
```

### 8.2 错误处理

```java
@Service
public class RobustAgentService {
    
    @Retryable(
        value = {Exception.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2)
    )
    public String chatWithRetry(String message) {
        try {
            return agent.chat(message);
        } catch (Exception e) {
            log.error("Agent调用失败", e);
            throw e;
        }
    }
    
    @Recover
    public String recover(Exception e, String message) {
        return "抱歉，系统暂时无法处理您的请求，请稍后重试。";
    }
}
```

### 8.3 性能优化

```java
@Service
public class PerformanceOptimizedService {
    
    // 异步处理
    @Async
    public CompletableFuture<String> chatAsync(String message) {
        return CompletableFuture.supplyAsync(() -> 
            agent.chat(message)
        );
    }
    
    // 批量处理
    public List<String> batchChat(List<String> messages) {
        return messages.parallelStream()
            .map(agent::chat)
            .collect(Collectors.toList());
    }
    
    // 缓存结果
    @Cacheable(value = "agent-responses", key = "#message")
    public String chat(String message) {
        return agent.chat(message);
    }
}
```

### 8.4 监控和日志

```java
@Aspect
@Component
public class AgentLoggingAspect {
    
    @Around("execution(* com.agentsflex.agent..*.*(..))")
    public Object logAgentCalls(ProceedingJoinPoint joinPoint) throws Throwable {
        long startTime = System.currentTimeMillis();
        try {
            Object result = joinPoint.proceed();
            long duration = System.currentTimeMillis() - startTime;
            log.info("Agent调用成功: {}ms", duration);
            return result;
        } catch (Exception e) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("Agent调用失败: {}ms", duration, e);
            throw e;
        }
    }
}
```

---

## 9. 实战案例

### 9.1 智能客服Agent

```java
@Service
public class CustomerServiceAgent {
    @Autowired
    private AgentFactory agentFactory;
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private UserRepository userRepository;
    
    public String handleCustomerQuery(String userId, String query) {
        // 创建客服Agent
        Agent agent = agentFactory.createReActAgent()
            .systemMessage("你是电商平台智能客服，可查询订单、处理售后、推荐商品。")
            .tools(createCustomerServiceTools())
            .memory(createCustomerMemory(userId))
            .maxIterations(8)
            .build();
        
        return agent.chat(query);
    }
    
    private List<Tool> createCustomerServiceTools() {
        return List.of(
            new OrderQueryTool(orderRepository),
            new RefundTool(orderRepository),
            new ProductRecommendTool(),
            new ShippingTool()
        );
    }
    
    private Memory createCustomerMemory(String userId) {
        // 结合用户历史对话和订单数据
        User user = userRepository.findById(userId).orElse(null);
        return new CompositeMemory(
            new ConversationMemory(),
            new UserProfileMemory(user),
            new OrderHistoryMemory(orderRepository.findByUserId(userId))
        );
    }
}
```

### 9.2 多Agent协作数据分析系统

```java
@Service
public class DataAnalysisSystem {
    public String analyzeBusinessData(String analysisGoal) {
        // 1. 创建数据采集Agent
        Agent dataCollector = agentFactory.createAgent()
            .systemMessage("你是数据采集专家，负责从数据库和API收集相关业务数据。")
            .tools(List.of(new DatabaseTool(), new ApiTool()))
            .build();
        
        // 2. 创建数据分析Agent
        Agent dataAnalyzer = agentFactory.createAgent()
            .systemMessage("你是数据分析专家，负责统计分析和可视化。")
            .tools(List.of(new StatisticsTool(), new VisualizationTool()))
            .build();
        
        // 3. 创建报告生成Agent
        Agent reportGenerator = agentFactory.createAgent()
            .systemMessage("你是报告撰写专家，负责生成业务分析报告。")
            .tools(List.of(new ReportTool()))
            .build();
        
        // 执行协作流程
        String rawData = dataCollector.chat(analysisGoal);
        String analysisResult = dataAnalyzer.chat(rawData);
        return reportGenerator.chat(analysisResult);
    }
}
```

### 9.3 Agent监控与可观测性

```java
@Configuration
public class AgentMonitoringConfig {
    @Bean
    public MeterRegistryCustomizer<MeterRegistry> agentMetrics() {
        return registry -> {
            registry.timer("agent.chat.duration");
            registry.counter("agent.tool.calls");
            registry.gauge("agent.memory.size");
        };
    }
    
    @Bean
    public AgentInterceptor monitoringInterceptor(MeterRegistry registry) {
        return new AgentInterceptor() {
            @Override
            public void beforeChat(String message) {
                // 记录对话开始
            }
            
            @Override
            public void afterChat(String response, long durationMs) {
                Timer.start(registry).stop(registry.timer("agent.chat.duration"));
            }
        };
    }
}
```

---

## 📚 参考资源

- 🔗 [Agent-Flex官方文档](https://github.com/alibaba-cloud/agent-flex)
- 🔗 [GitHub仓库](https://github.com/alibaba-cloud/agent-flex)
- 🔗 [示例代码](https://github.com/alibaba-cloud/agent-flex-examples)

---

*最后更新：2025-11-04*

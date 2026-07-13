# Agent核心架构与ReAct模式

> 从Agent定义到核心循环，从ReAct到Plan-Execute，掌握AI Agent的基础架构

---

## 📋 目录

1. [Agent概述](#1-agent概述)
2. [Agent核心循环](#2-agent核心循环)
3. [ReAct模式](#3-react模式)
4. [Plan-and-Execute模式](#4-plan-and-execute模式)
5. [ReWOO与LLMCompiler](#5-rewoo与llmcompiler)
6. [Agent设计模式](#6-agent设计模式)
7. [Spring AI Agent实战](#7-spring-ai-agent实战)
8. [面试题速查](#8-面试题速查)

---

## 1. Agent概述

### 1.1 什么是AI Agent

```
AI Agent = 感知环境 + 自主决策 + 执行行动 + 观察反馈

  ┌──────────────────────────────────────────────────────┐
  │  普通ChatBot               │  AI Agent                │
  │  ──────────              │  ──────                 │
  │  只能对话                   │  对话 + 行动              │
  │  被动回答                   │  主动规划执行             │
  │  无状态                     │  有记忆                   │
  │  无法操作外部系统            │  可调用工具/API           │
  │  单轮或简单多轮              │  复杂多步任务             │
  │  无法自我纠错               │  可反思和修正             │
  └──────────────────────────────────────────────────────┘

  Agent的核心能力:
    1. 理解意图 — 理解用户的复杂需求
    2. 规划任务 — 将目标分解为可执行步骤
    3. 使用工具 — 调用API/搜索/数据库/代码执行
    4. 观察反馈 — 根据工具返回结果调整策略
    5. 自主决策 — 判断任务是否完成或需要调整
    6. 持续记忆 — 记住之前的交互和中间结果

  类比:
    ChatBot = 问答机器(问什么答什么)
    Agent = 数字员工(给目标，自己想办法完成)
```

### 1.2 Agent vs Workflow

```
┌──────────────────────────────────────────────────────┐
  │  维度        │  Workflow(工作流)  │  Agent(智能体)    │
  │  ──────    │  ──────         │  ──────        │
  │  执行路径    │  预定义(固定)       │  动态(LLM决定)    │
  │  控制流      │  代码控制           │  LLM控制          │
  │  灵活性      │  低(分支固定)       │  高(自主决策)      │
  │  可预测性    │  高(路径确定)       │  低(路径不确定)    │
  │  适用场景    │  流程明确的任务      │  需要探索的任务    │
  │  调试难度    │  低                 │  高               │
  └──────────────────────────────────────────────────────┘

  选择建议:
    流程明确 → Workflow(如: 固定步骤的ETL)
    需要判断 → Agent(如: 用户问题→决定用哪个工具)
    混合 → Agent外层+Workflow内层(如: Agent决定策略→执行固定流程)
```

---

## 2. Agent核心循环

### 2.1 基本循环

```
Agent核心循环 = 观察 → 思考 → 行动 → 观察(循环)

  ┌──────────────────────────────────────────┐
  │            用户输入任务                     │
  │                ↓                          │
  │          ┌──────────┐                     │
  │          │  观察     │ ← 工具返回/环境状态  │
  │          │ Observe  │                     │
  │          └────┬─────┘                     │
  │               ↓                           │
  │          ┌──────────┐                     │
  │          │  思考     │ ← LLM推理决策       │
  │          │ Think    │                     │
  │          └────┬─────┘                     │
  │               ↓                           │
  │          ┌──────────┐                     │
  │          │  行动     │ → 调用工具/API      │
  │          │ Act      │                     │
  │          └────┬─────┘                     │
  │               ↓                           │
  │          ┌──────────┐                     │
  │          │ 观察结果  │ ← 工具返回           │
  │          │ Observe  │                     │
  │          └────┬─────┘                     │
  │               ↓                           │
  │         任务完成?                          │
  │          ↙    ↘                           │
  │        否      是                          │
  │        ↓        ↓                          │
  │     回到思考   输出结果                     │
  └──────────────────────────────────────────┘

  每一轮(Thought-Action-Observation)称为一个"step"
  Agent通常限制最大步数(如10-20步)防止无限循环
```

### 2.2 LLM as Agent Brain

```
LLM在Agent中的角色 = 大脑(决策中心)

  LLM负责:
    1. 理解用户意图 — "帮我查下北京明天天气" → 意图: 查天气
    2. 选择工具 — 从可用工具中选择"get_weather"
    3. 生成参数 — 从自然语言提取参数 {city: "北京", date: "明天"}
    4. 理解观察 — 解析工具返回的JSON数据
    5. 决定下一步 — 是否需要更多工具调用? 是否可以回答了?
    6. 生成最终回答 — 将多步结果整合为自然语言

  Agent需要的LLM能力:
    1. 指令跟随 — 准确理解复杂指令
    2. 工具调用 — Function Calling能力
    3. 推理能力 — 多步逻辑推理
    4. 上下文管理 — 处理长对话历史
    5. 结构化输出 — 输出JSON/特定格式

  适合做Agent的模型:
    Claude 4 — 推理+工具调用最强
    GPT-5 — 综合能力最强
    Qwen2.5-72B — 开源最强
    DeepSeek-V3 — 性价比最高
```

---

## 3. ReAct模式

### 3.1 ReAct原理

```
ReAct = Reason(推理) + Act(行动) 交替执行

  论文: "ReAct: Synergizing Reasoning and Acting in Language Models" (2022)

  核心思想:
    让LLM在"思考推理"和"执行行动"之间交替
    思考指导行动，行动的反馈指导下一步思考

  ReAct循环:
    Thought(思考) → Action(行动) → Observation(观察) → Thought → ...

  示例:
    用户: "北京和上海今天哪个温度高？"

    Thought 1: 我需要查询北京和上海的天气，然后比较温度
    Action 1: get_weather(city="北京")
    Observation 1: 北京今天晴，最高温度35°C

    Thought 2: 北京35°C，现在查上海
    Action 2: get_weather(city="上海")
    Observation 2: 上海今天多云，最高温度30°C

    Thought 3: 北京35°C > 上海30°C，北京温度更高
    Action 3: Final Answer: 北京今天温度更高，最高35°C，上海30°C
```

### 3.2 ReAct Prompt模板

```
ReAct的标准Prompt结构:

  System Prompt:
  ```
  你是一个能使用工具的AI助手。请按以下格式回答:

  Question: 用户的输入问题
  Thought: 你的思考和推理
  Action: 要使用的工具名称
  Action Input: 工具的参数(JSON格式)
  Observation: 工具返回的结果

  (Thought/Action/Observation可以重复多轮)

  Thought: 我现在可以回答了
  Final Answer: 最终回答
  ```

  工具描述:
  ```
  可用工具:
  1. search_web(query: str) - 搜索网页内容
  2. get_weather(city: str) - 查询天气
  3. calculator(expression: str) - 数学计算
  4. database_query(sql: str) - 查询数据库
  ```

  完整示例:
  ```
  Question: 查询用户ID为1001的订单总金额

  Thought: 我需要先查询数据库获取用户1001的订单
  Action: database_query
  Action Input: {"sql": "SELECT amount FROM orders WHERE user_id = 1001"}
  Observation: [{"amount": 99.9}, {"amount": 50.0}, {"amount": 200.5}]

  Thought: 有3笔订单，金额分别是99.9、50.0、200.5，我需要计算总和
  Action: calculator
  Action Input: {"expression": "99.9 + 50.0 + 200.5"}
  Observation: 350.4

  Thought: 总金额是350.4元，现在可以回答了
  Final Answer: 用户ID为1001的订单总金额为350.4元。
  ```
```

### 3.3 ReAct的优缺点

```
ReAct优点:
  1. 简单直观 — Thought-Action-Observation循环清晰
  2. 可解释 — 每步都有推理过程，易于调试
  3. 灵活 — LLM自主决定用哪个工具、什么时候用
  4. 自纠错 — Observation反馈后可以调整策略

ReAct缺点:
  1. 串行执行 — 每步等待前一步完成，速度慢
  2. LLM调用多 — 每步一次LLM调用，成本高
  3. 依赖LLM推理 — 如果LLM推理出错，后续全错
  4. 上下文增长 — 每步累积上下文，可能超出窗口
  5. 可能循环 — 陷入"Thought→Action→相同Observation"循环

  优化方案:
    1. 限制步数(max_iterations=10)
    2. 并行工具调用(可同时调用的工具并行)
    3. 上下文压缩(对话历史摘要)
    4. 超时机制(单步超时则跳过)
```

---

## 4. Plan-and-Execute模式

### 4.1 原理

```
Plan-and-Execute = 先全局规划，再逐步执行

  与ReAct的区别:
    ReAct: 每步都思考下一步做什么(走一步看一步)
    Plan-Execute: 先制定完整计划，再执行(谋定而后动)

  ┌──────────────────────────────────────────────┐
  │  ReAct模式:                                   │
  │    Think → Act → Observe → Think → Act → ...  │
  │    (每步决定下一步，可能走偏)                   │
  │                                              │
  │  Plan-Execute模式:                            │
  │    Plan: [步骤1, 步骤2, 步骤3, 步骤4]          │
  │    Execute: 逐步执行                           │
  │    Replan: 如果执行中发现计划不对，重新规划      │
  │    (全局视角，不容易走偏)                       │
  └──────────────────────────────────────────────┘

  示例:
    用户: "调研3个主流Java微服务框架的优缺点，写一份对比报告"

    Plan阶段:
      步骤1: 搜索Spring Cloud的特点和优缺点
      步骤2: 搜索Dubbo的特点和优缺点
      步骤3: 搜索Quarkus的特点和优缺点
      步骤4: 整理对比表格
      步骤5: 撰写总结报告

    Execute阶段:
      执行步骤1 → 得到Spring Cloud信息
      执行步骤2 → 得到Dubbo信息
      执行步骤3 → 得到Quarkus信息
      (如果某步信息不足，触发Replan)

    Execute步骤4-5: 整合并撰写报告
```

### 4.2 LangChain Plan-Execute实现

```python
from langchain import OpenAI, SerpAPIWrapper
from langchain.agents import initialize_agent, AgentType

# 方式1: LangChain内置Plan-Execute
# plan_and_execute需要LangChain Experimental模块

from langchain_experimental.plan_and_execute import (
    PlanAndExecute, load_agent_executor, load_chat_planner
)

# 规划器(生成计划)
planner = load_chat_planner(llm=ChatOpenAI(temperature=0))

# 执行器(逐步执行)
executor = load_agent_executor(
    llm=OpenAI(temperature=0),
    tools=[search_tool, calculator_tool],
    verbose=True
)

# 组合
agent = PlanAndExecute(planner=planner, executor=executor)
result = agent.run("对比3个Java微服务框架的优缺点")
```

```
Plan-Execute优缺点:

  优点:
    1. 全局视角 — 先规划再执行，不易走偏
    2. 效率高 — 并行执行无依赖的步骤
    3. 可追溯 — 计划明确，易于审查

  缺点:
    1. 规划可能不准 — LLM一次性规划可能遗漏
    2. 灵活性差 — 计划外的发现需要Replan
    3. 初始延迟 — 必须等规划完成才能开始执行
```

---

## 5. ReWOO与LLMCompiler

### 5.1 ReWOO

```
ReWOO = Reasoning WithOut Observation

  核心改进: 减少LLM调用次数
    ReAct: 每步都调用LLM(Thought需要LLM)
    ReWOO: 一次性生成所有计划和工具调用，并行执行，最后一次LLM合并

  ┌──────────────────────────────────────────────────┐
  │  ReWOO三阶段:                                     │
  │                                                  │
  │  1. Planner(规划): 一次LLM调用生成全部计划         │
  │     Plan#1: 搜索"Spring Cloud优缺点"              │
  │     Plan#2: 搜索"Dubbo优缺点" (依赖#1? 不依赖)    │
  │     Plan#3: 搜索"Quarkus优缺点"                   │
  │     Plan#4: 基于#1#2#3撰写对比报告                │
  │                                                  │
  │  2. Worker(执行): 并行执行无依赖的工具调用         │
  │     Plan#1, #2, #3 并行执行                       │
  │     Plan#4 等待#1#2#3完成后执行                   │
  │                                                  │
  │  3. Solver(合并): 一次LLM调用整合所有结果          │
  │     基于#1#2#3的结果生成最终报告                   │
  └──────────────────────────────────────────────────┘

  优势:
    LLM调用从N次降到3次(Planner + Solver + 可能的Replan)
    工具调用并行 → 速度快
    成本低(LLM调用少)
```

### 5.2 LLMCompiler

```
LLMCompiler = 并行工具调用编排(DAG执行)

  核心思想:
    将Agent任务表示为DAG(有向无环图)
    无依赖的节点并行执行
    有依赖的节点等待前置完成

  ┌──────────────────────────────────────────┐
  │  示例DAG:                                 │
  │                                          │
  │     搜索Spring Cloud    搜索Dubbo          │
  │         ↓                  ↓              │
  │     搜索Quarkus             │             │
  │         ↓                  ↓              │
  │         └──────┬───────────┘              │
  │                ↓                          │
  │           撰写报告                         │
  │                                          │
  │  前三个搜索并行 → 最后写报告                │
  └──────────────────────────────────────────┘

  LangGraph实现:
    from langgraph.graph import StateGraph

    # 定义节点函数
    def search_spring(state): ...
    def search_dubbo(state): ...
    def search_quarkus(state): ...
    def write_report(state): ...

    # 构建DAG
    graph = StateGraph(AgentState)
    graph.add_node("search_spring", search_spring)
    graph.add_node("search_dubbo", search_dubbo)
    graph.add_node("search_quarkus", search_quarkus)
    graph.add_node("write_report", write_report)

    # 边: 三个搜索 → 写报告( fan-in )
    graph.add_edge("search_spring", "write_report")
    graph.add_edge("search_dubbo", "write_report")
    graph.add_edge("search_quarkus", "write_report")

    # 三个搜索从START并行触发
    graph.set_conditional_entry_point(
        route_to_all_searches  # 返回多个节点名
    )
```

---

## 6. Agent设计模式

### 6.1 Router(路由)模式

```
Router Agent = 根据输入路由到不同的子Agent或工具

  ┌──────────────────────────────────────────┐
  │              用户输入                      │
  │                  ↓                        │
  │          ┌──────────────┐                 │
  │          │  Router LLM  │                 │
  │          │  (路由判断)   │                 │
  │          └──────┬───────┘                 │
  │          ↙      ↓       ↘                 │
  │     ┌──────┐┌──────┐┌──────┐            │
  │     │RAG   ││SQL   ││Search│            │
  │     │Agent ││Agent ││Agent │            │
  │     └──────┘└──────┘└──────┘            │
  │          ↘      ↓       ↙                 │
  │          ┌──────────────┐                 │
  │          │  合并输出     │                 │
  │          └──────────────┘                 │
  └──────────────────────────────────────────┘

  适用场景: 不同类型问题需要不同处理方式
  优点: 每个子Agent专注一个领域，效果好
  缺点: Router可能判断错误
```

### 6.2 Chain(链式)模式

```
Chain Agent = 多个Agent串行处理，前一个的输出是后一个的输入

  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
  │ 研究 │───→│ 写作 │───→│ 审校 │───→│ 发布 │
  │Agent │    │Agent │    │Agent │    │Agent │
  └──────┘    └──────┘    └──────┘    └──────┘

  适用场景: 流程性任务(研究→写作→审校→发布)
  优点: 每步专业化，质量高
  缺点: 串行执行慢，前一步出错影响后续
```

### 6.3 DAG(有向图)模式

```
DAG Agent = 有向无环图，支持并行和依赖

       ┌──────┐
       │ 规划 │
       └──┬───┘
          ↓
     ┌────┴────┐
     ↓         ↓
  ┌──────┐ ┌──────┐
  │ 搜索 │ │ 数据库│
  └──┬───┘ └──┬───┘
     ↓         ↓
     └────┬────┘
          ↓
     ┌──────┐
     │ 分析 │
     └──┬───┘
          ↓
     ┌──────┐
     │ 报告 │
     └──────┘

  适用场景: 有并行和依赖关系的复杂任务
  实现: LangGraph最擅长DAG编排
```

---

## 7. Spring AI Agent实战

### 7.1 基础Agent

```java
// Spring AI Function Calling Agent
@Configuration
public class AgentConfig {

    @Bean
    public ChatClient chatClient(ChatClient.Builder builder) {
        return builder
            .defaultSystem("你是一个智能助手，能够使用工具帮助用户解决问题")
            .build();
    }

    // 工具1: 天气查询
    @Bean
    @Description("查询指定城市的天气")
    public Function<WeatherRequest, WeatherResponse> getWeather() {
        return request -> {
            // 实际调用天气API
            String weather = weatherService.getWeather(request.city());
            return new WeatherResponse(weather);
        };
    }

    // 工具2: 计算
    @Bean
    @Description("执行数学计算")
    public Function<CalcRequest, CalcResponse> calculator() {
        return request -> {
            double result = evaluateExpression(request.expression());
            return new CalcResponse(result);
        };
    }

    // 工具3: 数据库查询
    @Bean
    @Description("查询数据库")
    public Function<QueryRequest, QueryResponse> queryDatabase() {
        return request -> {
            List<Map<String, Object>> rows = jdbcTemplate
                .queryForList(request.sql());
            return new QueryResponse(rows);
        };
    }
}

// 使用
@Service
public class AgentService {

    @Autowired
    private ChatClient chatClient;

    public String execute(String userMessage) {
        return chatClient.prompt()
            .user(userMessage)
            .functions("getWeather", "calculator", "queryDatabase")
            .call()
            .content();
    }
}
```

### 7.2 LangChain4j ReAct Agent

```java
// LangChain4j AI Services — 声明式Agent
interface SmartAssistant {

    @SystemMessage("""
        你是一个智能助手。你可以使用以下工具:
        - 搜索: 查询信息
        - 计算器: 数学计算
        - 天气: 查询天气
        请逐步思考，选择合适的工具完成任务。
        """)
    String chat(String userMessage);
}

// 工具定义
class AgentTools {

    @Tool("搜索网页获取信息")
    public String searchWeb(@P("搜索关键词") String query) {
        return webSearchService.search(query);
    }

    @Tool("执行数学计算")
    public double calculate(@P("数学表达式") String expression) {
        return calculator.evaluate(expression);
    }

    @Tool("查询城市天气")
    public String getWeather(@P("城市名") String city) {
        return weatherService.getWeather(city);
    }
}

// 构建Agent
SmartAssistant assistant = AiServices.builder(SmartAssistant.class)
    .chatLanguageModel(qwenModel)
    .tools(new AgentTools())
    .chatMemory(MessageWindowChatMemory.withMaxMessages(20))
    .build();

// 执行
String result = assistant.chat("北京和上海今天哪个温度高？");
// Agent内部自动ReAct:
//   Thought: 需要查询两个城市天气
//   Action: getWeather("北京") → 35°C
//   Action: getWeather("上海") → 30°C
//   Final: 北京35°C > 上海30°C，北京更高
```

### 7.3 Agent可观测性

```java
// Agent执行日志与追踪
@Service
public class ObservableAgent {

    private static final Logger log = LoggerFactory.getLogger(ObservableAgent.class);

    @Autowired
    private ChatClient chatClient;

    public AgentResponse execute(String userInput) {
        log.info("[Agent] 用户输入: {}", userInput);

        int maxSteps = 10;
        List<AgentStep> steps = new ArrayList<>();
        String currentInput = userInput;

        for (int i = 0; i < maxSteps; i++) {
            log.info("[Agent] Step {}: 开始推理", i + 1);
            long start = System.currentTimeMillis();

            // LLM推理
            String response = chatClient.prompt()
                .user(currentInput)
                .functions("getWeather", "calculator", "queryDatabase")
                .call()
                .content();

            long elapsed = System.currentTimeMillis() - start;
            log.info("[Agent] Step {} 完成, 耗时{}ms", i + 1, elapsed);

            // 记录步骤
            steps.add(new AgentStep(i + 1, currentInput, response, elapsed));

            // 判断是否完成
            if (isComplete(response)) {
                log.info("[Agent] 任务完成, 共{}步", i + 1);
                return new AgentResponse(response, steps);
            }

            // 更新下一轮输入
            currentInput = response;
        }

        log.warn("[Agent] 达到最大步数{}", maxSteps);
        return new AgentResponse("任务未能在限制步数内完成", steps);
    }
}
```

---

## 8. 面试题速查

**Q1: Agent和ChatBot的区别？**

```
ChatBot: 只能对话，被动回答，无状态，无法操作外部系统
Agent: 对话+行动，主动规划，有记忆，可调用工具
Agent = LLM(大脑) + 工具(手) + 记忆(脑) + 规划(思维)
```

**Q2: ReAct模式的流程？**

```
Thought→Action→Observation循环
Thought: LLM推理决定做什么
Action: 调用工具
Observation: 接收工具返回结果
循环直到Final Answer
优点: 简单可解释，缺点: 串行慢
```

**Q3: ReAct和Plan-Execute的区别？**

```
ReAct: 走一步看一步，每步LLM决策，灵活但可能走偏
Plan-Execute: 先全局规划再执行，全局视角但需Replan
选择: 简单任务ReAct，复杂任务Plan-Execute
```

**Q4: ReWOO如何减少LLM调用？**

```
ReAct每步一次LLM调用(N步=N次)
ReWOO: 1次Planner(生成全部计划)+并行执行+1次Solver(合并)
从N次降到约3次，成本低+速度快
```

**Q5: Agent有哪些设计模式？**

```
Router: 根据输入路由到子Agent(分类场景)
Chain: 串行处理(流水线场景)
DAG: 有向无环图(并行+依赖)
选择: 简单→ReAct，复杂→DAG，多专业→Router
```

**Q6: 如何防止Agent无限循环？**

```
1. 最大步数限制(max_iterations=10-20)
2. 超时机制(单步+总时间)
3. 重复检测(连续相同Action则终止)
4. 上下文窗口限制(超出则摘要压缩)
5. 用户中断机制
```

---

*最后更新: 2026-07-13*

# AI Agent框架全景对比

> AutoGen/CrewAI/MetaGPT/LangGraph/OpenAI Swarm，多语言Agent框架横向对比

---

## 📋 目录

1. [Agent框架概览](#1-agent框架概览)
2. [AutoGen（微软）](#2-autogen微软)
3. [CrewAI](#3-crewai)
4. [MetaGPT](#4-metagpt)
5. [LangGraph](#5-langgraph)
6. [OpenAI Swarm](#6-openai-swarm)
7. [Java Agent框架](#7-java-agent框架)
8. [对比与选型](#8-对比与选型)
9. [面试要点](#9-面试要点)

---

## 1. Agent框架概览

```
2024-2026年Agent框架爆发：

单Agent框架：
  LangChain Agent — 最早的Agent框架
  LangChain4j     — Java版
  Spring AI       — Spring生态

多Agent协作框架：
  AutoGen（微软）  — 对话式多Agent
  CrewAI          — 角色扮演多Agent
  MetaGPT         — 软件开发团队模拟
  LangGraph       — 图式Agent编排
  OpenAI Swarm    — 轻量级多Agent（OpenAI官方）

关键趋势：
  1. 从单Agent → 多Agent协作
  2. 从硬编码流程 → 动态编排
  3. 从Python → 多语言支持
  4. 从实验 → 生产部署
```

---

## 2. AutoGen（微软）

### 核心特点

```
对话式多Agent协作：
  Agent间通过消息对话完成任务
  支持代码执行（UserProxyAgent）
  支持群聊（GroupChat）

角色：
  AssistantAgent：AI助手，生成代码/方案
  UserProxyAgent：代理用户，执行代码/工具
  GroupChatManager：群聊管理器
```

### 适用场景

```
✅ 需要代码执行的开发任务
✅ 探索性任务（不确定步骤）
✅ 多轮迭代的优化任务
❌ 固定流程的任务（CrewAI更合适）
```

---

## 3. CrewAI

### 核心特点

```
角色+任务+流程：
  Agent：定义角色（Role/Goal/Backstory）
  Task：定义任务（描述/预期输出/依赖）
  Crew：编排流程（顺序/层级）

优势：
  - 角色定义清晰
  - 任务依赖明确
  - 流程可视化
  - 学习成本低
```

### 适用场景

```
✅ 内容创作（调研→写作→审核）
✅ 固定流程的多步骤任务
✅ 非技术人员可理解
❌ 需要代码执行（AutoGen更强）
```

---

## 4. MetaGPT

### 核心特点

```
MetaGPT = 模拟软件开发团队

角色：
  Product Manager → 产品经理
  Architect → 架构师
  Project Manager → 项目经理
  Engineer → 工程师
  QA Engineer → 测试工程师

输入一句话需求 → 输出完整软件项目
```

### 适用场景

```
✅ 快速生成软件原型
✅ 从需求到代码的全流程
✅ 学习软件工程流程
❌ 生产级代码（质量不够稳定）
```

---

## 5. LangGraph

### 核心特点

```
LangGraph = LangChain的图式Agent编排

核心概念：
  State：共享状态（所有节点可读写）
  Node：Agent/函数节点
  Edge：节点间连接（条件路由）
  Graph：有向图（DAG或含循环）

优势：
  - 精确控制流程（图结构）
  - 支持循环和条件分支
  - 状态管理清晰
  - 可视化流程图
```

### vs CrewAI

```
LangGraph：
  - 图式编排（更灵活）
  - 支持循环/条件/并行
  - 状态管理
  - 适合复杂流程

CrewAI：
  - 角色+任务（更直观）
  - 顺序/层级流程
  - 学习成本低
  - 适合简单流程
```

---

## 6. OpenAI Swarm

### 核心特点

```
Swarm = OpenAI官方轻量级多Agent框架

核心理念：
  Agent = Instructions + Tools
  Handoff：Agent间移交（简单路由）
  Context Variables：共享上下文

特点：
  - 极简（~500行代码）
  - 无状态（每次调用独立）
  - 教学性质（非生产框架）
  - 理解Agent协作原理
```

---

## 7. Java Agent框架

### LangChain4j Agent

```java
@AiService
public interface CodingAgent {
    
    @SystemMessage("你是Java开发专家")
    @UserMessage("{{task}}")
    String code(@V("task") String task);
}

// 配置Agent和工具
@Bean
public CodingAgent codingAgent(ChatLanguageModel model, 
        FileTools fileTools, GitTools gitTools) {
    return AiServices.builder(CodingAgent.class)
        .chatLanguageModel(model)
        .tools(fileTools, gitTools)
        .chatMemory(MessageWindowChatMemory.withMaxMessages(50))
        .build();
}
```

### Spring AI Agent

```java
// Spring AI + Function Calling
@Configuration
public class AgentConfig {
    
    @Bean
    @Description("查询数据库")
    public Function<QueryRequest, QueryResponse> queryDatabase() {
        return request -> dbService.query(request.getSql());
    }
    
    @Bean
    @Description("发送HTTP请求")
    public Function<HttpRequest, HttpResponse> httpRequest() {
        return request -> httpService.call(request);
    }
}

// 使用
String result = chatClient.prompt()
    .user("查询用户表的前10条数据")
    .functions("queryDatabase", "httpRequest")  // 自动选择工具
    .call()
    .content();
```

---

## 8. 对比与选型

| 框架 | 语言 | 多Agent | 复杂度 | 适用 |
|------|------|---------|--------|------|
| AutoGen | Python | ✅对话式 | 中 | 代码生成/探索 |
| CrewAI | Python | ✅角色式 | 低 | 内容创作/调研 |
| MetaGPT | Python | ✅团队模拟 | 中 | 软件原型 |
| LangGraph | Python | ✅图式 | 高 | 复杂流程 |
| Swarm | Python | ✅轻量 | 极低 | 学习/原型 |
| LangChain4j | Java | ❌单Agent | 中 | Java生态 |
| Spring AI | Java | ❌单Agent | 低 | Spring生态 |

### 选型建议

```
Java团队 → LangChain4j / Spring AI（单Agent + Function Calling）
Python快速原型 → CrewAI（简单）/ LangGraph（复杂）
需要代码执行 → AutoGen
软件开发模拟 → MetaGPT
学习Agent原理 → Swarm
生产级多Agent → LangGraph（可控性最强）
```

---

## 9. 面试要点

### Q1: 多Agent协作有哪些模式？

```
1. 对话式（AutoGen）：Agent间自由对话，灵活但不可控
2. 角色式（CrewAI）：角色+任务，流程清晰
3. 团队式（MetaGPT）：模拟组织架构，适合软件开发
4. 图式（LangGraph）：有向图编排，精确控制
5. 移交式（Swarm）：Agent间简单移交，轻量
```

### Q2: LangGraph和CrewAI的区别？

```
LangGraph：
  - 图式编排（Node+Edge）
  - 支持循环/条件/并行
  - 共享State管理
  - 适合复杂流程

CrewAI：
  - 角色+任务模式
  - 顺序/层级流程
  - 更易理解和配置
  - 适合简单流程

选择：简单→CrewAI，复杂→LangGraph
```

### Q3: Java怎么做多Agent？

```
Java生态目前以单Agent+Function Calling为主：

1. LangChain4j @AiService + @Tool
2. Spring AI + @Bean Function
3. 自定义ReAct循环（参考Agent设计模式文档）

多Agent协作（Java生态尚不成熟）：
  - 方案1：Java调用Python（AutoGen/CrewAI）通过API
  - 方案2：Java自定义多Agent编排（参考12_Agent设计模式.md）
  - 方案3：等待LangChain4j多Agent支持
```

---

## 10. LangGraph状态管理详解

> State是LangGraph的核心：所有节点共享、读写同一份状态，图的流转本质上是状态的演化。

### 10.1 State定义与Reducer

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import operator

# 方式1：消息列表（自动追加，不会覆盖）
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]   # reducer = 追加
    user_id: str

# 方式2：自定义reducer（累加/覆盖）
class ResearchState(TypedDict):
    messages: Annotated[list, add_messages]
    findings: Annotated[list[str], operator.add]  # 多节点结果累加
    summary: str                                    # 默认覆盖
    iteration: Annotated[int, operator.add]         # 计数累加
```

```
Reducer的作用：
  - 默认行为：后写覆盖前写（last-write-wins）
  - Annotated[T, reducer]：指定合并函数
  - add_messages：消息追加 + 同id更新（去重/编辑）
  - operator.add：列表拼接 / 数字累加
  - 自定义函数：def merge(old, new) -> new_state

为什么需要Reducer？
  - 多个节点并行写入同一字段时，需明确合并策略
  - 否则会出现数据覆盖、状态不一致
  - Reducer是LangGraph实现"可控并发"的关键
```

### 10.2 StateGraph构建与条件路由

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(ResearchState)

# 注册节点（每个节点接收state，返回state的更新部分）
graph.add_node("search", search_node)
graph.add_node("analyze", analyze_node)
graph.add_node("write", write_node)
graph.add_node("review", review_node)

# 固定边
graph.add_edge(START, "search")
graph.add_edge("search", "analyze")

# 条件边（根据state决定下一步）
def should_rewrite(state: ResearchState) -> str:
    if state["iteration"] >= 3:
        return "write"        # 达到迭代上限，进入写作
    if state.get("need_more_research"):
        return "search"       # 循环回search
    return "write"

graph.add_conditional_edges("analyze", should_rewrite)
graph.add_edge("write", "review")

# review → END 或 回到 write 修改
graph.add_conditional_edges("review", lambda s: "write" if s["need_revision"] else END)

app = graph.compile()
```

```
图结构能力：
  - DAG（有向无环）：线性/分支流程
  - 含循环：迭代优化、反思修正、ReAct循环
  - 并行扇出/扇入：多节点同时执行后合并（依赖Reducer）
  - 条件路由：add_conditional_edges 实现动态分支
```

### 10.3 持久化与Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.postgres import PostgresSaver  # 生产推荐

# 内存（开发/测试）
checkpointer = MemorySaver()

# SQLite（单机持久化）
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# 编译时注入
app = graph.compile(checkpointer=checkpointer)

# 通过thread_id隔离不同会话
config = {"configurable": {"thread_id": "user-123-session-1"}}
result = app.invoke(initial_state, config=config)

# 断点续跑：相同thread_id自动恢复上次状态
result = app.invoke(None, config=config)  # None = 从断点继续
```

```
Checkpointing的价值：
  1. 状态持久化：进程重启不丢失
  2. 断点续跑：长流程可分段执行
  3. Human-in-the-loop：暂停等待人工审批后继续
  4. 时间旅行：回退到任意历史checkpoint重新执行
  5. 多会话隔离：thread_id区分不同用户/会话

生产建议：
  - 开发用 MemorySaver
  - 单机用 SqliteSaver
  - 分布式用 PostgresSaver / RedisSaver
```

### 10.4 Human-in-the-loop（人机协同）

```python
# 方式1：interrupt_before（执行前暂停）
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["write"]   # 写作节点前暂停，等人工确认
)

# 执行到write前自动暂停
app.invoke(state, config=config)
# 人工审核/修改state后继续
app.invoke(None, config=config)

# 方式2：interrupt（动态中断，可传值）
from langgraph.types import interrupt, Command

def review_node(state):
    feedback = interrupt("请审核分析结果")  # 暂停，返回人工输入
    return {"feedback": feedback}

# 恢复时传入人工输入
app.invoke(Command(resume="通过，继续"), config=config)
```

---

## 11. CrewAI任务依赖机制

> CrewAI通过Task的context参数和Process类型实现任务编排与依赖。

### 11.1 任务间数据依赖

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(role="研究员", goal="收集资料", backstory="...", llm="gpt-4o")
writer = Agent(role="撰稿人", goal="写出文章", backstory="...", llm="gpt-4o")
editor = Agent(role="编辑", goal="审核润色", backstory="...", llm="gpt-4o")

# Task定义：context字段声明依赖（引用上游Task的输出）
research_task = Task(
    description="调研{topic}的核心观点",
    expected_output="调研报告（要点列表）",
    agent=researcher,
)

write_task = Task(
    description="基于调研报告写一篇800字文章",
    expected_output="文章初稿",
    agent=writer,
    context=[research_task],   # 依赖：自动注入research_task的输出
)

edit_task = Task(
    description="审核并润色文章",
    expected_output="最终文章",
    agent=editor,
    context=[write_task, research_task],  # 可依赖多个上游任务
)
```

```
context机制：
  - context=[task1, task2] 声明依赖
  - 执行时自动把上游Task的output注入到当前Task的提示中
  - 无需手动拼接，框架自动处理数据流
  - 支持依赖多个任务（多输入聚合）
```

### 11.2 Process：顺序 vs 层级

```python
# 顺序流程：按Task列表顺序执行，上游完成后下游开始
crew_sequential = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.sequential,   # 默认
)

# 层级流程：Manager Agent动态分配任务
crew_hierarchical = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.hierarchical,
    manager_llm="gpt-4o",         # 管理者Agent自动创建
    # manager_agent=custom_manager,  # 或自定义Manager
)
```

```
两种流程对比：

sequential（顺序）：
  - 按tasks数组顺序执行
  - 依赖靠context显式声明
  - 流程确定、可预测
  - 适合标准化流水线

hierarchical（层级）：
  - Manager Agent接管编排
  - Manager决定调用哪个Agent、调用几次
  - 可动态重试、跳过、循环
  - 适合开放性、探索性任务
  - 成本更高（Manager多轮决策）
```

### 11.3 异步任务与回调

```python
# async_execution=True：任务异步执行，不阻塞后续
parallel_task = Task(
    description="并行收集多个数据源",
    expected_output="数据汇总",
    agent=researcher,
    async_execution=True,   # 异步，下游需等待其完成
)

# callback：任务完成后回调
def on_complete(output):
    print(f"任务完成: {output.raw}")

task = Task(
    description="...",
    agent=writer,
    callback=on_complete,
)
```

```
异步任务注意：
  - async_execution=True 的任务会"提前触发"
  - 下游任务（依赖它的）会等待其完成
  - 适合并行扇出（多个独立子任务同时跑）
  - 最终Crew.result()会同步等待所有任务完成
```

---

## 12. Java多Agent实现方案

> Java生态原生多Agent框架尚不成熟，以下是4种工程化落地方案。

### 12.1 方案一：Java编排 + Python执行（混合架构）

```
架构：Java Spring Boot（业务层）  ──HTTP/gRPC──>  Python FastAPI（Agent层）

Java侧：                         Python侧：
  - 用户鉴权/限流                  - AutoGen/CrewAI/LangGraph
  - 业务逻辑编排                    - Agent协作执行
  - 结果持久化                      - 返回结构化结果
  - 监控/告警                       - 模型调用
```

```java
// Java侧：调用Python Agent服务
@Service
public class AgentOrchestratorClient {

    private final WebClient webClient;

    public AgentResult executeResearch(String topic) {
        AgentRequest request = AgentRequest.builder()
            .task("research")
            .input(Map.of("topic", topic))
            .build();

        return webClient.post()
            .uri("http://agent-service:8000/crew/run")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(AgentResult.class)
            .block();
    }
}
```

```
优点：复用Python成熟生态，Java专注业务
缺点：双语言维护、跨进程通信开销、部署复杂
适用：Java团队但需复杂多Agent能力
```

### 12.2 方案二：纯Java自定义编排器（Orchestrator模式）

```java
// Agent接口
public interface Agent {
    String getName();
    AgentResponse execute(AgentContext context);
}

// 编排器：管理多Agent协作
public class MultiAgentOrchestrator {

    private final Map<String, Agent> agents;
    private final ChatLanguageModel routerModel;

    public OrchestratorResult execute(String task, String workflow) {
        AgentContext context = new AgentContext(task);

        switch (workflow) {
            case "sequential" -> runSequential(context, List.of("researcher", "writer", "editor"));
            case "hierarchical" -> runHierarchical(context);
            case "react" -> runReActLoop(context);
        }
        return OrchestratorResult.from(context);
    }

    // 顺序流程
    private void runSequential(AgentContext ctx, List<String> agentNames) {
        for (String name : agentNames) {
            AgentResponse resp = agents.get(name).execute(ctx);
            ctx.addResult(name, resp);   // 结果累积到共享上下文
            ctx.appendToHistory(resp);   // 传递给下游
        }
    }

    // ReAct循环（反思-行动）
    private void runReActLoop(AgentContext ctx) {
        for (int i = 0; i < ctx.getMaxIterations(); i++) {
            String next = routerModel.generate(
                "根据当前状态决定下一步动作: " + ctx.getHistory());
            if (next.equals("FINISH")) break;
            AgentResponse resp = agents.get(next).execute(ctx);
            ctx.appendToHistory(resp);
        }
    }
}
```

```
优点：纯Java、可控性强、易集成Spring生态
缺点：需自研状态管理/容错/并行，工作量大
适用：流程相对固定、对可控性要求高的场景
```

### 12.3 方案三：LangChain4j多Agent路由

```java
// 用LangChain4j实现Agent路由（轻量多Agent）
public class RoutingAgent {

    private final ChatLanguageModel model;
    private final ResearchAgent researchAgent;
    private final CodeAgent codeAgent;
    private final SummaryAgent summaryAgent;

    public String handle(String userInput) {
        // 1. 路由：判断交给哪个Agent
        String route = model.generate("""
            根据用户输入选择Agent，只回复名称：
            - research: 调研类问题
            - code: 编程类问题
            - summary: 总结类问题
            输入: %s
            """.formatted(userInput));

        // 2. 分发执行
        return switch (route.trim()) {
            case "research" -> researchAgent.handle(userInput);
            case "code" -> codeAgent.handle(userInput);
            case "summary" -> summaryAgent.handle(userInput);
            default -> model.generate(userInput);
        };
    }
}

// 每个Agent用@AiService + @Tool定义
@AiService
public interface ResearchAgent {
    @SystemMessage("你是研究员，使用工具检索信息")
    String handle(@V("input") String input);
}
```

### 12.4 方案四：Spring AI + 多ChatClient

```java
@Configuration
public class MultiAgentConfig {

    @Bean("plannerAgent")
    public ChatClient plannerAgent(ChatClient.Builder builder) {
        return builder
            .defaultSystem("你是任务规划Agent，拆解用户需求为子任务，输出JSON数组")
            .build();
    }

    @Bean("executorAgent")
    public ChatClient executorAgent(ChatClient.Builder builder, ToolCallback[] tools) {
        return builder
            .defaultSystem("你是执行Agent，使用工具完成子任务")
            .defaultTools(tools)
            .build();
    }

    @Bean("reviewerAgent")
    public ChatClient reviewerAgent(ChatClient.Builder builder) {
        return builder
            .defaultSystem("你是审核Agent，检查结果质量，返回PASS或修改意见")
            .build();
    }
}

@Service
public class PlanExecuteReviewFlow {

    public String run(String userRequest) {
        // Plan
        String plan = plannerAgent.prompt().user(userRequest).call().content();
        List<String> subtasks = parsePlan(plan);

        // Execute（每个子任务交给executor）
        List<String> results = subtasks.stream()
            .map(t -> executorAgent.prompt().user(t).call().content())
            .toList();

        // Review
        String review = reviewerAgent.prompt()
            .user("审核结果: " + results).call().content();

        return review.contains("PASS") ? join(results) : run(userRequest);
    }
}
```

```
方案对比：
  方案一（混合）：功能最强，维护成本高，适合复杂场景
  方案二（自研）：可控性最强，工作量大，适合固定流程
  方案三（路由）：最简单，本质是单Agent路由，适合分类场景
  方案四（多Client）：Spring原生，Plan-Execute-Review模式，推荐起步方案
```

---

## 13. 生产部署建议

### 13.1 模型层

```
1. 模型路由：
   - 简单任务用小模型（GPT-4o-mini / Claude Haiku）降本
   - 复杂推理用大模型（GPT-4o / Claude Sonnet）
   - 路由器模型判断复杂度后分发

2. 降级策略：
   - 主模型超时/限流 → 自动切换备用模型
   - 多供应商配置（OpenAI / Anthropic / 本地模型）

3. 响应缓存：
   - 相同输入命中缓存，避免重复调用
   - 语义缓存（embedding相似度匹配）

4. 流式输出：
   - 用户端流式返回，降低首Token延迟感知
```

### 13.2 状态与容错

```
1. 状态持久化：
   - LangGraph用PostgresSaver，不要用MemorySaver
   - 自研方案：每步执行后持久化AgentContext到DB
   - 支持断点续跑（长流程必备）

2. 容错机制：
   - 模型调用：指数退避重试（3次）
   - 工具调用：超时 + 降级返回
   - Agent循环：max_iterations硬上限，防止死循环
   - 熔断：错误率超阈值时短路，返回兜底响应

3. 幂等性：
   - 每次执行带request_id，重复请求不重复扣费/执行
   - checkpoint支持幂等恢复
```

### 13.3 可观测性

```
1. Tracing（链路追踪）：
   - LangSmith / Langfuse / Arize Phoenix
   - 记录每步：输入/输出/Token/延迟/模型
   - 一次完整Agent执行的完整调用链

2. Logging：
   - 结构化日志（JSON），含trace_id
   - 记录：Agent决策、工具调用、状态变更

3. Metrics：
   - 执行成功率、平均步数、平均Token、平均延迟
   - 按Agent/Task/Workflow维度统计
   - 成本监控（每日Token消耗/费用）

4. 告警：
   - 失败率突增、延迟突增、成本异常
```

### 13.4 安全与成本

```
安全：
  1. 代码执行沙箱：UserProxyAgent/AutoGen的代码执行用Docker/沙箱隔离
  2. 工具权限：Agent只能调用授权工具，敏感操作需人工确认（HITL）
  3. 输入过滤：防Prompt注入、敏感信息脱敏
  4. 输出审核：有害内容过滤

成本控制：
  1. Token预算：单次执行/每日上限，超限拒绝或降级
  2. 上下文裁剪：长对话用摘要压缩历史，避免Token爆炸
  3. 模型分级：路由到合适模型，避免大材小用
  4. 缓存复用：相同/相似请求命中缓存
```

### 13.5 扩展性

```
1. 无状态部署：
   - Agent执行逻辑无状态，状态全部存DB（checkpointer）
   - 水平扩展：多实例无状态，负载均衡分发

2. 异步执行：
   - 长任务异步化（消息队列），避免HTTP超时
   - 用户提交任务 → 返回task_id → 轮询/WebSocket获取结果

3. 资源隔离：
   - 代码执行型Agent单独部署（资源消耗大）
   - 按租户/优先级隔离资源池
```

---

## 9. 面试要点（补充）

### Q4: LangGraph的State如何管理？Reducer是什么？

```
State管理：
  - State是所有节点共享的TypedDict，节点读取并返回更新
  - 默认"后写覆盖"，通过Annotated[T, reducer]指定合并策略

Reducer：
  - 合并函数，解决多节点并发写入同一字段的冲突
  - 内置：add_messages（消息追加+去重）、operator.add（累加/拼接）
  - 自定义：def reducer(old, new) -> merged

举例：
  findings: Annotated[list, operator.add]
  → 多个检索节点并行写入，结果自动拼接而非覆盖

价值：实现可控的并行扇出/扇入，是复杂图编排的基础。
```

### Q5: 多Agent系统如何做状态持久化和容错？

```
状态持久化：
  1. LangGraph：Checkpointer（Memory/Sqlite/Postgres），按thread_id隔离
  2. 自研：每步执行后将AgentContext序列化存DB，支持断点续跑
  3. 关键：状态序列化要完整（含中间结果、历史、迭代次数）

容错：
  1. 模型层：重试（指数退避）+ 多供应商降级
  2. 工具层：超时 + 降级返回 + 重试
  3. Agent层：max_iterations防死循环 + 熔断器
  4. 幂等性：request_id去重，恢复时从checkpoint继续
```

### Q6: CrewAI的任务依赖如何实现？顺序和层级流程的区别？

```
任务依赖：
  - Task的context=[task1, task2]参数声明依赖
  - 框架自动将上游Task的output注入下游Task的提示
  - 支持依赖多个上游任务（多输入聚合）

顺序流程（sequential）：
  - 按tasks数组顺序执行
  - 依赖靠context显式声明
  - 流程确定、可预测，适合标准化流水线

层级流程（hierarchical）：
  - Manager Agent接管编排，动态决定调用谁、调几次
  - 可重试/跳过/循环，适合开放性任务
  - 成本更高（Manager多轮决策）

选择：标准化流程→sequential，探索性任务→hierarchical。
```

### Q7: 生产环境部署Agent系统有哪些关键点？

```
1. 模型层：路由（大小模型分级）、降级（多供应商）、缓存、流式
2. 状态持久化：checkpointer存DB，支持断点续跑
3. 容错：重试+超时+熔断+max_iterations防死循环
4. 可观测性：Tracing（LangSmith/Langfuse）+ 结构化日志 + Metrics
5. 安全：代码执行沙箱、工具权限、HITL敏感确认、Prompt注入防护
6. 成本：Token预算、上下文裁剪、模型分级、缓存复用
7. 扩展性：无状态部署水平扩展、长任务异步化、资源隔离
```

### Q8: Agent系统的成本和延迟如何优化？

```
成本优化：
  1. 模型分级路由：简单任务用小模型，复杂推理用大模型
  2. 上下文裁剪：长历史用摘要压缩，避免Token线性增长
  3. 响应缓存：精确缓存 + 语义缓存（embedding相似匹配）
  4. Token预算：单次/每日上限，超限降级或拒绝
  5. 减少迭代：优化prompt减少Agent循环次数

延迟优化：
  1. 流式输出：首Token快速返回，改善感知延迟
  2. 并行扇出：独立子任务并行执行（CrewAI async / LangGraph并行节点）
  3. 模型选择：延迟敏感场景用小模型/本地模型
  4. 预计算：可预知的子任务提前执行并缓存
  5. 减少工具往返：合并工具调用，一次获取更多信息
```

---

## 📚 相关阅读

### 项目内文档

- [12_Agent设计模式](./12_Agent设计模式.md)
- [14_Agent记忆与上下文管理](./14_Agent记忆与上下文管理.md)
- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [06_Spring AI详解](./06_Spring AI详解.md)
- [16_Python AI生态全景](./16_Python AI生态全景.md)

### 官方文档

- LangGraph：https://langchain-ai.github.io/langgraph/
- CrewAI：https://docs.crewai.com/
- AutoGen：https://microsoft.github.io/autogen/
- MetaGPT：https://docs.deepwisdom.ai/main/en/
- OpenAI Swarm（已归档）：https://github.com/openai/swarm
- OpenAI Agents SDK（Swarm继任者）：https://github.com/openai/openai-agents-python
- LangChain4j：https://docs.langchain4j.dev
- Spring AI：https://docs.spring.io/spring-ai/reference/

### 进阶阅读

- LangGraph持久化与HITL：https://langchain-ai.github.io/langgraph/concepts/persistence/
- CrewAI流程机制：https://docs.crewai.com/concepts/crews
- "The Rise of Multi-Agent Systems" — LangChain博客
- 多Agent系统设计模式（Reflection / Tool Use / Planning / Multi-Agent）

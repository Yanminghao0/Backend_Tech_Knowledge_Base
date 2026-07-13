# 多Agent系统设计

> LangGraph、AutoGen、CrewAI多Agent协作框架与架构模式

---

## 📋 目录

1. [多Agent概述](#1-多agent概述)
2. [协作模式](#2-协作模式)
3. [LangGraph实战](#3-langgraph实战)
4. [AutoGen实战](#4-autogen实战)
5. [CrewAI实战](#5-crewai实战)
6. [多Agent架构设计](#6-多agent架构设计)
7. [面试题速查](#7-面试题速查)

---

## 1. 多Agent概述

### 1.1 为什么需要多Agent

```
单Agent的局限:
  1. 角色单一 — 一个Agent难以同时擅长写作+编程+分析
  2. 上下文限制 — 多任务在一个上下文中容易干扰
  3. 并行能力 — 单Agent只能串行处理
  4. 可靠性 — 一个错误影响全部

多Agent的优势:
  1. 专业分工 — 每个Agent专注一个领域
  2. 并行执行 — 无依赖的Agent可并行
  3. 交叉验证 — Agent互相审查，降低错误
  4. 模块化 — 单个Agent可独立优化/替换

  典型场景:
    软件开发 — PM+架构师+开发+测试+运维
    内容创作 — 研究员+写手+编辑+校对
    数据分析 — 数据提取+清洗+分析+可视化+报告
    投资研究 — 行业分析+财报分析+风险评估+报告
```

---

## 2. 协作模式

### 2.1 层级式

```
层级式(Hierarchical) — 上下级关系

  ┌──────────┐
  │  管理者   │ ← 接收任务，分配给下属
  │ Manager  │
  └────┬─────┘
       ↓ 分配任务
  ┌────┴────────────┐
  ↓       ↓       ↓
┌────┐ ┌────┐ ┌────┐
│研究 │ │写作 │ │审校 │ ← 各自执行
│Agent│ │Agent│ │Agent│
└──┬─┘ └──┬─┘ └──┬─┘
   └──────┼──────┘
          ↓ 汇报结果
   ┌──────┴──────┐
   │   管理者     │ ← 整合结果，决定下一步
   └─────────────┘

  特点:
    管理者负责决策和协调
    下属Agent执行具体任务
    管理者可以多次分配任务(迭代)
  实现: LangGraph/CrewAI Hierarchical
```

### 2.2 平等式

```
平等式(Collaborative) — 对话讨论

  ┌──────┐   ┌──────┐   ┌──────┐
  │Agent A│←→│Agent B│←→│Agent C│
  └──────┘   └──────┘   └──────┘
    ↕            ↕          ↕
       ← 互相讨论 →
            ↓
       共识结果

  特点:
    所有Agent平等，通过对话达成共识
    适合需要多视角讨论的问题
    可能产生分歧(需要仲裁机制)
  实现: AutoGen Group Chat
```

### 2.3 竞争式

```
竞争式(Competitive) — 辩论

  ┌──────────┐          ┌──────────┐
  │ Agent A   │ ←辩论→  │ Agent B   │
  │ 正方观点  │          │ 反方观点  │
  └─────┬────┘          └─────┬────┘
        ↓                      ↓
        └────────┬────────────┘
                 ↓
           ┌──────────┐
           │  裁判     │ ← 选出更好方案
           │ Judge    │
           └──────────┘

  特点:
    多个Agent提出不同方案
    裁判Agent或LLM选出最优
    适合需要择优的场景
```

---

## 3. LangGraph实战

### 3.1 LangGraph概述

```
LangGraph — LangChain团队的有状态多Agent编排框架

  核心概念:
    1. State — 共享状态(所有Agent读写)
    2. Node — 节点(每个Agent是一个节点)
    3. Edge — 边(节点间的连接)
    4. Conditional Edge — 条件边(根据状态动态路由)
    5. Checkpoint — 检查点(持久化+中断恢复)

  ┌──────────────────────────────────────────┐
  │  LangGraph vs LangChain Agent:           │
  │  LangChain Agent — ReAct循环(简单)        │
  │  LangGraph — 状态图(灵活、可编排多Agent)   │
  │                                          │
  │  LangGraph能做的事:                       │
  │  ✓ 多Agent协作                            │
  │  ✓ 条件路由                               │
  │  ✓ 并行执行                               │
  │  ✓ 人机协作(Human-in-loop)               │
  │  ✓ 中断+恢复                              │
  │  ✓ 持久化状态                             │
  │  ✓ 流式输出                               │
  └──────────────────────────────────────────┘
```

### 3.2 代码实现

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator

# 1. 定义共享状态
class AgentState(TypedDict):
    task: str                    # 原始任务
    research_result: str         # 研究结果
    draft: str                   # 初稿
    review_feedback: str         # 审校反馈
    final_report: str            # 最终报告
    messages: Annotated[List[str], operator.add]  # 消息历史

# 2. 定义Agent节点
def researcher_agent(state: AgentState):
    """研究员Agent — 搜索资料"""
    task = state["task"]
    result = llm.invoke(f"作为研究员，请搜索以下主题的信息: {task}")
    return {"research_result": result, "messages": [f"Researcher: {result[:100]}..."]}

def writer_agent(state: AgentState):
    """写手Agent — 基于研究结果撰写初稿"""
    research = state["research_result"]
    task = state["task"]
    draft = llm.invoke(f"基于以下信息撰写文章: {task}\n资料: {research}")
    return {"draft": draft, "messages": [f"Writer: 初稿完成"]}

def reviewer_agent(state: AgentState):
    """审校Agent — 审查并给出反馈"""
    draft = state["draft"]
    feedback = llm.invoke(f"请审查以下文章的质量: {draft}")
    return {"review_feedback": feedback, "messages": [f"Reviewer: {feedback[:100]}..."]}

def should_revise(state: AgentState):
    """条件路由: 根据审校反馈决定"""
    feedback = state["review_feedback"]
    if "需要修改" in feedback or "问题" in feedback:
        return "writer"  # 回到写手修改
    return "finalize"    # 审校通过，完成

def finalize_agent(state: AgentState):
    """完成Agent — 整合最终报告"""
    return {"final_report": state["draft"]}

# 3. 构建图
graph = StateGraph(AgentState)

# 添加节点
graph.add_node("researcher", researcher_agent)
graph.add_node("writer", writer_agent)
graph.add_node("reviewer", reviewer_agent)
graph.add_node("finalize", finalize_agent)

# 设置入口
graph.set_entry_point("researcher")

# 添加边(线性)
graph.add_edge("researcher", "writer")
graph.add_edge("writer", "reviewer")

# 条件边: 审校后决定下一步
graph.add_conditional_edges(
    "reviewer",
    should_revise,
    {"writer": "writer", "finalize": "finalize"}
)

# finalize → 结束
graph.add_edge("finalize", END)

# 4. 编译并运行
app = graph.compile()
result = app.invoke({"task": "写一份AI Agent技术趋势报告"})
print(result["final_report"])
```

---

## 4. AutoGen实战

```python
import autogen

# 1. 配置LLM
config_list = [{
    "model": "qwen-plus",
    "api_key": "your-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}]

# 2. 创建Agent
# 助手Agent
researcher = autogen.AssistantAgent(
    name="Researcher",
    system_message="你是一个研究助手，擅长搜索和分析信息。提供准确的事实和数据分析。",
    llm_config={"config_list": config_list},
)

# 写手Agent
writer = autogen.AssistantAgent(
    name="Writer",
    system_message="你是一个专业写手，擅长将研究结果转化为易读的文章。",
    llm_config={"config_list": config_list},
)

# 用户代理(执行代码/搜索)
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",  # 不需要人工输入
    max_consecutive_auto_reply=5,
    code_execution_config={"work_dir": "coding"},
)

# 3. Group Chat(群聊模式)
groupchat = autogen.GroupChat(
    agents=[user_proxy, researcher, writer],
    messages=[],
    max_round=10,
)
manager = autogen.GroupChatManager(groupchat=groupchat,
    llm_config={"config_list": config_list})

# 4. 执行
user_proxy.initiate_chat(
    manager,
    message="请研究AI Agent的发展趋势，然后写一篇500字的文章"
)
```

---

## 5. CrewAI实战

```python
from crewai import Agent, Task, Crew, Process

# 1. 定义Agent(角色)
researcher = Agent(
    role='资深研究员',
    goal='搜索并整理AI Agent最新技术趋势',
    backstory='你是一个有10年经验的AI研究员，擅长从海量信息中提炼关键洞察。',
    tools=[search_tool, web_scraper],
    verbose=True,
    llm=qwen_llm
)

writer = Agent(
    role='技术写手',
    goal='将研究结果转化为清晰易读的技术报告',
    backstory='你是一个资深技术博客作者，擅长将复杂技术概念用简洁语言表达。',
    verbose=True,
    llm=qwen_llm
)

editor = Agent(
    role='主编',
    goal='确保报告的质量、准确性和可读性',
    backstory='你是一个严谨的技术编辑，对内容质量有极高要求。',
    verbose=True,
    llm=qwen_llm
)

# 2. 定义任务
research_task = Task(
    description='搜索2026年AI Agent领域的重大技术进展，包括多Agent系统、RAG优化、工具调用等方向。',
    agent=researcher,
    expected_output='一份包含5-10个关键技术点的调研报告'
)

writing_task = Task(
    description='基于调研报告，撰写一篇面向开发者的技术趋势文章，要求有代码示例。',
    agent=writer,
    expected_output='一篇2000字左右的技术文章',
    context=[research_task]  # 依赖研究任务的输出
)

editing_task = Task(
    description='审校文章的技术准确性、逻辑清晰度和语言流畅度，给出修改建议或终稿。',
    agent=editor,
    expected_output='审校后的最终文章',
    context=[writing_task]
)

# 3. 组建Crew并执行
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential,  # 顺序执行
    verbose=True
)

result = crew.kickoff()
print(result)
```

---

## 6. 多Agent架构设计

### 6.1 框架选型

```
┌──────────────────────────────────────────────────────────┐
│  框架        │  特点               │  适用                │
│  ──────    │  ──────          │  ────              │
│  LangGraph  │  状态图/灵活/可控    │  复杂流程(推荐)      │
│  AutoGen    │  对话式/简单         │  对话型协作          │
│  CrewAI     │  角色扮演/易用       │  流程型任务          │
│  MetaGPT    │  软件公司模拟        │  软件开发场景        │
│  自建       │  完全可控            │  特殊需求            │
└──────────────────────────────────────────────────────────┘

  选型建议:
    需要精细控制 → LangGraph(状态图+条件路由)
    快速原型 → CrewAI(角色+任务最简单)
    对话型讨论 → AutoGen(Group Chat)
    Java生态 → Spring AI自建多Agent
```

### 6.2 通信设计

```
多Agent通信方式:

  1. 共享状态(LangGraph)
     所有Agent读写同一个State对象
     优点: 简单直接
     缺点: 状态可能太大

  2. 消息传递(AutoGen)
     Agent间直接发消息
     优点: 解耦
     缺点: 消息可能爆炸

  3. 黑板模式
     共享"黑板"，Agent读写
     优点: 灵活
     缺点: 需要协调机制

  4. 事件驱动
     Agent发布事件，其他订阅
     优点: 松耦合
     缺点: 调试难
```

---

## 7. 面试题速查

**Q1: 多Agent系统的协作模式有哪些？**

```
层级式: 管理者分配任务给下属(自上而下)
平等式: Agent间对话讨论(平等交流)
竞争式: 多方案辩论择优(辩论+裁判)
选择: 流程明确→层级, 需要讨论→平等, 需要择优→竞争
```

**Q2: LangGraph的核心概念？**

```
State: 共享状态(所有Agent读写)
Node: 节点(每个Agent是一个节点)
Edge: 边(节点间连接)
Conditional Edge: 条件边(动态路由)
Checkpoint: 检查点(持久化+中断恢复)
比LangChain Agent更灵活，适合复杂多Agent编排
```

**Q3: CrewAI和AutoGen的区别？**

```
CrewAI: 角色扮演(Role/Goal/Backstory)+任务驱动+顺序/层级
AutoGen: 对话式(Group Chat)+代码执行+更灵活
CrewAI适合流程型任务(研究→写作→审校)
AutoGen适合需要讨论和代码执行的场景
```

**Q4: 多Agent如何处理冲突？**

```
1. 仲裁Agent — 专门的裁判Agent做决定
2. LLM裁判 — 用更强的LLM评估并选择
3. 投票 — 多数决
4. 优先级 — 按Agent优先级决定
5. 人工介入 — Human-in-loop
```

---

*最后更新: 2026-07-13*

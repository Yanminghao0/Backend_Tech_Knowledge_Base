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

## 📚 相关阅读

- [12_Agent设计模式](./12_Agent设计模式.md)
- [14_Agent记忆与上下文管理](./14_Agent记忆与上下文管理.md)
- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [06_Spring AI详解](./06_Spring AI详解.md)
- [16_Python AI生态全景](./16_Python AI生态全景.md)

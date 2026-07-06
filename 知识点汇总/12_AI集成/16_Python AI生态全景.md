# Python AI生态全景

> LangChain/LlamaIndex/AutoGen/CrewAI/DSPy，Python AI框架横向对比

---

## 📋 目录

1. [Python AI生态概览](#1-python-ai生态概览)
2. [LangChain](#2-langchain)
3. [LlamaIndex](#3-llamaindex)
4. [AutoGen](#4-autogen)
5. [CrewAI](#5-crewai)
6. [DSPy](#6-dspy)
7. [框架对比与选型](#7-框架对比与选型)
8. [面试要点](#8-面试要点)

---

## 1. Python AI生态概览

```
Python是AI开发的第一语言，生态最丰富：

应用开发层：
  LangChain     — 通用LLM应用框架（最流行）
  LlamaIndex    — RAG专用框架（数据连接最强）
  Haystack      — 企业级搜索+QA管道

Agent层：
  AutoGen       — 微软出品，多Agent对话
  CrewAI        — 角色扮演多Agent协作
  LangGraph     — LangChain的Agent图引擎
  MetaGPT       — 多Agent软件开发团队

优化层：
  DSPy          — 编程式Prompt优化（不写Prompt写代码）
  Guidance      — 微软出品，结构化LLM输出

评估层：
  Ragas         — RAG评估框架
  DeepEval      — LLM单元测试
  Promptfoo     — Prompt对比测试
```

---

## 2. LangChain

### 核心概念

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 链式调用
prompt = ChatPromptTemplate.fromTemplate("翻译以下文本为英文：{text}")
model = ChatOpenAI(model="gpt-5")
parser = StrOutputParser()

chain = prompt | model | parser
result = chain.invoke({"text": "你好世界"})
# "Hello World"

# LCEL（LangChain Expression Language）
# 所有组件通过 | 连接，支持流式/批量/异步
```

### 核心组件

```
Models: LLM/ChatModel/Embedding
Prompts: Template/Few-shot/动态选择
Chains: LCEL管道（prompt|model|parser）
Memory: 对话记忆（Buffer/Summary/Vector）
Retrievers: 向量检索/关键词/多路召回
Agents: ReAct/OpenAI Functions/自定义
Tools: 搜索/计算/数据库/API
```

### 适用场景

```
✅ 通用LLM应用开发
✅ 快速原型验证
✅ 需要丰富生态集成（500+工具）
❌ 性能要求极高（Python GIL限制）
❌ Java团队（用LangChain4j替代）
```

---

## 3. LlamaIndex

### 核心定位

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# LlamaIndex专注于数据连接+RAG

# 1. 加载文档
documents = SimpleDirectoryReader("./data").load_data()

# 2. 构建索引
index = VectorStoreIndex.from_documents(documents)

# 3. 查询
query_engine = index.as_query_engine()
response = query_engine.query("什么是Spring Boot?")
print(response)
# "Spring Boot是Spring家族的框架..."

# 4. 高级：Chat Engine（对话模式）
chat_engine = index.as_chat_engine()
response = chat_engine.chat("告诉我更多")
```

### vs LangChain

```
LlamaIndex优势：
  - RAG流程更简洁（3行代码完成）
  - 数据连接器丰富（Notion/Confluence/Google Drive等）
  - 高级检索：子问题/递归/树形/关键词+向量
  - 内置评估

LangChain优势：
  - 通用性更强（不只是RAG）
  - Agent生态更丰富
  - 社区更大
  - 工具集成更多
```

---

## 4. AutoGen

### 多Agent对话

```python
import autogen

# AutoGen：多Agent协作框架

# 创建Agent
assistant = autogen.AssistantAgent(
    name="coder",
    llm_config={"model": "gpt-5"},
    system_message="你是一个Python开发者，负责写代码"
)

user_proxy = autogen.UserProxyAgent(
    name="user",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "coding"}
)

# Agent间对话
user_proxy.initiate_chat(
    assistant,
    message="写一个Web爬虫，爬取豆瓣电影Top250"
)
# coder写代码 → user_proxy执行 → 发现问题 → coder修复 → 循环
```

### 多Agent团队

```python
# 多角色协作
coder = autogen.AssistantAgent(name="coder", system_message="写代码")
reviewer = autogen.AssistantAgent(name="reviewer", system_message="代码审查")
tester = autogen.AssistantAgent(name="tester", system_message="写测试")

groupchat = autogen.GroupChat(
    agents=[user_proxy, coder, reviewer, tester],
    messages=[],
    max_round=20
)

manager = autogen.GroupChatManager(groupchat=groupchat)
user_proxy.initiate_chat(manager, message="开发一个用户注册API")
# coder写代码 → reviewer审查 → tester测试 → 循环改进
```

---

## 5. CrewAI

### 角色扮演Agent

```python
from crewai import Agent, Task, Crew

# CrewAI：定义角色、任务、流程

researcher = Agent(
    role='技术研究员',
    goal='研究最新的AI Agent技术',
    backstory='你是资深技术研究员，擅长技术调研',
    tools=[search_tool, web_scraper],
    llm='gpt-5'
)

writer = Agent(
    role='技术作家',
    goal='将研究结果写成技术报告',
    backstory='你是技术博客作家，擅长深入浅出',
    llm='claude-4-sonnet'
)

research_task = Task(
    description='调研2026年最热门的AI Agent框架',
    agent=researcher,
    expected_output='调研报告'
)

write_task = Task(
    description='将调研报告写成技术博客',
    agent=writer,
    expected_output='技术博客文章',
    context=[research_task]  # 依赖研究任务结果
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential  # 顺序执行
)

result = crew.kickoff()
```

### vs AutoGen

```
CrewAI：
  - 角色定义清晰（Role/Goal/Backstory）
  - 任务依赖明确（context参数）
  - 适合固定流程的协作
  - 更易用

AutoGen：
  - 对话式协作（更灵活）
  - 支持代码执行
  - 适合探索性任务
  - 更灵活但配置复杂
```

---

## 6. DSPy

### 编程式Prompt优化

```python
import dspy

# DSPy：不手写Prompt，用代码定义+自动优化

# 1. 定义签名（输入输出规范）
class QA(dspy.Signature):
    """回答问题"""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="简洁准确的回答")

# 2. 定义模块（Prompt逻辑）
class RAG(dspy.Module):
    def __init__(self):
        self.retrieve = dspy.Retrieve(k=3)
        self.generate = dspy.ChainOfThought("context, question -> answer")
    
    def forward(self, question):
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question)

# 3. 自动优化（不需要手写Prompt）
trainset = [...]  # 训练数据
rag = RAG()
optimized = dspy.BootstrapFewShot.optimize(rag, trainset=trainset)

# DSPy自动选择最佳Few-shot示例和Prompt措辞
result = optimized(question="什么是RAG?")
```

### DSPy核心理念

```
传统Prompt工程：手动调试Prompt措辞（像调参）
DSPy：用代码定义IO规范，自动优化Prompt（像训练模型）

优势：
  - 不需要手动写Prompt
  - 可量化评估优化效果
  - 换模型时自动重新优化
  - 版本管理（Prompt即代码）
```

---

## 7. 框架对比与选型

| 框架 | 定位 | 语言 | 学习成本 | 适用场景 |
|------|------|------|---------|---------|
| LangChain | 通用LLM应用 | Python/JS | 中 | 通用LLM应用 |
| LlamaIndex | RAG专用 | Python | 低 | 知识库/RAG |
| AutoGen | 多Agent协作 | Python | 中 | 代码生成/软件开发 |
| CrewAI | 角色协作 | Python | 低 | 内容创作/调研 |
| DSPy | Prompt优化 | Python | 高 | Prompt自动优化 |
| Haystack | 企业搜索 | Python | 中 | 企业搜索/QA |
| LangChain4j | Java版LangChain | Java | 中 | Java生态LLM |

### 选型建议

```
Java团队 → LangChain4j + Spring AI
Python快速原型 → LangChain
RAG知识库 → LlamaIndex
多Agent协作 → CrewAI（简单）/ AutoGen（灵活）
Prompt自动优化 → DSPy
企业搜索 → Haystack
```

---

## 8. 面试要点

### Q1: LangChain和LlamaIndex的区别？

```
LangChain：通用LLM应用框架，功能全面（Agent/Tool/Memory/Chain）
LlamaIndex：专注RAG，数据连接和检索更强

选LangChain：需要Agent、工具调用、复杂流程
选LlamaIndex：专注RAG知识库，需要丰富的数据源连接
```

### Q2: AutoGen和CrewAI的区别？

```
AutoGen：对话式协作，Agent间自由对话，支持代码执行
CrewAI：角色+任务模式，流程更结构化，更易用

选AutoGen：探索性任务、需要代码执行
选CrewAI：固定流程、内容创作、调研报告
```

### Q3: DSPy的核心理念是什么？

```
"Stop writing prompts, start programming them"

传统：手动写Prompt → 试错 → 优化
DSPy：定义IO签名 → 提供训练数据 → 自动优化Prompt

优势：
1. Prompt版本管理（代码管理）
2. 量化评估（有训练集和测试集）
3. 换模型自动重新优化
4. 减少人工调Prompt的时间
```

---

## 📚 相关阅读

- [04_LangChain4j详解](./04_LangChain4j详解.md)
- [06_Spring AI详解](./06_Spring AI详解.md)
- [12_Agent设计模式](./12_Agent设计模式.md)
- [20_AI Agent框架全景对比](./20_AI Agent框架全景对比.md)

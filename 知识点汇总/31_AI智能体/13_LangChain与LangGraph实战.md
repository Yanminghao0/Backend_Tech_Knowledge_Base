# LangChain与LangGraph实战

> LangChain Python生态、LCEL链式调用、LangGraph多Agent编排

---

## 📋 目录

1. [LangChain概述](#1-langchain概述)
2. [LCEL表达式语言](#2-lcel表达式语言)
3. [LangChain核心组件](#3-langchain核心组件)
4. [LangGraph状态图](#4-langgraph状态图)
5. [LlamaIndex RAG框架](#5-llamaindex-rag框架)
6. [Java工程师的Python速成](#6-java工程师的python速成)
7. [面试题速查](#7-面试题速查)

---

## 1. LangChain概述

```
LangChain — 最流行的LLM应用开发框架(Python)

  核心组件:
    1. Models — LLM/ChatModel/Embedding统一接口
    2. Prompts — Prompt模板管理
    3. Output Parsers — 结构化输出解析
    4. Retrievers — 检索器(RAG)
    5. Tools — 工具定义(Agent)
    6. Memory — 对话记忆
    7. Chains — 链式调用(LCEL)
    8. Agents — 自主Agent
    9. Callbacks — 事件回调(日志/监控)

  LangChain vs LangChain4j:
    LangChain(Python) — 生态最全，社区最大
    LangChain4j(Java) — Java移植版，功能约80%对齐
    建议: 两个都学，Python做原型/微调，Java做生产
```

---

## 2. LCEL表达式语言

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# LCEL = LangChain Expression Language (管道式链)
# 用 | 操作符连接组件

# 基础链: Prompt | LLM | Parser
prompt = ChatPromptTemplate.from_template("解释{topic}的概念")
model = ChatOpenAI(
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="your-dashscope-api-key"
)
parser = StrOutputParser()

chain = prompt | model | parser
result = chain.invoke({"topic": "Java Stream API"})
# → "Java Stream API是Java 8引入的函数式数据处理API..."

# 带RAG的链
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
vectorstore = Qdrant.from_existing_collection(
    embedding=embeddings,
    collection_name="documents",
    url="http://localhost:6333"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

rag_prompt = ChatPromptTemplate.from_template("""
基于以下信息回答问题:

{context}

问题: {question}
""")

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | rag_prompt
    | model
    | parser
)

result = rag_chain.invoke("什么是volatile关键字?")
```

---

## 3. LangChain核心组件

### 3.1 工具与Agent

```python
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent

# 定义工具
@tool
def search_web(query: str) -> str:
    """搜索网页获取最新信息"""
    return web_search(query)

@tool
def calculate(expression: str) -> str:
    """执行数学计算"""
    # 注意: 生产环境不要用eval()，应使用安全的数学解析库如numexpr
    import numexpr
    return str(numexpr.evaluate(expression))

@tool
def query_database(sql: str) -> str:
    """执行SQL查询数据库"""
    return db.execute(sql).to_json()

# 创建Agent
tools = [search_web, calculate, query_database]
agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = agent_executor.invoke({
    "input": "查询用户1001的订单总金额"
})
```

### 3.2 结构化输出

```python
from pydantic import BaseModel, Field

class PersonInfo(BaseModel):
    name: str = Field(description="人名")
    age: int = Field(description="年龄")
    email: str = Field(description="邮箱")

# 方式1: with_structured_output
structured_model = model.with_structured_output(PersonInfo)
result = structured_model.invoke("张三，25岁，邮箱zhangsan@example.com")
# → PersonInfo(name="张三", age=25, email="zhangsan@example.com")

# 方式2: JsonOutputParser
parser = JsonOutputParser(pydantic_object=PersonInfo)
chain = prompt | model | parser
```

---

## 4. LangGraph状态图

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator

# 定义状态
class WorkflowState(TypedDict):
    user_input: str
    search_results: str
    analysis: str
    report: str
    messages: Annotated[List[str], operator.add]

# 定义节点
def search_node(state: WorkflowState):
    results = search_tool(state["user_input"])
    return {"search_results": results, "messages": ["搜索完成"]}

def analyze_node(state: WorkflowState):
    analysis = llm.invoke(f"分析: {state['search_results']}")
    return {"analysis": analysis, "messages": ["分析完成"]}

def report_node(state: WorkflowState):
    report = llm.invoke(f"基于分析写报告: {state['analysis']}")
    return {"report": report, "messages": ["报告完成"]}

# 条件路由
def should_continue(state: WorkflowState):
    if "需要更多信息" in state["analysis"]:
        return "search"  # 回到搜索
    return "report"       # 生成报告

# 构建图
graph = StateGraph(WorkflowState)
graph.add_node("search", search_node)
graph.add_node("analyze", analyze_node)
graph.add_node("report", report_node)

graph.set_entry_point("search")
graph.add_edge("search", "analyze")
graph.add_conditional_edges("analyze", should_continue)
graph.add_edge("report", END)

# 编译运行
app = graph.compile()
result = app.invoke({"user_input": "分析2026年AI Agent趋势"})
```

---

## 5. LlamaIndex RAG框架

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike

# 配置
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-m3")
Settings.llm = OpenAILike(model="qwen-plus", api_base="...", api_key="...")

# 加载文档
documents = SimpleDirectoryReader("./docs").load_data()

# 分块
splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)

# 创建索引
index = VectorStoreIndex(nodes)

# 查询
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query("什么是volatile关键字?")
print(response.response)

# 流式查询
streaming_engine = index.as_query_engine(streaming=True)
for chunk in streaming_engine.query("解释Java并发"):
    print(chunk, end="", flush=True)

# 混合检索(向量+关键词)
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

vector_retriever = index.as_retriever(similarity_top_k=10)
bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=10)

hybrid_retriever = QueryFusionRetriever(
    [vector_retriever, bm25_retriever],
    num_queries=1,  # 不改写查询
    mode="reciprocal_rerank"  # RRF融合
)
```

---

## 6. Java工程师的Python速成

```
Java vs Python关键差异:

  ┌──────────────────────────────────────────────────────┐
  │  特性        │  Java           │  Python              │
  │  ──────   │  ────         │  ──────           │
  │  类型系统    │  静态强类型      │  动态类型             │
  │  语法        │  冗长             │  简洁(缩进)           │
  │  接口        │  interface       │  duck typing         │
  │  包管理      │  Maven/Gradle    │  pip/poetry          │
  │  虚拟环境    │  不常用           │  venv/conda(必须)    │
  │  异步        │  CompletableFuture│  async/await         │
  │  装饰器      │  注解(@)         │  装饰器(更强大)       │
  └──────────────────────────────────────────────────────┘

  Python AI生态必学:
    1. Pydantic — 数据验证(AI应用标配，类似Java Record)
    2. asyncio — 异步编程(类似CompletableFuture)
    3. typing — 类型注解(Python可选但AI代码必用)
    4. dataclass — 数据类(类似Java POJO)
    5. pip/venv — 包管理和虚拟环境

  快速上手路径:
    1. 语法基础(1天) — 廖雪峰Python教程
    2. Pydantic(半天) — AI应用都在用
    3. LangChain(2天) — 跟官方Tutorial走
    4. 实战(3天) — 用LangChain写RAG+Agent

  Java工程师学Python的优势:
    - 面向对象思维已有
    - 设计模式通用
    - 工程化思维有
    只需适应语法差异(动态类型/缩进/装饰器)
```

---

## 7. 面试题速查

**Q1: LangChain的LCEL是什么？**

```
LangChain Expression Language — 管道式链
用 | 操作符连接: prompt | model | parser
支持: 流式/异步/批量/并行(RunnableParallel)
比旧版Chain更灵活、更可组合
```

**Q2: LangGraph和LangChain Agent的区别？**

```
LangChain Agent: ReAct循环(简单但不灵活)
LangGraph: 状态图(灵活编排多Agent、条件路由、人机节点、中断恢复)
LangGraph是LangChain团队推荐的多Agent编排方案
```

**Q3: LlamaIndex和LangChain哪个好？**

```
LangChain: 通用LLM框架(Agent/Chain/工具全)
LlamaIndex: RAG专用(索引/检索/查询引擎更专业)
选择: 复杂Agent → LangChain/LangGraph; 纯RAG → LlamaIndex
两者可混用(LlamaIndex的检索器 + LangChain的Agent)
```

**Q4: Java工程师怎么学Python AI生态？**

```
1. 语法基础(1天) — 动态类型/缩进/装饰器
2. Pydantic(半天) — AI应用标配数据验证
3. LangChain(2天) — 官方Tutorial
4. 实战(3天) — RAG+Agent项目
优势: OO思维和工程能力已有，只需适应语法
```

---

*最后更新: 2026-07-13*

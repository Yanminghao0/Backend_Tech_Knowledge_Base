# 高级RAG: Self-RAG与GraphRAG

> Self-RAG、Corrective RAG、GraphRAG、Agentic RAG等前沿RAG技术

---

## 📋 目录

1. [标准RAG的局限](#1-标准rag的局限)
2. [Self-RAG](#2-self-rag)
3. [Corrective RAG(CRAG)](#3-corrective-ragcrag)
4. [GraphRAG](#4-graphrag)
5. [Adaptive RAG](#5-adaptive-rag)
6. [Agentic RAG](#6-agentic-rag)
7. [面试题速查](#7-面试题速查)

---

## 1. 标准RAG的局限

```
标准RAG流程: 查询→检索→拼接→生成

  问题:
    1. 总是检索 — 简单问题("你好")也检索，浪费
    2. 不评估质量 — 检索到垃圾也照用
    3. 无全局视角 — 只看Top-K片段，无法回答"总结全文"
    4. 无自我纠错 — 生成错误答案不会回头重检索
    5. 无关系推理 — 无法回答"A和B的关系是什么"

  ┌──────────────────────────────────────────────────┐
  │  标准RAG:  查询→检索(总是)→生成(直接)            │
  │  Self-RAG: 查询→判断→检索(按需)→评估→生成       │
  │  CRAG:     查询→检索→评估质量→纠正→生成         │
  │  GraphRAG: 查询→知识图谱检索→全局+局部→生成     │
  │  Adaptive: 查询→判断难度→选择策略→生成          │
  │  Agentic:  查询→Agent自主决策→多轮检索→生成     │
  └──────────────────────────────────────────────────┘
```

---

## 2. Self-RAG

```
Self-RAG — 模型自判断是否检索 + 检索质量评估

  论文: "Self-RAG: Learning to Retrieve, Generate, and Critique
        through Self-Reflection" (2023)

  核心改进:
    1. 不总是检索 — 模型自己决定是否需要检索
    2. 评估检索质量 — 检索结果是否相关
    3. 评估生成质量 — 回答是否忠实于检索内容

  流程:
    ┌──────────────────────────────────────────────────┐
    │  查询: "你好"                                     │
    │  → [Retrieve?] 模型判断: 不需要检索(简单问候)     │
    │  → 直接生成: "你好！有什么可以帮你的?"            │
    │                                                  │
    │  查询: "Java volatile原理"                        │
    │  → [Retrieve?] 模型判断: 需要检索                 │
    │  → 检索 → [Relevant?] 检查相关性                  │
    │    相关 → 生成 → [Faithful?] 检查忠实度           │
    │    不相关 → 重新检索或标记                        │
    └──────────────────────────────────────────────────┘

  反思token(Reflection Tokens):
    [Retrieve] — 是否检索 (yes/no)
    [IsRel] — 检索结果是否相关 (relevant/irrelevant)
    [IsSup] — 生成是否被检索内容支持 (fully/partially/no)
    [IsUse] — 生成是否有用 (5/4/3/2/1)

  实现(简化):
    def self_rag(query):
        # 1. 判断是否需要检索
        if llm.judge_need_retrieve(query):
            docs = retrieve(query)
            # 2. 评估检索质量
            if not llm.judge_relevant(query, docs):
                docs = retrieve(query, rewrite=True)  # 重写查询再检索
        else:
            docs = []

        # 3. 生成
        answer = llm.generate(query, docs)

        # 4. 评估忠实度
        if not llm.judge_faithful(answer, docs):
            answer = llm.regenerate(query, docs)  # 重新生成

        return answer
```

---

## 3. Corrective RAG(CRAG)

```
CRAG — 检索质量评估 + 纠正

  核心思想: 检索结果可能不好 → 评估 → 不好就纠正

  流程:
    1. 检索 — 标准向量检索获取文档
    2. 评估 — 用LLM/规则评估检索质量
       Correct: 检索结果高度相关
       Incorrect: 检索结果不相关
       Ambiguous: 不确定
    3. 纠正:
       Correct → 直接使用检索结果
       Incorrect → 用Web搜索补充(外部知识)
       Ambiguous → 检索结果+Web搜索都用
    4. 精炼 — 对文档进行精炼(提取关键信息)
    5. 生成 — 基于精炼后的内容生成

  ┌──────────────────────────────────────────────────┐
  │  标准: 检索→直接用                               │
  │  CRAG: 检索→评估→好就用/不好就Web搜索→精炼→生成  │
  └──────────────────────────────────────────────────┘

  代码实现(LangGraph):
    def retrieve(state):
        docs = vectorstore.search(state["query"])
        return {"docs": docs}

    def grade_documents(state):
        # 评估每个文档的相关性
        graded = []
        for doc in state["docs"]:
            score = llm.judge_relevance(state["query"], doc)
            graded.append((doc, score))
        return {"graded_docs": graded}

    def decide_to_search(state):
        # 如果检索结果都不好 → Web搜索
        if all(score == "no" for _, score in state["graded_docs"]):
            return "web_search"
        return "generate"

    def web_search(state):
        results = web_search_tool(state["query"])
        return {"docs": results}

    def generate(state):
        answer = llm.generate(state["query"], state["docs"])
        return {"answer": answer}

    # LangGraph编排
    graph = StateGraph()
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade", grade_documents)
    graph.add_node("web_search", web_search)
    graph.add_node("generate", generate)
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", decide_to_search)
    graph.add_edge("web_search", "generate")
    graph.add_edge("generate", END)
```

---

## 4. GraphRAG

### 4.1 原理

```
GraphRAG(微软) — 知识图谱 + 向量检索

  标准RAG的问题:
    "这本书的核心观点是什么?" → 只检索片段无法回答全局问题
    "A和B的关系?" → 片段检索无法回答关系推理

  GraphRAG解决:
    1. 构建知识图谱 — 从文档中抽取实体+关系
    2. 社区检测 — 将相关实体聚类成社区
    3. 社区摘要 — 每个社区生成摘要
    4. 检索 — 全局问题用社区摘要，局部问题用实体检索

  ┌──────────────────────────────────────────────────┐
  │  文档                                             │
  │    ↓                                             │
  │  实体抽取(人/组织/概念)                           │
  │    ↓                                             │
  │  关系抽取(A→B: "创建了")                         │
  │    ↓                                             │
  │  知识图谱(节点=实体, 边=关系)                     │
  │    ↓                                             │
  │  社区检测(Leiden算法)                             │
  │    ↓                                             │
  │  社区摘要(LLM为每个社区生成摘要)                  │
  │    ↓                                             │
  │  检索:                                           │
  │    全局问题 → 搜索社区摘要                        │
  │    局部问题 → 搜索实体+关系                       │
  └──────────────────────────────────────────────────┘
```

### 4.2 GraphRAG vs 标准RAG

```
┌──────────────────────────────────────────────────────┐
  │  维度        │  标准RAG        │  GraphRAG           │
  │  ──────   │  ──────      │  ──────         │
  │  检索单元    │  文本片段        │  实体+关系+社区     │
  │  全局问题    │  ❌(只看片段)   │  ✅(社区摘要)       │
  │  关系推理    │  ❌             │  ✅(图谱关系)       │
  │  构建成本    │  低(嵌入即可)   │  高(图谱构建)       │
  │  更新成本    │  低(增量嵌入)   │  高(重新构建图谱)   │
  │  适合        │  具体事实问答    │  全局分析/关系推理  │
  └──────────────────────────────────────────────────────┘

  GraphRAG适合:
    "分析这本书的主题"
    "这家公司的竞争格局"
    "A技术和B技术的区别与联系"

  标准RAG适合:
    "Java volatile关键字是什么?"
    "怎么配置Spring Boot?"
```

---

## 5. Adaptive RAG

```
Adaptive RAG — 根据问题难度选择检索策略

  核心思想: 不同问题用不同RAG策略

  ┌──────────────────────────────────────────────────┐
  │  问题类型        │  策略                          │
  │  ──────       │  ──────                     │
  │  简单(问候)     │  不检索(直接回答)              │
  │  事实查询       │  标准RAG(向量检索)             │
  │  复杂分析       │  GraphRAG(全局+社区)           │
  │  最新信息       │  Web搜索                       │
  │  多角度问题     │  多路检索+融合                  │
  │  需要推理       │  多步检索(迭代)                │
  └──────────────────────────────────────────────────┘

  实现:
    def adaptive_rag(query):
        # 1. 分类问题
        question_type = llm.classify(query)
        # 简单/事实/分析/最新/多角度/推理

        # 2. 选择策略
        if question_type == "simple":
            return llm.generate(query)  # 不检索
        elif question_type == "factual":
            return standard_rag(query)
        elif question_type == "analytical":
            return graph_rag(query)
        elif question_type == "latest":
            return web_search_rag(query)
        elif question_type == "multi_angle":
            return multi_query_rag(query)
        elif question_type == "reasoning":
            return iterative_rag(query)
```

---

## 6. Agentic RAG

```
Agentic RAG — Agent驱动RAG(自主决策检索)

  核心思想: 把RAG当作Agent的工具
    Agent决定: 是否检索/检索什么/检索几次/是否够了

  ┌──────────────────────────────────────────────────┐
  │  用户: "对比Spring Boot和Quarkus在微服务中的表现" │
  │                                                  │
  │  Agent决策:                                      │
  │  1. 检索"Spring Boot微服务性能" → 获取信息         │
  │  2. 检索"Quarkus微服务性能" → 获取信息             │
  │  3. 检索"Spring Boot vs Quarkus对比" → 补充        │
  │  4. 评估: 信息是否充分? → 是                      │
  │  5. 生成对比报告                                  │
  │                                                  │
  │  vs 标准RAG: 一次检索可能不够                     │
  │  Agentic RAG: Agent自主多轮检索直到信息充分       │
  └──────────────────────────────────────────────────┘

  实现(LangGraph):
    def agent_rag(query):
        # Agent有检索工具
        tools = [vector_search, web_search, keyword_search]

        # Agent循环
        for step in range(max_steps):
            # LLM决策: 需要检索什么?
            action = llm.decide(query, history, tools)

            if action.type == "final_answer":
                return action.answer

            # 执行检索
            results = execute_tool(action)

            # 评估是否充分
            if llm.is_sufficient(query, history, results):
                return llm.generate(query, history)

            history.append(results)

    # LangGraph实现更优雅:
    # Node: decide_retrieve → retrieve → evaluate → (loop) or generate
```

---

## 7. 面试题速查

**Q1: Self-RAG和标准RAG的区别？**

```
标准RAG: 总是检索，不评估质量
Self-RAG: 模型自判断是否检索+评估检索质量+评估生成忠实度
优势: 简单问题不浪费检索，复杂问题保证质量
```

**Q2: GraphRAG解决什么问题？**

```
标准RAG无法回答全局问题("全书核心观点")和关系问题("A和B关系")
GraphRAG: 构建知识图谱→社区检测→社区摘要
全局问题用社区摘要，局部问题用实体检索
适合: 分析类/关系推理类问题
```

**Q3: CRAG怎么纠正检索？**

```
检索→评估质量→好就用/不好就Web搜索→精炼→生成
标准RAG不管检索质量直接用
CRAG评估检索结果，不好就补充Web搜索
```

**Q4: Adaptive RAG的策略？**

```
根据问题类型选择策略:
简单→不检索, 事实→标准RAG, 分析→GraphRAG
最新→Web搜索, 多角度→多路检索, 推理→迭代检索
用LLM分类问题类型 → 选择策略
```

**Q5: Agentic RAG是什么？**

```
Agent驱动RAG: 把检索当作Agent工具
Agent自主决定: 检索什么/检索几次/是否够了
多轮检索直到信息充分 → 生成
比标准RAG灵活，适合复杂研究类问题
```

---

*最后更新: 2026-07-13*

# Agent规划与反思机制

> Plan-Execute、Self-Refine、Reflexion等Agent高级推理模式

---

## 📋 目录

1. [规划(Planning)机制](#1-规划planning机制)
2. [反思(Reflection)机制](#2-反思reflection机制)
3. [Self-Refine模式](#3-self-refine模式)
4. [Reflexion模式](#4-reflexion模式)
5. [Tree of Thoughts](#5-tree-of-thoughts)
6. [记忆系统](#6-记忆系统)
7. [Agent终止与控制](#7-agent终止与控制)
8. [面试题速查](#8-面试题速查)

---

## 1. 规划(Planning)机制

### 1.1 任务分解

```
任务分解(Task Decomposition) = 将复杂任务拆成可执行的子任务

  ┌──────────────────────────────────────────────────────┐
  │  用户: "帮我分析竞品APP的功能差异，写一份报告"          │
  │                                                      │
  │  规划:                                                │
  │  ├── 步骤1: 确定竞品范围(选3个竞品)                   │
  │  ├── 步骤2: 搜索竞品A的功能列表                       │
  │  ├── 步骤3: 搜索竞品B的功能列表                       │
  │  ├── 步骤4: 搜索竞品C的功能列表                       │
  │  ├── 步骤5: 整理功能对比矩阵                          │
  │  ├── 步骤6: 分析差异化亮点                            │
  │  └── 步骤7: 撰写报告                                  │
  │                                                      │
  │  执行: 逐步执行，步骤2-4可并行                        │
  └──────────────────────────────────────────────────────┘

  分解策略:
    1. 线性分解 — 步骤1→步骤2→步骤3(有依赖)
    2. 树形分解 — 一个步骤拆出多个并行子步骤
    3. DAG分解 — 有向无环图(有并行有依赖)

  分解粒度:
    太粗 → 步骤太大不好执行
    太细 → 步骤太多管理复杂
    经验: 每个步骤应该是"一次工具调用或一次LLM推理"能完成的
```

### 1.2 动态重规划

```
Replan(重规划) = 执行中发现计划不合理，重新规划

  触发条件:
    1. 工具调用失败 — API不可用/参数错误
    2. 结果不符合预期 — 搜索结果为空/数据不完整
    3. 发现新信息 — 需要补充之前没想到的步骤
    4. 超时 — 某步耗时过长，需要换方案

  示例:
    原计划:
      步骤1: 搜索"Spring Cloud Gateway"
      步骤2: 搜索"Spring Cloud Gateway限流配置"
      步骤3: 写总结

    执行步骤1 → 发现Spring Cloud Gateway已废弃，推荐用新版本
    → Replan:
      步骤2: 搜索"Spring Cloud Gateway 4.x限流"
      步骤3: 写总结(包含版本差异)

  实现:
    if (需要重规划) {
        remaining_steps = 当前计划中未执行的步骤
        new_plan = LLM.replan(原计划, 已执行步骤, 新信息, remaining_steps)
        执行 new_plan
    }
```

---

## 2. 反思(Reflection)机制

### 2.1 反思的价值

```
没有反思的Agent:
  执行→输出(可能出错，但不自知)

有反思的Agent:
  执行→输出→自我检查→发现问题→修正→更好的输出

  ┌──────────────────────────────────────────┐
  │  类比人类工作:                             │
  │  初稿 → 自我审查 → 修改 → 终稿             │
  │  代码 → Code Review → 修改 → 合并          │
  └──────────────────────────────────────────┘

  反思的收益:
    1. 提高准确率 — 发现并修正错误
    2. 提高完整性 — 发现遗漏的内容
    3. 提高质量 — 改进表达和结构
    4. 自我学习 — 从错误中学习改进
```

### 2.2 反思的实现

```python
# 反思的基本实现
def agent_with_reflection(user_task):
    # 1. 生成初始结果
    initial_result = llm.generate(user_task)

    # 2. 反思: 自我评估
    reflection_prompt = f"""
    任务: {user_task}
    你的回答: {initial_result}

    请评估你的回答:
    1. 是否完全回答了问题?
    2. 有没有事实错误?
    3. 有没有遗漏?
    4. 表达是否清晰?
    5. 如何改进?

    评估:
    """
    reflection = llm.generate(reflection_prompt)

    # 3. 基于反思改进
    improve_prompt = f"""
    任务: {user_task}
    初版回答: {initial_result}
    反思: {reflection}

    请基于反思改进你的回答:
    """
    improved = llm.generate(improve_prompt)

    return improved
```

---

## 3. Self-Refine模式

### 3.1 原理

```
Self-Refine = 生成→审查→修改循环

  论文: "Self-Refine: Iterative Refinement with Self-Feedback" (2023)

  ┌──────────────────────────────────────────┐
  │         用户输入任务                       │
  │             ↓                            │
  │      ┌──────────┐                       │
  │      │  生成     │ ← LLM生成初始输出      │
  │      └────┬─────┘                       │
  │           ↓                              │
  │      ┌──────────┐                       │
  │      │  反馈     │ ← LLM自我评估          │
  │      └────┬─────┘                       │
  │           ↓                              │
  │      ┌──────────┐                       │
  │      │  修改     │ ← LLM基于反馈修改      │
  │      └────┬─────┘                       │
  │           ↓                              │
  │      质量足够?                            │
  │       ↙    ↘                             │
  │     否      是                            │
  │     ↓        ↓                           │
  │   回到反馈  输出最终结果                   │
  └──────────────────────────────────────────┘

  与ReAct的区别:
    ReAct: Think→Act→Observe(行动+观察)
    Self-Refine: 生成→反馈→修改(文本质量改进)

  适用场景:
    代码生成 — 生成代码→审查→修改
    文案写作 — 初稿→评估→修改
    翻译 — 初翻→审校→修改
    数学推理 — 解题→验证→修正
```

### 3.2 代码实现

```python
def self_refine(task, max_iterations=3):
    # 1. 生成初始结果
    result = llm.generate(f"请完成以下任务:\n{task}")

    for i in range(max_iterations):
        # 2. 自我反馈
        feedback = llm.generate(f"""
        任务: {task}
        当前结果: {result}

        请找出当前结果的问题(不要修改，只指出问题):
        1. 准确性问题
        2. 完整性问题
        3. 表达问题
        """)

        # 3. 判断是否需要继续
        if "没有问题" in feedback or "很好" in feedback:
            break

        # 4. 基于反馈改进
        result = llm.generate(f"""
        任务: {task}
        当前结果: {result}
        反馈: {feedback}

        请基于反馈改进结果:
        """)

    return result

# 示例: 代码生成
code = self_refine("""
写一个Java方法: 给定一个整数数组，返回出现频率最高的K个元素
要求: 时间复杂度O(n log k)
""")
# 第1轮: 生成初始代码(可能有bug)
# 第2轮: 反馈发现没处理空数组 → 修改
# 第3轮: 反馈发现复杂度分析不对 → 修改
# 最终: 高质量代码
```

---

## 4. Reflexion模式

### 4.1 原理

```
Reflexion = 失败→反思记忆→重试(带记忆的自我改进)

  论文: "Reflexion: Language Agents with Verbal Reinforcement Learning" (2023)

  与Self-Refine的区别:
    Self-Refine: 同一次任务内迭代改进
    Reflexion: 跨多次尝试，记住之前的失败教训

  ┌──────────────────────────────────────────────┐
  │  尝试1:                                        │
  │    执行任务 → 失败                              │
  │    反思: "为什么失败? 因为没考虑边界条件"        │
  │    记忆: 存入"教训: 检查边界条件"               │
  │                                                │
  │  尝试2(带记忆):                                 │
  │    执行任务(应用之前的教训) → 可能还失败          │
  │    反思: "还失败因为算法选择不当"                │
  │    记忆: 追加"教训: 大数据用Hash不用排序"        │
  │                                                │
  │  尝试3(带全部记忆):                              │
  │    执行任务(应用所有教训) → 成功!                │
  └──────────────────────────────────────────────┘

  核心要素:
    1. 执行器(Actor) — 执行任务(ReAct/Plan-Execute)
    2. 评估器(Evaluator) — 评估执行结果(成功/失败/分数)
    3. 反思器(Reflector) — 分析失败原因，生成语言反馈
    4. 记忆(Memory) — 存储历史反思，指导下次尝试
```

### 4.2 实现示例

```python
def reflexion_agent(task, max_attempts=3):
    reflections = []  # 反思记忆

    for attempt in range(max_attempts):
        # 1. 执行任务(带历史反思)
        context = f"""
        任务: {task}

        历史教训:
        {chr(10).join(reflections) if reflections else "无"}

        请完成任务，注意避免之前的错误。
        """
        result = react_agent.execute(context)

        # 2. 评估结果
        evaluation = evaluator.evaluate(task, result)
        if evaluation.success:
            return result

        # 3. 反思失败原因
        reflection = llm.generate(f"""
        任务: {task}
        尝试#{attempt+1}的执行: {result}
        评估: {evaluation.feedback}

        为什么失败了? 学到了什么教训?
        请用一句话总结教训(下次应避免的):
        """)
        reflections.append(f"尝试#{attempt+1}: {reflection}")

    return result  # 返回最后一次结果(可能未成功)
```

---

## 5. Tree of Thoughts

### 5.1 原理

```
ToT(Tree of Thoughts) = 树形搜索+回溯

  论文: "Tree of Thoughts: Deliberate Problem Solving with LLMs" (2023)

  与CoT(链式思维)的区别:
    CoT: 线性推理 A→B→C→D(一条路走到底)
    ToT: 树形推理 → 每步生成多个候选 → 评估 → 选最优 → 可回溯

  ┌──────────────────────────────────────────────────┐
  │  问题: "24点游戏: 1, 5, 5, 5"                     │
  │                                                  │
  │  CoT: 5×5=25→25-1=24→✗(还剩一个5)               │
  │                                                  │
  │  ToT:                                            │
  │  Step1: 5/5=1 | 5-5=0 | 5×5=25 | 5+5=10         │
  │         ↓                                        │
  │  Step2: (对每个Step1结果继续)                      │
  │    5/5=1: 1+5=6 | 1-5=-4 | 1×5=5 | 1/5=0.2      │
  │    5-5=0: 0+5=5 | 0×5=0 | ...                   │
  │    5×5=25: 25-5=20 | 25+5=30 | 25/5=5 | ...     │
  │         ↓                                        │
  │  Step3: 评估每个分支 → 5/5=1→1×5=5→5×5=25?✗      │
  │         回溯 → 尝试其他分支                       │
  │         → 5-1/5=4.8 → 5×4.8=24 ✓                │
  └──────────────────────────────────────────────────┘

  ToT步骤:
    1. 分解 — 将问题分解为思维步骤
    2. 生成 — 每步生成多个候选思维
    3. 评估 — 给每个候选思维打分
    4. 搜索 — BFS/DFS搜索最优路径
    5. 回溯 — 走不通时回溯到上一步
```

### 5.2 适用场景

```
ToT适合: 需要探索+回溯的问题
  数学推理 — 24点、逻辑题
  创意写作 — 多种开头→选最优→继续
  决策问题 — 多种策略→评估→选最优
  代码调试 — 多种修复方案→试→评估

ToT不适合: 简单线性任务(用CoT即可)
  成本高(每步多次LLM调用)
  速度慢(搜索+回溯)
  大多数日常任务CoT+Self-Refine已够用
```

---

## 6. 记忆系统

### 6.1 记忆类型

```
┌──────────────────────────────────────────────────────┐
  │  记忆类型    │  存储          │  容量    │  检索方式  │
  │  ──────   │  ────       │  ────  │  ────   │
  │  短期记忆    │  对话上下文     │  有限    │  直接访问  │
  │  长期记忆    │  向量数据库     │  无限    │  语义检索  │
  │  工作记忆    │  任务状态变量   │  小      │  直接访问  │
  │  情景记忆    │  向量+时间戳    │  无限    │  时间+语义 │
  └──────────────────────────────────────────────────────┘

  短期记忆(Short-term):
    = 当前对话的上下文窗口
    实现: 消息列表 [user_msg1, ai_msg1, user_msg2, ...]
    限制: 上下文窗口大小(如4K/8K/128K token)
    管理: 滑动窗口/摘要压缩

  长期记忆(Long-term):
    = 跨会话的持久记忆
    实现: 向量数据库存储历史交互
    检索: 语义相似度检索相关历史
    示例: "用户之前问过Java并发，这次问线程池"
      → 检索历史 → 知道用户在学Java并发

  工作记忆(Working):
    = 当前任务的中间状态
    实现: JSON/Dict存储任务变量
    示例: {step: 3, found_data: [...], pending_tasks: [...]}

  情景记忆(Episodic):
    = 具体事件的记忆(何时何地发生了什么)
    实现: 向量+时间戳+元数据
    检索: "上周用户问了什么" → 时间范围+语义检索
```

### 6.2 记忆管理

```python
class AgentMemory:
    def __init__(self):
        self.short_term = []  # 短期记忆(对话历史)
        self.long_term = VectorStore(collection="agent_memory")  # 长期记忆
        self.working = {}  # 工作记忆(任务状态)
        self.max_short_term = 20  # 短期记忆最大条数

    def add_message(self, role, content):
        """添加对话消息到短期记忆"""
        self.short_term.append({"role": role, "content": content})
        # 超出限制 → 摘要压缩
        if len(self.short_term) > self.max_short_term:
            self._compress_memory()

    def _compress_memory(self):
        """压缩短期记忆: 将旧消息摘要后移入长期记忆"""
        # 取出前一半消息
        old_messages = self.short_term[:self.max_short_term // 2]
        # LLM摘要
        summary = llm.generate(f"请摘要以下对话:\n{old_messages}")
        # 存入长期记忆(带向量)
        self.long_term.add({
            "content": summary,
            "embedding": embedding_model.encode(summary),
            "timestamp": datetime.now(),
            "type": "conversation_summary"
        })
        # 保留后一半 + 摘要
        self.short_term = [
            {"role": "system", "content": f"历史摘要: {summary}"}
        ] + self.short_term[self.max_short_term // 2:]

    def recall(self, query, top_k=5):
        """从长期记忆中检索相关内容"""
        query_vec = embedding_model.encode(query)
        results = self.long_term.search(query_vec, top_k=top_k)
        return results

    def get_context(self, query):
        """获取完整上下文 = 短期记忆 + 长期检索"""
        long_term_recall = self.recall(query)
        context = {
            "short_term": self.short_term,
            "long_term_recall": long_term_recall,
            "working_memory": self.working
        }
        return context
```

---

## 7. Agent终止与控制

### 7.1 终止条件

```
Agent必须设置终止条件，否则可能无限循环:

  ┌──────────────────────────────────────────────────────┐
  │  终止条件          │  说明                            │
  │  ──────         │  ────                         │
  │  任务完成          │  LLM判断目标已达成               │
  │  最大步数          │  如max_steps=15                  │
  │  超时              │  如total_timeout=120s             │
  │  单步超时          │  如step_timeout=30s               │
  │  重复检测          │  连续相同Action→终止             │
  │  用户中断          │  用户主动取消                    │
  │  错误次数          │  连续失败超过阈值                 │
  │  Token预算         │  总Token消耗超限                  │
  └──────────────────────────────────────────────────────┘

  多条件组合: 满足任一条件即终止
```

### 7.2 人机协作

```
Human-in-the-loop = 关键决策需要人工确认

  ┌──────────────────────────────────────────┐
  │  场景1: 危险操作前确认                     │
  │  Agent: "我要执行DELETE FROM users"       │
  │  → 暂停 → 人工确认 → 继续/取消             │
  │                                          │
  │  场景2: 需要额外信息                       │
  │  Agent: "需要用户的手机号"                 │
  │  → 暂停 → 人工输入 → 继续                  │
  │                                          │
  │  场景3: 选择方案                           │
  │  Agent: "方案A成本低但慢, 方案B快但贵"     │
  │  → 暂停 → 人工选择 → 继续                  │
  └──────────────────────────────────────────┘

  实现(LangGraph):
    graph.add_node("ask_human", ask_human_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent",
        lambda state: "ask_human" if state.needs_approval else "execute"
    )
    graph.add_edge("ask_human", "agent")  # 人工回答后回到Agent
```

---

## 8. 面试题速查

**Q1: Agent的规划和反思有什么区别？**

```
规划(Planning): 任务执行前，将复杂任务分解为步骤
反思(Reflection): 任务执行后，评估结果并自我改进
规划是"事前"，反思是"事后"
两者可组合: Plan→Execute→Reflect→Replan
```

**Q2: Self-Refine和Reflexion的区别？**

```
Self-Refine: 同一次任务内 生成→反馈→修改 循环
Reflexion: 跨多次尝试，记住失败教训指导下次
Self-Refine是"即时改进"，Reflexion是"跨尝试学习"
```

**Q3: Tree of Thoughts和CoT的区别？**

```
CoT: 线性推理(一条路走到底)
ToT: 树形搜索(每步多候选→评估→选最优→可回溯)
ToT适合需要探索的问题(数学/决策)，但成本高
大多数场景CoT+Self-Refine够用
```

**Q4: Agent记忆系统如何设计？**

```
短期记忆: 对话上下文(窗口管理+摘要压缩)
长期记忆: 向量数据库(语义检索历史)
工作记忆: 任务状态(JSON变量)
检索: 当前问题→长期记忆语义检索→相关历史→注入上下文
```

**Q5: 如何防止Agent无限循环？**

```
1. 最大步数(max_steps=10-20)
2. 总超时(total_timeout=120s)
3. 重复检测(连续相同Action终止)
4. Token预算限制
5. 用户中断机制
6. 错误次数阈值(连续失败>3次终止)
```

---

*最后更新: 2026-07-13*

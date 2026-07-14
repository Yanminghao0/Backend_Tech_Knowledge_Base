# AI智能体与大模型

> Java工程师转AI智能体方向的完整知识体系：LLM原理、Agent开发、RAG系统、微调部署、多Agent、生产工程化

---

## 📋 文档列表

### P0 核心基础
| 文档 | 核心内容 | 大小 |
|------|----------|------|
| [01_LLM基础原理与Transformer架构](01_LLM基础原理与Transformer架构.md) | 神经网络/注意力机制/Transformer/Decoder-only/MoE/KV Cache | 38KB |
| [02_大模型训练全流程](02_大模型训练全流程.md) | 预训练/SFT/RLHF/DPO/分布式训练/Scaling Laws | 23KB |
| [03_Agent核心架构与ReAct模式](03_Agent核心架构与ReAct模式.md) | Agent循环/ReAct/Plan-Execute/ReWOO/设计模式 | 25KB |
| [04_工具调用与Function Calling实战](04_工具调用与FunctionCalling实战.md) | Function Calling/MCP/Spring AI/LangChain4j | 22KB |
| [05_向量数据库深入](05_向量数据库深入.md) | HNSW/IVF/PQ/Milvus/Qdrant/pgvector/混合检索 | 21KB |
| [06_Agent规划与反思机制](06_Agent规划与反思机制.md) | 规划/反思/Self-Refine/Reflexion/ToT/记忆系统 | 21KB |

### P1 进阶实战
| 文档 | 核心内容 | 大小 |
|------|----------|------|
| [07_多Agent系统设计](07_多Agent系统设计.md) | LangGraph/AutoGen/CrewAI/协作模式 | 14KB |
| [08_模型微调实战LoRA与QLoRA](08_模型微调实战LoRA与QLoRA.md) | LoRA原理/LLaMA-Factory/数据构建 | 13KB |
| [09_LLM部署与推理加速](09_LLM部署与推理加速.md) | vLLM/Ollama/PagedAttention/投机解码/GPU选型 | 15KB |
| [10_AI评估与监控](10_AI评估与监控.md) | RAGAS/LangSmith/Langfuse/在线监控 | 12KB |
| [11_AI安全与对齐](11_AI安全与对齐.md) | Prompt注入/幻觉/越狱/Agent安全/对齐技术 | 9KB |
| [12_多模态大模型](12_多模态大模型.md) | LLaVA/Qwen-VL/Whisper/多模态RAG/GUI Agent | 9KB |
| [13_LangChain与LangGraph实战](13_LangChain与LangGraph实战.md) | LCEL/LangGraph/LlamaIndex/Python速成 | 10KB |
| [14_AI生产工程化](14_AI生产工程化.md) | 多模型路由/缓存限流/成本优化/CI-CD | 14KB |
| [15_高级RAG_Self-RAG与GraphRAG](15_高级RAG_Self-RAG与GraphRAG.md) | Self-RAG/CRAG/GraphRAG/Adaptive/Agentic RAG | 14KB |

---

## 🎯 学习路线

```
Phase 1 (Week 1-3): 基础 — 01→02→04(模块4 Prompt)
Phase 2 (Week 4-5): RAG  — 05→15
Phase 3 (Week 6-8): Agent — 03→06→04→07
Phase 4 (Week 9-10): 微调部署 — 08→09
Phase 5 (Week 11-14): 生产 — 10→11→12→13→14
```

## 🔗 相关文档
- [12_AI集成](../12_AI集成/) — Spring AI/LangChain4j/RAG基础/Agent设计模式
- [15_MCP协议](../15_MCP协议/) — Function Calling/MCP协议详解
- [24_Java AI框架](../24_JavaAI框架/) — Java AI框架全景
- [99_计划/05_AI智能体学习规划](../99_计划/05_AI智能体学习规划.md) — 完整学习路线图

---

*最后更新: 2026-07-13*

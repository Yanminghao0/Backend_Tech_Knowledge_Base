# Java AI框架知识库

> 收录2025-2026年主流Java AI框架的核心知识点，为Java开发者提供全面的AI技术选型参考

---

## 📋 目录结构

| 文档 | 框架 | 核心定位 | 状态 |
|------|------|---------|------|
| [AI框架对比分析](./07_AI框架对比分析.md) | 综合对比 | 6大框架横向对比与选型指南 | ✅ 已完成 |
| [08_Solon框架](./08_Solon框架.md) | Solon | 国产轻量级应用框架，AI扩展支持 | ✅ 已完成 |
| [01_LangChain4J](./01_LangChain4J.md) | LangChain4J | LLM应用开发（集成、提示工程、记忆管理） | ✅ 已完成 |
| [02_Spring AI](./02_Spring%20AI.md) | Spring AI | Spring生态AI集成（声明式API、自动配置） | ✅ 已完成 |
| [03_Deeplearning4j](./03_Deeplearning4j.md) | DL4J | 分布式深度学习（Hadoop/Spark集成） | ✅ 已完成 |
| [04_Djl.ai](./04_Djl.ai.md) | DJL | 深度学习部署（多后端、GPU加速） | ✅ 已完成 |
| [05_Tribuo](./05_Tribuo.md) | Tribuo | 机器学习算法库（分类/聚类、可解释性） | ✅ 已完成 |
| [06_Solon AI](./06_Solon%20AI.md) | Solon AI | Solon框架的AI扩展模块 | ✅ 已完成 |

---

## 📊 框架对比速查表

| 框架名称 | 核心定位 | 采用率 | 主要优势 | 最佳适用场景 |
|---------|---------|-------|---------|------------|
| **LangChain4J** | LLM应用开发 | 68% | 大语言模型集成、提示工程、记忆管理 | 聊天机器人、智能问答、RAG系统 |
| **Spring AI** | Spring生态AI集成 | 52% | 声明式API、微服务友好、Spring生态无缝衔接 | Spring应用AI增强、企业级LLM集成 |
| **Djl.ai** | 深度学习部署 | 35% | 多后端支持、GPU加速、轻量化部署 | 计算机视觉、模型部署、实时推理 |
| **Deeplearning4j** | 分布式深度学习 | - | Hadoop/Spark集成、大规模训练 | 金融风控、企业级深度学习、大数据AI |
| **Tribuo** | 机器学习算法库 | - | 分类/聚类算法、Oracle集成、可解释性 | 企业数据分析、客户细分、风险评估 |
| **Solon AI** | 轻量级AI扩展 | - | 国产框架、轻量级、快速启动 | 中小项目AI集成、快速原型开发 |

---

## 🎯 技术选型指南

### 按功能需求选择

| 需求场景 | 推荐框架 | 备选方案 | 选择理由 |
|---------|---------|---------|---------|
| **大语言模型应用** | LangChain4J | Spring AI | 功能全面、社区活跃、RAG支持完善 |
| **Spring应用AI增强** | Spring AI | LangChain4J | 声明式API、自动配置、生态无缝衔接 |
| **深度学习部署** | Djl.ai | Deeplearning4j | 多后端(TensorFlow/PyTorch/MXNet)、轻量 |
| **分布式深度学习** | Deeplearning4j | Djl.ai | Hadoop/Spark原生集成、大规模训练 |
| **传统机器学习** | Tribuo | - | Oracle支持、可解释性强、企业级 |
| **轻量级AI集成** | Solon AI | Spring AI | 框架轻量、启动快、适合中小项目 |

### 按技术背景选择

- **Java开发者**：所有框架均提供原生Java API，推荐LangChain4J或Spring AI入门
- **Python转Java**：Djl.ai（语法简洁）或LangChain4J（概念与Python LangChain相似）
- **企业级部署**：Spring AI（成熟生态）或Tribuo（Oracle优化）
- **大数据团队**：Deeplearning4j（Hadoop/Spark集成）
- **国产化需求**：Solon AI（国产框架、中文社区支持）

### 按团队能力选择

- **AI入门团队**：LangChain4J → Spring AI → Djl.ai（由易到难）
- **有ML基础团队**：Tribuo → Djl.ai → Deeplearning4j
- **全栈团队**：Spring AI + LangChain4J（覆盖应用层和集成层）

---

## 📚 学习路径

```
阶段1: AI基础认知（1-2周）
├── 了解LLM基本概念（Token、Prompt、Context Window）
├── 理解Embedding和向量检索
└── 阅读: 07_AI框架对比分析.md

阶段2: LLM应用开发（2-4周）
├── LangChain4J快速入门
├── 实现简单的对话机器人
├── Function Calling和工具集成
└── 阅读: 01_LangChain4J.md

阶段3: 企业级AI集成（2-4周）
├── Spring AI集成实践
├── RAG检索增强生成
├── 对话记忆与上下文管理
└── 阅读: 02_Spring AI.md

阶段4: 深度学习部署（4-8周，可选）
├── Djl.ai模型部署
├── GPU加速推理
├── Deeplearning4j分布式训练
└── 阅读: 04_Djl.ai.md, 03_Deeplearning4j.md
```

---

## 🔗 相关知识库

- [12_AI集成](../12_AI集成/) - Java AI开发实战、LangChain4j详解、RAG应用
- [15_MCP协议](../15_MCP协议/) - MCP协议与Function Calling对比
- [23_技术动态](../23_技术动态/) - AI框架版本更新动态

---

## ✅ 完成状态

本知识库已覆盖2025-2026年主流Java AI框架，包含7个核心框架的详细文档和1个综合对比指南。所有文档均包含框架介绍、核心特性、Java实现示例、应用场景、注意事项和最佳实践六大模块，可作为Java AI开发的一站式参考资料。

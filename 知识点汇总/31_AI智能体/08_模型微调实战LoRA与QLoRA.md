# 模型微调实战LoRA与QLoRA

> PEFT参数高效微调、LoRA原理、LLaMA-Factory实战与数据构建

---

## 📋 目录

1. [微调概述](#1-微调概述)
2. [LoRA原理](#2-lora原理)
3. [QLoRA](#3-qlora)
4. [LLaMA-Factory实战](#4-llama-factory实战)
5. [数据集构建](#5-数据集构建)
6. [微调评估与部署](#6-微调评估与部署)
7. [面试题速查](#7-面试题速查)

---

## 1. 微调概述

### 1.1 为什么需要微调

```
基座模型(如Qwen2.5-7B)的局限:
  1. 通用回答 — 缺乏特定领域深度知识
  2. 格式不固定 — 可能不以期望格式输出
  3. 风格不匹配 — 不符合企业语气/风格
  4. 特定能力弱 — 如特定领域分类/抽取

  微调的价值:
  ┌──────────────────────────────────────────────────┐
  │  场景          │  微调效果                        │
  │  ──────     │  ──────                      │
  │  领域问答      │  注入领域知识，准确率提升20-40%   │
  │  代码生成      │  特定语言/框架代码质量提升        │
  │  文本分类      │  分类准确率显著提升               │
  │  信息抽取      │  结构化提取准确率提升             │
  │  风格定制      │  输出风格符合企业要求             │
  │  格式对齐      │  严格按JSON/特定格式输出          │
  └──────────────────────────────────────────────────┘

  微调 vs RAG:
    RAG: 检索外部知识，不改模型参数
    微调: 修改模型参数，内化能力
    组合: 微调改能力 + RAG补知识(最佳实践)
```

### 1.2 微调方法对比

```
┌──────────────────────────────────────────────────────┐
  │  方法          │  参数量    │  显存      │  效果     │
  │  ──────     │  ────   │  ────   │  ────  │
  │  全量微调      │  100%     │  最高      │  最好     │
  │  LoRA         │  0.1-1%   │  低        │  接近全量 │
  │  QLoRA        │  0.1-1%   │  最低      │  接近LoRA │
  │  Adapter      │  1-5%     │  中        │  略差     │
  │  Prefix Tuning│  0.1%     │  低        │  略差     │
  │  P-Tuning v2  │  0.1%     │  低        │  略差     │
  └──────────────────────────────────────────────────────┘

  推荐: LoRA/QLoRA(性价比最高)
    7B模型LoRA微调: 单卡RTX 4090(24GB)可完成
    70B模型QLoRA微调: 单卡A100(80GB)可完成
```

---

## 2. LoRA原理

### 2.1 低秩分解

```
LoRA(Low-Rank Adaptation) = 用低秩矩阵近似参数更新

  核心思想:
    全量微调: W' = W + ΔW (更新所有参数)
    LoRA: W' = W + B×A (只训练B和A，W冻结)

    W: 原始权重 (d×d，冻结不训练)
    A: 降维矩阵 (r×d，训练)
    B: 升维矩阵 (d×r，训练)
    r: 秩(如8/16/64)，r << d

  ┌──────────────────────────────────────────────┐
  │  原始:  y = W·x          W: d×d = 4096×4096  │
  │                                              │
  │  LoRA: y = W·x + B·A·x                       │
  │         W: 4096×4096 (冻结)                  │
  │         A: r×4096 = 8×4096 (训练)            │
  │         B: 4096×r = 4096×8 (训练)            │
  │                                              │
  │  原始参数: 4096×4096 = 16.7M                 │
  │  LoRA参数: 8×4096 + 4096×8 = 65K (减少256倍) │
  └──────────────────────────────────────────────┘

  为什么有效？
    "过参数化"假说: 大模型权重更新ΔW是低秩的
    → 用低秩矩阵B·A就能很好地近似ΔW
    → 只训练0.1%的参数就能达到接近全量微调的效果
```

### 2.2 LoRA参数

```
LoRA关键参数:

  rank (r):
    r=8  — 轻量，适合简单任务
    r=16 — 默认，大多数场景
    r=64 — 重型，复杂任务
    r越大 → 可训练参数越多 → 效果越好但过拟合风险

  alpha (α):
    缩放因子: 实际缩放 = α/r
    作用: 控制LoRA更新的强度
    经验: α = 2×r (如r=16, α=32)

  target_modules:
    应用LoRA的权重模块
    常见: ["q_proj", "k_proj", "v_proj", "o_proj"]  (注意力层)
    扩展: +["gate_proj", "up_proj", "down_proj"]  (FFN层)
    全量: 所有linear层都加LoRA(效果最好但参数多)

  dropout:
    LoRA层的Dropout(如0.05-0.1)，防止过拟合

  示例(LoRA参数量计算):
    Qwen2.5-7B, r=16, target=all_linear
    总参数: 7B
    LoRA参数: ~50M (约0.7%)
    训练显存: ~16GB (FP16 + LoRA + 优化器)
```

---

## 3. QLoRA

### 3.1 QLoRA原理

```
QLoRA = Quantized LoRA = 4bit量化 + LoRA

  核心改进:
    LoRA: 基座模型FP16 → 需要大显存
    QLoRA: 基座模型4bit(NF4) → 显存大幅降低

  ┌──────────────────────────────────────────────┐
  │  LoRA:   基座(FP16) + LoRA(FP16) + 优化器    │
  │  7B模型: 14GB + 0.1GB + 0.2GB ≈ 15GB        │
  │  70B模型: 140GB → 需要多卡                    │
  │                                              │
  │  QLoRA:  基座(NF4) + LoRA(FP16) + 优化器     │
  │  7B模型: 3.5GB + 0.1GB + 0.2GB ≈ 4GB        │
  │  70B模型: 35GB → 单卡A100(80GB)可行          │
  └──────────────────────────────────────────────┘

  QLoRA三大技术:
    1. NF4量化 — NormalFloat4，信息损失最小的4bit格式
    2. Double Quantization — 量化常数本身也量化(再省0.4bit/参数)
    3. Paged Optimizer — 用CUDA统一内存，防止显存溢出
```

---

## 4. LLaMA-Factory实战

### 4.1 LLaMA-Factory概述

```
LLaMA-Factory — 国产开源微调工具(Web UI + CLI)

  优势:
    1. 零代码 — WebUI可视化微调
    2. 多模型 — 支持LLaMA/Qwen/DeepSeek/Mistral等
    3. 多方法 — SFT/LoRA/QLoRA/DPO/RLHF
    4. 易部署 — pip install一行装好
    5. 中文友好 — 文档和社区都是中文
```

### 4.2 数据准备

```json
// dataset_info.json
{
  "my_dataset": {
    "file_name": "my_train.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}

// my_train.json (Alpaca格式)
[
  {
    "instruction": "请解释Java中的volatile关键字",
    "input": "",
    "output": "volatile是Java中的轻量级同步机制...\n1. 可见性: 写入后立即刷新到主内存...\n2. 有序性: 禁止指令重排序...\n3. 不保证原子性..."
  },
  {
    "instruction": "Java中HashMap和ConcurrentHashMap的区别？",
    "input": "",
    "output": "1. 线程安全: HashMap非线程安全...\n2. 性能: HashMap更快...\n3. 实现方式: ConcurrentHashMap用CAS+ synchronized..."
  }
]

// ShareGPT格式(多轮对话)
[
  {
    "conversations": [
      {"from": "human", "value": "什么是Java的Stream API?"},
      {"from": "gpt", "value": "Stream API是Java 8引入的函数式数据处理API..."},
      {"from": "human", "value": "和for循环比有什么优势?"},
      {"from": "gpt", "value": "1. 声明式编程...2. 并行处理...3. 链式操作..."}
    ]
  }
]
```

### 4.3 命令行微调

```bash
# LoRA微调Qwen2.5-7B
llamafactory-cli train \
    --stage sft \
    --do_train True \
    --model_name_or_path Qwen/Qwen2.5-7B-Instruct \
    --dataset my_dataset \
    --template qwen \
    --finetuning_type lora \
    --lora_target all \
    --lora_rank 16 \
    --lora_alpha 32 \
    --output_dir ./output/qwen-lora \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 4 \
    --learning_rate 5e-5 \
    --num_train_epochs 3 \
    --max_samples 100000 \
    --cutoff_len 2048 \
    --bf16 True \
    --save_steps 500 \
    --logging_steps 10 \
    --warmup_steps 100

# QLoRA微调(加量化参数)
llamafactory-cli train \
    --stage sft \
    --do_train True \
    --model_name_or_path Qwen/Qwen2.5-7B-Instruct \
    --dataset my_dataset \
    --template qwen \
    --finetuning_type lora \
    --lora_target all \
    --lora_rank 16 \
    --quantization_bit 4 \
    --quantization_method bits \
    --output_dir ./output/qwen-qlora \
    --per_device_train_batch_size 2 \
    --gradient_accumulation_steps 8 \
    --learning_rate 5e-5 \
    --num_train_epochs 3 \
    --bf16 True
```

### 4.4 WebUI微调

```bash
# 启动WebUI
llamafactory-cli webui

# 浏览器打开 http://localhost:7860
# 1. 选择模型 (Qwen2.5-7B-Instruct)
# 2. 选择微调方法 (LoRA)
# 3. 选择数据集
# 4. 设置参数 (r=16, alpha=32, lr=5e-5, epochs=3)
# 5. 点击"开始"
# 6. 观察Loss曲线
# 7. 训练完成后导出模型
```

---

## 5. 数据集构建

### 5.1 数据质量准则

```
微调数据质量 > 数量:

  LIMA论文: 1000条高质量数据 > 52000条低质量数据

  质量标准:
    1. 正确性 — 回答必须事实正确
    2. 多样性 — 覆盖不同子话题和难度
    3. 一致性 — 格式/风格一致
    4. 相关性 — 与目标领域强相关
    5. 复杂度梯度 — 包含简单/中等/困难

  数据量参考:
    领域问答: 1000-10000条
    格式对齐: 500-2000条
    代码生成: 2000-10000条
    分类任务: 5000-50000条
```

### 5.2 数据生成

```
用大模型生成微调数据:

  1. Seed指令 → GPT-5/Claude生成 → 质量过滤
  2. Evol-Instruct: 逐步增加复杂度
  3. 回译增强: 中文→英文→中文(增加多样性)

  示例(Self-Instruct流程):
    1. 手写100条种子指令
    2. 用GPT-5基于种子生成更多指令
    3. 去重(语义去重)
    4. 用GPT-5生成回答
    5. 质量过滤(规则+LLM评分)
    6. 最终得到训练数据
```

---

## 6. 微调评估与部署

### 6.1 评估

```
微调效果评估:

  1. 训练指标
     Loss曲线 — 持续下降，不过早收敛
     梯度范数 — 不爆炸/不消失

  2. 自动评估
     困惑度(PPL) — 越低越好
     MMLU/C-Eval — 知识能力
     人工构建测试集 — 领域准确率

  3. 人工评估
     抽样100条 → 人工打分(1-5)
     对比基座模型 → 提升多少

  4. LLM-as-Judge
     用GPT-5评估微调模型输出质量
     对比微调前后

  过拟合判断:
    训练Loss↓ 但 评估Loss↑ → 过拟合
    解决: 减少Epoch(2-3足够) / 增加数据 / 加Dropout
```

### 6.2 LoRA合并与部署

```bash
# 1. 合并LoRA到基座模型
llamafactory-cli export \
    --model_name_or_path Qwen/Qwen2.5-7B-Instruct \
    --adapter_name_or_path ./output/qwen-lora \
    --template qwen \
    --finetuning_type lora \
    --export_dir ./output/qwen-merged \
    --export_size 4 \
    --export_legacy_format False

# 2. 用vLLM部署合并后的模型
python -m vllm.entrypoints.openai.api_server \
    --model ./output/qwen-merged \
    --trust-remote-code \
    --port 8000

# 3. 或用Ollama部署
# 创建Modelfile
# FROM ./output/qwen-merged
# ollama create my-qwen -f Modelfile
# ollama run my-qwen
```

---

## 7. 面试题速查

**Q1: LoRA的原理？**

```
用低秩矩阵B×A近似权重更新ΔW
W' = W + B×A (W冻结，只训练B和A)
r(秩) << d(原始维度) → 参数量减少99%+
效果接近全量微调，显存大幅降低
```

**Q2: QLoRA和LoRA的区别？**

```
LoRA: 基座FP16 + LoRA训练
QLoRA: 基座4bit(NF4) + LoRA训练
QLoRA显存降至LoRA的1/4
7B只需4GB显存，70B只需35GB(单卡A100)
效果接近LoRA
```

**Q3: LoRA的rank怎么选？**

```
r=8: 简单任务(格式对齐)
r=16: 默认(大多数场景)
r=64: 复杂任务(领域知识注入)
r越大可学越多但过拟合风险
alpha通常=2×r
```

**Q4: 微调数据怎么构建？**

```
质量>数量: 1000条高质量 > 50000条低质量
来源: 人工标注(最好) / Self-Instruct(GPT生成) / 公开数据集
格式: Alpaca(instruction/input/output)或ShareGPT(多轮)
质量: 正确/多样/一致/相关
数量: 领域问答1000-10000条够用
```

**Q5: 如何判断微调过拟合？**

```
训练Loss↓ 但 评估Loss↑ → 过拟合
解决: 减Epoch(2-3) / 增数据 / 加Dropout / 减rank
正常: 训练Loss和评估Loss都下降并趋于平稳
```

---

*最后更新: 2026-07-13*

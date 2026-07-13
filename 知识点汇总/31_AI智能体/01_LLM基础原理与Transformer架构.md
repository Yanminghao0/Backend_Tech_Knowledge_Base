# LLM基础原理与Transformer架构

> 从神经网络到Transformer，从注意力机制到GPT/LLaMA架构，彻底理解大模型工作原理

---

## 📋 目录

1. [神经网络基础](#1-神经网络基础)
2. [自然语言处理演进](#2-自然语言处理演进)
3. [注意力机制](#3-注意力机制)
4. [Transformer架构](#4-transformer架构)
5. [Decoder-only架构(GPT/LLaMA)](#5-decoder-only架构gptllama)
6. [大模型关键组件](#6-大模型关键组件)
7. [主流大模型架构对比](#7-主流大模型架构对比)
8. [面试题速查](#8-面试题速查)

---

## 1. 神经网络基础

### 1.1 基本结构

```
神经网络 = 多层神经元连接的有向图

  输入层(Input Layer) → 隐藏层(Hidden Layer) → 输出层(Output Layer)

  ┌───┐     ┌───┐     ┌───┐
  │x₁ │────→│h₁ │────→│y₁ │
  ├───┤╲   ╱├───┤     └───┘
  │x₂ │──×──│h₂ │
  ├───┤╱   ╲├───┤
  │x₃ │────→│h₃ │
  └───┘     └───┘

  每个连接有一个权重w和偏置b:
    output = activation(w₁·x₁ + w₂·x₂ + ... + b)

  训练 = 不断调整w和b，使输出接近目标
```

```python
# 最简单的神经元(Python伪代码)
import numpy as np

class Neuron:
    def __init__(self, n_inputs):
        self.weights = np.random.randn(n_inputs)
        self.bias = np.random.randn()

    def forward(self, inputs):
        # 加权求和 + 激活函数
        z = np.dot(self.weights, inputs) + self.bias
        return self.relu(z)

    def relu(self, x):
        return max(0, x)

# 单个神经元处理3个输入
neuron = Neuron(3)
output = neuron.forward([1.0, 2.0, 3.0])
print(output)
```

### 1.2 激活函数

```
为什么需要激活函数？
  没有激活函数 → 多层线性变换 = 一层线性变换 → 无法学习非线性关系

  ┌──────────────────────────────────────────────────────┐
  │  激活函数    │  公式                    │  用于        │
  │  ──────    │  ──────                 │  ────      │
  │  ReLU       │  max(0, x)               │  隐藏层(最常用)│
  │  GELU       │  x·Φ(x)                  │  BERT/GPT   │
  │  SwiGLU     │  Swish(x₁W)⊗(x₂V)       │  LLaMA/Qwen │
  │  Sigmoid    │  1/(1+e⁻ˣ)               │  二分类输出  │
  │  Tanh       │  (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ)      │  RNN        │
  │  Softmax    │  eˣⁱ/Σeˣʲ                │  多分类输出  │
  └──────────────────────────────────────────────────────┘

  ReLU (最常用):
    x > 0 → x        ────/
    x ≤ 0 → 0        ___/
    优点: 计算简单、梯度不消失
    缺点: 负数区域梯度为0(死亡ReLU)

  GELU (BERT/GPT用):
    近似: 0.5x(1 + tanh(√(2/π)(x + 0.044715x³)))
    比ReLU更平滑，在0附近有曲率

  SwiGLU (LLaMA用):
    SwiGLU(x) = Swish(xW) ⊗ (xV)
    Swish(x) = x · sigmoid(x)
    带门控机制，比GELU效果好但参数翻倍
```

### 1.3 损失函数

```
损失函数(Loss Function) = 衡量预测值与真实值的差距

  ┌──────────────────────────────────────────────────┐
  │  损失函数              │  公式          │  用途    │
  │  ────────           │  ────        │  ────  │
  │  交叉熵(CE)            │  -Σyᵢlog(pᵢ)  │  分类/语言模型│
  │  均方误差(MSE)         │  Σ(y-ŷ)²/n    │  回归    │
  │  负对数似然(NLL)        │  -log(p_y)    │  分类    │
  └──────────────────────────────────────────────────┘

  语言模型的核心损失: 交叉熵
    L = -Σ log P(token_i | token_{<i})

    含义: 预测下一个token的负对数概率
    Loss越低 → 模型预测越准确

  困惑度(Perplexity) = exp(交叉熵)
    PPL = exp(L)
    PPL越低越好
    PPL=1表示完全确定，PPL=词表大小表示完全随机
```

### 1.4 归一化

```
归一化(Normalization) = 加速训练 + 稳定梯度

  LayerNorm (GPT/BERT用):
    对每个样本的所有特征做归一化
    mean = mean(x), std = std(x)
    output = (x - mean) / std * γ + β

  RMSNorm (LLaMA/Qwen用):
    去掉均值，只用均方根归一化
    rms = sqrt(mean(x²))
    output = x / rms * γ

    比LayerNorm少算一个均值，速度快约10-50%
    效果与LayerNorm相当

  ┌────────────────────────────────────────────────┐
  │  LayerNorm:  y = (x - μ)/σ × γ + β             │
  │  RMSNorm:    y = x/√(mean(x²)) × γ             │
  │                                                │
  │  LayerNorm在Transformer中:                     │
  │    ① Pre-Norm: x = x + Sublayer(LN(x))         │
  │    ② Post-Norm: x = LN(x + Sublayer(x))        │
  │  现代大模型用Pre-Norm(训练更稳定)                │
  └────────────────────────────────────────────────┘
```

### 1.5 残差连接

```
残差连接(Residual Connection) = 跳跃连接 + 恒等映射

  ┌──────┐
  │ 输入x │────┬──────→ 输出
  └──┬───┘    │
     ↓        │
  ┌──┴───┐    │
  │Sublayer│  │
  └──┬───┘    │
     ↓        │
     └─── + ──┘

  output = x + Sublayer(x)

  作用:
  1. 缓解梯度消失 — 梯度可以直接通过跳跃连接回传
  2. 信息高速公路 — 信息可以绕过子层直接到达输出
  3. 使深层网络可训练 — 没有它几十层就训不动

  Transformer中两个残差连接:
    ① x = x + Attention(LN(x))     // 注意力子层
    ② x = x + FFN(LN(x))           // 前馈网络子层
```

---

## 2. 自然语言处理演进

### 2.1 发展历程

```
NLP发展时间线:

  ┌──────────────────────────────────────────────────────┐
  │  时代          │  方法           │  代表               │
  │  ────        │  ────         │  ────             │
  │  2000s前      │  规则+统计      │  TF-IDF/隐马尔可夫   │
  │  2003         │  神经语言模型    │  NNLM(Bengio)       │
  │  2013         │  词向量         │  Word2Vec           │
  │  2014         │  序列模型       │  RNN/LSTM/GRU       │
  │  2014         │  Seq2Seq        │  Encoder-Decoder    │
  │  2015         │  注意力机制      │  Bahdanau Attention │
  │  2017         │  Transformer    │  Attention Is All...│
  │  2018         │  预训练         │  BERT/GPT           │
  │  2020         │  大模型         │  GPT-3(175B)        │
  │  2022         │  指令对齐        │  InstructGPT/RLHF   │
  │  2023         │  开源大模型      │  LLaMA/Qwen         │
  │  2024-2025    │  MoE/多模态     │  DeepSeek-V3/GPT-4o │
  └──────────────────────────────────────────────────────┘
```

### 2.2 词向量演进

```
词向量(Word Embedding) = 用向量表示词的语义

  One-hot编码:
    "猫" = [1,0,0,0,...]
    "狗" = [0,1,0,0,...]
    问题: 维度=词表大小(几万到几十万)，且无法表达语义相似度

  Word2Vec (2013):
    "猫" = [0.2, -0.5, 0.8, ...]  (300维)
    "狗" = [0.3, -0.4, 0.7, ...]  (相似)
    "汽车" = [-0.8, 0.1, -0.3, ...]  (不相似)
    核心思想: 上下文相似的词，语义相似
    著名等式: king - man + woman ≈ queen

  BERT嵌入 (2018):
    上下文相关 — "苹果"在"吃苹果"和"苹果手机"中向量不同
    Word2Vec是静态的，BERT是动态的

  LLM嵌入 (GPT/LLaMA):
    输入token ID → 嵌入层 → 向量序列
    嵌入维度: 768(GPT-2) / 4096(LLaMA-7B) / 8192(LLaMA-70B)
    嵌入层 = 查表操作(lookup table)
      [token_id=5] → 查表 → 第5行向量
```

### 2.3 分词器(Tokenizer)

```
分词 = 文本 → token序列 → token ID序列

  ┌──────────────────────────────────────────────────────┐
  │  分词器        │  原理              │  使用模型         │
  │  ──────      │  ────           │  ──────       │
  │  BPE          │  字节对编码        │  GPT系列/LLaMA   │
  │  WordPiece    │  类似BPE           │  BERT            │
  │  SentencePiece│  子词单元          │  T5/LLaMA/Qwen  │
  │  Tiktoken     │  BPE的优化实现     │  GPT-4/Claude   │
  └──────────────────────────────────────────────────────┘

  BPE(Byte Pair Encoding)分词过程:
    1. 初始化: 每个字符是一个token
       "hello" → ['h','e','l','l','o']
    2. 统计高频相邻pair，合并为新token
       'l'+'l' → 'll'
    3. 重复直到达到目标词表大小
    4. 最终: "hello" → ['he','ll','o'] (3个token)

  Token计算:
    中文: 1个汉字 ≈ 1-2个token
    英文: 1个单词 ≈ 1-1.5个token
    代码: 1行代码 ≈ 5-15个token

  估算:
    "你好世界" → 约4-6个token
    "Hello World" → 约2个token
    一页A4纸(500字) → 约800-1000个token

  成本计算:
    GPT-5: 输入$5/M token, 输出$15/M token
    DeepSeek-V3: 输入$0.27/M token, 输出$1.1/M token
    → DeepSeek比GPT-5便宜约15-20倍
```

---

## 3. 注意力机制

### 3.1 直觉理解

```
注意力(Attention) = 让模型"关注"输入中重要的部分

  类比: 在图书馆找书
    Q(Query) = 你的搜索关键词 → "Java并发编程"
    K(Key) = 每本书的标题/标签 → "Java核心", "Python入门", "Java并发实战"
    V(Value) = 书的内容

    匹配度(Q·K): "Java并发" 与 "Java并发实战" 匹配度高
    → 给这本书更高的注意力权重
    → 最终得到的V就是这本书的内容

  在语言模型中:
    Q = "它" 这个代词指代什么？
    K = 每个词的语义特征
    V = 每个词的信息
    Attention("它", 其他词) = 加权求和(V)，权重 = softmax(Q·K)
```

### 3.2 数学公式

```
缩放点积注意力(Scaled Dot-Product Attention):

  Attention(Q, K, V) = softmax(QKᵀ / √dₖ) · V

  分解:
    1. Q · Kᵀ → 相似度矩阵 (n×n)
       Q = [q₁, q₂, ..., qₙ]  (n个查询)
       K = [k₁, k₂, ..., kₙ]  (n个键)
       QKᵀ[i][j] = qᵢ · kⱼ  (第i个查询与第j个键的点积)

    2. / √dₖ → 缩放(防止点积过大导致梯度消失)
       dₖ = 键的维度(如64)

    3. softmax → 归一化为概率分布(权重和=1)
       每个查询对所有键的注意力权重

    4. · V → 加权求和
       output[i] = Σ attention_weight[i][j] · vⱼ

  示例(简化):
    "猫 追 老 鼠" (4个词)

    Q = [[q猫],[q追],[q老],[q鼠]]
    K = [[k猫],[k追],[k老],[k鼠]]
    V = [[v猫],[v追],[v老],[v鼠]]

    Attention("猫"):
      weights = softmax([q猫·k猫, q猫·k追, q猫·k老, q猫·k鼠] / √d)
      = [0.5, 0.2, 0.2, 0.1]  (猫最关注自己)
      output = 0.5·v猫 + 0.2·v追 + 0.2·v老 + 0.1·v鼠
```

### 3.3 多头注意力

```
多头注意力(Multi-Head Attention) = 多组Q/K/V并行计算

  为什么需要多头？
    单头注意力: 只能学到一种关注模式
    多头注意力: 不同头学到不同模式
      头1: 关注语法关系(主谓宾)
      头2: 关注语义关系(同义/反义)
      头3: 关注位置关系(相邻词)
      ...

  实现:
    将d_model维度拆成h个头，每个头 d_k = d_model/h

    MultiHead(Q,K,V) = Concat(head₁, head₂, ..., head_h) · W_O

    head_i = Attention(Q·W_Q^i, K·W_K^i, V·W_V^i)

  示例(LLaMA-7B):
    d_model = 4096
    n_heads = 32
    d_k = 4096/32 = 128
    每个头用128维的Q/K/V计算注意力

  GQA(Grouped Query Attention, LLaMA-2/3):
    传统MHA: 每个头有独立的K/V → KV Cache大
    MQA: 所有头共享1组K/V → KV Cache小但质量差
    GQA: 分组共享K/V → 平衡(如8组K/V服务32个头)
```

```python
# 注意力机制Python实现(简化)
import numpy as np

def attention(Q, K, V, mask=None):
    d_k = K.shape[-1]
    # 1. 计算注意力分数
    scores = np.matmul(Q, K.transpose(-2, -1)) / np.sqrt(d_k)
    # scores: [batch, heads, seq_len, seq_len]

    # 2. 应用mask(因果掩码，防止看未来)
    if mask is not None:
        scores = np.where(mask == 0, -1e9, scores)

    # 3. Softmax归一化
    weights = softmax(scores, axis=-1)

    # 4. 加权求和
    output = np.matmul(weights, V)
    return output

def softmax(x, axis=-1):
    exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)

# 因果掩码(下三角矩阵)
# 1 0 0 0    → 只能看到自己
# 1 1 0 0    → 能看到前2个
# 1 1 1 0    → 能看到前3个
# 1 1 1 1    → 能看到全部
mask = np.tril(np.ones((4, 4)))
```

---

## 4. Transformer架构

### 4.1 整体结构

```
Transformer (2017, "Attention Is All You Need")

  原始Transformer = Encoder + Decoder

  ┌──────────────────────────────────────────────┐
  │                输入                           │
  │                  ↓                            │
  │          ┌───────────────┐                    │
  │          │  Token Embedding│                   │
  │          │  + Position Enc │                   │
  │          └───────┬───────┘                    │
  │                  ↓                            │
  │     ┌────────────────────────┐                │
  │     │   Encoder Block × N    │                │
  │     │  ┌─────────────────┐   │                │
  │     │  │ Multi-Head Attn │   │                │
  │     │  │   (双向)        │   │                │
  │     │  └────────┬────────┘   │                │
  │     │           ↓            │                │
  │     │  ┌─────────────────┐   │                │
  │     │  │   Feed Forward  │   │                │
  │     │  └────────┬────────┘   │                │
  │     └───────────┼────────────┘                │
  │                 ↓                             │
  │     ┌────────────────────────┐                │
  │     │   Decoder Block × N    │                │
  │     │  ┌─────────────────┐   │                │
  │     │  │ Masked MHA      │   │  ← 因果掩码    │
  │     │  │   (单向)        │   │                │
  │     │  └────────┬────────┘   │                │
  │     │           ↓            │                │
  │     │  ┌─────────────────┐   │                │
  │     │  │ Cross-Attention │   │  ← 关注Encoder │
  │     │  └────────┬────────┘   │                │
  │     │           ↓            │                │
  │     │  ┌─────────────────┐   │                │
  │     │  │   Feed Forward  │   │                │
  │     │  └────────┬────────┘   │                │
  │     └───────────┼────────────┘                │
  │                 ↓                             │
  │          ┌────────────┐                       │
  │          │  Linear+   │                       │
  │          │  Softmax   │                       │
  │          └─────┬──────┘                       │
  │                ↓                              │
  │            输出概率                            │
  └──────────────────────────────────────────────┘
```

### 4.2 三种架构变体

```
┌──────────────────────────────────────────────────────────┐
  │  架构          │  结构         │  代表      │  特点     │
  │  ──────      │  ────       │  ────    │  ────   │
  │  Encoder-only  │  只有编码器   │  BERT      │  双向理解  │
  │  Decoder-only  │  只有解码器   │  GPT/LLaMA │  单向生成  │
  │  Enc-Dec       │  编码器+解码器 │  T5/BART   │  翻译/摘要 │
  └──────────────────────────────────────────────────────────┘

  为什么Decoder-only胜出？
    1. 生成能力强 — 自回归天生适合文本生成
    2. 预训练效率 — CLM目标比MLM更高效
    3. 规模化好 — Scaling Laws验证Decoder-only最优
    4. 统一架构 — 生成+理解统一为Next Token Prediction
    5. 涌现能力 — 大规模后展现出理解和推理能力

  BERT(Encoder-only):
    双向注意力 — 每个词能看到前后所有词
    预训练: MLM(掩码语言建模) — 完形填空
    擅长: 文本分类、NER、问答(理解类任务)
    不擅长: 文本生成

  GPT(Decoder-only):
    因果注意力 — 每个词只能看到前面的词
    预训练: CLM(因果语言建模) — 预测下一个token
    擅长: 文本生成、对话、代码(生成类任务)
    大规模后也擅长理解类任务

  T5(Enc-Dec):
    Encoder理解输入 + Decoder生成输出
    预训练: 填空任务(文本到文本)
    擅长: 翻译、摘要(输入→输出映射)
```

### 4.3 位置编码

```
为什么需要位置编码？
  Transformer的注意力机制本身没有位置感知
  打乱输入顺序 → 注意力输出相同 → 需要位置信息

  ┌──────────────────────────────────────────────────────┐
  │  位置编码          │  原理          │  使用模型        │
  │  ──────         │  ────       │  ──────     │
  │  绝对位置(正弦)    │  sin/cos函数   │  原始Transformer │
  │  可学习位置        │  训练学习      │  GPT-2/BERT     │
  │  ALiBi           │  注意力偏置     │  BLOOM/MPT      │
  │  RoPE旋转位置     │  旋转矩阵      │  LLaMA/Qwen/DS  │
  └──────────────────────────────────────────────────────┘

  RoPE(Rotary Position Embedding) — 主流大模型标配:
    核心思想: 通过旋转矩阵将位置信息编码到Q/K中
    优势:
    1. 相对位置感知 — 只关心token间的相对距离
    2. 长度外推 — 训练4K可推理到32K(配合缩放)
    3. 计算高效 — 只需矩阵乘法

    公式(简化):
      q_rotated = q * cos(mθ) + rotate_half(q) * sin(mθ)
      k_rotated = k * cos(nθ) + rotate_half(k) * sin(nθ)
      → q_rotated · k_rotated 只依赖 (m-n) 即相对位置

  ALiBi(Attention with Linear Biases):
    在注意力分数上加一个与距离成正比的偏置
    attention = softmax(QKᵀ - m·|i-j|) · V
    优势: 无需位置编码嵌入，直接外推
    但效果不如RoPE，已较少使用
```

### 4.4 前馈网络(FFN)

```
FFN(Feed-Forward Network) — 每个位置独立的两层全连接

  FFN(x) = activation(x·W₁ + b₁)·W₂ + b₂

  传统Transformer:
    FFN(x) = ReLU(x·W₁)·W₂
    d_model → d_ff(4×d_model) → d_model
    如: 512 → 2048 → 512

  GPT-2用GELU:
    FFN(x) = GELU(x·W₁)·W₂

  LLaMA用SwiGLU:
    FFN(x) = Swish(x·W_gate) ⊗ (x·W_up) · W_down
    三层: d_model → d_ff → d_ff → d_model
    比传统FFN多一个门控，效果好但参数多1.5倍

  作用:
    1. 非线性变换 — 注意力是线性的，FFN提供非线性
    2. 知识存储 — FFN层存储了大量知识(事实记忆)
    3. 特征变换 — 将注意力聚合的信息进一步加工
```

---

## 5. Decoder-only架构(GPT/LLaMA)

### 5.1 整体结构

```
GPT/LLaMA架构(Decoder-only):

  ┌────────────────────────────────────────────┐
  │  Token IDs: [1, 5, 12, 8, 3]               │
  │       ↓                                     │
  │  ┌──────────────┐                          │
  │  │  Embedding   │  token ID → 向量          │
  │  │  (查表)      │  [1]→v₁ [5]→v₂ ...       │
  │  └──────┬───────┘                          │
  │         ↓                                   │
  │  ┌──────────────┐                          │
  │  │  + RoPE      │  位置编码注入Q/K           │
  │  └──────┬───────┘                          │
  │         ↓                                   │
  │  ┌──────────────────────────────┐          │
  │  │  Transformer Block × N       │          │
  │  │  ┌────────────────────────┐  │          │
  │  │  │  RMSNorm               │  │          │
  │  │  │  ↓                      │  │          │
  │  │  │  Causal Self-Attention  │  │          │
  │  │  │  (GQA + RoPE + Mask)   │  │          │
  │  │  │  ↓                      │  │          │
  │  │  │  Residual Connection    │  │          │
  │  │  │  ↓                      │  │          │
  │  │  │  RMSNorm               │  │          │
  │  │  │  ↓                      │  │          │
  │  │  │  SwiGLU FFN            │  │          │
  │  │  │  ↓                      │  │          │
  │  │  │  Residual Connection    │  │          │
  │  │  └────────────────────────┘  │          │
  │  └──────────┬───────────────────┘          │
  │             ↓                               │
  │  ┌──────────────┐                          │
  │  │  RMSNorm     │                          │
  │  └──────┬───────┘                          │
  │         ↓                                   │
  │  ┌──────────────┐                          │
  │  │  LM Head     │  向量 → 词表概率           │
  │  │  (Linear)    │  [d_model] → [vocab_size] │
  │  └──────┬───────┘                          │
  │         ↓                                   │
  │  ┌──────────────┐                          │
  │  │  Softmax     │  概率分布                  │
  │  └──────┬───────┘                          │
  │         ↓                                   │
  │  下一个Token概率: [0.01, 0.02, ..., 0.85]  │
  │  → 选概率最高的token(或采样)                │
  └────────────────────────────────────────────┘
```

### 5.2 自回归生成

```
自回归(Autoregressive)生成 = 逐token生成

  输入: "Java是"
  目标: 续写

  Step 1: 输入 [Java, 是] → 模型 → 预测下一个 → "一"
  Step 2: 输入 [Java, 是, 一] → 模型 → 预测下一个 → "门"
  Step 3: 输入 [Java, 是, 一, 门] → 模型 → 预测下一个 → "编"
  Step 4: 输入 [Java, 是, 一, 门, 编] → 模型 → 预测下一个 → "程"
  Step 5: 输入 [Java, 是, 一, 门, 编, 程] → 模型 → 预测下一个 → "语"
  ...
  直到生成结束符(<EOS>)或达到长度限制

  每一步:
    输入n个token → 计算n个位置的注意力 → 只取最后一个位置的输出 → 预测第n+1个token

  KV Cache加速:
    Step 1: 计算所有Q/K/V，缓存K/V
    Step 2: 只计算新token的Q，复用缓存的K/V → 只算1个位置
    Step 3: 同上
    → 从O(n²)降到O(n)每步

  采样策略:
    Greedy: 选概率最高的token → 确定性输出
    Temperature: softmax(logits/T) → T越高越随机
    Top-k: 只从概率最高的k个中选
    Top-p(Nucleus): 从累积概率≥p的最小集合中选
    推荐: Temperature=0.7 + Top-p=0.9
```

### 5.3 因果掩码

```
因果掩码(Causal Mask) = 防止看到未来的token

  ┌──────────────────────────────────────┐
  │  原始注意力(双向):                    │
  │      词1   词2   词3   词4            │
  │  词1  ✓    ✓    ✓    ✓               │
  │  词2  ✓    ✓    ✓    ✓               │
  │  词3  ✓    ✓    ✓    ✓               │
  │  词4  ✓    ✓    ✓    ✓               │
  │  → 每个词能看到所有词(BERT)           │
  │                                      │
  │  因果掩码(单向):                      │
  │      词1   词2   词3   词4            │
  │  词1  ✓    ✗    ✗    ✗               │
  │  词2  ✓    ✓    ✗    ✗               │
  │  词3  ✓    ✓    ✓    ✗               │
  │  词4  ✓    ✓    ✓    ✓               │
  │  → 每个词只能看到自己和之前的词(GPT)   │
  └──────────────────────────────────────┘

  实现: 上三角矩阵填-∞
    mask = [[ 0,  -∞, -∞, -∞],
            [ 0,   0, -∞, -∞],
            [ 0,   0,  0, -∞],
            [ 0,   0,  0,  0]]

    scores = QKᵀ/√d + mask
    softmax(scores) → 被mask的位置权重=0
```

---

## 6. 大模型关键组件

### 6.1 KV Cache

```
KV Cache = 缓存历史token的Key和Value，避免重复计算

  没有KV Cache:
    Step 1: 输入[t1] → 计算[t1的Q,K,V] → 输出t2
    Step 2: 输入[t1,t2] → 计算[t1,t2的Q,K,V] → 输出t3
    Step 3: 输入[t1,t2,t3] → 计算[t1,t2,t3的Q,K,V] → 输出t4
    → t1的K/V被重复计算了3次!

  有KV Cache:
    Step 1: 输入[t1] → 计算Q1,K1,V1 → 缓存{K1,V1} → 输出t2
    Step 2: 输入[t2] → 计算Q2,K2,V2 → 缓存{K1,V1,K2,V2} → 输出t3
    Step 3: 输入[t3] → 计算Q3,K3,V3 → 缓存{K1,V1,K2,V2,K3,V3} → 输出t4
    → 每步只计算新token的Q,K,V，复用历史K,V

  KV Cache显存计算:
    KV Cache大小 = 2 × n_layers × n_kv_heads × d_head × seq_len × batch × dtype_size

    LLaMA-7B示例:
      n_layers = 32, n_kv_heads = 32(GQA=8), d_head = 128
      seq_len = 4096, batch = 1, dtype = FP16(2字节)
      KV Cache = 2 × 32 × 32 × 128 × 4096 × 2 = 2GB

    LLaMA-70B示例:
      n_layers = 80, n_kv_heads = 8(GQA), d_head = 128
      seq_len = 4096, batch = 1
      KV Cache = 2 × 80 × 8 × 128 × 4096 × 2 = 1.3GB

    → GQA大幅减少KV Cache显存!
```

### 6.2 MoE混合专家

```
MoE(Mixture of Experts) = 稀疏激活，用少量参数处理每个token

  ┌──────────────────────────────────────────────────┐
  │  传统Dense模型:                                   │
  │  每个token经过全部参数                             │
  │  7B模型 → 每个token激活7B参数                     │
  │                                                  │
  │  MoE模型:                                         │
  │  每个token只激活部分专家(如8选2)                    │
  │  Mixtral 8x7B: 总参数47B, 每token激活13B          │
  │  DeepSeek-V3: 总参数671B, 每token激活37B          │
  │  → 总参数大但推理快(激活参数少)                     │
  └──────────────────────────────────────────────────┘

  MoE架构:
    输入x → Router(Gate) → 选Top-K专家 → 专家并行计算 → 加权合并

    Router: W_router · x → [score_1, score_2, ..., score_N]
    选择Top-K个得分最高的专家
    output = Σ (gate_score_i × Expert_i(x))

  示例(DeepSeek-V3):
    256个专家 + 1个共享专家
    每个token选8个专家 + 1个共享专家
    总参数671B，激活37B

  MoE挑战:
    1. 负载均衡 — 防止某些专家过载/闲置
    2. 通信开销 — 多GPU间传输专家输出
    3. 显存占用 — 所有专家参数都在显存
    4. 训练不稳定 — 路由抖动
```

### 6.3 上下文窗口

```
上下文窗口(Context Window) = 模型一次能处理的最大token数

  ┌──────────────────────────────────────────────────┐
  │  模型          │  上下文窗口  │  显存(KV Cache)   │
  │  ────        │  ────────  │  ──────         │
  │  GPT-3        │  2K         │  -               │
  │  GPT-4 Turbo  │  128K       │  -               │
  │  GPT-5        │  1M         │  -               │
  │  Claude 3     │  200K       │  -               │
  │  Claude 4     │  500K       │  -               │
  │  Qwen2.5      │  128K       │  -               │
  │  LLaMA 3.1    │  128K       │  -               │
  │  DeepSeek-V3  │  128K       │  -               │
  └──────────────────────────────────────────────────┘

  上下文窗口的影响:
    1. 显存 — KV Cache与序列长度成正比
    2. 速度 — 注意力计算O(n²)
    3. 成本 — 输入token按量计费
    4. 效果 — 过长上下文可能"遗忘"中间内容(Lost in the Middle)

  长上下文扩展技术:
    1. RoPE缩放 — 调整RoPE频率，4K→32K
    2. YaRN — 分段插值，外推效果好
    3. NTK-aware — 自适应频率缩放
    4. 长文本微调 — 用长文本数据SFT
    5. KV Cache压缩 — 丢弃不重要的KV(StreamingLLM/H2O)
```

---

## 7. 主流大模型架构对比

### 7.1 架构参数对比

```
┌──────────────────────────────────────────────────────────────┐
  │  参数          │  GPT-4    │  LLaMA-3  │  Qwen2.5  │  DeepSeek-V3│
  │  ──────      │  ──────  │  ──────  │  ──────  │  ──────── │
  │  架构          │  Decoder  │  Decoder  │  Decoder  │  Decoder    │
  │  参数量        │  ~1.8T    │  70B      │  72B      │  671B(37B激活)│
  │  层数          │  ~120     │  80       │  80       │  61         │
  │  d_model       │  ~12288   │  8192     │  8192     │  7168       │
  │  注意力头数    │  ~96      │  64       │  64       │  128        │
  │  KV头数(GQA)   │  ?       │  8        │  8        │  128(MLA)   │
  │  d_head        │  128      │  128      │  128      │  192        │
  │  FFN维度       │  ?       │  28672    │  29568    │  MoE        │
  │  上下文窗口    │  128K     │  128K     │  128K     │  128K       │
  │  位置编码      │  ?       │  RoPE     │  RoPE     │  RoPE       │
  │  归一化        │  ?       │  RMSNorm  │  RMSNorm  │  RMSNorm    │
  │  激活函数      │  ?       │  SwiGLU   │  SwiGLU   │  SwiGLU     │
  │  专家数        │  MoE?     │  无       │  无       │  256+1共享  │
  │  词表大小      │  ~100K    │  128K     │  152K     │  129K       │
  └──────────────────────────────────────────────────────────────┘

  DeepSeek-V3特殊: MLA(Multi-head Latent Attention)
    将KV Cache压缩到低维潜空间，大幅减少KV Cache显存
    KV Cache只需传统MHA的1/4
```

### 7.2 模型选型建议

```
按场景选型(2026年):

  ┌──────────────────────────────────────────────────────────┐
  │  场景          │  闭源(API)       │  开源(本地)          │
  │  ──────      │  ──────        │  ──────           │
  │  最强推理      │  GPT-5/Claude4   │  DeepSeek-R1        │
  │  代码生成      │  Claude 4        │  DeepSeek-V3        │
  │  中文场景      │  通义千问3        │  Qwen2.5-72B        │
  │  多模态        │  GPT-4o          │  Qwen-VL-Max        │
  │  低成本        │  DeepSeek-V3 API │  Qwen2.5-7B(本地)   │
  │  Agent         │  Claude 4/GPT-5  │  Qwen2.5-72B        │
  │  微调基座      │  —              │  Qwen2.5-7B/14B     │
  │  嵌入模型      │  text-emb-3      │  BGE-M3              │
  │  Rerank       │  Cohere Rerank   │  bge-reranker-v2    │
  └──────────────────────────────────────────────────────────┘

  按规模选型:
    单卡(24GB): Qwen2.5-7B(Q4) / LLaMA-3-8B(Q4)
    单卡(80GB): Qwen2.5-14B(FP16) / 7B(FP16)
    4卡(A100): Qwen2.5-72B(Q4) / LLaMA-3-70B(Q4)
    8卡(A100): DeepSeek-V3(Q4) / Qwen2.5-72B(FP16)
```

---

## 8. 面试题速查

**Q1: Transformer为什么比RNN好？**

```
1. 并行性 — Transformer可并行处理所有位置，RNN必须串行
2. 长距离依赖 — 注意力直接连接任意两个位置，RNN梯度消失
3. 可扩展性 — Transformer容易堆叠到很深很大
4. 表达能力 — 多头注意力从多维度建模关系
```

**Q2: 注意力机制的Q/K/V分别是什么？**

```
Q(Query) = 当前token"想知道什么"
K(Key) = 其他token"有什么信息"
V(Value) = 其他token"的具体内容"
Attention = softmax(QKᵀ/√d)·V → 按相关度加权聚合信息
```

**Q3: 为什么需要多头注意力？**

```
单头只能学一种关注模式
多头从不同子空间学习不同模式(语法/语义/位置)
头数选择: 8/16/32/64，太多则每个头维度太小
GQA折中: 查询多头但共享K/V头(省KV Cache)
```

**Q4: RoPE位置编码的原理？**

```
通过旋转矩阵将位置信息注入Q/K
q_m = q·cos(mθ) + rotate(q)·sin(mθ)
k_n = k·cos(nθ) + rotate(k)·sin(nθ)
q_m·k_n 只依赖(m-n) → 天然的相对位置编码
优势: 可外推(配合缩放)、计算高效
```

**Q5: KV Cache为什么能加速？**

```
自回归生成时，历史token的K/V不变
缓存历史K/V → 每步只计算新token的Q/K/V
从O(n²)降到O(n)每步
代价: 额外显存(与seq_len成正比)
GQA/MLA就是为减少KV Cache显存设计的
```

**Q6: MoE模型为什么又快又大？**

```
总参数大(如DeepSeek-V3 671B)但激活参数少(37B)
每个token只路由到Top-K专家(8/256)
推理时只计算被激活的专家 → 速度等价于37B Dense模型
代价: 显存要装全部参数、多GPU通信
```

**Q7: 为什么Decoder-only胜出？**

```
1. 生成能力强(自回归天生适合)
2. 预训练效率高(CLM比MLM利用率高)
3. 规模化好(Scaling Laws验证)
4. 统一架构(生成+理解=Next Token Prediction)
5. 涌现能力(大规模后理解力涌现)
```

**Q8: 上下文窗口如何扩展？**

```
训练时4K → 推理时128K的方法:
1. RoPE缩放 — 降低旋转频率(线性/NTK/YaRN)
2. 长文本微调 — 用长文本SFT适应
3. KV Cache压缩 — StreamingLLM(保留首尾)
4. Flash Attention — 减少长序列内存
5. PagedAttention(vLLM) — 高效管理KV Cache
```

---

*最后更新: 2026-07-13*

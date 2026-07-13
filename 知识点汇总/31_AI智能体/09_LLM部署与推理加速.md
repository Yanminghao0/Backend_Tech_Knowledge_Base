# LLM部署与推理加速

> vLLM/Ollama部署、量化加速、KV Cache优化与生产推理服务

---

## 📋 目录

1. [模型格式与量化](#1-模型格式与量化)
2. [Ollama本地部署](#2-ollama本地部署)
3. [vLLM生产部署](#3-vllm生产部署)
4. [推理加速技术](#4-推理加速技术)
5. [GPU选型与显存](#5-gpu选型与显存)
6. [多GPU部署](#6-多gpu部署)
7. [面试题速查](#7-面试题速查)

---

## 1. 模型格式与量化

### 1.1 模型格式

```
┌──────────────────────────────────────────────────────────┐
│  格式        │  说明              │  适用                 │
│  ──────   │  ────          │  ────              │
│  PyTorch    │  .pt/.bin 原始格式  │  训练(逐步淘汰)       │
│  SafeTensors│  安全序列化(防注入) │  HF标准(推荐)         │
│  GGUF       │  llama.cpp格式     │  CPU/边缘/Ollama      │
│  AWQ        │  激活感知量化       │  vLLM/TensorRT        │
│  GPTQ       │  二阶信息量化      │  vLLM                 │
│  ONNX       │  跨平台格式        │  ONNX Runtime         │
└──────────────────────────────────────────────────────────┘

  量化格式:
    FP16(半精度) — 原始精度，质量最好
    INT8 — 8bit量化，质量损失极小
    INT4 — 4bit量化，质量损失约1-3%
    NF4 — NormalFloat4(QLoRA用)，信息损失最小

  量化方法对比:
    GGUF Q4_K_M — llama.cpp/Ollama用，均衡
    AWQ — 保护重要权重，质量好
    GPTQ — 基于二阶信息，速度快
    推荐: Ollama用GGUF, vLLM用AWQ
```

---

## 2. Ollama本地部署

### 2.1 Ollama概述

```
Ollama — 本地一键运行大模型(开发环境首选)

  优势:
    1. 一行命令 — ollama run qwen2.5
    2. 自动下载 — 拉取模型自动量化
    3. OpenAI兼容 — /v1/chat/completions接口
    4. 跨平台 — Mac/Linux/Windows
    5. Modelfile — 自定义模型

  适用: 开发调试/个人使用/原型验证
  不适用: 高并发生产环境(吞吐量低)
```

```bash
# 安装
curl -fsSL https://ollama.com/install.sh | sh

# 运行模型
ollama run qwen2.5:7b          # Qwen2.5 7B
ollama run qwen2.5:14b         # Qwen2.5 14B
ollama run deepseek-r1:7b      # DeepSeek R1
ollama run llama3.1:8b         # LLaMA 3.1

# 查看已安装模型
ollama list

# OpenAI兼容API(默认端口11434)
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'

# 自定义Modelfile(加载微调模型)
# FROM /path/to/merged-model
# PARAMETER temperature 0.7
# PARAMETER num_ctx 8192
# SYSTEM "你是一个Java技术助手"
ollama create my-qwen -f Modelfile
ollama run my-qwen
```

### 2.2 Spring AI对接Ollama

```java
// application.yml
// spring.ai.ollama.base-url=http://localhost:11434
// spring.ai.ollama.chat.options.model=qwen2.5:7b
// spring.ai.ollama.chat.options.temperature=0.7
// spring.ai.ollama.chat.options.num-ctx=8192

@Configuration
public class OllamaConfig {

    @Bean
    public ChatClient chatClient(ChatClient.Builder builder) {
        return builder
            .defaultSystem("你是一个智能Java技术助手")
            .build();
    }
}

// 直接使用
@Service
public class ChatService {
    @Autowired
    private ChatClient chatClient;

    public String chat(String message) {
        return chatClient.prompt()
            .user(message)
            .call()
            .content();
    }
}
```

---

## 3. vLLM生产部署

### 3.1 vLLM概述

```
vLLM — 生产级LLM推理引擎

  核心技术:
    1. PagedAttention — KV Cache分页管理(减少碎片)
    2. Continuous Batching — 动态组batch(提高吞吐)
    3. Prefix Caching — 共享System Prompt的KV Cache
    4. 多LoRA服务 — 动态加载多个LoRA适配器

  ┌──────────────────────────────────────────────────┐
  │  vLLM vs Ollama:                                 │
  │  Ollama: 简单易用，但吞吐低(适合开发)             │
  │  vLLM: 高吞吐，生产级(适合部署)                   │
  │                                                  │
  │  性能对比(7B模型, A100):                          │
  │  Ollama: ~50 tokens/s                            │
  │  vLLM:  ~2000+ tokens/s (40倍)                   │
  └──────────────────────────────────────────────────┘
```

### 3.2 vLLM部署

```bash
# 方式1: 直接命令行
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct \
    --trust-remote-code \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9

# 方式2: AWQ量化模型(省显存)
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-7B-Instruct-AWQ \
    --quantization awq \
    --trust-remote-code \
    --port 8000

# 方式3: 多GPU张量并行
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-72B-Instruct-AWQ \
    --quantization awq \
    --tensor-parallel-size 4 \
    --port 8000

# 方式4: Docker部署
docker run --gpus all -p 8000:8000 \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen2.5-7B-Instruct \
    --max-model-len 8192
```

### 3.3 调用vLLM API

```java
// vLLM完全兼容OpenAI API格式
// 用Spring AI的OpenAI client直接对接

// application.yml
// spring.ai.openai.base-url=http://vllm-host:8000
// spring.ai.openai.api-key=dummy  (vLLM不验证key)
// spring.ai.openai.chat.options.model=Qwen/Qwen2.5-7B-Instruct

@RestController
public class ChatController {

    @Autowired
    private ChatClient chatClient;

    @PostMapping("/chat")
    public String chat(@RequestBody String message) {
        return chatClient.prompt()
            .user(message)
            .call()
            .content();
    }

    // 流式输出
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> stream(@RequestParam String message) {
        return chatClient.prompt()
            .user(message)
            .stream()
            .content();
    }
}
```

---

## 4. 推理加速技术

### 4.1 PagedAttention

```
PagedAttention — KV Cache的分页管理(类似操作系统的虚拟内存)

  传统KV Cache问题:
    每个请求预分配最大长度的连续内存
    → 内存碎片严重 → 显存利用率低(60%浪费)

  PagedAttention:
    将KV Cache分成固定大小的"块"(Block)
    按需分配，不要求连续
    → 显存利用率96%+ → 同显存能服务更多并发请求

  ┌──────────────────────────────────────────────┐
  │  传统: 请求1[########预留####]               │
  │        请求2[####预留##########]             │
  │        → 大量预留空间浪费                    │
  │                                              │
  │  PagedAttention: 请求1[Block0][Block1]      │
  │                  请求2[Block2][Block3]       │
  │                  → 按需分配，无浪费           │
  └──────────────────────────────────────────────┘
```

### 4.2 连续批处理

```
Continuous Batching — 动态组batch

  传统批处理(Static Batching):
    等batch中所有请求都完成 → 才处理下一batch
    短请求等长请求 → GPU空闲

  连续批处理:
    每个请求完成 → 立即移出 → 新请求加入
    GPU持续工作 → 吞吐量提升5-10倍

  ┌──────────────────────────────────────────────┐
  │  时间→  t1   t2   t3   t4   t5   t6         │
  │  请求A: ████████ 完成                        │
  │  请求B: ████████████████ 完成                │
  │  请求C:      ████████ 完成                   │
  │  请求D:           ████████████████ 完成      │
  │  请求E:                ████████ 完成         │
  │  → GPU持续工作，无空闲                        │
  └──────────────────────────────────────────────┘
```

### 4.3 投机解码

```
Speculative Decoding — 小模型草稿+大模型验证

  原理:
    1. 小模型(快)生成N个token草稿
    2. 大模型(准)一次验证N个token
    3. 接受正确的token，拒绝后重新生成

  ┌──────────────────────────────────────────────┐
  │  传统: 大模型逐个生成token                    │
  │  t1→t2→t3→t4→t5 (5次大模型前向)              │
  │                                              │
  │  投机解码: 小模型生成5个 → 大模型1次验证       │
  │  小: t1→t2→t3→t4→t5 (快)                    │
  │  大: 一次验证5个 (接受4个)                    │
  │  → 1次大模型前向完成4个token                 │
  └──────────────────────────────────────────────┘

  变体:
    Medusa — 大模型自己加多个预测头
    EAGLE — 更准确的草稿模型
    Lookahead — 基于n-gram的草稿
```

---

## 5. GPU选型与显存

### 5.1 显存计算

```
LLM推理显存 = 模型参数 + KV Cache + 激活值

  模型参数:
    FP16: 参数量 × 2字节
    INT4: 参数量 × 0.5字节 + 量化开销

    7B FP16: 14GB
    7B INT4: 3.5GB
    70B FP16: 140GB
    70B INT4: 35GB

  KV Cache(每个请求):
    = 2 × n_layers × n_kv_heads × d_head × seq_len × 2字节

    Qwen2.5-7B (GQA, n_kv_heads=4):
      2 × 28 × 4 × 128 × 4096 × 2 = 0.47GB/请求(4K上下文)
      10个并发 → 4.7GB

  总显存估算:
    7B FP16 + 10并发4K = 14 + 4.7 ≈ 19GB → RTX 4090(24GB)够
    7B INT4 + 10并发4K = 3.5 + 4.7 ≈ 8GB → RTX 3090(24GB)绰绰有余
    70B INT4 + 10并发4K = 35 + 2.5 ≈ 38GB → A100(80GB)够
```

### 5.2 GPU选型

```
┌──────────────────────────────────────────────────────────┐
│  GPU          │  显存    │  适合模型           │  价格     │
│  ────       │  ────  │  ──────         │  ────   │
│  RTX 4090    │  24GB   │  7B FP16 / 14B Q4  │  ¥15K    │
│  RTX 3090    │  24GB   │  7B FP16 / 14B Q4  │  ¥8K(二手)│
│  A10         │  24GB   │  7B FP16           │  ¥30K    │
│  A100 80GB   │  80GB   │  70B Q4 / 14B FP16 │  ¥100K+  │
│  H100 80GB   │  80GB   │  70B FP16          │  ¥200K+  │
│  多卡4090×4  │  96GB   │  70B Q4            │  ¥60K    │
└──────────────────────────────────────────────────────────┘

  选型建议:
    开发/个人: RTX 4090(24GB) — 7B模型够用
    中小生产: A10/A100(40GB) — 14B/32B模型
    大规模生产: A100/H100 80GB — 70B+模型
    性价比: 多卡RTX 4090(但PCIe带宽限制)
```

---

## 6. 多GPU部署

### 6.1 张量并行

```
张量并行(Tensor Parallelism) — 将每一层的权重切分到多GPU

  ┌──────────────────────────────────────────────┐
  │  单GPU: y = W·x  (W: 4096×4096)             │
  │                                              │
  │  2GPU张量并行:                                │
  │  GPU0: y₀ = W₀·x  (W₀: 2048×4096, 左半)     │
  │  GPU1: y₁ = W₁·x  (W₁: 2048×4096, 右半)     │
  │  y = [y₀, y₁]  (AllReduce合并)              │
  └──────────────────────────────────────────────┘

  vLLM张量并行:
    --tensor-parallel-size 2  # 2路张量并行
    --tensor-parallel-size 4  # 4路

  注意:
    1. 需要NVLink/InfiniBand高速互联
    2. 每层需要AllReduce通信
    3. 通常不超过8路(TP>8通信开销过大)
    4. 消费级GPU(PCIe)通信慢，效果差
```

---

## 7. 面试题速查

**Q1: vLLM为什么比Ollama快？**

```
1. PagedAttention — KV Cache分页管理，显存利用率96%+
2. Continuous Batching — 动态组batch，GPU不空闲
3. 高效CUDA kernel — 专为推理优化
4. Prefix Caching — 共享System Prompt的KV Cache
Ollama适合开发(简单)，vLLM适合生产(高吞吐)
```

**Q2: PagedAttention的原理？**

```
KV Cache分页管理(类似虚拟内存)
将KV Cache分成固定Block → 按需分配 → 不要求连续
传统: 每请求预分配最大长度 → 60%显存浪费
PagedAttention: 显存利用率96%+ → 同显存更多并发
```

**Q3: 投机解码怎么加速？**

```
小模型(快)生成N个token草稿 → 大模型(准)一次验证N个
接受正确的 → 拒绝后重新生成
1次大模型前向完成多个token → 加速2-3倍
变体: Medusa/EAGLE/Lookahead
```

**Q4: 7B模型需要多少显存？**

```
FP16: 14GB(参数) + KV Cache(4K≈0.5GB/请求)
INT4: 3.5GB(参数) + KV Cache
开发: RTX 4090(24GB)跑FP16够用
生产: 需考虑并发 → KV Cache随并发增长
```

**Q5: 模型量化Q4和FP16的质量差异？**

```
Q4(4bit): 质量损失约1-3%，显存降至1/4
FP16: 原始精度，质量最好
大多数场景Q4够用(特别是AWQ/GGUF Q4_K_M)
追求极致质量用FP16
```

---

*最后更新: 2026-07-13*

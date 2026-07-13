# eBPF技术详解

> 内核级可编程数据面，云原生可观测性与网络的新基石

---

## 📋 目录

1. [eBPF概述](#1-ebpf概述)
2. [工作原理](#2-工作原理)
3. [eBPF程序开发](#3-ebpf程序开发)
4. [应用场景](#4-应用场景)
5. [主流工具生态](#5-主流工具生态)
6. [eBPF vs 内核模块](#6-ebpf-vs-内核模块)
7. [面试要点](#7-面试要点)

---

## 1. eBPF概述

```
eBPF (Extended Berkeley Packet Filter) = 内核可编程虚拟机

核心价值：
  - 无需修改内核源码，在内核中运行自定义程序
  - 无需重启系统，动态加载/卸载
  - 安全：验证器确保程序不会崩溃内核
  - 高性能：JIT编译为原生指令

类比：
  - JavaScript让浏览器可编程 → eBPF让Linux内核可编程
  - 前端不修改浏览器源码 → eBPF不修改内核源码
```

### 1.1 发展历程

```
1992  BPF诞生 — Berkeley Packet Filter，BSD系统包过滤
      └─ 经典BPF（cBPF），用于tcpdump/libpcap

2014  eBPF — Alexei Starovoitov引入Linux 3.15
      └─ 扩展BPF（eBPF），64位寄存器，通用虚拟机

2018  eBPF爆发 — Cilium/Calico/XDP生态成熟
      └─ K8s网络、可观测性、安全

2020+  eBPF成为云原生基础设施标配
      └─ CO-RE（Compile Once Run Everywhere）
      └─ BTF（BPF Type Format）
      └─ libbpf 1.0
```

### 1.2 为什么eBPF如此重要

```
传统方式的痛点：
┌─────────────────────────────────────────────┐
│ 内核模块（LKM）          │ iptables              │
│ - 开发复杂              │ - 规则链线性匹配       │
│ - 可能崩溃内核          │ - O(n)性能，万条规则卡 │
│ - 需要内核版本匹配      │ - 不支持L7协议        │
└─────────────────────────────────────────────┘

eBPF的解决方案：
┌─────────────────────────────────────────────┐
│ - C子集编写，LLVM编译   │ - eBPF Map哈希查找    │
│ - 验证器保证安全        │ - O(1)性能            │
│ - CO-RE跨内核版本       │ - 支持L7（HTTP/gRPC） │
└─────────────────────────────────────────────┘
```

---

## 2. 工作原理

### 2.1 eBPF程序生命周期

```
  开发阶段                          运行阶段
┌──────────────┐               ┌──────────────┐
│ 1. 编写C程序  │               │ 5. 挂载Hook   │
│ (限制的C子集) │               │ (kprobe/XDP)  │
└──────┬───────┘               └──────┬───────┘
       ▼                              ▼
┌──────────────┐               ┌──────────────┐
│ 2. LLVM编译   │               │ 6. 事件触发   │
│ → eBPF字节码  │               │ 内核执行程序  │
└──────┬───────┘               └──────┬───────┘
       ▼                              ▼
┌──────────────┐               ┌──────────────┐
│ 3. 验证器检查 │               │ 7. Map通信    │
│ 安全/无死循环 │               │ 内核↔用户态   │
└──────┬───────┘               └──────────────┘
       ▼
┌──────────────┐
│ 4. JIT编译    │
│ → 原生机器码  │
└──────────────┘
```

### 2.2 验证器（Verifier）

```c
// 验证器检查项：
// 1. 程序大小限制（100万条指令，Linux 5.2+）
// 2. 无无限循环
// 3. 无未初始化的寄存器使用
// 4. 无越界访问
// 5. 无空指针解引用
// 6. 所有执行路径都能到达出口

// 示例：一个安全的eBPF程序
SEC("kprobe/tcp_v4_connect")
int trace_connect(struct pt_regs *ctx) {
    // 读取进程名
    char comm[16];
    bpf_get_current_comm(&comm, sizeof(comm));
    
    // 通过Map输出到用户态
    bpf_trace_printk("TCP connect from %s\\n", comm);
    return 0;
}
```

### 2.3 Hook点类型

| Hook点 | 触发时机 | 典型用途 |
|--------|----------|----------|
| kprobe/kretprobe | 内核函数入口/返回 | 追踪内核函数调用 |
| uprobe/uretprobe | 用户函数入口/返回 | 追踪应用函数 |
| tracepoint | 内核预定义追踪点 | 系统调用追踪 |
| XDP | 网卡收到包时 | DDoS防护、L4负载均衡 |
| TC (Traffic Control) | 网络协议栈 | 包修改、重定向 |
| perf_event | CPU性能事件 | 火焰图、CPU profiling |
| cgroup | cgroup操作 | 容器资源监控 |
| socket | socket操作 | 网络过滤 |

---

## 3. eBPF程序开发

### 3.1 BPF Map（数据结构）

```c
// Map是eBPF程序与用户态通信的桥梁

// 1. Hash Map — 键值存储
struct bpf_map_def SEC("maps") my_hash = {
    .type = BPF_MAP_TYPE_HASH,
    .key_size = sizeof(u32),
    .value_size = sizeof(u64),
    .max_entries = 10000,
};

// 2. Perf Event Array — 事件输出到用户态
struct bpf_map_def SEC("maps") events = {
    .type = BPF_MAP_TYPE_PERF_EVENT_ARRAY,
    .key_size = sizeof(int),
    .value_size = sizeof(u32),
    .max_entries = 0,
};

// 3. Ring Buffer — 环形缓冲区（Linux 5.8+，推荐）
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);  // 1MB
} rb SEC(".maps");

// 使用示例
SEC("kprobe/sys_enter_openat")
int trace_open(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u64 ts = bpf_ktime_get_ns();
    
    // 写入Hash Map
    bpf_map_update_elem(&my_hash, &pid, &ts, BPF_ANY);
    
    // 输出事件到Ring Buffer
    struct event *e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (e) {
        e->pid = pid;
        bpf_get_current_comm(&e->comm, sizeof(e->comm));
        bpf_ringbuf_submit(e, 0);
    }
    return 0;
}
```

### 3.2 bpftrace — 一行命令追踪

```bash
# 统计各进程打开文件的次数
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { 
    @[comm] = count(); 
}'

# 追踪TCP连接延迟
bpftrace -e 'kprobe:tcp_v4_connect { 
    @start[tid] = nsecs; 
} 
kretprobe:tcp_v4_connect /@start[tid]/ { 
    @latency = hist((nsecs - @start[tid]) / 1000); 
    delete(@start[tid]); 
}'

# 追踪函数执行耗时Top 10
bpftrace -e 'kprobe: vfs_read { @start[tid] = nsecs; }
kr: vfs_read /@start[tid]/ { 
    @us[func] = hist((nsecs - @start[tid]) / 1000); 
    delete(@start[tid]); 
}'

# 追踪GC暂停（Java应用）
bpftrace -e 'uprobe:/path/to/libjvm.so:*GC* { 
    @gc_start[pid] = nsecs; 
}'
```

---

## 4. 应用场景

### 4.1 可观测性

```
1. 网络监控：TCP连接、重传、延迟（无需应用改造）
2. 系统调用追踪：文件IO、内存分配
3. CPU profiling：内核+用户态火焰图
4. HTTP/gRPC追踪：无需应用代码侵入
5. 数据库查询追踪：MySQL/PostgreSQL慢查询

工具：Pixie、Parca、Inspektor Gadget
```

### 4.2 网络安全

```
1. Cilium：eBPF驱动的K8s网络插件（替代kube-proxy）
   - Service负载均衡（eBPF vs iptables：快10倍）
   - NetworkPolicy（L3/L4/L7层策略）
   - L7可观测性（HTTP/gRPC/Kafka流量）
   - mTLS加密（无需Sidecar）

2. XDP（eXpress Data Path）：网卡级包处理
   - DDoS防护（在网卡丢弃恶意包，CPU零开销）
   - 负载均衡（L4 LB，Maglev算法）
   - 防火墙（比iptables快100倍）
```

### 4.3 性能分析

```bash
# bpftrace火焰图
bpftrace -e 'profile:hz:99 { @[ustack] = count(); }' | flamegraph.pl > cpu.svg

# BCC工具：biolatency（磁盘IO延迟分布）
/usr/share/bcc/tools/biolatency

# BCC工具：tcplife（TCP连接生命周期）
/usr/share/bcc/tools/tcplife

# BCC工具：execsnoop（追踪短命进程）
/usr/share/bcc/tools/execsnoop
```

---

## 5. 主流工具生态

| 工具 | 功能 | 适用场景 |
|------|------|----------|
| Cilium | K8s网络+安全 | 替代kube-proxy/Calico |
| Hubble | 网络流量可视化 | Cilium配套，Service Map |
| Pixie | K8s可观测性 | 无侵入监控HTTP/gRPC |
| Parca | 持续性能分析 | eBPF火焰图 |
| bpftrace | 内核追踪 | 一行命令性能分析 |
| BCC | eBPF工具集 | 100+系统级诊断工具 |
| Falco | 运行时安全 | 异常行为检测 |
| Tetragon | 安全执行 | 实时策略执行 |
| kubectl-trace | K8s集成 | 在集群中运行bpftrace |

---

## 6. eBPF vs 内核模块 vs Sidecar

| 维度 | eBPF | 内核模块(LKM) | Sidecar(Envoy) |
|------|------|-------------|----------------|
| 开发难度 | 中（C子集） | 高（完整C） | 中（Go/C++） |
| 安全性 | 高（验证器） | 低（可崩溃内核） | 高（隔离） |
| 性能 | 极高（内核态） | 极高（内核态） | 中（用户态代理） |
| 资源开销 | 极低（无额外进程） | 低 | 高（每Pod一个Sidecar） |
| 可移植性 | 高（CO-RE） | 低（内核版本绑定） | 高（容器化） |
| 侵入性 | 无 | 无 | 需修改网络配置 |

---

## 7. 面试要点

### Q1: eBPF是什么？有什么优势？

```
eBPF = Linux内核可编程虚拟机

优势：
1. 无需改内核源码/重启，动态加载
2. 安全（验证器保证不会崩溃）
3. 高性能（JIT编译为原生码）
4. 无侵入（不修改应用代码，不需要Sidecar）
```

### Q2: eBPF在K8s中的应用？

```
1. Cilium：eBPF替代kube-proxy/iptables
   - Service负载均衡快10倍（Map O(1) vs iptables O(n)）
   - L7 NetworkPolicy（HTTP路径级控制）
   - 无Sidecar的mTLS

2. 无侵入可观测性
   - 追踪HTTP/gRPC调用链（不需要应用改代码）
   - 替代Sidecar方案（减少资源开销）

3. 安全审计
   - Falco检测异常系统调用
   - 容器运行时安全
```

### Q3: eBPF为什么比iptables快？

```
iptables：O(n)线性规则匹配
  - 每个包遍历规则链
  - 万条规则时性能急剧下降
  - 规则更新需要全量替换

eBPF：O(1)哈希查找
  - Map数据结构直接查找
  - 无论规则多少性能恒定
  - 规则更新只需更新Map
```

### Q4: eBPF的验证器如何保证安全？

```
1. 控制流分析：确保无无限循环
2. 类型检查：寄存器类型追踪
3. 边界检查：所有内存访问必须验证边界
4. 路径分析：遍历所有可能执行路径
5. 指令限制：最多100万条指令（Linux 5.2+）
```

---

## 📚 相关阅读

- [01_Kubernetes进阶实战](./01_Kubernetes进阶实战.md)
- [05_云原生可观测性](./05_云原生可观测性.md)
- [04_监控告警体系](../18_DevOps与CICD/04_监控告警体系.md)

---

*最后更新：2026-07-13*

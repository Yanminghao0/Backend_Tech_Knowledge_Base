# eBPF技术详解

> 内核级可编程数据面，云原生可观测性与网络的新基石

---

## 📋 目录

1. [eBPF概述](#1-ebpf概述)
2. [工作原理](#2-工作原理)
3. [应用场景](#3-应用场景)
4. [主流工具](#4-主流工具)
5. [面试要点](#5-面试要点)

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

---

## 2. 工作原理

```
eBPF程序生命周期：

  1. 编写eBPF程序（C语言子集）
  2. 编译为eBPF字节码（LLVM）
  3. 验证器检查安全性（无无限循环、内存安全）
  4. JIT编译为原生机器码
  5. 挂载到内核Hook点
  6. 事件触发时执行
  7. 通过Map与用户态通信

Hook点：
  - 系统调用（tracepoint）
  - 网络包（XDP/TC）
  - 内核函数（kprobe）
  - 用户函数（uprobe）
  - Perf事件
```

---

## 3. 应用场景

### 可观测性

```
1. 网络监控：TCP连接、重传、延迟（无需应用改造）
2. 系统调用追踪：文件IO、内存分配
3. CPU profiling：内核+用户态火焰图
4. HTTP/gRPC追踪：无需应用代码侵入

工具：Pixie、Parca、Inspektor Gadget
```

### 网络安全

```
1. Cilium：eBPF驱动的K8s网络插件（替代kube-proxy）
   - Service负载均衡（eBPF vs iptables：快10倍）
   - NetworkPolicy（L7层策略）
   - L7可观测性（HTTP/gRPC/Kafka流量）

2. XDP（eXpress Data Path）：网卡级包处理
   - DDoS防护（在网卡丢弃恶意包）
   - 负载均衡（L4 LB）
```

### 性能分析

```bash
# bpftrace：一行命令追踪内核
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { 
    @[comm] = count(); 
}'
# 统计各进程打开文件的次数

# 追踪TCP连接延迟
bpftrace -e 'kprobe:tcp_v4_connect { 
    @start[tid] = nsecs; 
} 
kretprobe:tcp_v4_connect /@start[tid]/ { 
    @latency = hist((nsecs - @start[tid]) / 1000); 
    delete(@start[tid]); 
}'
```

---

## 4. 主流工具

| 工具 | 功能 | 适用场景 |
|------|------|---------|
| Cilium | K8s网络+安全 | 替代kube-proxy/Calico |
| Pixie | K8s可观测性 | 无侵入监控 |
| bpftrace | 内核追踪 | 性能分析/排查 |
| BCC | eBPF工具集 | 系统级诊断 |
| Falco | 运行时安全 | 异常检测 |
| Hubble | 网络流量可视化 | Cilium配套 |

---

## 5. 面试要点

### Q1: eBPF是什么？有什么优势？

```
eBPF = Linux内核可编程虚拟机

优势：
1. 无需改内核源码/重启
2. 安全（验证器保证不会崩溃）
3. 高性能（JIT编译）
4. 无侵入（不修改应用代码）
```

### Q2: eBPF在K8s中的应用？

```
1. Cilium：eBPF替代kube-proxy/iptables
   - Service负载均衡快10倍
   - L7 NetworkPolicy（HTTP路径级控制）

2. 无侵入可观测性
   - 追踪HTTP/gRPC调用链
   - 不需要应用改代码或Sidecar

3. 安全审计
   - Falco检测异常系统调用
   - 容器运行时安全
```

---

## 📚 相关阅读

- [01_Kubernetes进阶实战](../19_云原生技术/01_Kubernetes进阶实战.md)
- [05_云原生可观测性](../19_云原生技术/05_云原生可观测性.md)
- [04_监控告警体系](../18_DevOps与CICD/04_监控告警体系.md)

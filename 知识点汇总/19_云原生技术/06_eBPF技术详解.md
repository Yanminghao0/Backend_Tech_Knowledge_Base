# eBPF技术详解

> 内核级可编程数据面，云原生可观测性与网络的新基石

---

## 📋 目录

1. [eBPF概述](#1-ebpf概述)
2. [工作原理](#2-工作原理)
3. [应用场景](#3-应用场景)
4. [主流工具](#4-主流工具)
5. [面试要点](#5-面试要点)
6. [eBPF程序开发实战](#6-ebpf程序开发实战)
7. [Cilium网络架构详解](#7-cilium网络架构详解)
8. [性能监控实战（bpftrace）](#8-性能监控实战bpftrace)
9. [eBPF在K8s中的3大应用场景](#9-ebpf在k8s中的3大应用场景)

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

### Q3: eBPF程序如何保证安全？

```
验证器（Verifier）三层检查：
1. 有向无环图（DAG）：程序必须无循环，执行路径有限
2. 寄存器跟踪：模拟执行，确保所有内存访问合法
3. 指令数限制：上限100万条（5.x+），防止超时

运行时安全：
- 权限检查：加载需CAP_BPF（5.8+）或root
- 内核版本匹配：BTF保证跨版本兼容
- 资源限额：Map大小、栈空间(512KB)有限制
```

### Q4: XDP和TC有什么区别？

```
XDP（eXpress Data Path）：
  - Hook点：网卡驱动层（最早的拦截点）
  - 特点：包还没进入内核协议栈
  - 场景：DDoS防护、L4负载均衡、包过滤
  - 动作：XDP_PASS/XDP_DROP/XDP_REDIRECT

TC（Traffic Control）：
  - Hook点：内核流量控制层（协议栈内）
  - 特点：包已进入内核，有完整skb结构
  - 场景：NetworkPolicy、Service负载均衡、NAT
  - 优势：可以修改包内容、做L7处理

关系：XDP在TC之前执行，两者互补
```

### Q5: eBPF的Map是什么？有哪些类型？

```
BPF Map = 内核态与用户态通信的数据结构

常见类型：
  - BPF_MAP_TYPE_HASH：哈希表，KV存储
  - BPF_MAP_TYPE_ARRAY：数组，固定大小
  - BPF_MAP_TYPE_PERCPU_HASH：per-CPU哈希表（无锁）
  - BPF_MAP_TYPE_PERF_EVENT_ARRAY：事件推送（→用户态）
  - BPF_MAP_TYPE_RINGBUF：环形缓冲区（替代PerfEvent）
  - BPF_MAP_TYPE_SOCKHASH：Socket存储（用于重定向）

用途：
  - 统计数据上报（count/hist）
  - 事件传递（PerfEvent/RingBuf）
  - 配置下发（用户态→内核态的策略表）
  - 连接跟踪（conntrack表）
```

---

## 6. eBPF程序开发实战

### 6.1 编写eBPF程序（C语言）

```c
// trace_open.c — 追踪文件打开系统调用
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

// 定义事件结构（传递给用户态）
struct event {
    u32 pid;
    u32 uid;
    char comm[16];
    char filename[128];
};

// Perf事件Map（用于向用户态发送事件）
struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(u32));
    __uint(value_size, sizeof(u32));
} events SEC(".maps");

// 挂载到 sys_enter_openat tracepoint
SEC("tracepoint/syscalls/sys_enter_openat")
int trace_openat(struct trace_event_raw_sys_enter *ctx)
{
    struct event e = {};
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u32 uid = bpf_get_current_uid_gid();

    e.pid = pid;
    e.uid = uid;
    bpf_get_current_comm(&e.comm, sizeof(e.comm));
    bpf_probe_read_user_str(&e.filename, sizeof(e.filename), ctx->args[1]);

    // 提交事件到用户态
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, &e, sizeof(e));
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 6.2 编译eBPF字节码

```bash
# 使用clang编译为eBPF字节码（.o）
clang -O2 -g -target bpf \
    -D__TARGET_ARCH_x86 \
    -I/usr/include/x86_64-linux-gnu \
    -c trace_open.c -o trace_open.o

# 生成BPF skeleton头文件（libbpf风格，供用户态程序引用）
bpftool gen skeleton trace_open.o > trace_open.skel.h
```

### 6.3 用户态加载器（C语言）

```c
// loader.c — 用户态程序：加载eBPF + 读取事件
#include <stdio.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "trace_open.skel.h"

static int handle_event(void *ctx, int cpu, void *data, unsigned int size)
{
    struct event *e = data;
    printf("PID:%d UID:%d COMM:%s FILE:%s\n",
           e->pid, e->uid, e->comm, e->filename);
    return 0;
}

int main()
{
    struct trace_open_bpf *skel;
    struct perf_buffer *pb;

    // 1. 打开并加载BPF程序（验证器检查）
    skel = trace_open_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to load BPF skeleton\n");
        return 1;
    }

    // 2. 挂载到tracepoint
    int err = trace_open_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF program\n");
        return 1;
    }

    // 3. 设置Perf Buffer回调
    pb = perf_buffer__new(bpf_map__fd(skel->maps.events), 8,
                          handle_event, NULL, NULL, NULL);

    printf("Tracing openat... Ctrl+C to exit\n");

    // 4. 轮询事件（阻塞循环）
    while (true) {
        perf_buffer__poll(pb, 100);
    }

    trace_open_bpf__destroy(skel);
    return 0;
}
```

### 6.4 编译运行

```bash
# 编译用户态程序
gcc loader.c -o loader -lbpf -lelf -lz

# 运行（需要root权限）
sudo ./loader
# 输出示例：
# PID:1234 UID:1000 COMM:bash FILE:/etc/passwd
# PID:1235 UID:1000 COMM:python FILE:./config.yaml
```

### 6.5 开发工具链对比

```
开发方式             难度   灵活性   适用场景
──────────────────────────────────────────────────
libbpf + C           高     最高     生产级BPF程序
BCC（Python + C）    中     高       快速原型 / 运维脚本
bpftrace             低     中       一次性追踪 / 排障
Aya（Rust）          中     高       Rust生态集成
```

---

## 7. Cilium网络架构详解

### 7.1 整体架构

```
┌────────────────────────────────────────────────────────┐
│                    Kubernetes 集群                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│  │  Node 1  │   │  Node 2  │   │  Node 3  │           │
│  │ ┌──────┐ │   │ ┌──────┐ │   │ ┌──────┐ │           │
│  │ │Pod A │ │   │ │Pod C │ │   │ │Pod E │ │           │
│  │ └──┬───┘ │   │ └──┬───┘ │   │ └──┬───┘ │           │
│  │    │veth │   │    │veth │   │    │veth │           │
│  │ ┌──┴────┐│   │ ┌──┴────┐│   │ ┌──┴────┐│           │
│  │ │eBPF   ││   │ │eBPF   ││   │ │eBPF   ││           │
│  │ │数据面  ││   │ │数据面  ││   │ │数据面  ││           │
│  │ └──┬────┘│   │ └──┬────┘│   │ └──┬────┘│           │
│  │  TC/XDP  │   │  TC/XDP  │   │  TC/XDP  │           │
│  └───┬──────┘   └───┬──────┘   └───┬──────┘           │
│      └──────┬───────┴───────────────┘                  │
│         VXLAN / Geneve 隧道                             │
└────────────────────────────────────────────────────────┘

关键组件：
  - cilium-agent     每个节点的守护进程，管理eBPF程序生命周期
  - cilium-operator  集群级控制面（IPAM分配、安全策略同步）
  - Hubble           基于eBPF的流量观测平台（Service Map）
  - kvstore（etcd）  存储Cilium集群状态
```

### 7.2 数据面：eBPF Hook点

```
数据包入站路径（Pod接收流量）：
  网卡 → XDP（最早拦截） → TC ingress → 路由判断
       → TC egress（重定向到Pod） → Pod的veth

数据包出站路径（Pod发送流量）：
  Pod → veth → TC ingress（容器侧）
       → TC egress（主机侧） → 路由 → 网卡/隧道

Cilium在以下Hook点加载eBPF程序：
  1. XDP              DDoS防护、源地址验证
  2. TC ingress       入站策略、负载均衡
  3. TC egress        出站策略、NAT、SNAT
  4. cgroup/connect   Socket级重定向（SockLB）
```

### 7.3 Service负载均衡：eBPF vs kube-proxy

```
                    kube-proxy(iptables)        Cilium(eBPF)
                    ────────────────────        ──────────────
数据包路径           Pod→iptables→Pod            Pod→eBPF→Pod
                    （多次netfilter钩子）         （TC层直接重定向）

规则更新             O(n)重写全表                 O(1)更新Map
                    （Service多了变慢）           （万级Service仍快）

连接跟踪             内核conntrack表              eBPF ct_map
                    （全局限额）                  （per-CPU优化）

L7负载均衡           不支持                       支持（Envoy集成）
Socket重定向         不支持                       支持（SockLB）
                    （每个包都走栈）              （客户端Socket直连后端）
```

### 7.4 NetworkPolicy：L3/L4 → L7

```yaml
# Cilium L7 NetworkPolicy 示例
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-server-l7-policy
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
  # L4层：允许访问 api-server 的 443 端口
  - toEndpoints:
    - matchLabels:
        app: api-server
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
  # L7层：只允许 GET /api/v1/orders，禁止 DELETE
  - toEndpoints:
    - matchLabels:
        app: api-server
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/api/v1/orders.*"
        - method: POST
          path: "/api/v1/orders"
        # 未列出的 HTTP 方法自动拒绝
```

### 7.5 Hubble：网络可观测性

```bash
# 实时查看 Pod 间流量
hubble observe --pod payment-service

# 查看被 NetworkPolicy 拒绝的流量
hubble observe --verdict DROPPED

# 生成服务依赖图（L4 + L7）
hubble observe --type l7 --since 5m

# 输出示例：
# Jul 10 10:00:01.234 default/payment-service:8080 <>
#   default/api-server:443 HTTP GET /api/v1/orders 200 OK
# Jul 10 10:00:02.567 default/payment-service:8080 <>
#   default/api-server:443 HTTP DELETE /api/v1/orders/123 403 FORBIDDEN
#   (policy denied)
```

---

## 8. 性能监控实战（bpftrace）

### 8.1 文件IO延迟分析

```bash
# 追踪 read() 系统调用延迟分布
bpftrace -e '
BEGIN { printf("Tracing read latency... Ctrl+C to stop\n"); }
tracepoint:syscalls:sys_enter_read {
    @start[tid] = nsecs;
}
tracepoint:syscalls:sys_exit_read /@start[tid]/ {
    @us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}
'

# 输出（微秒级延迟直方图）：
# @us:
# [4, 8)              123 |@@                              |
# [8, 16)             456 |@@@@@@@@                        |
# [16, 32)           1890 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ |
# [32, 64)            567 |@@@@@@@@@                       |
# [64, 128)           234 |@@@@                            |
# [128, 256)           45 |                                |
```

### 8.2 系统调用Top排行

```bash
# 统计5秒内各进程的系统调用次数排行
bpftrace -e '
tracepoint:raw_syscalls:sys_enter {
    @[comm] = count();
}
interval:s:5 {
    print(@, 20);
    clear(@);
}
'
```

### 8.3 内核函数耗时直方图

```bash
# 追踪 vfs_read 调用耗时（纳秒 → 微秒）
bpftrace -e '
kprobe:vfs_read { @start[tid] = nsecs; }
kretprobe:vfs_read /@start[tid]/ {
    $dur = nsecs - @start[tid];
    @vfs_read_us = hist($dur / 1000);
    @slow_reads = lhist($dur / 1000, 0, 1000, 10);
    delete(@start[tid]);
}
'
```

### 8.4 TCP连接追踪

```bash
# 追踪 TCP 连接建立耗时 + 目标地址
bpftrace -e '
#include <net/sock.h>
kprobe:tcp_v4_connect {
    @start[tid] = nsecs;
    @addr[tid] = ((struct sockaddr_in *)arg1)->sin_addr.s_addr;
}
kretprobe:tcp_v4_connect /@start[tid]/ {
    $lat = (nsecs - @start[tid]) / 1000000;
    $a = @addr[tid];
    printf("connect %-15r -> %d.%d.%d.%d  %dms\n",
        comm, $a & 0xff, ($a>>8)&0xff, ($a>>16)&0xff, ($a>>24)&0xff, $lat);
    @latency_ms = hist($lat);
    delete(@start[tid]);
    delete(@addr[tid]);
}
'
```

### 8.5 磁盘IO分布（per-disk）

```bash
# 按磁盘追踪 IO 大小和延迟
bpftrace -e '
tracepoint:block:block_rq_issue {
    @start[arg.dev] = nsecs;
    @size[arg.dev] = arg.bytes;
}
tracepoint:block:block_rq_complete /@start[arg.dev]/ {
    @lat_us[arg.dev] = hist((nsecs - @start[arg.dev]) / 1000);
    @io_size_kb[arg.dev] = lhist(arg.bytes / 1024, 0, 64, 4);
    delete(@start[arg.dev]);
}
'
```

### 8.6 常用bpftrace速查

```
场景                 探针                                    说明
──────────────────────────────────────────────────────────────────────
系统调用统计          tracepoint:syscalls:sys_enter_*         按 comm 统计调用次数
函数调用次数          kprobe:tcp_sendmsg                      追踪特定内核函数
CPU 火焰图            profile:hz:99                           99Hz 采样用户态栈
内存分配大小          uprobe:malloc /pid==1234/               追踪用户态函数参数
进程调度延迟          tracepoint:sched:sched_switch           统计调度切换次数
```

---

## 9. eBPF在K8s中的3大应用场景

### 场景一：网络（替代kube-proxy）

```
传统方式（kube-proxy + iptables）：
  Service创建 → iptables规则 → 每个包经过netfilter链

  问题：
  - 10000+ Service → iptables规则爆炸
  - 规则匹配 O(n)，新增Service需要重写全表
  - 每个包都走完整协议栈（TC → Netfilter → 路由）

eBPF方式（Cilium）：
  Service创建 → 更新eBPF Map → TC层直接查表重定向

  优势：
  - O(1) 查找（哈希表），万级Service仍亚毫秒
  - Socket-level 重定向：客户端 Socket 直连后端 Pod
  - 连接跟踪 per-CPU 优化，无锁竞争
  - 不经过 iptables，减少 30-50% 延迟
```

### 场景二：可观测性（无Sidecar监控）

```
传统方式（Istio/Linkerd Sidecar）：
  Pod = 业务容器 + Envoy Sidecar
  - Sidecar 劫持流量 → 性能损耗（10-20% CPU）
  - 注入 Sidecar 需要重启 Pod
  - 多一个容器增加资源开销

eBPF方式（Pixie/Cilium）：
  内核 Hook 拦截 Socket → 提取 HTTP/gRPC 请求

  优势：
  - 零侵入：不改应用代码，不注入 Sidecar
  - 零性能损耗：内核态处理，无用户态拷贝
  - 即时生效：挂载 eBPF 程序即可，无需重启 Pod
  - L7协议解析：自动识别 HTTP/gRPC/Kafka/Redis

  典型工具：
  - Pixie              K8s原生可观测性平台，无侵入追踪
  - Hubble             Cilium的流量可视化组件
  - Inspektor Gadget   K8s诊断工具集
```

### 场景三：安全（运行时威胁检测）

```
传统方式：
  - 静态策略（NetworkPolicy只看 L3/L4）
  - 事后审计（日志分析，非实时）
  - 容器逃逸检测依赖宿主机Agent

eBPF方式（Falco/Tetragon）：
  内核态监控系统调用 → 实时检测异常行为

  优势：
  - 实时检测：系统调用级别，毫秒级响应
  - 容器感知：知道是哪个 Pod/Container 的行为
  - L7安全策略：HTTP路径级访问控制
  - 阻断能力：Tetragon 支持内核态实时阻断

  典型场景：
  - 容器逃逸        检测 ptrace/mount 系统调用
  - 提权检测        监控 setuid/setgid
  - 文件篡改        监控 /etc/passwd、/etc/shadow 写入
  - 反弹Shell       监控异常 execve + socket 组合
  - 加密货币挖矿    监控异常进程启动 + CPU突增
```

---

## 📚 相关阅读

- [01_Kubernetes进阶实战](../19_云原生技术/01_Kubernetes进阶实战.md)
- [05_云原生可观测性](../19_云原生技术/05_云原生可观测性.md)
- [04_监控告警体系](../18_DevOps与CICD/04_监控告警体系.md)

### 外部资源

- [eBPF官方文档](https://ebpf.io/)
- [Cilium文档](https://docs.cilium.io/)
- [bpftrace参考指南](https://github.com/iovisor/bpftrace)
- [BCC工具集](https://github.com/iovisor/bcc)
- [Libbpf Bootstrap](https://github.com/libbpf/libbpf-bootstrap)
- [eBPF for Kubernetes（Cilium博客）](https://cilium.io/blog/)

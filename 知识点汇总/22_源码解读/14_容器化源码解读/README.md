# 容器化源码解读

> Docker、Kubernetes、Istio核心源码解析

---

## 📋 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 21.1_Docker源码解析.md | 镜像分层（OverlayFS）、容器运行时（runc）、网络模型（bridge/overlay） | ⭐⭐⭐ | 📄 待补充 |
| 21.2_Kubernetes源码解析.md | Pod调度（Scheduler）、Informer机制、Controller Manager、kubelet | ⭐⭐⭐⭐ | 📄 待补充 |
| 21.3_Istio源码解析.md | Envoy拦截（iptables）、VirtualService路由、熔断策略、xDS协议 | ⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **理解Docker原理**：Namespace六种隔离（PID/NET/IPC/MOUNT/UTS/USER）、Cgroup资源限制（CPU/MEM/IO）、UnionFS分层存储（OverlayFS的lowerdir/upperdir/merged）
2. **掌握K8s调度**：调度器Filter→Score→Bind流程、Informer List-Watch机制、Controller Manager的调谐循环（Reconcile Loop）、kubelet的PLEG（Pod Lifecycle Event Generator）
3. **理解Istio**：Sidecar注入（MutatingWebhook）、流量劫持（iptables REDIRECT）、xDS协议下发配置（LDS/RDS/CDS/EDS）、Envoy过滤器链

---

## 📐 核心架构图

### Docker 架构图（Namespace + Cgroup + UnionFS）

```
┌──────────────────────────────────────────────────────────┐
│                     Docker Daemon                        │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  REST API   │  │  Image Mgmt  │  │   Network Mgmt │ │
│  │  (dockerd)  │  │  (layered)   │  │   (libnetwork) │ │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘ │
│         │                │                  │          │
│  ┌──────┴────────────────┴──────────────────┴────────┐ │
│  │              containerd (高级运行时)                │ │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────────┐ │ │
│  │  │  Task    │  │  Content  │  │   Snapshot     │ │ │
│  │  │  Manager │  │  Store    │  │   (OverlayFS)  │ │ │
│  │  └────┬─────┘  └───────────┘  └────────────────┘ │ │
│  │       │  ┌──────────────────────────────────────┐ │ │
│  │       └──│ runc (OCI低级运行时)                  │ │ │
│  │          │  ┌─────────────────────────────────┐ │ │ │
│  │          │  │  Namespace (隔离)                │ │ │ │
│  │          │  │  PID | NET | IPC | MOUNT | UTS  │ │ │ │
│  │          │  └─────────────────────────────────┘ │ │ │
│  │          │  ┌─────────────────────────────────┐ │ │ │
│  │          │  │  Cgroup (限制)                   │ │ │ │
│  │          │  │  cpu.shares | memory.limit_in_bytes│ │ │
│  │          │  └─────────────────────────────────┘ │ │ │
│  │          └──────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘

镜像分层结构 (OverlayFS):
┌─────────────────────────────┐
│        merged (容器视角)     │  ← 容器看到的统一文件系统
├─────────────────────────────┤
│  upperdir (可写层, 容器独有) │  ← Copy-on-Write, 修改写这里
├─────────────────────────────┤
│  lowerdir (只读, 镜像各层)   │  ← overlay2可多层lowerdir堆叠
│  [layer3: app code]         │
│  [layer2: apt install]      │
│  [layer1: base image]       │
└─────────────────────────────┘
```

### K8s 组件交互图

```
┌─────────────────────────────── Control Plane (Master) ──────────────────────────────┐
│                                                                                     │
│   ┌──────────┐     ┌──────────────────┐     ┌──────────────────┐                   │
│   │ kubectl  │────▶│   kube-apiserver │◀───▶│    etcd (Raft)   │                   │
│   │ (CLI)    │     │  (REST/gRPC)     │     │   (唯一存储)      │                   │
│   └──────────┘     └────────┬─────────┘     └──────────────────┘                   │
│                             │                                                      │
│              ┌──────────────┼──────────────┐                                      │
│              ▼              ▼              ▼                                      │
│   ┌────────────────┐ ┌────────────┐ ┌──────────────────┐                          │
│   │ Scheduler      │ │ Controller │ │ Cloud Controller │                          │
│   │ Filter→Score   │ │ Manager    │ │ Manager          │                          │
│   │ →Bind          │ │ (N个Reconcile│ │                  │                          │
│   │                │ │  Loop)      │ │                  │                          │
│   └────────────────┘ └────────────┘ └──────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                        │ Watch (List-Watch)
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │  Node 1          │ │  Node 2          │ │  Node N          │
         │ ┌──────────────┐ │ │ ┌──────────────┐ │ │ ┌──────────────┐ │
         │ │  kubelet     │ │ │ │  kubelet     │ │ │ │  kubelet     │ │
         │ │ (PLEG监控Pod)│ │ │ │              │ │ │ │              │ │
         │ ├──────────────┤ │ │ ├──────────────┤ │ │ ├──────────────┤ │
         │ │ kube-proxy   │ │ │ │ kube-proxy   │ │ │ │ kube-proxy   │ │
         │ │ (iptables/   │ │ │ │              │ │ │ │              │ │
         │ │  IPVS)       │ │ │ │              │ │ │ │              │ │
         │ ├──────────────┤ │ │ ├──────────────┤ │ │ ├──────────────┤ │
         │ │ Pod A  Pod B │ │ │ │ Pod C  Pod D │ │ │ │ Pod E        │ │
         │ │ ┌───┐ ┌───┐  │ │ │ │ ┌───┐ ┌───┐  │ │ │ │ ┌───┐       │ │
         │ │ │P1│ │P1│  │ │ │ │ │P1│ │P1│  │ │ │ │ │P1│       │ │
         │ │ │P2│ │P2│  │ │ │ │ │P2│ │P2│  │ │ │ │ │P2│       │ │
         │ │ └───┘ └───┘  │ │ │ │ └───┘ └───┘  │ │ │ │ └───┘       │ │
         │ └──────────────┘ │ │ └──────────────┘ │ │ └──────────────┘ │
         │  containerd/runc │ │  containerd/runc │ │  containerd/runc │
         └──────────────────┘ └──────────────────┘ └──────────────────┘

Informer机制 (Controller内部):
  Reflector ──List()──▶ LocalStore (缓存)
            ──Watch()──▶ Delta FIFO Queue ──▶ Indexer ──▶ Reconcile Loop
  (List全量 + Watch增量 = 本地缓存与etcd最终一致)
```

### Istio 流量劫持图 (iptables)

```
┌─────────────────── Pod 网络命名空间 ──────────────────────┐
│                                                          │
│  应用容器 (app:8080)          Sidecar (envoy:15001)      │
│  ┌──────────────┐             ┌──────────────────────┐  │
│  │  application │             │     Envoy Proxy       │  │
│  │  listen 8080 │             │  listen 15001(入站)   │  │
│  │              │             │  listen 15006(出站)   │  │
│  └──────┬───────┘             └──────────┬───────────┘  │
│         │                                │              │
│  ───────┴──── iptables NAT 链 ──────────┴──────         │
│                                                          │
│  PREROUTING (入站流量)                                    │
│    └─ ISTIO_INBOUND                                      │
│         └─ REDIRECT → 15006 (envoy入站监听)              │
│                                                          │
│  OUTPUT (出站流量)                                        │
│    └─ ISTIO_OUTPUT                                       │
│         ├─ 目标是15001/15006 → RETURN (跳过劫持)         │
│         ├─ UID=istio-proxy → ISTIO_OUTPUT (envoy自身)    │
│         └─ 其他 → REDIRECT → 15001 (envoy出站监听)       │
│                                                          │
│  流量路径:                                                │
│  入站: 外部 → PREROUTING → 15006(envoy) → 8080(app)     │
│  出站: app:随机端口 → OUTPUT → 15001(envoy) → 外部       │
│                                                          │
│  特殊: ISTIO_REDIRECT链设置了--preserve-mark保持原始目的 │
│        envoy通过SO_ORIGINAL_DST获取真实目标地址          │
└──────────────────────────────────────────────────────────┘
```

---

## 📖 学习路径

```
阶段一: Docker基础原理
  ↓  Namespace隔离 + Cgroup限制 + OverlayFS分层
  ↓  理解容器本质: 容器=受限的进程, 不是轻量虚拟机
阶段二: K8s核心机制
  ↓  Informer(List-Watch) → Controller(Reconcile) → Scheduler(Filter-Score-Bind)
  ↓  理解声明式API: 期望状态 vs 实际状态 → 调谐循环
阶段三: Istio服务网格
  ↓  iptables劫持 → Envoy过滤器链 → xDS动态配置
  ↓  理解Sidecar模式: 无侵入流量治理
阶段四: 进阶
  ↓  Containerd/CRI-O运行时、CNI网络插件、CSI存储插件
```

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐ 高频：
- Docker的Namespace和Cgroup分别做什么？容器和虚拟机的本质区别？
- Docker镜像如何分层？OverlayFS的Copy-on-Write原理？
- K8s的Pod调度流程？如何指定调度策略？（nodeSelector/Affinity/Taint-Toleration）
- K8s的Informer机制？List-Watch为什么不全用Watch？（List做全量同步防丢事件）
- K8s Controller的Reconcile Loop？为什么用最终一致而非立即同步？
- Istio的Sidecar如何劫持流量？iptables规则链如何设置？
- 容器和虚拟机的本质区别？（共享内核 vs 独立内核, 进程隔离 vs 硬件虚拟化）

⭐⭐⭐ 中频：
- kubelet的PLEG机制？如何感知Pod状态变化？
- K8s Service的ClusterIP如何工作？（kube-proxy + iptables/IPVS）
- Docker network模式有哪些？bridge和overlay的区别？
- Istio的xDS协议？LDS/RDS/CDS/EDS分别下发什么配置？
- Pod的QoS等级？ Guaranteed/Burstable/BestEffort如何影响驱逐？
- containerd和Docker的关系？为什么K8s弃用Docker？(CRI接口标准化)
```

---

*最后更新：2026-07-13*

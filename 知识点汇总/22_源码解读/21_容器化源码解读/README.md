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

1. **理解Docker原理**：Namespace隔离、Cgroup限制、UnionFS分层存储
2. **掌握K8s调度**：调度器Filter→Score→Bind流程、Informer List-Watch机制
3. **理解Istio**：Sidecar注入、流量劫持、xDS下发配置

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐ 高频：
- Docker的Namespace和Cgroup分别做什么？
- K8s的Pod调度流程？如何指定调度策略？
- K8s的Informer机制？List-Watch原理？
- Istio的Sidecar如何劫持流量？
- 容器和虚拟机的本质区别？
```

---

*最后更新：2026-07-13*

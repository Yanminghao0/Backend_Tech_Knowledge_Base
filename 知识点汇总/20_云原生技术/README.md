# 20_云原生技术

> 云原生时代的容器编排、服务网格与可观测性

---

## 📚 目录结构

```
20_云原生技术/
├── README.md                          # 本文件
├── Kubernetes进阶实战.md              # K8s进阶：调度、存储、网络、安全
├── Service Mesh(Istio)详解.md         # 服务网格：流量管理、安全、可观测性
├── Serverless架构详解.md              # 无服务器架构：Knative、云函数
└── 云原生可观测性.md                  # 可观测性三支柱：日志、指标、追踪
```

---

## 🎯 学习路径

### 阶段1：Kubernetes进阶 ⭐⭐⭐⭐⭐
**学习重点**：
- Pod调度策略（亲和性、污点、优先级）
- 存储管理（PV、PVC、StorageClass）
- 网络模型（CNI、Service、Ingress）
- 安全机制（RBAC、NetworkPolicy、PSP）
- 集群运维（备份恢复、升级、监控）

**实战项目**：
- 部署高可用K8s集群
- 实现多租户隔离
- 配置自动扩缩容（HPA、VPA）

---

### 阶段2：Service Mesh（Istio） ⭐⭐⭐⭐⭐
**学习重点**：
- Istio架构（数据面、控制面）
- 流量管理（路由、重试、超时、熔断）
- 安全（mTLS、JWT、RBAC）
- 可观测性（Metrics、Logging、Tracing）
- 灰度发布（蓝绿、金丝雀、A/B测试）

**实战项目**：
- 部署Istio服务网格
- 实现金丝雀发布
- 配置全链路追踪

---

### 阶段3：Serverless架构 ⭐⭐⭐⭐
**学习重点**：
- Serverless原理与优势
- Knative核心组件（Serving、Eventing、Build）
- 云函数开发（阿里云FC、AWS Lambda）
- 事件驱动架构
- 冷启动优化

**实战项目**：
- 部署Knative应用
- 开发云函数API
- 实现事件驱动架构

---

### 阶段4：云原生可观测性 ⭐⭐⭐⭐⭐
**学习重点**：
- 可观测性三支柱（Logging、Metrics、Tracing）
- Prometheus监控体系
- ELK/EFK日志收集
- Jaeger/Zipkin全链路追踪
- Grafana可视化

**实战项目**：
- 搭建Prometheus+Grafana监控
- 部署EFK日志收集
- 实现全链路追踪

---

## 📊 知识图谱

```
云原生技术
│
├── 容器编排 (Kubernetes)
│   ├── 基础概念 → 10_容器化/Docker与Kubernetes详解.md
│   ├── 进阶实战 → Kubernetes进阶实战.md
│   └── 生产运维
│
├── 服务网格 (Service Mesh)
│   ├── Istio架构
│   ├── 流量管理
│   ├── 安全策略
│   └── 可观测性
│
├── Serverless
│   ├── Knative
│   ├── 云函数
│   └── 事件驱动
│
└── 可观测性
    ├── 日志 (ELK/EFK)
    ├── 指标 (Prometheus/Grafana)
    └── 追踪 (Jaeger/Zipkin)
```

---

## 🔗 关联章节

### 前置知识
- **10_容器化** → Docker基础、K8s入门
- **06_微服务** → 微服务架构基础
- **08_网络通信** → HTTP、gRPC协议

### 后续应用
- **14_架构设计** → 云原生架构设计
- **11_性能优化** → 云原生应用性能优化
- **19_DevOps与CI/CD** → 云原生CI/CD

---

## 💡 学习建议

### 1. 循序渐进
```
Docker基础 
  → K8s入门 
  → K8s进阶 
  → Service Mesh 
  → Serverless 
  → 可观测性
```

### 2. 实战为主
- ✅ 搭建本地K8s集群（Minikube、Kind）
- ✅ 部署微服务应用到K8s
- ✅ 实践Istio流量管理
- ✅ 搭建监控告警体系

### 3. 关注生态
- Kubernetes生态（Helm、Operator、CRD）
- CNCF项目（Prometheus、Envoy、Jaeger）
- 云厂商方案（阿里云ACK、腾讯云TKE）

---

## 🎯 能力目标

### 初级（1-2年）
- ✅ 理解K8s核心概念
- ✅ 能够部署应用到K8s
- ✅ 使用Helm管理应用
- ✅ 配置基础监控告警

### 中级（3-5年）
- ✅ 精通K8s调度、存储、网络
- ✅ 能够设计高可用K8s集群
- ✅ 掌握Istio流量管理
- ✅ 实现全链路追踪

### 高级（5年+）
- ✅ 能够定制K8s Operator
- ✅ 设计云原生架构
- ✅ 优化Serverless性能
- ✅ 构建完整可观测性体系

---

## 📖 推荐资源

### 官方文档
- [Kubernetes官方文档](https://kubernetes.io/docs/)
- [Istio官方文档](https://istio.io/docs/)
- [Knative官方文档](https://knative.dev/docs/)

### 开源项目
- [Kubernetes](https://github.com/kubernetes/kubernetes)
- [Istio](https://github.com/istio/istio)
- [Prometheus](https://github.com/prometheus/prometheus)

### 实战课程
- 极客时间《深入剖析Kubernetes》
- 《Kubernetes in Action》
- 《Istio实战指南》

---

## ⚡ 快速导航

| 文档 | 难度 | 重要性 | 预计学习时间 |
|------|------|--------|-------------|
| [Kubernetes进阶实战](./Kubernetes进阶实战.md) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 2-3周 |
| [Service Mesh(Istio)详解](./Service%20Mesh(Istio)详解.md) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 2-3周 |
| [Serverless架构详解](./Serverless架构详解.md) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 1-2周 |
| [云原生可观测性](./云原生可观测性.md) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1-2周 |

---

## 🔥 面试高频

### Kubernetes
- Pod调度策略有哪些？如何实现亲和性调度？
- K8s网络模型是什么？Service和Ingress的区别？
- 如何实现K8s的水平扩缩容（HPA）？
- K8s如何保证应用的高可用？

### Istio
- Istio的架构是什么？数据面和控制面的职责？
- 如何使用Istio实现金丝雀发布？
- Istio如何实现服务间的mTLS？
- 什么是流量镜像？有什么用？

### Serverless
- Serverless的优缺点是什么？
- 如何优化Serverless的冷启动？
- Knative的核心组件有哪些？
- 什么场景适合使用Serverless？

### 可观测性
- 可观测性三支柱是什么？
- Prometheus的架构和存储模型？
- 如何实现全链路追踪？
- 如何设计合理的监控指标？

---

**更新时间**: 2025-10-29  
**版本**: v1.0  
**作者**: Java高级工程师知识库


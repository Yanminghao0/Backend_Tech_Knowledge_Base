# Docker与K8s面试题

> 云原生时代面试标配：Docker原理/K8s核心概念/故障排查

---

## 📋 目录

1. [Docker基础](#1-docker基础)
2. [Docker原理](#2-docker原理)
3. [Dockerfile最佳实践](#3-dockerfile最佳实践)
4. [Docker网络与存储](#4-docker网络与存储)
5. [K8s核心概念](#5-k8s核心概念)
6. [K8s调度与运维](#6-k8s调度与运维)
7. [面试题速查](#7-面试题速查)

---

## 1. Docker基础

**Q: 容器 vs 虚拟机？**

| 维度 | 容器 | 虚拟机 |
|------|------|--------|
| 隔离级别 | 进程级(OS隔离) | 硬件级(完整OS) |
| 启动 | 秒级 | 分钟级 |
| 资源占用 | MB级 | GB级 |
| 性能 | 接近原生 | 有虚拟化开销 |
| 镜像大小 | MB | GB |
| 隔离性 | 弱(共享内核) | 强(独立内核) |

---

## 2. Docker原理

**Q: Docker底层技术？**

```
1. Namespace(命名空间): 隔离
   PID:   进程隔离(容器内PID=1)
   NET:   网络隔离(独立网卡/IP/端口)
   IPC:   进程间通信隔离
   MNT:   挂载点隔离(独立文件系统)
   UTS:   主机名隔离
   USER:  用户隔离

2. Cgroups(控制组): 资源限制
   CPU/内存/IO/网络带宽限制

3. UnionFS(联合文件系统): 镜像分层
   Overlay2(默认): upperdir(可写层) + lowerdir(只读层) + merged(合并视图)
   每层只存差异(Copy-on-Write)
```

---

## 3. Dockerfile最佳实践

**Q: 常用Dockerfile指令？最佳实践？**

```dockerfile
# 多阶段构建(减小镜像体积)
FROM maven:3.9-eclipse-temurin-17 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline           # 先下依赖(利用缓存)
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine       # 运行时用JRE(更小)
WORKDIR /app
COPY --from=builder /app/target/app.jar .
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]

# 最佳实践:
# 1. 用alpine/slim基础镜像(减小体积)
# 2. .dockerignore排除不需要的文件
# 3. 依赖COPY在前，源码COPY在后(利用层缓存)
# 4. 合并RUN命令(减少层数)
# 5. 非root用户运行(USER appuser)
# 6. 多阶段构建(构建环境≠运行环境)
```

**Q: COPY vs ADD？**

```
COPY: 纯复制文件到镜像(推荐)
ADD:  复制+自动解压tar+支持URL(不推荐用URL)
区别: ADD会自动解压.tar.gz，COPY不会
建议: 统一用COPY，需要解压时手动RUN tar
```

---

## 4. Docker网络与存储

**Q: Docker网络模式？**

| 模式 | 说明 | 场景 |
|------|------|------|
| bridge(默认) | 虚拟网桥，容器间通过NAT通信 | 开发/默认 |
| host | 容器直接用宿主机网络(无隔离) | 性能要求高 |
| none | 无网络 | 安全隔离 |
| overlay | 跨主机容器通信(Swarm/K8s) | 集群 |
| macvlan | 容器有独立MAC地址 | 物理网络集成 |

**Q: Volume vs Bind Mount？**

```
Volume: Docker管理(/var/lib/docker/volumes)
  优点: 独立于宿主机路径/可跨平台/支持备份/可命名
  场景: 数据库数据/应用数据持久化

Bind Mount: 直接挂载宿主机目录
  优点: 简单直接
  缺点: 依赖宿主机路径/权限问题
  场景: 开发时挂载源码热重载
```

---

## 5. K8s核心概念

**Q: K8s核心组件？**

```
控制面(Control Plane):
  etcd: 键值存储(集群状态)
  kube-apiserver: API入口(所有操作经过它)
  kube-scheduler: 调度Pod到Node
  kube-controller-manager: 控制器(Deployment/ReplicaSet等)
  kube-cloud-controller-manager: 云平台集成

工作节点(Node):
  kubelet: 管理本节点Pod生命周期(向APIServer汇报)
  kube-proxy: 网络代理(Service负载均衡/iptables/IPVS)
  容器运行时: containerd/CRI-O(运行容器)
```

**Q: Pod/Deployment/Service关系？**

```
Pod: 最小调度单位，包含1-N个容器(共享网络/存储)
  生命周期: Pending→Running→Succeeded/Failed
  特点: 临时性(重启后数据丢失)，用Volume持久化

Deployment: 管理Pod的副本集(声明式)
  滚动更新: 逐个替换旧Pod(可控制速率/暂停/回滚)
  伸缩: kubectl scale deployment xxx --replicas=5

Service: 为Pod提供稳定的网络入口(标签选择器)
  ClusterIP: 集群内部访问(默认)
  NodePort: 节点端口映射(30000-32767)
  LoadBalancer: 云厂商负载均衡器
  Headless: 直接返回Pod IP(StatefulSet用)

流量链路: 外部 → Ingress → Service → Pod
```

**Q: ConfigMap vs Secret？**

```
ConfigMap: 非敏感配置(数据库地址/feature开关)
Secret:    敏感数据(密码/证书/Token)，Base64编码(非加密)
  类型: Opaque/TLS/Docker Registry/ServiceAccount Token
  使用: 环境变量注入 / Volume挂载

生产建议: Secret配合云KMS/AES加密(etcd加密存储)
```

---

## 6. K8s调度与运维

**Q: Pod状态Pending/CrashLoopBackOff怎么排查？**

```bash
# Pending(无法调度):
kubectl describe pod <name>  # 看Events
# 常见原因: 资源不足/节点污点/调度约束/镜像拉取失败

# CrashLoopBackOff(反复崩溃):
kubectl logs <name> --previous  # 看上次崩溃的日志
# 常见原因: 应用启动失败/配置错误/依赖服务不可达/健康检查失败

# ImagePullBackOff(镜像拉取失败):
# 检查镜像名/Tag/仓库认证/网络
```

**Q: 常用kubectl命令？**

```bash
kubectl get pods -o wide              # 查看Pod(含IP/Node)
kubectl get deployment                # 查看Deployment
kubectl describe pod <name>           # 详情(Events很重要)
kubectl logs <name> -f --tail=100     # 实时日志
kubectl exec -it <name> -- sh         # 进入容器
kubectl scale deployment xxx --replicas=5  # 伸缩
kubectl rollout restart deployment xxx     # 滚动重启
kubectl rollout undo deployment xxx        # 回滚
kubectl top pod                       # 资源使用(需metrics-server)
```

**Q: 健康检查机制？**

```
Liveness Probe(存活探针): 失败→重启Pod
  httpGet: HTTP 200=健康
  tcpSocket: TCP连接成功=健康
  exec: 退出码0=健康

Readiness Probe(就绪探针): 失败→从Service摘除(不重启)
  Pod启动慢时用Readiness，就绪前不接收流量

Startup Probe(启动探针): 启动期间禁用Liveness/Readiness
  适用: 启动慢的应用(JVM预热)
```

---

## 7. 面试题速查

**Q1: 容器 vs 虚拟机？**
```
进程级隔离(秒启动MB级) vs 硬件级隔离(分钟启动GB级)
```

**Q2: Docker底层？**
```
Namespace隔离 + Cgroups限制 + UnionFS分层
```

**Q3: Dockerfile最佳实践？**
```
多阶段构建/alpine基础镜像/依赖COPY在前/非root运行
```

**Q4: K8s Pod/Deployment/Service？**
```
Pod=最小调度单位, Deployment=管理副本, Service=稳定网络入口
```

**Q5: Pod Pending？**
```
kubectl describe看Events → 资源不足/污点/调度约束/镜像拉取失败
```

**Q6: CrashLoopBackOff？**
```
kubectl logs --previous看崩溃日志 → 配置错误/依赖不可达/健康检查失败
```

**Q7: Liveness vs Readiness？**
```
Liveness失败重启Pod, Readiness失败摘除流量不重启
```

**Q8: K8s滚动更新？**
```
Deployment逐个替换Pod, maxSurge/maxUnavailable控制速率, 支持回滚
```

---

*最后更新: 2026-07-14*

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

## 8. 补充面试题

**Q: Docker镜像如何分层存储？**

```
镜像 = 多个只读层(Layer)叠加

构建过程:
  FROM openjdk:17          → 基础层(300MB)
  COPY app.jar /app/       → 新增层(50MB)
  RUN apt install curl     → 新增层(10MB)

容器运行: 在镜像层之上加一个可写层(Container Layer)
  修改文件时: Copy-on-Write, 复制到可写层修改

为什么分层:
  1. 复用: 多个镜像共享基础层, 节省存储
  2. 缓存: 构建时未变化的层使用缓存, 加速构建
  3. 传输: 只传输变化的层(docker push/pull)

查看分层: docker history <image>
```

**Q: Docker Compose常用场景？**

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports: ["8080:8080"]
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - REDIS_HOST=redis
    depends_on:
      - mysql
      - redis
    restart: always

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root123
    volumes:
      - mysql_data:/var/lib/mysql
    ports: ["3306:3306"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  mysql_data:

# 命令:
# docker-compose up -d        # 启动全部
# docker-compose down          # 停止并删除
# docker-compose logs -f app   # 查看日志
# docker-compose restart app   # 重启单个服务
```

**Q: K8s中Pod内容器共享什么？**

```
Pod内多个容器共享:
  1. 网络: 相同IP和端口空间(可通过localhost互访)
  2. 存储: 共享Volume挂载
  3. IPC: 共享进程间通信

不共享:
  1. PID命名空间(默认隔离, shareProcessNamespace可开启)
  2. 文件系统(各自隔离, 除共享Volume)

设计模式(Sidecar):
  主容器: 业务应用
  Sidecar: 日志收集/监控Agent/配置同步/Service Mesh代理
```

**Q: K8s Service负载均衡原理？**

```
Service通过Label Selector关联Pod:
  Service(selector: app=order) → Pod(app=order)

ClusterIP:
  虚拟IP, 通过kube-proxy的iptables/IPVS规则转发到Pod
  iptables: 随机选Pod DNAT
  IPVS: 更高效的负载均衡(rr/wrr/lc/sh等算法)

kube-proxy模式:
  iptables(默认): 规则链, 大量Service时性能下降
  ipvs: 内核级LB, 万级Service仍高效(推荐生产)
  ebpf: Cilium等替代kube-proxy(最高性能)

DNS: CoreDNS自动为Service创建DNS记录
  my-service.my-namespace.svc.cluster.local
```

**Q: K8s滚动更新和回滚？**

```bash
# 滚动更新(修改镜像)
kubectl set image deployment/app container=app:v2

# 更新策略
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%         # 最多多创建25%的Pod
      maxUnavailable: 25%   # 最多25%不可用

# 查看更新状态
kubectl rollout status deployment/app

# 暂停/恢复
kubectl rollout pause deployment/app
kubectl rollout resume deployment/app

# 回滚
kubectl rollout undo deployment/app              # 回滚到上一版本
kubectl rollout undo deployment/app --to-revision=2  # 回滚到指定版本
kubectl rollout history deployment/app           # 查看历史版本
```

**Q: K8s资源限制和QoS？**

```yaml
resources:
  requests:          # 调度依据(保证最小资源)
    cpu: "500m"      # 0.5核
    memory: "512Mi"
  limits:            # 上限(超过CPU限流, 内存超过OOMKill)
    cpu: "1000m"     # 1核
    memory: "1Gi"
```

```
QoS等级(决定Pod在资源不足时的驱逐顺序):
  Guaranteed: requests=limits (最后被驱逐)
  Burstable:   requests < limits (中间)
  BestEffort:  没有设置requests/limits (最先被驱逐)

CPU单位: 1核=1000m, 500m=0.5核
内存: Mi/Gi(MiB/GiB), M/G(MB/GB)
```

---

## 7. 更多面试题

**Q: Docker多阶段构建的原理和好处？**

```dockerfile
# 第一阶段: 构建(用大镜像, 有Maven/JDK)
FROM maven:3.9-eclipse-temurin-17 AS builder
COPY src ./src
COPY pom.xml .
RUN mvn package -DskipTests

# 第二阶段: 运行(用小镜像, 只有JRE)
FROM eclipse-temurin:17-jre-alpine
COPY --from=builder /target/app.jar /app/app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

好处:
  - 构建环境与运行环境隔离(Builder有Maven/JDK, 运行只需JRE)
  - 镜像从800MB→200MB(去掉构建工具/源码/缓存)
  - 安全性更高(不含编译器/源码)

**Q: K8s StatefulSet vs Deployment？**

```
Deployment: 无状态应用(Web/API)
  - Pod可替换(名称随机, IP随机)
  - 适合: 前端/API/微服务
  - 持久化: 通过PVC共享

StatefulSet: 有状态应用(数据库/MQ)
  - Pod有稳定标识(pod-0, pod-1, pod-2)
  - 有序创建/删除(0→1→2启动, 2→1→0停止)
  - 每个Pod独立PVC(数据不共享)
  - 稳定DNS: pod-0.service.namespace.svc.cluster.local
  - 适合: MySQL主从/Redis集群/ZooKeeper/ElasticSearch
```

**Q: K8s ConfigMap热更新？**

```
ConfigMap更新后:
  1. 环境变量注入: 不会自动更新(需重启Pod)
  2. Volume挂载: 自动更新(约10-60秒 kubelet同步)
     → 但应用需要感知文件变化(如Spring Cloud的@RefreshScope)

生产推荐:
  - 配置变更: Nacos/Apollo(配置中心) 热推送
  - K8s ConfigMap: 启动配置/不常变配置
  - 避免依赖ConfigMap热更新(延迟不可控)
```

---

*最后更新: 2026-07-14*

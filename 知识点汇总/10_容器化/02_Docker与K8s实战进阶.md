# Docker与Kubernetes实战进阶

> 从Dockerfile最佳实践到K8s生产调优，容器化全链路实战指南

---

## 📋 目录

1. [Dockerfile最佳实践](#1-dockerfile最佳实践)
2. [多阶段构建](#2-多阶段构建)
3. [K8s部署实战](#3-k8s部署实战)
4. [Helm包管理](#4-helm包管理)
5. [K8s调优](#5-k8s调优)
6. [面试要点](#6-面试要点)

---

## 1. Dockerfile最佳实践

### 镜像分层原理

```
每条Dockerfile指令生成一层（Layer）
Layer是只读的，上层覆盖下层
相同Layer会被缓存复用（Build Cache）

优化目标：
1. 减少层数（合并RUN指令）
2. 利用缓存（不频繁变化的放前面）
3. 减小镜像体积（清理临时文件）
```

### Java应用Dockerfile最佳实践

```dockerfile
# 基础镜像：使用Eclipse Temurin（比openjdk更小）
FROM eclipse-temurin:21-jre-alpine AS base

# 设置时区
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 创建非root用户
RUN addgroup -S app && adduser -S app -G app
USER app

# 复制应用（利用缓存：依赖JAR和业务JAR分开）
COPY --chown=app:app target/*.jar /app/application.jar

# JVM参数
ENV JAVA_OPTS="-XX:MaxRAMPercentage=75.0 \
  -XX:+UseG1GC \
  -XX:MaxGCPauseMillis=200 \
  -Djava.security.egd=file:/dev/./urandom"

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/application.jar"]
```

### 常见反模式

```dockerfile
# ❌ 反模式1: 使用大基础镜像
FROM ubuntu:22.04          # 77MB，太大
# ✅ 正确:
FROM eclipse-temurin:21-jre-alpine  # 120MB，包含JRE

# ❌ 反模式2: 频繁变化的层放前面
COPY src/ /app/src/        # 代码频繁变化，放前面导致缓存失效
COPY pom.xml /app/
# ✅ 正确: 先COPY不变的部分
COPY pom.xml /app/
COPY src/ /app/src/

# ❌ 反模式3: 不清理构建缓存
RUN apt-get update && apt-get install -y maven
# ✅ 正确: 清理缓存
RUN apt-get update && apt-get install -y --no-install-recommends maven \
    && rm -rf /var/lib/apt/lists/*

# ❌ 反模式4: 以root运行
# ✅ 正确: 创建非root用户
RUN addgroup -S app && adduser -S app -G app
USER app
```

---

## 2. 多阶段构建

### Spring Boot多阶段构建

```dockerfile
# 阶段1: 构建
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline                    # 缓存依赖
COPY src/ ./src/
RUN mvn package -DskipTests -Dmaven.test.skip=true

# 阶段2: 运行（使用分层JAR优化）
FROM eclipse-temurin:21-jre-alpine AS runtime
RUN addgroup -S app && adduser -S app -G app
USER app
WORKDIR /app

# Spring Boot分层提取
COPY --from=builder /build/target/*.jar app.jar
RUN java -Djarmode=layertools -jar app.jar extract

COPY --from=builder /build/target/dependencies/ ./
COPY --from=builder /build/target/spring-boot-loader/ ./
COPY --from=builder /build/target/snapshot-dependencies/ ./
COPY --from=builder /build/target/application/ ./

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

### Native Image构建

```dockerfile
# 阶段1: Native Image编译
FROM ghcr.io/graalvm/native-image-community:21 AS builder
WORKDIR /build
COPY pom.xml .
COPY src/ ./src/
RUN ./mvnw native:compile -Pnative

# 阶段2: 极简运行镜像
FROM alpine:latest
RUN apk add --no-cache libstdc++
COPY --from=builder /build/target/myapp /app/myapp
EXPOSE 8080
ENTRYPOINT ["/app/myapp"]
# 镜像大小: ~50MB（vs JRE版 ~200MB）
```

---

## 3. K8s部署实战

### Spring Boot应用部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: registry.cn-hangzhou.aliyuncs.com/myrepo/myapp:v1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: JAVA_OPTS
          value: "-XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 20
        lifecycle:
          preStop:
            exec:
              command: ["sh", "-c", "sleep 10"]  # 优雅停机
      terminationGracePeriodSeconds: 60
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

### ConfigMap和Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  application.yml: |
    spring:
      datasource:
        url: jdbc:mysql://mysql-svc:3306/mydb
      redis:
        host: redis-svc
---
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secret
type: Opaque
stringData:
  db-password: "your-password"
  redis-password: "your-redis-password"
```

---

## 4. Helm包管理

### Helm Chart结构

```
myapp-chart/
├── Chart.yaml          # Chart元数据
├── values.yaml         # 默认配置
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── _helpers.tpl    # 模板辅助函数
└── charts/             # 依赖Chart
```

### values.yaml

```yaml
replicaCount: 3

image:
  repository: registry.cn-hangzhou.aliyuncs.com/myrepo/myapp
  tag: "1.0.0"
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 250m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  host: api.example.com
```

### 部署命令

```bash
# 安装
helm install myapp ./myapp-chart -f values-prod.yaml

# 升级
helm upgrade myapp ./myapp-chart -f values-prod.yaml

# 回滚
helm rollback myapp 2

# 卸载
helm uninstall myapp
```

---

## 5. K8s调优

### 资源管理

```yaml
# 资源请求与限制的最佳实践
resources:
  requests:
    cpu: 500m       # 保证资源（调度依据）
    memory: 1Gi
  limits:
    cpu: 2000m      # 最大资源（硬限制）
    memory: 2Gi

# OOM和CPU Throttling
# memory limit超过 → OOMKilled
# cpu limit超过 → Throttling（限流，不杀进程）
```

### HPA自动伸缩

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70    # CPU使用率超过70%扩容
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30   # 扩容快速响应
      policies:
      - type: Percent
        value: 100                      # 每次最多扩容100%
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300   # 缩容保守（5分钟）
      policies:
      - type: Percent
        value: 10                       # 每次最多缩容10%
        periodSeconds: 60
```

### 亲和性与反亲和性

```yaml
# Pod反亲和性：同一节点不部署相同应用
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: myapp
          topologyKey: kubernetes.io/hostname

# 节点亲和性：调度到特定节点
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node-role
            operator: In
            values: ["app"]
```

### 优雅停机

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
  - name: myapp
    lifecycle:
      preStop:
        exec:
          command:
          - sh
          - -c
          - |
            # 1. 从注册中心注销
            curl -X POST http://localhost:8080/actuator/service-registry
            # 2. 等待流量排空
            sleep 15
```

---

## 6. 面试要点

### Q1: Docker镜像如何优化？

```
1. 多阶段构建：构建阶段和运行阶段分离
2. 使用Alpine基础镜像（5MB vs Ubuntu 77MB）
3. 合并RUN指令，减少层数
4. 清理缓存文件（apt cache, npm cache）
5. 使用.dockerignore排除不必要文件
6. Spring Boot分层JAR（dependencies/application分层缓存）
7. GraalVM Native Image（50MB vs 200MB）
```

### Q2: K8s中Pod的启动流程？

```
1. 调度器选择节点
2. kubelet创建Pod
3. 启动init containers（按顺序）
4. 启动主containers（并行）
5. 启动postStart hook
6. readinessProbe通过 → Pod Ready → 加入Service Endpoints
7. livenessProbe持续检查 → 失败则重启
```

### Q3: K8s如何实现滚动更新？

```
Deployment滚动更新策略：
1. 创建新ReplicaSet，启动1个新Pod
2. 新Pod readinessProbe通过后，旧ReplicaSet缩容1个
3. 重复直到全部替换
4. 可配置maxSurge（超出期望副本数上限）和maxUnavailable（不可用副本数上限）

spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 滚动更新时最多多出1个
      maxUnavailable: 0    # 滚动更新时不允许减少（零停机）
```

### Q4: K8s中Service和Ingress的区别？

```
Service: 四层负载均衡（TCP/UDP），集群内访问
  - ClusterIP: 集群内访问
  - NodePort: 节点端口暴露
  - LoadBalancer: 云厂商负载均衡器

Ingress: 七层负载均衡（HTTP/HTTPS），域名路由
  - 基于域名/路径路由到不同Service
  - 支持TLS终止
  - 通常配合Nginx/Traefik Ingress Controller使用
```

### Q5: 如何排查K8s Pod异常？

```bash
# 1. 查看Pod状态
kubectl get pods -o wide
kubectl describe pod <pod-name>

# 2. 查看Pod事件
kubectl get events --field-selector involvedObject.name=<pod-name>

# 3. 查看日志
kubectl logs <pod-name> --previous   # 上次崩溃的日志
kubectl logs <pod-name> -f           # 实时日志

# 4. 进入Pod排查
kubectl exec -it <pod-name> -- /bin/sh

# 常见问题：
# ImagePullBackOff: 镜像拉取失败
# CrashLoopBackOff: 容器启动后崩溃
# OOMKilled: 内存不足被杀
# Evicted: 节点资源不足被驱逐
```

---

## 📚 相关阅读

- [01_Docker与Kubernetes详解](./01_Docker与Kubernetes详解.md)
- [Kubernetes进阶实战](../19_云原生技术/01_Kubernetes进阶实战.md)
- [JVM调优实战](../11_性能优化/01_JVM调优实战.md)
- [DevOps与CICD](../18_DevOps与CICD/README.md)

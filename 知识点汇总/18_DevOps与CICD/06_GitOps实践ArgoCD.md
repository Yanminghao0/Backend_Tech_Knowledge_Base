# GitOps实践：ArgoCD

> 声明式基础设施管理，Git作为单一真相源

---

## 📋 目录

1. [GitOps概述](#1-gitops概述)
2. [ArgoCD架构](#2-argocd架构)
3. [ArgoCD实战](#3-argocd实战)
4. [面试要点](#4-面试要点)
5. [ApplicationSet多集群部署](#5-applicationset多集群部署)
6. [Notifications配置](#6-notifications配置)
7. [Helm+ArgoCD实战](#7-helmargocd实战)
8. [Kustomize+ArgoCD](#8-kustomizeargocd)
9. [渐进式发布Argo Rollouts](#9-渐进式发布argo-rollouts)
10. [面试要点补充](#10-面试要点补充)
11. [相关阅读](#相关阅读)

---

## 1. GitOps概述

### 核心原则

```
1. 声明式：系统状态用声明式描述（YAML）
2. 版本控制：Git作为唯一真相源
3. 自动拉取：Agent自动同步Git到集群
4. 持续协调：持续检测实际状态vs期望状态
```

### GitOps vs 传统CI/CD

| 维度 | 传统CI/CD | GitOps |
|------|----------|--------|
| 部署方向 | Push（CI推送） | Pull（集群拉取） |
| 配置管理 | CI平台 | Git仓库 |
| 回滚 | 重新构建+部署 | Git revert |
| 审计 | CI日志 | Git历史 |
| 集群权限 | CI需集群凭据 | Agent在集群内 |

---

## 2. ArgoCD架构

```
┌─────────────────────────────────────────┐
│              Git仓库                     │
│  ├── deployment.yaml                     │
│  ├── service.yaml                        │
│  └── configmap.yaml                      │
└──────────────┬──────────────────────────┘
               │ 拉取
┌──────────────┴──────────────────────────┐
│            ArgoCD Server                  │
│  ┌──────────┐  ┌──────────┐             │
│  │API Server│  │  Web UI  │             │
│  └──────────┘  └──────────┘             │
│  ┌──────────┐  ┌──────────┐             │
│  │Repo Server│ │Controller│             │
│  └──────────┘  └──────────┘             │
└──────────────┬──────────────────────────┘
               │ 同步
┌──────────────┴──────────────────────────┐
│            K8s集群                       │
│  Application Controller (持续协调)       │
│  → 对比Git期望状态 vs 集群实际状态        │
│  → 不一致则同步（自动或手动）             │
└─────────────────────────────────────────┘
```

---

## 3. ArgoCD实战

### 安装

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 获取密码
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### 创建Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/myorg/myapp-k8s
    targetRevision: main
    path: manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:           # 自动同步
      prune: true         # 删除Git中已删除的资源
      selfHeal: true      # 自动修复手动修改
    syncOptions:
      - CreateNamespace=true
```

### Helm + ArgoCD

```yaml
spec:
  source:
    repoURL: https://github.com/myorg/myapp-k8s
    path: charts/myapp
    helm:
      valueFiles:
        - values-production.yaml
```

---

## 4. 面试要点

### Q1: GitOps的优势？

```
1. Git为唯一真相源：审计、版本控制、回滚
2. 集群无需暴露CI凭据：安全提升
3. 自动协调：集群漂移自动修复
4. 回滚简单：git revert → 自动同步
5. 多环境管理：不同分支对应不同环境
```

### Q2: ArgoCD的工作原理？

```
1. 监听Git仓库变更
2. 对比Git中声明的状态 vs 集群实际状态
3. 不一致时触发Sync
4. Sync = apply YAML到集群
5. 持续协调（selfHeal：手动修改会被自动修复）
```

---

## 5. ApplicationSet多集群部署

### 为什么需要ApplicationSet

单个Application只能绑定一个Git源和一个目标集群。当需要在多个集群、多命名空间批量部署同一应用时，手写N个Application既冗余又易错。ApplicationSet控制器通过「模板+生成器」自动批量创建Application。

### 核心概念

```
ApplicationSet = 生成器(Generator) + 模板(Template)
  生成器：产生参数集合（cluster名、namespace、环境变量等）
  模板：  把参数填入Application模板，渲染出N个Application
```

### 常用生成器

| 生成器 | 用途 | 典型场景 |
|--------|------|----------|
| List | 手写列表 | 少量固定集群 |
| Clusters | 读取ArgoCD已注册集群 | 多集群统一部署 |
| Git | 扫描Git目录/文件 | 每个目录一个微服务 |
| ClusterDecisionResource | 基于自定义资源 | 与GPA/Cluster API联动 |
| Pull Request | 扫描PR | 每个PR一个预览环境 |
| Matrix | 组合多个生成器 | 集群×环境笛卡尔积 |

### 实战：Git目录生成器批量部署微服务

仓库结构：

```
myorg/apps-config/
  ├── services/
  │   ├── service-a/
  │   │   └── kustomization.yaml
  │   ├── service-b/
  │   │   └── kustomization.yaml
  │   └── service-c/
  │       └── kustomization.yaml
  └── applicationset.yaml
```

ApplicationSet定义：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: microservices
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/myorg/apps-config
        revision: main
        directories:
          - path: services/*
  template:
    metadata:
      name: '{{path.basename}}'   # service-a, service-b...
    spec:
      source:
        repoURL: https://github.com/myorg/apps-config
        targetRevision: main
        path: '{{path}}'           # services/service-a
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

Git目录下每出现一个子目录，就自动生成一个Application。

### 实战：多集群 + 多环境矩阵部署

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: app-multi-env
  namespace: argocd
spec:
  generators:
    - matrix:
        generators:
          # 生成器1：集群列表
          - clusters:
              selector:
                matchLabels:
                  env: production   # 只选带env=production标签的集群
          # 生成器2：环境变量
          - list:
              elements:
                - env: prod
                  valuesFile: values-prod.yaml
                - env: staging
                  valuesFile: values-staging.yaml
  template:
    metadata:
      name: 'app-{{name}}-{{env}}'   # name来自clusters生成器
    spec:
      source:
        repoURL: https://github.com/myorg/myapp
        targetRevision: main
        path: charts/myapp
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: '{{server}}'         # server来自clusters生成器
        namespace: myapp-{{env}}
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

matrix生成器会对「集群 × 环境」做笛卡尔积，批量渲染Application。

### 注册外部集群

```bash
# 在目标集群上生成注册信息
CLUSTER_NAME=prod-cluster-east
argocd cluster add ${CLUSTER_NAME} \
  --label env=production \
  --label region=east \
  --upsert

# 查看已注册集群
argocd cluster list
```

ApplicationSet的clusters生成器会自动读取这些已注册集群。

---

## 6. Notifications配置

### 架构概览

```
Git变更 → ArgoCD检测到Drift → Application状态变化
   → Notifications Controller订阅Application事件
   → 触发Trigger（如on-deployed/on-health-degraded）
   → 渲染模板 → 发送到通知渠道（Slack/钉钉/邮件/飞书/Webhook）
```

### 安装Notifications

```bash
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj-labs/argocd-notifications/stable/manifests/install.yaml

# 将Notifications的ServiceAccount绑定到ArgoCD
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj-labs/argocd-notifications/stable/manifests/install.yaml
```

> ArgoCD v2.3+ 已内置Notifications功能，新版本无需单独安装。

### 配置Slack通知

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  # 1. 定义通知服务
  service.slack: |
    token: $slack-token    # 引用Secret中的token

  # 2. 定义触发器（何时触发）
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [deployed-template]
  trigger.on-health-degraded: |
    - when: app.status.health.status == 'Degraded'
      send: [degraded-template]

  # 3. 定义模板（发什么内容）
  template.deployed-template: |
    message: |
      ✅ {{.app.metadata.name}} 已成功部署
      同步状态: {{.app.status.sync.status}}
      健康状态: {{.app.status.health.status}}
      Git版本: {{.app.status.sync.revision}}
      详情: {{.context.argocdUrl}}/applications/{{.app.metadata.name}}
  template.degraded-template: |
    message: |
      ❌ {{.app.metadata.name}} 健康检查异常
      当前状态: {{.app.status.health.status}}
      请立即检查: {{.context.argocdUrl}}/applications/{{.app.metadata.name}}
```

### 配置Secret

```bash
# Slack Bot OAuth Token
kubectl create secret generic argocd-notifications-secret \
  -n argocd \
  --from-literal=slack-token=xoxb-xxxxxxxxxxxxxxxxxxxx

# 确保ConfigMap引用的$slack-token变量能被解析
# Notifications Controller会自动从同名Secret读取
```

### 给Application打标签订阅通知

```bash
# 给Application打上标签，订阅deployed和health-degraded触发器
argocd app set myapp \
  -l notifications.argoproj.io/subscribe.on-deployed.slack=devops-team
argocd app set myapp \
  -l notifications.argoproj.io/subscribe.on-health-degraded.slack=devops-team
```

对应到YAML，即给Application加注解：

```yaml
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-deployed.slack: devops-team
    notifications.argoproj.io/subscribe.on-health-degraded.slack: devops-team
```

### 配置钉钉/飞书Webhook

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.webhook.dingtalk: |
    url: https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx
    headers:
      - name: Content-Type
        value: application/json
  template.dingtalk-template: |
    message: |
      {
        "msgtype": "markdown",
        "markdown": {
          "title": "ArgoCD通知",
          "text": "### {{.app.metadata.name}}\n状态: {{.app.status.sync.status}}\n健康: {{.app.status.health.status}}"
        }
      }
  trigger.on-deployed: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [dingtalk-template]
```

### 常用触发器组合

| 触发器 | 条件 | 典型用途 |
|--------|------|----------|
| on-deployed | 同步成功 | 通知发布完成 |
| on-health-degraded | 健康状态降级 | 告警 |
| on-sync-failed | 同步失败 | 告警 |
| on-sync-running | 同步进行中 | 状态可见性 |
| on-sync-status-unknown | 状态未知 | 集群连接异常 |
| on-created | Application创建 | 资源审计 |

---

## 7. Helm+ArgoCD实战

### Helm在ArgoCD中的两种模式

```
模式1：Chart仓库（Helm Repository）
  ArgoCD直接从Helm Repo拉取Chart
  source.chart 指定chart名，source.repoURL指定helm repo地址

模式2：Git仓库中的Chart
  ArgoCD从Git拉取，source.path指向chart目录
  更适合GitOps：Chart源码和values都在Git里
```

### 模式1：从Helm Repository部署

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: redis
  namespace: argocd
spec:
  source:
    repoURL: https://charts.bitnami.com/bitnami   # Helm Repo地址
    chart: redis                                    # Chart名
    targetRevision: 18.0.1                          # 版本
    helm:
      releaseName: my-redis
      values: |
        architecture: replication
        auth:
          enabled: true
          password: "mysecret"
        replica:
          replicaCount: 3
  destination:
    server: https://kubernetes.default.svc
    namespace: redis
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 模式2：Git仓库中的Chart（推荐）

仓库结构：

```
myorg/myapp-config/
  ├── charts/
  │   └── myapp/
  │       ├── Chart.yaml
  │       ├── templates/
  │       └── values.yaml
  ├── values-dev.yaml
  ├── values-staging.yaml
  └── values-production.yaml
```

Application定义：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-production
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/myorg/myapp-config
    targetRevision: main
    path: charts/myapp                # 指向chart目录
    helm:
      valueFiles:
        - values-production.yaml      # 使用生产环境values
      # 传参给Helm（等价于 helm install --set）
      parameters:
        - name: image.tag
          value: v1.2.3
        - name: replicaCount
          value: "5"
      # 是否忽略缺失的value（默认false，缺失会报错）
      ignoreMissingValueFiles: false
      # 跳过CRD安装（多Application共享CRD时有用）
      skipCrds: false
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Helm+ArgoCD的多环境管理策略

```
策略A：一个Chart，多个values文件（简单场景）
  values-dev.yaml / values-staging.yaml / values-prod.yaml
  不同环境的Application引用不同valueFiles

策略B：多分支，每环境一个分支（严格隔离）
  main分支 → 生产
  staging分支 → 预发
  dev分支 → 开发
  Application的targetRevision指向对应分支

策略C：多仓库（Chart与应用配置分离）
  Chart在独立的charts仓库（版本化发布）
  应用配置在apps仓库（引用Chart版本+values）
  适合大型团队，Chart复用性强
```

### Helm hooks与ArgoCD同步

ArgoCD支持Helm的hook注解，在同步生命周期执行特定动作：

```yaml
# templates/pre-install-hook.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-migrate
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: myapp/migrate:{{ .Values.image.tag }}
          command: ["./migrate", "up"]
      restartPolicy: Never
```

ArgoCD会在Sync时先执行该Job，成功后再部署其余资源。

### 常见问题

```
Q: Helm部署的Secret会被ArgoCD「自愈」回去？
A: 是的。selfHeal=true时，任何手动kubectl edit都会被Git状态覆盖。
   如需运行时生成的Secret（如外部密钥），建议：
   1. 使用Sealed Secrets / SOPS加密后存入Git
   2. 或使用External Secrets Operator从Vault/AWS SM拉取
   3. 对这类资源设置syncOptions: - RespectIgnoreDifferences=true
      并在ignoreDifferences中声明忽略的字段
```

---

## 8. Kustomize+ArgoCD

### 为什么用Kustomize

```
Helm：模板引擎，用{{}}渲染，逻辑复杂时难维护
Kustomize：无模板，通过「基础+覆盖」组合，声明式patch
  - base/：公共资源定义
  - overlays/：按环境/集群覆盖（改image、副本数、configmap等）
  - 无需学模板语法，纯YAML叠加
  - Kubernetes原生（kubectl apply -k）
```

### 仓库结构

```
myorg/myapp-kustomize/
  ├── base/
  │   ├── deployment.yaml
  │   ├── service.yaml
  │   ├── configmap.yaml
  │   └── kustomization.yaml
  └── overlays/
      ├── dev/
      │   ├── kustomization.yaml
      │   └── replica-patch.yaml
      ├── staging/
      │   ├── kustomization.yaml
      │   └── replica-patch.yaml
      └── production/
          ├── kustomization.yaml
          ├── replica-patch.yaml
          └── image-patch.yaml
```

base/kustomization.yaml：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
commonLabels:
  app.kubernetes.io/name: myapp
  app.kubernetes.io/managed-by: argocd
```

overlays/production/kustomization.yaml：

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: production
resources:
  - ../../base

# 1. 修改镜像版本
images:
  - name: myapp               # 原镜像名
    newName: registry.io/myapp
    newTag: v1.2.3

# 2. 修改副本数
replicas:
  - name: myapp
    count: 5

# 3. 覆盖configmap字段
configMapGenerator:
  - name: myapp-config
    behavior: merge
    literals:
      - LOG_LEVEL=warn
      - FEATURE_NEW_API=true

# 4. 使用Strategic Merge Patch
patches:
  - path: replica-patch.yaml
```

### ArgoCD Application引用Kustomize

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-prod
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/myorg/myapp-kustomize
    targetRevision: main
    path: overlays/production          # 指向kustomization目录
    # Kustomize相关参数（可选）
    kustomize:
      # 覆盖镜像（等价于 kustomize edit set image）
      images:
        - registry.io/myapp:v1.2.4
      # 覆盖命名空间
      namePrefix: prod-
      # 传入参数（Kustomize 4.3+）
      commonLabels:
        env: production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Kustomize vs Helm 选型

| 维度 | Kustomize | Helm |
|------|-----------|------|
| 学习曲线 | 低（纯YAML） | 中（模板语法） |
| 复用性 | base/overlays叠加 | Chart包，版本化分发 |
| 社区生态 | 较少，官方维护 | 极丰富（Artifact Hub） |
| 逻辑能力 | 弱（无条件判断） | 强（if/range等） |
| GitOps友好度 | 高（无渲染，直接是YAML） | 中（需渲染，但ArgoCD支持） |
| 适用场景 | 内部应用、环境差异管理 | 通用应用分发、第三方Chart |

### 实战技巧：Kustomize组件化

```yaml
# components/monitoring/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component
resources:
  - servicemonitor.yaml
patches:
  - path: metrics-patch.yaml
```

```yaml
# overlays/production/kustomization.yaml
components:
  - ../../../components/monitoring
  - ../../../components/network-policies
```

Component允许将「可选功能块」模块化，按需组合，比纯overlays更灵活。

---

## 9. 渐进式发布Argo Rollouts

### Argo Rollouts是什么

Argo Rollouts是Argo生态的渐进式发布控制器，作为Deployment的替代品，提供：

```
1. 蓝绿部署（Blue-Green）
2. 金丝雀发布（Canary）
3. 渐进式交付（基于指标自动推进/回滚）
4. 与Prometheus/Datadog等指标系统集成
```

### 安装

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f \
  https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# 安装kubectl插件
brew install argoproj/tap/kubectl-argo-rollouts   # macOS
# 或
curl -sLO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

### 蓝绿部署示例

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-rollout
spec:
  replicas: 5
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
          image: registry.io/myapp:v1.0.0
          ports:
            - containerPort: 8080
  strategy:
    blueGreen:
      activeService: myapp-active        # 指向当前稳定版的Service
      previewService: myapp-preview      # 指向新版本的Service
      autoPromotionEnabled: false         # 手动确认切流
      # autoPromotionSeconds: 30          # 自动切流（可选）
      scaleDownDelaySeconds: 30           # 旧版保留30s后缩容
      prePromotionAnalysis:
        templates:
          - templateName: success-rate    # 切流前做分析
        args:
          - name: service-name
            value: myapp-preview
```

```bash
# 手动切流
kubectl argo rollouts promote myapp-rollout

# 查看发布状态
kubectl argo rollouts get rollout myapp-rollout --watch
```

### 金丝雀发布示例

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-canary
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: myapp-canary      # 金丝雀流量Service
      stableService: myapp-stable      # 稳定版流量Service
      trafficRouting:
        nginx:
          stableIngress: myapp-ingress  # 通过Ingress切流
      steps:
        # 第1步：5%流量，暂停10分钟
        - setWeight: 5
        - pause: { duration: 10m }
        # 第2步：20%流量，分析指标
        - setWeight: 20
        - analysis:                      # 嵌入式分析
            templates:
              - templateName: success-rate
            args:
              - name: service-name
                value: myapp-canary
        # 第3步：50%流量，手动确认
        - setWeight: 50
        - pause: {}                      # 无限暂停，等手动promote
        # 第4步：全量
        - setWeight: 100
```

### 基于Prometheus指标的自动分析

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      # 成功率阈值：必须 > 95%
      successCondition: result[0] >= 0.95
      failureLimit: 3                    # 连续3次失败则回滚
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",code!~"5.."}[2m]))
            /
            sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
```

发布过程中，如果成功率低于95%且连续3次，Argo Rollouts自动回滚到稳定版。

### Rollouts与ArgoCD集成

```
要点：
1. Rollout是CRD，ArgoCD可以像管理Deployment一样管理Rollout
2. Git中存放Rollout YAML，ArgoCD同步到集群
3. 镜像更新流程：
   开发者在Git中修改Rollout的image.tag → ArgoCD检测变更 → 同步到集群
   → Argo Rollouts控制器接管，按strategy执行渐进式发布
4. ArgoCD负责「同步Git到集群」，Argo Rollouts负责「发布策略」
   两者解耦，职责清晰
```

Application示例：

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/myorg/myapp-config
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

> 注意：selfHeal=true时，ArgoCD会把Rollout的spec还原成Git中的版本。但Rollout的status（如当前canary权重）是运行时状态，不会被还原。

---

## 10. 面试要点补充

### Q1: ApplicationSet解决了什么问题？有哪些生成器？

```
问题：单个Application只能对应一个集群和一个Git源，多集群/多环境场景下需手写大量Application，维护成本高。
解决：ApplicationSet通过「生成器+模板」自动批量创建Application。

常用生成器：
1. List：手写列表，适合少量固定目标
2. Clusters：读取ArgoCD已注册集群，实现多集群部署
3. Git：扫描Git目录/文件，每个目录生成一个Application（微服务批量部署）
4. Pull Request：每个PR生成预览环境
5. Matrix：组合多个生成器（如 集群 × 环境 笛卡尔积）
6. ClusterDecisionResource：基于自定义资源动态决策
```

### Q2: ArgoCD Notifications的配置流程？

```
1. 配置ConfigMap（argocd-notifications-cm）：
   - service：定义通知渠道（Slack/钉钉/Webhook/邮件）
   - trigger：定义触发条件（on-deployed/on-health-degraded等）
   - template：定义消息内容模板
2. 配置Secret：存放渠道凭据（如Slack token）
3. 给Application打注解订阅触发器：
   notifications.argoproj.io/subscribe.on-deployed.slack=channel-name
4. Notifications Controller监听Application状态变化，匹配trigger后渲染template并发送

关键点：订阅是基于注解的，不是全局配置，每个Application独立订阅。
```

### Q3: Helm和Kustomize在ArgoCD中如何选型？

```
Helm：
- 适合第三方应用部署（Artifact Hub上有大量现成Chart）
- 适合需要版本化分发的场景（Chart作为独立制品）
- 模板能力强，但维护复杂

Kustomize：
- 适合内部应用的多环境管理
- 无模板，纯YAML叠加，GitOps原生友好
- 学习成本低，但复用性依赖目录结构设计

ArgoCD对两者都原生支持：
- Helm：source.chart或source.path + source.helm
- Kustomize：source.path指向kustomization目录 + source.kustomize
常见做法：第三方用Helm，内部应用用Kustomize，两者在同一个ArgoCD实例共存。
```

### Q4: Argo Rollouts如何实现自动回滚？

```
1. Rollout定义strategy（blueGreen或canary）+ steps
2. 在steps中嵌入Analysis或引用AnalysisTemplate
3. AnalysisTemplate定义指标查询（如Prometheus成功率）和成功条件
4. 发布过程中，Rollouts控制器按interval查询指标：
   - 满足successCondition：继续推进到下一step
   - 不满足：累计failureLimit次后自动abort，回滚到stable版本
5. 也可设置pause: {}等待手动promote/abort

与ArgoCD的关系：
- ArgoCD负责把Rollout YAML同步到集群（GitOps层）
- Argo Rollouts负责执行发布策略（运行时层）
- 两者解耦，ArgoCD不关心发布过程，只关心Git与集群的一致性
```

### Q5: 如何在GitOps中管理Secret？

```
核心矛盾：Secret不应明文存入Git，但GitOps要求所有配置在Git中。

解决方案：
1. Sealed Secrets（Bitnami）：
   - 用私钥加密Secret为SealedSecret CRD，可安全存入Git
   - 集群中的Controller解密还原为原生Secret
   - 适合简单场景

2. SOPS（Mozilla）+ age/GPG：
   - 加密Secret的value字段，key保持明文
   - argocd-repo-server通过SOPS插件解密
   - 支持细粒度权限（KMS/云密钥管理）

3. External Secrets Operator（ESO）：
   - Secret数据存在外部密钥管理服务（Vault/AWS SM/GCP SM）
   - Git中只存ExternalSecret CRD（引用外部密钥的路径）
   - Controller从外部拉取并生成K8s Secret
   - 最适合企业级场景，支持密钥轮转

4. ArgoCD Vault Plugin：
   - argocd-repo-server插件，渲染时从Vault注入Secret
   - 与ESO类似但更贴近ArgoCD原生体验

推荐：小团队用Sealed Secrets，中大型用ESO+Vault。
```

---

## 📚 相关阅读

- [01_Docker与Kubernetes详解](../10_容器化/01_Docker与Kubernetes详解.md)
- [02_Docker与K8s实战进阶](../10_容器化/02_Docker与K8s实战进阶.md)
- [02_Jenkins流水线实战](../18_DevOps与CICD/02_Jenkins流水线实战.md)

### 官方文档

- ArgoCD 官方文档：https://argo-cd.readthedocs.io
- ArgoCD ApplicationSet：https://argo-cd.readthedocs.io/en/stable/operator-manual/applicationset
- ArgoCD Notifications：https://argocd-notifications.readthedocs.io
- Argo Rollouts：https://argo-rollouts.readthedocs.io
- Kustomize：https://kubectl.docs.kubernetes.io

### 进阶实践

- Sealed Secrets：https://github.com/bitnami-labs/sealed-secrets
- External Secrets Operator：https://external-secrets.io
- ArgoCD Vault Plugin：https://argocd-vault-plugin.readthedocs.io
- Argo CD Autopilot（GitOps骨架工具）：https://argoproj.github.io/argo-cd-autopilot
- ArgoCD + KubeVela 多集群应用交付：https://kubevela.io

### 相关工具对比

- FluxCD（另一主流GitOps工具）：https://fluxcd.io
- Jenkins X（GitOps + Pipeline）：https://jenkins-x.io
- Rancher Fleet（多集群GitOps）：https://fleet.rancher.io

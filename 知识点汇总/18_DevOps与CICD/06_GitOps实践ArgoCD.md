# GitOps实践：ArgoCD

> 声明式基础设施管理，Git作为单一真相源

---

## 📋 目录

1. [GitOps概述](#1-gitops概述)
2. [ArgoCD架构](#2-argocd架构)
3. [Application CRD详解](#3-application-crd详解)
4. [同步策略](#4-同步策略)
5. [多环境管理](#5-多环境管理)
6. [Argo Rollouts金丝雀发布](#6-argo-rollouts金丝雀发布)
7. [面试要点](#7-面试要点)

---

## 1. GitOps概述

### 1.1 核心理念

```
GitOps四大核心原则：

  1. 声明式（Declarative）
     - 系统状态用声明式描述（YAML）
     - 不用命令式操作（kubectl apply/run）

  2. 版本控制（Version Controlled）
     - Git作为唯一真相源（Single Source of Truth）
     - 所有变更通过Pull Request
     - 完整的审计历史

  3. 自动拉取（Pulled Automatically）
     - Agent自动同步Git到集群
     - 不是CI Push，而是集群Pull
     - 集群内的Agent持续观察Git

  4. 持续协调（Continuously Reconciled）
     - 持续检测实际状态vs期望状态
     - 漂移（Drift）自动修复
     - 确保集群始终与Git一致
```

### 1.2 GitOps vs 传统CI/CD

| 维度 | 传统CI/CD | GitOps |
|------|----------|--------|
| 部署方向 | Push（CI推送） | Pull（集群拉取） |
| 配置管理 | CI平台 | Git仓库 |
| 回滚 | 重新构建+部署 | Git revert |
| 审计 | CI日志 | Git历史 |
| 集群权限 | CI需集群凭据 | Agent在集群内 |
| 状态漂移 | 手动修复 | 自动协调 |
| 多环境 | CI Pipeline分支 | Git目录/Kustomize |
| 密钥管理 | CI变量 | Sealed Secrets/SOPS |

### 1.3 GitOps工作流

```
┌──────────────────────────────────────────────────────┐
│                  GitOps 工作流                        │
├──────────────────────────────────────────────────────┤
│                                                        │
│  开发者 ──→ Git Push ──→ Git仓库                      │
│                                │                       │
│                    ┌───────────┴───────────┐          │
│                    │   CI Pipeline          │          │
│                    │   - 构建镜像            │          │
│                    │   - 单元测试            │          │
│                    │   - 更新Git中的镜像Tag  │          │
│                    └───────────┬───────────┘          │
│                                │                       │
│                                ▼                       │
│                    ┌───────────────────────┐          │
│                    │   Git仓库（K8s清单）    │          │
│                    │   deployment.yaml      │          │
│                    │   service.yaml         │          │
│                    │   configmap.yaml       │          │
│                    └───────┬───────────────┘          │
│                            │ ArgoCD检测到变更           │
│                            ▼                           │
│                    ┌───────────────────────┐          │
│                    │   ArgoCD（集群内）      │          │
│                    │   - 拉取Git            │          │
│                    │   - 对比集群状态        │          │
│                    │   - 同步差异            │          │
│                    └───────┬───────────────┘          │
│                            │                           │
│                            ▼                           │
│                    ┌───────────────────────┐          │
│                    │   K8s集群              │          │
│                    │   实际状态=期望状态     │          │
│                    └───────────────────────┘          │
└──────────────────────────────────────────────────────┘
```

---

## 2. ArgoCD架构

### 2.1 组件架构

```
┌─────────────────────────────────────────────────────┐
│                    ArgoCD 架构                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  API Server │  │   Web UI    │  │  CLI       │  │
│  │  (gRPC/REST)│  │  (React)    │  │ (argocd)  │  │
│  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │
│         └────────────────┼─────────────────┘         │
│                          │                            │
│         ┌────────────────┼─────────────────┐         │
│         ▼                ▼                 ▼         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │ Application  │ │ Repo Server  │ │   Dex        │ │
│  │ Controller   │ │ (Git拉取+    │ │ (OIDC/SSO)   │ │
│  │ (协调循环)    │ │  渲染清单)    │ │              │ │
│  └──────┬───────┘ └──────┬───────┘ └──────────────┘ │
│         │                │                           │
│         │    ┌───────────┘                           │
│         ▼    ▼                                        │
│  ┌──────────────────┐                                │
│  │   Redis          │ (缓存Git仓库/渲染结果)          │
│  └──────────────────┘                                │
│                                                      │
│  ┌──────────────────┐                                │
│  │ ApplicationSet   │ (多集群/多应用批量生成)         │
│  │ Controller       │                                │
│  └──────────────────┘                                │
│                                                      │
│  ┌──────────────────┐                                │
│  │ Notification     │ (Slack/Email/Webhook通知)      │
│  │ Controller       │                                │
│  └──────────────────┘                                │
└─────────────────────────────────────────────────────┘
         │
         ▼ 同步
┌─────────────────────────────────────────────────────┐
│              K8s集群（可多个）                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Cluster 1│  │ Cluster 2│  │ Cluster 3│          │
│  │ (dev)    │  │ (staging)│  │ (prod)   │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────┘
```

### 2.2 核心组件详解

```
┌──────────────────────────────────────────────────────┐
│  API Server                                           │
├──────────────────────────────────────────────────────┤
│  - 暴露gRPC和REST API                                 │
│  - 管理Application CRD                                │
│  - 认证授权（RBAC + OIDC）                            │
│  - 供Web UI和CLI调用                                  │
├──────────────────────────────────────────────────────┤
│  Application Controller                               │
├──────────────────────────────────────────────────────┤
│  - 核心协调循环                                       │
│  - 监听Git仓库变更（通过Repo Server）                 │
│  - 对比Git声明状态 vs 集群实际状态                     │
│  - 检测到差异时触发Sync                               │
│  - 持续协调（selfHeal模式下自动修复漂移）              │
├──────────────────────────────────────────────────────┤
│  Repo Server                                          │
├──────────────────────────────────────────────────────┤
│  - 从Git仓库拉取清单文件                              │
│  - 渲染Helm/Kustomize/Jsonnet                        │
│  - 生成最终的K8s YAML                                 │
│  - 结果缓存在Redis中                                  │
├──────────────────────────────────────────────────────┤
│  ApplicationSet Controller                            │
├──────────────────────────────────────────────────────┤
│  - 批量生成Application                                │
│  - 支持Git目录生成器（每个目录一个Application）        │
│  - 支持集群生成器（每个集群一个Application）           │
│  - 支持Matrix生成器（组合多个生成器）                  │
└──────────────────────────────────────────────────────┘
```

---

## 3. Application CRD详解

### 3.1 基本Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
  # 最终izer确保删除时清理资源
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  # 源：Git仓库
  source:
    repoURL: https://github.com/myorg/myapp-k8s
    targetRevision: main
    path: manifests            # 仓库中的清单路径
    
    # 或使用Helm
    # path: charts/myapp
    # helm:
    #   valueFiles:
    #     - values-production.yaml
    #   parameters:
    #     - name: image.tag
    #       value: v1.2.3
    
    # 或使用Kustomize
    # path: overlays/production
    # kustomize:
    #   images:
    #     - myorg/myapp:v1.2.3
  
  # 目标：K8s集群
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  # 同步策略
  syncPolicy:
    automated:
      prune: true         # 删除Git中已删除的资源
      selfHeal: true      # 自动修复手动修改
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
      - ApplyOutOfSyncOnly=true
  
  # 忽略某些字段的变化（如HPA的replicas）
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas
```

### 3.2 多源Application（ArgoCD 2.6+）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-multi-source
  namespace: argocd
spec:
  sources:
    # 源1: Helm Chart
    - repoURL: https://charts.bitnami.com/bitnami
      chart: redis
      targetRevision: 17.0.0
      helm:
        valueFiles:
          - $values/charts/redis/values.yaml
    
    # 源2: 配置值文件
    - repoURL: https://github.com/myorg/myapp-config
      targetRevision: main
      ref: values            # 引用名，供其他源使用
    
    # 源3: 额外清单
    - repoURL: https://github.com/myorg/myapp-k8s
      targetRevision: main
      path: manifests/extra
```

### 3.3 ApplicationSet批量管理

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-multi-env
  namespace: argocd
spec:
  generators:
    # Git目录生成器：每个目录生成一个Application
    - git:
        repoURL: https://github.com/myorg/myapp-k8s
        revision: main
        directories:
          - path: overlays/*
  template:
    metadata:
      name: 'myapp-{{path.basename}}'
    spec:
      source:
        repoURL: https://github.com/myorg/myapp-k8s
        targetRevision: main
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

---

## 4. 同步策略

### 4.1 自动同步 vs 手动同步

```yaml
# 自动同步（适合dev/staging环境）
syncPolicy:
  automated:
    prune: true         # Git中删除的资源在集群中也删除
    selfHeal: true      # 手动kubectl修改会被自动修复
  syncOptions:
    - CreateNamespace=true

# 手动同步（适合production环境）
# 不设置syncPolicy.automated
# 需要在UI/CLI手动点击Sync
# 可以配置审批流程
spec:
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

### 4.2 同步阶段与钩子

```
ArgoCD同步流程：

  PreSync → Sync → PostSync → SyncFail(如果失败)

  ┌──────────────────────────────────────────────┐
  │  Sync阶段                                     │
  │                                                │
  │  PreSync:                                      │
  │    - 数据库迁移                                │
  │    - 准备配置                                  │
  │    - Hook资源（如Job）                          │
  │                                                │
  │  Sync:                                         │
  │    - 创建/更新K8s资源                          │
  │    - 按依赖顺序（先ConfigMap后Deployment）     │
  │                                                │
  │  PostSync:                                     │
  │    - 通知/验证                                 │
  │    - 健康检查                                  │
  │    - Hook资源                                  │
  │                                                │
  │  SyncFail (同步失败时):                        │
  │    - 回滚操作                                  │
  │    - 告警通知                                  │
  └──────────────────────────────────────────────┘
```

```yaml
# Sync Hook示例：数据库迁移Job
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  annotations:
    argocd.argoproj.io/hook: PreSync          # 在Sync前执行
    argocd.argoproj.io/hook-delete-policy: HookSucceeded  # 成功后删除
spec:
  template:
    spec:
      containers:
        - name: migration
          image: myorg/migration:v1.2.3
          command: ["flyway", "migrate"]
      restartPolicy: OnFailure
```

### 4.3 健康检查与资源状态

```yaml
# 自定义健康检查（ArgoCD Lua脚本）
# 配置在argocd-cm ConfigMap中
data:
  resource.customizations.health: |
    # 检查Deployment健康状态
    hs = {}
    if obj.status ~= nil then
      if obj.status.availableReplicas == obj.spec.replicas then
        hs.status = "Healthy"
        hs.message = "All replicas available"
      else
        hs.status = "Progressing"
        hs.message = "Waiting for replicas"
      end
    end
    return hs
```

---

## 5. 多环境管理

### 5.1 目录结构方案

```
方案1: 目录隔离（简单直接）

myapp-k8s/
├── base/                    # 基础清单
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
├── overlays/
│   ├── dev/                 # 开发环境覆盖
│   │   ├── kustomization.yaml
│   │   └── patch-replicas.yaml
│   ├── staging/             # 预发环境覆盖
│   │   ├── kustomization.yaml
│   │   └── patch-resources.yaml
│   └── production/          # 生产环境覆盖
│       ├── kustomization.yaml
│       └── patch-production.yaml

每个环境对应一个Application：
  dev → overlays/dev
  staging → overlays/staging
  production → overlays/production
```

### 5.2 分支策略方案

```
方案2: 分支隔离

Git仓库分支:
  main     → 开发环境
  staging  → 预发环境
  production → 生产环境

ArgoCD Application:
  dev:
    source.targetRevision: main
  staging:
    source.targetRevision: staging
  production:
    source.targetRevision: production

环境提升流程：
  dev (main) → PR merge to staging → staging → PR merge to production → production

优势：环境间通过PR审查隔离
劣势：分支管理复杂，merge冲突
```

### 5.3 Kustomize多环境配置

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  app: myapp

---
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: production

resources:
  - ../../base

patches:
  - target:
      kind: Deployment
      name: myapp
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: 512Mi
      - op: replace
        path: /spec/template/spec/containers/0/image
        value: myorg/myapp:v1.2.3

configMapGenerator:
  - name: app-config
    behavior: merge
    literals:
      - LOG_LEVEL=warn
      - FEATURE_FLAG_BETA=false
```

### 5.4 密钥管理

```yaml
# Sealed Secrets：加密后安全存储在Git中
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  encryptedData:
    username: AgB...加密内容...
    password: AgC...加密内容...
  template:
    metadata:
      name: db-credentials
    type: Opaque

# 或使用SOPS + age加密
# .sops.yaml配置
# creation_rules:
#   - path_regex: .*.yaml
#     encrypted_regex: '^(data|stringData)$'
#     age: age1xxxxxxxxxxxxxxx
```

---

## 6. Argo Rollouts金丝雀发布

### 6.1 Argo Rollouts架构

```
┌──────────────────────────────────────────────────────┐
│                Argo Rollouts                           │
├──────────────────────────────────────────────────────┤
│                                                        │
│  Rollout Controller                                     │
│  - 替代Deployment的渐进式部署控制器                     │
│  - 支持金丝雀(Canary)和蓝绿(Blue-Green)发布            │
│  - 集成Prometheus/Nginx/Datadog等进行分析              │
│                                                        │
│  工作流程：                                             │
│                                                        │
│  ┌──────────┐                                         │
│  │ Rollout  │ → ReplicaSet-v2 (新版本)                 │
│  │ CRD      │ → ReplicaSet-v1 (旧版本，逐步缩容)       │
│  └──────────┘                                         │
│                                                        │
│  Canary发布：                                          │
│  v1(100%) → v2(5%) → 分析 → v2(25%) → 分析 →          │
│  v2(50%) → 分析 → v2(100%)                           │
│                                                        │
│  Blue-Green发布：                                      │
│  Blue(100%) → Green(100%) → 切换流量 → 销毁Blue      │
└──────────────────────────────────────────────────────┘
```

### 6.2 金丝雀发布配置

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-rollout
  namespace: production
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: myapp-canary      # 金丝雀Service
      stableService: myapp-stable      # 稳定版Service
      trafficRouting:
        nginx:
          stableIngress: myapp-ingress  # 主Ingress
      steps:
        # 1. 5%流量到新版本，暂停等手动确认
        - setWeight: 5
        - pause: {}                    # 无限期暂停，等手动推进
        
        # 2. 20%流量，观察5分钟
        - setWeight: 20
        - pause: { duration: 5m }
        
        # 3. 50%流量，自动分析
        - setWeight: 50
        - analysis:                    # 自动分析指标
            templates:
              - templateName: success-rate
            args:
              - name: service-name
                value: myapp-canary
        
        # 4. 如果分析通过，全量发布
        - setWeight: 100
  
  template:
    spec:
      containers:
        - name: myapp
          image: myorg/myapp:v2.0.0
          ports:
            - containerPort: 8080

---
# 自动分析模板：检查错误率和延迟
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
      # Prometheus查询：成功率 > 95%
      successCondition: result[0] >= 0.95
      failureLimit: 3                   # 连续3次失败则中止
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",status!~"5.."}[2m]))
            / sum(rate(http_requests_total{service="{{args.service-name}}"}[2m]))
    
    - name: latency-p99
      interval: 1m
      # P99延迟 < 500ms
      successCondition: result[0] < 500
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_ms_bucket{service="{{args.service-name}}"}[2m]))
              by (le))
```

### 6.3 蓝绿发布配置

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp-bluegreen
spec:
  replicas: 5
  strategy:
    blueGreen:
      activeService: myapp-active       # 指向当前活跃版本
      previewService: myapp-preview     # 指向预览版本
      autoPromotionEnabled: false        # 手动确认切换
      scaleDownDelaySeconds: 30          # 切换后30秒缩容旧版本
      prePromotionAnalysis:              # 切换前分析
        templates:
          - templateName: success-rate
        args:
          - name: service-name
            value: myapp-preview
  template:
    spec:
      containers:
        - name: myapp
          image: myorg/myapp:v2.0.0
```

### 6.4 回滚操作

```bash
# 查看Rollout历史
kubectl argo rollouts get rollout myapp-rollout --history

# 回滚到上一版本
kubectl argo rollouts undo myapp-rollout

# 回滚到指定版本
kubectl argo rollouts undo myapp-rollout --to-revision=3

# 中止当前发布
kubectl argo rollouts abort myapp-rollout

# 暂停发布
kubectl argo rollouts pause myapp-rollout

# 恢复发布
kubectl argo rollouts promote myapp-rollout
```

---

## 7. 面试要点

### Q1: GitOps的优势？

```
1. Git为唯一真相源：审计、版本控制、回滚
2. 集群无需暴露CI凭据：安全提升
3. 自动协调：集群漂移自动修复
4. 回滚简单：git revert → 自动同步
5. 多环境管理：不同分支/目录对应不同环境
```

### Q2: ArgoCD的工作原理？

```
1. Application Controller监听Git仓库变更
2. Repo Server拉取Git并渲染Helm/Kustomize
3. 对比Git声明状态 vs 集群实际状态
4. 不一致时触发Sync
5. Sync = apply YAML到集群
6. 持续协调（selfHeal：手动修改自动修复）
```

### Q3: ArgoCD的同步策略有哪些？

```
自动同步（automated）：
  - prune: 删除Git中已删除的资源
  - selfHeal: 自动修复手动kubectl修改

手动同步：
  - 需要人工点击Sync
  - 适合生产环境

同步钩子：
  - PreSync: 迁移、准备
  - Sync: 创建/更新资源
  - PostSync: 验证、通知
  - SyncFail: 回滚
```

### Q4: Argo Rollouts如何实现金丝雀发布？

```
步骤：
  1. 新版本ReplicaSet创建，初始5%流量
  2. 暂停等待手动确认或自动分析
  3. 逐步增加流量：5% → 20% → 50% → 100%
  4. 每个阶段通过AnalysisTemplate检查指标
  5. 指标异常自动中止，指标正常继续推进
  6. 100%流量后，旧版本缩容

分析指标：
  - 错误率 < 5%
  - P99延迟 < 500ms
  - 连续3次失败自动回滚
```

### Q5: GitOps多环境管理有哪些方案？

```
方案1: 目录隔离
  - 每个环境一个目录（overlays/dev, overlays/prod）
  - Kustomize overlay覆盖差异
  - 每个环境一个Application

方案2: 分支隔离
  - 每个环境一个分支
  - 环境提升通过PR merge
  - 适合需要严格审查的场景

方案3: ApplicationSet批量管理
  - 自动为每个环境/集群生成Application
  - 减少重复配置
  - 适合大规模多集群场景
```

---

## 📚 相关阅读

- [01_Docker与Kubernetes详解](../10_容器化/01_Docker与Kubernetes详解.md)
- [02_Docker与K8s实战进阶](../10_容器化/02_Docker与K8s实战进阶.md)
- [02_Jenkins流水线实战](../18_DevOps与CICD/02_Jenkins流水线实战.md)

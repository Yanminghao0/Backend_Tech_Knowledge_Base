# GitOps实践：ArgoCD

> 声明式基础设施管理，Git作为单一真相源

---

## 📋 目录

1. [GitOps概述](#1-gitops概述)
2. [ArgoCD架构](#2-argocd架构)
3. [ArgoCD实战](#3-argocd实战)
4. [面试要点](#4-面试要点)

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

## 📚 相关阅读

- [01_Docker与Kubernetes详解](../10_容器化/01_Docker与Kubernetes详解.md)
- [02_Docker与K8s实战进阶](../10_容器化/02_Docker与K8s实战进阶.md)
- [02_Jenkins流水线实战](../18_DevOps与CICD/02_Jenkins流水线实战.md)

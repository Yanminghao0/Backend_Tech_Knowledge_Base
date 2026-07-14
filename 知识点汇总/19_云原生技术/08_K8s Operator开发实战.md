# K8s Operator开发实战

> CRD + Controller：自定义Kubernetes自动化运维能力

---

## 📋 目录

1. [Operator概述](#1-operator概述)
2. [CRD自定义资源定义](#2-crd自定义资源定义)
3. [Controller开发](#3-controller开发)
4. [Operator SDK实战](#4-operator-sdk实战)
5. [部署与测试](#5-部署与测试)
6. [面试题速查](#6-面试题速查)

---

## 1. Operator概述

```
Operator = CRD + Controller + 业务逻辑

  ┌────────────────────────────────────────┐
  │            用户创建CR实例                │
  │         apiVersion: app.example.com/v1  │
  │         kind: MyApp                     │
  │         spec: replicas: 3               │
  └─────────────────┬──────────────────────┘
                    │
  ┌─────────────────▼──────────────────────┐
  │            Controller (Reconcile)       │
  │  1. Watch: 监听CR变化                    │
  │  2. 对比: 期望状态 vs 实际状态            │
  │  3. 调谐: 创建/更新/删除资源              │
  └─────────────────┬──────────────────────┘
                    │
  ┌─────────────────▼──────────────────────┐
  │            Kubernetes资源               │
  │  Deployment / Service / ConfigMap...    │
  └────────────────────────────────────────┘

应用场景：
  - 数据库运维（备份/恢复/扩容/升级）
  - 消息队列管理（Topic创建/分区扩容）
  - 机器学习训练（GPU调度/检查点）
  - 有状态应用（Redis Cluster/ES/Kafka）
```

---

## 2. CRD自定义资源定义

```yaml
# crd.yaml — 定义自定义资源
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: myapps.app.example.com
spec:
  group: app.example.com
  names:
    kind: MyApp
    plural: myapps
    singular: myapp
    shortNames: ["ma"]
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              required: ["image", "replicas"]
              properties:
                image:
                  type: string
                replicas:
                  type: integer
                  minimum: 1
                  maximum: 100
                port:
                  type: integer
                  default: 8080
                env:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      value:
                        type: string
            status:
              type: object
              properties:
                readyReplicas:
                  type: integer
                conditions:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: string
                      status:
                        type: string
      subresources:
        status: {}
        scale:
          specReplicasPath: .spec.replicas
          statusReplicasPath: .status.readyReplicas
```

```yaml
# 创建CR实例
apiVersion: app.example.com/v1
kind: MyApp
metadata:
  name: my-app
  namespace: default
spec:
  image: nginx:latest
  replicas: 3
  port: 8080
  env:
    - name: ENV
      value: production
```

---

## 3. Controller开发

```java
// Java Operator SDK (Headlamp/Operator Framework)
@ControllerConfiguration
public class MyAppController implements Reconciler<MyApp> {

    @Override
    public UpdateControl<MyApp> reconcile(MyApp resource, Context context) {
        String name = resource.getMetadata().getName();
        int replicas = resource.getSpec().getReplicas();
        String image = resource.getSpec().getImage();
        
        // 1. 检查并创建Deployment
        Deployment deployment = client.apps().deployments()
            .inNamespace(resource.getMetadata().getNamespace())
            .withName(name)
            .get();
            
        if (deployment == null) {
            deployment = createDeployment(name, image, replicas, resource);
            client.apps().deployments().resource(deployment).create();
        } else if (deployment.getSpec().getReplicas() != replicas) {
            // 2. 扩缩容
            deployment.getSpec().setReplicas(replicas);
            client.apps().deployments().resource(deployment).update();
        }
        
        // 3. 检查并创建Service
        Service service = client.services()
            .inNamespace(resource.getMetadata().getNamespace())
            .withName(name)
            .get();
        if (service == null) {
            service = createService(name, resource);
            client.services().resource(service).create();
        }
        
        // 4. 更新Status
        int readyReplicas = deployment.getStatus().getReadyReplicas() != null 
            ? deployment.getStatus().getReadyReplicas() : 0;
        resource.getStatus().setReadyReplicas(readyReplicas);
        
        return UpdateControl.updateStatus(resource);
    }
    
    private Deployment createDeployment(String name, String image, int replicas, MyApp cr) {
        Deployment dep = new DeploymentBuilder()
            .withNewMetadata()
                .withName(name)
                .withNamespace(cr.getMetadata().getNamespace())
            .endMetadata()
            .withNewSpec()
                .withReplicas(replicas)
                .withNewSelector()
                    .addToMatchLabels("app", name)
                .endSelector()
                .withNewTemplate()
                    .withNewMetadata()
                        .addToLabels("app", name)
                    .endMetadata()
                    .withNewSpec()
                        .addNewContainer()
                            .withName(name)
                            .withImage(image)
                            .addNewPort()
                                .withContainerPort(cr.getSpec().getPort())
                            .endPort()
                        .endContainer()
                    .endSpec()
                .endTemplate()
            .endSpec()
            .build();
        return dep;
    }
}
```

---

## 4. Operator SDK实战

```bash
# Go Operator SDK（更主流）
# 1. 创建项目
operator-sdk init --domain example.com --repo github.com/myorg/myapp-operator

# 2. 创建API
operator-sdk create api --group app --version v1 --kind MyApp --resource --controller

# 3. 生成的项目结构
myapp-operator/
├── api/v1/myapp_types.go      # CRD类型定义
├── controllers/myapp_controller.go  # Controller逻辑
├── config/
│   ├── crd/                    # CRD YAML
│   ├── manager/                # Operator部署
│   └── samples/                # CR示例
├── main.go
└── Makefile

# 4. 定义CRD类型（Go）
# api/v1/myapp_types.go
type MyAppSpec struct {
    Image    string `json:"image"`
    Replicas int32  `json:"replicas"`
    Port     int32  `json:"port,omitempty"`
}

type MyAppStatus struct {
    ReadyReplicas int32 `json:"readyReplicas,omitempty"`
}

# 5. 实现Reconcile逻辑
# controllers/myapp_controller.go
func (r *MyAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    var myApp appv1.MyApp
    if err := r.Get(ctx, req.NamespacedName, &myApp); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }
    
    // 检查Deployment是否存在
    var deployment appsv1.Deployment
    err := r.Get(ctx, req.NamespacedName, &deployment)
    if err != nil && errors.IsNotFound(err) {
        // 创建Deployment
        dep := r.constructDeployment(&myApp)
        if err := r.Create(ctx, dep); err != nil {
            return ctrl.Result{}, err
        }
    }
    
    // 更新Status
    myApp.Status.ReadyReplicas = deployment.Status.ReadyReplicas
    if err := r.Status().Update(ctx, &myApp); err != nil {
        return ctrl.Result{}, err
    }
    
    return ctrl.Result{RequeueAfter: time.Minute}, nil
}

# 6. 构建和部署
make manifests    # 生成CRD YAML
make docker-build docker-push IMG=myregistry/myapp-operator:v1
make deploy IMG=myregistry/myapp-operator:v1
```

---

## 5. 部署与测试

```yaml
# Operator部署（Deployment + RBAC）
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-operator
  namespace: operators
spec:
  replicas: 1
  selector:
    matchLabels:
      name: myapp-operator
  template:
    spec:
      serviceAccountName: myapp-operator
      containers:
        - name: manager
          image: myregistry/myapp-operator:v1
          command: ["/manager"]
          env:
            - name: WATCH_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
---
# RBAC
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: myapp-operator-role
rules:
  - apiGroups: ["app.example.com"]
    resources: ["myapps"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: [""]
    resources: ["services", "events"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
```

```bash
# 测试流程
kubectl apply -f config/crd/bases/app.example.com_myapps.yaml  # 安装CRD
kubectl apply -f config/manager/manager.yaml                    # 部署Operator
kubectl apply -f config/samples/app_v1_myapp.yaml               # 创建CR实例
kubectl get myapps                                              # 查看状态
kubectl get deployment my-app                                   # 验证创建
kubectl scale myapp my-app --replicas=5                         # 扩缩容测试
```

---

## 6. 面试题速查

**Q1: Operator是什么？解决什么问题？**
```
Operator = CRD + Controller，将人类运维知识编码为软件
解决：有状态应用的自动化运维（数据库备份/恢复/升级/扩容）
```

**Q2: CRD和Controller的关系？**
```
CRD：定义自定义资源类型（Schema）
Controller：监听CR变化，执行Reconcile逻辑
CRD是"声明什么"，Controller是"做什么"
```

**Q3: Reconcile循环的核心思想？**
```
期望状态 vs 实际状态 → 调谐
1. Watch监听CR和关联资源变化
2. 对比期望（CR spec）和实际（集群状态）
3. 不一致则执行操作（创建/更新/删除）
4. 持续循环，最终达到一致
```

**Q4: Operator和Helm的区别？**
```
Helm：一次性模板渲染，部署后不管
Operator：持续监控，自动调谐，支持 Day-2 运维
Helm适合无状态应用，Operator适合有状态应用
```

---

*最后更新：2026-07-13*

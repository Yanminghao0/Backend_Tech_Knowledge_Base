# Kubernetes进阶实战

> 从入门到精通，掌握K8s生产级部署与运维

---

## 📋 目录

- [1. K8s架构深入](#1-k8s架构深入)
- [2. Pod调度策略](#2-pod调度策略)
- [3. 存储管理](#3-存储管理)
- [4. 网络模型](#4-网络模型)
- [5. 安全机制](#5-安全机制)
- [6. 资源管理](#6-资源管理)
- [7. 高可用部署](#7-高可用部署)
- [8. 监控告警](#8-监控告警)
- [9. 故障排查](#9-故障排查)
- [10. 实战案例](#10-实战案例)

---

## 🎯 学习目标

通过本文档，你将掌握：
- ✅ K8s核心组件原理与交互流程
- ✅ Pod调度策略（亲和性、污点、优先级）
- ✅ 存储管理（PV、PVC、StorageClass、CSI）
- ✅ 网络模型（CNI、Service、Ingress、NetworkPolicy）
- ✅ 安全机制（RBAC、ServiceAccount、PSP）
- ✅ 资源管理（Request、Limit、QoS、HPA、VPA）
- ✅ 高可用K8s集群部署
- ✅ 生产环境监控告警体系
- ✅ 常见故障排查与优化

---

## 1. K8s架构深入

### 1.1 整体架构


```
Master节点（控制平面）
├── kube-apiserver        # API服务器，所有操作的入口
├── etcd                  # 分布式KV存储，保存集群状态
├── kube-scheduler        # 调度器，决定Pod运行在哪个Node
├── kube-controller-manager  # 控制器管理器
└── cloud-controller-manager # 云厂商控制器

Worker节点（数据平面）
├── kubelet               # 节点代理，管理Pod生命周期
├── kube-proxy            # 网络代理，实现Service
└── Container Runtime     # 容器运行时（Docker、containerd）
```

**核心交互流程**：

```
用户 kubectl apply -f pod.yaml
  ↓
kube-apiserver 接收请求，写入etcd
  ↓
kube-scheduler 监听到新Pod，计算调度结果，更新etcd
  ↓
kubelet 监听到Pod调度到本节点
  ↓
kubelet 调用容器运行时创建容器
  ↓
容器启动成功，更新状态到etcd
```

### 1.2 核心组件详解

#### kube-apiserver

**职责**：
- 🔹 提供RESTful API
- 🔹 认证、授权、准入控制
- 🔹 与etcd交互
- 🔹 集群内唯一与etcd通信的组件

**关键特性**：
```yaml
# API Server配置
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
apiServer:
  extraArgs:
    enable-admission-plugins: "NodeRestriction,PodSecurityPolicy"
    max-requests-inflight: "400"
    max-mutating-requests-inflight: "200"
```


#### kube-scheduler

**调度流程**：
```
1. Filtering（过滤）：筛选满足条件的Node
   - 资源是否足够（CPU、Memory）
   - 是否满足NodeSelector
   - 是否满足亲和性规则
   - 是否有污点

2. Scoring（打分）：对候选Node打分
   - 资源剩余量
   - 负载均衡
   - 亲和性权重

3. Binding（绑定）：选择分数最高的Node
```

**自定义调度器**：
```go
// 自定义调度插件
type MyPlugin struct{}

func (p *MyPlugin) Filter(pod *v1.Pod, node *v1.Node) bool {
    // 自定义过滤逻辑
    return node.Status.Allocatable.Cpu() > resource.MustParse("2")
}
```

#### etcd

**特性**：
- 🔹 分布式一致性KV存储（Raft协议）
- 🔹 存储K8s所有数据
- 🔹 支持Watch机制

**备份恢复**：
```bash
# 备份
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# 恢复
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot.db \
  --data-dir=/var/lib/etcd-restore
```

---

## 2. Pod调度策略

### 2.1 NodeSelector（节点选择器）

**最简单的调度方式**：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  nodeSelector:
    disktype: ssd      # 必须匹配标签
    zone: beijing
  containers:
  - name: nginx
    image: nginx
```

**给Node打标签**：
```bash
kubectl label nodes node1 disktype=ssd zone=beijing
```


### 2.2 亲和性与反亲和性

#### NodeAffinity（节点亲和性）

**硬亲和性（必须满足）**：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/e2e-az-name
            operator: In
            values:
            - e2e-az1
            - e2e-az2
  containers:
  - name: nginx
    image: nginx
```

**软亲和性（优先满足）**：
```yaml
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: disktype
            operator: In
            values:
            - ssd
```


#### PodAffinity（Pod亲和性）

**应用场景**：将相关的Pod调度到同一节点或同一可用区

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-pod-affinity
spec:
  affinity:
    podAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - nginx
        topologyKey: kubernetes.io/hostname  # 必须在同一节点
  containers:
  - name: app
    image: myapp
```

#### PodAntiAffinity（Pod反亲和性）

**应用场景**：将Pod分散到不同节点，提高可用性

```yaml
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: nginx
        topologyKey: kubernetes.io/hostname  # 每个节点最多1个
```

**实战示例**：高可用Redis部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: redis
            topologyKey: kubernetes.io/hostname  # 分散到不同节点
      containers:
      - name: redis
        image: redis:6.2
```


### 2.3 污点与容忍度

#### Taint（污点）

**作用**：阻止Pod调度到某些节点

```bash
# 给节点添加污点
kubectl taint nodes node1 key=value:NoSchedule

# 污点效果（Effect）
- NoSchedule：新Pod不调度到该节点
- PreferNoSchedule：尽量不调度
- NoExecute：不调度且驱逐已有Pod
```

**实际应用**：
```bash
# 将GPU节点标记为专用节点
kubectl taint nodes gpu-node1 gpu=true:NoSchedule

# Master节点污点（默认）
kubectl taint nodes master node-role.kubernetes.io/master:NoSchedule
```

#### Toleration（容忍度）

**允许Pod调度到有污点的节点**：

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-pod
spec:
  tolerations:
  - key: "gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  containers:
  - name: gpu-app
    image: nvidia/cuda
```

**容忍所有污点**：
```yaml
tolerations:
- operator: "Exists"  # 容忍所有污点
```

**实战场景**：节点维护
```bash
# 1. 添加污点（新Pod不调度，旧Pod不驱逐）
kubectl taint nodes node1 maintenance=true:NoSchedule

# 2. 驱逐现有Pod
kubectl drain node1 --ignore-daemonsets --delete-emptydir-data

# 3. 维护完成后移除污点
kubectl taint nodes node1 maintenance-
```

### 2.4 优先级与抢占

**PriorityClass（优先级类）**：

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "高优先级业务"
```


**使用优先级**：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: important-pod
spec:
  priorityClassName: high-priority
  containers:
  - name: app
    image: myapp
```

**抢占机制**：
```
1. 高优先级Pod无法调度时
2. 调度器查找低优先级Pod
3. 驱逐低优先级Pod
4. 调度高优先级Pod
```

---

## 3. 存储管理

### 3.1 存储架构

```
PersistentVolume (PV)      # 集群级资源，管理员创建
    ↕
PersistentVolumeClaim (PVC) # 命名空间级，用户申请
    ↕
Pod                         # 挂载PVC
```

### 3.2 PV与PVC

**创建PV（NFS示例）**：

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  nfs:
    server: 192.168.1.100
    path: /data/nfs
```

**创建PVC**：
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-nfs
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 5Gi
  storageClassName: nfs
```

**Pod使用PVC**：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: pvc-nfs
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
```

**访问模式（AccessModes）**：
- `ReadWriteOnce (RWO)`：单节点读写
- `ReadOnlyMany (ROX)`：多节点只读
- `ReadWriteMany (RWX)`：多节点读写

**回收策略（ReclaimPolicy）**：
- `Retain`：手动回收
- `Delete`：自动删除
- `Recycle`：清空数据（已弃用）

### 3.3 StorageClass（动态供给）

**创建StorageClass**：
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iopsPerGB: "10"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

**PVC自动创建PV**：
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
```

**常见Provisioner**：
- `kubernetes.io/aws-ebs`：AWS EBS
- `kubernetes.io/gce-pd`：Google Cloud Persistent Disk
- `kubernetes.io/azure-disk`：Azure Disk
- `kubernetes.io/cinder`：OpenStack Cinder
- `nfs.csi.k8s.io`：NFS CSI

### 3.4 CSI（容器存储接口）

**CSI架构**：
```
CSI Driver
├── Controller Plugin（部署为Deployment）
│   ├── CreateVolume
│   ├── DeleteVolume
│   └── AttachVolume
└── Node Plugin（部署为DaemonSet）
    ├── MountVolume
    └── UnmountVolume
```

**StatefulSet使用动态存储**：
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        volumeMounts:
        - name: data
          mountPath: /var/lib/mysql
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

---

## 4. 网络模型

### 4.1 K8s网络模型原则

**三大原则**：
1. 🔹 **所有Pod可以互相通信**，无需NAT
2. 🔹 **所有Node可以与Pod通信**，无需NAT
3. 🔹 **Pod看到的IP就是其他Pod看到的IP**

### 4.2 CNI（容器网络接口）

**常见CNI插件**：

| 插件 | 网络模型 | 性能 | 功能 |
|------|---------|------|------|
| Flannel | Overlay | 中 | 简单易用 |
| Calico | BGP/IPIP | 高 | NetworkPolicy |
| Cilium | eBPF | 极高 | L7策略 |
| Weave | Overlay | 中 | 加密通信 |

**Flannel部署**：
```bash
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```


**Calico部署**：
```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

### 4.3 Service（服务发现）

#### ClusterIP（默认）

**集群内部访问**：
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  type: ClusterIP
  selector:
    app: nginx
  ports:
  - port: 80        # Service端口
    targetPort: 80  # Pod端口
```

**访问方式**：
```bash
# 集群内访问
curl nginx-service.default.svc.cluster.local

# DNS解析
nginx-service              # 同命名空间
nginx-service.default      # 指定命名空间
nginx-service.default.svc.cluster.local  # 完整域名
```

#### NodePort

**暴露到节点端口**：
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080  # 30000-32767
```

**访问**：
```bash
curl <NodeIP>:30080
```

#### LoadBalancer

**云厂商负载均衡**：
```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-lb
spec:
  type: LoadBalancer
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
```

#### Headless Service

**不分配ClusterIP，直接访问Pod**：
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
spec:
  clusterIP: None  # Headless
  selector:
    app: mysql
  ports:
  - port: 3306
```

**DNS解析返回所有Pod IP**：
```bash
nslookup mysql-headless.default.svc.cluster.local
# 返回：
# mysql-0.mysql-headless.default.svc.cluster.local
# mysql-1.mysql-headless.default.svc.cluster.local
# mysql-2.mysql-headless.default.svc.cluster.local
```

### 4.4 Ingress（七层路由）

**安装Ingress Controller**：
```bash
# Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

**创建Ingress规则**：
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-service
            port:
              number: 80
  tls:
  - hosts:
    - myapp.example.com
    secretName: tls-secret
```

**TLS证书**：
```bash
kubectl create secret tls tls-secret \
  --cert=cert.crt \
  --key=cert.key
```

### 4.5 NetworkPolicy（网络策略）

**默认拒绝所有流量**：
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

**允许特定流量**：
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

**实战示例**：多层应用隔离
```yaml
# 前端 → 后端
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
spec:
  podSelector:
    matchLabels:
      tier: backend
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend
    ports:
    - port: 8080

---
# 后端 → 数据库
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
spec:
  podSelector:
    matchLabels:
      tier: database
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - port: 3306
```

---

## 5. 安全机制

### 5.1 RBAC（基于角色的访问控制）

**核心概念**：
```
Role / ClusterRole     # 定义权限
    ↕
RoleBinding / ClusterRoleBinding  # 绑定用户/服务账号
    ↕
User / ServiceAccount  # 认证主体
```

**创建Role**：
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
```

**创建RoleBinding**：
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```


**ClusterRole（跨命名空间）**：
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-admin
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

**ServiceAccount**：
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service-account
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-binding
subjects:
- kind: ServiceAccount
  name: my-service-account
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

**Pod使用ServiceAccount**：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-service-account
  containers:
  - name: app
    image: myapp
```

### 5.2 Pod Security Policy（PSP）

**限制Pod的安全行为**（已弃用，使用Pod Security Admission）：

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'persistentVolumeClaim'
  - 'secret'
```

### 5.3 Secrets管理

**创建Secret**：
```bash
# 从文件
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secret123

# 从YAML
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: YWRtaW4=  # base64编码
  password: c2VjcmV0MTIz
EOF
```

**使用Secret（环境变量）**：
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
  - name: app
    image: myapp
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-secret
          key: password
```


**使用Secret（文件挂载）**：
```yaml
spec:
  containers:
  - name: app
    image: myapp
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secret
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: db-secret
```

---

## 6. 资源管理

### 6.1 资源请求与限制

**Request vs Limit**：
- `Request`：调度依据，保证分配的最小资源
- `Limit`：资源上限，超过会被限制或OOM

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: frontend
spec:
  containers:
  - name: app
    image: myapp
    resources:
      requests:
        memory: "64Mi"
        cpu: "250m"      # 0.25核
      limits:
        memory: "128Mi"
        cpu: "500m"
```

### 6.2 QoS等级

**三种等级**：

| QoS | 条件 | 驱逐优先级 |
|-----|------|-----------|
| Guaranteed | Request = Limit | 最低 |
| Burstable | Request < Limit | 中 |
| BestEffort | 无Request/Limit | 最高 |

### 6.3 HPA（水平自动扩缩容）

**基于CPU自动扩容**：
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

**基于内存和自定义指标**：
```yaml
metrics:
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 75
- type: Pods
  pods:
    metric:
      name: http_requests_per_second
    target:
      type: AverageValue
      averageValue: "1000"
```

### 6.4 VPA（垂直自动扩缩容）

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-deployment
  updatePolicy:
    updateMode: "Auto"
```

---

## 7. 高可用部署

### 7.1 高可用架构

**Master节点高可用**：
```
LoadBalancer (HAProxy/Nginx)
├── Master1 (kube-apiserver)
├── Master2 (kube-apiserver)
└── Master3 (kube-apiserver)
```

### 7.2 应用高可用


**多副本 + 反亲和性**：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels:
                app: web
            topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx
        livenessProbe:
          httpGet:
            path: /healthz
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 7.3 PDB（Pod中断预算）

**保证最少可用Pod数**：
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web
```

---

## 8. 监控告警

### 8.1 Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### 8.2 Prometheus + Grafana

**部署Prometheus Operator**：
```bash
kubectl create ns monitoring
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```

---

## 9. 故障排查

### 9.1 常见问题

**Pod状态异常**：
```bash
# 查看Pod状态
kubectl get pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# 查看事件
kubectl get events --sort-by='.lastTimestamp'
```

**网络问题**：
```bash
# 进入Pod调试
kubectl exec -it <pod-name> -- /bin/bash

# DNS测试
nslookup kubernetes.default
```

---

## 10. 实战案例

### 10.1 部署微服务应用

**完整示例：部署SpringBoot应用到K8s**

**1. 创建Deployment**：
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spring-boot-app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spring-boot
  template:
    metadata:
      labels:
        app: spring-boot
    spec:
      containers:
      - name: app
        image: myregistry/spring-boot-app:v1.0
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: db.host
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: spring-boot-service
spec:
  selector:
    app: spring-boot
  ports:
  - port: 80
    targetPort: 8080
```

---

## 📚 总结


### 核心知识点

| 领域 | 关键技术 | 生产应用 |
|------|---------|---------|
| **调度** | 亲和性、污点、优先级 | 资源隔离、GPU调度 |
| **存储** | PV/PVC、StorageClass、CSI | 有状态服务 |
| **网络** | CNI、Service、Ingress、NetworkPolicy | 服务暴露、流量控制 |
| **安全** | RBAC、PSP、Secrets | 权限管理、密钥管理 |
| **资源** | Request/Limit、QoS、HPA/VPA | 资源优化、弹性伸缩 |
| **高可用** | 多副本、PDB、健康检查 | 业务连续性 |

### 最佳实践

✅ **调度优化**
- 合理使用亲和性分散Pod
- 专用节点使用污点隔离
- 设置优先级保证核心服务

✅ **存储管理**
- 使用StorageClass动态供给
- 选择合适的访问模式
- StatefulSet使用Headless Service

✅ **网络安全**
- 使用NetworkPolicy隔离流量
- Ingress配置TLS
- Service Mesh管理服务通信

✅ **资源控制**
- 所有Pod设置Request和Limit
- 核心服务使用Guaranteed QoS
- 配置HPA应对流量波动

✅ **高可用部署**
- Master节点至少3个
- 应用多副本 + 反亲和性
- 配置PDB保证可用性
- 健康检查及时发现故障

---

## 🔗 相关资源

- [Kubernetes官方文档](https://kubernetes.io/docs/)
- [Kubernetes GitHub](https://github.com/kubernetes/kubernetes)
- 极客时间《深入剖析Kubernetes》
- 《Kubernetes in Action》

---

**作者**: Java高级工程师知识库  
**更新时间**: 2025-10-29  
**版本**: v1.0

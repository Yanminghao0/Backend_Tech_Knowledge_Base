# Service Mesh(Istio)详解

> 下一代微服务治理：流量管理、安全、可观测性

---

## 📋 目录

- [1. Service Mesh概述](#1-service-mesh概述)
- [2. Istio架构](#2-istio架构)
- [3. 流量管理](#3-流量管理)
- [4. 安全机制](#4-安全机制)
- [5. 可观测性](#5-可观测性)
- [6. 灰度发布](#6-灰度发布)
- [7. 故障注入](#7-故障注入)
- [8. 最佳实践](#8-最佳实践)

---

## 🎯 学习目标

- ✅ 理解Service Mesh核心理念
- ✅ 掌握Istio架构与核心组件
- ✅ 实现智能流量管理（路由、重试、超时、熔断）
- ✅ 配置服务间mTLS加密
- ✅ 实现全链路追踪与监控
- ✅ 掌握金丝雀、蓝绿发布
- ✅ 故障注入与混沌工程

---

## 1. Service Mesh概述

### 1.1 什么是Service Mesh

**定义**：
> Service Mesh是一个专用的基础设施层，用于处理服务间通信。它通过轻量级网络代理（Sidecar）实现微服务治理。

**核心特性**：
- 🔹 **流量管理**：路由、负载均衡、重试、超时、熔断
- 🔹 **安全**：mTLS、认证、授权
- 🔹 **可观测性**：指标、日志、追踪
- 🔹 **策略执行**：限流、配额、黑白名单

### 1.2 为什么需要Service Mesh

**传统微服务的痛点**：
```
业务代码 + 服务治理代码（SDK）耦合
├── 限流熔断逻辑侵入业务代码
├── SDK升级困难
├── 多语言治理复杂
└── 统一治理困难
```

**Service Mesh解决方案**：
```
业务代码（应用容器）
    ↕ localhost
Sidecar代理（Envoy）
    ↕ 网络
Sidecar代理（Envoy）
    ↕ localhost
业务代码（应用容器）
```

**优势**：
- ✅ 业务代码与治理逻辑分离
- ✅ 多语言统一治理
- ✅ 无侵入式升级
- ✅ 统一配置管理

---

## 2. Istio架构

### 2.1 整体架构

**Istio 1.5+架构（简化）**：

```
控制平面（Control Plane）
└── Istiod（Pilot + Citadel + Galley）
    ├── 服务发现
    ├── 配置下发
    ├── 证书管理
    └── Sidecar注入

数据平面（Data Plane）
└── Envoy Proxy（每个Pod一个Sidecar）
    ├── 流量拦截
    ├── 策略执行
    ├── 遥测数据上报
    └── mTLS加密
```

### 2.2 核心组件

#### Istiod

**职责**：
- 🔹 **Pilot**：服务发现、流量管理配置
- 🔹 **Citadel**：证书管理、mTLS
- 🔹 **Galley**：配置验证、分发

#### Envoy Proxy

**功能**：
- 动态服务发现
- 负载均衡
- TLS终止
- HTTP/2、gRPC代理
- 熔断、重试、超时
- 指标收集

### 2.3 安装Istio

**使用istioctl安装**：
```bash
# 下载Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-1.20.0
export PATH=$PWD/bin:$PATH

# 安装（demo配置）
istioctl install --set profile=demo -y

# 启用自动Sidecar注入
kubectl label namespace default istio-injection=enabled
```

**验证安装**：
```bash
kubectl get pods -n istio-system
# 应该看到istiod运行中
```

---

## 3. 流量管理

### 3.1 核心资源

**Istio流量管理CRD**：
- `VirtualService`：路由规则
- `DestinationRule`：目标策略（负载均衡、连接池、熔断）
- `Gateway`：入口网关
- `ServiceEntry`：注册外部服务

### 3.2 VirtualService（路由规则）

#### 基于版本路由

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v1
```

#### 基于权重的流量分配（金丝雀发布）

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 90
    - destination:
        host: reviews
        subset: v2
      weight: 10
```

#### 基于URL路径路由

```yaml
spec:
  hosts:
  - bookinfo.com
  http:
  - match:
    - uri:
        prefix: /api/v1
    route:
    - destination:
        host: reviews
        subset: v2
  - match:
    - uri:
        prefix: /api/v2
    route:
    - destination:
        host: reviews
        subset: v3
```

### 3.3 DestinationRule（目标策略）

#### 定义服务子集

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
  - name: v3
    labels:
      version: v3
```

#### 负载均衡策略

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
spec:

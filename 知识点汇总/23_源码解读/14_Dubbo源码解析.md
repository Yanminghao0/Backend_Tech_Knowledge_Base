# Dubbo源码解析

> SPI机制、服务发布、服务引用、负载均衡核心原理

---

## 📋 目录

- [1. Dubbo架构](#1-dubbo架构)
- [2. SPI机制](#2-spi机制)
- [3. 服务发布流程](#3-服务发布流程)
- [4. 服务引用流程](#4-服务引用流程)
- [5. 服务调用流程](#5-服务调用流程)
- [6. 负载均衡](#6-负载均衡)
- [7. 集群容错](#7-集群容错)
- [8. 面试高频问题](#8-面试高频问题)

---

## 🎯 学习目标

- ✅ 理解Dubbo整体架构
- ✅ 掌握SPI扩展机制
- ✅ 理解服务暴露流程
- ✅ 理解服务引用流程
- ✅ 掌握负载均衡策略实现
- ✅ 理解集群容错机制

---

## 1. Dubbo架构

### 1.1 核心角色

```
┌──────────┐         ┌──────────┐
│ Provider │         │ Consumer │
│ (服务提供者)│         │ (服务消费者)│
└────┬─────┘         └────┬─────┘
     │register           │subscribe
     │                    │
     ▼                    ▼
┌────────────────────────────┐
│     Registry(注册中心)       │
│  (Zookeeper/Nacos/Redis)   │
└────────────────────────────┘
     │                    │
     │notify              │
     └────────────────────┘
           │
           ▼
    ┌────────────┐
    │  Monitor   │
    │ (监控中心)   │
    └────────────┘
```

**核心流程**：
1. Provider向Registry注册服务
2. Consumer从Registry订阅服务
3. Registry推送服务列表给Consumer
4. Consumer根据负载均衡选择Provider发起调用
5. Monitor统计调用次数和时间

### 1.2 分层架构

```
┌─────────────────────────────────────┐
│         Business (业务层)             │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│         RPC (远程调用层)              │
│  Protocol | Proxy | Registry        │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│       Remoting (远程通信层)           │
│  Exchange | Transport | Serialize   │
└─────────────────────────────────────┘
```

---

## 2. SPI机制

### 2.1 JDK SPI vs Dubbo SPI

**JDK SPI缺点**：
- 一次加载所有实现类
- 无法按需加载
- 不支持依赖注入
- 无法获取扩展点名称

**Dubbo SPI优势**：
- 按需加载
- 支持AOP、IOC
- 自适应扩展（Adaptive）
- 扩展点自动包装（Wrapper）

### 2.2 Dubbo SPI示例

**扩展点接口**：
```java
@SPI("random")  // 默认实现
public interface LoadBalance {
    @Adaptive({"loadbalance"})  // 自适应扩展
    <T> Invoker<T> select(List<Invoker<T>> invokers, URL url, Invocation invocation);
}
```

**实现类**：
```java
public class RandomLoadBalance extends AbstractLoadBalance {
    @Override
    protected <T> Invoker<T> doSelect(List<Invoker<T>> invokers, URL url, Invocation invocation) {
        // 随机负载均衡实现
    }
}
```

**配置文件**：
```
# META-INF/dubbo/org.apache.dubbo.rpc.cluster.LoadBalance
random=org.apache.dubbo.rpc.cluster.loadbalance.RandomLoadBalance
roundrobin=org.apache.dubbo.rpc.cluster.loadbalance.RoundRobinLoadBalance
leastactive=org.apache.dubbo.rpc.cluster.loadbalance.LeastActiveLoadBalance
```

**使用**：
```java
ExtensionLoader<LoadBalance> loader = ExtensionLoader.getExtensionLoader(LoadBalance.class);
LoadBalance loadBalance = loader.getExtension("random");
```

---

## 3. 服务发布流程

### 3.1 核心流程

```
1. ServiceConfig.export()
    ↓
2. 根据协议暴露服务
    ↓
3. 创建Invoker
    ↓
4. 启动NettyServer
    ↓
5. 注册服务到注册中心
```

### 3.2 核心代码

```java
// ServiceConfig#export()
public synchronized void export() {
    if (!shouldExport()) {
        return;
    }
    
    // 延迟暴露
    if (delay != null && delay > 0) {
        Thread.sleep(delay);
    }
    
    // 执行暴露
    doExport();
}

// ServiceConfig#doExportUrls()
private void doExportUrls() {
    // 加载注册中心
    List<URL> registryURLs = loadRegistries(true);
    
    // 遍历协议，分别暴露
    for (ProtocolConfig protocolConfig : protocols) {
        doExportUrlsFor1Protocol(protocolConfig, registryURLs);
    }
}

// ServiceConfig#doExportUrlsFor1Protocol()
private void doExportUrlsFor1Protocol(ProtocolConfig protocolConfig, List<URL> registryURLs) {
    // 构建服务URL
    URL url = new URL(name, host, port, path, map);
    
    // 1. 本地暴露（injvm协议）
    if (scope == null || !Constants.SCOPE_REMOTE.equals(scope)) {
        exportLocal(url);
    }
    
    // 2. 远程暴露
    if (scope == null || !Constants.SCOPE_LOCAL.equals(scope)) {
        // 创建Invoker
        Invoker<?> invoker = proxyFactory.getInvoker(ref, (Class) interfaceClass, url);
        
        // Protocol暴露服务
        Exporter<?> exporter = protocol.export(invoker);
        
        // 注册到注册中心
        register(registryURL.addParameterAndEncoded(EXPORT_KEY, url.toFullString()));
    }
}
```

---

## 4. 服务引用流程

### 4.1 核心流程

```
1. ReferenceConfig.get()
    ↓
2. 创建代理对象
    ↓
3. 从注册中心订阅服务
    ↓
4. 创建Invoker
    ↓
5. 包装成Cluster
    ↓
6. 返回代理对象
```

### 4.2 核心代码

```java
// ReferenceConfig#get()
public synchronized T get() {
    if (ref == null) {
        init();
    }
    return ref;
}

// ReferenceConfig#init()
private void init() {
    // 创建代理
    ref = createProxy(map);
}

// ReferenceConfig#createProxy()
private T createProxy(Map<String, String> map) {
    // 1. 从注册中心获取服务列表
    URL url = loadRegistries(false);
    
    // 2. Protocol引用服务，返回Invoker
    invoker = refprotocol.refer(interfaceClass, url);
    
    // 3. 创建代理对象
    return (T) proxyFactory.getProxy(invoker);
}
```

---

## 5. 服务调用流程

### 5.1 调用链路

```
Proxy (代理对象)
  ↓
InvokerInvocationHandler (调用处理器)
  ↓
MockClusterInvoker (Mock集群容错)
  ↓
FailoverClusterInvoker (容错策略)
  ↓
RegistryDirectory (服务目录)
  ↓
Router (路由)
  ↓
LoadBalance (负载均衡)
  ↓
Filter (过滤器链)
  ↓
DubboInvoker (Dubbo协议)
  ↓
NettyClient (网络通信)
  ↓
Provider
```

---

## 6. 负载均衡

### 6.1 负载均衡策略

**Random（随机）**：
```java
public class RandomLoadBalance extends AbstractLoadBalance {
    protected <T> Invoker<T> doSelect(List<Invoker<T>> invokers, URL url, Invocation invocation) {
        int length = invokers.size();
        boolean sameWeight = true;
        int[] weights = new int[length];
        int totalWeight = 0;
        
        // 计算总权重
        for (int i = 0; i < length; i++) {
            int weight = getWeight(invokers.get(i), invocation);
            weights[i] = weight;
            totalWeight += weight;
            if (sameWeight && i > 0 && weight != weights[i - 1]) {
                sameWeight = false;
            }
        }
        
        // 权重随机
        if (totalWeight > 0 && !sameWeight) {
            int offset = ThreadLocalRandom.current().nextInt(totalWeight);
            for (int i = 0; i < length; i++) {
                offset -= weights[i];
                if (offset < 0) {
                    return invokers.get(i);
                }
            }
        }
        
        // 普通随机
        return invokers.get(ThreadLocalRandom.current().nextInt(length));
    }
}
```

**策略对比**：
| 策略 | 特点 | 适用场景 |
|------|------|---------|
| Random | 按权重随机 | 通用 |
| RoundRobin | 轮询 | 性能相近的服务器 |
| LeastActive | 最少活跃调用数 | 响应时间差异大 |
| ConsistentHash | 一致性Hash | 需要会话保持 |

---

## 7. 集群容错

### 7.1 容错策略

**Failover（失败自动切换）**：
```java
public class FailoverClusterInvoker<T> extends AbstractClusterInvoker<T> {
    public Result doInvoke(Invocation invocation, List<Invoker<T>> invokers, LoadBalance loadbalance) {
        // 重试次数
        int len = getUrl().getMethodParameter(methodName, RETRIES_KEY, DEFAULT_RETRIES) + 1;
        
        for (int i = 0; i < len; i++) {
            // 负载均衡选择Invoker
            Invoker<T> invoker = select(loadbalance, invocation, invokers, invoked);
            invoked.add(invoker);
            
            try {
                // 执行调用
                Result result = invoker.invoke(invocation);
                return result;
            } catch (RpcException e) {
                // 失败重试下一个
                if (i == len - 1) {
                    throw e;
                }
            }
        }
    }
}
```

**容错策略对比**：
| 策略 | 说明 | 适用场景 |
|------|------|---------|
| Failover | 失败重试其他服务器 | 读操作 |
| Failfast | 快速失败，只调用一次 | 写操作 |
| Failsafe | 失败忽略 | 日志记录 |
| Failback | 失败后台重试 | 消息通知 |
| Forking | 并行调用多个，一个成功即返回 | 实时性要求高 |

---

## 8. 面试高频问题

### Q1: Dubbo的调用流程？

**答案**：
1. Consumer调用代理对象
2. 经过Filter过滤器链
3. Cluster集群容错
4. LoadBalance负载均衡选择Invoker
5. Protocol发起远程调用
6. 序列化请求
7. Netty发送数据
8. Provider接收并反序列化
9. 执行本地方法
10. 返回结果

### Q2: Dubbo SPI和JDK SPI的区别？

**答案**：
- JDK SPI：全量加载，不支持依赖注入
- Dubbo SPI：按需加载，支持AOP/IOC，支持自适应扩展

### Q3: Dubbo有哪些负载均衡策略？

**答案**：
1. Random - 随机（默认）
2. RoundRobin - 轮询
3. LeastActive - 最少活跃调用数
4. ConsistentHash - 一致性Hash

### Q4: Dubbo有哪些容错策略？

**答案**：
1. Failover - 失败自动切换（默认）
2. Failfast - 快速失败
3. Failsafe - 失败安全
4. Failback - 失败自动恢复
5. Forking - 并行调用
6. Broadcast - 广播调用

### Q5: Dubbo如何实现服务降级？

**答案**：
1. Mock机制
2. 超时降级
3. 失败降级
4. 限流降级

---

## 📚 参考资料

- 《深入理解Apache Dubbo与实战》
- [Dubbo官方文档](https://dubbo.apache.org/zh/)
- [Dubbo源码GitHub](https://github.com/apache/dubbo)

---

**最后更新时间**：2025-10-29

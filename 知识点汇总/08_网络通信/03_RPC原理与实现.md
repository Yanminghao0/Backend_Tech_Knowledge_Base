# RPC原理与实现

> 从动态代理到序列化协议，深入理解远程过程调用的全链路原理

---

## 📋 目录

1. [RPC概述](#1-rpc概述)
2. [RPC核心流程](#2-rpc核心流程)
3. [动态代理](#3-动态代理)
4. [序列化协议](#4-序列化协议)
5. [网络通信](#5-网络通信)
6. [服务注册与发现](#6-服务注册与发现)
7. [主流RPC框架对比](#7-主流rpc框架对比)
8. [面试要点](#8-面试要点)

---

## 1. RPC概述

### 什么是RPC

```
RPC (Remote Procedure Call) 远程过程调用：
  让调用远程方法像调用本地方法一样简单。

本地调用：
  String result = userService.getUser(1);

远程调用（RPC）：
  // 看起来和本地调用一样，但实际跨网络
  @DubboReference
  private UserService userService;
  String result = userService.getUser(1);
```

### RPC vs HTTP

| 维度 | RPC | HTTP |
|------|-----|------|
| 定位 | 方法级调用 | 资源级操作 |
| 协议 | TCP（通常） | HTTP（TCP之上） |
| 序列化 | 二进制（高效） | JSON/XML（可读） |
| 性能 | 高 | 中 |
| 跨语言 | 需IDL（gRPC） | 天然跨语言 |
| 适用场景 | 微服务内部通信 | 面向外部API |

---

## 2. RPC核心流程

```
调用方(Consumer)                    服务方(Provider)
    │                                    │
    1. 调用本地代理方法                      │
    │                                    │
    2. 代理封装请求                          │
    │ (接口名+方法名+参数+序列化)            │
    │                                    │
    3. 网络发送 ──────────────────────→  4. 接收请求
    │                                    │
    │                                    5. 反序列化
    │                                    │
    │                                    6. 反射调用本地实现
    │                                    │
    │                                    7. 序列化返回值
    │                                    │
    8. 接收响应 ←──────────────────────  网络返回
    │                                    │
    9. 反序列化结果                          │
    │                                    │
    10. 返回给调用方                         │
```

### 核心组件

```
1. 代理层(Proxy)：屏蔽远程调用细节
2. 序列化层(Serialization)：对象 ↔ 字节流
3. 网络层(Transport)：数据传输
4. 注册中心(Registry)：服务发现
```

---

## 3. 动态代理

### JDK动态代理

```java
// RPC客户端代理：让远程调用看起来像本地调用
public class RpcProxy implements InvocationHandler {
    
    private final String serviceName;
    private final String serviceAddress;
    
    @SuppressWarnings("unchecked")
    public static <T> T create(Class<T> interfaceClass, String address) {
        return (T) Proxy.newProxyInstance(
            interfaceClass.getClassLoader(),
            new Class<?>[]{interfaceClass},
            new RpcProxy(interfaceClass.getName(), address)
        );
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        // 1. 封装请求
        RpcRequest request = new RpcRequest();
        request.setInterfaceName(method.getDeclaringClass().getName());
        request.setMethodName(method.getName());
        request.setParameterTypes(method.getParameterTypes());
        request.setParameters(args);
        
        // 2. 序列化
        byte[] data = serialize(request);
        
        // 3. 网络发送
        byte[] responseData = httpClient.post(serviceAddress, data);
        
        // 4. 反序列化
        RpcResponse response = deserialize(responseData, RpcResponse.class);
        
        // 5. 返回结果
        if (response.getError() != null) {
            throw new RuntimeException(response.getError());
        }
        return response.getResult();
    }
}

// 使用
UserService userService = RpcProxy.create(UserService.class, "http://10.0.0.1:8080");
User user = userService.getUser(1);  // 像本地调用一样
```

### Dubbo代理机制

```java
// Dubbo使用javassist字节码增强，比JDK代理更快
// @DubboReference注解 → Dubbo自动生成代理

@DubboReference(timeout = 3000, retries = 2)
private UserService userService;

// Dubbo内部流程：
// 1. 创建Invoker代理（MockClusterInvoker → FailoverClusterInvoker → DubboInvoker）
// 2. 调用Invoker.invoke() → 负载均衡选择Provider → 网络调用
// 3. 返回结果
```

---

## 4. 序列化协议

### 协议对比

| 协议 | 性能 | 体积 | 跨语言 | 可读性 | 适用场景 |
|------|------|------|--------|--------|---------|
| JSON | 中 | 大 | ✅ | ✅ | REST API |
| Protobuf | 高 | 小 | ✅ | ❌ | gRPC |
| Hessian2 | 高 | 中 | ✅ | ❌ | Dubbo默认 |
| Kryo | 极高 | 极小 | ❌(Java) | ❌ | Java内部 |
| JDK | 低 | 大 | ❌(Java) | ❌ | 不推荐 |

### Protobuf示例

```protobuf
// 定义消息格式 (.proto文件)
syntax = "proto3";

message UserRequest {
    int64 id = 1;
}

message UserResponse {
    int64 id = 1;
    string name = 2;
    int32 age = 3;
}

service UserService {
    rpc getUser(UserRequest) returns (UserResponse);
}
```

```java
// gRPC使用Protobuf序列化
UserRequest request = UserRequest.newBuilder().setId(1L).build();
UserResponse response = userServiceBlockingStub.getUser(request);
// Protobuf序列化后仅几十字节，比JSON小5-10倍
```

### Hessian2（Dubbo默认）

```java
// Dubbo序列化配置
@DubboReference(serialization = "hessian2")
private UserService userService;

// Hessian2优势：
// - 自描述序列化（不需要schema文件）
// - 支持复杂对象图
// - 体积比JSON小，性能比JSON高
```

---

## 5. 网络通信

### Netty实现RPC通信

```java
// RPC服务端：Netty接收请求
public class RpcServer {
    
    public void start(int port) {
        EventLoopGroup boss = new NioEventLoopGroup(1);
        EventLoopGroup worker = new NioEventLoopGroup();
        
        ServerBootstrap bootstrap = new ServerBootstrap();
        bootstrap.group(boss, worker)
            .channel(NioServerSocketChannel.class)
            .childHandler(new ChannelInitializer<SocketChannel>() {
                @Override
                protected void initChannel(SocketChannel ch) {
                    ch.pipeline()
                        // 长度字段解码器（解决粘包拆包）
                        .addLast(new LengthFieldBasedFrameDecoder(65536, 0, 4, 0, 4))
                        .addLast(new LengthFieldPrepender(4))
                        // 序列化/反序列化
                        .addLast(new HessianDecoder())
                        .addLast(new HessianEncoder())
                        // 业务处理
                        .addLast(new RpcRequestHandler());
                }
            });
        bootstrap.bind(port).sync();
    }
}

// 请求处理器
public class RpcRequestHandler extends SimpleChannelInboundHandler<RpcRequest> {
    
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, RpcRequest request) {
        // 1. 根据接口名找到实现类
        Object service = serviceRegistry.get(request.getInterfaceName());
        
        // 2. 反射调用方法
        Method method = service.getClass().getMethod(
            request.getMethodName(), request.getParameterTypes());
        Object result = method.invoke(service, request.getParameters());
        
        // 3. 返回结果
        RpcResponse response = new RpcResponse();
        response.setResult(result);
        ctx.writeAndFlush(response);
    }
}
```

### 粘包拆包解决方案

```
TCP是流式协议，没有消息边界：

解决方案：
1. 固定长度：每条消息固定长度（浪费空间）
2. 分隔符：用特殊字符分隔（消息不能含分隔符）
3. 长度字段：消息头中包含消息体长度（最常用）

Dubbo协议头（16字节）：
  0-1: 魔数(0xdabb)
  2:   标志位(请求/响应/序列化方式)
  3:   状态码
  4-7: 请求ID
  8-11:数据长度
  12-15:保留
```

---

## 6. 服务注册与发现

### 注册中心交互流程

```
Provider启动：
  1. 向注册中心注册服务（接口名 + IP:Port）
  2. 注册中心通知Consumer服务变更

Consumer调用：
  1. 从注册中心订阅服务列表
  2. 本地缓存服务地址
  3. 负载均衡选择一个Provider
  4. 发起RPC调用

Provider下线：
  1. 注册中心检测到Provider下线
  2. 通知Consumer更新服务列表
```

### 负载均衡策略

```java
// Dubbo负载均衡配置
@DubboReference(loadbalance = "roundrobin")  // 轮询
private UserService userService;

// 策略列表：
// random   - 随机（默认，按权重随机）
// roundrobin - 轮询（按权重轮询）
// leastactive - 最少活跃数（慢的Provider少分配）
// consistenthash - 一致性哈希（相同参数到同一Provider）
// shortestresponse - 最短响应时间（Dubbo 2.7+）
```

---

## 7. 主流RPC框架对比

| 框架 | 序列化 | 协议 | 注册中心 | 跨语言 | 特点 |
|------|--------|------|---------|--------|------|
| Dubbo | Hessian2 | Dubbo协议 | Nacos/ZK | ❌ | Java生态，功能丰富 |
| gRPC | Protobuf | HTTP/2 | 需外接 | ✅ | Google出品，跨语言 |
| Thrift | Thrift | TBinary | 需外接 | ✅ | Facebook出品 |
| Motan | Hessian2 | Motan | Consul/ZK | ❌ | 微博出品 |

### Dubbo vs gRPC选型

```
Dubbo：
  ✅ Java生态，注解驱动，开发简单
  ✅ 丰富的服务治理（限流/降级/集群容错）
  ❌ 仅限Java

gRPC：
  ✅ 跨语言（Java/Go/Python/C++）
  ✅ HTTP/2多路复用
  ✅ Protobuf高性能序列化
  ❌ 需要写.proto文件
  ❌ 服务治理需自己实现

选型：
  - 纯Java微服务 → Dubbo
  - 多语言微服务 → gRPC
  - 对外API → HTTP/REST
```

---

## 8. 面试要点

### Q1: RPC和HTTP的区别？

```
RPC是概念（远程过程调用），HTTP是协议。

RPC通常基于TCP：
  - 自定义二进制协议，头部开销小
  - 长连接复用，减少握手开销
  - 二进制序列化，体积小速度快

HTTP：
  - 文本协议，头部开销大
  - 每次请求可能新建连接（HTTP Keep-Alive可复用）
  - JSON序列化，可读但体积大

实际：gRPC用的就是HTTP/2，但通过Protobuf序列化提升性能
```

### Q2: Dubbo的一次调用流程？

```
1. Consumer调用代理方法
2. 代理 → ClusterInvoker（集群容错）
3. → LoadBalance（选择Provider）
4. → DubboInvoker（发起网络调用）
5. → ExchangeClient（Netty发送请求）
6. Provider接收 → 反射调用实现类 → 返回结果
7. Consumer接收响应 → 反序列化 → 返回结果
```

### Q3: RPC如何处理超时？

```
1. Consumer设置超时时间（如3000ms）
2. 发起调用时启动定时器
3. 超时未收到响应 → 取消请求 → 抛超时异常
4. Provider可能还在处理 → 丢弃响应（Consumer已超时）

Dubbo超时配置：
  @DubboReference(timeout = 3000)
  
建议：Consumer超时 > Provider超时（避免Consumer等不到结果）
```

### Q4: 序列化协议怎么选？

```
性能优先：Kryo（Java） / Protobuf（跨语言）
兼容性优先：JSON / Hessian2
空间优先：Protobuf / Kryo

Dubbo默认Hessian2：
  - 自描述（不需要schema）
  - 跨语言
  - 兼容性好
  - 性能中等偏上
```

### Q5: 如何实现RPC的异步调用？

```java
// Dubbo异步调用
@DubboReference(async = true)
private UserService userService;

// 调用后立即返回
CompletableFuture<User> future = userService.getUserAsync(1L);

// 做其他事情
doSomethingElse();

// 等待结果
User user = future.get(3, TimeUnit.SECONDS);
```

---

## 📚 相关阅读

- [02_Netty核心原理详解](./02_Netty核心原理详解.md)
- [01_HTTP协议与网络编程](./01_HTTP协议与网络编程.md)
- [Dubbo与gRPC详解](../06_微服务/通信协议/01_Dubbo与gRPC详解.md)
- [Dubbo源码解析](../22_源码解读/13_Dubbo源码解读/README.md)

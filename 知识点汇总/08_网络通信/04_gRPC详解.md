# gRPC详解

> Google出品的高性能RPC框架，基于HTTP/2和Protobuf构建

---

## 📋 目录

1. [gRPC概述](#1-grpc概述)
2. [Protobuf协议](#2-protobuf协议)
3. [HTTP/2基础](#3-http2基础)
4. [四种调用模式](#4-四种调用模式)
5. [Spring Boot集成](#5-spring-boot集成)
6. [gRPC vs Dubbo](#6-grpc-vs-dubbo)
7. [面试要点](#7-面试要点)

---

## 1. gRPC概述

### 核心特性

```
1. 跨语言：Protobuf IDL定义接口，自动生成多语言代码
2. HTTP/2：多路复用、头部压缩、流式传输
3. Protobuf：二进制序列化，体积小速度快
4. 四种模式：Unary/Server Stream/Client Stream/Bidirectional
5. 健康检查：标准健康检查协议
6. 拦截器：支持客户端/服务端拦截器
```

### 架构

```
┌────────────┐     ┌────────────┐
│  Client    │     │  Server    │
│ (Java/Go/  │     │ (Java/Go/  │
│  Python)   │     │  Python)   │
├────────────┤     ├────────────┤
│ gRPC Stub  │     │ gRPC Server│
├────────────┤     ├────────────┤
│  HTTP/2    │ ←→  │  HTTP/2    │
├────────────┤     ├────────────┤
│ Protobuf   │     │ Protobuf   │
└────────────┘     └────────────┘
```

---

## 2. Protobuf协议

### 定义.proto文件

```protobuf
syntax = "proto3";

package com.example.grpc;
option java_package = "com.example.grpc";
option java_multiple_files = true;

// 用户服务
service UserService {
    // Unary：一元调用（请求-响应）
    rpc getUser(UserRequest) returns (UserResponse);
    
    // Server Streaming：服务端流
    rpc listUsers(ListUsersRequest) returns (stream UserResponse);
    
    // Client Streaming：客户端流
    rpc batchCreate(stream CreateUserRequest) returns (BatchCreateResponse);
    
    // Bidirectional Streaming：双向流
    rpc chat(stream ChatMessage) returns (stream ChatMessage);
}

message UserRequest {
    int64 id = 1;
}

message UserResponse {
    int64 id = 1;
    string name = 2;
    string email = 3;
    int32 age = 4;
    repeated string roles = 5;
}

message ListUsersRequest {
    int32 page = 1;
    int32 size = 2;
    string keyword = 3;
}
```

### Protobuf优势

```
vs JSON：
  - 体积小3-10倍（二进制 vs 文本）
  - 解析快20-100倍（无需解析字符串）
  - 类型安全（编译时检查）

vs Hessian2：
  - 跨语言（Protobuf原生支持多语言）
  - 需要schema文件（Hessian2自描述）
  - 更紧凑

字段编号规则：
  1-15：1字节编码（高频字段用）
  16-2047：2字节编码
  字段编号一旦使用不可更改
```

---

## 3. HTTP/2基础

### HTTP/2 vs HTTP/1.1

| 特性 | HTTP/1.1 | HTTP/2 |
|------|----------|--------|
| 传输 | 文本 | 二进制 |
| 多路复用 | ❌ | ✅ 一个连接并发多个请求 |
| 头部压缩 | ❌ | ✅ HPACK压缩 |
| 服务端推送 | ❌ | ✅ Server Push |
| 流式传输 | ❌ | ✅ Stream |

### 多路复用

```
HTTP/1.1：
  请求1 → 响应1 → 请求2 → 响应2（串行，或开多个连接）

HTTP/2：
  单个TCP连接上：
    Stream 1: 请求1 → 响应1
    Stream 2: 请求2 → 响应2    （并发）
    Stream 3: 请求3 → 响应3

gRPC利用HTTP/2多路复用：
  - 单个TCP连接处理所有RPC调用
  - 减少连接数和握手开销
  - 支持流式传输
```

---

## 4. 四种调用模式

### Unary RPC（一元调用）

```java
// 服务端实现
public class UserServiceImpl extends UserServiceGrpc.UserServiceImplBase {
    @Override
    public void getUser(UserRequest request, StreamObserver<UserResponse> responseObserver) {
        User user = userMapper.selectById(request.getId());
        UserResponse response = UserResponse.newBuilder()
            .setId(user.getId())
            .setName(user.getName())
            .setEmail(user.getEmail())
            .build();
        responseObserver.onNext(response);
        responseObserver.onCompleted();
    }
}

// 客户端调用
UserResponse response = userServiceBlockingStub.getUser(
    UserRequest.newBuilder().setId(1L).build()
);
```

### Server Streaming RPC（服务端流）

```java
// 服务端：返回多个结果
@Override
public void listUsers(ListUsersRequest request, 
        StreamObserver<UserResponse> responseObserver) {
    List<User> users = userMapper.findByPage(request.getPage(), request.getSize());
    for (User user : users) {
        responseObserver.onNext(toResponse(user));  // 逐条发送
    }
    responseObserver.onCompleted();
}

// 客户端：接收流
Iterator<UserResponse> iterator = userServiceStub.listUsers(
    ListUsersRequest.newBuilder().setPage(1).setSize(100).build()
);
while (iterator.hasNext()) {
    UserResponse user = iterator.next();
    System.out.println(user.getName());
}
```

### Client Streaming RPC（客户端流）

```java
// 服务端：接收多个请求
@Override
public StreamObserver<CreateUserRequest> batchCreate(
        StreamObserver<BatchCreateResponse> responseObserver) {
    return new StreamObserver<CreateUserRequest>() {
        int successCount = 0;
        
        @Override
        public void onNext(CreateUserRequest request) {
            userMapper.insert(toUser(request));
            successCount++;
        }
        
        @Override
        public void onError(Throwable t) {
            log.error("批量创建异常", t);
        }
        
        @Override
        public void onCompleted() {
            responseObserver.onNext(
                BatchCreateResponse.newBuilder()
                    .setSuccessCount(successCount)
                    .build()
            );
            responseObserver.onCompleted();
        }
    };
}
```

### Bidirectional Streaming RPC（双向流）

```java
// 双向流聊天
@Override
public StreamObserver<ChatMessage> chat(
        StreamObserver<ChatMessage> responseObserver) {
    return new StreamObserver<ChatMessage>() {
        @Override
        public void onNext(ChatMessage message) {
            // 接收消息 → 处理 → 返回响应
            ChatMessage reply = ChatMessage.newBuilder()
                .setUserId(message.getUserId())
                .setContent("收到: " + message.getContent())
                .setTimestamp(System.currentTimeMillis())
                .build();
            responseObserver.onNext(reply);
        }
        
        @Override
        public void onError(Throwable t) {
            log.error("聊天异常", t);
        }
        
        @Override
        public void onCompleted() {
            responseObserver.onCompleted();
        }
    };
}
```

---

## 5. Spring Boot集成

### 依赖配置

```xml
<!-- grpc-spring-boot-starter -->
<dependency>
    <groupId>net.devh</groupId>
    <artifactId>grpc-server-spring-boot-starter</artifactId>
    <version>3.1.0</version>
</dependency>
<dependency>
    <groupId>net.devh</groupId>
    <artifactId>grpc-client-spring-boot-starter</artifactId>
    <version>3.1.0</version>
</dependency>
```

### 服务端

```java
// 服务端：使用注解暴露gRPC服务
@GrpcService
public class UserGrpcService extends UserServiceGrpc.UserServiceImplBase {
    
    @Autowired
    private UserMapper userMapper;
    
    @Override
    public void getUser(UserRequest request, 
            StreamObserver<UserResponse> responseObserver) {
        User user = userMapper.selectById(request.getId());
        responseObserver.onNext(toResponse(user));
        responseObserver.onCompleted();
    }
}

// application.yml
grpc:
  server:
    port: 9090
```

### 客户端

```java
// 客户端：注入gRPC Stub
@Service
public class UserGrpcClient {
    
    @GrpcClient("user-service")
    private UserServiceGrpc.UserServiceBlockingStub blockingStub;
    
    @GrpcClient("user-service")
    private UserServiceGrpc.UserServiceStub asyncStub;
    
    public UserResponse getUser(Long id) {
        return blockingStub.getUser(
            UserRequest.newBuilder().setId(id).build()
        );
    }
}

// application.yml
grpc:
  client:
    user-service:
      address: 'static://localhost:9090'
      negotiation-type: plaintext
```

### 拦截器

```java
// 服务端拦截器：日志/认证/限流
@GrpcGlobalServerInterceptor
public class LogInterceptor implements ServerInterceptor {
    @Override
    public <ReqT, RespT> ServerCall.Listener<ReqT> interceptCall(
            ServerCall<ReqT, RespT> call, Metadata headers,
            ServerCallHandler<ReqT, RespT> next) {
        long start = System.currentTimeMillis();
        log.info("gRPC调用: {}", call.getMethodDescriptor().getFullMethodName());
        
        return next.startCall(call, headers);
    }
}
```

---

## 6. gRPC vs Dubbo

| 维度 | gRPC | Dubbo |
|------|------|-------|
| 协议 | HTTP/2 | Dubbo协议(TCP) |
| 序列化 | Protobuf | Hessian2(默认) |
| 跨语言 | ✅ 原生支持 | ❌ 仅Java |
| 服务治理 | 弱（需自己实现） | 强（限流/降级/集群容错） |
| 注册中心 | 需外接(Nacos/Consul) | 内置支持 |
| 流式传输 | ✅ 四种模式 | ✅ Triple协议支持 |
| 学习成本 | 中（需学Protobuf） | 低（注解驱动） |
| 生态 | Google背书，全球生态 | 阿里背书，国内生态 |

### 选型建议

```
选gRPC：
  - 多语言微服务（Java+Go+Python）
  - 对外提供gRPC API
  - 需要流式传输（实时聊天/数据推送）
  - 团队接受Protobuf

选Dubbo：
  - 纯Java微服务
  - 需要丰富的服务治理
  - 快速开发，注解驱动
  - 国内团队，中文文档

混合方案：
  - 内部服务间：Dubbo（Java生态，治理完善）
  - 跨语言/对外：gRPC（标准协议，跨语言）
```

---

## 7. 面试要点

### Q1: gRPC为什么性能高？

```
1. HTTP/2多路复用：单连接并发多个请求，减少连接开销
2. Protobuf序列化：二进制编码，体积比JSON小3-10倍
3. 头部压缩：HPACK压缩HTTP头
4. 二进制传输：比文本协议解析更快
```

### Q2: gRPC的四种调用模式？

```
1. Unary：一请求一响应（最常用，类似普通RPC）
2. Server Streaming：一请求多响应（大数据量分批返回）
3. Client Streaming：多请求一响应（批量上传）
4. Bidirectional Streaming：双向流（实时聊天/推送）
```

### Q3: Protobuf为什么比JSON快？

```
1. 二进制编码 vs 文本编码
   - Protobuf用字段编号+类型+值，紧凑编码
   - JSON用key-value文本，冗余多

2. 解析方式
   - Protobuf直接按字段编号读取，无需解析字符串
   - JSON需要词法分析→语法分析→构建对象

3. 体积对比
   - 同一消息Protobuf约比JSON小3-10倍
   - 传输更快，缓存命中率更高
```

### Q4: gRPC和Dubbo怎么选？

```
gRPC适合：多语言、流式传输、对外API
Dubbo适合：纯Java、服务治理、快速开发

实际选择：
  - 纯Java微服务 → Dubbo（治理完善）
  - 多语言微服务 → gRPC（跨语言）
  - 对外提供API → gRPC（标准协议）
```

### Q5: gRPC如何做服务发现？

```
gRPC本身不提供服务发现，需要配合：
1. Nacos/Consul/etcd作为注册中心
2. 客户端实现NameResolver从注册中心获取地址
3. 客户端LoadBalancer做负载均衡

Spring Boot grpc-spring-boot-starter支持：
  - Nacos服务发现
  - 自动负载均衡（Round Robin）
```

---

## 📚 相关阅读

- [03_RPC原理与实现](./03_RPC原理与实现.md)
- [Dubbo与gRPC详解](../06_微服务/02_通信协议/01_Dubbo与gRPC详解.md)
- [02_Netty核心原理详解](./02_Netty核心原理详解.md)
- [Dubbo源码解析](../22_源码解读/13_Dubbo源码解读/README.md)

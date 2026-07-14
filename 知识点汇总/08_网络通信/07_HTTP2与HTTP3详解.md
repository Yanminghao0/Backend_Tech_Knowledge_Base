# HTTP/2与HTTP/3详解

> 从HTTP/1.1到HTTP/3：协议演进、性能优化与实战配置

---

## 📋 目录

1. [HTTP协议演进](#1-http协议演进)
2. [HTTP/2核心特性](#2-http2核心特性)
3. [HTTP/2实战配置](#3-http2实战配置)
4. [HTTP/3与QUIC](#4-http3与quic)
5. [版本对比](#5-版本对比)
6. [面试题速查](#6-面试题速查)

---

## 1. HTTP协议演进

```
HTTP/1.0 (1996)
  ├─ 每次请求新建TCP连接
  └─ 连接复用：Connection: keep-alive（非标准）

HTTP/1.1 (1997) — 使用最广泛
  ├─ 持久连接（keep-alive默认开启）
  ├─ 管道化（Pipeline）— 几乎没人用，队头阻塞
  ├─ 分块传输（Transfer-Encoding: chunked）
  └─ 缓存控制（Cache-Control, ETag）

HTTP/2 (2015) — 基于SPDY
  ├─ 二进制分帧（Binary Framing）
  ├─ 多路复用（Multiplexing）— 解决HTTP层队头阻塞
  ├─ 头部压缩（HPACK）
  ├─ 服务端推送（Server Push）
  └─ 基于TLS 1.2+（浏览器强制HTTPS）

HTTP/3 (2022) — 基于QUIC
  ├─ 基于UDP（非TCP）
  ├─ 解决TCP层队头阻塞
  ├─ 0-RTT连接建立
  ├─ 连接迁移（IP切换不断连）
  └─ 内置TLS 1.3
```

---

## 2. HTTP/2核心特性

### 2.1 二进制分帧

```
HTTP/1.1：文本协议
  GET /api/users HTTP/1.1\r\n
  Host: example.com\r\n
  \r\n

HTTP/2：二进制协议
  ┌──────────┬──────────┬──────────┐
  │ Length    │ Type     │ Flags    │
  │ (3字节)   │ (1字节)  │ (1字节)  │
  ├──────────┴──────────┴──────────┤
  │ Stream Identifier (4字节)       │
  ├─────────────────────────────────┤
  │ Frame Payload (变长)            │
  └─────────────────────────────────┘

一个HTTP请求/响应被拆分为多个Frame：
  Headers Frame → 头部信息
  Data Frame    → 请求体/响应体
```

### 2.2 多路复用

```
HTTP/1.1：一个TCP连接同时只能处理一个请求
  浏览器开6个并发连接 → 6个并行请求
  问题：连接多、资源消耗大

HTTP/2：一个TCP连接同时处理多个请求
  ┌──────── TCP连接 ────────┐
  │ Stream 1: GET /html     │ ← 并行
  │ Stream 3: GET /css      │ ← 并行
  │ Stream 5: GET /js       │ ← 并行
  │ Stream 7: GET /image    │ ← 并行
  └──────────────────────────┘
  一个连接上多个Stream并行，互不阻塞
```

### 2.3 头部压缩（HPACK）

```
HTTP/1.1：每次请求重复发送完整头部
  GET /api/users HTTP/1.1
  Host: example.com          ← 每次都发
  User-Agent: Mozilla/5.0... ← 每次都发（几百字节）
  Accept: application/json   ← 每次都发
  Cookie: session=xxx...     ← 每次都发（可能几KB）

HTTP/2：HPACK压缩
  ├─ 静态表：61个常见头部（如 :method, :path, host）
  ├─ 动态表：连接内共享，首次发送后后续引用索引
  └─ Huffman编码：压缩字符串

  首次：发送完整头部 → 存入动态表
  后续：只发索引号（如 62, 63, 64）→ 几个字节
```

### 2.4 服务端推送

```nginx
# Nginx配置服务端推送
server {
    listen 443 ssl http2;
    
    location /index.html {
        http2_push /style.css;
        http2_push /script.js;
        http2_push /logo.png;
    }
}

# 客户端请求 index.html
# 服务端主动推送 style.css, script.js, logo.png
# 减少客户端等待HTML解析后再请求的延迟
```

---

## 3. HTTP/2实战配置

### 3.1 Nginx配置

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # HTTP/2特性配置
    http2_max_concurrent_streams 128;
    http2_max_concurrent_pushes 10;
    http2_chunk_size 8k;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3.2 Spring Boot配置

```java
// Spring Boot 3.x + 内嵌Tomcat/Netty 默认支持HTTP/2
// application.yml
server:
  http2:
    enabled: true
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: changeit
    key-store-type: PKCS12
```

---

## 4. HTTP/3与QUIC

### 4.1 QUIC协议

```
QUIC = Quick UDP Internet Connections

  TCP + TLS 1.3 → QUIC（基于UDP）

  ┌─────────────────────────────┐
  │          Application          │
  ├─────────────────────────────┤
  │            HTTP/3             │
  ├─────────────────────────────┤
  │            QUIC               │ ← 传输层（UDP）
  ├─────────────────────────────┤
  │            UDP                │
  ├─────────────────────────────┤
  │              IP               │
  └─────────────────────────────┘

QUIC核心特性：
  1. 解决TCP队头阻塞：Stream间独立，一个丢包不阻塞其他
  2. 0-RTT连接建立：首次1-RTT，后续0-RTT（TLS 1.3）
  3. 连接迁移：基于Connection ID，IP变化不断连（WiFi切5G）
  4. 内置加密：TLS 1.3集成，无法明文嗅探
  5. 拥塞控制：改进的Cubic/BBR
```

### 4.2 HTTP/3 vs HTTP/2 队头阻塞对比

```
HTTP/2（TCP层队头阻塞）：
  TCP连接：[Stream1] [Stream3] [Stream5]
  Stream1丢包 → TCP等待重传 → Stream3和Stream5也被阻塞
  问题：TCP不知道Stream的概念，一个丢包阻塞所有

HTTP/3（QUIC解决队头阻塞）：
  QUIC连接：[Stream1] [Stream3] [Stream5]
  Stream1丢包 → 只重传Stream1 → Stream3和Stream5继续传输
  优势：Stream间独立，丢包只影响自己
```

---

## 5. 版本对比

| 特性 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|------|----------|--------|--------|
| 传输层 | TCP | TCP | QUIC(UDP) |
| 格式 | 文本 | 二进制 | 二进制 |
| 多路复用 | ❌ | ✅ | ✅ |
| 队头阻塞 | HTTP层 | TCP层 | ❌已解决 |
| 头部压缩 | ❌ | HPACK | QPACK |
| 服务端推送 | ❌ | ✅ | ✅ |
| 连接建立 | 1-RTT | 1-RTT+TLS | 0-RTT |
| 连接迁移 | ❌ | ❌ | ✅ |
| 加密 | 可选 | 强制TLS | 内置TLS 1.3 |
| 浏览器支持 | 100% | 98% | 95%+ |

```
选型建议：
  通用Web应用 → HTTP/2（成熟稳定，Nginx一键开启）
  弱网/移动端 → HTTP/3（连接迁移优势明显）
  内部API → HTTP/1.1够用（连接少、请求少）
  高并发静态资源 → HTTP/2（多路复用优势大）
```

---

## 6. 面试题速查

**Q1: HTTP/2相比HTTP/1.1有哪些改进？**
```
1. 二进制分帧：更高效解析
2. 多路复用：一个连接并行多个请求
3. 头部压缩：HPACK减少重复头部
4. 服务端推送：主动推送资源
5. 基于TLS：强制加密
```

**Q2: HTTP/2的队头阻塞问题？**
```
HTTP/2解决了HTTP层队头阻塞（多路复用）
但TCP层仍有队头阻塞：一个TCP包丢失，后续所有Stream等待重传
HTTP/3用QUIC(UDP)解决了这个问题
```

**Q3: HTTP/3为什么用UDP？**
```
TCP是可靠传输但队头阻塞：一个丢包阻塞整个连接
QUIC基于UDP自己实现可靠性，且Stream间独立：
  一个Stream丢包只影响自己，不阻塞其他Stream
  代价：UDP在部分网络可能被防火墙拦截
```

**Q4: HPACK头部压缩原理？**
```
1. 静态表：61个常见头部字段预定义
2. 动态表：连接内首次发送后存入表，后续用索引引用
3. Huffman编码：压缩字符串值
效果：重复头部从几百字节→几个字节
```

---

*最后更新：2026-07-13*

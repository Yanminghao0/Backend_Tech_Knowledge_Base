# HTTP协议与网络编程

> 深入理解HTTP协议、HTTPS、HTTP/2、WebSocket

---

## 📋 目录

1. [HTTP协议基础](#1-http协议基础)
2. [HTTPS加密原理](#2-https加密原理)
3. [HTTP/2新特性](#3-http2新特性)
4. [WebSocket协议](#4-websocket协议)
5. [网络编程最佳实践](#5-网络编程最佳实践)
6. [常见问题与解决方案](#6-常见问题与解决方案)

---

## 1. HTTP协议基础

### 1.1 HTTP请求格式

```
HTTP请求结构：
┌────────────────────────────────────┐
│ 请求行（Request Line）              │
│ GET /api/users HTTP/1.1            │
├────────────────────────────────────┤
│ 请求头（Request Headers）          │
│ Host: www.example.com              │
│ User-Agent: Chrome/100.0           │
│ Accept: application/json           │
│ Content-Type: application/json     │
│ Content-Length: 27                 │
├────────────────────────────────────┤
│ 空行                                │
├────────────────────────────────────┤
│ 请求体（Request Body）              │
│ {"name":"John","age":30}           │
└────────────────────────────────────┘
```

### 1.2 HTTP响应格式

```
HTTP响应结构：
┌────────────────────────────────────┐
│ 状态行（Status Line）               │
│ HTTP/1.1 200 OK                    │
├────────────────────────────────────┤
│ 响应头（Response Headers）         │
│ Content-Type: application/json     │
│ Content-Length: 45                 │
│ Cache-Control: max-age=3600        │
├────────────────────────────────────┤
│ 空行                                │
├────────────────────────────────────┤
│ 响应体（Response Body）             │
│ {"id":1,"name":"John","age":30}   │
└────────────────────────────────────┘
```

### 1.3 HTTP状态码

```
1xx：信息响应
100 Continue：继续请求
101 Switching Protocols：切换协议（WebSocket）

2xx：成功
200 OK：成功
201 Created：资源创建成功
204 No Content：无内容
206 Partial Content：部分内容（断点续传）

3xx：重定向
301 Moved Permanently：永久重定向
302 Found：临时重定向
304 Not Modified：未修改（缓存有效）

4xx：客户端错误
400 Bad Request：请求错误
401 Unauthorized：未授权
403 Forbidden：禁止访问
404 Not Found：资源不存在
405 Method Not Allowed：方法不允许
429 Too Many Requests：请求过多（限流）

5xx：服务器错误
500 Internal Server Error：服务器内部错误
502 Bad Gateway：网关错误
503 Service Unavailable：服务不可用
504 Gateway Timeout：网关超时
```

### 1.4 HTTP方法

```
GET：获取资源（幂等、安全）
POST：创建资源
PUT：更新资源（幂等）
PATCH：部分更新资源
DELETE：删除资源（幂等）
HEAD：获取资源元信息
OPTIONS：获取支持的方法
TRACE：回显请求
CONNECT：建立隧道（HTTPS代理）

幂等性：
✅ GET、PUT、DELETE、HEAD、OPTIONS：多次调用结果相同
❌ POST、PATCH：多次调用可能产生不同结果

安全性：
✅ GET、HEAD、OPTIONS：只读操作
❌ POST、PUT、PATCH、DELETE：修改数据
```

### 1.5 HTTP头部详解

```java
/**
 * 常用HTTP头部
 */
public class HttpHeaders {
    
    // 通用头部
    public void commonHeaders() {
        // Cache-Control：缓存控制
        "Cache-Control: no-cache, no-store, must-revalidate";
        "Cache-Control: public, max-age=3600";
        
        // Connection：连接管理
        "Connection: keep-alive";  // 持久连接
        "Connection: close";       // 关闭连接
        
        // Date：消息发送时间
        "Date: Wed, 27 Oct 2025 10:00:00 GMT";
    }
    
    // 请求头部
    public void requestHeaders() {
        // Host：目标主机（必需）
        "Host: www.example.com";
        
        // User-Agent：客户端信息
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/100.0";
        
        // Accept：接受的内容类型
        "Accept: application/json, text/plain, */*";
        "Accept-Encoding: gzip, deflate, br";  // 接受的编码
        "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8";  // 接受的语言
        
        // Authorization：认证信息
        "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
        
        // Cookie：Cookie信息
        "Cookie: session_id=abc123; user_id=456";
        
        // Referer：来源页面
        "Referer: https://www.google.com";
        
        // If-None-Match：条件请求（ETag）
        "If-None-Match: \"33a64df551425fcc55e4d42a148795d9f25f89d4\"";
        
        // If-Modified-Since：条件请求（时间）
        "If-Modified-Since: Wed, 21 Oct 2025 07:28:00 GMT";
    }
    
    // 响应头部
    public void responseHeaders() {
        // Content-Type：内容类型
        "Content-Type: application/json; charset=utf-8";
        
        // Content-Length：内容长度
        "Content-Length: 348";
        
        // Content-Encoding：内容编码
        "Content-Encoding: gzip";
        
        // Set-Cookie：设置Cookie
        "Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Strict";
        
        // Location：重定向地址
        "Location: https://www.example.com/new-url";
        
        // ETag：资源标识
        "ETag: \"33a64df551425fcc55e4d42a148795d9f25f89d4\"";
        
        // Last-Modified：最后修改时间
        "Last-Modified: Wed, 21 Oct 2025 07:28:00 GMT";
        
        // Access-Control-Allow-Origin：CORS
        "Access-Control-Allow-Origin: *";
        "Access-Control-Allow-Methods: GET, POST, PUT, DELETE";
        "Access-Control-Allow-Headers: Content-Type, Authorization";
    }
}
```

---

## 2. HTTPS加密原理

### 2.1 对称加密 vs 非对称加密

```
对称加密（AES、DES）：
┌────────┐    密钥K    ┌────────┐    密钥K    ┌────────┐
│ 明文   │ ─────────> │ 密文   │ ─────────> │ 明文   │
└────────┘   加密      └────────┘   解密      └────────┘

优点：速度快
缺点：密钥传输不安全

非对称加密（RSA）：
┌────────┐   公钥     ┌────────┐   私钥     ┌────────┐
│ 明文   │ ─────────> │ 密文   │ ─────────> │ 明文   │
└────────┘   加密      └────────┘   解密      └────────┘

优点：安全
缺点：速度慢

HTTPS = 非对称加密（交换密钥） + 对称加密（传输数据）
```

### 2.2 HTTPS握手流程

```mermaid
sequenceDiagram
    participant Client
    participant Server
    
    Client->>Server: 1. ClientHello<br/>(支持的加密算法、随机数C)
    Server->>Client: 2. ServerHello<br/>(选择的加密算法、随机数S)
    Server->>Client: 3. Certificate<br/>(服务器证书)
    Server->>Client: 4. ServerHelloDone
    Client->>Client: 5. 验证证书
    Client->>Server: 6. ClientKeyExchange<br/>(预主密钥，用服务器公钥加密)
    Client->>Server: 7. ChangeCipherSpec<br/>(切换到加密通信)
    Client->>Server: 8. Finished<br/>(握手消息摘要)
    Server->>Client: 9. ChangeCipherSpec
    Server->>Client: 10. Finished
    Client->>Server: 11. Application Data<br/>(加密的应用数据)
```

**详细步骤**：
```
1. Client Hello：
   - 客户端支持的TLS版本
   - 支持的加密套件列表
   - 客户端随机数（Client Random）

2. Server Hello：
   - 选择的TLS版本
   - 选择的加密套件
   - 服务器随机数（Server Random）

3. Certificate：
   - 服务器的数字证书（包含公钥）

4. Server Key Exchange（可选）：
   - DH参数等

5. Client Key Exchange：
   - 客户端生成预主密钥（Pre-Master Secret）
   - 用服务器公钥加密后发送

6. 计算主密钥：
   Master Secret = PRF(Pre-Master Secret, "master secret", 
                       Client Random + Server Random)

7. 生成会话密钥：
   - 客户端加密密钥
   - 服务器加密密钥
   - 客户端MAC密钥
   - 服务器MAC密钥

8. Change Cipher Spec：
   - 通知对方后续使用协商的密钥加密

9. Finished：
   - 用会话密钥加密的握手消息摘要
   - 验证握手过程的完整性

10. Application Data：
   - 使用会话密钥加密传输数据
```

### 2.3 数字证书验证

```
数字证书链：
根证书CA（操作系统内置）
    └── 中间证书CA
            └── 服务器证书

证书内容：
- 域名
- 公钥
- 有效期
- 颁发机构
- 数字签名

验证流程：
1. 检查证书有效期
2. 检查域名是否匹配
3. 检查证书是否被吊销（OCSP）
4. 验证证书签名
5. 验证证书链
```

---

## 3. HTTP/2新特性

### 3.1 HTTP/1.1 vs HTTP/2

```
┌─────────────────┬──────────────┬──────────────┐
│ 特性            │ HTTP/1.1     │ HTTP/2       │
├─────────────────┼──────────────┼──────────────┤
│ 传输方式        │ 文本         │ 二进制帧     │
│ 多路复用        │ ❌           │ ✅           │
│ 头部压缩        │ ❌           │ ✅ (HPACK)   │
│ 服务器推送      │ ❌           │ ✅           │
│ 优先级          │ ❌           │ ✅           │
│ 连接数          │ 6个/域名     │ 1个/域名     │
└─────────────────┴──────────────┴──────────────┘
```

### 3.2 二进制分帧

```
HTTP/2帧结构：
┌────────────────────────────────────┐
│ Length (24bit)                     │  帧长度
├────────────────────────────────────┤
│ Type (8bit)                        │  帧类型
├────────────────────────────────────┤
│ Flags (8bit)                       │  标志位
├────────────────────────────────────┤
│ R (1bit) │ Stream ID (31bit)       │  流ID
├────────────────────────────────────┤
│ Frame Payload                      │  帧载荷
└────────────────────────────────────┘

帧类型：
- DATA：传输数据
- HEADERS：传输头部
- PRIORITY：优先级
- RST_STREAM：重置流
- SETTINGS：设置参数
- PUSH_PROMISE：服务器推送
- PING：心跳
- GOAWAY：关闭连接
- WINDOW_UPDATE：流量控制
```

### 3.3 多路复用

```
HTTP/1.1：
连接1: ────Request1────Response1────Request2────Response2────
连接2: ────Request3────Response3────Request4────Response4────
连接3: ────Request5────Response5────Request6────Response6────

问题：
- 队头阻塞（Head-of-Line Blocking）
- 多个连接，资源消耗大

HTTP/2：
连接1: ──Request1──Request2──Request3──Request4──Request5──
       ─Response1─Response2─Response3─Response4─Response5─

优点：
✅ 单连接多路复用
✅ 消除队头阻塞
✅ 降低延迟
✅ 减少连接数
```

### 3.4 头部压缩（HPACK）

```
HTTP/1.1：
GET /api/users HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0 ...
Accept: application/json
Cookie: session=abc123; user=456
Authorization: Bearer eyJhbGciOiJI...

第二个请求重复发送相同头部 → 浪费带宽

HTTP/2（HPACK）：
索引表：
1: :method GET
2: :path /api/users
3: :scheme https
4: host example.com
5: user-agent Mozilla/5.0 ...

第一个请求：发送完整头部 + 建立索引
第二个请求：只发送索引编号

压缩效果：减少80%的头部大小
```

### 3.5 服务器推送

```
传统方式：
Client -> Server: GET /index.html
Server -> Client: index.html (包含<link href="style.css">)
Client -> Server: GET /style.css
Server -> Client: style.css

HTTP/2 Server Push：
Client -> Server: GET /index.html
Server -> Client: PUSH_PROMISE /style.css
Server -> Client: index.html
Server -> Client: style.css (主动推送)

优点：
✅ 减少往返次数
✅ 降低延迟

配置示例（Nginx）：
location / {
    http2_push /style.css;
    http2_push /script.js;
}
```

---

## 4. WebSocket协议

### 4.1 WebSocket vs HTTP

```
HTTP：
- 单向通信（客户端请求 → 服务器响应）
- 无状态
- 请求-响应模型
- 适合：API调用、页面加载

WebSocket：
- 双向通信（全双工）
- 有状态（持久连接）
- 长连接
- 适合：实时通信、聊天、推送
```

### 4.2 WebSocket握手

```
客户端请求（升级协议）：
GET /chat HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

服务器响应：
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

握手成功后，连接升级为WebSocket协议
```

### 4.3 WebSocket帧格式

```
WebSocket帧结构：
┌────────────────────────────────────┐
│ FIN(1) RSV(3) Opcode(4)            │
├────────────────────────────────────┤
│ Mask(1) Payload Length(7)          │
├────────────────────────────────────┤
│ Extended Payload Length(16/64)     │  可选
├────────────────────────────────────┤
│ Masking Key(32)                    │  如果Mask=1
├────────────────────────────────────┤
│ Payload Data                       │
└────────────────────────────────────┘

Opcode：
0x0：继续帧
0x1：文本帧
0x2：二进制帧
0x8：关闭连接
0x9：Ping
0xA：Pong
```

### 4.4 WebSocket使用示例

**JavaScript客户端**：
```javascript
// 创建WebSocket连接
const ws = new WebSocket('ws://example.com/chat');

// 连接打开
ws.onopen = () => {
    console.log('Connected');
    ws.send('Hello Server!');
};

// 接收消息
ws.onmessage = (event) => {
    console.log('Received:', event.data);
};

// 连接关闭
ws.onclose = () => {
    console.log('Disconnected');
};

// 错误处理
ws.onerror = (error) => {
    console.error('Error:', error);
};

// 发送消息
ws.send('Hello');
ws.send(JSON.stringify({type: 'message', content: 'Hello'}));

// 关闭连接
ws.close();
```

**Java服务端（Spring Boot）**：
```java
/**
 * WebSocket服务端
 */
@ServerEndpoint("/chat")
@Component
public class ChatWebSocket {
    
    private static final Set<Session> sessions = 
        Collections.synchronizedSet(new HashSet<>());
    
    @OnOpen
    public void onOpen(Session session) {
        sessions.add(session);
        System.out.println("新连接: " + session.getId());
    }
    
    @OnMessage
    public void onMessage(String message, Session session) {
        System.out.println("收到消息: " + message);
        // 广播给所有客户端
        broadcast(message);
    }
    
    @OnClose
    public void onClose(Session session) {
        sessions.remove(session);
        System.out.println("连接关闭: " + session.getId());
    }
    
    @OnError
    public void onError(Session session, Throwable error) {
        System.err.println("错误: " + error.getMessage());
    }
    
    private void broadcast(String message) {
        sessions.forEach(session -> {
            try {
                session.getBasicRemote().sendText(message);
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
    }
}
```

---

## 5. 网络编程最佳实践

### 5.1 连接池管理

```java
/**
 * HTTP连接池配置
 */
@Configuration
public class HttpClientConfig {
    
    @Bean
    public CloseableHttpClient httpClient() {
        // 连接池管理器
        PoolingHttpClientConnectionManager connectionManager = 
            new PoolingHttpClientConnectionManager();
        
        // 最大连接数
        connectionManager.setMaxTotal(200);
        
        // 每个路由最大连接数
        connectionManager.setDefaultMaxPerRoute(20);
        
        // 连接超时
        RequestConfig requestConfig = RequestConfig.custom()
            .setConnectTimeout(5000)           // 连接超时5秒
            .setSocketTimeout(10000)           // 读超时10秒
            .setConnectionRequestTimeout(3000) // 从连接池获取连接超时3秒
            .build();
        
        return HttpClients.custom()
            .setConnectionManager(connectionManager)
            .setDefaultRequestConfig(requestConfig)
            .setRetryHandler(new DefaultHttpRequestRetryHandler(3, true))
            .build();
    }
}
```

### 5.2 超时设置

```java
/**
 * 多层超时设置
 */
public class TimeoutConfiguration {
    
    // 1. 连接超时
    // - 建立TCP连接的时间
    // - 推荐：3-5秒
    
    // 2. 读超时（Socket超时）
    // - 读取响应数据的时间
    // - 推荐：10-30秒
    
    // 3. 写超时
    // - 发送请求数据的时间
    // - 推荐：10秒
    
    // 4. 请求超时
    // - 整个请求的时间（连接+读+写）
    // - 推荐：30-60秒
    
    public void setTimeouts(OkHttpClient.Builder builder) {
        builder
            .connectTimeout(5, TimeUnit.SECONDS)   // 连接超时
            .readTimeout(30, TimeUnit.SECONDS)     // 读超时
            .writeTimeout(10, TimeUnit.SECONDS)    // 写超时
            .callTimeout(60, TimeUnit.SECONDS);    // 整体超时
    }
}
```

### 5.3 重试策略

```java
/**
 * 重试策略
 */
public class RetryStrategy {
    
    // 1. 固定重试间隔
    public void fixedRetry() {
        int maxRetries = 3;
        int retryDelay = 1000;  // 1秒
        
        for (int i = 0; i < maxRetries; i++) {
            try {
                // 执行请求
                return;
            } catch (Exception e) {
                if (i == maxRetries - 1) {
                    throw e;
                }
                Thread.sleep(retryDelay);
            }
        }
    }
    
    // 2. 指数退避（推荐）⭐
    public void exponentialBackoff() {
        int maxRetries = 5;
        int baseDelay = 1000;  // 1秒
        
        for (int i = 0; i < maxRetries; i++) {
            try {
                // 执行请求
                return;
            } catch (Exception e) {
                if (i == maxRetries - 1) {
                    throw e;
                }
                int delay = baseDelay * (int) Math.pow(2, i);  // 1s, 2s, 4s, 8s, 16s
                Thread.sleep(delay);
            }
        }
    }
    
    // 3. Spring Retry
    @Retryable(
        value = {IOException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2)
    )
    public String callWithRetry() throws IOException {
        // 自动重试
        return httpClient.get("https://example.com");
    }
}
```

### 5.4 缓存策略

```java
/**
 * HTTP缓存策略
 */
public class CacheStrategy {
    
    // 1. 强缓存（Cache-Control）
    public void strongCache() {
        // 服务端响应头
        response.setHeader("Cache-Control", "max-age=3600");  // 缓存1小时
        response.setHeader("Cache-Control", "no-cache");      // 协商缓存
        response.setHeader("Cache-Control", "no-store");      // 不缓存
    }
    
    // 2. 协商缓存（ETag/Last-Modified）
    public void negotiatedCache(HttpServletRequest request, 
                               HttpServletResponse response) {
        String resourceETag = calculateETag();
        String clientETag = request.getHeader("If-None-Match");
        
        if (resourceETag.equals(clientETag)) {
            // 资源未修改，返回304
            response.setStatus(HttpServletResponse.SC_NOT_MODIFIED);
            return;
        }
        
        // 资源已修改，返回新数据
        response.setHeader("ETag", resourceETag);
        response.setStatus(HttpServletResponse.SC_OK);
        // 返回数据...
    }
    
    // 3. 本地缓存（Caffeine）
    private final Cache<String, String> cache = Caffeine.newBuilder()
        .maximumSize(10000)
        .expireAfterWrite(1, TimeUnit.HOURS)
        .build();
    
    public String getWithCache(String url) {
        return cache.get(url, key -> httpClient.get(key));
    }
}
```

---

## 6. 常见问题与解决方案

### 6.1 跨域问题（CORS）

**问题现象**：
```
Access to XMLHttpRequest at 'https://api.example.com' from origin 
'https://www.example.com' has been blocked by CORS policy
```

**解决方案**：
```java
/**
 * CORS配置
 */
@Configuration
public class CorsConfig {
    
    // 方法1：全局CORS配置
    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                    .allowedOrigins("https://www.example.com")
                    .allowedMethods("GET", "POST", "PUT", "DELETE")
                    .allowedHeaders("*")
                    .allowCredentials(true)
                    .maxAge(3600);
            }
        };
    }
    
    // 方法2：控制器级别
    @CrossOrigin(origins = "https://www.example.com")
    @RestController
    public class ApiController {
        // ...
    }
    
    // 方法3：过滤器
    @Component
    @Order(Ordered.HIGHEST_PRECEDENCE)
    public class CorsFilter implements Filter {
        
        @Override
        public void doFilter(ServletRequest req, ServletResponse res, 
                           FilterChain chain) throws IOException, ServletException {
            HttpServletResponse response = (HttpServletResponse) res;
            HttpServletRequest request = (HttpServletRequest) req;
            
            response.setHeader("Access-Control-Allow-Origin", "*");
            response.setHeader("Access-Control-Allow-Methods", 
                "GET, POST, PUT, DELETE, OPTIONS");
            response.setHeader("Access-Control-Allow-Headers", 
                "Content-Type, Authorization");
            response.setHeader("Access-Control-Max-Age", "3600");
            
            if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
                response.setStatus(HttpServletResponse.SC_OK);
            } else {
                chain.doFilter(req, res);
            }
        }
    }
}
```

### 6.2 请求限流

```java
/**
 * 接口限流
 */
@RestController
public class RateLimitController {
    
    // 1. Guava RateLimiter
    private final RateLimiter rateLimiter = RateLimiter.create(10.0);  // 每秒10个请求
    
    @GetMapping("/api/data")
    public ResponseEntity<?> getData() {
        if (!rateLimiter.tryAcquire()) {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body("Too many requests");
        }
        // 处理请求
        return ResponseEntity.ok(data);
    }
    
    // 2. Bucket4j（令牌桶）
    private final Bucket bucket = Bucket4j.builder()
        .addLimit(Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1))))
        .build();
    
    @GetMapping("/api/data2")
    public ResponseEntity<?> getData2() {
        if (bucket.tryConsume(1)) {
            return ResponseEntity.ok(data);
        } else {
            return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
                .body("Rate limit exceeded");
        }
    }
    
    // 3. Redis + Lua脚本（分布式限流）
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    public boolean isAllowed(String key, int maxRequests, int windowSeconds) {
        String luaScript = 
            "local key = KEYS[1]\n" +
            "local limit = tonumber(ARGV[1])\n" +
            "local window = tonumber(ARGV[2])\n" +
            "local current = redis.call('INCR', key)\n" +
            "if current == 1 then\n" +
            "    redis.call('EXPIRE', key, window)\n" +
            "end\n" +
            "return current <= limit";
        
        DefaultRedisScript<Boolean> script = new DefaultRedisScript<>();
        script.setScriptText(luaScript);
        script.setResultType(Boolean.class);
        
        return redisTemplate.execute(script, 
            Collections.singletonList(key), 
            String.valueOf(maxRequests), 
            String.valueOf(windowSeconds));
    }
}
```

### 6.3 长连接优化

```java
/**
 * Keep-Alive优化
 */
public class KeepAliveOptimization {
    
    // 1. HTTP/1.1 Keep-Alive配置
    public void configureKeepAlive() {
        // 响应头
        response.setHeader("Connection", "keep-alive");
        response.setHeader("Keep-Alive", "timeout=60, max=100");
        // timeout：连接保持时间（秒）
        // max：最大请求数
    }
    
    // 2. Tomcat Keep-Alive配置
    // server.xml
    /*
    <Connector port="8080" 
               protocol="HTTP/1.1"
               connectionTimeout="20000"
               maxKeepAliveRequests="100"
               keepAliveTimeout="60000"
               maxConnections="10000" />
    */
    
    // 3. Nginx Keep-Alive配置
    // nginx.conf
    /*
    http {
        keepalive_timeout 60s;
        keepalive_requests 100;
        
        upstream backend {
            server 127.0.0.1:8080;
            keepalive 32;  # 连接池大小
        }
    }
    */
}
```

### 6.4 大文件传输

```java
/**
 * 大文件上传下载
 */
@RestController
public class FileTransferController {
    
    // 1. 分块上传
    @PostMapping("/upload/chunk")
    public ResponseEntity<?> uploadChunk(
        @RequestParam("file") MultipartFile file,
        @RequestParam("chunkNumber") int chunkNumber,
        @RequestParam("totalChunks") int totalChunks,
        @RequestParam("identifier") String identifier) {
        
        // 保存分块
        String chunkPath = "/tmp/" + identifier + "_" + chunkNumber;
        file.transferTo(new File(chunkPath));
        
        // 如果是最后一块，合并文件
        if (chunkNumber == totalChunks - 1) {
            mergeChunks(identifier, totalChunks);
        }
        
        return ResponseEntity.ok("Chunk uploaded");
    }
    
    // 2. 断点续传
    @GetMapping("/download")
    public ResponseEntity<StreamingResponseBody> download(
        @RequestHeader(value = "Range", required = false) String range) {
        
        File file = new File("/path/to/file");
        long fileSize = file.length();
        long start = 0;
        long end = fileSize - 1;
        
        // 解析Range头
        if (range != null && range.startsWith("bytes=")) {
            String[] ranges = range.substring(6).split("-");
            start = Long.parseLong(ranges[0]);
            if (ranges.length > 1) {
                end = Long.parseLong(ranges[1]);
            }
        }
        
        final long finalStart = start;
        final long finalEnd = end;
        long contentLength = end - start + 1;
        
        StreamingResponseBody body = outputStream -> {
            try (RandomAccessFile raf = new RandomAccessFile(file, "r")) {
                raf.seek(finalStart);
                byte[] buffer = new byte[4096];
                long remaining = contentLength;
                
                while (remaining > 0) {
                    int read = raf.read(buffer, 0, 
                        (int) Math.min(buffer.length, remaining));
                    if (read == -1) break;
                    outputStream.write(buffer, 0, read);
                    remaining -= read;
                }
            }
        };
        
        return ResponseEntity.status(HttpStatus.PARTIAL_CONTENT)
            .header("Content-Range", "bytes " + start + "-" + end + "/" + fileSize)
            .header("Accept-Ranges", "bytes")
            .contentLength(contentLength)
            .body(body);
    }
    
    // 3. 流式传输
    @GetMapping(value = "/stream", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    public StreamingResponseBody streamFile() {
        return outputStream -> {
            try (InputStream inputStream = new FileInputStream("/path/to/file")) {
                byte[] buffer = new byte[4096];
                int bytesRead;
                while ((bytesRead = inputStream.read(buffer)) != -1) {
                    outputStream.write(buffer, 0, bytesRead);
                }
            }
        };
    }
}
```

---

## 📚 参考资料

- 📖 《HTTP权威指南》
- 📖 《图解HTTP》
- 🔗 [HTTP/2 RFC 7540](https://tools.ietf.org/html/rfc7540)
- 🔗 [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)

---

*最后更新：2025-10-27*

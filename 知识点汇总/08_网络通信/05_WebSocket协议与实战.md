# WebSocket协议与实战

> 全双工实时通信，从协议原理到Spring Boot实现

---

## 📋 目录

1. [WebSocket概述](#1-websocket概述)
2. [协议原理](#2-协议原理)
3. [Spring Boot实现](#3-spring-boot实现)
4. [心跳与重连](#4-心跳与重连)
5. [面试要点](#5-面试要点)

---

## 1. WebSocket概述

### HTTP vs WebSocket

| 维度 | HTTP | WebSocket |
|------|------|-----------|
| 通信方式 | 请求-响应（单向） | 全双工（双向） |
| 连接 | 短连接（HTTP/1.1可Keep-Alive） | 长连接 |
| 实时性 | 轮询，延迟高 | 服务端推送，实时 |
| 开销 | 每次带HTTP头 | 握手后帧头仅2-10字节 |
| 适用 | 普通API | 实时聊天/推送/协同 |

### WebSocket应用场景

```
- 即时通讯：聊天室、客服系统
- 实时推送：股票行情、赛事直播
- 协同编辑：文档协作、白板
- 在线游戏：多人实时交互
- IoT监控：设备状态实时上报
```

---

## 2. 协议原理

### 握手过程

```
1. 客户端发起HTTP升级请求
   GET /ws HTTP/1.1
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13

2. 服务端返回101 Switching Protocols
   HTTP/1.1 101 Switching Protocols
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

3. 握手完成后，TCP连接升级为WebSocket连接
   后续通信用WebSocket帧格式
```

### 帧格式

```
WebSocket帧结构：
  FIN(1位) | RSV(3位) | Opcode(4位) | MASK(1位) | Payload Length(7/16/64位)
  Mask Key(32位，仅客户端发送时) | Payload Data

Opcode类型：
  0x0: Continuation（续帧）
  0x1: Text（文本帧）
  0x2: Binary（二进制帧）
  0x8: Close（关闭帧）
  0x9: Ping（心跳）
  0xA: Pong（心跳响应）
```

---

## 3. Spring Boot实现

### 服务端实现

```java
@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {
    
    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(new ChatHandler(), "/ws/chat")
                .setAllowedOrigins("*");
    }
}

@Component
public class ChatHandler extends TextWebSocketHandler {
    
    private final ConcurrentHashMap<String, WebSocketSession> sessions = new ConcurrentHashMap<>();
    
    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String userId = session.getAttributes().get("userId").toString();
        sessions.put(userId, session);
        broadcast("用户 " + userId + " 上线");
    }
    
    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String userId = session.getAttributes().get("userId").toString();
        // 广播消息
        broadcast(userId + ": " + message.getPayload());
    }
    
    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        String userId = session.getAttributes().get("userId").toString();
        sessions.remove(userId);
        broadcast("用户 " + userId + " 下线");
    }
    
    private void broadcast(String message) {
        sessions.values().forEach(session -> {
            try {
                session.sendMessage(new TextMessage(message));
            } catch (IOException e) {
                log.error("发送失败", e);
            }
        });
    }
}
```

### STOMP协议（推荐）

```java
// STOMP：WebSocket之上的消息协议，更规范
@Configuration
@EnableWebSocketMessageBroker
public class StompConfig implements WebSocketMessageBrokerConfigurer {
    
    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws").setAllowedOrigins("*");
    }
    
    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic", "/queue");
        registry.setApplicationDestinationPrefixes("/app");
    }
}

@Controller
public class ChatController {
    
    @MessageMapping("/chat.send")        // 客户端发送到 /app/chat.send
    @SendTo("/topic/messages")            // 广播到 /topic/messages
    public ChatMessage send(ChatMessage message) {
        message.setTime(System.currentTimeMillis());
        return message;
    }
    
    @MessageMapping("/chat.private")      // 私聊
    @SendToUser("/queue/private")         // 发送到当前用户 /user/queue/private
    public ChatMessage privateChat(ChatMessage message, Principal principal) {
        return message;
    }
}
```

### 前端连接

```javascript
// STOMP.js + SockJS
const socket = new SockJS('http://localhost:8080/ws');
const stompClient = Stomp.over(socket);

stompClient.connect({}, function(frame) {
    // 订阅公共频道
    stompClient.subscribe('/topic/messages', function(message) {
        const msg = JSON.parse(message.body);
        console.log(msg.content);
    });
    
    // 订阅私信
    stompClient.subscribe('/user/queue/private', function(message) {
        console.log('私信:', JSON.parse(message.body));
    });
});

// 发送消息
stompClient.send('/app/chat.send', {}, JSON.stringify({
    content: 'Hello World',
    sender: 'Alice'
}));
```

---

## 4. 心跳与重连

### 心跳机制

```java
// 服务端心跳配置
@Override
public void registerStompEndpoints(StompEndpointRegistry registry) {
    registry.addEndpoint("/ws")
        .setAllowedOrigins("*")
        .withSockJS()
        .setHeartbeatTime(25000);  // 25秒发一次心跳
}

// 自定义心跳处理
public class HeartbeatHandler extends ChannelInboundHandlerAdapter {
    @Override
    public void channelIdle(ChannelHandlerContext ctx, IdleStateEvent evt) {
        if (evt == IdleStateEvent.READER_IDLE_STATE_EVENT) {
            // 30秒未收到客户端消息，关闭连接
            ctx.close();
        }
    }
}
```

### 前端重连

```javascript
class ReconnectingWebSocket {
    constructor(url) {
        this.url = url;
        this.reconnectInterval = 3000;
        this.maxReconnectAttempts = 10;
        this.attempts = 0;
        this.connect();
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            this.attempts = 0;
            console.log('WebSocket已连接');
        };
        
        this.ws.onclose = () => {
            if (this.attempts < this.maxReconnectAttempts) {
                this.attempts++;
                console.log(`${this.reconnectInterval}ms后重连(${this.attempts}/${this.maxReconnectAttempts})`);
                setTimeout(() => this.connect(), this.reconnectInterval);
            }
        };
        
        this.ws.onmessage = (event) => {
            console.log('收到:', event.data);
        };
    }
}
```

---

## 5. 面试要点

### Q1: WebSocket和HTTP轮询的区别？

```
HTTP轮询：
  - 客户端定时发请求 → 服务端响应
  - 延迟 = 轮询间隔
  - 大量无效请求，浪费带宽

WebSocket：
  - 握手后保持长连接
  - 服务端可主动推送
  - 帧头仅2-10字节，开销小
  - 实时延迟 < 100ms
```

### Q2: WebSocket握手过程？

```
1. 客户端发HTTP GET请求，带Upgrade: websocket头
2. 服务端返回101 Switching Protocols
3. TCP连接升级为WebSocket
4. 后续用WebSocket帧格式通信
```

### Q3: WebSocket如何处理断线重连？

```
1. 客户端检测连接关闭（onclose事件）
2. 指数退避重连：3s → 6s → 12s → 24s
3. 设置最大重连次数
4. 重连成功后重新订阅
5. 心跳检测：定时发Ping，未收到Pong则判定断线
```

---

## 📚 相关阅读

- [01_HTTP协议与网络编程](./01_HTTP协议与网络编程.md)
- [02_Netty核心原理详解](./02_Netty核心原理详解.md)
- [设计IM系统](../21_系统设计与面试/经典系统设计案例/03_设计IM系统.md)

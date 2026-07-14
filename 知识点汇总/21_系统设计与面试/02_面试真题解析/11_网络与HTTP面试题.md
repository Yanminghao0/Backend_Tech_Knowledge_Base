# 网络与HTTP面试题

> TCP/HTTP/HTTPS高频面试真题：握手/状态码/跨域/输入URL全过程

---

## 📋 目录

1. [TCP三次握手与四次挥手](#1-tcp三次握手与四次挥手)
2. [TCP vs UDP](#2-tcp-vs-udp)
3. [HTTP版本演进](#3-http版本演进)
4. [HTTPS原理](#4-https原理)
5. [HTTP状态码](#5-http状态码)
6. [Cookie/Session/Token](#6-cookiesessiontoken)
7. [跨域问题](#7-跨域问题)
8. [输入URL到页面渲染](#8-输入url到页面渲染)
9. [面试题速查](#9-面试题速查)

---

## 1. TCP三次握手与四次挥手

**Q: 三次握手过程？为什么是三次不是两次？**

```
客户端                    服务端
  |--- SYN(seq=x) --------->|    第1次: 客户端发SYN，进入SYN_SENT
  |<-- SYN+ACK(seq=y,ack=x+1) -|  第2次: 服务端回SYN+ACK，进入SYN_RCVD
  |--- ACK(ack=y+1 -------->|    第3次: 客户端回ACK，双方ESTABLISHED

为什么三次:
  两次无法确认客户端的接收能力 → 服务端发SYN+ACK后不知道客户端是否收到
  三次确保双方收发能力都正常
  防止历史连接(SYN洪泛): 服务端收到旧SYN直接RST
```

**Q: 四次挥手？TIME_WAIT为什么是2MSL？**

```
客户端                    服务端
  |--- FIN(seq=u) ---------->|     第1次: 主动方发FIN，进入FIN_WAIT_1
  |<-- ACK(ack=u+1) ---------|     第2次: 被动方回ACK，进入CLOSE_WAIT
  |                          |     (被动方处理剩余数据)
  |<-- FIN(seq=v) -----------|     第3次: 被动方发FIN，进入LAST_ACK
  |--- ACK(ack=v+1) -------->|     第4次: 主动方回ACK，进入TIME_WAIT

TIME_WAIT = 2*MSL(最大报文段生存时间，默认60s):
  1. 确保最后一个ACK到达(如果丢了对端会重发FIN)
  2. 确保旧连接的报文消失(防止干扰新连接)
```

---

## 2. TCP vs UDP

**Q: TCP vs UDP？适用场景？**

| 维度 | TCP | UDP |
|------|-----|-----|
| 连接 | 面向连接 | 无连接 |
| 可靠性 | 可靠(重传/排序/确认) | 不可靠 |
| 有序性 | 有序 | 无序 |
| 速度 | 慢(握手/确认开销) | 快 |
| 头部 | 20字节 | 8字节 |
| 场景 | HTTP/SSH/邮件 | DNS/视频/游戏/QUIC |

---

## 3. HTTP版本演进

**Q: HTTP/1.0 → 1.1 → 2.0 → 3.0核心改进？**

| 版本 | 年份 | 核心改进 | 问题 |
|------|------|---------|------|
| 1.0 | 1996 | 每次请求新建TCP连接 | 连接开销大 |
| 1.1 | 1997 | Keep-Alive长连接/管道化/Host头 | 队头阻塞 |
| 2.0 | 2015 | 多路复用/Header压缩/服务端推送 | TCP层队头阻塞 |
| 3.0 | 2022 | QUIC(UDP)解决TCP队头阻塞/0-RTT | 部署中 |

```
HTTP/2多路复用: 一个TCP连接上并行多个请求(二进制分帧)
HTTP/3 QUIC: 基于UDP，每个流独立(不互相阻塞)，0-RTT建连
```

---

## 4. HTTPS原理

**Q: HTTPS握手过程？**

```
1. ClientHello: 客户端发送支持的TLS版本+加密套件+随机数A
2. ServerHello: 服务端选定套件+随机数B+返回证书
3. 客户端验证证书: 证书链验证(CA签名→根证书) → 证书未过期 → 域名匹配
4. 客户端生成Pre-Master Secret(用服务端公钥加密发送)
5. 双方用 随机数A + 随机数B + Pre-Master → 计算出会话密钥
6. 后续通信用对称加密(AES) + 会话密钥

混合加密: 非对称加密(RSA/ECDHE)交换密钥 + 对称加密(AES)传输数据
```

---

## 5. HTTP状态码

**Q: 常用HTTP状态码？**

```
1xx 信息: 100 Continue
2xx 成功: 200 OK / 201 Created / 204 No Content
3xx 重定向: 301永久重定向 / 302临时重定向 / 304 Not Modified(缓存)
4xx 客户端错误: 400 Bad Request / 401 Unauthorized / 403 Forbidden / 404 Not Found / 429 Too Many Requests
5xx 服务端错误: 500 Internal Error / 502 Bad Gateway / 503 Service Unavailable / 504 Gateway Timeout

面试常问:
  301 vs 302: 永久/临时重定向(浏览器是否缓存/SEO影响)
  401 vs 403: 401未认证(需登录) / 403无权限(登录了但没权限)
  502 vs 504: 502网关收到无效响应(上游挂了) / 504网关超时(上游没响应)
```

---

## 6. Cookie/Session/Token

**Q: Cookie vs Session vs Token(JWT)？**

| 维度 | Cookie | Session | JWT Token |
|------|--------|---------|-----------|
| 存储 | 浏览器 | 服务端 | 客户端(Header) |
| 大小 | 4KB | 无限制 | 无限制 |
| 安全 | 低(可篡改) | 中(服务端控制) | 高(签名防篡改) |
| 扩展 | 不适合分布式 | 需共享Session | 天然分布式 |
| 过期 | 可设置 | 服务端控制 | payload含exp |

```
JWT结构: Header.Payload.Signature (Base64编码)
  Header: {"alg":"HS256","typ":"JWT"}
  Payload: {"userId":123,"exp":1699999999}
  Signature: HMAC-SHA256(base64(Header)+"."+base64(Payload), secret)

JWT缺点: 无法主动失效(签发后到期前一直有效)
  解决: Redis黑名单 / 短期Token+RefreshToken
```

---

## 7. 跨域问题

**Q: 什么是同源策略？什么是CORS？**

```
同源: 协议+域名+端口完全相同
跨域: 浏览器限制JS跨域请求(AJAX/Fetch), 不限制<script>/<img>/<link>

CORS(跨域资源共享):
  简单请求(GET/POST/HEAD + 特定Content-Type):
    浏览器直接发请求，服务端响应头 Access-Control-Allow-Origin: *
    
  预检请求(OPTIONS):
    非简单请求(PUT/DELETE/自定义Header)先发OPTIONS
    服务端返回允许的方法/Header/有效期
    浏览器收到允许后再发真实请求

Spring Boot配置:
  @CrossOrigin(origins="https://example.com")  // 方法级
  或 WebMvcConfigurer.addCorsMappings()         // 全局
```

---

## 8. 输入URL到页面渲染

**Q: 从输入URL到页面展示发生了什么？**

```
1. DNS解析: 域名 → IP(浏览器缓存→hosts→本地DNS→递归查询)
2. TCP连接: 三次握手
3. TLS握手: 如果是HTTPS(见第4节)
4. 发送HTTP请求: 请求行+Header+Body
5. 服务端处理: 路由→Controller→DB→响应
6. 浏览器接收响应: HTML
7. 解析HTML → DOM树
8. 解析CSS → CSSOM树
9. DOM+CSSOM → 渲染树(Render Tree)
10. 布局(Layout): 计算元素位置
11. 绘制(Paint): 像素绘制
12. 合成(Composite): GPU合成图层
13. 执行JS(可能阻塞解析: defer/async)
```

---

## 9. 面试题速查

**Q1: 三次握手为什么不是两次？**
```
两次无法确认客户端接收能力，无法防止历史SYN连接
```

**Q2: TIME_WAIT为什么2MSL？**
```
确保ACK到达(丢了对方重发FIN) + 旧报文消失
```

**Q3: HTTP/2核心改进？**
```
多路复用(一个TCP并行多请求) + Header压缩(HPACK) + 服务端推送
```

**Q4: HTTPS混合加密？**
```
非对称加密交换密钥 + 对称加密传输数据
```

**Q5: 401 vs 403？**
```
401未认证(需登录) / 403无权限(登录了但没权限)
```

**Q6: JWT怎么主动失效？**
```
Redis黑名单 / 短期Token+RefreshToken
```

**Q7: 跨域预检请求？**
```
非简单请求(PUT/DELETE/自定义Header)先发OPTIONS，服务端返回允许的方法
```

**Q8: 输入URL全过程？**
```
DNS→TCP→TLS→HTTP→服务端处理→HTML解析→DOM+CSSOM→渲染树→布局→绘制
```

---

*最后更新: 2026-07-14*

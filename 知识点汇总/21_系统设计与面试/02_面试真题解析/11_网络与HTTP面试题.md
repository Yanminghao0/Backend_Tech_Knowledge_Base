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

## 9. 补充面试题

**Q: CDN原理？**

```
CDN(Content Delivery Network)内容分发网络:
  核心思想: 把内容缓存到离用户最近的边缘节点

流程:
  1. 用户请求 www.example.com
  2. DNS解析: CNAME指向CDN的DNS
  3. CDN的GSLB(全局负载均衡)返回离用户最近的边缘节点IP
  4. 用户请求边缘节点
  5. 边缘节点有缓存 → 直接返回(命中)
  6. 边缘节点无缓存 → 回源站获取 → 缓存后返回(未命中)

缓存策略:
  - TTL过期: 过期后回源
  - 主动刷新: 源站内容更新后通知CDN刷新
  - 热点预热: 提前把热门内容推送到边缘节点
```

**Q: DNS解析过程？**

```
浏览器输入www.example.com的DNS解析:

1. 浏览器DNS缓存 → 没找到
2. OS hosts文件 → 没找到
3. OS DNS缓存 → 没找到
4. 本地DNS服务器(配置的DNS, 如8.8.8.8)
   → 查根DNS(.): 返回.com的TLD DNS
   → 查TLD DNS(.com): 返回example.com的权威DNS
   → 查权威DNS: 返回www.example.com的A记录(IP)
5. 本地DNS缓存结果 → 返回给OS → 返回给浏览器

递归查询(客户端→本地DNS) + 迭代查询(本地DNS→各级DNS)
```

**Q: TCP如何保证可靠传输？**

```
1. 序列号和确认号: 每个字节有序列号, 接收方确认
2. 重传机制: 超时重传(RTO) + 快速重传(3个重复ACK)
3. 流量控制: 滑动窗口(接收方告知发送方窗口大小)
4. 拥塞控制: 慢启动→拥塞避免→快恢复→快重传
5. 数据校验: CRC校验和(检测传输中数据是否损坏)
6. 有序到达: 序列号保证有序, 乱序时重新排序
```

**Q: TCP滑动窗口？**

```
发送方窗口:
  已发送已确认 | 已发送未确认 | 未发送可发送 | 未发送不可发送
                  ← 发送窗口 →

  窗口大小 = min(拥塞窗口cwnd, 接收窗口rwnd)
  接收方通过ACK中的窗口字段告知发送方自己的接收能力

零窗口探测:
  接收方窗口=0时, 发送方定期发零窗口探测报文
  防止窗口更新报文丢失导致死锁
```

**Q: TCP拥塞控制算法？**

```
1. 慢启动: cwnd从1开始, 每RTT翻倍(指数增长)
   到达ssthresh(慢启动阈值) → 进入拥塞避免

2. 拥塞避免: cwnd每RTT加1(线性增长)
   直到发生丢包 → 快恢复或慢启动

3. 快重传: 收到3个重复ACK → 立即重传(不等超时)
   ssthresh = cwnd/2, cwnd = ssthresh

4. 快恢复: cwnd = ssthresh + 3(快重传后不减到1)
   继续拥塞避免(线性增长)

BBR算法(Google): 不依赖丢包判断拥塞, 测量带宽和RTT
  → 更高效利用带宽, Linux 4.9+默认
```

**Q: HTTP长连接 vs 短连接？**

```
短连接(HTTP/1.0): 每次请求建TCP → 请求响应 → 断开
  开销: 每次TCP握手+挥手, 高延迟

长连接(HTTP/1.1 Keep-Alive): TCP建立后保持, 多个请求复用
  优点: 减少TCP建连开销
  缺点: 队头阻塞(一个慢请求阻塞后面的)

连接复用限制:
  - 同域名最多6个并发连接(浏览器限制)
  - HTTP/2多路复用解决了队头阻塞(一个TCP并行多请求)
```

**Q: WebSocket vs HTTP？**

```
HTTP: 请求-响应模式, 单向(客户端发起), 每次需带Header
WebSocket: 全双工通信, 服务端可主动推送, 只握手时用HTTP

WebSocket握手:
  GET /ws HTTP/1.1
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Key: ...

  服务端响应101 Switching Protocols → 升级为WebSocket

适用场景: 实时聊天/股票行情/协同编辑/在线游戏
```

**Q: RESTful API设计规范？**

```
URI: 名词复数, 不含动词
  GET    /users          # 获取用户列表
  GET    /users/123      # 获取单个用户
  POST   /users          # 创建用户
  PUT    /users/123      # 全量更新
  PATCH  /users/123      # 部分更新
  DELETE /users/123      # 删除

状态码:
  200 OK / 201 Created / 204 No Content
  400 Bad Request / 401 Unauthorized / 404 Not Found
  500 Internal Error

版本: URI(/v1/users) 或 Header(Accept: application/vnd.api+json;version=1)

分页: /users?page=1&size=20 或 /users?cursor=xxx

HATEOAS: 响应中包含相关操作的链接(自描述API)
```

---

*最后更新: 2026-07-14*

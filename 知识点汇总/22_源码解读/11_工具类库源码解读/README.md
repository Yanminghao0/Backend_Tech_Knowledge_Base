# 工具类库源码解读

> 序列化框架与HTTP客户端核心源码解析

---

## 📋 文档列表

### 序列化框架（4篇）

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 18.1_Jackson源码解析.md | ObjectMapper、Serializer/Deserializer、注解处理 | ⭐⭐⭐⭐ | 📄 待补充 |
| 18.2_Fastjson源码解析.md | 自描述序列化、AutoType、安全漏洞分析 | ⭐⭐⭐⭐ | 📄 待补充 |
| 18.3_Gson源码解析.md | TypeAdapter、反射机制、流式API | ⭐⭐⭐ | 📄 待补充 |
| 18.4_Protobuf源码解析.md | 二进制编码、Schema定义、跨语言支持 | ⭐⭐⭐⭐ | 📄 待补充 |

### HTTP客户端（3篇）

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 18.5_OkHttp源码解析.md | 拦截器链、连接池、Dispatcher调度 | ⭐⭐⭐⭐ | 📄 待补充 |
| 18.6_HttpClient源码解析.md | 连接管理池、重试机制、异步Future | ⭐⭐⭐ | 📄 待补充 |
| 18.7_RestTemplate源码解析.md | 消息转换器、拦截器、错误处理 | ⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **掌握JSON序列化**：Jackson的序列化流程（ObjectMapper→TokenStream→Serializer）、注解处理（@JsonProperty/@JsonAlias/@JsonIgnore）、性能优化（JsonFactory复用、ByteSourcePrinter）
2. **理解二进制序列化**：Protobuf的Varint编码、字段编号、前向/后向兼容、proto3语法
3. **掌握HTTP客户端**：OkHttp的拦截器链设计（责任链模式）、连接池管理（ConnectionPool，5分钟空闲回收）、Dispatcher调度（同步/异步队列）
4. **安全意识**：Fastjson AutoType漏洞成因（@type反序列化任意类）、Jackson反序列化漏洞、防御方案

---

## 📊 序列化框架对比表

| 维度 | Jackson | Fastjson | Gson | Protobuf |
|------|---------|----------|------|----------|
| **格式** | JSON | JSON | JSON | 二进制 |
| **性能** | ⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ 最高 | ⭐⭐⭐ 中 | ⭐⭐⭐⭐⭐ 极高 |
| **安全性** | ⭐⭐⭐⭐ 有漏洞但可控 | ⭐⭐ 历史漏洞多 | ⭐⭐⭐⭐⭐ 安全 | ⭐⭐⭐⭐⭐ 安全 |
| **生态** | ⭐⭐⭐⭐⭐ Spring默认 | ⭐⭐⭐ 阿里系 | ⭐⭐⭐⭐ Google系 | ⭐⭐⭐⭐ gRPC |
| **可读性** | 好 | 好 | 好 | 差(需proto) |
| **跨语言** | 仅Java | 仅Java | 仅Java | 30+语言 |
| **Schema** | 不需要 | 不需要 | 不需要 | 需要.proto |
| **字段兼容** | @JsonIgnoreProperties | @JSONField | @SerializedName | 字段编号天然兼容 |
| **推荐场景** | Spring项目 | 内部系统 | Android/轻量 | 微服务RPC |

### Protobuf Varint 编码示例

```
字段值: 300
二进制: 1 00101100  (9bit)

Varint编码: 每字节高位1bit做续位标志
  → 10101100 00000010
  → 去掉续位: 0101100 0000010
  → 拼接: 0000010 0101100 = 300

字段1, 值300的完整编码:
  tag = (field_number << 3) | wire_type = (1 << 3) | 0 = 0x08
  → 08 AC 02  (仅3字节)
```

---

## 📊 HTTP客户端对比表

| 维度 | OkHttp | Apache HttpClient | RestTemplate |
|------|--------|-------------------|--------------|
| **架构** | 拦截器链(责任链) | 经典/异步两套API | 模板方法模式 |
| **连接池** | ConnectionPool(5min) | PoolingHttpClientConnectionManager | 委托底层实现 |
| **异步支持** | Dispatcher+Callback | Future/CompletableFuture | 不原生支持 |
| **拦截器** | Application+Network | HttpRequestInterceptor | ClientHttpRequestInterceptor |
| **HTTP/2** | ✅ 支持 | ✅ (5.x) | 取决底层 |
| **WebSocket** | ✅ 内置 | ❌ | ❌ |
| **Spring集成** | 需手动配置 | 需手动配置 | Spring默认(已过时) |
| **推荐度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ (迁移WebClient) |
| **适用场景** | Android/微服务 | 传统Java EE | Spring MVC |

### OkHttp 拦截器链执行顺序

```
请求方向 ↓
┌──────────────────────────────────┐
│  RetryAndFollowUpInterceptor     │  ← 重试、重定向
├──────────────────────────────────┤
│  BridgeInterceptor               │  ← 补全请求头(Content-Type等)
├──────────────────────────────────┤
│  CacheInterceptor                │  ← 缓存命中检查
├──────────────────────────────────┤
│  ConnectInterceptor              │  ← 建立连接(连接池复用)
├──────────────────────────────────┤
│  自定义NetworkInterceptor         │  ← 用户扩展
├──────────────────────────────────┤
│  CallServerInterceptor           │  ← 真正发送HTTP请求
└──────────────────────────────────┘
响应方向 ↑ (逆序返回)
```

---

## 📖 学习路径

```
阶段一: Jackson（最主流，Spring默认）
  ↓  理解JSON序列化的TokenStream模型
阶段二: Protobuf（理解二进制编码优势）
  ↓  对比JSON vs 二进制，理解Schema驱动的兼容性
阶段三: OkHttp（HTTP客户端标杆）
  ↓  理解拦截器链设计模式
阶段四: Fastjson/Gson（对比学习）
  ↓  理解AutoType漏洞、反射式序列化
```

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐ 高频：
- Jackson和Fastjson的区别和选型？
- Fastjson的AutoType安全漏洞原理？
- Protobuf为什么比JSON快？（Varint编码 + 无反射 + Schema预编译）
- OkHttp的拦截器链执行顺序？责任链模式如何实现？
- OkHttp连接池如何管理？（5分钟空闲，最多5个连接，CleanupTask自动回收）
- RestTemplate vs WebClient？为什么RestTemplate被废弃？

⭐⭐⭐ 中频：
- Jackson的@JsonCreator和@Builder如何配合？
- Protobuf的前向兼容和后向兼容如何实现？
- HttpClient的连接池如何配置MaxPerRoute？
- 序列化循环引用如何处理？（@JsonIdentityInfo / Fastjson循环引用检测）
```

---

*最后更新：2026-07-13*

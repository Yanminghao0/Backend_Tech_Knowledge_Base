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

1. **掌握JSON序列化**：Jackson的序列化流程、注解处理、性能优化
2. **理解二进制序列化**：Protobuf的Varint编码、字段编号、前向兼容
3. **掌握HTTP客户端**：OkHttp的拦截器链设计、连接池管理

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐ 高频：
- Jackson和Fastjson的区别和选型？
- Fastjson的AutoType安全漏洞原理？
- Protobuf为什么比JSON快？
- OkHttp的拦截器链执行顺序？
- RestTemplate vs WebClient？
```

---

*最后更新：2026-07-13*

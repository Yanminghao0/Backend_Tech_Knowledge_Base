# 22_源码解读

> 深入理解主流框架源码，从使用者到贡献者的进阶之路

---

## 📚 目录结构

```
22_源码解读/
├── README.md                          # 本文档
├── 源码阅读方法论.md                   # 源码阅读技巧与方法论
├── 快速开始指南.md                     # 学习路径指南
├── 手写系列(Spring+RPC).md             # 手写简化版框架
├── 源码解读补充规划.md                  # 补充规划文档
│
├── 01_Java核心源码解读/                 # Java基础核心类源码
├── 02_集合框架源码解读/                 # Java集合源码（8篇）
├── 03_并发包源码解读/                   # JUC并发包源码（11篇）
├── 04_Spring源码解读/                   # Spring框架源码（13篇）
├── 05_MyBatis源码解读/                  # MyBatis框架源码（4篇）
├── 06_数据访问层源码解读/               # 连接池/分库分表源码（1篇+待补充）
├── 07_Netty源码解读/                    # Netty框架源码（8篇）
├── 08_Tomcat源码解读/                   # Tomcat源码（6篇）
├── 09_Dubbo源码解读/                    # Dubbo框架源码（6篇）
├── 10_中间件源码解读/                   # MQ/ES/缓存源码（待补充）
├── 11_工具类库源码解读/                 # 序列化/HTTP客户端源码（待补充）
├── 12_JVM源码解读/                      # JVM核心源码（待补充）
├── 13_分布式系统源码解读/               # ZK/Etcd/Consul源码（待补充）
└── 14_容器化源码解读/                   # Docker/K8s/Istio源码（待补充）
```

---

## 📖 源码解读内容

### 1️⃣ Java核心源码解读 📄待补充
📂 [01_Java核心源码解读](./01_Java核心源码解读/)
- Object/String/Thread/ClassLoader等基础类源码

### 2️⃣ 集合框架源码解读 ✅
📂 [02_集合框架源码解读](./02_集合框架源码解读/)
- ✅ HashMap、ArrayList、LinkedList、TreeMap
- ✅ HashSet、LinkedHashMap、PriorityQueue、ArrayDeque
- ⭐⭐⭐⭐⭐ HashMap原理（面试必问）

### 3️⃣ 并发包源码解读 ✅
📂 [03_并发包源码解读](./03_并发包源码解读/)
- ✅ AQS、ReentrantLock、ConcurrentHashMap
- ✅ ThreadPoolExecutor、CompletableFuture
- ✅ CountDownLatch、CyclicBarrier、Semaphore
- ✅ ReentrantReadWriteLock、AtomicInteger、BlockingQueue
- ⭐⭐⭐⭐⭐ AQS核心原理（面试高频）

### 4️⃣ Spring源码解读 ✅
📂 [04_Spring源码解读](./04_Spring源码解读/)
- ✅ IoC容器、AOP、@Autowired注入
- ✅ BeanPostProcessor、@Configuration、ApplicationListener
- ✅ SpringBoot启动流程、自动配置、Starter机制
- ✅ SpringMVC、事务管理、内嵌Tomcat
- ⭐⭐⭐⭐⭐ Bean生命周期（面试必问）

### 5️⃣ MyBatis源码解读 ✅
📂 [05_MyBatis源码解读](./05_MyBatis源码解读/)
- ✅ SqlSession、Mapper代理
- ✅ 一二级缓存、插件机制
- ⭐⭐⭐⭐⭐ Mapper代理原理

### 6️⃣ 数据访问层源码解读 🔸
📂 [06_数据访问层源码解读](./06_数据访问层源码解读/)
- ✅ HikariCP连接池
- 📄 待补充：Druid、ShardingSphere

### 7️⃣ Netty源码解读 ✅
📂 [07_Netty源码解读](./07_Netty源码解读/)
- ✅ 核心架构、Bootstrap、EventLoop
- ✅ Pipeline、ChannelHandler、内存管理
- ✅ 零拷贝、编解码器
- ⭐⭐⭐⭐⭐ Reactor线程模型

### 8️⃣ Tomcat源码解读 ✅
📂 [08_Tomcat源码解读](./08_Tomcat源码解读/)
- ✅ 启动流程、Connector、Container
- ✅ Servlet处理、线程模型、类加载机制

### 9️⃣ Dubbo源码解读 ✅
📂 [09_Dubbo源码解读](./09_Dubbo源码解读/)
- ✅ SPI机制、服务暴露、服务引用
- ✅ 协议层、负载均衡、集群容错
- ⭐⭐⭐⭐⭐ SPI扩展机制

### 🔟 中间件源码解读 📄待补充
📂 [10_中间件源码解读](./10_中间件源码解读/)
- 📄 RocketMQ、Kafka、RabbitMQ
- 📄 Elasticsearch、Lucene
- 📄 Caffeine、Guava Cache、Ehcache

### 1️⃣1️⃣ 工具类库源码解读 📄待补充
📂 [11_工具类库源码解读](./11_工具类库源码解读/)
- 📄 Jackson、Fastjson、Gson、Protobuf
- 📄 OkHttp、HttpClient、RestTemplate

### 1️⃣2️⃣ JVM源码解读 📄待补充
📂 [12_JVM源码解读](./12_JVM源码解读/)
- 📄 ClassLoader、GC算法、JIT编译器
- 📄 内存模型、synchronized、volatile

### 1️⃣3️⃣ 分布式系统源码解读 📄待补充
📂 [13_分布式系统源码解读](./13_分布式系统源码解读/)
- 📄 Zookeeper、Etcd、Consul

### 1️⃣4️⃣ 容器化源码解读 📄待补充
📂 [14_容器化源码解读](./14_容器化源码解读/)
- 📄 Docker、Kubernetes、Istio

---

## 🚀 快速开始

### 新手入门
📄 [快速开始指南.md](./快速开始指南.md) — 零基础学习路径、面试突击必背

### 学习路径推荐
```
第一阶段（2-3周）：Java核心源码
├── HashMap源码解析 ⭐⭐⭐⭐⭐
├── AQS源码解析 ⭐⭐⭐⭐⭐
└── ThreadPoolExecutor源码解析 ⭐⭐⭐⭐⭐

第二阶段（3-4周）：Spring框架源码
├── IoC容器源码解析 ⭐⭐⭐⭐⭐
├── AOP源码解析 ⭐⭐⭐⭐⭐
└── SpringBoot自动配置源码 ⭐⭐⭐⭐

第三阶段（2-3周）：持久层和网络
├── MyBatis源码解析 ⭐⭐⭐⭐
├── Netty核心架构解析 ⭐⭐⭐⭐
└── Dubbo源码解析 ⭐⭐⭐⭐
```

---

## 📋 补充规划

📄 [源码解读补充规划.md](./源码解读补充规划.md) — 详细规划文档

| 优先级 | 内容 | 篇数 | 状态 |
|--------|------|------|------|
| P0 | Java核心+Spring+MyBatis | 22篇 | ✅ 100% |
| P1 | Web容器+微服务+数据访问 | 37篇 | 🔸 46% |
| P2 | 中间件+工具类库 | 15篇 | 📄 框架已搭建 |
| P3 | JVM+分布式+容器化 | 12篇 | 📄 框架已搭建 |

---

## 🔗 相关资源

### 推荐书籍
- 📘 《Spring源码深度解析》- 郝佳
- 📘 《MyBatis技术内幕》- 徐郡明
- 📘 《Netty实战》- Norman Maurer
- 📘 《Java并发编程的艺术》- 方腾飞

### 源码仓库
- 💻 [Spring Framework](https://github.com/spring-projects/spring-framework)
- 💻 [MyBatis](https://github.com/mybatis/mybatis-3)
- 💻 [Netty](https://github.com/netty/netty)
- 💻 [Dubbo](https://github.com/apache/dubbo)

---

*最后更新：2026-07-13*

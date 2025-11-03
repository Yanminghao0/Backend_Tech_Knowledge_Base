# 23_源码解读

> 深入剖析主流框架源码，理解底层原理与设计思想

---

## 📚 目录结构

### Spring生态源码

- [Spring核心源码解析.md](./Spring核心源码解析.md) - IoC容器、AOP、事务实现原理
- [SpringBoot自动装配原理.md](./SpringBoot自动装配原理.md) - 自动配置、Starter机制
- [SpringCloud核心组件源码.md](./SpringCloud核心组件源码.md) - Ribbon、Feign、Hystrix

### 持久层框架源码

- [MyBatis源码解析.md](./MyBatis源码解析.md) - 执行流程、缓存、插件机制
- [Hibernate源码解析.md](./Hibernate源码解析.md) - ORM映射、缓存、延迟加载

### 分布式框架源码

- [Dubbo源码解析.md](./Dubbo源码解析.md) - SPI、服务发布、服务引用、负载均衡
- [Nacos源码解析.md](./Nacos源码解析.md) - 配置中心、注册中心实现
- [Seata源码解析.md](./Seata源码解析.md) - AT模式、TCC模式实现

### 中间件源码

- [RocketMQ源码解析.md](./RocketMQ源码解析.md) - 消息存储、主从同步、事务消息
- [Redis源码解析.md](./Redis源码解析.md) - 数据结构、持久化、主从复制

### 手写系列

- [手写系列(Spring+RPC).md](./手写系列(Spring+RPC).md) - 手写IoC、AOP、RPC框架

---

## 🎯 学习路径

### 阶段一：Spring核心（必学）
1. **Spring IoC容器**
   - BeanFactory vs ApplicationContext
   - Bean生命周期
   - 循环依赖解决
   - 三级缓存机制

2. **Spring AOP**
   - JDK动态代理 vs CGLIB
   - ProxyFactory创建流程
   - 拦截器链执行

3. **Spring事务**
   - TransactionInterceptor
   - 传播行为实现
   - 编程式 vs 声明式

### 阶段二：持久层框架
1. **MyBatis核心**
   - SqlSessionFactory创建
   - Mapper代理机制
   - 一级/二级缓存
   - 插件拦截器

### 阶段三：分布式框架
1. **Dubbo RPC**
   - SPI扩展机制
   - 服务暴露流程
   - 服务引用流程
   - 负载均衡策略
   - 集群容错

2. **Nacos**
   - 配置变更推送
   - 服务注册心跳
   - AP vs CP模式

### 阶段四：手写实现
1. **手写Spring IoC**
   - 注解扫描
   - Bean工厂
   - 依赖注入

2. **手写RPC框架**
   - 动态代理
   - 网络通信（Netty）
   - 序列化/反序列化
   - 服务注册发现

---

## 📖 阅读建议

### 源码阅读方法

1. **带着问题读源码**
   - 为什么Spring能解决循环依赖？
   - MyBatis如何实现延迟加载？
   - Dubbo如何实现服务降级？

2. **抓住主流程**
   - 不要陷入细节
   - 先画出核心流程图
   - 再深入关键节点

3. **调试跟踪**
   - 打断点单步调试
   - 观察调用栈
   - 记录关键变量

4. **画图总结**
   - 类图（核心类关系）
   - 时序图（执行流程）
   - 流程图（业务逻辑）

### 源码阅读工具

- **IDEA插件**
  - SequenceDiagram - 生成时序图
  - PlantUML - 画UML图
  - Call Graph - 方法调用图

- **在线工具**
  - ProcessOn - 流程图
  - Draw.io - 架构图

---

## 🔥 核心问题清单

### Spring

- [ ] Spring IoC容器的启动流程是什么？
- [ ] Spring如何解决循环依赖？三级缓存的作用？
- [ ] @Autowired和@Resource的区别？底层实现？
- [ ] Spring AOP的实现原理？JDK代理和CGLIB的选择逻辑？
- [ ] Spring事务如何实现的？传播行为如何工作？
- [ ] SpringBoot自动装配原理？@EnableAutoConfiguration做了什么？

### MyBatis

- [ ] MyBatis的执行流程？
- [ ] Mapper接口如何生成代理对象？
- [ ] MyBatis一级缓存和二级缓存的实现？
- [ ] MyBatis插件原理？如何实现分页插件？
- [ ] MyBatis如何防止SQL注入？

### Dubbo

- [ ] Dubbo的SPI机制和JDK SPI的区别？
- [ ] Dubbo服务暴露和引用的流程？
- [ ] Dubbo支持哪些负载均衡策略？如何实现？
- [ ] Dubbo的容错机制有哪些？Failover如何实现？
- [ ] Dubbo如何实现异步调用？

### RocketMQ

- [ ] RocketMQ的消息存储结构？CommitLog、ConsumeQueue的作用？
- [ ] RocketMQ如何保证消息不丢失？
- [ ] RocketMQ事务消息的实现原理？
- [ ] RocketMQ的主从同步机制？

---

## 💡 学习资源

### 官方文档

- [Spring Framework文档](https://docs.spring.io/spring-framework/reference/)
- [MyBatis文档](https://mybatis.org/mybatis-3/zh/)
- [Dubbo文档](https://dubbo.apache.org/zh/)
- [RocketMQ文档](https://rocketmq.apache.org/zh/)

### 推荐书籍

- 《Spring源码深度解析》 - 郝佳
- 《MyBatis技术内幕》 - 徐郡明
- 《深入理解Apache Dubbo与实战》 - 诣极、林琳
- 《RocketMQ实战与原理解析》 - 杨开元

### 开源项目

- [tiny-spring](https://github.com/code4craft/tiny-spring) - 简化版Spring
- [mini-rpc](https://github.com/luxiaoxun/NettyRpc) - 简单RPC框架

---

## ✅ 学习目标

通过源码解读，达到以下目标：

1. **理解设计思想**
   - 理解IoC、AOP等核心思想
   - 掌握面向接口编程
   - 学习优秀的设计模式应用

2. **掌握实现原理**
   - 理解框架核心流程
   - 掌握关键技术点
   - 能够回答面试常见问题

3. **提升编码能力**
   - 学习优秀代码写法
   - 理解架构设计
   - 具备手写简化版能力

4. **解决实际问题**
   - 理解配置原理
   - 快速定位问题
   - 优化性能调优

---

## 📌 待补充

- [ ] Netty源码解析
- [ ] Tomcat源码解析
- [ ] Sentinel源码解析
- [ ] Hystrix源码解析
- [ ] Spring Security源码解析

---

**最后更新时间**：2025-10-29

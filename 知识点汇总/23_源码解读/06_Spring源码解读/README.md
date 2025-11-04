# Spring源码解读

> 💡 深入理解Spring框架核心原理，从IoC到AOP的完整源码分析

---

## 📚 目录结构

```
Spring源码解读/
├── README.md                           # 本文档
├── IoC容器源码解析.md                   # IoC容器核心原理
├── AOP源码解析.md                      # AOP实现原理
├── 事务管理源码解析.md                  # 事务管理机制
├── SpringMVC源码解析.md                # MVC请求处理流程
├── SpringBoot自动配置源码.md           # 自动配置原理
├── @Autowired注入源码解析.md           # 依赖注入原理 ✅
├── SpringBoot启动流程源码解析.md        # 启动流程详解 ✅
├── @Configuration配置类源码解析.md      # 配置类CGLIB代理 ✅ NEW
├── BeanPostProcessor源码解析.md        # Bean后置处理器 ✅ NEW
├── ApplicationListener源码解析.md      # 事件机制 ✅ NEW
├── @EnableAutoConfiguration源码解析.md # 自动配置加载 ✅ NEW
├── Starter机制源码解析.md              # Starter开发 ✅ NEW
└── SpringBoot内嵌Tomcat源码解析.md     # 内嵌容器 ✅ NEW
```

---

## 🎯 学习目标

### 核心问题
1. Spring IoC容器是如何管理Bean的？
2. Spring AOP是如何实现的？
3. Spring事务是如何工作的？
4. SpringMVC请求处理流程是怎样的？
5. SpringBoot自动配置原理是什么？

### 面试高频问题
- ⭐⭐⭐⭐⭐ Bean的生命周期
- ⭐⭐⭐⭐⭐ 循环依赖如何解决
- ⭐⭐⭐⭐⭐ AOP动态代理选择
- ⭐⭐⭐⭐ 事务传播机制
- ⭐⭐⭐⭐ 自动配置原理

---

## 📖 核心内容

### 1️⃣ IoC容器源码解析
📄 [IoC容器源码解析.md](./IoC容器源码解析.md)

**核心内容**：
- ✅ BeanFactory与ApplicationContext
- ✅ Bean定义加载与解析
- ✅ Bean实例化与初始化
- ✅ 依赖注入实现
- ✅ 循环依赖三级缓存

**核心类**：
```
BeanFactory                 # Bean工厂接口
DefaultListableBeanFactory  # 默认实现
ApplicationContext          # 应用上下文
BeanDefinition             # Bean定义
BeanPostProcessor          # Bean后置处理器
```

### 2️⃣ AOP源码解析
📄 [AOP源码解析.md](./AOP源码解析.md)

**核心内容**：
- ✅ AOP核心概念
- ✅ 动态代理实现（JDK/CGLIB）
- ✅ 切面织入时机
- ✅ 拦截器链执行

**核心类**：
```
AopProxy                   # AOP代理接口
JdkDynamicAopProxy        # JDK动态代理
CglibAopProxy             # CGLIB代理
ProxyFactory              # 代理工厂
Advisor                   # 切面
MethodInterceptor         # 方法拦截器
```

### 3️⃣ 事务管理源码解析
📄 [事务管理源码解析.md](./事务管理源码解析.md)

**核心内容**：
- ✅ 事务管理器
- ✅ 事务传播机制
- ✅ 事务同步管理
- ✅ @Transactional原理

**核心类**：
```
PlatformTransactionManager  # 事务管理器接口
DataSourceTransactionManager # 数据源事务管理器
TransactionDefinition       # 事务定义
TransactionStatus          # 事务状态
TransactionSynchronizationManager # 事务同步管理器
```

### 4️⃣ SpringMVC源码解析
📄 [SpringMVC源码解析.md](./SpringMVC源码解析.md)

**核心内容**：
- ✅ DispatcherServlet初始化
- ✅ 请求处理流程
- ✅ 参数解析与绑定
- ✅ 视图解析与渲染

**核心类**：
```
DispatcherServlet          # 前端控制器
HandlerMapping             # 处理器映射
HandlerAdapter             # 处理器适配器
HandlerMethodArgumentResolver # 参数解析器
ViewResolver               # 视图解析器
```

### 5️⃣ SpringBoot自动配置源码
📄 [SpringBoot自动配置源码.md](./SpringBoot自动配置源码.md)

**核心内容**：
- ✅ @SpringBootApplication解析
- ✅ 自动配置加载机制
- ✅ 条件注解原理
- ✅ Starter原理

**核心类**：
```
SpringApplication          # 启动类
AutoConfigurationImportSelector # 自动配置导入
Condition                  # 条件接口
@ConditionalOnClass       # 条件注解
spring.factories          # 配置文件
```

---

## 🚀 学习路径

### 阶段1：IoC容器（1-2周）
```
学习顺序：
1. BeanFactory接口体系
2. BeanDefinition加载
3. Bean实例化流程
4. 依赖注入实现
5. 循环依赖解决

重点掌握：
- Bean生命周期完整流程
- 三级缓存解决循环依赖
- BeanPostProcessor扩展点
```

### 阶段2：AOP（1周）
```
学习顺序：
1. AOP核心概念
2. 代理创建时机
3. JDK动态代理实现
4. CGLIB代理实现
5. 拦截器链执行

重点掌握：
- 代理选择策略
- 切面织入流程
- 拦截器链调用
```

### 阶段3：事务（1周）
```
学习顺序：
1. 事务管理器体系
2. @Transactional解析
3. 事务传播机制
4. 事务同步管理

重点掌握：
- 事务传播行为
- 事务失效场景
- 编程式事务
```

### 阶段4：SpringMVC（1周）
```
学习顺序：
1. DispatcherServlet初始化
2. 请求映射流程
3. 参数解析机制
4. 返回值处理

重点掌握：
- 请求处理完整流程
- 参数解析器扩展
- 异常处理机制
```

### 阶段5：SpringBoot（1周）
```
学习顺序：
1. 启动流程分析
2. 自动配置加载
3. 条件注解原理
4. 自定义Starter

重点掌握：
- 自动配置原理
- 条件注解使用
- Starter开发
```

---

## 💡 核心知识点速查

### Bean生命周期
```
1. 实例化（Instantiation）
   - createBeanInstance()
   
2. 属性填充（Populate）
   - populateBean()
   
3. 初始化（Initialization）
   - invokeAwareMethods()
   - BeanPostProcessor.postProcessBeforeInitialization()
   - InitializingBean.afterPropertiesSet()
   - init-method
   - BeanPostProcessor.postProcessAfterInitialization()
   
4. 销毁（Destruction）
   - DisposableBean.destroy()
   - destroy-method
```

### 循环依赖三级缓存
```java
// 一级缓存：完整的Bean
Map<String, Object> singletonObjects

// 二级缓存：早期暴露的Bean（未完成属性填充）
Map<String, Object> earlySingletonObjects

// 三级缓存：Bean工厂（用于创建代理）
Map<String, ObjectFactory<?>> singletonFactories

// 解决流程：
// A创建 → 放入三级缓存 → 填充属性需要B
// B创建 → 放入三级缓存 → 填充属性需要A
// 从三级缓存获取A → 移到二级缓存 → B完成创建
// A从一级缓存获取B → A完成创建
```

### AOP代理选择
```
JDK动态代理：
- 目标类实现了接口
- 基于接口代理
- 性能略优

CGLIB代理：
- 目标类没有实现接口
- 基于继承代理
- 不能代理final方法

选择策略：
- proxyTargetClass=false：优先JDK代理
- proxyTargetClass=true：强制CGLIB代理
```

### 事务传播行为
```
REQUIRED（默认）：有事务加入，没有新建
REQUIRES_NEW：总是新建事务
NESTED：嵌套事务
SUPPORTS：有事务加入，没有非事务执行
NOT_SUPPORTED：非事务执行
MANDATORY：必须有事务，否则异常
NEVER：必须没有事务，否则异常
```

---

## 📚 参考资料

### 推荐书籍
- 📘 《Spring源码深度解析》- 郝佳
- 📘 《Spring技术内幕》- 计文柯
- 📘 《Spring Boot编程思想》- 小马哥

### 在线资源
- 🌐 [Spring官方文档](https://spring.io/docs)
- 🌐 [Spring源码](https://github.com/spring-projects/spring-framework)

---

**深入Spring源码，成为Spring专家！** 🚀

*最后更新：2025-12-28*
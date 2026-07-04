# Spring核心源码解析

> IoC容器、AOP、事务管理核心实现原理

---

## 📋 目录

- [1. Spring IoC容器](#1-spring-ioc容器)
- [2. Spring AOP](#2-spring-aop)
- [3. Spring事务](#3-spring事务)
- [4. Spring循环依赖](#4-spring循环依赖)
- [5. Spring扩展点](#5-spring扩展点)
- [6. 面试高频问题](#6-面试高频问题)

---

## 🎯 学习目标

- ✅ 掌握Spring IoC容器启动流程
- ✅ 理解Bean的完整生命周期
- ✅ 掌握三级缓存解决循环依赖原理
- ✅ 理解AOP代理创建与执行流程
- ✅ 掌握Spring事务实现原理
- ✅ 熟悉Spring核心扩展点

---

## 1. Spring IoC容器

### 1.1 容器体系结构

**核心接口**：
```
BeanFactory（根接口）
    ↓
ListableBeanFactory（可列举Bean）
    ↓
HierarchicalBeanFactory（分层Bean工厂）
    ↓
ConfigurableBeanFactory（可配置Bean工厂）
    ↓
ApplicationContext（应用上下文）
    ↓
ConfigurableApplicationContext
    ↓
AbstractApplicationContext
    ↓
ClassPathXmlApplicationContext / AnnotationConfigApplicationContext
```

**核心类**：
- `DefaultListableBeanFactory`：最重要的实现类
- `BeanDefinition`：Bean定义信息
- `BeanPostProcessor`：Bean后置处理器

### 1.2 容器启动流程

#### 核心方法：refresh()

```java
// AbstractApplicationContext#refresh()
public void refresh() throws BeansException, IllegalStateException {
    synchronized (this.startupShutdownMonitor) {
        // 1. 准备刷新上下文环境
        prepareRefresh();
        
        // 2. 获取BeanFactory（创建或刷新）
        ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();
        
        // 3. 对BeanFactory进行功能填充
        prepareBeanFactory(beanFactory);
        
        try {
            // 4. 允许子类修改BeanFactory（扩展点）
            postProcessBeanFactory(beanFactory);
            
            // 5. 执行BeanFactoryPostProcessor（重要！）
            invokeBeanFactoryPostProcessors(beanFactory);
            
            // 6. 注册BeanPostProcessor
            registerBeanPostProcessors(beanFactory);
            
            // 7. 初始化消息源（国际化）
            initMessageSource();
            
            // 8. 初始化事件广播器
            initApplicationEventMulticaster();
            
            // 9. 留给子类初始化其他Bean（扩展点）
            onRefresh();
            
            // 10. 注册监听器
            registerListeners();
            
            // 11. 实例化所有非懒加载的单例Bean（重要！）
            finishBeanFactoryInitialization(beanFactory);
            
            // 12. 发布容器刷新完成事件
            finishRefresh();
        }
        catch (BeansException ex) {
            // 销毁已创建的单例Bean
            destroyBeans();
            cancelRefresh(ex);
            throw ex;
        }
        finally {
            resetCommonCaches();
        }
    }
}
```

**流程图**：
```
1. prepareRefresh()
   ├── 设置启动时间
   ├── 初始化属性源
   └── 验证必要属性

2. obtainFreshBeanFactory()
   ├── 刷新BeanFactory
   ├── 加载BeanDefinition
   └── 返回BeanFactory

3. prepareBeanFactory()
   ├── 设置类加载器
   ├── 添加BeanPostProcessor
   └── 注册默认环境Bean

4. postProcessBeanFactory()
   └── 子类扩展点

5. invokeBeanFactoryPostProcessors()
   ├── 执行BeanDefinitionRegistryPostProcessor
   └── 执行BeanFactoryPostProcessor

6. registerBeanPostProcessors()
   └── 注册所有BeanPostProcessor

7. initMessageSource()
   └── 国际化支持

8. initApplicationEventMulticaster()
   └── 事件发布器

9. onRefresh()
   └── 创建Web服务器等

10. registerListeners()
    └── 注册事件监听器

11. finishBeanFactoryInitialization()
    └── 实例化所有单例Bean

12. finishRefresh()
    ├── 初始化生命周期处理器
    ├── 发布ContextRefreshedEvent
    └── 启动完成
```

### 1.3 Bean的生命周期

**完整流程**：

```java
// 1. 实例化Bean
createBeanInstance()

// 2. 属性赋值
populateBean()

// 3. 初始化前置处理
applyBeanPostProcessorsBeforeInitialization()

// 4. 初始化
invokeInitMethods()
   ├── afterPropertiesSet()  // InitializingBean接口
   └── init-method          // 自定义初始化方法

// 5. 初始化后置处理（AOP代理在这里创建！）
applyBeanPostProcessorsAfterInitialization()

// 6. 使用Bean

// 7. 销毁
destroyBean()
   ├── destroy()           // DisposableBean接口
   └── destroy-method     // 自定义销毁方法
```

**核心代码**：

```java
// AbstractAutowireCapableBeanFactory#doCreateBean()
protected Object doCreateBean(String beanName, RootBeanDefinition mbd, Object[] args) {
    BeanWrapper instanceWrapper = null;
    
    // 1. 实例化Bean
    instanceWrapper = createBeanInstance(beanName, mbd, args);
    Object bean = instanceWrapper.getWrappedInstance();
    
    // 2. 提前暴露Bean（解决循环依赖）
    addSingletonFactory(beanName, () -> getEarlyBeanReference(beanName, mbd, bean));
    
    // 3. 属性赋值
    populateBean(beanName, mbd, instanceWrapper);
    
    // 4. 初始化Bean
    bean = initializeBean(beanName, bean, mbd);
    
    return bean;
}

protected Object initializeBean(String beanName, Object bean, RootBeanDefinition mbd) {
    // 执行Aware接口回调
    invokeAwareMethods(beanName, bean);
    
    // BeanPostProcessor前置处理
    Object wrappedBean = applyBeanPostProcessorsBeforeInitialization(bean, beanName);
    
    // 执行初始化方法
    invokeInitMethods(beanName, wrappedBean, mbd);
    
    // BeanPostProcessor后置处理（AOP代理）
    wrappedBean = applyBeanPostProcessorsAfterInitialization(wrappedBean, beanName);
    
    return wrappedBean;
}
```

---

## 4. Spring循环依赖

### 4.1 什么是循环依赖

**示例**：
```java
@Service
public class A {
    @Autowired
    private B b;
}

@Service
public class B {
    @Autowired
    private A a;
}
```

### 4.2 三级缓存机制

**核心代码**：
```java
// DefaultSingletonBeanRegistry

// 一级缓存：成品Bean
private final Map<String, Object> singletonObjects = new ConcurrentHashMap<>(256);

// 二级缓存：早期Bean（已实例化，未初始化）
private final Map<String, Object> earlySingletonObjects = new HashMap<>(16);

// 三级缓存：Bean工厂
private final Map<String, ObjectFactory<?>> singletonFactories = new HashMap<>(16);

protected Object getSingleton(String beanName, boolean allowEarlyReference) {
    // 1. 从一级缓存获取
    Object singletonObject = this.singletonObjects.get(beanName);
    
    if (singletonObject == null && isSingletonCurrentlyInCreation(beanName)) {
        synchronized (this.singletonObjects) {
            // 2. 从二级缓存获取
            singletonObject = this.earlySingletonObjects.get(beanName);
            
            if (singletonObject == null && allowEarlyReference) {
                // 3. 从三级缓存获取
                ObjectFactory<?> singletonFactory = this.singletonFactories.get(beanName);
                if (singletonFactory != null) {
                    singletonObject = singletonFactory.getObject();
                    // 放入二级缓存
                    this.earlySingletonObjects.put(beanName, singletonObject);
                    // 从三级缓存移除
                    this.singletonFactories.remove(beanName);
                }
            }
        }
    }
    return singletonObject;
}
```

**解决流程**：
```
1. A创建：实例化A，放入三级缓存
2. A注入B：发现需要B，去创建B
3. B创建：实例化B，放入三级缓存
4. B注入A：从三级缓存获取A（半成品），注入
5. B完成初始化，放入一级缓存
6. A注入B成功，A完成初始化，放入一级缓存
```

**为什么需要三级缓存？**
- 一级缓存：存储完整Bean
- 二级缓存：存储早期Bean
- 三级缓存：存储Bean工厂（为AOP代理预留）

**关键点**：
- 只能解决setter注入的循环依赖
- 构造器注入无法解决
- prototype无法解决

---

## 6. 面试高频问题

### Q1: Spring如何解决循环依赖？

**答案**：
使用三级缓存机制：
1. 一级缓存存成品Bean
2. 二级缓存存早期Bean
3. 三级缓存存Bean工厂

通过提前暴露半成品Bean，让其他Bean先注入引用，后续再完成初始化。

### Q2: 为什么构造器注入无法解决循环依赖？

**答案**：
构造器注入时Bean还未实例化，无法提前暴露引用。

### Q3: BeanFactory和ApplicationContext的区别？

**答案**：
- BeanFactory：IoC容器基本实现，懒加载
- ApplicationContext：BeanFactory的子接口，提供更多企业级功能
  - 事件发布
  - 国际化
  - 资源访问
  - 自动注册BeanPostProcessor

### Q4: Spring AOP如何选择JDK代理还是CGLIB？

**答案**：
- 如果目标对象实现了接口 → JDK动态代理
- 如果目标对象没有接口 → CGLIB代理
- 可以强制使用CGLIB：`@EnableAspectJAutoProxy(proxyTargetClass = true)`

### Q5: Spring事务失效的场景？

**答案**：
1. 方法不是public
2. 同类方法调用（this调用）
3. 异常被catch没有抛出
4. 数据库不支持事务
5. 没有被Spring管理
6. propagation设置错误

---

## 📚 参考资料

- 《Spring源码深度解析》
- [Spring Framework官方文档](https://docs.spring.io/spring-framework/reference/)
- [Spring源码GitHub](https://github.com/spring-projects/spring-framework)

---

**最后更新时间**：2025-10-29

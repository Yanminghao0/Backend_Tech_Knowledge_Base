# Spring面试题

> Spring框架高频面试题及详细解答

## 📋 目录
- [IoC容器](#ioc容器)
- [AOP面向切面编程](#aop面向切面编程)
- [Spring事务管理](#spring事务管理)
- [Spring MVC](#spring-mvc)
- [Spring Boot](#spring-boot)
- [Spring Cloud](#spring-cloud)

---

## IoC容器

### Q1: 什么是IoC（控制反转）和DI（依赖注入）？（⭐⭐⭐⭐⭐）

**IoC（Inversion of Control）**：
```
传统方式：
  class UserService {
      private UserDao userDao = new UserDaoImpl();  // 自己创建依赖
  }
  
  问题：
    ❌ 紧耦合
    ❌ 难以测试
    ❌ 难以替换实现

IoC方式：
  class UserService {
      private UserDao userDao;  // 依赖由外部注入
      
      public void setUserDao(UserDao userDao) {
          this.userDao = userDao;
      }
  }
  
  优势：
    ✅ 松耦合
    ✅ 易于测试
    ✅ 易于替换实现
    
控制反转：
  - 对象创建的控制权从应用代码转移到IoC容器
  - 容器负责创建对象、管理依赖
```

**DI（Dependency Injection）**：
```
DI是实现IoC的一种方式

三种注入方式：

1. 构造器注入（推荐）：
   @Service
   public class UserService {
       private final UserDao userDao;
       
       @Autowired  // Spring 4.3后可省略
       public UserService(UserDao userDao) {
           this.userDao = userDao;
       }
   }
   
   优势：
     ✅ 依赖不可变（final）
     ✅ 避免空指针
     ✅ 便于单元测试
     ✅ Spring推荐方式

2. Setter注入：
   @Service
   public class UserService {
       private UserDao userDao;
       
       @Autowired
       public void setUserDao(UserDao userDao) {
           this.userDao = userDao;
       }
   }
   
   优势：
     ✅ 可选依赖
     ✅ 可重新注入
   
   劣势：
     ❌ 依赖可变
     ❌ 可能空指针

3. 字段注入（不推荐）：
   @Service
   public class UserService {
       @Autowired
       private UserDao userDao;
   }
   
   劣势：
     ❌ 无法使用final
     ❌ 难以单元测试
     ❌ 隐藏依赖关系
     ❌ 违反单一职责（依赖过多不易发现）
```

---

### Q2: Bean的生命周期？（⭐⭐⭐⭐⭐）

**完整生命周期**：
```
1. 实例化（Instantiation）：
   - 通过构造器创建Bean实例
   - 或通过工厂方法创建

2. 属性赋值（Populate）：
   - 依赖注入
   - @Autowired、@Value等

3. 初始化前（BeanPostProcessor.postProcessBeforeInitialization）：
   - @PostConstruct
   - ApplicationContextAwareProcessor

4. 初始化（Initialization）：
   - 执行InitializingBean.afterPropertiesSet()
   - 执行自定义init-method

5. 初始化后（BeanPostProcessor.postProcessAfterInitialization）：
   - AOP代理在这里创建

6. 使用（In Use）：
   - Bean可以被使用了

7. 销毁前：
   - @PreDestroy

8. 销毁（Destruction）：
   - DisposableBean.destroy()
   - 自定义destroy-method
```

**源码解析**：
```java
// AbstractAutowireCapableBeanFactory.doCreateBean()
protected Object doCreateBean(String beanName, RootBeanDefinition mbd, Object[] args) {
    // 1. 实例化Bean
    BeanWrapper instanceWrapper = createBeanInstance(beanName, mbd, args);
    Object bean = instanceWrapper.getWrappedInstance();
    
    // 2. 属性赋值
    populateBean(beanName, mbd, instanceWrapper);
    
    // 3. 初始化Bean
    Object exposedObject = initializeBean(beanName, bean, mbd);
    
    return exposedObject;
}

// 初始化Bean
protected Object initializeBean(String beanName, Object bean, RootBeanDefinition mbd) {
    // 3.1 Aware接口回调
    invokeAwareMethods(beanName, bean);
    
    // 3.2 BeanPostProcessor前置处理
    Object wrappedBean = applyBeanPostProcessorsBeforeInitialization(bean, beanName);
    
    // 3.3 初始化方法
    invokeInitMethods(beanName, wrappedBean, mbd);
    
    // 3.4 BeanPostProcessor后置处理（AOP代理）
    wrappedBean = applyBeanPostProcessorsAfterInitialization(wrappedBean, beanName);
    
    return wrappedBean;
}
```

**实战示例**：
```java
@Component
public class UserService implements InitializingBean, DisposableBean {
    
    private UserDao userDao;
    
    // 1. 构造器
    public UserService() {
        System.out.println("1. 构造器执行");
    }
    
    // 2. 依赖注入
    @Autowired
    public void setUserDao(UserDao userDao) {
        System.out.println("2. 依赖注入");
        this.userDao = userDao;
    }
    
    // 3. @PostConstruct
    @PostConstruct
    public void postConstruct() {
        System.out.println("3. @PostConstruct执行");
    }
    
    // 4. InitializingBean
    @Override
    public void afterPropertiesSet() {
        System.out.println("4. afterPropertiesSet执行");
    }
    
    // 5. init-method
    public void initMethod() {
        System.out.println("5. init-method执行");
    }
    
    // 6. @PreDestroy
    @PreDestroy
    public void preDestroy() {
        System.out.println("6. @PreDestroy执行");
    }
    
    // 7. DisposableBean
    @Override
    public void destroy() {
        System.out.println("7. destroy执行");
    }
    
    // 8. destroy-method
    public void destroyMethod() {
        System.out.println("8. destroy-method执行");
    }
}

// 输出顺序：
// 1. 构造器执行
// 2. 依赖注入
// 3. @PostConstruct执行
// 4. afterPropertiesSet执行
// 5. init-method执行
// ... 使用Bean ...
// 6. @PreDestroy执行
// 7. destroy执行
// 8. destroy-method执行
```

---

### Q3: @Autowired vs @Resource vs @Inject？（⭐⭐⭐⭐）

**详细对比**：

| 特性 | @Autowired | @Resource | @Inject |
|------|------------|-----------|---------|
| 来源 | Spring | Java EE (JSR-250) | Java EE (JSR-330) |
| 匹配方式 | 类型→名称 | 名称→类型 | 类型 |
| 支持required | ✅ @Autowired(required=false) | ❌ | ❌ |
| 支持@Qualifier | ✅ | ❌ | ✅ @Named |
| 支持@Primary | ✅ | ✅ | ✅ |
| 依赖 | Spring | javax.annotation | javax.inject |

**匹配逻辑对比**：
```java
// 假设有两个实现类
@Component("userDaoMysql")
public class UserDaoMysqlImpl implements UserDao {}

@Component("userDaoOracle")
public class UserDaoOracleImpl implements UserDao {}

// @Autowired：先按类型，再按名称
@Autowired
private UserDao userDaoMysql;  // ✅ 匹配成功（按名称）

@Autowired
private UserDao userDao;  // ❌ 报错：找到2个UserDao类型的Bean

@Autowired
@Qualifier("userDaoMysql")
private UserDao userDao;  // ✅ 匹配成功（指定名称）

// @Resource：先按名称，再按类型
@Resource(name = "userDaoMysql")
private UserDao userDao;  // ✅ 匹配成功（按名称）

@Resource
private UserDao userDaoMysql;  // ✅ 匹配成功（字段名=Bean名）

@Resource
private UserDao userDao;  // ❌ 报错：找不到名为userDao的Bean

// @Inject：按类型（需要javax.inject依赖）
@Inject
@Named("userDaoMysql")
private UserDao userDao;  // ✅ 匹配成功
```

**源码解析（@Autowired）**：
```java
// AutowiredAnnotationBeanPostProcessor
@Override
public PropertyValues postProcessProperties(PropertyValues pvs, Object bean, String beanName) {
    // 1. 找到所有@Autowired字段和方法
    InjectionMetadata metadata = findAutowiringMetadata(beanName, bean.getClass(), pvs);
    
    // 2. 注入
    metadata.inject(bean, beanName, pvs);
    
    return pvs;
}

// 依赖解析
protected Object doResolveDependency(DependencyDescriptor descriptor, String beanName,
        Set<String> autowiredBeanNames, TypeConverter typeConverter) {
    
    // 1. 查找类型匹配的所有Bean
    Map<String, Object> matchingBeans = findAutowireCandidates(beanName, type, descriptor);
    
    // 2. 如果找到多个，按名称匹配
    if (matchingBeans.size() > 1) {
        String autowiredBeanName = determineAutowireCandidate(matchingBeans, descriptor);
        if (autowiredBeanName != null) {
            return matchingBeans.get(autowiredBeanName);
        }
        // 3. 都不匹配，抛异常
        throw new NoUniqueBeanDefinitionException(type, matchingBeans.keySet());
    }
    
    return matchingBeans.values().iterator().next();
}
```

**使用建议**：
```
推荐使用 @Autowired：
  ✅ Spring原生支持
  ✅ 功能最强大
  ✅ 支持required属性
  ✅ 配合@Qualifier使用灵活
  
使用 @Resource：
  ✅ Java EE标准
  ✅ 按名称注入更明确
  ✅ 减少对Spring的依赖
  
使用 @Inject：
  ✅ Java EE标准
  ❌ 需要额外依赖
  ❌ 功能不如@Autowired丰富
```

---

### Q4: Spring如何解决循环依赖？（⭐⭐⭐⭐⭐）

**循环依赖示例**：
```java
@Component
public class A {
    @Autowired
    private B b;
}

@Component
public class B {
    @Autowired
    private A a;
}

// 创建A → 需要B → 创建B → 需要A → ...
// 形成循环！
```

**三级缓存机制**：
```java
// DefaultSingletonBeanRegistry
public class DefaultSingletonBeanRegistry {
    // 一级缓存：成品Bean（已初始化完成）
    private final Map<String, Object> singletonObjects = new ConcurrentHashMap<>(256);
    
    // 二级缓存：半成品Bean（已实例化，未初始化）
    private final Map<String, Object> earlySingletonObjects = new HashMap<>(16);
    
    // 三级缓存：Bean工厂
    private final Map<String, ObjectFactory<?>> singletonFactories = new HashMap<>(16);
}
```

**解决过程**：
```
假设创建A和B：

1. 创建A：
   - 实例化A（未初始化）
   - 将A的ObjectFactory放入三级缓存
   - 填充A的属性，发现依赖B
   
2. 创建B：
   - 实例化B（未初始化）
   - 将B的ObjectFactory放入三级缓存
   - 填充B的属性，发现依赖A
   
3. 从缓存获取A：
   - 一级缓存没有A
   - 二级缓存没有A
   - 三级缓存有A的ObjectFactory
   - 调用ObjectFactory.getObject()获取A（可能是代理对象）
   - 将A放入二级缓存，从三级缓存移除
   - 返回A给B
   
4. B初始化完成：
   - B的属性填充完成（a已注入）
   - B执行初始化方法
   - B放入一级缓存，从二级、三级缓存移除
   
5. A初始化完成：
   - A的属性填充完成（b已注入）
   - A执行初始化方法
   - A放入一级缓存，从二级、三级缓存移除

循环依赖解决 ✅
```

**源码解析**：
```java
// DefaultSingletonBeanRegistry.getSingleton()
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
                    singletonObject = singletonFactory.getObject();  // 获取Bean
                    this.earlySingletonObjects.put(beanName, singletonObject);  // 放入二级缓存
                    this.singletonFactories.remove(beanName);  // 从三级缓存移除
                }
            }
        }
    }
    return singletonObject;
}
```

**为什么需要三级缓存？**
```
两级缓存够吗？

场景1：普通Bean循环依赖
  - 两级缓存就够了
  - 一级：成品
  - 二级：半成品
  
场景2：Bean需要AOP代理
  - 需要三级缓存
  - 原因：AOP代理是在初始化后创建的
  - 但循环依赖时，需要提前创建代理对象
  
  A → B → A
  
  创建A：
    1. 实例化A（普通对象）
    2. 如果直接放二级缓存，B拿到的是普通对象
    3. 最后A完成初始化后创建代理对象
    4. B持有的还是普通对象 ❌
  
  三级缓存（ObjectFactory）：
    1. 实例化A
    2. 将ObjectFactory放入三级缓存
    3. B需要A时，调用ObjectFactory.getObject()
    4. ObjectFactory判断是否需要代理，如需要则创建代理对象
    5. B拿到的是代理对象 ✅
    6. A完成初始化，不会再创建代理
```

**无法解决的循环依赖**：
```java
// 1. 构造器循环依赖（无法解决）
@Component
public class A {
    private B b;
    
    @Autowired
    public A(B b) {  // 构造器注入
        this.b = b;
    }
}

@Component
public class B {
    private A a;
    
    @Autowired
    public B(A a) {  // 构造器注入
        this.a = a;
    }
}

// ❌ 报错：BeanCurrentlyInCreationException
// 原因：实例化时就需要依赖，无法提前暴露

// 解决方案：
// 方案1：改用字段注入或setter注入
// 方案2：使用@Lazy延迟注入
@Component
public class A {
    private B b;
    
    @Autowired
    public A(@Lazy B b) {
        this.b = b;
    }
}

// 2. 原型Bean循环依赖（无法解决）
@Component
@Scope("prototype")
public class A {
    @Autowired
    private B b;
}

@Component
@Scope("prototype")
public class B {
    @Autowired
    private A a;
}

// ❌ 报错：原型Bean不缓存，每次创建新对象
// 原因：三级缓存只对单例Bean有效
```

---

### Q5: @Component vs @Bean？（⭐⭐⭐⭐）

**本质区别**：
```
@Component：
  - 类级别注解
  - 组件扫描自动发现
  - Spring管理Bean的生命周期
  - 一个类只能创建一个Bean
  
@Bean：
  - 方法级别注解
  - 手动配置Bean
  - 可以使用Java代码自定义创建逻辑
  - 一个类可以创建多个Bean
```

**使用示例**：
```java
// @Component：自动扫描
@Component
public class UserService {
    @Autowired
    private UserDao userDao;
}

// @Bean：手动配置
@Configuration
public class AppConfig {
    
    @Bean
    public UserService userService() {
        UserService service = new UserService();
        service.setUserDao(userDao());
        // 可以添加自定义逻辑
        return service;
    }
    
    @Bean
    public UserDao userDao() {
        return new UserDaoImpl();
    }
}
```

**选择建议**：
```
使用 @Component：
  ✅ 自己编写的类
  ✅ 一个类一个Bean
  ✅ 无需复杂初始化
  
使用 @Bean：
  ✅ 第三方类（如DataSource）
  ✅ 需要复杂初始化逻辑
  ✅ 一个类创建多个Bean
  ✅ 条件化创建Bean（@Conditional）

示例：配置数据源
@Bean
public DataSource dataSource() {
    DruidDataSource ds = new DruidDataSource();
    ds.setUrl(url);
    ds.setUsername(username);
    ds.setPassword(password);
    ds.setInitialSize(10);
    ds.setMaxActive(50);
    // 复杂配置...
    return ds;
}
```

---

## AOP面向切面编程

### Q6: AOP的实现原理？（⭐⭐⭐⭐⭐）

**AOP核心概念**：
```
AOP术语：

1. 切面（Aspect）：
   - 横切关注点的模块化
   - 例：日志、事务、安全

2. 连接点（JoinPoint）：
   - 程序执行的某个点
   - 例：方法调用、异常抛出

3. 切点（Pointcut）：
   - 匹配连接点的表达式
   - 例：execution(* com.example.service.*.*(..))

4. 通知（Advice）：
   - 切面在切点执行的动作
   - 类型：Before、After、AfterReturning、AfterThrowing、Around

5. 目标对象（Target）：
   - 被代理的对象

6. 代理对象（Proxy）：
   - AOP创建的对象
   - 包含了切面逻辑

7. 织入（Weaving）：
   - 将切面应用到目标对象的过程
   - 时机：编译期、类加载期、运行期
```

**Spring AOP实现方式**：
```
1. JDK动态代理：
   - 基于接口
   - 使用java.lang.reflect.Proxy
   - 目标对象必须实现接口

2. CGLIB代理：
   - 基于继承
   - 生成目标类的子类
   - 无需接口
   - final类和final方法无法代理
```

**JDK动态代理示例**：
```java
// 1. 定义接口
public interface UserService {
    void save(User user);
}

// 2. 实现类
public class UserServiceImpl implements UserService {
    @Override
    public void save(User user) {
        System.out.println("保存用户：" + user.getName());
    }
}

// 3. InvocationHandler
public class LogInvocationHandler implements InvocationHandler {
    private Object target;
    
    public LogInvocationHandler(Object target) {
        this.target = target;
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        System.out.println("方法执行前：" + method.getName());
        Object result = method.invoke(target, args);
        System.out.println("方法执行后：" + method.getName());
        return result;
    }
}

// 4. 创建代理
UserService target = new UserServiceImpl();
UserService proxy = (UserService) Proxy.newProxyInstance(
    target.getClass().getClassLoader(),
    target.getClass().getInterfaces(),
    new LogInvocationHandler(target)
);

proxy.save(new User("张三"));

// 输出：
// 方法执行前：save
// 保存用户：张三
// 方法执行后：save
```

**CGLIB代理示例**：
```java
// 1. 目标类（无接口）
public class UserService {
    public void save(User user) {
        System.out.println("保存用户：" + user.getName());
    }
}

// 2. MethodInterceptor
public class LogMethodInterceptor implements MethodInterceptor {
    @Override
    public Object intercept(Object obj, Method method, Object[] args, MethodProxy proxy) 
            throws Throwable {
        System.out.println("方法执行前：" + method.getName());
        Object result = proxy.invokeSuper(obj, args);  // 调用父类方法
        System.out.println("方法执行后：" + method.getName());
        return result;
    }
}

// 3. 创建代理
Enhancer enhancer = new Enhancer();
enhancer.setSuperclass(UserService.class);
enhancer.setCallback(new LogMethodInterceptor());
UserService proxy = (UserService) enhancer.create();

proxy.save(new User("张三"));
```

**JDK动态代理 vs CGLIB**：

| 对比项 | JDK动态代理 | CGLIB |
|--------|-------------|-------|
| 实现方式 | 接口代理 | 继承代理 |
| 是否需要接口 | ✅ 必须 | ❌ 不需要 |
| final类 | - | ❌ 无法代理 |
| final方法 | - | ❌ 无法代理 |
| 性能 | 调用稍快 | 创建代理快 |
| Spring默认 | 有接口时 | 无接口时 |

**Spring AOP源码分析**：
```java
// AbstractAutoProxyCreator.postProcessAfterInitialization()
@Override
public Object postProcessAfterInitialization(Object bean, String beanName) {
    if (bean != null) {
        Object cacheKey = getCacheKey(bean.getClass(), beanName);
        if (!this.earlyProxyReferences.contains(cacheKey)) {
            return wrapIfNecessary(bean, beanName, cacheKey);  // 创建代理
        }
    }
    return bean;
}

// 创建代理
protected Object wrapIfNecessary(Object bean, String beanName, Object cacheKey) {
    // 1. 获取所有适用的Advisor
    Object[] specificInterceptors = getAdvicesAndAdvisorsForBean(
        bean.getClass(), beanName, null);
    
    if (specificInterceptors != DO_NOT_PROXY) {
        this.advisedBeans.put(cacheKey, Boolean.TRUE);
        // 2. 创建代理
        Object proxy = createProxy(
            bean.getClass(), beanName, specificInterceptors, new SingletonTargetSource(bean));
        this.proxyTypes.put(cacheKey, proxy.getClass());
        return proxy;
    }
    
    return bean;
}

// 决定使用哪种代理
protected Object createProxy(Class<?> beanClass, String beanName,
        Object[] specificInterceptors, TargetSource targetSource) {
    
    ProxyFactory proxyFactory = new ProxyFactory();
    
    if (!proxyFactory.isProxyTargetClass()) {
        // 判断是否有接口
        if (shouldProxyTargetClass(beanClass, beanName)) {
            proxyFactory.setProxyTargetClass(true);  // CGLIB
        } else {
            evaluateProxyInterfaces(beanClass, proxyFactory);  // JDK动态代理
        }
    }
    
    return proxyFactory.getProxy(getProxyClassLoader());
}
```

---

### Q7: 切点表达式详解？（⭐⭐⭐⭐）

**execution表达式语法**：
```
execution(modifiers-pattern? 
          ret-type-pattern 
          declaring-type-pattern?
          name-pattern(param-pattern)
          throws-pattern?)

说明：
  - modifiers-pattern：访问修饰符（可选）
  - ret-type-pattern：返回类型（必填）
  - declaring-type-pattern：类路径（可选）
  - name-pattern：方法名（必填）
  - param-pattern：参数类型（必填）
  - throws-pattern：异常类型（可选）
  - ?表示可选
  - *表示通配符
  - ..表示任意参数
```

**常用示例**：
```java
// 1. 匹配所有public方法
execution(public * *(..))

// 2. 匹配所有save开头的方法
execution(* save*(..))

// 3. 匹配service包下所有类的所有方法
execution(* com.example.service.*.*(..))

// 4. 匹配service包及子包下所有类的所有方法
execution(* com.example.service..*.*(..))

// 5. 匹配UserService类的所有方法
execution(* com.example.service.UserService.*(..))

// 6. 匹配第一个参数为String的方法
execution(* *(String, ..))

// 7. 匹配只有一个参数且为String的方法
execution(* *(String))

// 8. 匹配无参方法
execution(* *())

// 9. 匹配返回User类型的方法
execution(com.example.entity.User *(..))

// 10. 组合条件（且）
execution(public * com.example.service.*.*(..))

// 11. 组合条件（或）
@Pointcut("execution(* com.example.service.*.*(..)) || " +
          "execution(* com.example.controller.*.*(..))")

// 12. 组合条件（非）
@Pointcut("execution(* com.example.service.*.*(..)) && " +
          "!execution(* com.example.service.UserService.*(..))")
```

**其他切点表达式**：
```java
// @annotation：匹配带有指定注解的方法
@Pointcut("@annotation(com.example.annotation.Log)")

// @within：匹配带有指定注解的类
@Pointcut("@within(org.springframework.stereotype.Service)")

// within：匹配指定类型
@Pointcut("within(com.example.service..*)")

// args：匹配参数类型
@Pointcut("args(String, int)")

// @args：匹配参数带有指定注解
@Pointcut("@args(com.example.annotation.Validated)")

// this：匹配代理对象类型
@Pointcut("this(com.example.service.UserService)")

// target：匹配目标对象类型
@Pointcut("target(com.example.service.UserService)")

// bean：匹配Bean名称
@Pointcut("bean(userService)")
@Pointcut("bean(*Service)")  // 所有以Service结尾的Bean
```

**实战示例**：
```java
@Aspect
@Component
public class LogAspect {
    
    // 切点：service包下所有类的所有方法
    @Pointcut("execution(* com.example.service..*.*(..))")
    public void servicePointcut() {}
    
    // 切点：带@Log注解的方法
    @Pointcut("@annotation(com.example.annotation.Log)")
    public void logPointcut() {}
    
    // 前置通知
    @Before("servicePointcut()")
    public void before(JoinPoint joinPoint) {
        String methodName = joinPoint.getSignature().getName();
        Object[] args = joinPoint.getArgs();
        System.out.println("方法" + methodName + "开始执行，参数：" + Arrays.toString(args));
    }
    
    // 后置通知
    @AfterReturning(pointcut = "servicePointcut()", returning = "result")
    public void afterReturning(JoinPoint joinPoint, Object result) {
        String methodName = joinPoint.getSignature().getName();
        System.out.println("方法" + methodName + "执行成功，返回值：" + result);
    }
    
    // 异常通知
    @AfterThrowing(pointcut = "servicePointcut()", throwing = "ex")
    public void afterThrowing(JoinPoint joinPoint, Exception ex) {
        String methodName = joinPoint.getSignature().getName();
        System.out.println("方法" + methodName + "执行异常：" + ex.getMessage());
    }
    
    // 最终通知
    @After("servicePointcut()")
    public void after(JoinPoint joinPoint) {
        String methodName = joinPoint.getSignature().getName();
        System.out.println("方法" + methodName + "执行结束");
    }
    
    // 环绕通知
    @Around("servicePointcut()")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        long startTime = System.currentTimeMillis();
        
        System.out.println("方法" + methodName + "开始执行");
        
        Object result = null;
        try {
            result = joinPoint.proceed();  // 执行目标方法
            System.out.println("方法" + methodName + "执行成功");
        } catch (Throwable e) {
            System.out.println("方法" + methodName + "执行异常：" + e.getMessage());
            throw e;
        } finally {
            long endTime = System.currentTimeMillis();
            System.out.println("方法" + methodName + "执行耗时：" + (endTime - startTime) + "ms");
        }
        
        return result;
    }
}
```

---

## Spring事务管理

### Q8: Spring事务传播机制？（⭐⭐⭐⭐⭐）

**7种传播行为**：

**1. REQUIRED（默认）**：
```java
@Transactional(propagation = Propagation.REQUIRED)
public void methodA() {
    // ...
    methodB();
}

@Transactional(propagation = Propagation.REQUIRED)
public void methodB() {
    // ...
}

行为：
  - 如果当前有事务，加入该事务
  - 如果当前没有事务，创建新事务
  
场景：
  methodA调用methodB：
    - methodA有事务
    - methodB加入methodA的事务
    - 两个方法在同一个事务中
    - methodB抛异常，methodA也回滚
```

**2. SUPPORTS**：
```java
@Transactional(propagation = Propagation.SUPPORTS)
public void methodB() {
    // ...
}

行为：
  - 如果当前有事务，加入该事务
  - 如果当前没有事务，以非事务方式执行
  
场景：
  - 查询方法可以使用
  - 有事务就用，没事务也行
```

**3. MANDATORY**：
```java
@Transactional(propagation = Propagation.MANDATORY)
public void methodB() {
    // ...
}

行为：
  - 如果当前有事务，加入该事务
  - 如果当前没有事务，抛异常
  
场景：
  - 强制要求在事务中执行
  - 防止被非事务方法调用
```

**4. REQUIRES_NEW**：
```java
@Transactional(propagation = Propagation.REQUIRED)
public void methodA() {
    // 事务A
    methodB();  // 挂起事务A，创建事务B
    // 事务A继续
}

@Transactional(propagation = Propagation.REQUIRES_NEW)
public void methodB() {
    // 事务B（独立）
}

行为：
  - 总是创建新事务
  - 如果当前有事务，挂起当前事务
  
场景：
  - 日志记录（无论主事务是否回滚，日志都要保存）
  - 积分系统（下单失败，积分照样扣）

示例：
@Transactional
public void createOrder(Order order) {
    orderDao.insert(order);  // 事务A
    
    // 记录日志（独立事务）
    logService.saveLog(log);  // 事务B
    
    if (someCondition) {
        throw new RuntimeException();  // 事务A回滚
    }
    // 事务A回滚，但日志已保存（事务B已提交）✅
}

@Transactional(propagation = Propagation.REQUIRES_NEW)
public void saveLog(Log log) {
    logDao.insert(log);  // 独立事务
}
```

**5. NOT_SUPPORTED**：
```java
@Transactional(propagation = Propagation.NOT_SUPPORTED)
public void methodB() {
    // 以非事务方式执行
}

行为：
  - 总是以非事务方式执行
  - 如果当前有事务，挂起当前事务
  
场景：
  - 查询大量数据（不需要事务）
  - 批量处理（不需要事务保护）
```

**6. NEVER**：
```java
@Transactional(propagation = Propagation.NEVER)
public void methodB() {
    // ...
}

行为：
  - 总是以非事务方式执行
  - 如果当前有事务，抛异常
  
场景：
  - 严格要求非事务环境
```

**7. NESTED**：
```java
@Transactional(propagation = Propagation.REQUIRED)
public void methodA() {
    // 外部事务
    try {
        methodB();  // 嵌套事务（SavePoint）
    } catch (Exception e) {
        // methodB回滚，methodA可以继续
    }
}

@Transactional(propagation = Propagation.NESTED)
public void methodB() {
    // 嵌套事务
}

行为：
  - 如果当前有事务，创建嵌套事务（SavePoint）
  - 如果当前没有事务，等同于REQUIRED
  - 嵌套事务回滚不影响外部事务
  - 外部事务回滚会回滚嵌套事务
  
场景：
  - 批量处理（部分失败）
  - 主流程 + 子流程

示例：批量导入
@Transactional
public void batchImport(List<User> users) {
    for (User user : users) {
        try {
            importUser(user);  // 嵌套事务
        } catch (Exception e) {
            log.error("导入失败：" + user.getName());
            // 单个失败不影响其他
        }
    }
}

@Transactional(propagation = Propagation.NESTED)
public void importUser(User user) {
    userDao.insert(user);
    // 可能抛异常
}
```

**REQUIRES_NEW vs NESTED**：
```
REQUIRES_NEW：
  - 完全独立的事务
  - 不受外部事务影响
  - 外部事务回滚，内部事务不回滚
  
NESTED：
  - 嵌套事务（SavePoint）
  - 受外部事务影响
  - 外部事务回滚，内部事务也回滚
  - 内部事务回滚，外部事务可以不回滚

对比：
methodA {
    事务A开始
    methodB()
    事务A提交/回滚
}

REQUIRES_NEW：
  - methodB创建事务B
  - 事务B独立提交
  - methodA回滚不影响事务B
  
NESTED：
  - methodB创建SavePoint
  - methodB回滚到SavePoint
  - methodA回滚会回滚methodB
```

---

### Q9: @Transactional失效场景？（⭐⭐⭐⭐⭐）

**常见失效场景**：

**1. 方法不是public**：
```java
// ❌ 失效
@Transactional
protected void save(User user) {
    userDao.insert(user);
}

// ❌ 失效
@Transactional
private void save(User user) {
    userDao.insert(user);
}

// ✅ 有效
@Transactional
public void save(User user) {
    userDao.insert(user);
}

原因：
  - Spring AOP基于代理
  - 代理只能拦截public方法
  - protected/private方法无法被代理
```

**2. 方法内部调用**：
```java
@Service
public class UserService {
    
    // ❌ 事务失效
    public void methodA() {
        methodB();  // 内部调用，不走代理
    }
    
    @Transactional
    public void methodB() {
        userDao.insert(user);
    }
}

原因：
  - methodA直接调用methodB
  - 不经过代理对象
  - 事务失效

解决方案：
// 方案1：注入自己
@Service
public class UserService {
    @Autowired
    private UserService self;
    
    public void methodA() {
        self.methodB();  // 通过代理调用 ✅
    }
    
    @Transactional
    public void methodB() {
        userDao.insert(user);
    }
}

// 方案2：获取代理对象
public void methodA() {
    UserService proxy = (UserService) AopContext.currentProxy();
    proxy.methodB();  // 通过代理调用 ✅
}
// 需要配置：@EnableAspectJAutoProxy(exposeProxy = true)

// 方案3：拆分到不同类
@Service
public class UserService {
    @Autowired
    private UserServiceHelper helper;
    
    public void methodA() {
        helper.methodB();  // 调用其他类 ✅
    }
}

@Service
public class UserServiceHelper {
    @Transactional
    public void methodB() {
        userDao.insert(user);
    }
}
```

**3. 异常被捕获**：
```java
// ❌ 事务不回滚
@Transactional
public void save(User user) {
    try {
        userDao.insert(user);
        int i = 1 / 0;  // 抛异常
    } catch (Exception e) {
        e.printStackTrace();  // 异常被捕获
    }
}

// ✅ 正确做法1：重新抛出
@Transactional
public void save(User user) {
    try {
        userDao.insert(user);
        int i = 1 / 0;
    } catch (Exception e) {
        e.printStackTrace();
        throw e;  // 重新抛出
    }
}

// ✅ 正确做法2：手动回滚
@Transactional
public void save(User user) {
    try {
        userDao.insert(user);
        int i = 1 / 0;
    } catch (Exception e) {
        e.printStackTrace();
        TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
    }
}
```

**4. 异常类型不匹配**：
```java
// ❌ 默认只回滚RuntimeException和Error
@Transactional
public void save(User user) throws Exception {
    userDao.insert(user);
    if (someCondition) {
        throw new Exception("业务异常");  // 检查异常，不回滚
    }
}

// ✅ 指定回滚异常
@Transactional(rollbackFor = Exception.class)
public void save(User user) throws Exception {
    userDao.insert(user);
    if (someCondition) {
        throw new Exception("业务异常");  // 会回滚 ✅
    }
}

// 不回滚指定异常
@Transactional(noRollbackFor = BusinessException.class)
public void save(User user) {
    userDao.insert(user);
    if (someCondition) {
        throw new BusinessException();  // 不回滚
    }
}
```

**5. 数据库引擎不支持事务**：
```sql
-- ❌ MyISAM不支持事务
CREATE TABLE user (
    id INT PRIMARY KEY,
    name VARCHAR(50)
) ENGINE=MyISAM;

-- ✅ InnoDB支持事务
CREATE TABLE user (
    id INT PRIMARY KEY,
    name VARCHAR(50)
) ENGINE=InnoDB;
```

**6. 没有被Spring管理**：
```java
// ❌ new出来的对象，不是Spring Bean
UserService service = new UserService();
service.save(user);  // 事务失效

// ✅ 从Spring容器获取
@Autowired
private UserService service;

service.save(user);  // 事务生效
```

**7. 多线程调用**：
```java
// ❌ 事务失效
@Transactional
public void save(User user) {
    userDao.insert(user);
    
    new Thread(() -> {
        // 新线程，不在同一个事务中
        orderDao.insert(order);
    }).start();
}

原因：
  - Spring事务基于ThreadLocal
  - 不同线程有不同的事务
  - 子线程的操作不在事务中

解决方案：
  - 使用消息队列
  - 使用Spring的@Async（配合事务传播）
  - 使用TransactionTemplate编程式事务
```

**8. 传播行为配置错误**：
```java
// ❌ NOT_SUPPORTED：不使用事务
@Transactional(propagation = Propagation.NOT_SUPPORTED)
public void save(User user) {
    userDao.insert(user);
}

// ❌ NEVER：有事务就报错
@Transactional(propagation = Propagation.NEVER)
public void save(User user) {
    userDao.insert(user);
}
```

**9. final方法**（CGLIB代理）：
```java
@Service
public class UserService {
    // ❌ final方法无法被CGLIB代理
    @Transactional
    public final void save(User user) {
        userDao.insert(user);
    }
}

原因：
  - CGLIB基于继承
  - final方法无法被重写
  - 事务失效
```

**总结**：
```
@Transactional失效场景：
  1. 方法不是public ❌
  2. 方法内部调用 ❌
  3. 异常被捕获 ❌
  4. 异常类型不匹配（检查异常）❌
  5. 数据库引擎不支持事务 ❌
  6. 没有被Spring管理 ❌
  7. 多线程调用 ❌
  8. 传播行为配置错误 ❌
  9. final方法（CGLIB）❌
  10. 类没有被Spring代理 ❌

避免方案：
  ✅ public方法
  ✅ 通过代理调用
  ✅ 异常重新抛出或手动回滚
  ✅ rollbackFor = Exception.class
  ✅ 使用InnoDB引擎
  ✅ 使用Spring Bean
  ✅ 避免多线程
  ✅ 正确配置传播行为
  ✅ 避免final方法
```

---

## Spring MVC

### Q10: Spring MVC执行流程？（⭐⭐⭐⭐⭐）

**完整流程**：
```
1. 用户请求 → DispatcherServlet

2. DispatcherServlet → HandlerMapping
   - 查找Handler（Controller）

3. HandlerMapping → DispatcherServlet
   - 返回HandlerExecutionChain（Handler + Interceptors）

4. DispatcherServlet → HandlerAdapter
   - 选择合适的适配器

5. HandlerAdapter → Controller
   - 执行Controller方法

6. Controller → HandlerAdapter
   - 返回ModelAndView

7. HandlerAdapter → DispatcherServlet
   - 返回ModelAndView

8. DispatcherServlet → ViewResolver
   - 解析视图名称

9. ViewResolver → DispatcherServlet
   - 返回View对象

10. DispatcherServlet → View
    - 渲染视图

11. View → 用户
    - 返回响应
```

**核心组件**：
```
1. DispatcherServlet（前端控制器）：
   - 接收所有请求
   - 协调各组件工作
   - 统一异常处理

2. HandlerMapping（处理器映射器）：
   - 根据URL找到Handler
   - RequestMappingHandlerMapping（@RequestMapping）

3. HandlerAdapter（处理器适配器）：
   - 执行Handler
   - RequestMappingHandlerAdapter（@RequestMapping）

4. ViewResolver（视图解析器）：
   - 解析视图名称
   - InternalResourceViewResolver（JSP）
   - ThymeleafViewResolver（Thymeleaf）

5. View（视图）：
   - 渲染模型数据
   - InternalResourceView（JSP）
   - ThymeleafView（Thymeleaf）
```

**源码分析**：
```java
// DispatcherServlet.doDispatch()
protected void doDispatch(HttpServletRequest request, HttpServletResponse response) {
    HandlerExecutionChain mappedHandler = null;
    
    try {
        ModelAndView mv = null;
        Exception dispatchException = null;
        
        try {
            // 1. 检查是否文件上传
            processedRequest = checkMultipart(request);
            
            // 2. 获取Handler（Controller）
            mappedHandler = getHandler(processedRequest);
            if (mappedHandler == null) {
                noHandlerFound(processedRequest, response);
                return;
            }
            
            // 3. 获取HandlerAdapter
            HandlerAdapter ha = getHandlerAdapter(mappedHandler.getHandler());
            
            // 4. 执行拦截器preHandle
            if (!mappedHandler.applyPreHandle(processedRequest, response)) {
                return;
            }
            
            // 5. 执行Handler（Controller方法）
            mv = ha.handle(processedRequest, response, mappedHandler.getHandler());
            
            // 6. 设置默认视图名
            applyDefaultViewName(processedRequest, mv);
            
            // 7. 执行拦截器postHandle
            mappedHandler.applyPostHandle(processedRequest, response, mv);
            
        } catch (Exception ex) {
            dispatchException = ex;
        }
        
        // 8. 处理结果（渲染视图）
        processDispatchResult(processedRequest, response, mappedHandler, mv, dispatchException);
        
    } finally {
        // 9. 执行拦截器afterCompletion
        if (mappedHandler != null) {
            mappedHandler.triggerAfterCompletion(request, response, null);
        }
    }
}
```

---

### Q11: @RequestMapping详解？（⭐⭐⭐⭐）

**基本用法**：
```java
// 类级别
@RestController
@RequestMapping("/user")
public class UserController {
    
    // 方法级别
    @RequestMapping("/list")
    public List<User> list() {
        return userService.list();
    }
    
    // 完整路径：/user/list
}
```

**HTTP方法**：
```java
// 方式1：method属性
@RequestMapping(value = "/save", method = RequestMethod.POST)
public void save(@RequestBody User user) {
    userService.save(user);
}

// 方式2：组合注解（推荐）
@GetMapping("/list")      // GET请求
@PostMapping("/save")     // POST请求
@PutMapping("/update")    // PUT请求
@DeleteMapping("/delete") // DELETE请求
@PatchMapping("/patch")   // PATCH请求
```

**参数绑定**：
```java
// 1. @PathVariable：路径变量
@GetMapping("/user/{id}")
public User getById(@PathVariable Long id) {
    return userService.getById(id);
}
// 请求：GET /user/123

// 2. @RequestParam：请求参数
@GetMapping("/user")
public User getByName(@RequestParam String name) {
    return userService.getByName(name);
}
// 请求：GET /user?name=zhangsan

// 可选参数
@GetMapping("/user")
public List<User> list(@RequestParam(required = false) String name) {
    return userService.list(name);
}

// 默认值
@GetMapping("/user")
public List<User> list(@RequestParam(defaultValue = "1") int page) {
    return userService.list(page);
}

// 3. @RequestBody：请求体（JSON）
@PostMapping("/user")
public void save(@RequestBody User user) {
    userService.save(user);
}
// 请求：POST /user
// Content-Type: application/json
// {"name":"zhangsan","age":20}

// 4. @RequestHeader：请求头
@GetMapping("/user")
public void get(@RequestHeader("Authorization") String token) {
    // ...
}

// 5. @CookieValue：Cookie
@GetMapping("/user")
public void get(@CookieValue("JSESSIONID") String sessionId) {
    // ...
}

// 6. HttpServletRequest/HttpServletResponse
@GetMapping("/user")
public void get(HttpServletRequest request, HttpServletResponse response) {
    String name = request.getParameter("name");
    // ...
}
```

**参数校验**：
```java
@PostMapping("/user")
public void save(@RequestBody @Validated User user) {
    userService.save(user);
}

public class User {
    @NotNull(message = "姓名不能为空")
    private String name;
    
    @Min(value = 0, message = "年龄不能小于0")
    @Max(value = 150, message = "年龄不能大于150")
    private Integer age;
    
    @Email(message = "邮箱格式不正确")
    private String email;
}
```

**返回值类型**：
```java
// 1. 对象（自动转JSON）
@GetMapping("/user/{id}")
public User getById(@PathVariable Long id) {
    return userService.getById(id);
}

// 2. ResponseEntity（自定义状态码、头）
@GetMapping("/user/{id}")
public ResponseEntity<User> getById(@PathVariable Long id) {
    User user = userService.getById(id);
    if (user == null) {
        return ResponseEntity.notFound().build();
    }
    return ResponseEntity.ok(user);
}

// 3. void（无返回值）
@DeleteMapping("/user/{id}")
public void delete(@PathVariable Long id) {
    userService.deleteById(id);
}

// 4. String（视图名）
@GetMapping("/user/edit")
public String edit(Model model) {
    model.addAttribute("title", "编辑用户");
    return "user/edit";  // 返回视图名
}

// 5. ModelAndView
@GetMapping("/user/list")
public ModelAndView list() {
    ModelAndView mv = new ModelAndView();
    mv.setViewName("user/list");
    mv.addObject("users", userService.list());
    return mv;
}
```

---

## Spring Boot

### Q12: Spring Boot自动配置原理？（⭐⭐⭐⭐⭐）

**核心注解**：
```java
@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

// @SpringBootApplication = 
//   @SpringBootConfiguration + 
//   @EnableAutoConfiguration + 
//   @ComponentScan
```

**@EnableAutoConfiguration原理**：
```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@AutoConfigurationPackage
@Import(AutoConfigurationImportSelector.class)  // 核心
public @interface EnableAutoConfiguration {
}
```

**AutoConfigurationImportSelector**：
```java
public class AutoConfigurationImportSelector {
    
    @Override
    public String[] selectImports(AnnotationMetadata annotationMetadata) {
        // 1. 判断是否开启自动配置
        if (!isEnabled(annotationMetadata)) {
            return NO_IMPORTS;
        }
        
        // 2. 获取所有自动配置类
        AutoConfigurationEntry autoConfigurationEntry = 
            getAutoConfigurationEntry(annotationMetadata);
        
        return StringUtils.toStringArray(autoConfigurationEntry.getConfigurations());
    }
    
    protected AutoConfigurationEntry getAutoConfigurationEntry(AnnotationMetadata annotationMetadata) {
        // 1. 加载 META-INF/spring.factories
        List<String> configurations = getCandidateConfigurations(annotationMetadata, attributes);
        
        // 2. 去重
        configurations = removeDuplicates(configurations);
        
        // 3. 排除（exclude）
        Set<String> exclusions = getExclusions(annotationMetadata, attributes);
        configurations.removeAll(exclusions);
        
        // 4. 过滤（@Conditional）
        configurations = filter(configurations, autoConfigurationMetadata);
        
        return new AutoConfigurationEntry(configurations, exclusions);
    }
}
```

**spring.factories**：
```properties
# spring-boot-autoconfigure/META-INF/spring.factories

org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
org.springframework.boot.autoconfigure.admin.SpringApplicationAdminJmxAutoConfiguration,\
org.springframework.boot.autoconfigure.aop.AopAutoConfiguration,\
org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration,\
org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration,\
...
```

**自动配置类示例**：
```java
// RedisAutoConfiguration
@Configuration
@ConditionalOnClass(RedisOperations.class)  // 类路径有RedisOperations才生效
@EnableConfigurationProperties(RedisProperties.class)  // 绑定配置
public class RedisAutoConfiguration {
    
    @Bean
    @ConditionalOnMissingBean(name = "redisTemplate")  // 没有redisTemplate才创建
    public RedisTemplate<Object, Object> redisTemplate(
            RedisConnectionFactory redisConnectionFactory) {
        RedisTemplate<Object, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(redisConnectionFactory);
        return template;
    }
    
    @Bean
    @ConditionalOnMissingBean
    public StringRedisTemplate stringRedisTemplate(
            RedisConnectionFactory redisConnectionFactory) {
        StringRedisTemplate template = new StringRedisTemplate();
        template.setConnectionFactory(redisConnectionFactory);
        return template;
    }
}

// RedisProperties
@ConfigurationProperties(prefix = "spring.redis")
public class RedisProperties {
    private String host = "localhost";
    private int port = 6379;
    private String password;
    private int database = 0;
    // getter/setter...
}
```

**@Conditional注解**：
```java
// 常用条件注解

@ConditionalOnClass          // 类路径存在指定类
@ConditionalOnMissingClass   // 类路径不存在指定类
@ConditionalOnBean           // 容器中存在指定Bean
@ConditionalOnMissingBean    // 容器中不存在指定Bean
@ConditionalOnProperty       // 配置文件存在指定属性
@ConditionalOnResource       // 类路径存在指定资源
@ConditionalOnWebApplication // Web应用
@ConditionalOnNotWebApplication // 非Web应用

// 示例
@Configuration
@ConditionalOnClass(DataSource.class)  // 有DataSource类
@ConditionalOnProperty(name = "spring.datasource.url")  // 配置了URL
public class DataSourceAutoConfiguration {
    
    @Bean
    @ConditionalOnMissingBean  // 用户没有自定义DataSource
    public DataSource dataSource(DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder().build();
    }
}
```

**自定义Starter**：
```
步骤：

1. 创建spring-boot-starter-xxx项目

2. 创建XxxAutoConfiguration类：
   @Configuration
   @ConditionalOnClass(Xxx.class)
   @EnableConfigurationProperties(XxxProperties.class)
   public class XxxAutoConfiguration {
       @Bean
       @ConditionalOnMissingBean
       public Xxx xxx(XxxProperties properties) {
           return new Xxx(properties);
       }
   }

3. 创建XxxProperties类：
   @ConfigurationProperties(prefix = "xxx")
   public class XxxProperties {
       private String name;
       private int port;
       // getter/setter...
   }

4. 创建META-INF/spring.factories：
   org.springframework.boot.autoconfigure.EnableAutoConfiguration=\
   com.example.autoconfigure.XxxAutoConfiguration

5. 使用：
   <dependency>
       <groupId>com.example</groupId>
       <artifactId>spring-boot-starter-xxx</artifactId>
   </dependency>
   
   application.properties：
   xxx.name=test
   xxx.port=8080
```

---

## Spring Cloud

### Q13: Spring Cloud核心组件？（⭐⭐⭐⭐）

**核心组件**：
```
1. Eureka/Nacos：服务注册与发现
2. Ribbon：客户端负载均衡
3. Feign/OpenFeign：声明式HTTP客户端
4. Hystrix/Sentinel：服务熔断降级
5. Gateway/Zuul：API网关
6. Config：配置中心
7. Sleuth+Zipkin：链路追踪
```

**服务注册与发现**：
```java
// 1. 注册中心（Eureka Server）
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}

// 2. 服务提供者（Eureka Client）
@SpringBootApplication
@EnableEurekaClient  // 或 @EnableDiscoveryClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}

// application.yml
eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
  instance:
    prefer-ip-address: true

spring:
  application:
    name: user-service
```

**负载均衡（Ribbon）**：
```java
@Configuration
public class RibbonConfig {
    
    @Bean
    @LoadBalanced  // 开启负载均衡
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}

@Service
public class OrderService {
    @Autowired
    private RestTemplate restTemplate;
    
    public User getUser(Long userId) {
        // user-service是服务名，Ribbon会负载均衡
        return restTemplate.getForObject(
            "http://user-service/user/" + userId,
            User.class
        );
    }
}

// 负载均衡策略
@Configuration
public class RibbonConfig {
    
    @Bean
    public IRule ribbonRule() {
        return new RandomRule();  // 随机
        // return new RoundRobinRule();  // 轮询（默认）
        // return new RetryRule();  // 重试
        // return new WeightedResponseTimeRule();  // 响应时间加权
    }
}
```

**Feign声明式调用**：
```java
// 1. 启用Feign
@SpringBootApplication
@EnableFeignClients
public class OrderServiceApplication {
}

// 2. 定义Feign Client
@FeignClient(name = "user-service", fallback = UserServiceFallback.class)
public interface UserServiceClient {
    
    @GetMapping("/user/{id}")
    User getById(@PathVariable("id") Long id);
    
    @PostMapping("/user")
    void save(@RequestBody User user);
}

// 3. 使用
@Service
public class OrderService {
    @Autowired
    private UserServiceClient userServiceClient;
    
    public void createOrder(Long userId) {
        User user = userServiceClient.getById(userId);
        // ...
    }
}

// 4. 降级处理
@Component
public class UserServiceFallback implements UserServiceClient {
    
    @Override
    public User getById(Long id) {
        return new User();  // 返回默认值
    }
    
    @Override
    public void save(User user) {
        // 记录日志
    }
}
```

**API网关（Gateway）**：
```java
// 路由配置
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service  // lb:负载均衡
          predicates:
            - Path=/user/**
          filters:
            - StripPrefix=1
            
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/order/**
          filters:
            - AddRequestHeader=X-Request-Id, ${random.uuid}

// 自定义过滤器
@Component
public class AuthFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String token = exchange.getRequest().getHeaders().getFirst("Authorization");
        
        if (token == null) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        return chain.filter(exchange);
    }
    
    @Override
    public int getOrder() {
        return -100;  // 优先级
    }
}
```

---

## 💡 面试技巧

### 答题思路
```
1. 先答要点：
   - 简明扼要说核心概念
   
2. 原理解析：
   - 底层实现原理
   - 源码分析
   
3. 举例说明：
   - 代码示例
   - 实际应用场景
   
4. 对比分析：
   - 与其他方案对比
   - 优缺点
   
5. 注意事项：
   - 常见坑点
   - 最佳实践
```

### 高频考点总结
```
⭐⭐⭐⭐⭐（必考）：
  - IoC和DI
  - Bean生命周期
  - AOP实现原理
  - 事务传播机制
  - @Transactional失效场景
  - 循环依赖
  - Spring MVC执行流程
  - Spring Boot自动配置

⭐⭐⭐⭐（高频）：
  - @Autowired vs @Resource
  - JDK动态代理 vs CGLIB
  - 切点表达式
  - 事务隔离级别
  - @RequestMapping详解
  - Spring Cloud组件

⭐⭐⭐（中频）：
  - @Component vs @Bean
  - Feign原理
  - Gateway路由
  - 配置中心
```

---

## 📖 相关文档

- [02_Spring生态/Spring核心原理](../../02_Spring生态/)
- [23_源码解读/Spring核心源码解析](../../23_源码解读/Spring核心源码解析.md)
- [Java基础面试题](./Java基础面试题.md)

---

**最后更新**: 2025-10-29  
**文档状态**: ✅ 完整内容已完成（1100+行）

💡 **记住**: Spring是Java后端开发的核心框架，必须深入掌握！



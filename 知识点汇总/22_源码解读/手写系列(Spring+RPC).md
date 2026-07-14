# 手写系列(Spring+RPC)

> 从零实现IoC容器、AOP、RPC框架，深入理解核心原理

---

## 📋 目录

- [1. 手写IoC容器](#1-手写ioc容器)
- [2. 手写AOP](#2-手写aop)
- [3. 手写RPC框架](#3-手写rpc框架)
- [4. 进阶扩展](#4-进阶扩展)

---

## 🎯 学习目标

- ✅ 实现Bean工厂与依赖注入
- ✅ 实现JDK动态代理和CGLIB代理
- ✅ 实现RPC远程调用
- ✅ 实现服务注册与发现
- ✅ 理解框架核心设计思想

---

## 1. 手写IoC容器

### 1.1 核心接口设计

**BeanFactory接口**：
```java
public interface BeanFactory {
    Object getBean(String name);
    <T> T getBean(String name, Class<T> requiredType);
    <T> T getBean(Class<T> requiredType);
}
```

**BeanDefinition（Bean定义）**：
```java
public class BeanDefinition {
    private String beanName;
    private Class<?> beanClass;
    private String scope = "singleton";
    private PropertyValues propertyValues;
    
    // getter/setter...
}
```

### 1.2 实现Bean工厂

**SimpleBeanFactory**：
```java
public class SimpleBeanFactory implements BeanFactory {
    // Bean定义注册表
    private Map<String, BeanDefinition> beanDefinitionMap = new ConcurrentHashMap<>();
    
    // 单例Bean缓存
    private Map<String, Object> singletonObjects = new ConcurrentHashMap<>();
    
    // 注册BeanDefinition
    public void registerBeanDefinition(String beanName, BeanDefinition beanDefinition) {
        beanDefinitionMap.put(beanName, beanDefinition);
    }
    
    @Override
    public Object getBean(String name) {
        // 1. 先从单例缓存获取
        Object singleton = singletonObjects.get(name);
        if (singleton != null) {
            return singleton;
        }
        
        // 2. 获取BeanDefinition
        BeanDefinition beanDefinition = beanDefinitionMap.get(name);
        if (beanDefinition == null) {
            throw new RuntimeException("Bean not found: " + name);
        }
        
        // 3. 创建Bean
        Object bean = createBean(beanDefinition);
        
        // 4. 如果是单例，放入缓存
        if ("singleton".equals(beanDefinition.getScope())) {
            singletonObjects.put(name, bean);
        }
        
        return bean;
    }
    
    private Object createBean(BeanDefinition beanDefinition) {
        try {
            // 1. 实例化
            Object bean = beanDefinition.getBeanClass().newInstance();
            
            // 2. 属性注入
            populateBean(bean, beanDefinition);
            
            return bean;
        } catch (Exception e) {
            throw new RuntimeException("Failed to create bean: " + beanDefinition.getBeanName(), e);
        }
    }
    
    private void populateBean(Object bean, BeanDefinition beanDefinition) {
        // 通过反射注入属性
        for (PropertyValue pv : beanDefinition.getPropertyValues().getPropertyValues()) {
            try {
                Field field = bean.getClass().getDeclaredField(pv.getName());
                field.setAccessible(true);
                
                // 如果是Bean引用，递归获取
                Object value = pv.getValue();
                if (value instanceof BeanReference) {
                    value = getBean(((BeanReference) value).getBeanName());
                }
                
                field.set(bean, value);
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
```

### 1.3 注解扫描

**ComponentScan注解**：
```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface ComponentScan {
    String value() default "";
}

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Component {
    String value() default "";
}

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Autowired {
}
```

**注解扫描器**：
```java
public class ClassPathBeanDefinitionScanner {
    private BeanFactory beanFactory;
    
    public void scan(String basePackage) {
        // 1. 扫描包下所有class文件
        Set<Class<?>> classes = scanPackage(basePackage);
        
        // 2. 筛选出有@Component的类
        for (Class<?> clazz : classes) {
            if (clazz.isAnnotationPresent(Component.class)) {
                Component component = clazz.getAnnotation(Component.class);
                String beanName = component.value();
                if (beanName.isEmpty()) {
                    beanName = lowerFirstCase(clazz.getSimpleName());
                }
                
                // 3. 注册BeanDefinition
                BeanDefinition beanDefinition = new BeanDefinition();
                beanDefinition.setBeanName(beanName);
                beanDefinition.setBeanClass(clazz);
                
                beanFactory.registerBeanDefinition(beanName, beanDefinition);
            }
        }
    }
    
    private Set<Class<?>> scanPackage(String basePackage) {
        Set<Class<?>> classes = new HashSet<>();
        String packagePath = basePackage.replace(".", "/");
        
        try {
            URL url = Thread.currentThread().getContextClassLoader().getResource(packagePath);
            File packageDir = new File(url.getFile());
            
            for (File file : packageDir.listFiles()) {
                if (file.isDirectory()) {
                    scanPackage(basePackage + "." + file.getName());
                } else if (file.getName().endsWith(".class")) {
                    String className = basePackage + "." + file.getName().replace(".class", "");
                    classes.add(Class.forName(className));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        return classes;
    }
}
```

---

## 2. 手写AOP

### 2.1 JDK动态代理

```java
public class JdkDynamicProxy implements InvocationHandler {
    private Object target;
    
    public Object getProxy(Object target) {
        this.target = target;
        return Proxy.newProxyInstance(
            target.getClass().getClassLoader(),
            target.getClass().getInterfaces(),
            this
        );
    }
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        // 前置增强
        before();
        
        // 执行原方法
        Object result = method.invoke(target, args);
        
        // 后置增强
        after();
        
        return result;
    }
    
    private void before() {
        System.out.println("前置增强...");
    }
    
    private void after() {
        System.out.println("后置增强...");
    }
}
```

### 2.2 CGLIB代理

```java
public class CglibProxy implements MethodInterceptor {
    
    public Object getProxy(Class<?> clazz) {
        Enhancer enhancer = new Enhancer();
        enhancer.setSuperclass(clazz);
        enhancer.setCallback(this);
        return enhancer.create();
    }
    
    @Override
    public Object intercept(Object obj, Method method, Object[] args, MethodProxy proxy) throws Throwable {
        before();
        Object result = proxy.invokeSuper(obj, args);
        after();
        return result;
    }
}
```

---

## 3. 手写RPC框架

### 3.1 整体架构

```
Client端
├── Proxy（动态代理）
├── Serialize（序列化）
├── NettyClient（网络通信）
└── Registry（服务发现）

Server端
├── NettyServer（网络通信）
├── Deserialize（反序列化）
├── ServiceProvider（服务提供者）
└── Registry（服务注册）
```

### 3.2 定义协议

**RpcRequest（请求）**：
```java
@Data
public class RpcRequest implements Serializable {
    private String requestId;      // 请求ID
    private String className;      // 类名
    private String methodName;     // 方法名
    private Class<?>[] parameterTypes;  // 参数类型
    private Object[] parameters;   // 参数值
}
```

**RpcResponse（响应）**：
```java
@Data
public class RpcResponse implements Serializable {
    private String requestId;
    private Object result;
    private Throwable error;
}
```

### 3.3 客户端代理

**RpcClientProxy**：
```java
public class RpcClientProxy implements InvocationHandler {
    private String host;
    private int port;
    
    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        // 1. 构建请求
        RpcRequest request = new RpcRequest();
        request.setRequestId(UUID.randomUUID().toString());
        request.setClassName(method.getDeclaringClass().getName());
        request.setMethodName(method.getName());
        request.setParameterTypes(method.getParameterTypes());
        request.setParameters(args);
        
        // 2. 发送请求
        RpcClient client = new RpcClient(host, port);
        RpcResponse response = client.send(request);
        
        // 3. 返回结果
        if (response.getError() != null) {
            throw response.getError();
        }
        return response.getResult();
    }
    
    @SuppressWarnings("unchecked")
    public <T> T getProxy(Class<T> clazz) {
        return (T) Proxy.newProxyInstance(
            clazz.getClassLoader(),
            new Class<?>[]{clazz},
            this
        );
    }
}
```

### 3.4 Netty Client

```java
public class RpcClient {
    private String host;
    private int port;
    
    public RpcResponse send(RpcRequest request) {
        EventLoopGroup group = new NioEventLoopGroup();
        RpcClientHandler handler = new RpcClientHandler();
        
        try {
            Bootstrap bootstrap = new Bootstrap();
            bootstrap.group(group)
                .channel(NioSocketChannel.class)
                .handler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ch.pipeline()
                            .addLast(new ObjectEncoder())
                            .addLast(new ObjectDecoder(ClassResolvers.cacheDisabled(null)))
                            .addLast(handler);
                    }
                });
            
            // 连接服务器
            ChannelFuture future = bootstrap.connect(host, port).sync();
            
            // 发送请求
            future.channel().writeAndFlush(request).sync();
            future.channel().closeFuture().sync();
            
            return handler.getResponse();
        } catch (Exception e) {
            throw new RuntimeException(e);
        } finally {
            group.shutdownGracefully();
        }
    }
}

public class RpcClientHandler extends SimpleChannelInboundHandler<RpcResponse> {
    private RpcResponse response;
    
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, RpcResponse msg) {
        this.response = msg;
    }
    
    public RpcResponse getResponse() {
        return response;
    }
}
```

### 3.5 Netty Server

```java
public class RpcServer {
    private int port;
    private Map<String, Object> serviceMap = new ConcurrentHashMap<>();
    
    // 注册服务
    public void registerService(Class<?> interfaceClass, Object serviceBean) {
        serviceMap.put(interfaceClass.getName(), serviceBean);
    }
    
    public void start() throws Exception {
        EventLoopGroup bossGroup = new NioEventLoopGroup();
        EventLoopGroup workerGroup = new NioEventLoopGroup();
        
        try {
            ServerBootstrap bootstrap = new ServerBootstrap();
            bootstrap.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ch.pipeline()
                            .addLast(new ObjectEncoder())
                            .addLast(new ObjectDecoder(ClassResolvers.cacheDisabled(null)))
                            .addLast(new RpcServerHandler(serviceMap));
                    }
                });
            
            ChannelFuture future = bootstrap.bind(port).sync();
            System.out.println("RPC Server started on port " + port);
            future.channel().closeFuture().sync();
        } finally {
            bossGroup.shutdownGracefully();
            workerGroup.shutdownGracefully();
        }
    }
}

public class RpcServerHandler extends SimpleChannelInboundHandler<RpcRequest> {
    private Map<String, Object> serviceMap;
    
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, RpcRequest request) {
        RpcResponse response = new RpcResponse();
        response.setRequestId(request.getRequestId());
        
        try {
            // 获取服务实例
            Object service = serviceMap.get(request.getClassName());
            if (service == null) {
                throw new RuntimeException("Service not found: " + request.getClassName());
            }
            
            // 反射调用
            Method method = service.getClass().getMethod(
                request.getMethodName(),
                request.getParameterTypes()
            );
            Object result = method.invoke(service, request.getParameters());
            
            response.setResult(result);
        } catch (Exception e) {
            response.setError(e);
        }
        
        // 返回响应
        ctx.writeAndFlush(response);
    }
}
```

### 3.6 使用示例

**服务接口**：
```java
public interface HelloService {
    String hello(String name);
}
```

**服务实现**：
```java
public class HelloServiceImpl implements HelloService {
    @Override
    public String hello(String name) {
        return "Hello, " + name;
    }
}
```

**服务端启动**：
```java
public class ServerTest {
    public static void main(String[] args) throws Exception {
        RpcServer server = new RpcServer(8080);
        server.registerService(HelloService.class, new HelloServiceImpl());
        server.start();
    }
}
```

**客户端调用**：
```java
public class ClientTest {
    public static void main(String[] args) {
        RpcClientProxy proxy = new RpcClientProxy("localhost", 8080);
        HelloService helloService = proxy.getProxy(HelloService.class);
        
        String result = helloService.hello("World");
        System.out.println(result);  // Hello, World
    }
}
```

---

## 4. 进阶扩展

### 4.1 服务注册与发现

**使用Zookeeper**：
```java
public class ZookeeperRegistry {
    private CuratorFramework client;
    private static final String ROOT_PATH = "/rpc";
    
    public void register(String serviceName, String address) {
        String path = ROOT_PATH + "/" + serviceName;
        try {
            if (client.checkExists().forPath(path) == null) {
                client.create()
                    .creatingParentsIfNeeded()
                    .withMode(CreateMode.PERSISTENT)
                    .forPath(path);
            }
            
            String addressPath = path + "/" + address;
            client.create()
                .withMode(CreateMode.EPHEMERAL)
                .forPath(addressPath);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
    
    public List<String> discover(String serviceName) {
        String path = ROOT_PATH + "/" + serviceName;
        try {
            return client.getChildren().forPath(path);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
```

### 4.2 负载均衡

**随机策略**：
```java
public class RandomLoadBalancer implements LoadBalancer {
    @Override
    public String select(List<String> addresses) {
        return addresses.get(new Random().nextInt(addresses.size()));
    }
}
```

**轮询策略**：
```java
public class RoundRobinLoadBalancer implements LoadBalancer {
    private AtomicInteger index = new AtomicInteger(0);
    
    @Override
    public String select(List<String> addresses) {
        int i = index.getAndIncrement() % addresses.size();
        return addresses.get(i);
    }
}
```

### 4.3 序列化

**JSON序列化**：
```java
public class JsonSerializer implements Serializer {
    private ObjectMapper objectMapper = new ObjectMapper();
    
    @Override
    public byte[] serialize(Object obj) {
        try {
            return objectMapper.writeValueAsBytes(obj);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
    
    @Override
    public <T> T deserialize(byte[] data, Class<T> clazz) {
        try {
            return objectMapper.readValue(data, clazz);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
```

---

## 📚 总结

### 关键要点

**IoC容器**：
- Bean定义注册
- Bean实例化
- 依赖注入
- 单例缓存

**AOP**：
- JDK动态代理（接口）
- CGLIB代理（类）
- 方法拦截与增强

**RPC框架**：
- 动态代理（客户端）
- 网络通信（Netty）
- 序列化/反序列化
- 服务注册与发现
- 负载均衡

### 进阶方向

- [ ] 实现Bean的完整生命周期
- [ ] 实现循环依赖解决
- [ ] 实现AOP切面表达式解析
- [ ] 实现事务管理
- [ ] 实现异步调用
- [ ] 实现服务降级
- [ ] 实现心跳检测
- [ ] 实现自定义协议

---

**最后更新时间**：2025-10-29

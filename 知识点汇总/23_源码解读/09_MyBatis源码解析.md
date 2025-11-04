# MyBatis源码解析

> 执行流程、缓存机制、插件原理深度剖析

---

## 📋 目录

- [1. MyBatis整体架构](#1-mybatis整体架构)
- [2. 初始化流程](#2-初始化流程)
- [3. SQL执行流程](#3-sql执行流程)
- [4. Mapper代理机制](#4-mapper代理机制)
- [5. 缓存机制](#5-缓存机制)
- [6. 插件原理](#6-插件原理)
- [7. 面试高频问题](#7-面试高频问题)

---

## 🎯 学习目标

- ✅ 理解MyBatis整体架构
- ✅ 掌握SqlSessionFactory创建流程
- ✅ 理解Mapper动态代理机制
- ✅ 掌握一级、二级缓存实现
- ✅ 理解插件拦截器原理
- ✅ 掌握SQL执行完整流程

---

## 1. MyBatis整体架构

### 1.1 分层架构

```
应用层（User Code）
    ↓
API层（SqlSession）
    ↓
核心处理层
    ├── 配置解析（Configuration）
    ├── SQL解析（SqlSource）
    ├── SQL执行（Executor）
    ├── 结果映射（ResultSetHandler）
    └── 参数处理（ParameterHandler）
    ↓
基础支撑层
    ├── 数据源（DataSource）
    ├── 事务管理（Transaction）
    ├── 缓存（Cache）
    ├── 日志（Log）
    └── 反射（Reflector）
```

### 1.2 核心组件

**核心类**：
- `SqlSessionFactory`：会话工厂
- `SqlSession`：SQL会话
- `Executor`：执行器（Simple/Reuse/Batch/Caching）
- `StatementHandler`：JDBC Statement处理器
- `ParameterHandler`：参数处理器
- `ResultSetHandler`：结果集处理器
- `TypeHandler`：类型转换器

---

## 2. 初始化流程

### 2.1 SqlSessionFactory创建

**示例代码**：
```java
String resource = "mybatis-config.xml";
InputStream inputStream = Resources.getResourceAsStream(resource);
SqlSessionFactory sqlSessionFactory = 
    new SqlSessionFactoryBuilder().build(inputStream);
```

**核心流程**：
```java
// SqlSessionFactoryBuilder#build()
public SqlSessionFactory build(InputStream inputStream) {
    // 1. 创建XML配置解析器
    XMLConfigBuilder parser = new XMLConfigBuilder(inputStream);
    
    // 2. 解析配置文件，生成Configuration对象
    Configuration config = parser.parse();
    
    // 3. 根据Configuration创建SqlSessionFactory
    return build(config);
}

// XMLConfigBuilder#parse()
public Configuration parse() {
    // 解析configuration节点
    parseConfiguration(parser.evalNode("/configuration"));
    return configuration;
}

private void parseConfiguration(XNode root) {
    // 解析properties
    propertiesElement(root.evalNode("properties"));
    // 解析settings
    settingsElement(root.evalNode("settings"));
    // 解析typeAliases
    typeAliasesElement(root.evalNode("typeAliases"));
    // 解析plugins
    pluginElement(root.evalNode("plugins"));
    // 解析environments
    environmentsElement(root.evalNode("environments"));
    // 解析mappers（重要！）
    mapperElement(root.evalNode("mappers"));
}
```

### 2.2 Mapper解析

```java
// XMLMapperBuilder#parse()
public void parse() {
    // 1. 解析mapper.xml
    configurationElement(parser.evalNode("/mapper"));
    
    // 2. 绑定Mapper接口
    bindMapperForNamespace();
}

private void configurationElement(XNode context) {
    String namespace = context.getStringAttribute("namespace");
    
    // 解析cache-ref
    cacheRefElement(context.evalNode("cache-ref"));
    // 解析cache
    cacheElement(context.evalNode("cache"));
    // 解析parameterMap
    parameterMapElement(context.evalNodes("/mapper/parameterMap"));
    // 解析resultMap
    resultMapElements(context.evalNodes("/mapper/resultMap"));
    // 解析sql片段
    sqlElement(context.evalNodes("/mapper/sql"));
    // 解析select|insert|update|delete
    buildStatementFromContext(context.evalNodes("select|insert|update|delete"));
}
```

---

## 3. SQL执行流程

### 3.1 完整执行链路

**流程图**：
```
1. SqlSession.selectOne()
    ↓
2. Executor.query()
    ↓
3. CachingExecutor（二级缓存）
    ↓
4. BaseExecutor（一级缓存）
    ↓
5. StatementHandler.query()
    ↓
6. ParameterHandler.setParameters()
    ↓
7. JDBC Statement.execute()
    ↓
8. ResultSetHandler.handleResultSets()
    ↓
9. 返回结果
```

### 3.2 核心代码

```java
// DefaultSqlSession#selectOne()
public <T> T selectOne(String statement, Object parameter) {
    List<T> list = this.selectList(statement, parameter);
    return list.isEmpty() ? null : list.get(0);
}

public <E> List<E> selectList(String statement, Object parameter) {
    // 获取MappedStatement
    MappedStatement ms = configuration.getMappedStatement(statement);
    // 执行查询
    return executor.query(ms, wrapCollection(parameter), 
                         RowBounds.DEFAULT, Executor.NO_RESULT_HANDLER);
}

// CachingExecutor#query()（二级缓存）
public <E> List<E> query(MappedStatement ms, Object parameterObject, 
                        RowBounds rowBounds, ResultHandler resultHandler) {
    // 获取BoundSql
    BoundSql boundSql = ms.getBoundSql(parameterObject);
    // 创建缓存Key
    CacheKey key = createCacheKey(ms, parameterObject, rowBounds, boundSql);
    
    // 先查二级缓存
    Cache cache = ms.getCache();
    if (cache != null) {
        Object cachedResult = cache.getObject(key);
        if (cachedResult != null) {
            return (List<E>) cachedResult;
        }
    }
    
    // 委托给BaseExecutor
    return delegate.query(ms, parameterObject, rowBounds, resultHandler);
}

// BaseExecutor#query()（一级缓存）
public <E> List<E> query(MappedStatement ms, Object parameter, 
                        RowBounds rowBounds, ResultHandler resultHandler) {
    // 创建CacheKey
    CacheKey key = createCacheKey(ms, parameter, rowBounds, boundSql);
    
    // 查一级缓存
    List<E> list = localCache.getObject(key);
    if (list != null) {
        return list;
    }
    
    // 查询数据库
    list = queryFromDatabase(ms, parameter, rowBounds, resultHandler, key, boundSql);
    return list;
}

private <E> List<E> queryFromDatabase(...) {
    // 执行查询
    list = doQuery(ms, parameter, rowBounds, resultHandler, boundSql);
    // 放入一级缓存
    localCache.putObject(key, list);
    return list;
}
```

---

## 4. Mapper代理机制

### 4.1 Mapper接口代理

**如何生成代理对象**：

```java
// 获取Mapper
UserMapper userMapper = sqlSession.getMapper(UserMapper.class);

// DefaultSqlSession#getMapper()
public <T> T getMapper(Class<T> type) {
    return configuration.getMapper(type, this);
}

// MapperRegistry#getMapper()
public <T> T getMapper(Class<T> type, SqlSession sqlSession) {
    // 获取MapperProxyFactory
    MapperProxyFactory<T> mapperProxyFactory = knownMappers.get(type);
    
    // 创建Mapper代理对象
    return mapperProxyFactory.newInstance(sqlSession);
}

// MapperProxyFactory#newInstance()
public T newInstance(SqlSession sqlSession) {
    // 创建MapperProxy（InvocationHandler）
    MapperProxy<T> mapperProxy = new MapperProxy<>(sqlSession, mapperInterface);
    
    // JDK动态代理
    return (T) Proxy.newProxyInstance(mapperInterface.getClassLoader(),
                                     new Class[]{mapperInterface},
                                     mapperProxy);
}
```

### 4.2 方法调用拦截

```java
// MapperProxy#invoke()
public Object invoke(Object proxy, Method method, Object[] args) {
    // 如果是Object的方法，直接执行
    if (Object.class.equals(method.getDeclaringClass())) {
        return method.invoke(this, args);
    }
    
    // 创建MapperMethod
    MapperMethod mapperMethod = cachedMapperMethod(method);
    
    // 执行SQL
    return mapperMethod.execute(sqlSession, args);
}

// MapperMethod#execute()
public Object execute(SqlSession sqlSession, Object[] args) {
    Object result;
    switch (command.getType()) {
        case INSERT:
            Object param = method.convertArgsToSqlCommandParam(args);
            result = sqlSession.insert(command.getName(), param);
            break;
        case UPDATE:
            Object param = method.convertArgsToSqlCommandParam(args);
            result = sqlSession.update(command.getName(), param);
            break;
        case DELETE:
            Object param = method.convertArgsToSqlCommandParam(args);
            result = sqlSession.delete(command.getName(), param);
            break;
        case SELECT:
            if (method.returnsMany()) {
                result = sqlSession.selectList(command.getName(), param);
            } else {
                result = sqlSession.selectOne(command.getName(), param);
            }
            break;
    }
    return result;
}
```

---

## 5. 缓存机制

### 5.1 一级缓存（Session级别）

**特性**：
- 默认开启
- SqlSession级别
- 生命周期与SqlSession一致
- 增删改或手动清空会清除缓存

**实现**：
```java
// BaseExecutor中的一级缓存
protected PerpetualCache localCache;  // HashMap实现

// 查询时先查缓存
CacheKey key = createCacheKey(ms, parameter, rowBounds, boundSql);
List<E> list = localCache.getObject(key);

// 更新时清空缓存
public int update(MappedStatement ms, Object parameter) {
    clearLocalCache();  // 清空一级缓存
    return doUpdate(ms, parameter);
}
```

### 5.2 二级缓存（Namespace级别）

**特性**：
- 需要手动开启
- Mapper级别（namespace）
- 跨SqlSession共享
- 需要实体类实现Serializable

**配置**：
```xml
<!-- Mapper.xml中开启 -->
<cache/>

<!-- 或自定义配置 -->
<cache eviction="LRU"
       flushInterval="60000"
       size="512"
       readOnly="true"/>
```

---

## 6. 插件原理

### 6.1 插件机制

**可拦截的对象**：
- Executor（执行器）
- StatementHandler（Statement处理器）
- ParameterHandler（参数处理器）
- ResultSetHandler（结果处理器）

**自定义插件示例**：
```java
@Intercepts({
    @Signature(type = Executor.class,
               method = "query",
               args = {MappedStatement.class, Object.class, 
                       RowBounds.class, ResultHandler.class})
})
public class MyPlugin implements Interceptor {
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        // 前置处理
        System.out.println("执行前...");
        
        // 执行原方法
        Object result = invocation.proceed();
        
        // 后置处理
        System.out.println("执行后...");
        return result;
    }
    
    @Override
    public Object plugin(Object target) {
        return Plugin.wrap(target, this);
    }
}
```

---

## 7. 面试高频问题

### Q1: MyBatis的执行流程？

**答案**：
1. SqlSessionFactory创建（解析配置）
2. SqlSession创建
3. 获取Mapper代理对象
4. 执行方法，拦截到MapperProxy
5. 查询二级缓存
6. 查询一级缓存
7. 查询数据库
8. 结果映射
9. 放入缓存

### Q2: MyBatis一级缓存和二级缓存的区别？

**答案**：
| 特性 | 一级缓存 | 二级缓存 |
|------|---------|---------|
| 作用域 | SqlSession | Mapper(Namespace) |
| 默认开启 | 是 | 否 |
| 共享性 | 不共享 | 跨SqlSession共享 |
| 清除时机 | 增删改/手动清除 | 增删改/手动清除 |

### Q3: Mapper接口如何生成代理对象？

**答案**：
使用JDK动态代理：
1. MapperRegistry管理所有Mapper接口
2. MapperProxyFactory创建代理工厂
3. MapperProxy实现InvocationHandler
4. Proxy.newProxyInstance创建代理对象

### Q4: MyBatis如何防止SQL注入？

**答案**：
- 使用#{}：预编译，参数占位符，防止SQL注入
- 避免${}：字符串拼接，有SQL注入风险

### Q5: MyBatis插件原理？

**答案**：
1. 使用责任链模式
2. 通过动态代理拦截四大对象
3. 在目标方法执行前后添加自定义逻辑

---

## 📚 参考资料

- 《MyBatis技术内幕》
- [MyBatis官方文档](https://mybatis.org/mybatis-3/zh/)
- [MyBatis源码GitHub](https://github.com/mybatis/mybatis-3)

---

**最后更新时间**：2025-10-29

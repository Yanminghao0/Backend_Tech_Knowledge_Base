# MyBatis 源码深度解读：SQL 执行流程与插件机制

> "MyBatis 的设计哲学是 SQL First——它不试图隐藏 SQL，而是让 SQL 的编写和执行变得优雅而可控。" —— Clinton Begin（MyBatis 创始人）

---

## 📋 目录

1. [MyBatis 整体架构与核心组件](#1-mybatis-整体架构与核心组件)
2. [SqlSessionFactory 初始化源码解析](#2-sqlsessionfactory-初始化源码解析)
3. [Mapper 接口绑定原理](#3-mapper-接口绑定原理)
4. [SqlSession 执行流程全链路](#4-sqlsession-执行流程全链路)
5. [Executor 执行器源码解析](#5-executor-执行器源码解析)
6. [StatementHandler 与 ParameterHandler](#6-statementhandler-与-parameterhandler)
7. [ResultSetHandler 结果映射](#7-resultsethandler-结果映射)
8. [一级缓存与二级缓存源码](#8-一级缓存与二级缓存源码)
9. [插件（拦截器）机制源码](#9-插件拦截器机制源码)
10. [面试题速查](#10-面试题速查)

---

## 1. MyBatis 整体架构与核心组件

MyBatis 的架构分为三层：

```
┌──────────────────────────────────────────────────────────┐
│                      接口层                                │
│    SqlSession / Mapper接口                                │
├──────────────────────────────────────────────────────────┤
│                      核心处理层                             │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ │
│  │Configuration│ │ Executor │ │StatementH │ │ResultSetH │ │
│  │ (全局配置) │ │ (执行器)  │ │ (语句处理器)│ │(结果处理器) │ │
│  └──────────┘ └──────────┘ └───────────┘ └───────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐                │
│  │MappedStmt│ │ParameterH│ │   TypeH   │                │
│  │(SQL映射)  │ │(参数处理) │ │(类型处理)  │                │
│  └──────────┘ └──────────┘ └───────────┘                │
├──────────────────────────────────────────────────────────┤
│                      基础支撑层                             │
│  日志 / 反射 / 数据源 / 事务管理 / 缓存 / 类型转换           │
└──────────────────────────────────────────────────────────┘
```

核心组件职责：

| 组件 | 职责 |
|------|------|
| `SqlSessionFactory` | 创建 SqlSession 的工厂（重量级，全局唯一） |
| `SqlSession` | 一次数据库会话（轻量级，非线程安全） |
| `Executor` | SQL 执行器，负责一级缓存和事务管理 |
| `StatementHandler` | 创建并操作 JDBC Statement |
| `ParameterHandler` | 设置 SQL 参数 |
| `ResultSetHandler` | 处理 ResultSet 映射为 Java 对象 |
| `MappedStatement` | 一条 SQL 的完整映射信息 |

---

## 2. SqlSessionFactory 初始化源码解析

### 2.1 XML 解析入口

```java
// SqlSessionFactoryBuilder.java
public class SqlSessionFactoryBuilder {
    public SqlSessionFactory build(InputStream inputStream) {
        return build(inputStream, null, null);
    }

    public SqlSessionFactory build(InputStream inputStream, String environment,
                                   Properties properties) {
        try {
            // XMLConfigBuilder 负责解析 mybatis-config.xml
            XMLConfigBuilder parser = new XMLConfigBuilder(inputStream, environment, properties);
            // 解析配置并构建 Configuration 对象
            Configuration configuration = parser.parse();
            // 用 Configuration 构建 DefaultSqlSessionFactory
            return build(configuration);
        } catch (Exception e) {
            throw ExceptionFactory.wrapException(
                "Error building SqlSession.", e);
        } finally {
            ErrorContext.instance().reset();
            try { inputStream.close(); } catch (IOException e) {}
        }
    }

    public SqlSessionFactory build(Configuration config) {
        return new DefaultSqlSessionFactory(config);
    }
}
```

### 2.2 Configuration 解析过程

```java
// XMLConfigBuilder.java
public class XMLConfigBuilder extends BaseBuilder {
    public Configuration parse() {
        if (parsed) {
            throw new BuilderException("Each XMLConfigBuilder can only be used once.");
        }
        parsed = true;
        // 从 <configuration> 根节点开始解析
        parseConfiguration(parser.evalNode("/configuration"));
        return configuration;
    }

    private void parseConfiguration(XNode root) {
        try {
            // 依次解析配置文件的各个部分
            propertiesElement(root.evalNode("properties"));          // 1. <properties>
            Properties settings = settingsAsProperties(root.evalNode("settings")); // 2. <settings>
            loadCustomVfs(settings);
            typeAliasesElement(root.evalNode("typeAliases"));        // 3. <typeAliases>
            pluginElement(root.evalNode("plugins"));                 // 4. <plugins> - 注册插件
            objectFactoryElement(root.evalNode("objectFactory"));    // 5. <objectFactory>
            objectWrapperFactoryElement(root.evalNode("objectWrapperFactory"));
            reflectorFactoryElement(root.evalNode("reflectorFactory"));
            settingsElement(settings);                               // 应用 settings
            environmentsElement(root.evalNode("environments"));      // 6. <environments>
            databaseIdProviderElement(root.evalNode("databaseIdProvider"));
            typeHandlerElement(root.evalNode("typeHandlers"));       // 7. <typeHandlers>
            mapperElement(root.evalNode("mappers"));                 // 8. <mappers> - 解析Mapper
        } catch (Exception e) {
            throw new BuilderException("Error parsing SQL Mapper Configuration.", e);
        }
    }
}
```

### 2.3 Mapper XML 解析

```java
// XMLMapperBuilder.java
public class XMLMapperBuilder extends BaseBuilder {
    public void parse() {
        if (!configuration.isResourceLoaded(resource)) {
            configurationElement(parser.evalNode("/mapper"));
            configuration.addLoadedResource(resource);
            bindMapperForNamespace();  // 绑定 Mapper 接口
        }
        // 处理未完成的语句（解决引用循环）
        parsePendingResultMaps();
        parsePendingCacheRefs();
        parsePendingStatements();
    }

    private void configurationElement(XNode context) {
        try {
            String namespace = context.getStringAttribute("namespace");
            if (namespace == null || namespace.equals("")) {
                throw new BuilderException("Mapper's namespace cannot be empty");
            }
            builderAssistant.setCurrentNamespace(namespace);
            cacheRefElement(context.evalNode("cache-ref"));       // <cache-ref>
            cacheElement(context.evalNode("cache"));              // <cache>
            parameterMapElement(context.evalNodes("/mapper/parameterMap")); // <parameterMap>
            resultMapElements(context.evalNodes("/mapper/resultMap"));      // <resultMap>
            sqlElement(context.evalNodes("/mapper/sql"));                   // <sql> 片段
            buildStatementFromContext(context.evalNodes("select|insert|update|delete")); // SQL语句
        } catch (Exception e) {
            throw new BuilderException("Error parsing Mapper XML.", e);
        }
    }

    private void buildStatementFromContext(List<XNode> list) {
        for (XNode context : list) {
            final XMLStatementBuilder statementParser = new XMLStatementBuilder(
                configuration, builderAssistant, context, databaseId);
            statementParser.parseStatementNode();
        }
    }
}
```

### 2.4 MappedStatement 构建

```java
// XMLStatementBuilder.java
public class XMLStatementBuilder extends BaseBuilder {
    public void parseStatementNode() {
        String id = context.getStringAttribute("id");
        String databaseId = context.getStringAttribute("databaseId");

        // ... 解析各种属性 ...

        // 解析 <include> 标签，替换为 <sql> 片段内容
        List<SqlNode> contents = parseDynamicTags(context);
        // 构建 SqlSource（区分动态SQL和静态SQL）
        MixedSqlNode rootSqlNode = new MixedSqlNode(contents);
        SqlSource sqlSource;
        if (isDynamic) {
            sqlSource = new DynamicSqlSource(configuration, rootSqlNode);
        } else {
            sqlSource = new RawSqlSource(configuration, rootSqlNode, parameterType);
        }

        // 构建 MappedStatement 并注册到 Configuration
        builderAssistant.addMappedStatement(id, sqlSource, statementType, sqlCommandType,
            fetchSize, timeout, parameterMap, parameterType, resultMap, resultType,
            resultSetTypeEnum, flushCache, useCache, resultOrdered,
            keyGenerator, keyProperty, keyColumn, databaseId, langDriver, resultSets);
    }
}
```

`MappedStatement` 是 MyBatis 中最重要的对象之一，它封装了一条 SQL 的所有信息：SQL 文本、参数类型、返回类型、缓存配置等。解析完成后存储在 `Configuration.mappedStatements` Map 中。

---

## 3. Mapper 接口绑定原理

### 3.1 MapperProxy 代理机制

MyBatis 的 Mapper 接口不需要实现类，它通过 JDK 动态代理生成代理对象：

```java
// MapperProxy.java
public class MapperProxy<T> implements InvocationHandler, Serializable {
    private static final long serialVersionUID = -1L;
    private final SqlSession sqlSession;
    private final Class<T> mapperInterface;
    private final Map<Method, MapperMethod> methodCache;

    public MapperProxy(SqlSession sqlSession, Class<T> mapperInterface,
                       Map<Method, MapperMethod> methodCache) {
        this.sqlSession = sqlSession;
        this.mapperInterface = mapperInterface;
        this.methodCache = methodCache;
    }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        try {
            // Object 方法直接调用
            if (Object.class.equals(method.getDeclaringClass())) {
                return method.invoke(this, args);
            } else if (method.isDefault()) {
                // Java 8 default 方法特殊处理
                return invokeDefaultMethod(proxy, method, args);
            }
        } catch (Throwable t) {
            throw ExceptionUtil.unwrapThrowable(t);
        }
        // 核心：从缓存获取或创建 MapperMethod 并执行
        final MapperMethod mapperMethod = cachedMapperMethod(method);
        return mapperMethod.execute(sqlSession, args);
    }

    private MapperMethod cachedMapperMethod(Method method) {
        MapperMethod mapperMethod = methodCache.get(method);
        if (mapperMethod == null) {
            mapperMethod = new MapperMethod(mapperInterface, method, sqlSession.getConfiguration());
            methodCache.put(method, mapperMethod);
        }
        return mapperMethod;
    }
}
```

### 3.2 MapperMethod 命令模式

```java
// MapperMethod.java
public class MapperMethod {
    private final SqlCommand command;
    private final MethodSignature method;

    public MapperMethod(Class<?> mapperInterface, Method method, Configuration config) {
        this.command = new SqlCommand(config, mapperInterface, method);
        this.method = new MethodSignature(config, mapperInterface, method);
    }

    public Object execute(SqlSession sqlSession, Object[] args) {
        Object result;
        switch (command.getType()) {
            case INSERT: {
                Object param = method.convertArgsToSqlCommandParam(args);
                result = rowCountResult(sqlSession.insert(command.getName(), param));
                break;
            }
            case UPDATE: {
                Object param = method.convertArgsToSqlCommandParam(args);
                result = rowCountResult(sqlSession.update(command.getName(), param));
                break;
            }
            case DELETE: {
                Object param = method.convertArgsToSqlCommandParam(args);
                result = rowCountResult(sqlSession.delete(command.getName(), param));
                break;
            }
            case SELECT:
                if (method.returnsVoid() && method.hasResultHandler()) {
                    // 无返回值，使用 ResultHandler 回调
                    executeWithResultHandler(sqlSession, args);
                    result = null;
                } else if (method.returnsMany()) {
                    result = executeForMany(sqlSession, args);
                } else if (method.returnsMap()) {
                    result = executeForMap(sqlSession, args);
                } else if (method.returnsCursor()) {
                    result = executeForCursor(sqlSession, args);
                } else {
                    // 返回单个对象
                    Object param = method.convertArgsToSqlCommandParam(args);
                    result = sqlSession.selectOne(command.getName(), param);
                    if (method.returnsOptional() &&
                        (result == null || !method.getReturnType().equals(result.getClass()))) {
                        result = Optional.ofNullable(result);
                    }
                }
                break;
            case FLUSH:
                result = sqlSession.flushStatements();
                break;
            default:
                throw new BindingException("Unknown execution method for: " + command.getName());
        }
        return result;
    }
}
```

`SqlCommand` 通过方法全限定名（接口全名 + 方法名）从 `Configuration` 中查找对应的 `MappedStatement`，这就是为什么 Mapper 接口方法名必须与 XML 中的 `id` 一致。

### 3.3 参数绑定机制

```java
// ParamNameResolver.java
public Object getNamedParams(Object[] args) {
        final int paramCount = names.size();
        if (args == null || paramCount == 0) {
            return null;
        } else if (!hasParamAnnotation && paramCount == 1) {
            // 单参数无注解：直接返回参数值
            Object value = args[names.firstKey()];
            return wrapToMapIfCollection(value, useActualParamName ? names.get(0) : null);
        } else {
            // 多参数或有 @Param 注解：构建 ParamMap
            final Map<String, Object> param = new ParamMap<>();
            int i = 0;
            for (Map.Entry<Integer, String> entry : names.entrySet()) {
                param.put(entry.getValue(), args[entry.getKey()]);
                // 额外添加 param1, param2, ... 作为通用名称
                final String genericParamName = GENERIC_NAME_PREFIX + (i + 1);
                if (!names.containsValue(genericParamName)) {
                    param.put(genericParamName, args[entry.getKey()]);
                }
                i++;
            }
            return param;
        }
    }
}
```

这就是为什么在多参数情况下，SQL 中可以使用 `#{param1}`、`#{param2}` 或 `@Param` 指定的名称来引用参数。

---

## 4. SqlSession 执行流程全链路

### 4.1 DefaultSqlSession

```java
// DefaultSqlSession.java
public class DefaultSqlSession implements SqlSession {
    private final Configuration configuration;
    private final Executor executor;
    private final boolean autoCommit;
    private boolean dirty;

    @Override
    public <E> List<E> selectList(String statement, Object parameter, RowBounds rowBounds) {
        try {
            // 从 Configuration 获取 MappedStatement
            MappedStatement ms = configuration.getMappedStatement(statement);
            // 委托给 Executor 执行
            return executor.query(ms, wrapCollection(parameter), rowBounds, Executor.NO_RESULT_HANDLER);
        } catch (Exception e) {
            throw ExceptionFactory.wrapException(
                "Error querying database.  Cause: " + e, e);
        } finally {
            ErrorContext.instance().reset();
        }
    }

    @Override
    public int update(String statement, Object parameter) {
        try {
            dirty = true;
            MappedStatement ms = configuration.getMappedStatement(statement);
            return executor.update(ms, wrapCollection(parameter));
        } catch (Exception e) {
            throw ExceptionFactory.wrapException(
                "Error updating database.  Cause: " + e, e);
        } finally {
            ErrorContext.instance().reset();
        }
    }
}
```

### 4.2 完整调用链路图

```
Mapper.method(args)
  └─► MapperProxy.invoke()
        └─► MapperMethod.execute()
              └─► SqlSession.selectList() / update()
                    └─► Executor.query() / update()
                          ├─► 查询一级缓存
                          ├─► StatementHandler.prepare() → 创建 Statement
                          ├─► StatementHandler.parameterize()
                          │     └─► ParameterHandler.setParameters()
                          ├─► StatementHandler.query()
                          │     └─► PreparedStatement.execute()
                          │     └─► ResultSetHandler.handleResultSets()
                          └─► 更新一级缓存
```

---

## 5. Executor 执行器源码解析

### 5.1 Executor 三种类型

```java
// Configuration.java
public Executor newExecutor(Transaction transaction, ExecutorType executorType) {
    executorType = executorType == null ? defaultExecutorType : executorType;
    executorType = executorType == null ? ExecutorType.SIMPLE : executorType;
    Executor executor;
    if (ExecutorType.BATCH == executorType) {
        executor = new BatchExecutor(this, transaction);
    } else if (ExecutorType.REUSE == executorType) {
        executor = new ReuseExecutor(this, transaction);
    } else {
        executor = new SimpleExecutor(this, transaction);
    }
    // 二级缓存装饰
    if (cacheEnabled) {
        executor = new CachingExecutor(executor);
    }
    // 插件拦截
    executor = (Executor) interceptorChain.pluginAll(executor);
    return executor;
}
```

| 类型 | 特点 |
|------|------|
| `SimpleExecutor` | 每次执行创建新 Statement，执行后关闭 |
| `ReuseExecutor` | 缓存 Statement，相同 SQL 复用 |
| `BatchExecutor` | 批处理模式，使用 JDBC addBatch/executeBatch |
| `CachingExecutor` | 二级缓存装饰器，装饰以上三种 |

### 5.2 BaseExecutor 模板方法模式

```java
// BaseExecutor.java
public abstract class BaseExecutor implements Executor {
    protected PerpetualCache localCache;       // 一级缓存
    protected PerpetualCache localOutputParameterCache;
    protected Configuration configuration;
    protected Transaction transaction;

    @Override
    public <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds,
                             ResultHandler resultHandler) throws SQLException {
        // 获取 BoundSql（动态SQL已解析为最终SQL）
        BoundSql boundSql = ms.getBoundSql(parameter);
        // 创建缓存Key
        CacheKey key = createCacheKey(ms, parameter, rowBounds, boundSql);
        return query(ms, parameter, rowBounds, resultHandler, key, boundSql);
    }

    @SuppressWarnings("unchecked")
    @Override
    public <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds,
                             ResultHandler resultHandler, CacheKey key, BoundSql boundSql) throws SQLException {
        ErrorContext.instance().resource(ms.getResource()).activity("executing a query").object(ms.getId());
        if (closed) {
            throw new ExecutorException("Executor was closed.");
        }
        if (queryStack == 0 && ms.isFlushCacheRequired()) {
            clearLocalCache();
        }
        List<E> list;
        try {
            queryStack++;
            // 查一级缓存
            list = resultHandler == null ? (List<E>) localCache.getObject(key) : null;
            if (list != null) {
                handleLocallyCachedOutputParameters(ms, key, parameter, boundSql);
            } else {
                // 缓存未命中，查数据库
                list = queryFromDatabase(ms, parameter, rowBounds, resultHandler, key, boundSql);
            }
        } finally {
            queryStack--;
        }
        if (queryStack == 0) {
            for (DeferredLoad deferredLoad : deferredLoads) {
                deferredLoad.load();
            }
            deferredLoads.clear();
            if (configuration.getLocalCacheScope() == LocalCacheScope.STATEMENT) {
                clearLocalCache();
            }
        }
        return list;
    }

    private <E> List<E> queryFromDatabase(MappedStatement ms, Object parameter,
                                          RowBounds rowBounds, ResultHandler resultHandler,
                                          CacheKey key, BoundSql boundSql) throws SQLException {
        List<E> list;
        localCache.putObject(key, EXECUTION_PLACEHOLDER);  // 防止循环引用
        try {
            // 模板方法：由子类实现具体查询
            list = doQuery(ms, parameter, rowBounds, resultHandler, boundSql);
        } finally {
            localCache.removeObject(key);
        }
        // 放入一级缓存
        localCache.putObject(key, list);
        if (ms.getStatementType() == StatementType.CALLABLE) {
            localOutputParameterCache.putObject(key, parameter);
        }
        return list;
    }

    // 子类实现的抽象方法
    protected abstract <E> List<E> doQuery(MappedStatement ms, Object parameter,
                                           RowBounds rowBounds, ResultHandler resultHandler,
                                           BoundSql boundSql) throws SQLException;
}
```

### 5.3 SimpleExecutor 实现

```java
// SimpleExecutor.java
public class SimpleExecutor extends BaseExecutor {
    @Override
    public <E> List<E> doQuery(MappedStatement ms, Object parameter, RowBounds rowBounds,
                               ResultHandler resultHandler, BoundSql boundSql) throws SQLException {
        Statement stmt = null;
        try {
            Configuration configuration = ms.getConfiguration();
            // 创建 StatementHandler（会被插件拦截）
            StatementHandler handler = configuration.newStatementHandler(
                wrapper, ms, parameter, rowBounds, resultHandler, boundSql);
            // 准备 Statement
            stmt = prepareStatement(handler, ms.getStatementLog());
            // 执行查询
            return handler.query(stmt, resultHandler);
        } finally {
            closeStatement(stmt);
        }
    }

    private Statement prepareStatement(StatementHandler handler, Log statementLog) throws SQLException {
        Statement stmt;
        Connection connection = getConnection(statementLog);
        // 创建 Statement 并设置参数
        stmt = handler.prepare(connection, transaction.getTimeout());
        handler.parameterize(stmt);
        return stmt;
    }
}
```

---

## 6. StatementHandler 与 ParameterHandler

### 6.1 StatementHandler 创建

```java
// Configuration.java
public StatementHandler newStatementHandler(Executor executor, MappedStatement mappedStatement,
            Object parameterObject, RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) {
    // 根据 statementType 创建对应的 Handler
    StatementHandler statementHandler = new RoutingStatementHandler(
        executor, mappedStatement, parameterObject, rowBounds, resultHandler, boundSql);
    // 插件拦截
    statementHandler = (StatementHandler) interceptorChain.pluginAll(statementHandler);
    return statementHandler;
}
```

### 6.2 RoutingStatementHandler 路由

```java
// RoutingStatementHandler.java
public class RoutingStatementHandler implements StatementHandler {
    private final StatementHandler delegate;

    public RoutingStatementHandler(Executor executor, MappedStatement ms, Object parameter,
                                   RowBounds rowBounds, ResultHandler resultHandler, BoundSql boundSql) {
        switch (ms.getStatementType()) {
            case STATEMENT:
                delegate = new SimpleStatementHandler(executor, ms, parameter, rowBounds,
                                                      resultHandler, boundSql);
                break;
            case PREPARED:  // 默认
                delegate = new PreparedStatementHandler(executor, ms, parameter, rowBounds,
                                                        resultHandler, boundSql);
                break;
            case CALLABLE:
                delegate = new CallableStatementHandler(executor, ms, parameter, rowBounds,
                                                        resultHandler, boundSql);
                break;
            default:
                throw new ExecutorException("Unknown statement type: " + ms.getStatementType());
        }
    }

    @Override
    public void parameterize(Statement statement) throws SQLException {
        delegate.parameterize(statement);
    }

    @Override
    public void batch(Statement statement) throws SQLException {
        delegate.batch(statement);
    }

    @Override
    public <E> List<E> query(Statement statement, ResultHandler resultHandler) throws SQLException {
        return delegate.query(statement, resultHandler);
    }
}
```

### 6.3 PreparedStatementHandler 核心方法

```java
// PreparedStatementHandler.java
public class PreparedStatementHandler extends BaseStatementHandler {
    @Override
    public Statement prepare(Connection connection, Integer transactionTimeout) throws SQLException {
        ErrorContext.instance().activity("preparing a statement").object(statementLog);
        Statement statement = null;
        try {
            // 创建 PreparedStatement
            statement = instantiateStatement(connection);
            // 设置超时和 fetchSize
            setStatementTimeout(statement, transactionTimeout);
            setFetchSize(statement);
            return statement;
        } catch (SQLException e) {
            closeStatement(statement);
            throw e;
        } catch (Exception e) {
            closeStatement(statement);
            throw new ExecutorException("Error preparing statement.  Cause: " + e, e);
        }
    }

    @Override
    public void parameterize(Statement statement) throws SQLException {
        // 使用 ParameterHandler 设置参数
        parameterHandler.setParameters((PreparedStatement) statement);
    }

    @Override
    public <E> List<E> query(Statement statement, ResultHandler resultHandler) throws SQLException {
        PreparedStatement ps = (PreparedStatement) statement;
        ps.execute();  // 执行 SQL
        // 使用 ResultSetHandler 处理结果
        return resultSetHandler.handleResultSets(ps);
    }

    @Override
    public int update(Statement statement) throws SQLException {
        PreparedStatement ps = (PreparedStatement) statement;
        ps.execute();
        int rows = ps.getUpdateCount();
        Object parameterObject = boundSql.getParameterObject();
        KeyGenerator keyGenerator = mappedStatement.getKeyGenerator();
        keyGenerator.processAfter(executor, mappedStatement, ps, parameterObject);
        return rows;
    }
}
```

### 6.4 ParameterHandler 参数设置

```java
// DefaultParameterHandler.java
public class DefaultParameterHandler implements ParameterHandler {
    @Override
    public void setParameters(PreparedStatement ps) {
        ErrorContext.instance().activity("setting parameters").object(mappedStatement.getParameterMap().getId());
        // 获取参数映射列表
        List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();
        if (parameterMappings != null) {
            for (int i = 0; i < parameterMappings.size(); i++) {
                ParameterMapping parameterMapping = parameterMappings.get(i);
                if (parameterMapping.getMode() != ParameterMode.OUT) {
                    Object value;
                    String propertyName = parameterMapping.getProperty();
                    if (boundSql.hasAdditionalParameter(propertyName)) {
                        value = boundSql.getAdditionalParameter(propertyName);
                    } else if (parameterObject == null) {
                        value = null;
                    } else if (typeHandlerRegistry.hasTypeHandler(parameterObject.getClass())) {
                        value = parameterObject;
                    } else {
                        // 通过 MetaObject 反射获取属性值
                        MetaObject metaObject = configuration.newMetaObject(parameterObject);
                        value = metaObject.getValue(propertyName);
                    }
                    // 获取 TypeHandler
                    TypeHandler typeHandler = parameterMapping.getTypeHandler();
                    JdbcType jdbcType = parameterMapping.getJdbcType();
                    if (value == null && jdbcType == null) {
                        jdbcType = configuration.getJdbcTypeForNull();
                    }
                    try {
                        // 委托给 TypeHandler 设置参数
                        typeHandler.setParameter(ps, i + 1, value, jdbcType);
                    } catch (TypeException | SQLException e) {
                        throw new TypeException("Error setting non null for parameter #"
                            + (i + 1) + " with JdbcType " + jdbcType, e);
                    }
                }
            }
        }
    }
}
```

---

## 7. ResultSetHandler 结果映射

### 7.1 handleResultSets 主流程

```java
// DefaultResultSetHandler.java
public class DefaultResultSetHandler implements ResultSetHandler {
    @Override
    public List<Object> handleResultSets(Statement stmt) throws SQLException {
        ErrorContext.instance().activity("handling results").object(mappedStatement.getId());

        final List<Object> multipleResults = new ArrayList<>();
        int resultSetCount = 0;
        ResultSetWrapper rsw = getFirstResultSet(stmt);
        List<ResultMap> resultMaps = mappedStatement.getResultMaps();
        int resultMapCount = resultMaps.size();
        validateResultMapsCount(rsw, resultMapCount);
        while (rsw != null && resultMapCount > resultSetCount) {
            ResultMap resultMap = resultMaps.get(resultSetCount);
            // 处理单个 ResultSet
            handleResultSet(rsw, resultMap, multipleResults, null);
            rsw = getNextResultSet(stmt);
            cleanUpAfterHandlingResultSet();
            resultSetCount++;
        }

        // 处理多结果集
        String[] resultSets = mappedStatement.getResultSets();
        if (resultSets != null) {
            while (rsw != null && resultSetCount < resultSets.length) {
                ResultMapping parentMapping = nextResultMaps.get(resultSets[resultSetCount]);
                if (parentMapping != null) {
                    String nestedResultMapId = parentMapping.getNestedResultMapId();
                    ResultMap resultMap = configuration.getResultMap(nestedResultMapId);
                    handleResultSet(rsw, resultMap, null, parentMapping);
                }
                rsw = getNextResultSet(stmt);
                cleanUpAfterHandlingResultSet();
                resultSetCount++;
            }
        }

        return collapseSingleResultList(multipleResults);
    }

    private void handleResultSet(ResultSetWrapper rsw, ResultMap resultMap,
                                 List<Object> multipleResults, ResultMapping parentMapping) throws SQLException {
        try {
            if (parentMapping != null) {
                handleRowValues(rsw, resultMap, null, RowBounds.DEFAULT, parentMapping);
            } else {
                DefaultResultHandler defaultResultHandler = new DefaultResultHandler(objectFactory);
                handleRowValues(rsw, resultMap, defaultResultHandler, rowBounds, null);
                multipleResults.add(defaultResultHandler.getResultList());
            }
        } finally {
            closeResultSet(rsw.getResultSet());
        }
    }
}
```

### 7.2 行数据映射

```java
private void handleRowValues(ResultSetWrapper rsw, ResultMap resultMap,
                             ResultHandler<?> resultHandler, RowBounds rowBounds,
                             ResultMapping parentMapping) throws SQLException {
    if (resultMap.hasNestedResultMaps()) {
        // 嵌套结果映射（关联查询）
        handleRowValuesForNestedResultMap(rsw, resultMap, resultHandler, rowBounds, parentMapping);
    } else {
        // 简单结果映射
        handleRowValuesForSimpleResultMap(rsw, resultMap, resultHandler, rowBounds, parentMapping);
    }
}

private void handleRowValuesForSimpleResultMap(ResultSetWrapper rsw, ResultMap resultMap,
                                               ResultHandler<?> resultHandler, RowBounds rowBounds,
                                               ResultMapping parentMapping) throws SQLException {
    DefaultResultContext<Object> resultContext = new DefaultResultContext<>();
    ResultSet resultSet = rsw.getResultSet();
    skipRows(resultSet, rowBounds);  // 处理分页
    while (shouldProcessMoreRows(resultContext, rowBounds) && !resultSet.isClosed() && resultSet.next()) {
        ResultMap discriminatedResultMap = resolveDiscriminatedResultMap(rsw, resultMap, null);
        // 将一行数据映射为 Java 对象
        Object rowValue = getRowValue(rsw, discriminatedResultMap, null);
        storeObject(resultHandler, resultContext, rowValue, parentMapping, resultSet);
    }
}

private Object getRowValue(ResultSetWrapper rsw, ResultMap resultMap, String columnPrefix) throws SQLException {
    final ResultLoaderMap lazyLoader = new ResultLoaderMap();
    // 创建目标对象（可能通过 ObjectFactory）
    Object rowValue = createResultObject(rsw, resultMap, lazyLoader, columnPrefix);
    if (rowValue != null && !hasTypeHandlerForResultObject(rsw, resultMap.getType())) {
        final MetaObject metaObject = configuration.newMetaObject(rowValue);
        boolean foundValues = this.useConstructorMappings;
        if (shouldApplyAutomaticMappings(resultMap, false)) {
            // 自动映射（列名与属性名匹配）
            foundValues = applyAutomaticMappings(rsw, resultMap, metaObject, columnPrefix) || foundValues;
        }
        // 手动映射（根据 ResultMap 配置）
        foundValues = applyPropertyMappings(rsw, resultMap, metaObject, lazyLoader, columnPrefix) || foundValues;
        foundValues = lazyLoader.consolidate() || foundValues;
        rowValue = foundValues || resultMap.getConfiguration().isReturnInstanceForEmptyRow() ? rowValue : null;
    }
    return rowValue;
}
```

### 7.3 自动映射机制

```java
private boolean applyAutomaticMappings(ResultSetWrapper rsw, ResultMap resultMap,
                                       MetaObject metaObject, String columnPrefix) throws SQLException {
    // 获取未映射的列名
    List<String> unmappedColumnNames = rsw.getUnmappedColumnNames(resultMap, columnPrefix);
    boolean foundValues = false;
    for (String columnName : unmappedColumnNames) {
        String propertyName = columnName;
        if (columnPrefix != null && !columnPrefix.isEmpty()) {
            // 处理列前缀
            if (columnName.toUpperCase(Locale.ENGLISH).startsWith(columnPrefix)) {
                propertyName = columnName.substring(columnPrefix.length());
            } else {
                continue;
            }
        }
        // 驼峰转换
        final String property = metaObject.findProperty(propertyName, this.configuration.isMapUnderscoreToCamelCase());
        if (property != null && metaObject.hasSetter(property)) {
            final Class<?> propertyType = metaObject.getSetterType(property);
            if (typeHandlerRegistry.hasTypeHandler(propertyType)) {
                // 使用 TypeHandler 获取值并设置
                final TypeHandler<?> typeHandler = rsw.getTypeHandler(propertyType, columnName);
                final Object value = typeHandler.getResult(rsw.getResultSet(), columnName);
                if (value != null || !configuration.isCallSettersOnNulls()) {
                    if (value != null
                        || !propertyType.isPrimitive()) {
                        metaObject.setValue(property, value);
                    }
                }
                foundValues = value != null || foundValues;
            }
        }
    }
    return foundValues;
}
```

---

## 8. 一级缓存与二级缓存源码

### 8.1 一级缓存

一级缓存是 `PerpetualCache`，存储在 `BaseExecutor` 中，作用域为 SqlSession：

```java
// PerpetualCache.java
public class PerpetualCache implements Cache {
    private final String id;
    private final Map<Object, Object> cache = new HashMap<>();  // 简单的 HashMap

    @Override
    public void putObject(Object key, Object value) {
        cache.put(key, value);
    }

    @Override
    public Object getObject(Object key) {
        return cache.get(key);
    }

    @Override
    public Object removeObject(Object key) {
        return cache.remove(key);
    }

    @Override
    public void clear() {
        cache.clear();
    }
}
```

CacheKey 的生成逻辑：

```java
// BaseExecutor.java
@Override
public CacheKey createCacheKey(MappedStatement ms, Object parameterObject,
                               RowBounds rowBounds, BoundSql boundSql) {
    if (closed) {
        throw new ExecutorException("Executor was closed.");
    }
    CacheKey cacheKey = new CacheKey();
    // Statement ID
    cacheKey.update(ms.getId());
    // 分页偏移量
    cacheKey.update(rowBounds.getOffset());
    cacheKey.update(rowBounds.getLimit());
    // SQL 文本
    cacheKey.update(boundSql.getSql());
    // 参数值
    List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();
    for (ParameterMapping parameterMapping : parameterMappings) {
        if (parameterMapping.getMode() != ParameterMode.OUT) {
            Object value;
            String propertyName = parameterMapping.getProperty();
            if (boundSql.hasAdditionalParameter(propertyName)) {
                value = boundSql.getAdditionalParameter(propertyName);
            } else if (parameterObject == null) {
                value = null;
            } else if (typeHandlerRegistry.hasTypeHandler(parameterObject.getClass())) {
                value = parameterObject;
            } else {
                MetaObject metaObject = configuration.newMetaObject(parameterObject);
                value = metaObject.getValue(propertyName);
            }
            cacheKey.update(value);
        }
    }
    // Environment ID
    if (configuration.getEnvironment() != null) {
        cacheKey.update(configuration.getEnvironment().getId());
    }
    return cacheKey;
}
```

一级缓存的失效时机：
- SqlSession 关闭时
- 执行 `commit()` 或 `rollback()` 时
- 执行 `update()` 操作时（清空整个 SqlSession 的一级缓存）
- 配置 `flushCache="true"` 时

### 8.2 二级缓存

二级缓存是跨 SqlSession 的，通过 `CachingExecutor` 装饰器实现：

```java
// CachingExecutor.java
public class CachingExecutor implements Executor {
    private final Executor delegate;  // 被装饰的执行器
    private final TransactionalCacheManager tcm = new TransactionalCacheManager();

    @Override
    public <E> List<E> query(MappedStatement ms, Object parameterObject, RowBounds rowBounds,
                             ResultHandler resultHandler, CacheKey key, BoundSql boundSql) throws SQLException {
        Cache cache = ms.getCache();
        if (cache != null) {
            flushCacheIfRequired(ms);
            if (ms.isUseCache() && resultHandler == null) {
                ensureNoOutParams(ms, boundSql);
                @SuppressWarnings("unchecked")
                List<E> list = (List<E>) tcm.getObject(cache, key);
                if (list == null) {
                    // 委托给底层 Executor 执行
                    list = delegate.query(ms, parameterObject, rowBounds, resultHandler, key, boundSql);
                    // 放入二级缓存（暂存区，提交后才真正写入）
                    tcm.putObject(cache, key, list);
                }
                return list;
            }
        }
        return delegate.query(ms, parameterObject, rowBounds, resultHandler, key, boundSql);
    }

    @Override
    public int update(MappedStatement ms, Object parameterObject) throws SQLException {
        int rows = delegate.update(ms, parameterObject);
        // 更新操作清空二级缓存
        flushCacheIfRequired(ms);
        return rows;
    }

    @Override
    public void commit(boolean required) throws SQLException {
        delegate.commit(required);
        tcm.commit();  // 提交暂存区缓存
    }

    @Override
    public void rollback(boolean required) throws SQLException {
        try {
            delegate.rollback(required);
        } finally {
            if (required) {
                tcm.rollback();
            }
        }
    }
}
```

`TransactionalCacheManager` 使用暂存区机制保证缓存与事务的一致性：

```java
// TransactionalCacheManager.java
public class TransactionalCacheManager {
    private final Map<Cache, TransactionalCache> transactionalCaches = new HashMap<>();

    public void commit() {
        for (TransactionalCache txCache : transactionalCaches.values()) {
            txCache.commit();
        }
    }

    // ...
}

// TransactionalCache.java - 装饰器
public class TransactionalCache implements Cache {
    private final Cache delegate;
    private boolean clearOnCommit;
    private final Map<Object, Object> entriesToAddOnCommit;  // 暂存区

    @Override
    public void putObject(Object key, Object object) {
        // 不直接放入 delegate，而是放入暂存区
        entriesToAddOnCommit.put(key, object);
    }

    public void commit() {
        if (clearOnCommit) {
            delegate.clear();
        }
        // 提交时一次性写入真实缓存
        for (Map.Entry<Object, Object> entry : entriesToAddOnCommit.entrySet()) {
            delegate.putObject(entry.getKey(), entry.getValue());
        }
    }
}
```

这种设计保证了：事务回滚时缓存不会被污染，只有 commit 后缓存才更新。

---

## 9. 插件（拦截器）机制源码

### 9.1 Interceptor 接口

```java
// Interceptor.java
public interface Interceptor {
    // 拦截逻辑
    Object intercept(Invocation invocation) throws Throwable;

    // 包装目标对象
    default Object plugin(Object target) {
        return Plugin.wrap(target, this);
    }

    // 设置属性
    default void setProperties(Properties properties) {
    }
}
```

### 9.2 Plugin 动态代理核心

```java
// Plugin.java
public class Plugin implements InvocationHandler {
    private final Object target;
    private final Interceptor interceptor;
    private final Map<Class<?>, Set<String>> signatureMap;

    private Plugin(Object target, Interceptor interceptor, Map<Class<?>, Set<String>> signatureMap) {
        this.target = target;
        this.interceptor = interceptor;
        this.signatureMap = signatureMap;
    }

    public static Object wrap(Object target, Interceptor interceptor) {
        // 获取拦截器 @Intercepts 注解中定义的签名
        Map<Class<?>, Set<String>> signatureMap = getSignatureMap(interceptor);
        Class<?> type = target.getClass();
        // 获取目标对象实现的所有接口中，被拦截器签名的接口
        Class<?>[] interfaces = getAllInterfaces(type, signatureMap);
        if (interfaces.length > 0) {
            // 创建 JDK 动态代理
            return Proxy.newProxyInstance(
                type.getClassLoader(),
                interfaces,
                new Plugin(target, interceptor, signatureMap));
        }
        return target;
    }

    @Override
    public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
        try {
            // 检查方法是否被拦截
            Set<String> methods = signatureMap.get(method.getDeclaringClass());
            if (methods != null && methods.contains(method.getName())) {
                // 命中拦截，调用拦截器
                return interceptor.intercept(new Invocation(target, method, args));
            }
            // 未命中，直接调用
            return method.invoke(target, args);
        } catch (Exception e) {
            throw ExceptionUtil.unwrapThrowable(e);
        }
    }

    private static Map<Class<?>, Set<String>> getSignatureMap(Interceptor interceptor) {
        Intercepts interceptsAnnotation = interceptor.getClass().getAnnotation(Intercepts.class);
        if (interceptsAnnotation == null) {
            throw new PluginException("No @Intercepts annotation was found in interceptor " +
                interceptor.getClass().getName());
        }
        Signature[] sigs = interceptsAnnotation.value();
        Map<Class<?>, Set<String>> signatureMap = new HashMap<>();
        for (Signature sig : sigs) {
            Set<String> methods = signatureMap.computeIfAbsent(sig.type(), k -> new HashSet<>());
            try {
                methods.add(sig.method());
            } catch (Exception e) {
                throw new PluginException("Could not find method on " + sig.type() + " named " +
                    sig.method() + ". Cause: " + e, e);
            }
        }
        return signatureMap;
    }
}
```

### 9.3 插件链式调用

```java
// InterceptorChain.java
public class InterceptorChain {
    private final List<Interceptor> interceptors = new ArrayList<>();

    public Object pluginAll(Object target) {
        for (Interceptor interceptor : interceptors) {
            // 链式包装：每个拦截器包装前一个结果
            target = interceptor.plugin(target);
        }
        return target;
    }

    public void addInterceptor(Interceptor interceptor) {
        interceptors.add(interceptor);
    }

    public List<Interceptor> getInterceptors() {
        return Collections.unmodifiableList(interceptors);
    }
}
```

插件应用时序图：

```
Configuration.newExecutor()
  └─► InterceptorChain.pluginAll(executor)
        └─► interceptor1.plugin(executor)   → Proxy1
              └─► interceptor2.plugin(Proxy1) → Proxy2
                    └─► interceptor3.plugin(Proxy2) → Proxy3

调用时：Proxy3.invoke() → 拦截? → interceptor3.intercept()
                                   └─► Proxy2.invoke() → 拦截? → interceptor2.intercept()
                                                            └─► Proxy1.invoke() → 拦截? → interceptor1.intercept()
                                                                                     └─► executor.query()
```

### 9.4 自定义分页插件示例

```java
@Intercepts({
    @Signature(type = Executor.class, method = "query",
               args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class})
})
public class PageInterceptor implements Interceptor {

    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        Object[] args = invocation.getArgs();
        MappedStatement ms = (MappedStatement) args[0];
        Object parameter = args[1];
        RowBounds rowBounds = (RowBounds) args[2];

        // 如果参数中包含分页对象
        if (parameter instanceof Map) {
            Object pageObj = ((Map<?, ?>) parameter).get("page");
            if (pageObj instanceof Page) {
                Page<?> page = (Page<?>) pageObj;

                // 1. 先执行 count 查询
                long total = queryCount(ms, parameter);
                page.setTotal(total);

                // 2. 修改 SQL 添加分页
                BoundSql boundSql = ms.getBoundSql(parameter);
                String sql = boundSql.getSql();
                String pageSql = sql + " LIMIT " + page.getOffset() + ", " + page.getSize();

                // 3. 通过反射修改 SQL
                Field sqlField = BoundSql.class.getDeclaredField("sql");
                sqlField.setAccessible(true);
                sqlField.set(boundSql, pageSql);

                // 4. 执行分页查询
                return invocation.proceed();
            }
        }
        return invocation.proceed();
    }
}
```

MyBatis 可拦截的四大对象：

| 对象 | 拦截方法 | 典型用途 |
|------|---------|---------|
| `Executor` | update, query, commit, rollback | 二级缓存、事务控制 |
| `StatementHandler` | prepare, parameterize, batch | SQL 改写、分页 |
| `ParameterHandler` | setParameters | 参数加密、敏感数据处理 |
| `ResultSetHandler` | handleResultSets | 结果脱敏、数据转换 |

---

## 10. 面试题速查

### Q1: MyBatis 中 Mapper 接口为什么不需要实现类？
MyBatis 使用 JDK 动态代理创建 Mapper 接口的代理对象（`MapperProxy`）。调用接口方法时，`MapperProxy.invoke()` 根据方法全限定名查找 `MappedStatement`，然后委托给 `SqlSession` 执行 SQL。

### Q2: MyBatis 的执行器有哪几种？区别是什么？
- `SimpleExecutor`：每次执行创建新 Statement，用完即关（默认）
- `ReuseExecutor`：缓存 Statement 对象，相同 SQL 复用
- `BatchExecutor`：批量执行模式，使用 JDBC addBatch/executeBatch
- `CachingExecutor`：装饰器，在以上三种基础上添加二级缓存

### Q3: 一级缓存和二级缓存的区别？
| | 一级缓存 | 二级缓存 |
|---|---------|---------|
| 作用域 | SqlSession | Mapper namespace（跨 SqlSession） |
| 实现 | PerpetualCache (HashMap) | 可配置 EhCache/Redis 等 |
| 开启 | 默认开启 | 需手动配置 |
| 失效 | update/commit/close | commit 后生效（暂存区机制） |
| 数据一致性 | 同一 SqlSession 内一致 | 跨 Session 需注意脏读 |

### Q4: MyBatis 插件机制原理？可以拦截哪些对象？
基于 JDK 动态代理实现。`InterceptorChain.pluginAll()` 对目标对象链式包装。每次调用被拦截方法时，进入 `Plugin.invoke()`，命中签名则调用拦截器的 `intercept()` 方法。可拦截四大对象：Executor、StatementHandler、ParameterHandler、ResultSetHandler。

### Q5: #{} 和 ${} 的区别？
`#{}` 使用 PreparedStatement 的参数占位符 `?`，通过 TypeHandler 设置参数，可以防止 SQL 注入。`${}` 直接做字符串拼接，存在 SQL 注入风险，但适用于动态表名、列名等场景。

### Q6: MyBatis 动态 SQL 是如何实现的？
SQL 节点被解析为 `SqlNode` 树（如 `IfSqlNode`、`ForeachSqlNode`、`TextSqlNode` 等），执行时通过 `DynamicContext` 上下文逐节点 apply，最终生成完整 SQL。如果是动态 SQL 使用 `DynamicSqlSource`，静态 SQL 使用 `RawSqlSource`。

### Q7: 二级缓存的暂存区机制是什么？
`CachingExecutor` 查询结果不直接放入缓存，而是放入 `TransactionalCache` 的 `entriesToAddOnCommit` 暂存区。只有事务 commit 后，暂存区数据才写入真实缓存。这保证了回滚时缓存不会被脏数据污染。

### Q8: MyBatis 如何处理延迟加载？
使用 `ProxyFactory`（CGLIB 或 Javassist）创建代理对象。当访问关联属性时，代理拦截方法调用，触发 `ResultLoader` 从数据库加载数据。通过 `lazyLoadTriggerMethods` 配置可以控制触发加载的方法。

### Q9: MyBatis 的 CacheKey 包含哪些要素？
- MappedStatement ID（namespace + 方法名）
- RowBounds 偏移量和限制
- SQL 文本
- 所有参数值
- Environment ID

这些要素组合计算的 hashcode 决定缓存命中。

### Q10: 为什么 MyBatis 插件是责任链模式而非 AOP？
MyBatis 插件基于 JDK 动态代理实现链式包装，每个拦截器包装前一个代理对象。相比 AOP（如 Spring AOP 的字节码增强或 CGLIB），这种方式更轻量、无额外依赖，且精确控制拦截点（通过 @Signature 注解）。AOP 更通用但复杂度更高，MyBatis 选择更简单可控的方案。

---

> **总结**：MyBatis 源码的核心设计是**模板方法 + 责任链 + 代理模式**的组合。Executor 用模板方法控制执行流程并管理一级缓存，CachingExecutor 用装饰器模式实现二级缓存，插件机制用动态代理实现责任链。理解这些设计模式在 MyBatis 中的实际应用，不仅有助于掌握 MyBatis 本身，更对理解框架设计哲学大有裨益。

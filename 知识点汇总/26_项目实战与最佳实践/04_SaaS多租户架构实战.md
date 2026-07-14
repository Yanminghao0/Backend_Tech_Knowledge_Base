# SaaS多租户架构实战

> SaaS（Software as a Service）系统的核心挑战是在同一套代码、同一套基础设施上服务多个租户，既要做到资源隔离和安全保障，又要兼顾成本效益和运维效率。本文系统梳理多租户架构的设计方案与落地实践。

---

## 📋 目录

1. [多租户架构概述](#1-多租户架构概述)
2. [租户隔离方案对比](#2-租户隔离方案对比)
3. [共享DB独立Schema方案](#3-共享db独立schema方案)
4. [独立DB方案](#4-独立db方案)
5. [数据路由机制](#5-数据路由机制)
6. [租户上下文管理](#6-租户上下文管理)
7. [计费模型设计](#7-计费模型设计)
8. [可扩展性设计](#8-可扩展性设计)
9. [安全与合规](#9-安全与合规)
10. [面试题速查](#10-面试题速查)

---

## 1. 多租户架构概述

### 1.1 什么是多租户

多租户（Multi-Tenancy）是指一套软件系统同时服务多个客户（租户），每个租户的数据彼此隔离，但共享同一套应用程序代码和基础设施。

```
┌────────────────────────────────────────────┐
│              SaaS 应用层                    │
│        (同一套代码服务所有租户)              │
├────────────────────────────────────────────┤
│  租户A   │  租户B   │  租户C   │  租户D    │
│  数据    │  数据    │  数据    │  数据      │
├────────────────────────────────────────────┤
│         共享的基础设施                      │
│    (服务器/数据库/缓存/存储)                │
└────────────────────────────────────────────┘
```

### 1.2 核心设计目标

| 目标 | 描述 |
|------|------|
| 数据隔离 | 租户间数据绝对隔离，不能交叉访问 |
| 资源共享 | 代码和基础设施共享，降低成本 |
| 弹性扩展 | 大租户可以独立扩展，不影响小租户 |
| 按需计费 | 根据使用量精确计费 |
| 定制能力 | 支持租户级别的配置和定制 |
| 运维效率 | 统一部署升级，降低运维成本 |

---

## 2. 租户隔离方案对比

### 2.1 三种经典方案

```
方案一: 共享DB共享Schema (字段隔离)
┌─────────────────────────────┐
│       Database              │
│  ┌─────────────────────┐    │
│  │ Table: orders        │    │
│  │ id | tenant_id | ... │    │  ← 每行带tenant_id
│  └─────────────────────┘    │
└─────────────────────────────┘

方案二: 共享DB独立Schema
┌─────────────────────────────────┐
│         Database                │
│  ┌──────┐ ┌──────┐ ┌──────┐    │
│  │租户A  │ │租户B  │ │租户C  │    │  ← 每个租户独立Schema
│  │Schema│ │Schema│ │Schema│    │
│  └──────┘ └──────┘ └──────┘    │
└─────────────────────────────────┘

方案三: 独立DB
┌──────────┐ ┌──────────┐ ┌──────────┐
│ 租户A DB  │ │ 租户B DB  │ │ 租户C DB  │   ← 每个租户独立数据库
└──────────┘ └──────────┘ └──────────┘
```

### 2.2 详细对比

| 维度 | 共享DB共享Schema | 共享DB独立Schema | 独立DB |
|------|-----------------|-----------------|--------|
| 隔离级别 | 低 | 中 | 高 |
| 成本 | 最低 | 低 | 高 |
| 运维复杂度 | 低 | 中 | 高 |
| 数据隔离性 | 弱(逻辑隔离) | 中(Schema隔离) | 强(物理隔离) |
| 定制能力 | 弱 | 中 | 强 |
| 扩展性 | 好 | 中 | 差 |
| 单租户性能影响 | 大 | 小 | 无 |
| 备份恢复 | 全量备份 | 按Schema备份 | 按DB备份 |
| 适合租户数 | 数千~数万 | 数百~数千 | 数十~数百 |
| 典型产品 | Slack早期 | 阿里云部分产品 | 大型企业SaaS |

### 2.3 混合方案

实际生产中通常采用混合策略：

```
租户分级:
├── 小租户 (免费/基础版) → 共享DB共享Schema (字段隔离)
├── 中租户 (专业版)     → 共享DB独立Schema
├── 大租户 (企业版)     → 独立DB
└── VIP租户 (私有化)    → 独立集群
```

```java
/**
 * 租户级别与隔离策略映射
 */
public enum TenantLevel {
    FREE("免费版", IsolationStrategy.SHARED_DB_SHARED_SCHEMA),
    PROFESSIONAL("专业版", IsolationStrategy.SHARED_DB_INDEPENDENT_SCHEMA),
    ENTERPRISE("企业版", IsolationStrategy.INDEPENDENT_DB),
    PRIVATE("私有化", IsolationStrategy.INDEPENDENT_CLUSTER);

    private final String desc;
    private final IsolationStrategy strategy;
}

public enum IsolationStrategy {
    SHARED_DB_SHARED_SCHEMA,      // 共享DB共享Schema
    SHARED_DB_INDEPENDENT_SCHEMA,  // 共享DB独立Schema
    INDEPENDENT_DB,                // 独立DB
    INDEPENDENT_CLUSTER            // 独立集群
}
```

---

## 3. 共享DB独立Schema方案

### 3.1 Schema管理

```java
/**
 * 租户Schema管理器
 * 每个租户拥有独立的数据库Schema
 */
@Service
public class TenantSchemaManager {

    @Autowired
    private DataSource dataSource;

    /**
     * 为新租户创建Schema
     */
    @Transactional
    public void createTenantSchema(String tenantId) {
        String schemaName = "tenant_" + tenantId;
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {

            // 1. 创建Schema
            stmt.execute("CREATE SCHEMA " + schemaName);

            // 2. 执行建表DDL
            String ddl = loadSchemaDDL();
            // 替换Schema名称
            ddl = ddl.replace("${schema}", schemaName);
            for (String sql : ddl.split(";")) {
                if (!sql.trim().isEmpty()) {
                    stmt.execute(sql);
                }
            }

            // 3. 创建数据库用户并授权
            String dbUser = "u_" + tenantId;
            stmt.execute("CREATE USER " + dbUser + " IDENTIFIED BY '" + generatePassword() + "'");
            stmt.execute("GRANT ALL PRIVILEGES ON " + schemaName + ".* TO " + dbUser);

            log.info("租户Schema创建成功: {}", schemaName);
        } catch (SQLException e) {
            throw new RuntimeException("创建租户Schema失败: " + tenantId, e);
        }
    }

    /**
     * 删除租户Schema
     */
    public void dropTenantSchema(String tenantId) {
        String schemaName = "tenant_" + tenantId;
        try (Connection conn = dataSource.getConnection();
             Statement stmt = conn.createStatement()) {
            stmt.execute("DROP SCHEMA IF EXISTS " + schemaName + " CASCADE");
            log.info("租户Schema已删除: {}", schemaName);
        } catch (SQLException e) {
            throw new RuntimeException("删除租户Schema失败: " + tenantId, e);
        }
    }

    /**
     * 加载建表DDL模板
     */
    private String loadSchemaDDL() {
        try {
            return new String(
                getClass().getResourceAsStream("/sql/tenant_schema_template.sql").readAllBytes(),
                StandardCharsets.UTF_8
            );
        } catch (IOException e) {
            throw new RuntimeException("加载Schema模板失败", e);
        }
    }
}
```

### 3.2 Schema模板SQL

```sql
-- tenant_schema_template.sql
-- 所有租户共享相同的表结构，但各自在独立Schema中

CREATE TABLE ${schema}.sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(128) NOT NULL,
    email VARCHAR(128),
    phone VARCHAR(32),
    status TINYINT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX uk_username(username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ${schema}.biz_order (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(64) NOT NULL,
    user_id BIGINT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status TINYINT DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX uk_order_no(order_no),
    INDEX idx_user(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 4. 独立DB方案

### 4.1 动态数据源管理

```java
/**
 * 动态数据源管理器
 * 为每个租户维护独立的数据源连接池
 */
@Component
public class DynamicDataSourceManager {

    private final ConcurrentHashMap<String, DataSource> dataSourceMap = new ConcurrentHashMap<>();

    @Autowired
    private TenantDataSourceConfig config;

    private DataSource defaultDataSource;

    /**
     * 获取租户数据源
     */
    public DataSource getDataSource(String tenantId) {
        return dataSourceMap.computeIfAbsent(tenantId, this::createDataSource);
    }

    /**
     * 创建租户数据源
     */
    private DataSource createDataSource(String tenantId) {
        TenantDBConfig dbConfig = config.getConfig(tenantId);
        if (dbConfig == null) {
            return defaultDataSource; // 降级到默认数据源
        }

        HikariConfig hikariConfig = new HikariConfig();
        hikariConfig.setJdbcUrl(dbConfig.getJdbcUrl());
        hikariConfig.setUsername(dbConfig.getUsername());
        hikariConfig.setPassword(dbConfig.getPassword());
        hikariConfig.setDriverClassName("com.mysql.cj.jdbc.Driver");

        // 连接池配置
        hikariConfig.setMaximumPoolSize(20);
        hikariConfig.setMinimumIdle(5);
        hikariConfig.setConnectionTimeout(30000);
        hikariConfig.setIdleTimeout(600000);
        hikariConfig.setMaxLifetime(1800000);

        HikariDataSource dataSource = new HikariDataSource(hikariConfig);
        log.info("租户数据源创建: tenantId={}", tenantId);
        return dataSource;
    }

    /**
     * 销毁租户数据源
     */
    public void removeDataSource(String tenantId) {
        DataSource ds = dataSourceMap.remove(tenantId);
        if (ds instanceof HikariDataSource) {
            ((HikariDataSource) ds).close();
            log.info("租户数据源已关闭: tenantId={}", tenantId);
        }
    }

    /**
     * 租户数据源健康检查
     */
    @Scheduled(fixedRate = 60000)
    public void healthCheck() {
        dataSourceMap.forEach((tenantId, ds) -> {
            if (ds instanceof HikariDataSource) {
                HikariDataSource hikari = (HikariDataSource) ds;
                if (hikari.isClosed()) {
                    log.warn("租户数据源异常: tenantId={}", tenantId);
                    dataSourceMap.remove(tenantId);
                }
            }
        });
    }
}
```

### 4.2 动态数据源路由

```java
/**
 * 继承AbstractRoutingDataSource实现租户级数据源路由
 */
public class TenantAwareDataSource extends AbstractRoutingDataSource {

    @Autowired
    private DynamicDataSourceManager dataSourceManager;

    @Override
    protected Object determineCurrentLookupKey() {
        return TenantContext.getTenantId();
    }

    @Override
    protected DataSource determineTargetDataSource() {
        String tenantId = TenantContext.getTenantId();
        if (tenantId == null) {
            return getDefaultDataSource();
        }
        return dataSourceManager.getDataSource(tenantId);
    }
}

/**
 * Spring配置
 */
@Configuration
public class DataSourceConfig {

    @Bean
    @Primary
    public DataSource dataSource(DynamicDataSourceManager manager) {
        TenantAwareDataSource dataSource = new TenantAwareDataSource();
        dataSource.setDataSourceManager(manager);
        // 设置默认数据源(用于系统级操作)
        Map<Object, Object> targetDataSources = new HashMap<>();
        targetDataSources.put("default", manager.getDefaultDataSource());
        dataSource.setTargetDataSources(targetDataSources);
        dataSource.setDefaultTargetDataSource(manager.getDefaultDataSource());
        return dataSource;
    }
}
```

---

## 5. 数据路由机制

### 5.1 共享Schema字段隔离路由

```java
/**
 * 基于MyBatis-Plus的租户字段拦截器
 * 自动在SQL中添加tenant_id条件
 */
@Component
public class TenantSqlInterceptor implements InnerInterceptor {

    private static final String TENANT_COLUMN = "tenant_id";

    /**
     * 查询时自动添加租户条件
     */
    @Override
    public void beforeQuery(Executor executor, MappedStatement ms,
            Object parameter, RowBounds rowBounds, ResultHandler resultHandler,
            BoundSql boundSql) throws SQLException {
        String tenantId = TenantContext.getTenantId();
        if (tenantId == null) return;

        String sql = boundSql.getSql();
        String newSql = addTenantCondition(sql, tenantId);
        reflectSetFieldValue(boundSql, "sql", newSql);
    }

    /**
     * 为SQL添加tenant_id条件
     */
    private String addTenantCondition(String sql, String tenantId) {
        // 使用JSqlParse解析并修改SQL
        Statement statement = CCJSqlParserUtil.parse(sql);
        Select select = (Select) statement;

        PlainSelect plainSelect = (PlainSelect) select.getSelectBody();
        Expression where = plainSelect.getWhere();

        EqualsTo tenantCondition = new EqualsTo();
        tenantCondition.setLeftExpression(new Column(TENANT_COLUMN));
        tenantCondition.setRightExpression(new StringLiteral("'" + tenantId + "'"));

        if (where == null) {
            plainSelect.setWhere(tenantCondition);
        } else {
            AndExpression and = new AndExpression(where, tenantCondition);
            plainSelect.setWhere(and);
        }

        return select.toString();
    }

    /**
     * INSERT时自动填充tenant_id
     */
    @Override
    public void beforeInsert(Executor executor, MappedStatement ms,
            Object parameter) throws SQLException {
        String tenantId = TenantContext.getTenantId();
        if (tenantId == null) return;

        // 通过反射为实体对象设置tenantId
        if (parameter instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) parameter;
            for (Object value : map.values()) {
                if (value instanceof TenantAware) {
                    ((TenantAware) value).setTenantId(tenantId);
                }
            }
        } else if (parameter instanceof TenantAware) {
            ((TenantAware) parameter).setTenantId(tenantId);
        }
    }
}
```

### 5.2 MyBatis-Plus租户插件配置

```java
/**
 * MyBatis-Plus租户插件配置
 */
@Configuration
public class MybatisPlusTenantConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();

        // 租户插件
        TenantLineInnerInterceptor tenantInterceptor = new TenantLineInnerInterceptor();
        tenantInterceptor.setTenantLineHandler(new TenantLineHandler() {
            @Override
            public Expression getTenantId() {
                String tenantId = TenantContext.getTenantId();
                if (tenantId == null) {
                    throw new IllegalStateException("租户ID不能为空");
                }
                return new StringValue(tenantId);
            }

            @Override
            public String getTenantIdColumn() {
                return "tenant_id";
            }

            @Override
            public boolean ignoreTable(String tableName) {
                // 系统表不需要租户隔离
                return tableName.startsWith("sys_global_") ||
                       tableName.equals("t_tenant_info") ||
                       tableName.equals("t_tenant_config");
            }
        });

        interceptor.addInnerInterceptor(tenantInterceptor);
        // 分页插件
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));

        return interceptor;
    }
}
```

---

## 6. 租户上下文管理

### 6.1 租户上下文

```java
/**
 * 租户上下文
 * 基于ThreadLocal存储当前请求的租户信息
 */
public class TenantContext {

    private static final ThreadLocal<TenantInfo> CONTEXT = new ThreadLocal<>();

    public static void setTenantId(String tenantId) {
        TenantInfo info = CONTEXT.get();
        if (info == null) {
            info = new TenantInfo();
            CONTEXT.set(info);
        }
        info.setTenantId(tenantId);
    }

    public static String getTenantId() {
        TenantInfo info = CONTEXT.get();
        return info != null ? info.getTenantId() : null;
    }

    public static void setTenantInfo(TenantInfo tenantInfo) {
        CONTEXT.set(tenantInfo);
    }

    public static TenantInfo getTenantInfo() {
        return CONTEXT.get();
    }

    public static void clear() {
        CONTEXT.remove();
    }

    @Data
    public static class TenantInfo {
        private String tenantId;
        private String tenantName;
        private TenantLevel level;
        private IsolationStrategy isolationStrategy;
        private String dbSchema;
        private String dbUrl;
        private int maxUsers;
        private LocalDateTime expireTime;
    }
}
```

### 6.2 租户解析过滤器

```java
/**
 * 租户解析过滤器
 * 从请求中提取租户信息并设置到上下文
 */
@Component
public class TenantResolverFilter extends OncePerRequestFilter {

    @Autowired
    private TenantInfoService tenantInfoService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        try {
            // 1. 从请求头/域名/Token中解析租户ID
            String tenantId = resolveTenantId(request);
            if (tenantId == null) {
                response.setStatus(400);
                response.getWriter().write("{\"code\":400,\"message\":\"缺少租户标识\"}");
                return;
            }

            // 2. 查询租户信息
            TenantInfo tenantInfo = tenantInfoService.getTenantInfo(tenantId);
            if (tenantInfo == null) {
                response.setStatus(404);
                response.getWriter().write("{\"code\":404,\"message\":\"租户不存在\"}");
                return;
            }

            // 3. 校验租户状态
            if (tenantInfo.getExpireTime() != null &&
                tenantInfo.getExpireTime().isBefore(LocalDateTime.now())) {
                response.setStatus(403);
                response.getWriter().write("{\"code\":403,\"message\":\"租户已过期\"}");
                return;
            }

            // 4. 设置租户上下文
            TenantContext.setTenantInfo(tenantInfo);

            filterChain.doFilter(request, response);
        } finally {
            // 清理ThreadLocal
            TenantContext.clear();
        }
    }

    /**
     * 多策略解析租户ID
     */
    private String resolveTenantId(HttpServletRequest request) {
        // 策略1: 请求头 X-Tenant-Id
        String tenantId = request.getHeader("X-Tenant-Id");
        if (tenantId != null) return tenantId;

        // 策略2: 子域名解析 (tenantId.example.com)
        String host = request.getServerName();
        if (host.contains(".")) {
            String subdomain = host.split("\\.")[0];
            if (!"www".equals(subdomain) && !"api".equals(subdomain)) {
                return subdomain;
            }
        }

        // 策略3: JWT Token中的租户信息
        String auth = request.getHeader("Authorization");
        if (auth != null && auth.startsWith("Bearer ")) {
            String token = auth.substring(7);
            Claims claims = JwtUtil.parse(token);
            return claims.get("tenant_id", String.class);
        }

        // 策略4: 请求参数
        return request.getParameter("tenant_id");
    }
}
```

### 6.3 异步任务租户传递

```java
/**
 * 异步任务中传递租户上下文
 * ThreadLocal不能自动传递到子线程，需要手动处理
 */
@Configuration
public class TenantAsyncConfig {

    @Bean
    public TaskDecorator tenantTaskDecorator() {
        return runnable -> {
            // 在主线程中捕获租户上下文
            TenantContext.TenantInfo tenantInfo = TenantContext.getTenantInfo();
            return () -> {
                try {
                    // 在子线程中恢复租户上下文
                    if (tenantInfo != null) {
                        TenantContext.setTenantInfo(tenantInfo);
                    }
                    runnable.run();
                } finally {
                    TenantContext.clear();
                }
            };
        };
    }

    @Bean
    public ThreadPoolTaskExecutor taskExecutor(TaskDecorator tenantTaskDecorator) {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(200);
        executor.setTaskDecorator(tenantTaskDecorator);
        executor.initialize();
        return executor;
    }
}
```

---

## 7. 计费模型设计

### 7.1 计费模型架构

```sql
-- 租户套餐表
CREATE TABLE t_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL COMMENT '套餐名称',
    level TINYINT NOT NULL COMMENT '1免费 2专业 3企业',
    price_monthly DECIMAL(10,2) COMMENT '月费',
    price_yearly DECIMAL(10,2) COMMENT '年费',
    max_users INT NOT NULL COMMENT '最大用户数',
    max_storage BIGINT NOT NULL COMMENT '最大存储(字节)',
    max_api_calls INT NOT NULL COMMENT '月API调用上限',
    features JSON COMMENT '功能特性列表',
    status TINYINT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 租户订阅表
CREATE TABLE t_subscription (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id VARCHAR(64) NOT NULL,
    plan_id BIGINT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status TINYINT DEFAULT 1 COMMENT '1有效 2过期 3取消',
    auto_renew TINYINT DEFAULT 1 COMMENT '自动续费',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant(tenant_id)
);

-- 用量记录表
CREATE TABLE t_usage_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id VARCHAR(64) NOT NULL,
    usage_date DATE NOT NULL,
    user_count INT DEFAULT 0 COMMENT '用户数',
    storage_used BIGINT DEFAULT 0 COMMENT '存储使用量',
    api_calls INT DEFAULT 0 COMMENT 'API调用次数',
    UNIQUE INDEX uk_tenant_date(tenant_id, usage_date)
);

-- 账单表
CREATE TABLE t_invoice (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_id VARCHAR(64) NOT NULL,
    invoice_no VARCHAR(64) UNIQUE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status TINYINT DEFAULT 0 COMMENT '0待支付 1已支付 2已逾期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant(tenant_id)
);
```

### 7.2 用量计量服务

```java
/**
 * 用量计量服务
 * 实时统计租户资源使用情况
 */
@Service
public class UsageMeteringService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Autowired
    private UsageRecordMapper usageRecordMapper;

    /**
     * 记录API调用
     */
    public void recordApiCall(String tenantId) {
        String key = "usage:api:" + tenantId + ":" + LocalDate.now();
        redisTemplate.opsForValue().increment(key);
        redisTemplate.expire(key, 35, TimeUnit.DAYS);
    }

    /**
     * 记录存储使用
     */
    public void recordStorage(String tenantId, long bytes) {
        String key = "usage:storage:" + tenantId;
        redisTemplate.opsForValue().increment(key, bytes);
    }

    /**
     * 检查用量是否超限
     */
    public UsageCheckResult checkLimit(String tenantId) {
        TenantContext.TenantInfo tenant = TenantContext.getTenantInfo();
        Plan plan = planService.getById(tenant.getPlanId());

        // 检查API调用限制
        String apikey = "usage:api:" + tenantId + ":" + LocalDate.now();
        Long apiCalls = Long.parseLong(
            redisTemplate.opsForValue().get(apikey) != null ?
            redisTemplate.opsForValue().get(apikey) : "0");

        // 检查用户数限制
        int userCount = userService.countByTenant(tenantId);

        // 检查存储限制
        String storageKey = "usage:storage:" + tenantId;
        Long storage = Long.parseLong(
            redisTemplate.opsForValue().get(storageKey) != null ?
            redisTemplate.opsForValue().get(storageKey) : "0");

        UsageCheckResult result = new UsageCheckResult();
        result.setApiCallsExceeded(apiCalls >= plan.getMaxApiCalls());
        result.setUsersExceeded(userCount >= plan.getMaxUsers());
        result.setStorageExceeded(storage >= plan.getMaxStorage());
        return result;
    }

    /**
     * 每日用量快照
     */
    @Scheduled(cron = "0 0 2 * * ?")
    public void dailyUsageSnapshot() {
        List<String> tenantIds = tenantInfoService.getAllActiveTenantIds();
        for (String tenantId : tenantIds) {
            UsageRecord record = new UsageRecord();
            record.setTenantId(tenantId);
            record.setUsageDate(LocalDate.now().minusDays(1));
            record.setUserCount(userService.countByTenant(tenantId));

            String storageKey = "usage:storage:" + tenantId;
            String storage = redisTemplate.opsForValue().get(storageKey);
            record.setStorageUsed(storage != null ? Long.parseLong(storage) : 0);

            String apiKey = "usage:api:" + tenantId + ":" + LocalDate.now().minusDays(1);
            String apiCalls = redisTemplate.opsForValue().get(apiKey);
            record.setApiCalls(apiCalls != null ? Integer.parseInt(apiCalls) : 0);

            usageRecordMapper.insertOrUpdate(record);
        }
    }
}
```

### 7.3 自动账单生成

```java
/**
 * 账单生成服务
 */
@Service
public class InvoiceService {

    /**
     * 每月1号自动生成账单
     */
    @Scheduled(cron = "0 0 0 1 * ?")
    public void generateMonthlyInvoices() {
        List<String> activeTenants = tenantInfoService.getPaidTenantIds();
        for (String tenantId : activeTenants) {
            try {
                generateInvoice(tenantId);
            } catch (Exception e) {
                log.error("账单生成失败, tenantId: {}", tenantId, e);
            }
        }
    }

    @Transactional
    public void generateInvoice(String tenantId) {
        TenantContext.TenantInfo tenant = tenantInfoService.getTenantInfo(tenantId);
        Plan plan = planService.getById(tenant.getPlanId());

        // 计算账期
        LocalDate periodStart = LocalDate.now().minusMonths(1).withDayOfMonth(1);
        LocalDate periodEnd = LocalDate.now().minusDays(1);

        // 统计用量
        UsageSummary usage = usageRecordMapper.summarize(tenantId, periodStart, periodEnd);

        // 计算费用
        BigDecimal amount = plan.getPriceMonthly();
        // 超量费用
        if (usage.getApiCalls() > plan.getMaxApiCalls()) {
            int extra = usage.getApiCalls() - plan.getMaxApiCalls();
            amount = amount.add(BigDecimal.valueOf(extra * 0.001)); // 每次API调用0.001元
        }
        if (usage.getStorageUsed() > plan.getMaxStorage()) {
            long extraBytes = usage.getStorageUsed() - plan.getMaxStorage();
            double extraGB = extraBytes / (1024.0 * 1024 * 1024);
            amount = amount.add(BigDecimal.valueOf(extraGB * 0.5)); // 每GB 0.5元
        }

        // 创建账单
        Invoice invoice = new Invoice();
        invoice.setTenantId(tenantId);
        invoice.setInvoiceNo(generateInvoiceNo());
        invoice.setPeriodStart(periodStart);
        invoice.setPeriodEnd(periodEnd);
        invoice.setAmount(amount);
        invoice.setStatus(0); // 待支付
        invoiceMapper.insert(invoice);

        // 通知租户管理员
        notifyService.sendInvoiceNotification(tenantId, invoice);
    }
}
```

---

## 8. 可扩展性设计

### 8.1 租户级别配置

```java
/**
 * 租户配置服务
 * 每个租户可以自定义配置
 */
@Service
public class TenantConfigService {

    @Autowired
    private StringRedisTemplate redisTemplate;

    /**
     * 获取租户配置
     * 三级配置: 租户配置 > 套餐默认配置 > 系统默认配置
     */
    public <T> T getConfig(String tenantId, String configKey, Class<T> type) {
        // 1. 租户自定义配置
        String key = "tenant:config:" + tenantId + ":" + configKey;
        String value = redisTemplate.opsForValue().get(key);
        if (value != null) {
            return JSON.parseObject(value, type);
        }

        // 2. 套餐默认配置
        TenantContext.TenantInfo tenant = tenantInfoService.getTenantInfo(tenantId);
        Plan plan = planService.getById(tenant.getPlanId());
        Map<String, Object> planDefaults = plan.getFeatures();
        if (planDefaults != null && planDefaults.containsKey(configKey)) {
            return JSON.parseObject(JSON.toJSONString(planDefaults.get(configKey)), type);
        }

        // 3. 系统默认配置
        return systemConfigService.getDefault(configKey, type);
    }

    /**
     * 设置租户配置
     */
    public void setConfig(String tenantId, String configKey, Object value) {
        String key = "tenant:config:" + tenantId + ":" + configKey;
        redisTemplate.opsForValue().set(key, JSON.toJSONString(value));
    }
}
```

### 8.2 租户级别功能开关

```java
/**
 * 功能开关服务
 * 不同租户可以启用/禁用不同功能模块
 */
@Service
public class FeatureToggleService {

    /**
     * 检查租户是否拥有某功能
     */
    public boolean hasFeature(String tenantId, Feature feature) {
        TenantContext.TenantInfo tenant = TenantContext.getTenantInfo();
        if (tenant == null) return false;

        Plan plan = planService.getById(tenant.getPlanId());
        Set<Feature> planFeatures = plan.getFeatureSet();

        // 套餐不包含该功能
        if (!planFeatures.contains(feature)) {
            return false;
        }

        // 租户是否禁用了该功能
        String key = "tenant:feature:" + tenantId + ":" + feature.name();
        String disabled = redisTemplate.opsForValue().get(key);
        return !"false".equals(disabled);
    }

    /**
     * 注解式功能控制
     */
    @Target(ElementType.METHOD)
    @Retention(RetentionPolicy.RUNTIME)
    public @interface RequireFeature {
        Feature value();
    }

    /**
     * AOP拦截器
     */
    @Aspect
    @Component
    public static class FeatureAspect {
        @Autowired
        private FeatureToggleService toggleService;

        @Around("@annotation(requireFeature)")
        public Object checkFeature(ProceedingJoinPoint pjp, RequireFeature requireFeature) throws Throwable {
            String tenantId = TenantContext.getTenantId();
            if (!toggleService.hasFeature(tenantId, requireFeature.value())) {
                throw new FeatureNotAvailableException("当前套餐不支持该功能，请升级");
            }
            return pjp.proceed();
        }
    }
}
```

### 8.3 大租户独立迁移

```java
/**
 * 租户迁移服务
 * 当小租户成长为中大租户时，迁移到独立DB
 */
@Service
public class TenantMigrationService {

    /**
     * 迁移租户到独立DB
     */
    public void migrateToIndependentDB(String tenantId) {
        log.info("开始迁移租户到独立DB: {}", tenantId);

        // 1. 创建新数据库
        String newDbName = "saas_tenant_" + tenantId;
        createDatabase(newDbName);

        // 2. 数据迁移
        migrateData(tenantId, newDbName);

        // 3. 更新路由配置
        updateDataSourceConfig(tenantId, newDbName);

        // 4. 灰度切换 (双写过渡)
        enableDualWrite(tenantId);

        // 5. 验证数据一致性
        verifyDataConsistency(tenantId);

        // 6. 切换到新数据源
        switchDataSource(tenantId);

        // 7. 清理旧数据
        cleanupOldData(tenantId);

        log.info("租户迁移完成: {}", tenantId);
    }

    /**
     * 数据迁移
     */
    private void migrateData(String tenantId, String newDbName) {
        // 从共享库查询租户所有数据
        List<String> tables = Arrays.asList("sys_user", "biz_order", "biz_product");

        for (String table : tables) {
            int page = 1;
            int size = 5000;
            while (true) {
                // 从源表分页读取
                List<Map<String, Object>> records = sourceJdbcTemplate.queryForList(
                    "SELECT * FROM " + table + " WHERE tenant_id = ? LIMIT ?, ?",
                    tenantId, (page - 1) * size, size);

                if (records.isEmpty()) break;

                // 批量写入目标表
                batchInsert(newDbName, table, records);

                if (records.size() < size) break;
                page++;
            }
        }
    }
}
```

---

## 9. 安全与合规

### 9.1 数据安全隔离

```java
/**
 * 数据访问安全检查
 */
@Aspect
@Component
public class TenantSecurityAspect {

    /**
     * 拦截所有Repository查询，确保带租户条件
     */
    @Around("execution(* com.saas..repository.*.*(..))")
    public Object checkTenantIsolation(ProceedingJoinPoint pjp) throws Throwable {
        String tenantId = TenantContext.getTenantId();

        // 系统级操作不需要租户检查
        if (isSystemOperation(pjp)) {
            return pjp.proceed();
        }

        if (tenantId == null) {
            throw new SecurityException("非系统操作必须指定租户上下文");
        }

        return pjp.proceed();
    }

    /**
     * 防止跨租户访问
     */
    @AfterReturning(pointcut = "execution(* com.saas..service.*.get*(..))", returning = "result")
    public void verifyTenantAccess(Object result) {
        if (result instanceof TenantAware) {
            String entityTenantId = ((TenantAware) result).getTenantId();
            String currentTenantId = TenantContext.getTenantId();
            if (!entityTenantId.equals(currentTenantId)) {
                throw new SecurityException("非法跨租户数据访问");
            }
        }
    }
}
```

### 9.2 数据加密

```java
/**
 * 租户数据加密
 * 敏感数据使用租户专属密钥加密
 */
@Service
public class TenantEncryptionService {

    /**
     * 获取租户加密密钥
     */
    public SecretKey getTenantKey(String tenantId) {
        // 从密钥管理服务(KMS)获取租户密钥
        String keyMaterial = kmsService.decrypt(
            tenantKeyMapper.getEncryptedKey(tenantId)
        );
        return new SecretKeySpec(
            Base64.getDecoder().decode(keyMaterial),
            "AES"
        );
    }

    /**
     * 加密敏感字段
     */
    public String encrypt(String tenantId, String plaintext) {
        SecretKey key = getTenantKey(tenantId);
        return AESUtil.encrypt(plaintext, key);
    }

    /**
     * 解密敏感字段
     */
    public String decrypt(String tenantId, String ciphertext) {
        SecretKey key = getTenantKey(tenantId);
        return AESUtil.decrypt(ciphertext, key);
    }
}
```

---

## 10. 面试题速查

**Q1: SaaS多租户三种隔离方案的优缺点？**

共享DB共享Schema(字段隔离)：成本最低、运维简单，但隔离性最差，单表数据量大影响性能。共享DB独立Schema：中等隔离，按Schema分开管理，适合中等规模租户。独立DB：隔离最强、性能最好，但成本高、运维复杂。实际中用混合策略：小租户共享、大租户独立。

**Q2: 如何实现自动化的租户数据路由？**

共享Schema模式用MyBatis-Plus租户插件，自动在SQL中拼接tenant_id条件，INSERT时自动填充。独立Schema/DB模式用AbstractRoutingDataSource动态切换数据源，基于ThreadLocal的TenantContext路由。异步任务需要通过TaskDecorator传递租户上下文。

**Q3: 租户上下文怎么在异步线程中传递？**

ThreadLocal不能自动传递到子线程。方案：① 线程池配置TaskDecorator，在任务提交时捕获TenantContext，在任务执行前恢复；② @Async方法配合TaskDecorator自动传递；③ MQ消息中携带tenantId，消费端解析后设置到上下文。

**Q4: 大租户从小租户迁移到独立DB怎么做？**

① 创建新数据库和表结构；② 全量数据迁移(分页读取+批量写入)；③ 开启双写(同时写旧库和新库)；④ 数据一致性校验；⑤ 灰度切读流量到新库；⑥ 完全切换数据源；⑦ 清理旧库数据。整个过程需要支持回滚。

**Q5: SaaS计费系统怎么设计？**

三级模型：套餐(Plan)→订阅(Subscription)→用量(Usage)。实时用量记录到Redis(计数器)，每日快照到数据库。账单按月生成：基础月费+超量费用(API调用超额、存储超额)。支持自动续费和到期降级。用量检查在每次API请求时拦截。

**Q6: 如何防止租户间数据泄露？**

① SQL层：MyBatis-Plus租户插件自动加tenant_id条件，全表扫描不可能跨租户；② AOP层：查询结果返回前校验entity的tenantId与当前上下文一致；③ 数据库层：独立DB的大租户物理隔离；④ 加密层：敏感数据用租户专属密钥加密；⑤ 审计层：记录所有数据访问日志。

**Q7: 租户级别功能开关怎么实现？**

三级配置优先级：租户配置 > 套餐默认 > 系统默认。用注解@RequireFeature标注需要特定功能的接口，AOP拦截器检查租户是否拥有该功能。功能列表定义在Plan中，租户可以在套餐范围内启用/禁用功能。

**Q8: 多租户缓存如何隔离？**

Key前缀隔离：所有Redis Key加上`tenant:{tenantId}:`前缀，简单可靠。Redis独立DB：大租户分配独立Redis DB。Spring Cache注解中通过自定义KeyGenerator自动拼接租户前缀。注意缓存穿透/雪崩也要在租户维度考虑，不能因为一个租户的缓存失效影响其他租户。

---

*最后更新：2026-07-13*

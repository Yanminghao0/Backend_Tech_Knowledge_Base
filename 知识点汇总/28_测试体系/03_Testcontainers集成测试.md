# Testcontainers 集成测试

> Testcontainers 是一个 Java 库，它提供了一种轻量级、可抛弃的 Docker 容器实例，专门用于集成测试。开发者无需手动搭建数据库、消息队列等中间件环境，只需在测试代码中声明容器，即可获得与生产环境高度一致的测试基础设施。

---

## 📋 目录

1. [Testcontainers 核心概念](#1-testcontainers-核心概念)
2. [环境搭建与依赖配置](#2-环境搭建与依赖配置)
3. [数据库容器测试](#3-数据库容器测试)
4. [Redis 容器测试](#4-redis-容器测试)
5. [Kafka 容器测试](#5-kafka-容器测试)
6. [通用容器（GenericContainer）](#6-通用容器genericcontainer)
7. [容器生命周期管理](#7-容器生命周期管理)
8. [与 Spring Boot 集成](#8-与-spring-boot-集成)
9. [最佳实践与性能优化](#9-最佳实践与性能优化)
10. [面试题速查](#10-面试题速查)

---

## 1. Testcontainers 核心概念

### 1.1 为什么需要 Testcontainers

传统集成测试面临的问题：

| 问题 | 传统方案 | Testcontainers 方案 |
|------|---------|-------------------|
| 数据库环境 | H2 内存数据库 | 真实 PostgreSQL/MySQL |
| 消息队列 | Mock 或嵌入式 | 真实 Kafka/RabbitMQ |
| Redis | Embedded Redis | 真实 Redis |
| 环境一致性 | 开发者手动搭建 | 代码自动声明 |
| 环境隔离 | 共享测试服务器 | 每次测试独立容器 |
| 清理 | 手动清理数据 | 容器销毁即清理 |

### 1.2 核心组件

- **GenericContainer**：通用容器，支持任意 Docker 镜像
- **专用容器**：PostgreSQLContainer、MySQLContainer、RedisContainer、KafkaContainer 等
- **DockerComposeContainer**：通过 docker-compose 编排多容器
- **Network**：容器间网络通信

---

## 2. 环境搭建与依赖配置

### 2.1 前置条件

- Docker 或 Podman 已安装并运行
- Java 11+
- JUnit 5

### 2.2 Maven 依赖

```xml
<dependencies>
    <!-- Testcontainers 核心 BOM -->
    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>testcontainers-bom</artifactId>
        <version>1.19.7</version>
        <type>pom</type>
        <scope>import</scope>
    </dependency>

    <!-- JUnit 5 集成 -->
    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>junit-jupiter</artifactId>
        <scope>test</scope>
    </dependency>

    <!-- PostgreSQL 容器 -->
    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>postgresql</artifactId>
        <scope>test</scope>
    </dependency>

    <!-- MySQL 容器 -->
    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>mysql</artifactId>
        <scope>test</scope>
    </dependency>

    <!-- Redis 容器 -->
    <dependency>
        <groupId>com.redis</groupId>
        <artifactId>testcontainers-redis</artifactId>
        <version>2.2.2</version>
        <scope>test</scope>
    </dependency>

    <!-- Kafka 容器 -->
    <dependency>
        <groupId>org.testcontainers</groupId>
        <artifactId>kafka</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

---

## 3. 数据库容器测试

### 3.1 PostgreSQL 容器

```java
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.sql.*;

@Testcontainers
class PostgresIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test")
        .withInitScript("init.sql"); // 从 resources 加载初始化脚本

    @Test
    void shouldConnectAndQuery() throws SQLException {
        String jdbcUrl = postgres.getJdbcUrl();
        String username = postgres.getUsername();
        String password = postgres.getPassword();

        try (Connection conn = DriverManager.getConnection(jdbcUrl, username, password);
             Statement stmt = conn.createStatement()) {

            stmt.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(100))");
            stmt.execute("INSERT INTO users (name) VALUES ('张三')");

            ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE name = '张三'");
            assertTrue(rs.next());
            assertEquals("张三", rs.getString("name"));
        }
    }
}
```

### 3.2 MySQL 容器

```java
@Testcontainers
class MySQLIntegrationTest {

    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0")
        .withDatabaseName("testdb")
        .withUsername("root")
        .withPassword("root123")
        .withCommand("--default-authentication-plugin=mysql_native_password");

    @Test
    void shouldExecuteComplexQuery() throws SQLException {
        try (Connection conn = DriverManager.getConnection(
                mysql.getJdbcUrl(), mysql.getUsername(), mysql.getPassword())) {

            conn.createStatement().executeUpdate(
                "CREATE TABLE products (" +
                "  id INT AUTO_INCREMENT PRIMARY KEY," +
                "  name VARCHAR(200) NOT NULL," +
                "  price DECIMAL(10,2)," +
                "  stock INT DEFAULT 0" +
                ")"
            );

            PreparedStatement ps = conn.prepareStatement(
                "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)"
            );
            ps.setString(1, "笔记本电脑");
            ps.setBigDecimal(2, new BigDecimal("5999.00"));
            ps.setInt(3, 100);
            ps.executeUpdate();

            ResultSet rs = conn.createStatement().executeQuery(
                "SELECT COUNT(*) FROM products"
            );
            assertTrue(rs.next());
            assertEquals(1, rs.getInt(1));
        }
    }
}
```

### 3.3 数据库初始化脚本

```sql
-- src/test/resources/init.sql
CREATE TABLE IF NOT EXISTS accounts (
    id BIGSERIAL PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO accounts (account_number, balance) VALUES
    ('ACC001', 10000.00),
    ('ACC002', 5000.00),
    ('ACC003', 0.00);
```

---

## 4. Redis 容器测试

### 4.1 基础 Redis 容器

```java
import org.junit.jupiter.api.Test;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.containers.GenericContainer;
import redis.clients.jedis.Jedis;

@Testcontainers
class RedisIntegrationTest {

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @Test
    void shouldSetAndGetValue() {
        String host = redis.getHost();
        int port = redis.getMappedPort(6379);

        try (Jedis jedis = new Jedis(host, port)) {
            jedis.set("user:1:name", "张三");
            jedis.set("user:1:age", "25");

            assertEquals("张三", jedis.get("user:1:name"));
            assertEquals("25", jedis.get("user:1:age"));
        }
    }

    @Test
    void shouldHandleHashOperations() {
        try (Jedis jedis = new Jedis(redis.getHost(), redis.getMappedPort(6379))) {
            jedis.hset("user:1", "name", "李四");
            jedis.hset("user:1", "email", "lisi@test.com");
            jedis.hset("user:1", "age", "30");

            Map<String, String> userFields = jedis.hgetAll("user:1");
            assertEquals("李四", userFields.get("name"));
            assertEquals("lisi@test.com", userFields.get("email"));
            assertEquals(3, userFields.size());
        }
    }

    @Test
    void shouldHandleListOperations() {
        try (Jedis jedis = new Jedis(redis.getHost(), redis.getMappedPort(6379))) {
            jedis.lpush("tasks", "task1", "task2", "task3");

            assertEquals(3, jedis.llen("tasks"));
            assertEquals("task3", jedis.rpop()); // 从右弹出
            assertEquals("task2", jedis.rpop());
        }
    }
}
```

### 4.2 带密码认证的 Redis

```java
@Container
static GenericContainer<?> redisWithAuth = new GenericContainer<>("redis:7-alpine")
    .withCommand("redis-server", "--requirepass", "mypassword")
    .withExposedPorts(6379);

@Test
void shouldConnectWithPassword() {
    try (Jedis jedis = new Jedis(redisWithAuth.getHost(), redisWithAuth.getMappedPort(6379))) {
        jedis.auth("mypassword");
        jedis.set("key", "value");
        assertEquals("value", jedis.get("key"));
    }
}
```

---

## 5. Kafka 容器测试

### 5.1 Kafka 生产者与消费者测试

```java
import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.clients.producer.*;
import org.apache.kafka.common.serialization.StringSerializer;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.testcontainers.containers.KafkaContainer;
import org.testcontainers.utility.DockerImageName;

@Testcontainers
class KafkaIntegrationTest {

    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.5.0")
    );

    @Test
    void shouldProduceAndConsumeMessages() throws Exception {
        String bootstrapServers = kafka.getBootstrapServers();

        // 生产者配置
        Properties producerProps = new Properties();
        producerProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        producerProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        producerProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);

        try (KafkaProducer<String, String> producer = new KafkaProducer<>(producerProps)) {
            // 发送消息
            ProducerRecord<String, String> record = new ProducerRecord<>("test-topic", "key1", "Hello Kafka!");
            Future<RecordMetadata> future = producer.send(record);
            RecordMetadata metadata = future.get(10, TimeUnit.SECONDS);
            assertEquals(0, metadata.offset());
        }

        // 消费者配置
        Properties consumerProps = new Properties();
        consumerProps.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        consumerProps.put(ConsumerConfig.GROUP_ID_CONFIG, "test-group");
        consumerProps.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        consumerProps.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        consumerProps.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);

        try (KafkaConsumer<String, String> consumer = new KafkaConsumer<>(consumerProps)) {
            consumer.subscribe(List.of("test-topic"));

            // 轮询消费
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofSeconds(10));
            assertEquals(1, records.count());

            ConsumerRecord<String, String> record = records.iterator().next();
            assertEquals("key1", record.key());
            assertEquals("Hello Kafka!", record.value());
        }
    }
}
```

### 5.2 Kafka Schema Registry

```java
@Container
static GenericContainer<?> schemaRegistry = new GenericContainer<>("confluentinc/cp-schema-registry:7.5.0")
    .withEnv("SCHEMA_REGISTRY_HOST_NAME", "schema-registry")
    .withEnv("SCHEMA_REGISTRY_LISTENERS", "http://0.0.0.0:8081")
    .withEnv("SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS", "PLAINTEXT://" + kafka.getNetworkAliases().get(0) + ":9092")
    .withExposedPorts(8081)
    .dependsOn(kafka);
```

---

## 6. 通用容器（GenericContainer）

### 6.1 任意 Docker 镜像

```java
@Testcontainers
class GenericContainerTest {

    @Container
    static GenericContainer<?> nginx = new GenericContainer<>("nginx:alpine")
        .withExposedPorts(80)
        .withStartupTimeout(Duration.ofSeconds(30));

    @Test
    void shouldServeNginxDefaultPage() {
        String url = String.format("http://%s:%d", nginx.getHost(), nginx.getMappedPort(80));

        HttpResponse<String> response = HttpClient.newHttpClient()
            .send(
                HttpRequest.newBuilder().uri(URI.create(url)).GET().build(),
                HttpResponse.BodyHandlers.ofString()
            );

        assertEquals(200, response.statusCode());
        assertTrue(response.body().contains("Welcome to nginx!"));
    }
}
```

### 6.2 自定义命令和文件挂载

```java
@Container
static GenericContainer<?> customContainer = new GenericContainer<>("alpine:3.18")
    .withCommand("sh", "-c", "while true; do echo 'heartbeat'; sleep 5; done")
    .withFileSystemBind("./data", "/app/data", BindMode.READ_WRITE)
    .withEnv("APP_ENV", "test")
    .withStartupTimeout(Duration.ofSeconds(10));
```

### 6.3 Docker Compose 容器编排

```java
@Testcontainers
class DockerComposeTest {

    static DockerComposeContainer<?> compose = new DockerComposeContainer<>(
        new File("src/test/resources/docker-compose-test.yml")
    )
    .withExposedService("postgres", 5432)
    .withExposedService("redis", 6379)
    .withLocalCompose(true);

    @BeforeAll
    static void startCompose() {
        compose.start();
    }

    @AfterAll
    static void stopCompose() {
        compose.stop();
    }

    @Test
    void shouldAccessMultipleServices() {
        String pgHost = compose.getServiceHost("postgres", 5432);
        int pgPort = compose.getServicePort("postgres", 5432);

        String redisHost = compose.getServiceHost("redis", 6379);
        int redisPort = compose.getServicePort("redis", 6379);

        // 使用获取到的 host 和 port 连接服务
    }
}
```

---

## 7. 容器生命周期管理

### 7.1 容器共享与复用

```java
// 方式1：静态字段 — 所有测试共享一个容器实例（推荐，启动快）
@Testcontainers
class SharedContainerTest {

    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    static {
        postgres.start(); // 手动启动，不受 @Container 管理
    }

    @Test
    void test1() { /* 使用 postgres */ }

    @Test
    void test2() { /* 使用 postgres */ }
}

// 方式2：@Container 静态字段 — 每个测试类共享一个容器
@Testcontainers
class PerClassContainerTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Test
    void test1() { }

    @Test
    void test2() { }
}

// 方式3：@Container 实例字段 — 每个测试方法创建新容器（慢，不推荐）
@Testcontainers
class PerMethodContainerTest {

    @Container
    PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Test
    void test1() { }
    // 容器在 test1 后销毁，test2 重新创建
}
```

### 7.2 容器复用模式

```java
// 通过 Singleton 模式共享容器
public abstract class AbstractIntegrationTest {

    protected static final PostgreSQLContainer<?> POSTGRES;

    static {
        POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("integration_test")
            .withReuse(true); // 启用复用
        POSTGRES.start();
    }

    protected String getJdbcUrl() {
        return POSTGRES.getJdbcUrl();
    }

    protected Connection getConnection() throws SQLException {
        return DriverManager.getConnection(
            POSTGRES.getJdbcUrl(),
            POSTGRES.getUsername(),
            POSTGRES.getPassword()
        );
    }
}

class UserServiceIT extends AbstractIntegrationTest {

    @Test
    void shouldSaveUser() throws SQLException {
        try (Connection conn = getConnection()) {
            // 使用共享的 PostgreSQL 容器
        }
    }
}
```

### 7.3 启动等待策略

```java
// 等待日志输出
GenericContainer<?> app = new GenericContainer<>("myapp:latest")
    .waitingFor(Wait.forLogMessage(".*Started Application.*", 1))
    .withStartupTimeout(Duration.ofMinutes(2));

// 等待 HTTP 端口就绪
GenericContainer<?> webApp = new GenericContainer<>("myapp:latest")
    .waitingFor(Wait.forHttp("/health").forStatusCode(200))
    .withExposedPorts(8080);

// 等待 TCP 端口就绪
GenericContainer<?> db = new GenericContainer<>("custom-db:latest")
    .waitingFor(Wait.forListeningPort())
    .withExposedPorts(3306);
```

---

## 8. 与 Spring Boot 集成

### 8.1 动态数据源配置

```java
@SpringBootTest
@Testcontainers
class SpringBootIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.datasource.driver-class-name", () -> "org.postgresql.Driver");
    }

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldSaveAndRetrieveUser() {
        User user = new User("张三", "zhangsan@test.com");
        userRepository.save(user);

        Optional<User> found = userRepository.findByEmail("zhangsan@test.com");
        assertTrue(found.isPresent());
        assertEquals("张三", found.get().getName());
    }
}
```

### 8.2 Redis + Spring Boot

```java
@SpringBootTest
@Testcontainers
class RedisSpringBootTest {

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @DynamicPropertySource
    static void configureRedis(DynamicPropertyRegistry registry) {
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
    }

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Test
    void shouldCacheData() {
        redisTemplate.opsForValue().set("key", "value");
        assertEquals("value", redisTemplate.opsForValue().get("key"));
    }
}
```

### 8.3 Kafka + Spring Boot

```java
@SpringBootTest
@Testcontainers
class KafkaSpringBootTest {

    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.5.0")
    );

    @DynamicPropertySource
    static void configureKafka(DynamicPropertyRegistry registry) {
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Test
    void shouldSendMessage() throws Exception {
        kafkaTemplate.send("test-topic", "key", "message");
        // 验证消息处理...
    }
}
```

---

## 9. 最佳实践与性能优化

### 9.1 性能优化策略

```java
// 1. 使用静态容器共享（减少启动次数）
@Container
static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");
// 而非实例字段

// 2. 使用轻量级镜像
new PostgreSQLContainer<>("postgres:16-alpine")  // alpine 版本更小更快
// 而非
new PostgreSQLContainer<>("postgres:16")  // 完整版本较大

// 3. 启用容器复用
new PostgreSQLContainer<>("postgres:16-alpine")
    .withReuse(true); // 需要在 ~/.testcontainers.properties 中设置 testcontainers.reuse.enable=true

// 4. 设置资源限制
new PostgreSQLContainer<>("postgres:16-alpine")
    .withCreateContainerCmdModifier(cmd -> cmd
        .withMemory(512L * 1024 * 1024)  // 512MB
        .withCpuCount(2L)
    );
```

### 9.2 测试数据隔离

```java
@Testcontainers
class DataIsolationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    private Connection connection;

    @BeforeEach
    void setUp() throws SQLException {
        connection = DriverManager.getConnection(
            postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword()
        );
        // 每个测试前开启事务
        connection.setAutoCommit(false);
    }

    @AfterEach
    void tearDown() throws SQLException {
        // 每个测试后回滚，保持数据隔离
        connection.rollback();
        connection.close();
    }

    @Test
    void testInsertUser() throws SQLException {
        connection.createStatement().execute(
            "INSERT INTO users (name) VALUES ('张三')"
        );
        // 不会影响其他测试
    }
}
```

### 9.3 通用测试基类

```java
public abstract class ContainerBaseTest {

    protected static final PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");

    protected static final GenericContainer<?> redis =
        new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);

    protected static final KafkaContainer kafka =
        new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.5.0"));

    static {
        postgres.start();
        redis.start();
        kafka.start();
    }

    @DynamicPropertySource
    static void configureAll(DynamicPropertyRegistry registry) {
        // DataSource
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);

        // Redis
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", () -> redis.getMappedPort(6379));

        // Kafka
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }
}
```

---

## 10. 面试题速查

**Q1: Testcontainers 解决了什么问题？**
- 解决集成测试环境搭建困难、环境不一致、H2 等内存数据库与生产数据库行为差异大的问题
- 通过 Docker 提供真实、隔离、可抛弃的测试环境

**Q2: @Container 注解在静态字段和实例字段上的区别？**
- 静态字段：整个测试类共享一个容器，启动一次
- 实例字段：每个测试方法创建新容器，启动多次（慢）

**Q3: 如何优化 Testcontainers 的启动速度？**
- 使用静态容器共享实例
- 使用 alpine 轻量级镜像
- 启用容器复用（`withReuse(true)`）
- 设置合理的资源限制

**Q4: @DynamicPropertySource 的作用？**
- 在 Spring Boot 测试中动态注入容器连接信息（URL、端口、用户名密码等）

**Q5: Testcontainers 如何管理容器间通信？**
- 使用 `Network` 接口创建共享网络
- 或使用 `DockerComposeContainer` 编排多容器

**Q6: Testcontainers 的等待策略有哪些？**
- `Wait.forLogMessage()`：等待日志输出
- `Wait.forHttp()`：等待 HTTP 端口就绪
- `Wait.forListeningPort()`：等待 TCP 端口就绪
- 可自定义 `WaitStrategy`

**Q7: Testcontainers 和 H2 内存数据库的选择？**
- 简单 CRUD 测试可用 H2
- 涉及数据库特有功能（JSON、窗口函数、存储过程）必须用真实数据库
- CI 中推荐 Testcontainers，保证环境一致性

*最后更新：2026-07-13*

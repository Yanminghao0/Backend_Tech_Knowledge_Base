# Spring Boot 测试全指南

> Spring Boot 提供了一套完整的测试支持体系，从切片测试到全栈集成测试，覆盖了应用开发的各个层面。通过合理使用各种测试注解和工具，开发者可以在测试速度和测试覆盖度之间取得最佳平衡。

---

## 📋 目录

1. [Spring Boot 测试体系概览](#1-spring-boot-测试体系概览)
2. [@SpringBootTest 全栈测试](#2-springboottest-全栈测试)
3. [@WebMvcTest 控制器切片](#3-webmvctest-控制器切片)
4. [@DataJpaTest 持久层切片](#4-datajpatest-持久层切片)
5. [@DataRedisTest Redis 切片](#5-dataredistest-redis-切片)
6. [TestSlice 切片测试原理](#6-testslice-切片测试原理)
7. [@MockBean 与依赖模拟](#7-mockbean-与依赖模拟)
8. [事务回滚机制](#8-事务回滚机制)
9. [测试工具与辅助注解](#9-测试工具与辅助注解)
10. [测试策略与最佳实践](#10-测试策略与最佳实践)
11. [面试题速查](#11-面试题速查)

---

## 1. Spring Boot 测试体系概览

### 1.1 测试层次

```
┌─────────────────────────────────────────────┐
│           @SpringBootTest (全栈)             │
│  ┌─────────────────────────────────────┐    │
│  │  Controller → Service → Repository   │    │
│  │  ┌──────────┐  ┌──────────────────┐ │    │
│  │  │@WebMvcTest│ │@DataJpaTest/Redis │ │    │
│  │  │(Web切片) │  │  (数据层切片)      │ │    │
│  │  └──────────┘  └──────────────────┘ │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### 1.2 依赖配置

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

`spring-boot-starter-test` 包含：
- JUnit 5
- Spring Test & Spring Boot Test
- AssertJ
- Mockito
- JSONassert
- JsonPath
- Testcontainers（可选）

---

## 2. @SpringBootTest 全栈测试

### 2.1 基本用法

```java
@SpringBootTest
class ApplicationIntegrationTest {

    @Autowired
    private UserService userService;

    @Test
    void contextLoads() {
        // 验证 Spring 上下文能正常加载
        assertNotNull(userService);
    }
}
```

### 2.2 Web 环境配置

```java
// 不启动 Web 环境
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
class NonWebTest { }

// 模拟 Servlet 环境（默认）
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.MOCK)
class MockWebTest {
    @Autowired
    private MockMvc mockMvc;
}

// 随机端口启动真实 Web 环境
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class RealWebTest {
    @LocalServerPort
    private int port;
}

// 固定端口启动
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.DEFINED_PORT,
    properties = "server.port=8081")
class FixedPortTest { }
```

### 2.3 自定义配置

```java
@SpringBootTest
@ActiveProfiles("test")
class ProfileTest { }

@SpringBootTest(properties = {
    "app.feature.enabled=true",
    "spring.datasource.url=jdbc:h2:mem:testdb"
})
class CustomPropertyTest { }

// 只加载特定配置类
@SpringBootTest(classes = {TestConfig.class, UserService.class})
class MinimalContextTest { }
```

---

## 3. @WebMvcTest 控制器切片

### 3.1 基本用法

```java
@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    void shouldReturnUserById() throws Exception {
        // Given
        User user = new User(1L, "张三", "zhangsan@test.com");
        when(userService.findById(1L)).thenReturn(user);

        // When & Then
        mockMvc.perform(get("/api/users/1")
                .contentType(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.name").value("张三"))
            .andExpect(jsonPath("$.email").value("zhangsan@test.com"));
    }

    @Test
    void shouldReturn404WhenUserNotFound() throws Exception {
        when(userService.findById(999L)).thenThrow(new UserNotFoundException(999L));

        mockMvc.perform(get("/api/users/999"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.error").value("User not found"))
            .andExpect(jsonPath("$.userId").value(999));
    }
}
```

### 3.2 POST 请求测试

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Test
    void shouldCreateOrder() throws Exception {
        OrderRequest request = new OrderRequest("user-001", List.of("item1", "item2"));
        OrderResponse response = new OrderResponse("order-123", "CREATED", BigDecimal.valueOf(199.99));

        when(orderService.createOrder(any(OrderRequest.class))).thenReturn(response);

        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "userId": "user-001",
                        "items": ["item1", "item2"]
                    }
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.orderId").value("order-123"))
            .andExpect(jsonPath("$.status").value("CREATED"))
            .andExpect(jsonPath("$.totalAmount").value(199.99));
    }

    @Test
    void shouldReturn400WhenValidationFails() throws Exception {
        mockMvc.perform(post("/api/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                        "userId": "",
                        "items": []
                    }
                    """))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.errors").isNotEmpty());
    }
}
```

### 3.3 自定义 JSON 序列化

```java
@WebMvcTest(UserController.class)
class UserControllerJsonTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private UserService userService;

    @Test
    void shouldSerializeDateCorrectly() throws Exception {
        User user = new User(1L, "张三", LocalDate.of(2024, 1, 15));
        when(userService.findById(1L)).thenReturn(user);

        mockMvc.perform(get("/api/users/1"))
            .andExpect(jsonPath("$.createdAt").value("2024-01-15"));
    }
}
```

---

## 4. @DataJpaTest 持久层切片

### 4.1 基本用法

```java
@DataJpaTest
class UserRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldSaveAndFindUser() {
        User user = new User("张三", "zhangsan@test.com");
        entityManager.persist(user);
        entityManager.flush();

        Optional<User> found = userRepository.findByEmail("zhangsan@test.com");

        assertTrue(found.isPresent());
        assertEquals("张三", found.get().getName());
    }

    @Test
    void shouldFindUsersByNameContaining() {
        entityManager.persist(new User("张三", "z1@test.com"));
        entityManager.persist(new User("张四", "z2@test.com"));
        entityManager.persist(new User("李五", "l1@test.com"));
        entityManager.flush();

        List<User> results = userRepository.findByNameContaining("张");

        assertEquals(2, results.size());
        assertTrue(results.stream().allMatch(u -> u.getName().startsWith("张")));
    }
}
```

### 4.2 自定义查询测试

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private OrderRepository orderRepository;

    @Test
    void shouldCalculateTotalAmountByUser() {
        entityManager.persist(new Order("user-001", BigDecimal.valueOf(100)));
        entityManager.persist(new Order("user-001", BigDecimal.valueOf(200)));
        entityManager.persist(new Order("user-002", BigDecimal.valueOf(50)));
        entityManager.flush();

        BigDecimal total = orderRepository.sumAmountByUserId("user-001");

        assertEquals(0, BigDecimal.valueOf(300).compareTo(total));
    }

    @Test
    void shouldFindTopNRecentOrders() {
        entityManager.persist(new Order("user-001", BigDecimal.TEN, LocalDateTime.now().minusDays(3)));
        entityManager.persist(new Order("user-001", BigDecimal.ONE, LocalDateTime.now()));
        entityManager.persist(new Order("user-001", BigDecimal.ZERO, LocalDateTime.now().minusDays(1)));
        entityManager.flush();

        List<Order> recent = orderRepository.findTop5ByUserIdOrderByCreatedAtDesc("user-001");

        assertEquals(3, recent.size());
        assertEquals(BigDecimal.ONE, recent.get(0).getAmount());
    }
}
```

### 4.3 使用真实数据库

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@TestPropertySource(properties = {
    "spring.datasource.url=jdbc:postgresql://localhost:5432/testdb",
    "spring.datasource.username=test",
    "spring.datasource.password=test"
})
class RealDatabaseRepositoryTest {
    // 使用真实 PostgreSQL 而非 H2
}
```

---

## 5. @DataRedisTest Redis 切片

### 5.1 基本用法

```java
@DataRedisTest
class UserRepositoryRedisTest {

    @Autowired
    private StringRedisTemplate redisTemplate;

    @Test
    void shouldStoreAndRetrieveValue() {
        redisTemplate.opsForValue().set("test:key", "test-value");
        String value = redisTemplate.opsForValue().get("test:key");

        assertEquals("test-value", value);
    }

    @Test
    void shouldHandleHashOperations() {
        redisTemplate.opsForHash().put("user:1", "name", "张三");
        redisTemplate.opsForHash().put("user:1", "age", "25");

        Map<Object, Object> fields = redisTemplate.opsForHash().entries("user:1");

        assertEquals("张三", fields.get("name"));
        assertEquals("25", fields.get("age"));
        assertEquals(2, fields.size());
    }

    @Test
    void shouldSetExpiration() {
        redisTemplate.opsForValue().set("temp:key", "temp-value", Duration.ofSeconds(60));

        Long ttl = redisTemplate.getExpire("temp:key");
        assertNotNull(ttl);
        assertTrue(ttl > 0 && ttl <= 60);
    }
}
```

### 5.2 自定义 Repository 测试

```java
@DataRedisTest
class RedisRepositoryTest {

    @Autowired
    private ProductRedisRepository productRedisRepository;

    @Test
    void shouldSaveAndFindProduct() {
        Product product = new Product("p001", "笔记本电脑", BigDecimal.valueOf(5999));
        productRedisRepository.save(product);

        Optional<Product> found = productRedisRepository.findById("p001");

        assertTrue(found.isPresent());
        assertEquals("笔记本电脑", found.get().getName());
    }

    @Test
    void shouldExpireAfterTTL() throws Exception {
        Product product = new Product("p002", "手机", BigDecimal.valueOf(2999));
        product.setTtl(Duration.ofSeconds(1));
        productRedisRepository.save(product);

        assertTrue(productRedisRepository.findById("p002").isPresent());

        Thread.sleep(1500);

        assertTrue(productRedisRepository.findById("p002").isEmpty());
    }
}
```

---

## 6. TestSlice 切片测试原理

### 6.1 切片测试一览

| 注解 | 扫描范围 | 适用场景 |
|------|---------|---------|
| `@WebMvcTest` | @Controller, @ControllerAdvice, Filter, HandlerInterceptor | 控制器层 |
| `@DataJpaTest` | @Entity, @Repository | JPA 仓储层 |
| `@DataRedisTest` | Redis Repository | Redis 层 |
| `@DataLdapTest` | LDAP Repository | LDAP 层 |
| `@JdbcTest` | JdbcTemplate, DataSource | JDBC 层 |
| `@JsonTest` | Jackson, Gson, Jsonb | JSON 序列化 |
| `@RestClientTest` | RestTemplate, WebClient | REST 客户端 |
| `@WebServiceClientTest` | WebServiceTemplate | SOAP 客户端 |

### 6.2 @JsonTest 示例

```java
@JsonTest
class UserJsonTest {

    @Autowired
    private JacksonTester<User> jsonTester;

    @Test
    void shouldSerializeUser() throws IOException {
        User user = new User(1L, "张三", "zhangsan@test.com");

        JsonContent<User> result = jsonTester.write(user);

        assertThat(result).hasJsonPathStringValue("$.name");
        assertThat(result).extractingJsonPathStringValue("$.name").isEqualTo("张三");
        assertThat(result).doesNotHaveJsonPath("$.password");
    }

    @Test
    void shouldDeserializeUser() throws IOException {
        String json = """
            {
                "id": 1,
                "name": "李四",
                "email": "lisi@test.com"
            }
            """;

        User user = jsonTester.parseObject(json);

        assertEquals("李四", user.getName());
        assertEquals("lisi@test.com", user.getEmail());
    }
}
```

### 6.3 @RestClientTest 示例

```java
@RestClientTest(WeatherClient.class)
class WeatherClientTest {

    @Autowired
    private WeatherClient weatherClient;

    @Autowired
    private MockRestServiceServer mockServer;

    @Test
    void shouldGetWeatherData() {
        mockServer.expect(requestTo("https://api.weather.com/v1/current?city=beijing"))
            .andRespond(withSuccess(
                """
                {
                    "city": "beijing",
                    "temperature": 25,
                    "condition": "sunny"
                }
                """,
                MediaType.APPLICATION_JSON
            ));

        WeatherResponse response = weatherClient.getWeather("beijing");

        assertEquals(25, response.getTemperature());
        assertEquals("sunny", response.getCondition());
        mockServer.verify();
    }
}
```

---

## 7. @MockBean 与依赖模拟

### 7.1 @MockBean 基本用法

```java
@SpringBootTest
class UserServiceMockBeanTest {

    @Autowired
    private UserService userService;

    @MockBean
    private EmailService emailService;

    @Test
    void shouldNotSendEmailWhenRegistrationFails() {
        // 由于 EmailService 被 Mock，即使注册失败也不会真正发邮件
        when(emailService.sendWelcomeEmail(anyString())).thenReturn(true);

        boolean result = userService.register("invalid-email");

        assertFalse(result);
        verify(emailService, never()).sendWelcomeEmail(anyString());
    }
}
```

### 7.2 @MockBean vs @SpyBean

```java
@SpringBootTest
class SpyBeanTest {

    @Autowired
    private OrderService orderService;

    @SpyBean
    private PaymentGateway paymentGateway; // 包装真实 Bean，默认调用真实方法

    @Test
    void shouldCallRealPaymentGatewayButVerifyInteraction() {
        doReturn(true).when(paymentGateway).charge(anyString(), any(BigDecimal.class));

        OrderResult result = orderService.placeOrder("order-001", BigDecimal.valueOf(100));

        assertTrue(result.isSuccess());
        verify(paymentGateway).charge("order-001", BigDecimal.valueOf(100));
    }
}
```

### 7.3 @MockBean 的影响

```java
// @MockBean 会替换 Spring 上下文中的 Bean
// 如果在多个测试类中使用 @MockBean，会导致上下文缓存失效（上下文重建）
// 建议：相同 Mock 配置的测试放在一起

@SpringBootTest
class ContextCacheTest {

    // 这个类使用默认 EmailService
    @Autowired
    private EmailService emailService;
}

@SpringBootTest
class MockEmailTest {

    @MockBean
    private EmailService emailService; // 替换后，Spring 创建新的上下文
    // 上下文缓存被破坏，启动变慢
}
```

---

## 8. 事务回滚机制

### 8.1 默认回滚行为

```java
@SpringBootTest
class TransactionRollbackTest {

    @Autowired
    private UserRepository userRepository;

    @Test
    @Transactional // 默认在测试结束后回滚
    void shouldRollbackAfterTest() {
        userRepository.save(new User("张三", "zhangsan@test.com"));

        // 测试内可以查到数据
        assertTrue(userRepository.findByEmail("zhangsan@test.com").isPresent());

        // 测试结束后自动回滚，数据库不留痕迹
    }

    @Test
    @Transactional
    @Commit // 或 @Rollback(false) — 不回滚，数据持久化
    void shouldCommitAfterTest() {
        userRepository.save(new User("李四", "lisi@test.com"));
        // 数据会保留在数据库中
    }
}
```

### 8.2 事务回滚的限制

```java
@SpringBootTest
class TransactionLimitTest {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private CacheManager cacheManager;

    @Test
    @Transactional
    void shouldNotAffectCacheOnRollback() {
        userRepository.save(new User("王五", "wangwu@test.com"));

        // 注意：事务回滚只回滚数据库操作
        // 如果代码中有缓存操作，缓存不会被回滚！
        // 这可能导致后续测试读取到脏缓存数据
    }

    // 解决方案：在 @BeforeEach 或 @AfterEach 中清理缓存
    @AfterEach
    void clearCache() {
        cacheManager.getCacheNames()
            .forEach(cacheName -> cacheManager.getCache(cacheName).clear());
    }
}
```

### 8.3 跨事务测试

```java
@SpringBootTest
class MultiTransactionTest {

    @Autowired
    private PlatformTransactionManager transactionManager;

    @Test
    void shouldTestMultipleTransactions() {
        // 方式1：使用 TransactionTemplate
        TransactionTemplate txTemplate = new TransactionTemplate(transactionManager);

        txTemplate.execute(status -> {
            // 事务1
            userRepository.save(new User("user1", "u1@test.com"));
            return null;
        });

        txTemplate.execute(status -> {
            // 事务2
            userRepository.save(new User("user2", "u2@test.com"));
            return null;
        });

        assertEquals(2, userRepository.count());
    }
}
```

---

## 9. 测试工具与辅助注解

### 9.1 TestEntityManager

```java
@DataJpaTest
class TestEntityManagerDemo {

    @Autowired
    private TestEntityManager entityManager;

    @Test
    void shouldPersistAndFlush() {
        User user = new User("张三", "zhangsan@test.com");
        User saved = entityManager.persistAndFlush(user);

        assertNotNull(saved.getId());
        assertEquals("张三", saved.getName());
    }

    @Test
    void shouldFindEntity() {
        User user = entityManager.persistFlushFind(new User("李四", "lisi@test.com"));

        User found = entityManager.find(User.class, user.getId());
        assertEquals("李四", found.getName());
    }

    @Test
    void shouldClearPersistenceContext() {
        entityManager.persist(new User("王五", "wangwu@test.com"));
        entityManager.flush();
        entityManager.clear(); // 清空持久化上下文

        // 之后查询会从数据库重新加载
        User found = entityManager
            .getEntityManager()
            .createQuery("SELECT u FROM User u WHERE u.email = :email", User.class)
            .setParameter("email", "wangwu@test.com")
            .getSingleResult();
        assertEquals("王五", found.getName());
    }
}
```

### 9.2 OutputCapture

```java
@SpringBootTest
class OutputCaptureTest {

    @RegisterExtension
    OutputCaptureExtension outputCapture = new OutputCaptureExtension();

    @Test
    void shouldCaptureSystemOut(CapturedOutput output) {
        System.out.println("Hello, Test!");

        assertTrue(output.getOut().contains("Hello, Test!"));
    }
}
```

### 9.3 @DynamicPropertySource

```java
@SpringBootTest
class DynamicPropertyTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @DynamicPropertySource
    static void registerProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

### 9.4 @TestConfiguration

```java
@TestConfiguration
class TestConfig {

    @Bean
    @Primary
    public Clock testClock() {
        return Clock.fixed(Instant.parse("2024-01-01T00:00:00Z"), ZoneOffset.UTC);
    }

    @Bean
    public TestRestTemplate testRestTemplate() {
        return new TestRestTemplate();
    }
}

@SpringBootTest
@Import(TestConfig.class)
class WithTestConfigTest {

    @Autowired
    private Clock clock;

    @Test
    void shouldUseFixedClock() {
        Instant now = Instant.now(clock);
        assertEquals(Instant.parse("2024-01-01T00:00:00Z"), now);
    }
}
```

---

## 10. 测试策略与最佳实践

### 10.1 测试金字塔

```
           ╱╲
          ╱  ╲        E2E 测试（少量）
         ╱────╲
        ╱      ╲      集成测试（适量）
       ╱────────╲
      ╱          ╲    单元测试（大量）
     ╱────────────╲
```

### 10.2 各层测试策略

| 层级 | 注解 | 速度 | 覆盖范围 | 依赖 |
|------|------|------|---------|------|
| Controller | `@WebMvcTest` | 快 | HTTP 请求/响应 | Mock Service |
| Service | 纯单元测试 | 极快 | 业务逻辑 | Mock Repository |
| Repository | `@DataJpaTest` | 中 | SQL/ORM | H2/真实DB |
| 全栈集成 | `@SpringBootTest` | 慢 | 全链路 | 真实组件 |

### 10.3 最佳实践清单

```java
// 1. Controller 测试只测 Web 层，Mock Service
@WebMvcTest(UserController.class)
class UserControllerTest {
    @MockBean private UserService userService; // Mock 掉
}

// 2. Service 测试用纯 JUnit + Mockito，不加载 Spring 上下文
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    @Mock private UserRepository userRepository;
    @InjectMocks private UserService userService;
}

// 3. Repository 测试用 @DataJpaTest + 真实数据库
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class UserRepositoryTest { }

// 4. 集成测试用 @SpringBootTest + Testcontainers
@SpringBootTest
@Testcontainers
class FullStackIT { }
```

### 10.4 常见陷阱

1. **在单元测试中加载 Spring 上下文**：Service 层测试应避免 `@SpringBootTest`，用纯 Mockito
2. **@MockBean 滥用**：过多 `@MockBean` 导致上下文频繁重建，测试变慢
3. **忽略事务回滚**：测试数据未清理导致后续测试失败
4. **切片测试包含过多组件**：`@WebMvcTest(controllers = {A.class, B.class, C.class})` 应拆分
5. **测试间数据依赖**：每个测试应独立，不依赖其他测试的执行顺序

---

## 11. 面试题速查

**Q1: @SpringBootTest 和 @WebMvcTest 的区别？**
- `@SpringBootTest`：加载完整 Spring 上下文，全栈测试
- `@WebMvcTest`：只加载 Web 层（Controller + MVC 基础设施），Service 自动被 Mock

**Q2: TestSlice 切片测试的优势？**
- 只加载特定层的组件，启动速度快
- 自动 Mock 其他层依赖，测试隔离性好

**Q3: @MockBean 和 @SpyBean 的区别？**
- `@MockBean`：完全替换 Bean 为 Mock 对象，所有方法返回默认值
- `@SpyBean`：包装真实 Bean，默认调用真实方法，可选择性 Stub

**Q4: 为什么 @DataJpaTest 默认使用 H2？**
- H2 内存数据库启动快，适合快速测试
- 可通过 `@AutoConfigureTestDatabase(replace = NONE)` 使用真实数据库

**Q5: @Transactional 在测试中默认回滚还是提交？**
- 默认回滚，测试数据不持久化
- 用 `@Commit` 或 `@Rollback(false)` 可以提交

**Q6: Spring Boot 测试中如何注入动态属性？**
- 使用 `@DynamicPropertySource` 注解配合 `DynamicPropertyRegistry`

**Q7: @WebMvcTest 中如何测试全局异常处理？**
- `@WebMvcTest(controllers = UserController.class)`
- 加上 `@ControllerAdvice` 会被自动扫描
- 或通过 `@Import(GlobalExceptionHandler.class)` 显式导入

**Q8: 如何加速 Spring Boot 测试？**
- 优先使用切片测试（`@WebMvcTest`, `@DataJpaTest`）
- 减少 `@MockBean` 使用（避免上下文重建）
- 合理使用 `@DirtiesContext`
- 共享 Testcontainers 容器实例

*最后更新：2026-07-13*

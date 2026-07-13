# 契约测试 Pact

> 在微服务架构中，服务间的接口契约一致性是一个核心痛点。契约测试通过消费者驱动的契约（Consumer-Driven Contracts）模式，在不进行全链路集成测试的前提下，确保服务间接口的兼容性。Pact 是最流行的契约测试框架之一。

---

## 📋 目录

1. [契约测试核心概念](#1-契约测试核心概念)
2. [消费者驱动契约（CDC）](#2-消费者驱动契约cdc)
3. [Pact 文件结构](#3-pact-文件结构)
4. [消费者端测试](#4-消费者端测试)
5. [Provider 端验证](#5-provider-端验证)
6. [Pact Broker](#6-pact-broker)
7. [CI/CD 集成](#7-cicd-集成)
8. [微服务实战场景](#8-微服务实战场景)
9. [最佳实践与常见陷阱](#9-最佳实践与常见陷阱)
10. [面试题速查](#10-面试题速查)

---

## 1. 契约测试核心概念

### 1.1 为什么需要契约测试

传统集成测试的痛点：

| 问题 | 描述 |
|------|------|
| 环境搭建困难 | 需要同时启动多个微服务 |
| 测试速度慢 | 全链路测试耗时巨大 |
| 脆弱性高 | 任何服务变化都可能导致集成测试失败 |
| 反馈慢 | 只有部署后才发现接口不兼容 |

契约测试的解决思路：

- **消费者**定义它期望 Provider 提供什么（契约）
- **Provider** 验证自己是否满足契约
- 不需要两个服务同时运行
- 通过 Pact Broker 共享契约文件

### 1.2 契约测试 vs 集成测试

```
集成测试：
  Consumer ──实际调用──> Provider
  （需要两个服务同时运行）

契约测试：
  Consumer ──生成Pact文件──> Pact Broker ──验证──> Provider
  （两个服务独立测试，通过 Pact 文件解耦）
```

### 1.3 Pact 工作流程

```
┌─────────────┐     生成 Pact 文件     ┌──────────────┐
│  Consumer    │ ──────────────────> │  Pact Broker  │
│  (消费者)    │                      │  (契约仓库)   │
└─────────────┘                      └──────┬───────┘
                                           │ 拉取 Pact 文件
                                           ▼
                                     ┌─────────────┐
                                     │  Provider    │
                                     │  (提供者)    │
                                     └─────────────┘
```

---

## 2. 消费者驱动契约（CDC）

### 2.1 核心思想

消费者驱动契约（Consumer-Driven Contracts, CDC）的核心理念是：

- **消费者定义需求**：消费者明确声明它期望从 Provider 获得什么
- **Provider 满足所有消费者**：Provider 必须满足所有消费者的契约
- **变更安全**：如果 Provider 的变更不破坏任何契约，则可以安全发布

### 2.2 角色定义

```
消费者（Consumer）：调用 API 的一方
  → 定义期望的请求和响应
  → 生成 Pact 文件

提供者（Provider）：被调用的一方
  → 接收 Pact 文件
  → 验证自己的 API 是否满足契约
```

### 2.3 依赖配置（Java）

```xml
<dependencies>
    <!-- Pact Consumer -->
    <dependency>
        <groupId>au.com.dius.pact.consumer</groupId>
        <artifactId>junit5</artifactId>
        <version>4.6.14</version>
        <scope>test</scope>
    </dependency>

    <!-- Pact Provider -->
    <dependency>
        <groupId>au.com.dius.pact.provider</groupId>
        <artifactId>junit5</artifactId>
        <version>4.6.14</version>
        <scope>test</scope>
    </dependency>

    <!-- Spring Boot Test（如果使用 Spring） -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-test</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

---

## 3. Pact 文件结构

### 3.1 Pact 文件格式

Pact 文件是一个 JSON 文档，记录了消费者和 Provider 之间的交互契约：

```json
{
  "consumer": {
    "name": "order-service"
  },
  "provider": {
    "name": "user-service"
  },
  "interactions": [
    {
      "description": "获取用户信息请求",
      "request": {
        "method": "GET",
        "path": "/api/users/1",
        "headers": {
          "Accept": "application/json"
        }
      },
      "response": {
        "status": 200,
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "id": 1,
          "name": "张三",
          "email": "zhangsan@example.com"
        },
        "matchingRules": {
          "body": {
            "$.id": {
              "matchers": [
                {
                  "match": "integer"
                }
              ]
            },
            "$.name": {
              "matchers": [
                {
                  "match": "type"
                }
              ]
            }
          }
        }
      }
    }
  ],
  "metadata": {
    "pactSpecification": {
      "version": "3.0.0"
    },
    "pact-jvm": {
      "version": "4.6.14"
    }
  }
}
```

### 3.2 匹配规则

Pact 支持多种匹配规则，避免硬编码具体值：

| 匹配类型 | 说明 | 示例 |
|---------|------|------|
| `type` | 类型匹配 | `{"match": "type"}` — 值类型一致即可 |
| `integer` | 整数匹配 | `{"match": "integer"}` |
| `decimal` | 小数匹配 | `{"match": "decimal"}` |
| `regex` | 正则匹配 | `{"match": "regex", "regex": "\\d+"}` |
| `date` | 日期格式 | `{"match": "date", "format": "yyyy-MM-dd"}` |
| `timestamp` | 时间戳格式 | `{"match": "timestamp", "format": "yyyy-MM-dd'T'HH:mm:ss'Z'"}` |
| `values` | 每个元素匹配 | `{"match": "values"}` |

---

## 4. 消费者端测试

### 4.1 基本消费者测试

```java
import au.com.dius.pact.consumer.dsl.PactDslJsonBody;
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import au.com.dius.pact.core.model.PactSpecVersion;
import au.com.dius.pact.core.model.RequestResponsePact;
import au.com.dius.pact.core.model.annotations.Pact;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import java.util.Map;

@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "user-service", pactVersion = PactSpecVersion.V3)
class UserServiceConsumerTest {

    @Pact(consumer = "order-service")
    public RequestResponsePact getUserByIdPact(PactDslWithProvider builder) {
        Map<String, String> headers = Map.of("Content-Type", "application/json");

        return builder
            .given("用户ID为1的用户存在")
            .uponReceiving("获取用户信息请求")
                .path("/api/users/1")
                .method("GET")
                .headers(Map.of("Accept", "application/json"))
            .willRespondWith()
                .status(200)
                .headers(headers)
                .body(new PactDslJsonBody()
                    .integerType("id", 1)
                    .stringType("name", "张三")
                    .stringType("email", "zhangsan@example.com")
                    .booleanType("active", true)
                )
            .toPact();
    }

    @Test
    @PactTestFor(pactMethod = "getUserByIdPact")
    void shouldGetUserById() {
        // Pact 会启动一个 Mock Server，将请求转发到 Mock Server
        UserServiceClient client = new UserServiceClient("http://localhost:8080");

        UserResponse response = client.getUserById(1L);

        assertNotNull(response);
        assertEquals(1L, response.getId());
        assertNotNull(response.getName());
        assertNotNull(response.getEmail());
    }
}
```

### 4.2 多个交互场景

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "user-service", pactVersion = PactSpecVersion.V3)
class UserServiceMultiPactTest {

    @Pact(consumer = "order-service")
    public RequestResponsePact multipleInteractions(PactDslWithProvider builder) {
        return builder
            // 交互1：成功获取用户
            .given("用户存在")
            .uponReceiving("获取存在的用户")
                .path("/api/users/1")
                .method("GET")
            .willRespondWith()
                .status(200)
                .body(new PactDslJsonBody()
                    .integerType("id", 1)
                    .stringType("name", "张三")
                )
            // 交互2：用户不存在
            .given("用户ID为999不存在")
            .uponReceiving("获取不存在的用户")
                .path("/api/users/999")
                .method("GET")
            .willRespondWith()
                .status(404)
                .body(new PactDslJsonBody()
                    .stringType("error", "User not found")
                    .integerType("userId", 999)
                )
            // 交互3：创建用户
            .uponReceiving("创建新用户")
                .path("/api/users")
                .method("POST")
                .body(new PactDslJsonBody()
                    .stringType("name", "李四")
                    .stringType("email", "lisi@example.com")
                )
            .willRespondWith()
                .status(201)
                .body(new PactDslJsonBody()
                    .integerType("id", 2)
                    .stringType("name", "李四")
                    .stringType("email", "lisi@example.com")
                )
            .toPact();
    }

    @Test
    @PactTestFor(pactMethod = "multipleInteractions")
    void testMultipleInteractions() {
        UserServiceClient client = new UserServiceClient("http://localhost:8080");

        // 测试获取存在的用户
        UserResponse user = client.getUserById(1L);
        assertNotNull(user);

        // 测试获取不存在的用户
        assertThrows(UserNotFoundException.class, () -> client.getUserById(999L));

        // 测试创建用户
        UserResponse created = client.createUser(new CreateUserRequest("李四", "lisi@example.com"));
        assertNotNull(created.getId());
    }
}
```

### 4.3 使用正则匹配

```java
@Pact(consumer = "order-service")
public RequestResponsePact pactWithRegex(PactDslWithProvider builder) {
    return builder
        .given("订单存在")
        .uponReceiving("获取订单信息")
            .path("/api/orders/order-2024-001")
            .method("GET")
        .willRespondWith()
            .status(200)
            .body(new PactDslJsonBody()
                .stringMatcher("orderId", "order-\\d{4}-\\d{3}", "order-2024-001")
                .stringMatcher("status", "PENDING|CONFIRMED|SHIPPED|DELIVERED", "CONFIRMED")
                .date("createdAt", "yyyy-MM-dd", "2024-01-15")
                .decimalType("totalAmount", 199.99)
            )
        .toPact();
}
```

### 4.4 消费者端使用 Spring Boot

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "user-service", pactVersion = PactSpecVersion.V3)
class SpringBootConsumerTest {

    @Autowired
    private UserClient userClient;

    @Pact(consumer = "order-service")
    public RequestResponsePact getUserPact(PactDslWithProvider builder) {
        return builder
            .given("用户存在")
            .uponReceiving("获取用户信息")
                .path("/api/users/1")
                .method("GET")
                .headers(Map.of("Accept", "application/json"))
            .willRespondWith()
                .status(200)
                .body(new PactDslJsonBody()
                    .integerType("id", 1)
                    .stringType("name")
                    .stringType("email")
                )
            .toPact();
    }

    @Test
    @PactTestFor(pactMethod = "getUserPact")
    void shouldCallUserService() {
        // userClient 内部会调用 Mock Server
        UserResponse response = userClient.getUser(1L);
        assertNotNull(response);
    }
}
```

---

## 5. Provider 端验证

### 5.1 基本验证

```java
import au.com.dius.pact.provider.junit5.PactVerificationContext;
import au.com.dius.pact.provider.junit5.PactVerificationInvocationContextProvider;
import au.com.dius.pact.provider.junitsupport.Provider;
import au.com.dius.pact.provider.junitsupport.State;
import au.com.dius.pact.provider.junitsupport.loader.PactBroker;
import au.com.dius.pact.provider.junitsupport.loader.PactFolder;
import org.junit.jupiter.api.TestTemplate;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Provider("user-service")
@PactFolder("pacts") // 从本地文件夹加载 Pact 文件
class UserServiceProviderTest {

    @LocalServerPort
    private int port;

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        // 设置 Provider 的目标地址
        context.setTarget(HttpTestTarget.fromUrl(new URL("http://localhost:" + port)));
        context.verifyInteraction();
    }

    @State("用户ID为1的用户存在")
    void userExists() {
        // 准备测试数据：确保用户ID为1的用户存在
        userRepository.save(new User(1L, "张三", "zhangsan@example.com"));
    }

    @State("用户ID为999不存在")
    void userDoesNotExist() {
        // 准备测试数据：确保用户ID为999不存在
        userRepository.deleteById(999L);
    }
}
```

### 5.2 从 Pact Broker 加载

```java
@Provider("user-service")
@PactBroker(
    url = "https://pact-broker.example.com",
    authentication = @PactBrokerAuth(username = "pact", password = "pact123")
)
class UserServiceBrokerProviderTest {

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        context.verifyInteraction();
    }

    @State("用户存在")
    void setupUserExists() {
        // 准备 Provider 状态
    }
}
```

### 5.3 Provider 状态管理

```java
@Provider("user-service")
@PactFolder("pacts")
class UserServiceProviderTest {

    @Autowired
    private UserRepository userRepository;

    @State("用户ID为1的用户存在")
    void setupUser1Exists() {
        userRepository.deleteAll();
        userRepository.save(new User(1L, "张三", "zhangsan@example.com"));
    }

    @State("用户ID为999不存在")
    void setupUser999NotExists() {
        userRepository.deleteById(999L);
    }

    @State(value = "用户有订单", params = {"userId"})
    void setupUserWithOrders(Map<String, Object> params) {
        Long userId = Long.valueOf(params.get("userId").toString());
        // 根据参数准备状态
        orderRepository.save(new Order(userId, "order-001"));
    }
}
```

---

## 6. Pact Broker

### 6.1 Pact Broker 的作用

Pact Broker 是一个 Pact 文件的存储和共享中心，提供：

- **契约存储**：集中管理所有 Pact 文件
- **版本管理**：支持契约的版本化
- **验证结果**：记录 Provider 验证结果
- **can-i-deploy 检查**：发布前检查是否可以安全部署
- **可视化**：展示服务依赖关系图

### 6.2 Docker 部署 Pact Broker

```yaml
# docker-compose-pact-broker.yml
version: '3'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: pact
      POSTGRES_USER: pact
      POSTGRES_PASSWORD: pact123
    volumes:
      - pact-db:/var/lib/postgresql/data

  pact-broker:
    image: pactfoundation/pact-broker:2.108.0
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_ADAPTER: postgres
      PACT_BROKER_DATABASE_HOST: postgres
      PACT_BROKER_DATABASE_NAME: pact
      PACT_BROKER_DATABASE_USERNAME: pact
      PACT_BROKER_DATABASE_PASSWORD: pact123
    depends_on:
      - postgres

volumes:
  pact-db:
```

### 6.3 发布 Pact 文件到 Broker

```bash
# 使用 pact-cli 发布
docker run --rm \
  -v $(pwd)/target/pacts:/pacts \
  pactfoundation/pact-cli:latest \
  publish /pacts \
  --broker-base-url http://localhost:9292 \
  --consumer-app-version $(git rev-parse --short HEAD) \
  --branch $(git rev-parse --abbrev-ref HEAD)
```

### 6.4 Maven 集成发布

```xml
<plugin>
    <groupId>au.com.dius.pact.provider</groupId>
    <artifactId>maven</artifactId>
    <version>4.6.14</version>
    <configuration>
        <pactBrokerUrl>http://localhost:9292</pactBrokerUrl>
        <projectVersion>${project.version}</projectVersion>
    </configuration>
</plugin>
```

---

## 7. CI/CD 集成

### 7.1 完整 CI 流程

```yaml
# .github/workflows/pact-test.yml
name: Pact Contract Testing

on: [push, pull_request]

jobs:
  consumer-test:
    name: Consumer 测试
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'

      - name: 运行消费者测试并生成 Pact 文件
        run: mvn test -pl order-service

      - name: 发布 Pact 文件到 Broker
        run: |
          mvn pact:publish \
            -DpactBrokerUrl=https://pact-broker.example.com \
            -DpactBrokerToken=${{ secrets.PACT_BROKER_TOKEN }}

  provider-test:
    name: Provider 验证
    runs-on: ubuntu-latest
    needs: consumer-test
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'

      - name: 从 Broker 拉取并验证 Pact
        run: |
          mvn test -pl user-service \
            -Dpact.verifier.publishResults=true \
            -Dpactbroker.url=https://pact-broker.example.com \
            -Dpactbroker.auth.token=${{ secrets.PACT_BROKER_TOKEN }}

  can-i-deploy:
    name: 部署前检查
    runs-on: ubuntu-latest
    needs: [consumer-test, provider-test]
    steps:
      - name: Check can-i-deploy
        run: |
          docker run --rm pactfoundation/pact-cli:latest \
            broker can-i-deploy \
            --pacticipant order-service \
            --version $(git rev-parse --short HEAD) \
            --to-environment production \
            --broker-base-url https://pact-broker.example.com \
            --broker-token ${{ secrets.PACT_BROKER_TOKEN }}
```

### 7.2 can-i-deploy 检查

```bash
# 检查 order-service 是否可以部署到生产环境
pact-broker can-i-deploy \
  --pacticipant order-service \
  --version $(git rev-parse --short HEAD) \
  --to-environment production \
  --broker-base-url https://pact-broker.example.com

# 输出示例：
# Computer says yes \o/
# There is sufficient verification data to deploy
# order-service (abc1234) to production
```

---

## 8. 微服务实战场景

### 8.1 场景：订单服务调用用户服务

**消费者：订单服务（order-service）**

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "user-service", pactVersion = PactSpecVersion.V3)
class OrderServiceConsumerTest {

    @Pact(consumer = "order-service")
    public RequestResponsePact getUserForOrder(PactDslWithProvider builder) {
        return builder
            .given("用户ID为100的用户存在且状态为活跃")
            .uponReceiving("获取用户信息用于创建订单")
                .path("/api/users/100")
                .method("GET")
                .headers(Map.of("Accept", "application/json",
                                 "X-Request-Source", "order-service"))
            .willRespondWith()
                .status(200)
                .body(new PactDslJsonBody()
                    .integerType("id", 100)
                    .stringType("name", "张三")
                    .stringType("email", "zhangsan@example.com")
                    .booleanType("active", true)
                    .eachLike("addresses", new PactDslJsonBody()
                        .integerType("id")
                        .stringType("city")
                        .stringType("detail")
                    )
                )
            .toPact();
    }

    @Test
    @PactTestFor(pactMethod = "getUserForOrder")
    void shouldCreateOrderWithUserInfo() {
        OrderService orderService = new OrderService(new UserServiceClient("http://localhost:8080"));

        OrderResult result = orderService.createOrder(100L, List.of("item1"), BigDecimal.valueOf(99.99));

        assertTrue(result.isSuccess());
        assertEquals("张三", result.getUserName());
    }
}
```

**提供者：用户服务（user-service）**

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Provider("user-service")
@PactBroker(url = "https://pact-broker.example.com")
class UserServiceProviderPactTest {

    @LocalServerPort
    private int port;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private AddressRepository addressRepository;

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) throws Exception {
        context.setTarget(HttpTestTarget.fromUrl(new URL("http://localhost:" + port)));
        context.verifyInteraction();
    }

    @State("用户ID为100的用户存在且状态为活跃")
    void setupActiveUser100() {
        userRepository.deleteAll();
        addressRepository.deleteAll();

        User user = userRepository.save(new User(100L, "张三", "zhangsan@example.com", true));
        addressRepository.save(new Address(1L, user.getId(), "北京", "朝阳区xxx"));
    }
}
```

### 8.2 场景：消息队列契约

```java
// 消费者：定义消息契约
@Pact(consumer = "notification-service")
public MessagePact messagePact(MessagePactBuilder builder) {
    return builder
        .given("订单已创建")
        .expectsToReceive("订单创建事件")
        .withContent(new PactDslJsonBody()
            .stringType("eventType", "ORDER_CREATED")
            .integerType("orderId")
            .stringType("userId")
            .decimalType("totalAmount")
            .datetime("createdAt", "yyyy-MM-dd'T'HH:mm:ss'Z'")
        )
        .toPact();
}

@Test
@PactTestFor(pactMethod = "messagePact")
void shouldHandleOrderCreatedMessage() {
    // 消费者处理消息的逻辑测试
}
```

---

## 9. 最佳实践与常见陷阱

### 9.1 最佳实践

1. **消费者驱动**：让消费者定义契约，而不是 Provider
2. **最小契约**：只包含消费者实际使用的字段
3. **使用匹配规则**：避免硬编码具体值，用类型匹配和正则匹配
4. **Provider 状态清理**：每个 `@State` 方法应确保数据一致性
5. **CI 集成**：将 Pact 测试纳入 CI/CD 流水线
6. **版本管理**：用 Git commit hash 作为版本号

### 9.2 常见陷阱

```java
// ❌ 陷阱1：硬编码所有值，导致 Provider 微小变更就失败
.body(new PactDslJsonBody()
    .integerType("id", 1)     // 如果 Provider 返回2就失败
    .stringType("name", "张三") // 如果返回"李四"就失败
)

// ✅ 使用类型匹配
.body(new PactDslJsonBody()
    .integerType("id")    // 任何整数都通过
    .stringType("name")   // 任何字符串都通过
)

// ❌ 陷阱2：契约过于宽松，失去了验证意义
.body(new PactDslJsonBody()
    .minArrayLike("items", 0) // 0个元素的数组？太宽松了
)

// ✅ 合理的最小约束
.body(new PactDslJsonBody()
    .minArrayLike("items", 1) // 至少1个元素
    .eachLike("items", new PactDslJsonBody()
        .integerType("id")
        .stringType("name")
    )
)

// ❌ 陷阱3：Provider State 未清理数据
@State("用户存在")
void userExists() {
    userRepository.save(new User(1L, "张三", "test@test.com"));
    // 没有清理旧数据，可能导致重复
}

// ✅ 先清理再准备
@State("用户存在")
void userExists() {
    userRepository.deleteAll(); // 清理
    userRepository.save(new User(1L, "张三", "test@test.com"));
}
```

---

## 10. 面试题速查

**Q1: 什么是消费者驱动契约（CDC）？**
- 消费者定义对 Provider 的期望（契约），Provider 负责满足所有消费者的契约
- 核心优势：消费者需求驱动 API 设计，避免 Provider 过度设计

**Q2: Pact 的基本工作流程是什么？**
- 消费者测试生成 Pact 文件 → 发布到 Pact Broker → Provider 拉取并验证 → can-i-deploy 检查

**Q3: Pact 文件包含哪些内容？**
- Consumer 和 Provider 名称
- 交互列表（请求 + 响应 + 描述）
- 匹配规则
- 元数据（Pact 版本等）

**Q4: Provider State 的作用是什么？**
- 在 Provider 验证前准备特定数据状态
- 通过 `@State` 注解实现，确保验证时数据存在

**Q5: Pact Broker 的 can-i-deploy 是什么？**
- 在部署前检查当前版本是否与所有依赖服务兼容
- 基于 Pact 验证结果决定是否允许部署

**Q6: 契约测试和集成测试的区别？**
- 集成测试需要服务同时运行，契约测试独立运行
- 契约测试通过 Pact 文件解耦，速度更快
- 契约测试不验证完整链路，只验证接口兼容性

**Q7: Pact 中的匹配规则有哪些？**
- `type`：类型匹配
- `integer`/`decimal`：数值匹配
- `regex`：正则匹配
- `date`/`timestamp`：日期时间格式匹配
- `values`：集合元素匹配

**Q8: 如何在微服务中推广契约测试？**
- 从最核心的服务间交互开始
- 搭建 Pact Broker 作为基础设施
- 将 Pact 测试纳入 CI/CD 流水线
- 建立 can-i-deploy 门禁机制

*最后更新：2026-07-13*

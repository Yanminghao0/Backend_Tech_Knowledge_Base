# 契约测试Pact

> 在微服务架构中，服务间的接口变更频繁导致集成问题。契约测试（Contract Testing）通过消费者驱动的契约（CDC）模式，确保服务间接口的一致性。本文系统介绍Pact框架、契约文件、Pact Broker、Provider验证和CI集成。

---

## 📋 目录

1. [契约测试概念](#1-契约测试概念)
2. [消费者驱动契约](#2-消费者驱动契约)
3. [Pact文件结构](#3-pact文件结构)
4. [消费者测试](#4-消费者测试)
5. [Provider验证](#5-provider验证)
6. [Pact Broker](#6-pact-broker)
7. [CI集成](#7-ci集成)
8. [微服务实战](#8-微服务实战)
9. [面试题速查](#9-面试题速查)

---

## 1. 契约测试概念

### 1.1 为什么需要契约测试

```
传统集成测试的问题：

┌──────────┐         ┌──────────┐
│ 消费者A   │ ──HTTP──│ Provider │
│ (前端)    │         │ (后端API) │
├──────────┤         ├──────────┤
│ 测试自己的│         │ 测试自己的│
│ 逻辑     │         │ 逻辑     │
└──────────┘         └──────────┘

问题：
1. 消费者A期望{"name": "张三"}，Provider返回{"userName": "张三"} → 集成失败
2. Provider修改了字段名但没有通知消费者 → 生产事故
3. 端到端集成测试环境复杂、脆弱、慢

契约测试的解决方案：

┌──────────┐         ┌──────────┐
│ 消费者A   │         │ Provider │
│          │         │          │
│ 1.定义期望│         │          │
│ 2.生成契约│ ──────→ │ 3.验证契约│
│   文件    │  Pact   │   是否匹配│
│          │  Broker │          │
│ 4.验证Mock│ ←────── │          │
│   符合契约│  契约   │          │
└──────────┘         └──────────┘

契约测试确保双方都遵守约定的接口规范
```

### 1.2 契约测试 vs 端到端测试

```markdown
| 维度        | 契约测试              | 端到端测试           |
|------------|----------------------|---------------------|
| 测试范围    | 服务间接口契约         | 完整业务流程          |
| 环境需求    | 无需真实集成环境        | 需要完整环境          |
| 执行速度    | 快（秒级）             | 慢（分钟级）          |
| 稳定性      | 高（不依赖外部服务）     | 低（环境依赖多）       |
| 覆盖范围    | 接口格式和数据          | 完整功能              |
| 维护成本    | 低                    | 高                   |

最佳实践：契约测试 + 少量端到端冒烟测试
```

### 1.3 Pact核心术语

```yaml
术语表:

Consumer（消费者）:
  调用API的一方，定义对Provider的期望

Provider（提供者）:
  提供API的一方，需要满足消费者的期望

Pact（契约）:
  消费者定义的交互协议，包含请求和期望响应

Interaction（交互）:
  一次请求-响应对，包含:
  - description: 交互描述
  - request: HTTP请求（方法、路径、头、体）
  - response: 期望的HTTP响应（状态码、头、体）

Pact Broker:
  契约存储和共享中心，支持:
  - 契约存储和版本管理
  - Provider验证结果记录
  - can-i-deploy检查
  - 可视化依赖关系图

Verification（验证）:
  Provider执行测试，验证自己的API符合契约
```

---

## 2. 消费者驱动契约

### 2.1 CDC工作流程

```
消费者驱动契约（CDC）工作流：

步骤1: 消费者编写契约测试
  消费者A → 定义对Provider API的期望
  消费者B → 定义对Provider API的期望

步骤2: 生成Pact文件
  消费者A → pact-consumer-A-provider.json
  消费者B → pact-consumer-B-provider.json

步骤3: 上传到Pact Broker
  pact-consumer-A-provider.json → Pact Broker
  pact-consumer-B-provider.json → Pact Broker

步骤4: Provider拉取契约并验证
  Provider ← 拉取所有消费者的契约
  Provider → 执行验证测试
  Provider → 上传验证结果到Broker

步骤5: 部署前检查
  can-i-deploy consumer-A 1.0.0?
  → 检查Broker中该版本的契约是否被Provider验证通过
  → 通过则允许部署
```

### 2.2 Maven依赖

```xml
<!-- 消费者端 -->
<dependency>
    <groupId>au.com.dius.pact.consumer</groupId>
    <artifactId>junit5</artifactId>
    <version>4.6.14</version>
    <scope>test</scope>
</dependency>

<!-- Provider端 -->
<dependency>
    <groupId>au.com.dius.pact.provider</groupId>
    <artifactId>junit5</artifactId>
    <version>4.6.14</version>
    <scope>test</scope>
</dependency>

<!-- Pact Broker客户端 -->
<dependency>
    <groupId>au.com.dius.pact</groupId>
    <artifactId>pact-jvm-pact-broker</artifactId>
    <version>4.6.14</version>
</dependency>
```

---

## 3. Pact文件结构

### 3.1 JSON格式

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
      "description": "a request for user details",
      "providerState": "a user with id 1 exists",
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
          "email": "zhangsan@test.com",
          "status": "ACTIVE"
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
            "$.email": {
              "matchers": [
                {
                  "match": "regex",
                  "regex": "^[^@]+@[^@]+\\.[^@]+$"
                }
              ]
            }
          }
        }
      }
    },
    {
      "description": "a request for non-existent user",
      "providerState": "no user with id 999 exists",
      "request": {
        "method": "GET",
        "path": "/api/users/999",
        "headers": {
          "Accept": "application/json"
        }
      },
      "response": {
        "status": 404,
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "error": "User Not Found",
          "message": "用户不存在: 999"
        }
      }
    }
  ],
  "metadata": {
    "pactSpecification": {
      "version": "2.0.0"
    },
    "pact-jvm": {
      "version": "4.6.14"
    }
  }
}
```

### 3.2 匹配规则

```java
// Pact支持多种匹配规则，避免硬编码具体值

import static au.com.dius.pact.consumer.dsl.LambdaDsl.*;

// 1. 精确匹配（默认）
body(newJsonBody(o -> o
    .numberType("id", 1)          // 类型匹配，示例值1
    .stringType("name", "张三")    // 类型匹配，示例值"张三"
    .booleanType("active", true)  // 类型匹配
).build())

// 2. 正则匹配
body(newJsonBody(o -> o
    .stringMatcher("email", 
        "^[^@]+@[^@]+\\.[^@]+$",  // 正则
        "test@example.com")         // 示例值
    .stringMatcher("phone",
        "^1[3-9]\\d{9}$",
        "13800138000")
).build())

// 3. 每次生成不同值（不比较具体值）
body(newJsonBody(o -> o
    .datetime("createdAt", 
        "yyyy-MM-dd'T'HH:mm:ss",    // 格式
        "2024-01-01T12:00:00")       // 示例值
    .eachLike("tags", tag -> tag.stringType("name"))
).build())

// 4. 数组匹配
body(newJsonBody(o -> o
    .minArrayLike("items", 1, item -> item
        .numberType("id")
        .stringType("name")
        .numberType("quantity")
    )  // 至少1个元素的数组，每个元素结构相同
    .maxArrayLike("tags", 5, tag -> tag
        .stringType("value")
    )  // 最多5个元素
).build())

// 5. 包含匹配（允许额外字段）
body(newJsonBody(o -> o
    .stringType("name")
    .stringType("email")
).build())  // Provider返回的body可以包含name和email之外的字段
```

---

## 4. 消费者测试

### 4.1 编写消费者契约测试

```java
import au.com.dius.pact.consumer.dsl.PactDslWithProvider;
import au.com.dius.pact.consumer.junit5.PactConsumerTestExt;
import au.com.dius.pact.consumer.junit5.PactTestFor;
import au.com.dius.pact.core.model.PactSpecVersion;
import au.com.dius.pact.core.model.RequestResponsePact;
import au.com.dius.pact.core.model.annotations.Pact;
import org.apache.hc.core5.http.HttpResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import java.util.Map;

@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(
    providerName = "user-service",
    pactVersion = PactSpecVersion.V3
)
class UserServiceConsumerPactTest {
    
    @Pact(consumer = "order-service")
    RequestResponsePact getUserByIdPact(PactDslWithProvider builder) {
        Map<String, String> headers = Map.of("Accept", "application/json");
        
        return builder
            .given("a user with id 1 exists")
            .uponReceiving("a request for user details")
                .path("/api/users/1")
                .method("GET")
                .headers(headers)
            .willRespondWith()
                .status(200)
                .headers(Map.of("Content-Type", "application/json"))
                .body(newJsonBody(o -> o
                    .numberType("id", 1)
                    .stringType("name", "张三")
                    .stringType("email", "zhangsan@test.com")
                    .stringType("status", "ACTIVE")
                ).build())
            .toPact();
    }
    
    @Pact(consumer = "order-service")
    RequestResponsePact getUserNotFoundPact(PactDslWithProvider builder) {
        return builder
            .given("no user with id 999 exists")
            .uponReceiving("a request for non-existent user")
                .path("/api/users/999")
                .method("GET")
                .headers(Map.of("Accept", "application/json"))
            .willRespondWith()
                .status(404)
                .headers(Map.of("Content-Type", "application/json"))
                .body(newJsonBody(o -> o
                    .stringType("error", "User Not Found")
                    .stringType("message", "用户不存在: 999")
                ).build())
            .toPact();
    }
    
    @Test
    @PactTestFor(pactMethod = "getUserByIdPact")
    void testGetUserById(MockServer mockServer) throws IOException {
        // 使用MockServer的真实URL调用消费者代码
        UserServiceClient client = new UserServiceClient(mockServer.getUrl());
        
        User user = client.getUserById(1L);
        
        assertNotNull(user);
        assertEquals(1L, user.getId());
        assertEquals("张三", user.getName());
        assertEquals("zhangsan@test.com", user.getEmail());
    }
    
    @Test
    @PactTestFor(pactMethod = "getUserNotFoundPact")
    void testGetUserNotFound(MockServer mockServer) throws IOException {
        UserServiceClient client = new UserServiceClient(mockServer.getUrl());
        
        UserNotFoundException exception = assertThrows(
            UserNotFoundException.class,
            () -> client.getUserById(999L)
        );
        
        assertEquals("用户不存在: 999", exception.getMessage());
    }
}
```

### 4.2 POST请求契约

```java
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "payment-service", 
             pactVersion = PactSpecVersion.V3)
class PaymentServiceConsumerPactTest {
    
    @Pact(consumer = "order-service")
    RequestResponsePact processPaymentPact(PactDslWithProvider builder) {
        return builder
            .given("payment gateway is available")
            .uponReceiving("a payment request")
                .method("POST")
                .path("/api/payments")
                .headers(Map.of(
                    "Content-Type", "application/json",
                    "Accept", "application/json"
                ))
                .body(newJsonBody(o -> o
                    .numberType("orderId", 1001)
                    .stringType("paymentMethod", "ALIPAY")
                    .numberType("amount", 10000)  // 单位: 分
                ).build())
            .willRespondWith()
                .status(201)
                .headers(Map.of("Content-Type", "application/json"))
                .body(newJsonBody(o -> o
                    .stringType("paymentId", "PAY-2024-001")
                    .stringType("status", "SUCCESS")
                    .datetime("processedAt", 
                        "yyyy-MM-dd'T'HH:mm:ss",
                        "2024-01-15T10:30:00")
                ).build())
            .toPact();
    }
    
    @Test
    @PactTestFor(pactMethod = "processPaymentPact")
    void testProcessPayment(MockServer mockServer) {
        PaymentClient client = new PaymentClient(mockServer.getUrl());
        
        PaymentRequest request = PaymentRequest.builder()
                .orderId(1001L)
                .paymentMethod("ALIPAY")
                .amount(10000)
                .build();
        
        PaymentResult result = client.processPayment(request);
        
        assertNotNull(result.getPaymentId());
        assertEquals("SUCCESS", result.getStatus());
    }
}
```

---

## 5. Provider验证

### 5.1 Provider端验证测试

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
@PactBroker(
    url = "${PACT_BROKER_URL:http://localhost:9292}",
    authentication = @PactBrokerAuth(username = "pact", password = "pact")
)
// 或使用本地Pact文件
// @PactFolder("pacts")
class UserServiceProviderPactTest {
    
    @LocalServerPort
    private int port;
    
    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        // 设置Provider的目标地址
        context.setTarget(new HttpTestTarget("localhost", port));
        context.verifyInteraction();
    }
    
    // Provider State处理
    @State("a user with id 1 exists")
    void setupUserExists() {
        // 准备测试数据：确保id=1的用户存在
        testDataManager.createUser(1L, "张三", 
            "zhangsan@test.com", "ACTIVE");
    }
    
    @State("no user with id 999 exists")
    void setupUserNotExists() {
        // 确保id=999的用户不存在
        testDataManager.deleteUser(999L);
    }
    
    @Autowired
    private TestDataManager testDataManager;
}
```

### 5.2 多状态验证

```java
@Provider("payment-service")
@PactBroker(url = "${PACT_BROKER_URL}")
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class PaymentServiceProviderPactTest {
    
    @LocalServerPort
    private int port;
    
    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        context.setTarget(new HttpTestTarget("localhost", port));
        context.verifyInteraction();
    }
    
    // 带参数的State
    @State({"payment gateway is available", 
            "order with id exists"})
    void setupPaymentEnvironment(Map<String, Object> params) {
        // 从params中获取参数
        Long orderId = (Long) params.get("orderId");
        
        // 准备环境
        paymentGatewayMock.enable();
        orderRepository.save(new Order(orderId, new BigDecimal("100.00")));
    }
    
    // 清理State
    @State("payment gateway is available")
    void teardownPaymentEnvironment() {
        paymentGatewayMock.reset();
        orderRepository.deleteAll();
    }
}
```

### 5.3 Message Pact验证

```java
// 消息（事件驱动）契约测试
@Provider("order-event-producer")
@PactFolder("pacts")
class OrderEventMessagePactTest {
    
    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        context.verifyInteraction();
    }
    
    @State("an order was created")
    void orderCreatedState() {
        // 准备状态
    }
    
    @PactVerifyProvider("order created event")
    public String verifyOrderCreatedEvent() {
        // 返回实际产生的消息内容
        OrderEvent event = new OrderEvent("ORD-001", "CREATED", 
            new BigDecimal("100.00"));
        return objectMapper.writeValueAsString(event);
    }
}
```

---

## 6. Pact Broker

### 6.1 部署Pact Broker

```yaml
# docker-compose.yml
version: '3'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pact
      POSTGRES_USER: pact
      POSTGRES_PASSWORD: pact
    volumes:
      - postgres-data:/var/lib/postgresql/data

  pact-broker:
    image: pactfoundation/pact-broker:2.108.0.1
    depends_on:
      - postgres
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_USERNAME: pact
      PACT_BROKER_DATABASE_PASSWORD: pact
      PACT_BROKER_DATABASE_HOST: postgres
      PACT_BROKER_DATABASE_NAME: pact
      PACT_BROKER_BASIC_AUTH_USERNAME: pact
      PACT_BROKER_BASIC_AUTH_PASSWORD: pact
      PACT_BROKER_LOG_LEVEL: INFO

volumes:
  postgres-data:
```

### 6.2 发布契约到Broker

```bash
# 使用Pact CLI发布契约
pact-broker publish \
  target/pacts \
  --consumer-app-version 1.0.0 \
  --broker-url http://localhost:9292 \
  --broker-username pact \
  --broker-password pact \
  --branch main

# 或使用Maven插件
```

```xml
<plugin>
    <groupId>au.com.dius.pact</groupId>
    <artifactId>pact-publish-maven-plugin</artifactId>
    <version>4.6.14</version>
    <configuration>
        <pactBrokerUrl>http://localhost:9292</pactBrokerUrl>
        <pactBrokerUsername>pact</pactBrokerUsername>
        <pactBrokerPassword>pact</pactBrokerPassword>
        <projectVersion>${project.version}</projectVersion>
        <tags>
            <tag>main</tag>
        </tags>
    </configuration>
</plugin>
```

### 6.3 can-i-deploy检查

```bash
# 检查是否可以部署
pact-broker can-i-deploy \
  --pacticipant order-service \
  --version 1.0.0 \
  --to-environment production \
  --broker-url http://localhost:9292 \
  --broker-username pact \
  --broker-password pact

# 输出示例:
# Computer says yes \o/
#
# CONSUMERS  | PROVIDERS     | PASS?
# ------------+--------------+-------
# order-service | user-service | true
# order-service | payment-service | true
#
# All verification results are success
```

---

## 7. CI集成

### 7.1 消费者CI流水线

```yaml
# .gitlab-ci.yml - 消费者端
stages:
  - test
  - publish-pact
  - verify-pact
  - deploy

consumer-test:
  stage: test
  script:
    - mvn test -Dtest="*PactTest"
  artifacts:
    paths:
      - target/pacts/

publish-pact:
  stage: publish-pact
  needs: [consumer-test]
  script:
    - mvn pact:publish
        -DpactBrokerUrl=$PACT_BROKER_URL
        -DpactBrokerToken=$PACT_BROKER_TOKEN
        -DprojectVersion=$CI_COMMIT_SHA

verify-provider:
  stage: verify-pact
  needs: [publish-pact]
  script:
    # 触发Provider的Pipeline验证契约
    - curl -X POST -F token=$PROVIDER_TRIGGER_TOKEN \
        -F ref=main \
        -F "variables[PACT_CONSUMER]=order-service" \
        -F "variables[PACT_VERSION]=$CI_COMMIT_SHA" \
        "$CI_API_V4_URL/projects/$PROVIDER_PROJECT_ID/trigger/pipeline"
    # 等待Provider验证结果
    - pact-broker can-i-deploy \
        --pacticipant order-service \
        --version $CI_COMMIT_SHA \
        --to-environment production \
        --broker-url $PACT_BROKER_URL

deploy:
  stage: deploy
  needs: [verify-provider]
  script:
    - echo "部署到生产环境"
  only:
    - main
```

### 7.2 Provider CI流水线

```yaml
# Provider端
stages:
  - verify-pact
  - deploy

provider-verify-pact:
  stage: verify-pact
  script:
    - mvn verify -Dtest="*ProviderPactTest" \
        -DPACT_BROKER_URL=$PACT_BROKER_URL
    # 验证结果自动上传到Broker
  rules:
    - if: $CI_PIPELINE_SOURCE == "trigger"  # 由消费者触发

provider-verify-all-consumers:
  stage: verify-pact
  script:
    # 验证所有消费者的契约
    - mvn verify -Dtest="*ProviderPactTest" \
        -DPACT_BROKER_URL=$PACT_BROKER_URL \
        -Dpact.verifier.publishResults=true
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### 7.3 Webhook自动触发

```bash
# 在Pact Broker中设置Webhook
# 当消费者发布新契约时自动触发Provider验证

pact-broker create-webhook \
  --broker-url http://localhost:9292 \
  --consumer order-service \
  --provider user-service \
  --request POST \
  --url "https://gitlab.com/api/v4/projects/$PROVIDER_ID/trigger/pipeline" \
  --header 'Content-Type: application/json' \
  --body '{"ref":"main","variables":{"PACT_CONSUMER":"order-service","PACT_VERSION":"${pact.version}"}}'
```

---

## 8. 微服务实战

### 8.1 多消费者场景

```java
// 场景：订单服务同时依赖用户服务和支付服务
// 订单服务是两个Provider的消费者

@ExtendWith(PactConsumerTestExt.class)
class UserServicePactTest {
    @Pact(consumer = "order-service", provider = "user-service")
    RequestResponsePact getUserPact(PactDslWithProvider builder) {
        return builder
            .given("user exists")
            .uponReceiving("get user")
                .path("/api/users/1")
                .method("GET")
            .willRespondWith()
                .status(200)
                .body(newJsonBody(o -> o
                    .numberType("id", 1)
                    .stringType("name", "张三")
                ).build())
            .toPact();
    }
}

@ExtendWith(PactConsumerTestExt.class)
class PaymentServicePactTest {
    @Pact(consumer = "order-service", provider = "payment-service")
    RequestResponsePact processPaymentPact(PactDslWithProvider builder) {
        return builder
            .given("payment gateway available")
            .uponReceiving("process payment")
                .method("POST")
                .path("/api/payments")
                .body(newJsonBody(o -> o
                    .numberType("orderId", 1)
                    .numberType("amount", 10000)
                ).build())
            .willRespondWith()
                .status(201)
                .body(newJsonBody(o -> o
                    .stringType("status", "SUCCESS")
                ).build())
            .toPact();
    }
}
```

### 8.2 版本管理

```yaml
# Pact Broker中的版本管理
# 每次消费者构建发布契约时关联Git SHA和分支

# 消费者发布
pact-broker publish target/pacts \
  --consumer-app-version $(git rev-parse HEAD) \
  --branch $(git branch --show-current) \
  --broker-url $PACT_BROKER_URL

# Pact Broker UI中可以看到:
# - 每个消费者版本的契约
# - Provider验证结果矩阵
# - 依赖关系图
# - can-i-deploy状态

# 标签管理
pact-broker create-version-tag \
  --pacticipant order-service \
  --version $(git rev-parse HEAD) \
  --tag production \
  --broker-url $PACT_BROKER_URL
```

### 8.3 契约测试策略

```markdown
## 契约测试最佳实践

### 1. 契约粒度
- 每个API端点至少一个契约
- 包含成功和错误场景
- 覆盖边界条件（空值、极值）
- 不要过度——3-5个核心场景即可

### 2. 匹配规则
- 使用类型匹配而非精确值
- 对动态字段（时间戳、ID）使用匹配规则
- 允许额外字段（向前兼容）
- 正则匹配确保格式正确

### 3. Provider State
- 每个交互的given对应一个State方法
- State方法负责准备和清理测试数据
- State应该是幂等的
- 使用Testcontainers或内存数据库隔离

### 4. CI策略
- 消费者PR → 运行消费者契约测试 → 发布契约到Broker
- Broker收到新契约 → Webhook触发Provider验证
- Provider验证 → 发布结果到Broker
- 部署前 → can-i-deploy检查

### 5. 版本兼容
- Provider只能做向后兼容的变更
- 破坏性变更需要协调消费者同时更新
- 使用Pact Broker的版本矩阵追踪兼容性
- 新字段添加不需要更新契约（允许额外字段）
```

---

## 9. 面试题速查

**Q1: 什么是消费者驱动契约测试（CDC）？**
> CDC是一种服务间接口测试模式：消费者定义对Provider API的期望（契约），Provider验证自己的API满足所有消费者的契约。与传统的"Provider定义接口，消费者被动适配"不同，CDC让消费者驱动接口定义，确保Provider不会做出破坏消费者的变更。

**Q2: Pact的工作原理是什么？**
> 1）消费者端：消费者在测试中定义期望的请求-响应交互，Pact启动Mock Server接收消费者的实际调用并验证匹配。2）生成Pact文件：测试通过后生成JSON格式的契约文件。3）上传到Broker：契约文件上传到Pact Broker存储。4）Provider验证：Provider拉取契约，重放每个请求到真实Provider，验证响应匹配。

**Q3: Pact Broker的作用是什么？**
> Pact Broker是契约的中央存储和管理中心。功能：1）存储和版本管理契约文件。2）记录Provider验证结果。3）can-i-deploy检查——部署前验证消费者和Provider的兼容性。4）依赖关系可视化。5）Webhook自动触发Provider验证。6）支持多环境（dev/staging/production）的版本标签。

**Q4: Pact中的matchingRules有什么作用？**
> matchingRules定义了响应匹配策略，避免硬编码具体值。类型匹配（numberType/stringType）只验证字段类型不验证值；正则匹配（stringMatcher）验证格式；datetime匹配验证日期格式。匹配规则让契约更灵活——Provider返回的ID可以是任意整数，只要类型正确就算通过。

**Q5: Provider State是什么？为什么需要它？**
> Provider State是契约中的given条件，对应Provider测试中的状态设置方法。需要它的原因：Provider验证时需要确保系统处于正确的初始状态。例如契约声明"当用户id=1存在时，GET /users/1返回200"，Provider的State方法负责创建id=1的用户。State方法在每个交互验证前执行。

**Q6: 契约测试能替代集成测试吗？**
> 不能完全替代。契约测试验证接口格式和数据契约，但不验证完整业务流程。建议：契约测试（高频、快速）+ 少量关键路径的端到端集成测试（低频、慢）。契约测试覆盖90%的接口兼容性检查，端到端测试覆盖10%的关键业务流程验证。

---

*最后更新：2026-07-13*

# TDD 与 BDD 实践

> 测试驱动开发（TDD）和行为驱动开发（BDD）是两种重要的开发方法论。TDD 以测试为先导驱动代码编写，BDD 以自然语言描述行为驱动开发和测试。两者相辅相成，共同提升代码质量和需求表达力。

---

## 📋 目录

1. [TDD 核心理念](#1-tdd-核心理念)
2. [TDD 三步骤：Red-Green-Refactor](#2-tdd-三步骤red-green-refactor)
3. [TDD 实战案例](#3-tdd-实战案例)
4. [BDD 核心理念](#4-bdd-核心理念)
5. [Given-When-Then 模式](#5-given-when-then-模式)
6. [Cucumber 与 Gherkin 语法](#6-cucumber-与-gherkin-语法)
7. [BDD 实战案例](#7-bdd-实战案例)
8. [TDD 与 BDD 的关系](#8-tdd-与-bdd-的关系)
9. [常见陷阱与最佳实践](#9-常见陷阱与最佳实践)
10. [面试题速查](#10-面试题速查)

---

## 1. TDD 核心理念

### 1.1 什么是 TDD

测试驱动开发（Test-Driven Development）是一种开发方法论，核心理念是**先写测试，再写实现代码**。它颠覆了传统的"先写代码，后写测试"的模式。

```
传统开发：  编码 → 测试 → 修复
TDD 开发：  测试 → 编码 → 重构
```

### 1.2 TDD 的价值

| 价值 | 说明 |
|------|------|
| **需求驱动设计** | 写测试的过程就是理解需求的过程 |
| **即时反馈** | 每写一个测试就能立即知道代码是否正确 |
| **设计引导** | 测试先写促使代码设计更松耦合、更可测试 |
| **安全重构** | 有测试保底，可以大胆重构 |
| **活文档** | 测试用例就是代码行为的文档 |
| **减少 Bug** | 在编码阶段就发现大量问题 |

### 1.3 TDD 的三条规则（Uncle Bob）

1. 除非是为了使一个失败的单元测试通过，否则不允许编写任何产品代码
2. 在一个单元测试中，只允许写刚好能导致失败的内容（编译失败也算失败）
3. 只允许写刚好能使失败测试通过的产品代码，不允许多写

---

## 2. TDD 三步骤：Red-Green-Refactor

### 2.1 三步骤循环

```
    ┌─────────┐
    │  Red    │ ← 写一个失败的测试
    │ (红色)  │
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │ Green   │ ← 写最少代码使测试通过
    │ (绿色)  │
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │Refactor │ ← 重构代码，保持测试通过
    │ (重构)  │
    └────┬────┘
         │
         └──→ 回到 Red（下一个测试）
```

### 2.2 Red：写失败测试

```java
// 第1步：Red — 写一个测试，此时目标类还不存在，编译失败
@Test
void shouldReturnZeroWhenAccountIsNew() {
    Account account = new Account();
    assertEquals(BigDecimal.ZERO, account.getBalance());
}
```

### 2.3 Green：最小实现

```java
// 第2步：Green — 创建类，写最少代码使测试通过
public class Account {
    public BigDecimal getBalance() {
        return BigDecimal.ZERO;
    }
}
```

### 2.4 Refactor：重构

```java
// 第3步：Refactor — 重构代码，保持测试通过
public class Account {
    private BigDecimal balance = BigDecimal.ZERO;

    public BigDecimal getBalance() {
        return balance;
    }
}
```

### 2.5 循环示例

```
第1轮 Red:   shouldReturnZeroWhenAccountIsNew → 失败（类不存在）
第1轮 Green: 创建 Account，返回 ZERO → 通过
第1轮 Refactor: 引入 balance 字段 → 通过

第2轮 Red:   shouldIncreaseBalanceOnDeposit → 失败（deposit 方法不存在）
第2轮 Green: 添加 deposit 方法 → 通过
第2轮 Refactor: 提取验证逻辑 → 通过

第3轮 Red:   shouldRejectNegativeDeposit → 失败
第3轮 Green: 添加参数验证 → 通过
第3轮 Refactor: 提取验证器 → 通过

... 循环继续
```

---

## 3. TDD 实战案例

### 3.1 案例：实现一个购物车

**需求：** 实现一个购物车，支持添加商品、计算总价、应用折扣

#### 第1轮：空购物车

```java
// Red
@Test
void shouldHaveZeroTotalWhenCartIsEmpty() {
    ShoppingCart cart = new ShoppingCart();
    assertEquals(BigDecimal.ZERO, cart.getTotal());
}

// Green
public class ShoppingCart {
    public BigDecimal getTotal() {
        return BigDecimal.ZERO;
    }
}

// Refactor — 暂时不需要
```

#### 第2轮：添加单个商品

```java
// Red
@Test
void shouldCalculateTotalWithSingleItem() {
    ShoppingCart cart = new ShoppingCart();
    cart.addItem(new CartItem("笔记本电脑", new BigDecimal("5999.00"), 1));
    assertEquals(new BigDecimal("5999.00"), cart.getTotal());
}

// Green
public class ShoppingCart {
    private List<CartItem> items = new ArrayList<>();

    public void addItem(CartItem item) {
        items.add(item);
    }

    public BigDecimal getTotal() {
        return items.stream()
            .map(item -> item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}

// Refactor — 代码已经简洁
```

#### 第3轮：添加多个商品

```java
// Red
@Test
void shouldCalculateTotalWithMultipleItems() {
    ShoppingCart cart = new ShoppingCart();
    cart.addItem(new CartItem("笔记本电脑", new BigDecimal("5999.00"), 1));
    cart.addItem(new CartItem("鼠标", new BigDecimal("99.00"), 2));
    assertEquals(new BigDecimal("6197.00"), cart.getTotal());
}

// Green — 已有的实现已经能处理，直接通过！
// Refactor — 不需要
```

#### 第4轮：应用折扣

```java
// Red
@Test
void shouldApplyPercentageDiscount() {
    ShoppingCart cart = new ShoppingCart();
    cart.addItem(new CartItem("笔记本电脑", new BigDecimal("5999.00"), 1));
    cart.applyDiscount(Discount.percentage(10)); // 10% off
    assertEquals(new BigDecimal("5399.10"), cart.getTotal());
}

// Green
public class ShoppingCart {
    private List<CartItem> items = new ArrayList<>();
    private Discount discount = Discount.none();

    public void addItem(CartItem item) {
        items.add(item);
    }

    public void applyDiscount(Discount discount) {
        this.discount = discount;
    }

    public BigDecimal getTotal() {
        BigDecimal subtotal = items.stream()
            .map(item -> item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
        return discount.apply(subtotal);
    }
}

public interface Discount {
    BigDecimal apply(BigDecimal amount);

    static Discount none() {
        return amount -> amount;
    }

    static Discount percentage(int percent) {
        return amount -> amount.multiply(BigDecimal.valueOf(100 - percent))
            .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
    }
}
```

#### 第5轮：拒绝负数折扣

```java
// Red
@Test
void shouldRejectNegativeDiscountPercentage() {
    ShoppingCart cart = new ShoppingCart();
    assertThrows(IllegalArgumentException.class,
        () -> cart.applyDiscount(Discount.percentage(-10)));
}

// Green
static Discount percentage(int percent) {
    if (percent < 0 || percent > 100) {
        throw new IllegalArgumentException("折扣百分比必须在0-100之间");
    }
    return amount -> amount.multiply(BigDecimal.valueOf(100 - percent))
        .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
}

// Refactor — 提取验证逻辑
static Discount percentage(int percent) {
    validatePercent(percent);
    return amount -> amount.multiply(BigDecimal.valueOf(100 - percent))
        .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
}

private static void validatePercent(int percent) {
    if (percent < 0 || percent > 100) {
        throw new IllegalArgumentException("折扣百分比必须在0-100之间");
    }
}
```

### 3.2 TDD 的设计驱动效应

观察上面的案例，TDD 自然驱动出了以下设计：

- `ShoppingCart` 只暴露 `addItem`、`applyDiscount`、`getTotal` 方法
- `CartItem` 和 `Discount` 作为值对象自然分离
- `Discount` 使用策略模式（接口 + 工厂方法）
- 验证逻辑自然嵌入

这不是刻意设计的，而是测试驱动的结果。

---

## 4. BDD 核心理念

### 4.1 什么是 BDD

行为驱动开发（Behavior-Driven Development）是 TDD 的演进，强调用**自然语言**描述系统行为，让开发者、测试人员和业务人员使用同一种语言沟通。

### 4.2 BDD 与 TDD 的区别

| 维度 | TDD | BDD |
|------|-----|-----|
| 关注点 | 代码正确性 | 系统行为 |
| 描述方式 | 编程语言 | 自然语言（Gherkin） |
| 参与者 | 开发者 | 开发者 + 测试 + 业务 |
| 粒度 | 方法级别 | 场景级别 |
| 输出 | 单元测试 | 可执行的规格说明 |

### 4.3 BDD 的核心价值

- **统一语言**：业务和技术使用相同描述
- **活文档**：场景即文档，始终与代码同步
- **需求验证**：在编码前验证需求理解
- **自动化验收**：场景自动执行，持续验证

---

## 5. Given-When-Then 模式

### 5.1 结构

```
Given（假设/前置条件） — 描述场景的初始状态
When（当/触发动作）    — 描述触发的事件或操作
Then（那么/期望结果）  — 描述期望的结果
```

### 5.2 自然语言示例

```
Feature: 用户登录

  Scenario: 使用正确的用户名和密码登录
    Given 用户 "张三" 已注册
    And 用户 "张三" 的密码是 "password123"
    When 用户使用用户名 "张三" 和密码 "password123" 登录
    Then 登录应该成功
    And 应该返回有效的 JWT Token
    And 应该返回用户角色信息

  Scenario: 使用错误的密码登录
    Given 用户 "张三" 已注册
    When 用户使用用户名 "张三" 和密码 "wrongpass" 登录
    Then 登录应该失败
    And 应该返回 "用户名或密码错误" 的错误信息
    And 失败计数应该增加 1
```

### 5.3 在测试代码中的应用

```java
@Test
void shouldLoginSuccessfullyWithCorrectCredentials() {
    // Given
    userRepository.save(new User("张三", passwordEncoder.encode("password123")));

    // When
    LoginResponse response = authService.login("张三", "password123");

    // Then
    assertThat(response.isSuccess()).isTrue();
    assertThat(response.getToken()).isNotNull();
    assertThat(response.getRoles()).contains("USER");
}

@Test
void shouldFailLoginWithWrongPassword() {
    // Given
    userRepository.save(new User("张三", passwordEncoder.encode("password123")));

    // When
    LoginResponse response = authService.login("张三", "wrongpass");

    // Then
    assertThat(response.isSuccess()).isFalse();
    assertThat(response.getErrorMessage()).isEqualTo("用户名或密码错误");
}
```

---

## 6. Cucumber 与 Gherkin 语法

### 6.1 依赖配置

```xml
<dependencies>
    <dependency>
        <groupId>io.cucumber</groupId>
        <artifactId>cucumber-java</artifactId>
        <version>7.15.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>io.cucumber</groupId>
        <artifactId>cucumber-junit-platform-engine</artifactId>
        <version>7.15.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>io.cucumber</groupId>
        <artifactId>cucumber-spring</artifactId>
        <version>7.15.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### 6.2 Gherkin 关键字

| 关键字 | 中文关键字 | 用途 |
|--------|-----------|------|
| Feature | 功能 | 描述功能模块 |
| Scenario | 场景 | 描述单个测试场景 |
| Given | 假设 | 前置条件 |
| When | 当 | 触发动作 |
| Then | 那么 | 期望结果 |
| And | 并且 | 附加条件/结果 |
| But | 但是 | 排除条件 |
| Background | 背景 | 所有场景共享的前置条件 |
| Scenario Outline | 场景大纲 | 参数化场景 |
| Examples | 例子 | 场景大纲的数据表 |

### 6.3 Feature 文件示例

```gherkin
# src/test/resources/features/shopping_cart.feature
Feature: 购物车管理

  Background:
    Given 购物车已清空

  Scenario: 添加商品到购物车
    Given 商品 "笔记本电脑" 的价格是 5999.00 元
    When 我将 1 件 "笔记本电脑" 加入购物车
    Then 购物车中应有 1 种商品
    And 购物车总价应为 5999.00 元

  Scenario: 添加多个相同商品
    Given 商品 "鼠标" 的价格是 99.00 元
    When 我将 3 件 "鼠标" 加入购物车
    Then 购物车中应有 1 种商品
    And 购物车中 "鼠标" 的数量应为 3
    And 购物车总价应为 297.00 元

  Scenario: 移除商品
    Given 购物车中已有 2 件 "鼠标" 单价 99.00 元
    When 我从购物车中移除 1 件 "鼠标"
    Then 购物车中 "鼠标" 的数量应为 1
    And 购物车总价应为 99.00 元

  Scenario Outline: 应用不同折扣
    Given 购物车总价为 <originalPrice> 元
    When 我应用 <discount>% 的折扣
    Then 购物车总价应为 <finalPrice> 元

    Examples:
      | originalPrice | discount | finalPrice |
      | 1000.00       | 10       | 900.00     |
      | 500.00        | 20       | 400.00     |
      | 200.00        | 50       | 100.00     |
      | 99.99         | 0        | 99.99      |
```

### 6.4 中文 Feature 文件

```gherkin
# src/test/resources/features/user_registration.feature
功能: 用户注册

  场景: 使用有效信息注册新用户
    假设 系统中不存在邮箱 "zhangsan@test.com" 的用户
    当 我使用以下信息注册:
      | 字段   | 值                  |
      | 用户名 | 张三                |
      | 邮箱   | zhangsan@test.com   |
      | 密码   | StrongP@ss123      |
      | 年龄   | 25                  |
    那么 注册应该成功
    而且 应该发送验证邮件到 "zhangsan@test.com"
    而且 用户状态应为 "PENDING_VERIFICATION"

  场景: 使用已存在的邮箱注册
    假设 系统中已存在邮箱 "zhangsan@test.com" 的用户
    当 我使用邮箱 "zhangsan@test.com" 注册
    那么 注册应该失败
    而且 错误信息应为 "邮箱已被注册"
```

---

## 7. BDD 实战案例

### 7.1 Step Definitions

```java
import io.cucumber.java.zh.假设;
import io.cucumber.java.zh.当;
import io.cucumber.java.zh.那么;
import io.cucumber.java.zh.而且;
import io.cucumber.java.DataTableType;
import io.cucumber.java.DataTable;

public class ShoppingCartSteps {

    private ShoppingCart cart = new ShoppingCart();
    private Map<String, BigDecimal> productPrices = new HashMap<>();
    private Exception lastException;

    @假设("商品 {string} 的价格是 {bigdecimal} 元")
    public void setProductPrice(String productName, BigDecimal price) {
        productPrices.put(productName, price);
    }

    @假设("购物车已清空")
    public void clearCart() {
        cart = new ShoppingCart();
    }

    @假设("购物车中已有 {int} 件 {string} 单价 {bigdecimal} 元")
    public void cartAlreadyHasItems(int quantity, String productName, BigDecimal price) {
        productPrices.put(productName, price);
        cart.addItem(new CartItem(productName, price, quantity));
    }

    @假设("购物车总价为 {bigdecimal} 元")
    public void cartTotalIs(BigDecimal total) {
        // 设置购物车总价为指定值（通过添加商品达到）
        cart.addItem(new CartItem("placeholder", total, 1));
    }

    @当("我将 {int} 件 {string} 加入购物车")
    public void addItemToCart(int quantity, String productName) {
        BigDecimal price = productPrices.getOrDefault(productName, BigDecimal.ZERO);
        cart.addItem(new CartItem(productName, price, quantity));
    }

    @当("我从购物车中移除 {int} 件 {string}")
    public void removeItemFromCart(int quantity, String productName) {
        cart.removeItem(productName, quantity);
    }

    @当("我应用 {int}% 的折扣")
    public void applyDiscount(int percentage) {
        try {
            cart.applyDiscount(Discount.percentage(percentage));
        } catch (Exception e) {
            lastException = e;
        }
    }

    @那么("购物车中应有 {int} 种商品")
    public void verifyItemCount(int expectedCount) {
        assertEquals(expectedCount, cart.getItemCount());
    }

    @那么("购物车中 {string} 的数量应为 {int}")
    public void verifyItemQuantity(String productName, int expectedQuantity) {
        assertEquals(expectedQuantity, cart.getItemQuantity(productName));
    }

    @那么("购物车总价应为 {bigdecimal} 元")
    public void verifyTotal(BigDecimal expectedTotal) {
        assertEquals(expectedTotal, cart.getTotal());
    }
}
```

### 7.2 Cucumber + Spring Boot 集成

```java
import io.cucumber.spring.CucumberContextConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.ActiveProfiles;

@CucumberContextConfiguration
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class CucumberSpringConfig {

    @LocalServerPort
    private int port;

    public String getBaseUrl() {
        return "http://localhost:" + port;
    }
}
```

### 7.3 API 级别 BDD 测试

```gherkin
# src/test/resources/features/api/user_api.feature
Feature: 用户 API

  Background:
    Given 数据库已清空

  Scenario: 创建用户并通过 API 查询
    When 我发送 POST 请求到 "/api/users" 包含:
      """
      {
        "name": "张三",
        "email": "zhangsan@test.com",
        "age": 25
      }
      """
    Then 响应状态码应为 201
    And 响应应包含字段 "id"
    And 响应的 "name" 应为 "张三"

    When 我发送 GET 请求到 "/api/users/{id}"
    Then 响应状态码应为 200
    And 响应的 "email" 应为 "zhangsan@test.com"

  Scenario: 查询不存在的用户返回 404
    When 我发送 GET 请求到 "/api/users/9999"
    Then 响应状态码应为 404
    And 响应应包含字段 "error"
```

```java
public class UserApiSteps {

    private String baseUrl;
    private HttpResponse<String> lastResponse;
    private Long createdUserId;

    public UserApiSteps(CucumberSpringConfig config) {
        this.baseUrl = config.getBaseUrl();
    }

    @当("我发送 POST 请求到 {string} 包含:")
    public void sendPostRequest(String path, String body) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + path))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body))
            .build();

        lastResponse = HttpClient.newHttpClient().send(request,
            HttpResponse.BodyHandlers.ofString());

        // 提取创建的用户ID
        if (lastResponse.statusCode() == 201) {
            createdUserId = JsonPath.read(lastResponse.body(), "$.id");
        }
    }

    @当("我发送 GET 请求到 {string}")
    public void sendGetRequest(String path) throws Exception {
        // 替换路径参数
        if (path.contains("{id}")) {
            path = path.replace("{id}", String.valueOf(createdUserId));
        }

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + path))
            .GET()
            .build();

        lastResponse = HttpClient.newHttpClient().send(request,
            HttpResponse.BodyHandlers.ofString());
    }

    @那么("响应状态码应为 {int}")
    public void verifyStatusCode(int expectedCode) {
        assertEquals(expectedCode, lastResponse.statusCode());
    }

    @那么("响应的 {string} 应为 {string}")
    public void verifyFieldValue(String field, String expectedValue) {
        Object actual = JsonPath.read(lastResponse.body(), "$." + field);
        assertEquals(expectedValue, actual.toString());
    }
}
```

---

## 8. TDD 与 BDD 的关系

### 8.1 互补关系

```
BDD（外部/行为层）
  │
  │ 描述系统行为，验收标准
  │
  ▼
TDD（内部/单元层）
  │
  │ 驱动代码设计，单元测试
  │
  ▼
实现代码
```

### 8.2 协作模式

```
1. 业务 + 开发 → 编写 BDD 场景（Feature 文件）
2. 开发 → 用 TDD 实现每个步骤（Step Definition）
3. BDD 场景作为验收测试，持续运行
4. TDD 单元测试保证代码质量
```

### 8.3 何时用 TDD，何时用 BDD

| 场景 | 推荐方法 |
|------|---------|
| 核心业务逻辑实现 | TDD |
| API 接口开发 | TDD + BDD |
| 需求不明确，需要与业务确认 | BDD |
| 复杂算法实现 | TDD |
| 用户故事验收 | BDD |
| 微服务间交互 | BDD（契约测试） |
| 单个类的设计 | TDD |

---

## 9. 常见陷阱与最佳实践

### 9.1 TDD 常见陷阱

```java
// ❌ 陷阱1：一次写太多测试
@Test
void testEverything() {
    // 测试了10个不同的事情，无法定位失败原因
}

// ✅ 一个测试只验证一个行为
@Test
void shouldRejectNullUsername() { }
@Test
void shouldRejectEmptyUsername() { }
@Test
void shouldRejectTooShortPassword() { }

// ❌ 陷阱2：Green 阶段写太多代码
// Red: 测试 add(2, 3) == 5
// Green: 写了完整的 Calculator 类，包括 subtract、multiply、divide
// 这样违反了"最少代码"原则

// ✅ 只写让测试通过的最少代码
public int add(int a, int b) {
    return 5; // 最简单（虽然看起来傻）
}
// 下一个测试会驱动出真正的实现

// ❌ 陷阱3：跳过 Refactor 阶段
// 测试通过了就进入下一个 Red，代码越来越乱

// ✅ 每轮 Green 后必须考虑重构
```

### 9.2 BDD 常见陷阱

```gherkin
# ❌ 陷阱1：场景过于技术化，业务人员看不懂
Scenario: 测试用户API
  Given HTTP 请求头 Content-Type 为 application/json
  When 发送 POST 到 /api/v1/users 端口 8080
  Then 返回 HTTP 201 和 JSON body

# ✅ 用业务语言描述
Scenario: 注册新用户
  Given 系统 中没有叫"张三"的用户
  When 张三 尝试注册
  Then 注册 成功
  And 张三 收到验证邮件

# ❌ 陷阱2：场景步骤太多，维护困难
Scenario: 复杂流程
  Given 步骤1
  And 步骤2
  And 步骤3
  And 步骤4
  And 步骤5
  And 步骤6
  When 步骤7
  And 步骤8
  Then 步骤9
  ...（20个步骤）

# ✅ 拆分为多个小场景，或使用 Background 提取公共步骤
```

### 9.3 最佳实践总结

| 实践 | TDD | BDD |
|------|-----|-----|
| 步骤大小 | 小步快走，每个测试只验证一点 | 每个场景聚焦一个用户故事 |
| 重构 | 每轮 Green 后必重构 | 定期重构 Step Definitions |
| 命名 | `should_When_` 模式 | 场景用自然语言 |
| 隔离 | 每个测试独立 | 场景之间无依赖 |
| 速度 | 单元测试毫秒级 | 集成测试秒级 |

---

## 10. 面试题速查

**Q1: TDD 的三个步骤是什么？**
- Red：写一个失败的测试
- Green：写最少代码使测试通过
- Refactor：重构代码，保持测试通过

**Q2: TDD 的核心价值是什么？**
- 需求驱动设计、即时反馈、安全重构、活文档

**Q3: BDD 和 TDD 的区别？**
- TDD 关注代码正确性，用编程语言描述，开发者使用
- BDD 关注系统行为，用自然语言描述，所有角色参与
- BDD 是 TDD 的演进和补充

**Q4: Given-When-Then 模式的含义？**
- Given：前置条件/初始状态
- When：触发动作/事件
- Then：期望结果/验证

**Q5: Gherkin 语法支持哪些关键字？**
- Feature、Scenario、Given、When、Then、And、But、Background、Scenario Outline、Examples

**Q6: Scenario Outline 的作用？**
- 参数化场景，通过 Examples 表格提供多组数据
- 避免写多个相似的 Scenario

**Q7: TDD 中 Green 阶段为什么要写"最少代码"？**
- 避免过度设计
- 确保每个代码路径都有测试覆盖
- 通过测试驱动出正确的实现

**Q8: TDD 和 BDD 如何配合使用？**
- BDD 定义验收标准和系统行为（外部视角）
- TDD 驱动实现每个行为的代码（内部视角）
- BDD 场景作为集成测试，TDD 测试作为单元测试

*最后更新：2026-07-13*

# TDD与BDD实践

> 测试驱动开发（TDD）和行为驱动开发（BDD）是两种以测试为中心的开发方法论。TDD关注代码实现的质量，BDD关注业务行为的正确性。本文系统介绍TDD的三步骤、BDD的Given-When-Then结构、Cucumber和Gherkin语法。

---

## 📋 目录

1. [TDD概述](#1-tdd概述)
2. [TDD三步骤](#2-tdd三步骤)
3. [TDD实战](#3-tdd实战)
4. [BDD概述](#4-bdd概述)
5. [Given-When-Then](#5-given-when-then)
6. [Cucumber与Gherkin](#6-cucumber与gherkin)
7. [BDD实战案例](#7-bdd实战案例)
8. [TDD vs BDD](#8-tdd-vs-bdd)
9. [面试题速查](#9-面试题速查)

---

## 1. TDD概述

### 1.1 什么是TDD

```
TDD (Test-Driven Development) 测试驱动开发

核心理念: 先写测试，再写代码

传统开发流程:
  需求 → 设计 → 编码 → 测试 → 修复 → 交付
                          ↑__________↓
                         (测试在编码之后)

TDD开发流程:
  需求 → 写测试(失败) → 写代码(通过) → 重构 → 交付
         ↑______________________________↓
         (测试驱动编码)
```

### 1.2 TDD的好处

```markdown
## TDD的核心价值

1. **确保测试覆盖**: 每行代码都有对应的测试
2. **改善设计**: 先写测试促使代码更可测试、更松耦合
3. **即时反馈**: 代码写完即测试，减少调试时间
4. **活文档**: 测试用例就是代码行为的使用文档
5. **重构信心**: 有测试保护，可以放心重构
6. **减少Bug**: 边开发边测试，问题在早期暴露

## TDD的挑战

1. **学习曲线**: 需要转变思维方式
2. **初期速度慢**: 写测试占用开发时间
3. **测试设计难**: 需要好的测试设计能力
4. **不适用场景**: UI探索、原型验证、一次性脚本
```

### 1.3 TDD原则

```java
// 原则1: 只在红灯时写代码
// 测试失败 → 写代码使其通过 → 不能在绿灯时随意加代码

// 原则2: 每次只写一个测试
// 不要一次写多个测试用例然后一起实现

// 原则3: 每次只写让测试通过的最少代码
// 不要过度设计，只满足当前测试

// 原则4: 绿灯时重构
// 测试通过后才能重构，重构后测试仍需通过

// 原则5: 三的法则（Rule of Three）
// 代码重复出现三次时才提取，避免过早抽象
```

---

## 2. TDD三步骤

### 2.1 Red-Green-Refactor循环

```
┌──────────────────────────────────────────────┐
│                                              │
│   🔴 RED (红灯)                              │
│   - 写一个失败的测试                          │
│   - 测试描述了期望的行为                       │
│   - 编译失败也是红灯                          │
│                                              │
│   ↓                                          │
│                                              │
│   🟢 GREEN (绿灯)                             │
│   - 写最少的代码让测试通过                     │
│   - 不考虑代码质量                            │
│   - 可以"作弊"，只要测试通过                   │
│                                              │
│   ↓                                          │
│                                              │
│   🔵 REFACTOR (重构)                         │
│   - 在绿灯下重构代码                          │
│   - 改善代码质量、提取方法、消除重复             │
│   - 测试必须始终保持通过                       │
│                                              │
│   ↓ (回到红灯，写下一个测试)                    │
│                                              │
└──────────────────────────────────────────────┘

每个循环应该很短: 1-5分钟
```

### 2.2 第一个TDD循环示例

```java
// 任务: 实现一个字符串计算器

// === 循环1: 空字符串返回0 ===

// 🔴 RED: 写测试
@Test
@DisplayName("空字符串返回0")
void emptyStringReturnsZero() {
    Calculator calculator = new Calculator();
    assertEquals(0, calculator.add(""));
}
// 编译失败：Calculator类不存在 → 这也是红灯

// 🟢 GREEN: 写最少代码
public class Calculator {
    public int add(String input) {
        return 0;
    }
}
// 测试通过！

// 🔵 REFACTOR: 暂时不需要重构

// === 循环2: 单个数字返回该数字 ===

// 🔴 RED: 写测试
@Test
@DisplayName("单个数字返回该数字")
void singleNumberReturnsTheNumber() {
    Calculator calculator = new Calculator();
    assertEquals(1, calculator.add("1"));
}
// 测试失败：期望1，实际0

// 🟢 GREEN: 修改代码
public class Calculator {
    public int add(String input) {
        if (input.isEmpty()) {
            return 0;
        }
        return Integer.parseInt(input);
    }
}
// 测试通过！

// 🔵 REFACTOR: 可以提取为三元表达式
public class Calculator {
    public int add(String input) {
        return input.isEmpty() ? 0 : Integer.parseInt(input);
    }
}

// === 循环3: 两个数字返回和 ===

// 🔴 RED
@Test
@DisplayName("两个数字返回和")
void twoNumbersReturnsSum() {
    Calculator calculator = new Calculator();
    assertEquals(3, calculator.add("1,2"));
}
// 测试失败

// 🟢 GREEN
public class Calculator {
    public int add(String input) {
        if (input.isEmpty()) {
            return 0;
        }
        String[] numbers = input.split(",");
        int sum = 0;
        for (String num : numbers) {
            sum += Integer.parseInt(num);
        }
        return sum;
    }
}
// 测试通过！

// 🔵 REFACTOR: 使用Stream简化
public class Calculator {
    public int add(String input) {
        if (input.isEmpty()) {
            return 0;
        }
        return Arrays.stream(input.split(","))
                .mapToInt(Integer::parseInt)
                .sum();
    }
}

// === 循环4: 支持任意数量数字 ===

// 🔴 RED
@Test
@DisplayName("任意数量数字返回和")
void anyAmountOfNumbersReturnsSum() {
    Calculator calculator = new Calculator();
    assertEquals(15, calculator.add("1,2,3,4,5"));
}
// 测试直接通过！——当前实现已支持

// 不需要GREEN和REFACTOR，继续下一个测试

// === 循环5: 支持换行符分隔 ===

// 🔴 RED
@Test
@DisplayName("支持换行符分隔")
void supportsNewlineDelimiter() {
    Calculator calculator = new Calculator();
    assertEquals(6, calculator.add("1\n2,3"));
}
// 测试失败

// 🟢 GREEN
public class Calculator {
    public int add(String input) {
        if (input.isEmpty()) {
            return 0;
        }
        String[] numbers = input.split("[,\n]");
        return Arrays.stream(numbers)
                .mapToInt(Integer::parseInt)
                .sum();
    }
}
// 测试通过！

// === 循环6: 负数抛出异常 ===

// 🔴 RED
@Test
@DisplayName("负数抛出异常")
void negativeNumberThrowsException() {
    Calculator calculator = new Calculator();
    IllegalArgumentException ex = assertThrows(
        IllegalArgumentException.class,
        () -> calculator.add("1,-2,3")
    );
    assertTrue(ex.getMessage().contains("-2"));
}
// 测试失败

// 🟢 GREEN
public class Calculator {
    public int add(String input) {
        if (input.isEmpty()) {
            return 0;
        }
        String[] numbers = input.split("[,\n]");
        List<Integer> negatives = new ArrayList<>();
        int sum = 0;
        for (String num : numbers) {
            int n = Integer.parseInt(num);
            if (n < 0) {
                negatives.add(n);
            }
            sum += n;
        }
        if (!negatives.isEmpty()) {
            throw new IllegalArgumentException(
                "负数不被允许: " + negatives);
        }
        return sum;
    }
}
// 测试通过！

// 🔵 REFACTOR: 提取验证逻辑
public class Calculator {
    public int add(String input) {
        if (input.isEmpty()) {
            return 0;
        }
        String[] tokens = input.split("[,\n]");
        int[] numbers = parseNumbers(tokens);
        validateNoNegatives(numbers);
        return Arrays.stream(numbers).sum();
    }
    
    private int[] parseNumbers(String[] tokens) {
        return Arrays.stream(tokens)
                .mapToInt(Integer::parseInt)
                .toArray();
    }
    
    private void validateNoNegatives(int[] numbers) {
        int[] negatives = Arrays.stream(numbers)
                .filter(n -> n < 0)
                .toArray();
        if (negatives.length > 0) {
            throw new IllegalArgumentException(
                "负数不被允许: " + Arrays.toString(negatives));
        }
    }
}
```

---

## 3. TDD实战

### 3.1 领域模型TDD

```java
// 任务: 实现Order领域模型

// === 循环1: 创建订单时状态为PENDING ===
@Test
void newOrderShouldHavePendingStatus() {
    Order order = Order.create(testRequest());
    assertThat(order.getStatus()).isEqualTo(OrderStatus.PENDING);
}

// === 循环2: 订单有创建时间 ===
@Test
void newOrderShouldHaveCreatedAt() {
    LocalDateTime before = LocalDateTime.now();
    Order order = Order.create(testRequest());
    LocalDateTime after = LocalDateTime.now();
    
    assertThat(order.getCreatedAt()).isBetween(before, after);
}

// === 循环3: 待处理订单可以取消 ===
@Test
void pendingOrderCanBeCancelled() {
    Order order = createPendingOrder();
    order.cancel();
    assertThat(order.getStatus()).isEqualTo(OrderStatus.CANCELLED);
}

// === 循环4: 已完成订单不能取消 ===
@Test
void completedOrderCannotBeCancelled() {
    Order order = createCompletedOrder();
    assertThatThrownBy(order::cancel)
        .isInstanceOf(IllegalStateException.class)
        .hasMessage("已完成订单不能取消");
}

// === 循环5: 订单金额必须为正 ===
@Test
void orderAmountMustBePositive() {
    assertThatThrownBy(() -> 
        Order.create(requestWithAmount(BigDecimal.ZERO))
    ).isInstanceOf(IllegalArgumentException.class)
     .hasMessage("订单金额必须大于0");
}

// 实现逐步完善
public class Order {
    private OrderStatus status;
    private BigDecimal amount;
    private LocalDateTime createdAt;
    
    public static Order create(OrderRequest request) {
        validateAmount(request.getAmount());
        Order order = new Order();
        order.amount = request.getAmount();
        order.status = OrderStatus.PENDING;
        order.createdAt = LocalDateTime.now();
        return order;
    }
    
    private static void validateAmount(BigDecimal amount) {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("订单金额必须大于0");
        }
    }
    
    public void cancel() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException(
                status.getDescription() + "订单不能取消");
        }
        this.status = OrderStatus.CANCELLED;
    }
}
```

### 3.2 Mock优先TDD

```java
// 使用Mock来驱动接口设计

// 步骤1: 写测试，Mock还不存在的依赖
@Test
void shouldCreateOrderAndNotifyCustomer() {
    // Mock不存在的接口——驱动设计
    OrderRepository mockRepo = mock(OrderRepository.class);
    NotificationService mockNotification = mock(NotificationService.class);
    when(mockRepo.save(any())).thenReturn(orderWithId(1L));
    
    OrderService service = new OrderService(mockRepo, mockNotification);
    OrderResult result = service.createOrder(validRequest());
    
    assertEquals(1L, result.getOrderId());
    verify(mockRepo).save(any(Order.class));
    verify(mockNotification).notifyOrderCreated(1L);
}

// 步骤2: 创建接口（编译通过）
public interface OrderRepository {
    Order save(Order order);
}

public interface NotificationService {
    void notifyOrderCreated(Long orderId);
}

// 步骤3: 实现OrderService
public class OrderService {
    private final OrderRepository repository;
    private final NotificationService notification;
    
    public OrderService(OrderRepository repo, 
                        NotificationService notification) {
        this.repository = repo;
        this.notification = notification;
    }
    
    public OrderResult createOrder(OrderRequest request) {
        Order order = Order.create(request);
        Order saved = repository.save(order);
        notification.notifyOrderCreated(saved.getId());
        return OrderResult.success(saved);
    }
}
```

---

## 4. BDD概述

### 4.1 什么是BDD

```
BDD (Behavior-Driven Development) 行为驱动开发

BDD关注的是系统的行为，而非代码的实现细节

TDD: 从开发者视角写测试
  - 测试方法名: testCreateOrderWithValidData()
  - 关注: 方法调用和返回值

BDD: 从业务视角描述行为
  - 场景: 创建订单时提供有效数据应该成功创建
  - 关注: 业务场景和预期结果

BDD的三要素:
  1. 共同语言: 业务、开发、测试使用相同的描述
  2. 活文档: 场景描述本身就是可执行的文档
  3. 自动化: 场景自动映射到测试代码
```

### 4.2 BDD的核心概念

```yaml
BDD核心概念:

Feature（功能）:
  描述一个业务功能的高层次需求
  示例: "订单管理"

Scenario（场景）:
  描述一个具体的行为场景
  示例: "创建订单时输入有效数据应该成功创建"

Given（假设/前置条件）:
  描述场景的初始状态
  示例: "Given 用户已登录且购物车中有商品"

When（当/操作）:
  描述触发行为的事件
  示例: "When 用户点击结算按钮"

Then（那么/预期结果）:
  描述期望的结果
  示例: "Then 系统创建订单并发送确认邮件"

And（且）:
  连接多个条件
  示例: "And 订单状态为待支付"
```

---

## 5. Given-When-Then

### 5.1 结构化场景描述

```gherkin
Feature: 订单管理
  作为一名消费者
  我希望管理系统中的订单
  以便追踪我的购买记录

  Background:  # 所有场景共享的前置条件
    Given 系统中存在以下用户:
      | id | name | email          | vip  |
      | 1  | 张三 | zhang@test.com | true |
      | 2  | 李四 | li@test.com    | false |

  Scenario: VIP用户创建大额订单享受15%折扣
    Given 用户"张三"已登录
    And 购物车中有以下商品:
      | sku    | name     | quantity | price |
      | SKU001 | iPhone   | 1        | 8999  |
      | SKU002 | AirPods  | 1        | 1299  |
    When 用户提交订单
    Then 订单创建成功
    And 订单总金额为"10298.00"
    And 折扣金额为"1544.70"
    And 实付金额为"8753.30"
    And 订单状态为"待支付"

  Scenario: 普通用户创建订单不享受折扣
    Given 用户"李四"已登录
    And 购物车中有以下商品:
      | sku    | name     | quantity | price |
      | SKU003 | iPad     | 1        | 3999  |
    When 用户提交订单
    Then 订单创建成功
    And 订单总金额为"3999.00"
    And 折扣金额为"0.00"
    And 订单状态为"待支付"

  Scenario: 空购物车不能创建订单
    Given 用户"张三"已登录
    And 购物车为空
    When 用户提交订单
    Then 系统返回错误"购物车不能为空"
    And 没有订单被创建

  Scenario Outline: 订单金额验证
    Given 用户已登录
    And 购物车中有1个商品，价格为"<price>"
    When 用户提交订单
    Then 订单创建结果为"<result>"

    Examples:
      | price | result  |
      | 0     | 失败    |
      | -1    | 失败    |
      | 0.01  | 成功    |
      | 99999 | 成功    |
```

### 5.2 测试代码中的GWT结构

```java
// 不使用Cucumber，在JUnit5中实践GWT风格
class OrderServiceBDDTest {
    
    @Test
    @DisplayName("VIP用户创建大额订单享受15%折扣")
    void vipUserLargeOrderGetsDiscount() {
        // Given
        Customer vipCustomer = CustomerTestDataBuilder.aCustomer()
                .withId(1L)
                .withName("张三")
                .vip()
                .build();
        ShoppingCart cart = CartTestDataBuilder.aCart()
                .withItem("SKU001", "iPhone", 1, new BigDecimal("8999"))
                .withItem("SKU002", "AirPods", 1, new BigDecimal("1299"))
                .build();
        
        given(customerRepository.findById(1L))
            .willReturn(Optional.of(vipCustomer));
        
        // When
        OrderResult result = orderService.createOrder(
            CreateOrderRequest.builder()
                .customerId(1L)
                .cart(cart)
                .build());
        
        // Then
        assertThat(result)
            .isSuccessful()
            .hasTotalAmount("10298.00")
            .hasDiscount("1544.70")
            .hasFinalAmount("8753.30")
            .hasStatus(OrderStatus.PENDING);
    }
    
    @Test
    @DisplayName("空购物车不能创建订单")
    void emptyCartCannotCreateOrder() {
        // Given
        Customer customer = CustomerTestDataBuilder.aCustomer().build();
        ShoppingCart emptyCart = ShoppingCart.empty();
        
        given(customerRepository.findById(1L))
            .willReturn(Optional.of(customer));
        
        // When
        Throwable thrown = catchThrowable(() -> 
            orderService.createOrder(
                CreateOrderRequest.builder()
                    .customerId(1L)
                    .cart(emptyCart)
                    .build()));
        
        // Then
        assertThat(thrown)
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("购物车不能为空");
        
        verify(orderRepository, never()).save(any());
    }
}
```

---

## 6. Cucumber与Gherkin

### 6.1 Cucumber架构

```
┌──────────────────────────────────────────────┐
│              .feature 文件                    │
│  (Gherkin语法编写的业务场景)                   │
│  Feature: 订单管理                            │
│    Scenario: VIP用户下单                      │
│      Given ...                                │
│      When ...                                 │
│      Then ...                                 │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           Step Definitions                   │
│  (Java代码，将Gherkin步骤映射到代码)           │
│  @Given("用户已登录")                         │
│  public void userLoggedIn() { ... }           │
│                                               │
│  @When("用户提交订单")                         │
│  public void submitOrder() { ... }            │
│                                               │
│  @Then("订单创建成功")                         │
│  public void orderCreated() { ... }           │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              测试执行                          │
│  Cucumber运行器                               │
│  - 解析.feature文件                           │
│  - 匹配Step Definitions                      │
│  - 执行对应的Java方法                          │
│  - 生成测试报告                                │
└──────────────────────────────────────────────┘
```

### 6.2 Maven依赖

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

### 6.3 Gherkin语法详解

```gherkin
# src/test/resources/features/order.feature

# Language: 中文
# language: zh-CN
功能: 订单管理
  作为消费者
  我希望管理订单
  以便追踪购买记录

  背景:
    假设 系统中存在以下商品:
      | 商品编号 | 商品名称 | 价格  | 库存 |
      | SKU001  | iPhone   | 8999 | 100 |
      | SKU002  | AirPods  | 1299 | 50  |

  场景: 创建简单订单
    假设 用户"张三"已登录
    当 用户将"SKU001"加入购物车，数量为1
    而且 用户提交订单
    那么 订单创建成功
    而且 订单总金额为"8999.00"
    而且 "SKU001"的库存减少1

  场景: 使用优惠券
    假设 用户"张三"已登录
    而且 用户有优惠券"SAVE100"，满500减100
    当 用户将"SKU001"加入购物车，数量为1
    而且 用户使用优惠券"SAVE100"
    而且 用户提交订单
    那么 订单创建成功
    而且 订单总金额为"8999.00"
    而且 优惠金额为"100.00"
    而且 实付金额为"8899.00"

  场景大纲: 库存不足时下单失败
    假设 用户"张三"已登录
    当 用户将"<sku>"加入购物车，数量为"<quantity>"
    而且 用户提交订单
    那么 下单失败，错误信息为"<error>"

    例子:
      | sku    | quantity | error           |
      | SKU001 | 101      | 库存不足         |
      | SKU002 | 51       | 库存不足         |
      | SKU999 | 1        | 商品不存在       |

  场景: 并发下单
    假设 用户"张三"和用户"李四"同时购买"SKU001"
    而且 "SKU001"库存仅为1
    当 两个用户同时提交订单
    那么 只有一个用户下单成功
    而且 另一个用户收到"库存不足"错误
```

---

## 7. BDD实战案例

### 7.1 Step Definitions

```java
// src/test/java/steps/OrderSteps.java

import io.cucumber.java.zh.cn.假设;
import io.cucumber.java.zh.cn.当;
import io.cucumber.java.zh.cn.那么;
import io.cucumber.java.zh.cn.而且;
import io.cucumber.datatable.DataTable;
import org.springframework.beans.factory.annotation.Autowired;

public class OrderSteps {
    
    @Autowired
    private TestContext context;
    
    @Autowired
    private ProductRepository productRepository;
    
    @Autowired
    private CustomerRepository customerRepository;
    
    @Autowired
    private OrderService orderService;
    
    @假设("系统中存在以下商品:")
    public void setupProducts(DataTable table) {
        List<Map<String, String>> rows = table.asMaps();
        for (Map<String, String> row : rows) {
            Product product = Product.builder()
                .sku(row.get("商品编号"))
                .name(row.get("商品名称"))
                .price(new BigDecimal(row.get("价格")))
                .stock(Integer.parseInt(row.get("库存")))
                .build();
            productRepository.save(product);
        }
    }
    
    @假设("用户\"{string}\"已登录")
    public void userLoggedIn(String userName) {
        Customer customer = customerRepository.findByName(userName);
        context.setCurrentUser(customer);
    }
    
    @当("用户将\"{string}\"加入购物车，数量为{int}")
    public void addToCart(String sku, int quantity) {
        context.getCart().addItem(sku, quantity);
    }
    
    @而且("用户提交订单")
    public void submitOrder() {
        try {
            CreateOrderRequest request = CreateOrderRequest.builder()
                .customerId(context.getCurrentUser().getId())
                .cart(context.getCart())
                .build();
            context.setOrderResult(orderService.createOrder(request));
        } catch (Exception e) {
            context.setException(e);
        }
    }
    
    @那么("订单创建成功")
    public void orderCreatedSuccessfully() {
        assertThat(context.getOrderResult()).isNotNull();
        assertThat(context.getException()).isNull();
        assertThat(context.getOrderResult().isSuccessful()).isTrue();
    }
    
    @而且("订单总金额为\"{string}\"")
    public void verifyTotalAmount(String expectedAmount) {
        assertThat(context.getOrderResult().getTotalAmount())
            .isEqualByComparingTo(expectedAmount);
    }
    
    @而且("{string}的库存减少{int}")
    public void verifyStockReduced(String sku, int reducedAmount) {
        Product product = productRepository.findBySku(sku);
        Product originalProduct = context.getOriginalProducts().get(sku);
        int expectedStock = originalProduct.getStock() - reducedAmount;
        assertThat(product.getStock()).isEqualTo(expectedStock);
    }
    
    @那么("下单失败，错误信息为\"{string}\"")
    public void verifyOrderFailed(String expectedError) {
        assertThat(context.getException())
            .isNotNull()
            .hasMessageContaining(expectedError);
    }
}
```

### 7.2 Cucumber运行配置

```java
// src/test/java/runners/CucumberRunner.java

import io.cucumber.junit.platform.engine.Cucumber;
import org.junit.platform.suite.api.ConfigurationParameter;
import org.junit.platform.suite.api.IncludeEngines;
import org.junit.platform.suite.api.SelectClasspathResource;
import org.junit.platform.suite.api.Suite;

@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(
    key = "cucumber.glue", 
    value = "com.example.steps"
)
@ConfigurationParameter(
    key = "cucumber.plugin",
    value = "pretty, html:target/cucumber-report.html, json:target/cucumber.json"
)
public class CucumberRunner {
}

// Spring集成
@CucumberContextConfiguration
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class SpringBootTestConfig {
    // Spring Boot测试配置
}
```

### 7.3 场景大纲实现

```java
// 场景大纲的Step Definition
public class InventorySteps {
    
    @当("用户将{string}加入购物车，数量为{int}")
    public void addToCart(String sku, int quantity) {
        context.getCart().addItem(sku, quantity);
    }
    
    @那么("下单失败，错误信息为{string}")
    public void orderFailedWithError(String expectedError) {
        assertThat(context.getException())
            .isNotNull();
        // 根据错误类型验证
        if (expectedError.equals("库存不足")) {
            assertThat(context.getException())
                .isInstanceOf(InsufficientStockException.class);
        } else if (expectedError.equals("商品不存在")) {
            assertThat(context.getException())
                .isInstanceOf(ProductNotFoundException.class);
        }
    }
}
```

---

## 8. TDD vs BDD

### 8.1 对比分析

```markdown
| 维度        | TDD                          | BDD                          |
|------------|------------------------------|------------------------------|
| 关注点      | 代码实现质量                   | 业务行为正确性                 |
| 视角       | 开发者                       | 业务+开发+测试                |
| 描述语言    | 编程语言                      | 自然语言(Gherkin)             |
| 测试粒度    | 方法级别                      | 场景级别                      |
| 执行速度    | 快（单元测试）                 | 较慢（集成测试）               |
| 适用层      | 单元测试                      | 集成测试/验收测试              |
| 文档价值    | 代码行为文档                   | 业务需求文档                   |
| 协作方式    | 开发者独立                     | 三方协作                      |
| 学习成本    | 中等                         | 较高                         |

最佳实践: TDD + BDD 结合使用
- BDD定义业务场景（验收测试）
- TDD实现内部逻辑（单元测试）
```

### 8.2 结合使用

```java
// BDD场景: 验收测试
// order.feature
/*
  场景: VIP用户享受折扣
    假设 用户"张三"是VIP
    当 用户下单1000元
    那么 享受15%折扣
    而且 实付850元
 */

// TDD单元测试: 驱动实现
@ExtendWith(MockitoExtension.class)
class DiscountCalculatorTest {
    
    @Test
    @DisplayName("VIP用户享受15%折扣")
    void vipGets15PercentDiscount() {
        // TDD: 先写测试驱动实现
        Customer vip = Customer.builder().vip(true).build();
        BigDecimal amount = new BigDecimal("1000");
        
        BigDecimal discount = calculator.calculate(vip, amount);
        
        assertThat(discount).isEqualByComparingTo("150.00");
    }
    
    @Test
    @DisplayName("普通用户大额订单享受5%折扣")
    void normalUserLargeOrderGets5PercentDiscount() {
        Customer normal = Customer.builder().vip(false).build();
        BigDecimal amount = new BigDecimal("1000");
        
        BigDecimal discount = calculator.calculate(normal, amount);
        
        assertThat(discount).isEqualByComparingTo("50.00");
    }
    
    @Test
    @DisplayName("普通用户小额订单无折扣")
    void normalUserSmallOrderNoDiscount() {
        Customer normal = Customer.builder().vip(false).build();
        BigDecimal amount = new BigDecimal("100");
        
        BigDecimal discount = calculator.calculate(normal, amount);
        
        assertThat(discount).isEqualByComparingTo("0.00");
    }
}

// BDD Step Definition: 验收测试
@那么("享受{int}%折扣")
public void verifyDiscountPercentage(int percentage) {
    BigDecimal expectedDiscount = context.getOrderAmount()
        .multiply(BigDecimal.valueOf(percentage))
        .divide(BigDecimal.valueOf(100));
    assertThat(context.getOrderResult().getDiscount())
        .isEqualByComparingTo(expectedDiscount);
}
```

---

## 9. 面试题速查

**Q1: TDD的Red-Green-Refactor循环是什么？**
> Red：先写一个失败的测试，描述期望的行为。Green：写最少的代码让测试通过，不考虑质量。Refactor：在测试通过的状态下重构代码，改善设计。每个循环1-5分钟，反复迭代。核心思想是"测试驱动设计"——先想清楚要什么，再实现它。

**Q2: TDD中"只写让测试通过的最少代码"是什么意思？**
> 不要提前实现测试未要求的功能。如果测试只要求返回0，就只写`return 0`，即使你知道后续需要更复杂的逻辑。这避免了过度设计和YAGNI（You Aren't Gonna Need It）问题。后续的测试会逐步驱动出更完整的实现。

**Q3: BDD和TDD有什么区别？**
> TDD从开发者视角写单元测试，关注方法级别的行为，使用编程语言。BDD从业务视角写场景，关注业务流程，使用自然语言（Gherkin）。TDD是开发实践，BDD是协作实践。最佳实践是结合使用：BDD定义验收场景，TDD驱动内部实现。

**Q4: Gherkin的Given-When-Then分别代表什么？**
> Given是前置条件——描述场景的初始状态。When是触发事件——描述执行的操作。Then是预期结果——描述期望的行为。And/But用于补充条件。GWT结构让非技术人员也能理解测试场景，形成活文档。

**Q5: Cucumber的工作原理是什么？**
> Cucumber解析.feature文件中的Gherkin文本，通过正则表达式匹配Step Definition（Java方法），执行对应代码并验证结果。每个Gherkin步骤对应一个@Given/@When/@Then注解的方法。Cucumber生成可视化报告，显示每个步骤的通过/失败状态。

**Q6: TDD适合所有场景吗？有什么局限？**
> 不适合的场景：1）UI探索性开发——界面设计需要快速迭代。2）原型验证——不确定方向时快速验证。3）一次性脚本——不值得投入测试。4）纯数据类——DTO/Entity的getter/setter。适合的场景：核心业务逻辑、算法实现、API设计、复杂条件分支。

**Q7: 场景大纲（Scenario Outline）和场景（Scenario）有什么区别？**
> Scenario是单个具体场景，使用固定值。Scenario Outline是参数化场景，使用占位符和Examples表格，一次定义多组数据执行。类似JUnit5的@ParameterizedTest。场景大纲减少了重复的场景定义，特别适合边界值测试和数据驱动测试。

---

*最后更新：2026-07-13*

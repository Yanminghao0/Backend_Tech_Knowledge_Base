# Mockito 与 Mock 测试

> Mockito 是 Java 生态中最流行的 Mock 框架，通过创建和管理模拟对象，让开发者能够隔离被测单元、控制依赖行为、验证交互逻辑。它完美配合 JUnit 5，是单元测试的核心工具。

---

## 📋 目录

1. [Mockito 核心概念](#1-mockito-核心概念)
2. [创建 Mock 对象](#2-创建-mock-对象)
3. [Stubbing：when-then 模式](#3-stubbingwhen-then-模式)
4. [验证交互：verify](#4-验证交互verify)
5. [ArgumentCaptor 参数捕获](#5-argumentcaptor-参数捕获)
6. [Spy 间谍对象](#6-spy-间谍对象)
7. [@InjectMocks 自动注入](#7-injectmocks-自动注入)
8. [BDDMockito 行为驱动](#8-bddmockito-行为驱动)
9. [高级技巧](#9-高级技巧)
10. [常见陷阱与最佳实践](#10-常见陷阱与最佳实践)
11. [面试题速查](#11-面试题速查)

---

## 1. Mockito 核心概念

### 1.1 什么是 Mock

Mock 测试的核心思想是用**模拟对象**替换真实依赖，使得被测代码可以在隔离的环境中运行：

- **Mock 对象**：完全模拟，所有方法都是空实现，需要手动设置行为
- **Spy 对象**：包装真实对象，默认调用真实方法，可选择性 Mock
- **Stub**：设置 Mock 对象的方法返回特定值
- **Verify**：验证 Mock 对象的方法是否被调用，调用次数和参数

### 1.2 依赖配置

```xml
<dependencies>
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-core</artifactId>
        <version>5.11.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-junit-jupiter</artifactId>
        <version>5.11.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### 1.3 与 JUnit 5 集成

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    // 自动初始化 @Mock 和 @InjectMocks
}
```

---

## 2. 创建 Mock 对象

### 2.1 注解方式（推荐）

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @Test
    void shouldCreateUser() {
        // userRepository 和 emailService 已自动初始化
        assertNotNull(userRepository);
    }
}
```

### 2.2 编程方式

```java
class UserServiceTest {

    private UserRepository userRepository;
    private EmailService emailService;

    @BeforeEach
    void setUp() {
        userRepository = Mockito.mock(UserRepository.class);
        emailService = Mockito.mock(EmailService.class);
    }
}
```

### 2.3 MockitoSettings 简化

```java
@MockitoSettings(strictness = Strictness.LENIENT)
class UserServiceTest {
    @Mock
    private UserRepository userRepository;
    // 更宽松的严格模式
}
```

---

## 3. Stubbing：when-then 模式

### 3.1 基本返回值设置

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Test
    void shouldReturnUserById() {
        // 设置 Mock 行为
        when(userRepository.findById(1L))
            .thenReturn(Optional.of(new User(1L, "张三")));

        // 测试
        Optional<User> result = userRepository.findById(1L);

        // 验证
        assertTrue(result.isPresent());
        assertEquals("张三", result.get().getName());
    }
}
```

### 3.2 返回不同值（多次调用）

```java
@Test
void shouldReturnDifferentValuesOnMultipleCalls() {
    when(userRepository.findById(1L))
        .thenReturn(Optional.of(new User(1L, "第一次")))
        .thenReturn(Optional.of(new User(1L, "第二次")))
        .thenReturn(Optional.empty()); // 第三次返回空

    assertEquals("第一次", userRepository.findById(1L).get().getName());
    assertEquals("第二次", userRepository.findById(1L).get().getName());
    assertTrue(userRepository.findById(1L).isEmpty());
}
```

### 3.3 抛出异常

```java
@Test
void shouldThrowExceptionWhenDatabaseFails() {
    when(userRepository.findById(1L))
        .thenThrow(new DatabaseException("连接超时"));

    assertThrows(DatabaseException.class, () -> {
        userRepository.findById(1L);
    });
}

// 根据异常类型
when(userRepository.save(any(User.class)))
    .thenThrow(new RuntimeException("保存失败"));
```

### 3.4 thenAnswer 自定义逻辑

```java
@Test
void shouldUseCustomAnswer() {
    when(userRepository.save(any(User.class)))
        .thenAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(99L); // 模拟数据库生成ID
            return user;
        });

    User saved = userRepository.save(new User("李四"));
    assertEquals(99L, saved.getId());
}
```

### 3.5 参数匹配器

```java
import static org.mockito.ArgumentMatchers.*;

@Test
void shouldUseArgumentMatchers() {
    // 匹配任意 Long 值
    when(userRepository.findById(anyLong()))
        .thenReturn(Optional.of(new User(1L, "任意用户")));

    // 匹配特定类型
    when(userRepository.save(any(User.class)))
        .thenReturn(new User(1L, "已保存"));

    // 匹配 null
    when(userRepository.findByName(isNull()))
        .thenReturn(Collections.emptyList());

    // 自定义匹配器
    when(userRepository.findByName(argThat(name -> name != null && name.length() > 2)))
        .thenReturn(List.of(new User(1L, "张三")));

    // 字符串匹配
    when(userRepository.search(eq("张三")))
        .thenReturn(List.of(new User(1L, "张三")));
}
```

> **重要规则：** 如果方法调用中使用了参数匹配器（如 `anyLong()`），那么所有参数都必须使用匹配器（用 `eq()` 包裹字面值）。

```java
// ❌ 错误：混合使用匹配器和字面值
when(service.findById(anyLong(), "extra")).thenReturn(...);

// ✅ 正确：全部使用匹配器
when(service.findById(anyLong(), eq("extra"))).thenReturn(...);
```

---

## 4. 验证交互：verify

### 4.1 基本验证

```java
@Test
void shouldVerifyInteractions() {
    UserService userService = new UserService(userRepository, emailService);

    userService.createUser("张三", "zhangsan@test.com");

    // 验证方法被调用
    verify(userRepository).save(any(User.class));

    // 验证方法从未被调用
    verify(emailService, never()).sendEmail(anyString(), anyString());

    // 验证调用次数
    verify(userRepository, times(1)).save(any(User.class));
    verify(userRepository, atLeastOnce()).save(any(User.class));
    verify(userRepository, atMost(2)).save(any(User.class));

    // 验证调用顺序
    InOrder inOrder = inOrder(userRepository, emailService);
    inOrder.verify(userRepository).save(any(User.class));
    inOrder.verify(emailService).sendWelcomeEmail(any(User.class));
}
```

### 4.2 验证模式

```java
// times(n) — 精确次数
verify(mock, times(3)).method();

// never() — 从未调用
verify(mock, never()).method();

// atLeast(n) — 至少 n 次
verify(mock, atLeast(2)).method();

// atMost(n) — 最多 n 次
verify(mock, atMost(5)).method();

// only() — 仅调用此方法
verify(mock, only()).method();

// timeout — 在指定时间内调用
verify(mock, timeout(100)).method();
```

### 4.3 验证参数

```java
@Test
void shouldVerifyWithArgumentMatchers() {
    userService.createUser("张三", "zhangsan@test.com");

    // 验证保存的用户名是否正确
    ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
    verify(userRepository).save(captor.capture());

    User savedUser = captor.getValue();
    assertEquals("张三", savedUser.getName());
    assertEquals("zhangsan@test.com", savedUser.getEmail());
}
```

### 4.4 VerifyNoMoreInteractions

```java
@Test
void shouldVerifyNoMoreInteractions() {
    userService.findById(1L);

    verify(userRepository).findById(1L);
    verifyNoMoreInteractions(userRepository); // 确保没有其他调用
}
```

---

## 5. ArgumentCaptor 参数捕获

ArgumentCaptor 用于捕获 Mock 方法调用时传入的参数，是验证复杂对象传参的最佳方式。

### 5.1 基本用法

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private NotificationService notificationService;

    @InjectMocks
    private OrderService orderService;

    @Test
    void shouldCaptureOrderAndNotificationArguments() {
        // 执行
        orderService.placeOrder("user-001", List.of("item1", "item2"), BigDecimal.valueOf(99.99));

        // 捕获保存的订单
        ArgumentCaptor<Order> orderCaptor = ArgumentCaptor.forClass(Order.class);
        verify(orderRepository).save(orderCaptor.capture());

        Order savedOrder = orderCaptor.getValue();
        assertEquals("user-001", savedOrder.getUserId());
        assertEquals(2, savedOrder.getItems().size());
        assertEquals(BigDecimal.valueOf(99.99), savedOrder.getTotalAmount());

        // 捕获通知参数
        ArgumentCaptor<String> userIdCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> messageCaptor = ArgumentCaptor.forClass(String.class);
        verify(notificationService).sendNotification(userIdCaptor.capture(), messageCaptor.capture());

        assertEquals("user-001", userIdCaptor.getValue());
        assertTrue(messageCaptor.getValue().contains("99.99"));
    }
}
```

### 5.2 捕获多次调用

```java
@Test
void shouldCaptureAllSavedOrders() {
    orderService.placeOrder("user-001", List.of("item1"), BigDecimal.TEN);
    orderService.placeOrder("user-002", List.of("item2"), BigDecimal.ONE);

    ArgumentCaptor<Order> captor = ArgumentCaptor.forClass(Order.class);
    verify(orderRepository, times(2)).save(captor.capture());

    List<Order> allSavedOrders = captor.getAllValues();
    assertEquals(2, allSavedOrders.size());
    assertEquals("user-001", allSavedOrders.get(0).getUserId());
    assertEquals("user-002", allSavedOrders.get(1).getUserId());
}
```

---

## 6. Spy 间谍对象

Spy 包装真实对象，默认调用真实方法，可以 selectively 对某些方法进行 Stub。

### 6.1 @Spy 注解

```java
@ExtendWith(MockitoExtension.class)
class SpyTest {

    @Spy
    private ArrayList<String> spyList = new ArrayList<>();

    @Test
    void shouldSpyOnRealObject() {
        spyList.add("one");
        spyList.add("two");

        // 真实方法被执行
        assertEquals(2, spyList.size());

        // 对特定方法进行 Stub
        when(spyList.size()).thenReturn(100);
        assertEquals(100, spyList.size());

        // 验证调用
        verify(spyList).add("one");
        verify(spyList).add("two");
    }
}
```

### 6.2 Spy vs Mock 关键区别

```java
@Test
void mockVsSpy() {
    // Mock：所有方法返回默认值（size 返回 0）
    List<String> mockList = mock(List.class);
    mockList.add("test");
    assertEquals(0, mockList.size()); // add 是空操作

    // Spy：调用真实方法（size 返回 1）
    List<String> spyList = spy(new ArrayList<>());
    spyList.add("test");
    assertEquals(1, spyList.size()); // add 真实执行
}
```

### 6.3 Spy 的 Stub 注意事项

```java
@Spy
private UserService spyUserService;

@Test
void shouldStubSpyCorrectly() {
    // ❌ 错误：when(spy).thenReturn 会先执行真实方法
    // when(spyUserService.getName()).thenReturn("Mocked");

    // ✅ 正确：使用 doReturn-when 避免执行真实方法
    doReturn("Mocked").when(spyUserService).getName();
    assertEquals("Mocked", spyUserService.getName());
}
```

---

## 7. @InjectMocks 自动注入

`@InjectMocks` 自动将 `@Mock` 或 `@Spy` 对象注入到被测对象的构造器、Setter 或字段中。

### 7.1 构造器注入（推荐）

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private PaymentGateway paymentGateway;

    @Mock
    private NotificationService notificationService;

    @InjectMocks
    private OrderService orderService; // 自动通过构造器注入上面的 Mock

    @Test
    void shouldPlaceOrderSuccessfully() {
        // 准备
        when(paymentGateway.charge(anyString(), any(BigDecimal.class)))
            .thenReturn(true);
        when(orderRepository.save(any(Order.class)))
            .thenAnswer(invocation -> invocation.getArgument(0));

        // 执行
        OrderResult result = orderService.placeOrder("order-001", BigDecimal.valueOf(100));

        // 验证
        assertTrue(result.isSuccess());
        verify(paymentGateway).charge(eq("order-001"), eq(BigDecimal.valueOf(100)));
        verify(notificationService).sendOrderConfirmation(any(Order.class));
    }
}
```

### 7.2 字段注入

```java
@ExtendWith(MockitoExtension.class)
class FieldInjectionTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService; // 通过反射注入到 private 字段

    @Test
    void shouldWorkWithFieldInjection() {
        when(userRepository.findById(1L))
            .thenReturn(Optional.of(new User(1L, "张三")));

        Optional<User> result = userService.findById(1L);
        assertTrue(result.isPresent());
    }
}
```

> **注入优先级：** 构造器注入 > Setter 注入 > 字段注入。推荐使用构造器注入，因为它更安全、更易于重构。

---

## 8. BDDMockito 行为驱动

BDDMockito 提供了 Given-When-Then 风格的 API，使测试代码更接近自然语言描述。

### 8.1 传统写法 vs BDD 写法

```java
// 传统写法
@Test
void traditionalStyle() {
    when(userRepository.findById(1L))
        .thenReturn(Optional.of(new User(1L, "张三")));

    User user = userService.getUser(1L);

    assertEquals("张三", user.getName());
    verify(userRepository).findById(1L);
}

// BDD 写法
@Test
void bddStyle() {
    // Given
    given(userRepository.findById(1L))
        .willReturn(Optional.of(new User(1L, "张三")));

    // When
    User user = userService.getUser(1L);

    // Then
    assertThat(user.getName()).isEqualTo("张三");
    then(userRepository).should().findById(1L);
}
```

### 8.2 完整 BDD 示例

```java
import static org.mockito.BDDMockito.*;
import static org.assertj.core.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class BddOrderServiceTest {

    @Mock
    private OrderRepository orderRepository;
    @Mock
    private PaymentService paymentService;
    @InjectMocks
    private OrderService orderService;

    @Test
    void shouldCompleteOrderWhenPaymentSucceeds() {
        // Given — 准备条件和 Mock 行为
        Order order = new Order("order-001", BigDecimal.valueOf(199.99));
        given(orderRepository.findById("order-001"))
            .willReturn(Optional.of(order));
        given(paymentService.processPayment(eq("order-001"), any(BigDecimal.class)))
            .willReturn(PaymentResult.success("txn-123"));

        // When — 执行被测逻辑
        OrderResult result = orderService.processOrder("order-001");

        // Then — 验证结果和交互
        assertThat(result.isSuccess()).isTrue();
        assertThat(result.getTransactionId()).isEqualTo("txn-123");

        then(orderRepository).should().save(order);
        then(paymentService).should(times(1))
            .processPayment("order-001", BigDecimal.valueOf(199.99));
        then(orderRepository).shouldHaveNoMoreInteractions();
    }

    @Test
    void shouldFailWhenPaymentDeclined() {
        // Given
        Order order = new Order("order-002", BigDecimal.valueOf(50.00));
        given(orderRepository.findById("order-002"))
            .willReturn(Optional.of(order));
        given(paymentService.processPayment(anyString(), any(BigDecimal.class)))
            .willReturn(PaymentResult.declined("余额不足"));

        // When
        OrderResult result = orderService.processOrder("order-002");

        // Then
        assertThat(result.isSuccess()).isFalse();
        assertThat(result.getErrorMessage()).contains("余额不足");
        then(orderRepository).should(never()).save(any());
    }
}
```

---

## 9. 高级技巧

### 9.1 Mock 静态方法

Mockito 3.4+ 支持静态方法 Mock（需要 mockito-inline）：

```java
@Test
void shouldMockStaticMethod() {
    try (MockedStatic<UtilityClass> mocked = mockStatic(UtilityClass.class)) {
        mocked.when(() -> UtilityClass.getCurrentTimestamp())
            .thenReturn(1700000000L);

        long timestamp = UtilityClass.getCurrentTimestamp();
        assertEquals(1700000000L, timestamp);

        mocked.verify(() -> UtilityClass.getCurrentTimestamp());
    }
    // try-with-resources 结束后自动恢复原始行为
}
```

### 9.2 Mock final 类和 final 方法

Mockito 5+ 默认支持 Mock final 类和方法：

```java
// mockito-core 5.x 默认使用 inline mock maker
final class FinalClass {
    public final String finalMethod() {
        return "real";
    }
}

@Test
void shouldMockFinalClass() {
    FinalClass mock = mock(FinalClass.class);
    when(mock.finalMethod()).thenReturn("mocked");
    assertEquals("mocked", mock.finalMethod());
}
```

### 9.3 Mock 构造器

```java
@Test
void shouldMockConstructor() throws Exception {
    try (MockedConstruction<PaymentGateway> mocked =
            mockConstruction(PaymentGateway.class,
                (mock, context) -> {
                    when(mock.charge(anyString(), any())).thenReturn(true);
                })) {

        // new PaymentGateway() 返回 Mock 对象
        PaymentGateway gateway = new PaymentGateway();
        assertTrue(gateway.charge("order-001", BigDecimal.TEN));

        assertEquals(1, mocked.constructed().size());
    }
}
```

### 9.4 Answer 接口

```java
@Test
void shouldUseAnswerForComplexLogic() {
    when(userRepository.save(any(User.class)))
        .thenAnswer((Answer<User>) invocation -> {
            User user = invocation.getArgument(0);
            if (user.getName() == null || user.getName().isEmpty()) {
                throw new IllegalArgumentException("用户名不能为空");
            }
            user.setId(System.currentTimeMillis());
            user.setCreatedAt(LocalDateTime.now());
            return user;
        });

    User saved = userRepository.save(new User("王五"));
    assertNotNull(saved.getId());
    assertNotNull(saved.getCreatedAt());
}
```

### 9.5 Timeout 验证

```java
@Test
void shouldVerifyWithinTimeout() {
    asyncService.processData();

    // 在100ms内至少被调用1次
    verify(callback, timeout(100)).onSuccess(any());

    // 在100ms内精确调用3次
    verify(callback, timeout(100).times(3)).onProgress(anyInt());
}
```

---

## 10. 常见陷阱与最佳实践

### 10.1 常见陷阱

```java
// ❌ 陷阱1：Mock 了不该 Mock 的值对象
@Mock
private User user; // 不要 Mock 数据模型，直接构造真实对象

// ✅ 正确
private User user = new User(1L, "张三");

// ❌ 陷阱2：过度 Stub，设置了不需要的返回值
when(repository.findAll()).thenReturn(list); // 如果测试不调用 findAll，这是噪音

// ❌ 陷阱3：Verify 过度，验证了实现细节而非行为
verify(repository, times(1)).save(any()); // 通常只需要验证 "是否调用了 save"

// ❌ 陷阱4：Spy 使用 when-then 导致真实方法执行
@Spy
private ExpensiveService spyService;

when(spyService.expensiveOperation()).thenReturn("mock"); // 会执行真实方法！
doReturn("mock").when(spyService).expensiveOperation();  // 正确

// ❌ 陷阱5：在匹配器中混合使用字面值
when(service.process(anyLong(), "type")).thenReturn(result); // 编译通过但运行时异常
when(service.process(anyLong(), eq("type"))).thenReturn(result); // 正确
```

### 10.2 最佳实践清单

| 实践 | 说明 |
|------|------|
| Mock 依赖，不 Mock 值对象 | User、Order 等数据类直接 new |
| 验证行为，不验证实现 | 关心 "调用了什么" 而非 "怎么调用" |
| 最小化 Stub | 只设置测试路径需要的返回值 |
| 使用 LENIENT 模式或合理 Stub | 避免不必要的严格性 |
| 优先 BDDMockito | 代码可读性更好 |
| 一个测试一个场景 | 避免 verify 之间互相干扰 |
| 不要 Mock 被测对象 | Mock 它的依赖，不要 Mock 被测类本身 |

---

## 11. 面试题速查

**Q1: Mock 和 Spy 的区别？**
- Mock：完全模拟，方法返回默认值（0、null、空集合）
- Spy：包装真实对象，默认调用真实方法，可选择性 Stub

**Q2: when-then 和 doReturn-when 的区别？**
- `when(mock).thenReturn()`：先调用 mock 方法（对 Spy 会执行真实方法）
- `doReturn(value).when(mock).method()`：不执行真实方法，直接设返回值

**Q3: @InjectMocks 的注入策略？**
- 优先级：构造器注入 > Setter 注入 > 字段注入
- 推荐构造器注入，最安全且支持 final 字段

**Q4: ArgumentCaptor 的使用场景？**
- 当需要验证传给 Mock 方法的复杂对象的内容时使用
- 在 verify 中调用 capture() 获取参数

**Q5: Mockito 如何 Mock 静态方法？**
- 使用 `mockStatic(Class)` + try-with-resources
- 需要 mockito-inline 或 Mockito 5+

**Q6: 参数匹配器的规则是什么？**
- 使用匹配器时所有参数都必须是匹配器
- 字面值用 `eq()` 包裹

**Q7: BDDMockito 相比传统 Mockito 的优势？**
- `given().willReturn()` 替代 `when().thenReturn()`，语义更清晰
- `then(mock).should()` 替代 `verify(mock)`
- 代码结构自然符合 Given-When-Then

**Q8: Mockito 的严格模式（Strictness）有什么作用？**
- `STRICT_STUBS`（默认）：未使用的 Stub 会报错，减少测试噪音
- `LENIENT`：允许未使用的 Stub
- `WARN_STUBS`：仅警告不报错

*最后更新：2026-07-13*

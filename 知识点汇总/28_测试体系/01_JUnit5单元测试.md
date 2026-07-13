# JUnit 5 单元测试

> JUnit 5 是 Java 生态中最核心的测试框架，由 JUnit Platform、JUnit Jupiter 和 JUnit Vintage 三大模块组成。它引入了全新的编程模型和扩展模型，支持 Lambda 表达式、嵌套测试、参数化测试、动态测试等现代测试特性，是构建高质量 Java 应用的基石。

---

## 📋 目录

1. [JUnit 5 架构概览](#1-junit-5-架构概览)
2. [核心注解详解](#2-核心注解详解)
3. [断言机制](#3-断言机制)
4. [测试生命周期](#4-测试生命周期)
5. [参数化测试](#5-参数化测试)
6. [嵌套测试](#6-嵌套测试)
7. [动态测试](#7-动态测试)
8. [条件执行](#8-条件执行)
9. [扩展模型](#9-扩展模型)
10. [最佳实践与常见陷阱](#10-最佳实践与常见陷阱)
11. [面试题速查](#11-面试题速查)

---

## 1. JUnit 5 架构概览

JUnit 5 不再是一个单体框架，而是由三个子项目组合而成：

```
JUnit 5 = JUnit Platform + JUnit Jupiter + JUnit Vintage
```

| 模块 | 说明 |
|------|------|
| **JUnit Platform** | 测试框架的基础引擎，定义了 TestEngine API，负责发现和执行测试。IDE 和构建工具通过它接入。 |
| **JUnit Jupiter** | JUnit 5 的编程模型和扩展模型的组合，提供新的注解和 API，是开发者日常使用的核心。 |
| **JUnit Vintage** | 向后兼容模块，支持在 Platform 上运行 JUnit 3 和 JUnit 4 的测试。 |

### Maven 依赖配置

```xml
<dependencies>
    <!-- JUnit Jupiter 依赖（包含 API 和 Engine） -->
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.2.5</version>
        </plugin>
    </plugins>
</build>
```

### Gradle 依赖配置

```groovy
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
}

test {
    useJUnitPlatform()
}
```

---

## 2. 核心注解详解

### 2.1 @Test

JUnit 5 的 `@Test` 注解来自 `org.junit.jupiter.api.Test` 包，不再像 JUnit 4 那样包含 `expected` 和 `timeout` 属性。

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    @Test
    void shouldAddTwoNumbers() {
        Calculator calc = new Calculator();
        int result = calc.add(2, 3);
        assertEquals(5, result);
    }
}
```

### 2.2 @DisplayName

为测试类和测试方法提供自定义的显示名称，支持 Emoji 和中文，极大提升测试报告的可读性。

```java
@DisplayName("🧮 计算器测试")
class CalculatorTest {

    @Test
    @DisplayName("加法运算：2 + 3 = 5")
    void shouldAddTwoNumbers() {
        assertEquals(5, new Calculator().add(2, 3));
    }

    @Test
    @DisplayName("除法运算：10 / 2 = 5")
    void shouldDivideCorrectly() {
        assertEquals(5, new Calculator().divide(10, 2));
    }
}
```

### 2.3 @DisplayNameGeneration

通过策略自动生成测试名称，如将驼峰命名转换为可读句子：

```java
@DisplayNameGeneration(DisplayNameGenerator.ReplaceUnderscores.class)
class CalculatorTest {

    @Test
    void should_add_two_numbers() {
        assertEquals(5, new Calculator().add(2, 3));
    }
    // 显示为：should add two numbers
}
```

### 2.4 @Disabled

禁用测试类或方法，可附加原因说明：

```java
@Disabled("暂时禁用，等待 Issue #42 修复")
@Test
void shouldNotRunForNow() {
    // 不会执行
}
```

### 2.5 @Tag

用于过滤测试，类似于 JUnit 4 的 Categories，适合在 CI 中按标签运行不同套件：

```java
@Tag("slow")
class SlowIntegrationTest {

    @Test
    @Tag("database")
    void testDatabaseConnection() { }

    @Test
    @Tag("network")
    void testNetworkCall() { }
}
```

在 Maven 中按标签过滤：

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <groups>fast</groups>
        <excludedGroups>slow</excludedGroups>
    </configuration>
</plugin>
```

---

## 3. 断言机制

JUnit 5 的断言全面使用 Lambda 表达式，在断言失败时才延迟构造错误消息，避免不必要的字符串拼接开销。

### 3.1 基础断言

```java
import static org.junit.jupiter.api.Assertions.*;

class AssertionDemo {

    @Test
    void standardAssertions() {
        assertEquals(5, 2 + 3);
        assertEquals(5, 2 + 3, "可选的错误消息");
        assertTrue(5 > 3, () -> "延迟计算的消息，仅在失败时构造");
        assertFalse(5 < 3);
        assertNull(null);
        assertNotNull(new Object());
    }

    @Test
    void groupedAssertions() {
        // 分组断言：所有断言都会执行，一次性报告所有失败
        assertAll("用户信息验证",
            () -> assertEquals("张三", user.getName()),
            () -> assertEquals(25, user.getAge()),
            () -> assertEquals("zhangsan@example.com", user.getEmail())
        );
    }
}
```

### 3.2 异常断言

JUnit 5 使用 `assertThrows` 替代了 JUnit 4 的 `@Test(expected = ...)`：

```java
@Test
void shouldThrowArithmeticException() {
    Calculator calc = new Calculator();

    ArithmeticException exception = assertThrows(
        ArithmeticException.class,
        () -> calc.divide(10, 0)
    );

    assertEquals("除数不能为零", exception.getMessage());
}
```

### 3.3 超时断言

```java
@Test
void shouldCompleteWithinTimeout() {
    // 在指定时间内完成
    assertTimeout(Duration.ofSeconds(2), () -> {
        Thread.sleep(1000);
    });

    // 在单独线程中执行，超时后强制中断
    assertTimeoutPreemptively(Duration.ofMillis(500), () -> {
        Thread.sleep(1000); // 会被中断
    });
}
```

### 3.4 自定义断言错误消息

```java
@Test
void withCustomMessage() {
    int expected = 42;
    int actual = compute();

    assertEquals(expected, actual,
        () -> String.format("期望 %d，实际 %d，偏差 %d", expected, actual, Math.abs(expected - actual)));
}
```

---

## 4. 测试生命周期

JUnit 5 的生命周期回调通过注解控制，其中 `@BeforeAll` 和 `@AfterAll` 默认要求方法为 `static`。

### 4.1 生命周期注解

```java
import org.junit.jupiter.api.*;

@DisplayName("生命周期演示")
class LifecycleDemo {

    @BeforeAll
    static void setUpAll() {
        System.out.println("所有测试执行前运行一次（类级别初始化）");
    }

    @BeforeEach
    void setUp() {
        System.out.println("每个测试方法执行前运行");
    }

    @Test
    void test1() {
        System.out.println("执行 test1");
    }

    @Test
    void test2() {
        System.out.println("执行 test2");
    }

    @AfterEach
    void tearDown() {
        System.out.println("每个测试方法执行后运行");
    }

    @AfterAll
    static void tearDownAll() {
        System.out.println("所有测试执行后运行一次（类级别清理）");
    }
}
```

### 4.2 执行顺序

```
@BeforeAll
  ├── @BeforeEach → @Test → @AfterEach
  ├── @BeforeEach → @Test → @AfterEach
  └── ...
@AfterAll
```

### 4.3 非静态生命周期方法

JUnit 5.8+ 支持通过 `@TestInstance` 注解让生命周期方法变为非静态：

```java
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
class NonStaticLifecycleDemo {

    private List<String> items;

    @BeforeAll
    void setUpAll() { // 不再需要 static
        items = new ArrayList<>();
    }

    @AfterAll
    void tearDownAll() { // 不再需要 static
        items.clear();
    }
}
```

---

## 5. 参数化测试

参数化测试允许用不同的参数组合运行同一个测试方法，是替代重复测试代码的利器。

### 5.1 @ValueSource

提供简单的字面值数组：

```java
@ParameterizedTest
@ValueSource(ints = {1, 2, 3, 4, 5})
void shouldReturnTrueForPositiveNumbers(int number) {
    assertTrue(number > 0);
}

@ParameterizedTest
@ValueSource(strings = {"", "  ", "\t"})
void shouldReturnTrueForBlankStrings(String input) {
    assertTrue(input.isBlank());
}

@ParameterizedTest
@NullAndEmptySource
@ValueSource(strings = {"", "  "})
void shouldReturnTrueForNullOrEmpty(String input) {
    assertTrue(input == null || input.isBlank());
}
```

### 5.2 @CsvSource

以 CSV 格式提供多参数：

```java
@ParameterizedTest
@CsvSource({
    "1, 1, 2",
    "2, 3, 5",
    "10, -5, 5",
    "0, 0, 0"
})
void shouldAddCorrectly(int a, int b, int expected) {
    assertEquals(expected, new Calculator().add(a, b));
}
```

### 5.3 @MethodSource

引用工厂方法提供参数（支持 Stream）：

```java
@ParameterizedTest
@MethodSource("provideUserTestData")
void shouldCreateUser(String name, int age, boolean isValid) {
    User user = new User(name, age);
    assertEquals(isValid, user.isValid());
}

static Stream<Arguments> provideUserTestData() {
    return Stream.of(
        Arguments.of("张三", 25, true),
        Arguments.of("李四", 200, false),  // 年龄不合法
        Arguments.of("", 30, false),        // 名字为空
        Arguments.of("王五", -1, false)     // 负数年龄
    );
}
```

### 5.4 @EnumSource

```java
@ParameterizedTest
@EnumSource(value = TimeUnit.class, names = {"NANOSECONDS", "MICROSECONDS"})
void shouldTestSmallTimeUnits(TimeUnit unit) {
    assertTrue(unit.toMillis(1000) < 1);
}

@ParameterizedTest
@EnumSource(value = TimeUnit.class, mode = Mode.EXCLUDE, names = {"DAYS", "HOURS"})
void shouldTestNonDayTimeUnits(TimeUnit unit) {
    assertTrue(unit.toMillis(1) < 86_400_000L);
}
```

### 5.5 自定义参数显示名称

```java
@ParameterizedTest(name = "[{index}] {0} + {1} = {2}")
@CsvSource({
    "1, 2, 3",
    "10, 20, 30",
    "100, 200, 300"
})
void additionTest(int a, int b, int sum) {
    assertEquals(sum, a + b);
}
// 输出：[1] 1 + 2 = 3, [2] 10 + 20 = 30, ...
```

---

## 6. 嵌套测试

`@Nested` 注解允许将相关测试分组到内部类中，表达测试之间的层次关系。内部类可以访问外部类的成员。

```java
@DisplayName("栈数据结构测试")
class StackTest {

    private Stack<String> stack;

    @BeforeEach
    void setUp() {
        stack = new Stack<>();
    }

    @Nested
    @DisplayName("空栈场景")
    class WhenEmpty {

        @Test
        @DisplayName("isEmpty 应返回 true")
        void shouldReturnTrueForIsEmpty() {
            assertTrue(stack.isEmpty());
        }

        @Test
        @DisplayName("pop 应抛出 EmptyStackException")
        void shouldThrowOnPop() {
            assertThrows(EmptyStackException.class, stack::pop);
        }

        @Test
        @DisplayName("peek 应抛出 EmptyStackException")
        void shouldThrowOnPeek() {
            assertThrows(EmptyStackException.class, stack::peek);
        }
    }

    @Nested
    @DisplayName("包含一个元素场景")
    class WhenOneElement {

        @BeforeEach
        void setUp() {
            stack.push("first");
        }

        @Test
        @DisplayName("isEmpty 应返回 false")
        void shouldReturnFalseForIsEmpty() {
            assertFalse(stack.isEmpty());
        }

        @Test
        @DisplayName("pop 应返回该元素")
        void shouldReturnElementOnPop() {
            assertEquals("first", stack.pop());
            assertTrue(stack.isEmpty());
        }

        @Test
        @DisplayName("peek 应返回该元素但不移除")
        void shouldReturnElementOnPeek() {
            assertEquals("first", stack.peek());
            assertEquals(1, stack.size());
        }
    }
}
```

> **注意：** `@BeforeAll` 和 `@AfterAll` 在 `@Nested` 类中默认不可用（需要 `PER_CLASS` 生命周期），`@BeforeEach` 和 `@AfterEach` 按照从外到内的顺序执行。

---

## 7. 动态测试

动态测试允许在运行时生成测试用例，适用于数据驱动场景：

```java
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.TestFactory;

import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.DynamicTest.*;

class DynamicTestDemo {

    @TestFactory
    Stream<DynamicTest> shouldValidateAllEmails() {
        List<String> validEmails = List.of(
            "user@example.com",
            "test.name@domain.org",
            "a@b.cn"
        );

        return validEmails.stream()
            .map(email -> dynamicTest(
                "验证邮箱: " + email,
                () -> assertTrue(EmailValidator.isValid(email))
            ));
    }

    @TestFactory
    Stream<DynamicTest> shouldTestCalculatorOperations() {
        return Stream.of(
            dynamicTest("加法", () -> assertEquals(5, 2 + 3)),
            dynamicTest("减法", () -> assertEquals(1, 3 - 2)),
            dynamicTest("乘法", () -> assertEquals(6, 2 * 3))
        );
    }
}
```

---

## 8. 条件执行

JUnit 5 提供了一组条件执行注解，基于环境、操作系统、JRE 版本等条件决定是否运行测试。

### 8.1 操作系统条件

```java
@Test
@EnabledOnOs(OS.LINUX)
void shouldOnlyRunOnLinux() {
    // 仅在 Linux 上运行
}

@Test
@EnabledOnOs({OS.MAC, OS.WINDOWS})
void shouldRunOnMacOrWindows() {
    // 在 macOS 和 Windows 上运行
}

@Test
@DisabledOnOs(OS.WINDOWS)
void shouldNotRunOnWindows() {
    // 不在 Windows 上运行
}
```

### 8.2 JRE 版本条件

```java
@Test
@EnabledForJreRange(min = JRE.JAVA_11, max = JRE.JAVA_21)
void shouldRunOnJDK11To21() {
    // 仅在 JDK 11 到 21 之间运行
}

@Test
@DisabledOnJre(JRE.JAVA_8)
void shouldNotRunOnJDK8() {
    // 不在 JDK 8 上运行
}
```

### 8.3 系统属性条件

```java
@Test
@EnabledIfSystemProperty(named = "os.arch", matches = ".*64.*")
void shouldRunOn64BitArch() {
    // 仅在 64 位架构上运行
}

@Test
@EnabledIfEnvironmentVariable(named = "ENV", matches = "staging|production")
void shouldRunInStagingOrProduction() {
    // 仅在 staging 或 production 环境运行
}
```

### 8.4 自定义条件

```java
@Test
@EnabledIf("isCIEnvironment")
void shouldRunOnlyInCI() {
    // 自定义条件
}

boolean isCIEnvironment() {
    return "true".equals(System.getenv("CI"));
}
```

---

## 9. 扩展模型

JUnit 5 的扩展模型是替代 JUnit 4 `@RunWith` 和 `@Rule` 的统一机制，通过实现特定接口来扩展框架行为。

### 9.1 核心扩展接口

| 接口 | 用途 |
|------|------|
| `BeforeAllCallback` | 所有测试之前回调 |
| `BeforeEachCallback` | 每个测试之前回调 |
| `AfterEachCallback` | 每个测试之后回调 |
| `AfterAllCallback` | 所有测试之后回调 |
| `InvocationInterceptor` | 拦截测试方法调用 |
| `ParameterResolver` | 为测试方法注入参数 |
| `TestExecutionExceptionHandler` | 处理测试方法抛出的异常 |
| `LifecycleMethodExecutionExceptionHandler` | 处理生命周期方法的异常 |

### 9.2 自定义扩展示例：重试机制

```java
import org.junit.jupiter.api.extension.*;

public class RetryExtension implements InvocationInterceptor, AfterTestExecutionCallback {

    private static final int MAX_RETRIES = 3;
    private static final ExtensionContext.Namespace NAMESPACE =
        ExtensionContext.Namespace.create(RetryExtension.class);

    @Override
    public void interceptTestTemplateMethod(
            Invocation<Void> invocation,
            ReflectiveInvocationContext<Method> invocationContext,
            ExtensionContext extensionContext) throws Throwable {

        int retryCount = extensionContext.getStore(NAMESPACE)
            .getOrComputeIfAbsent("retryCount", k -> 0, Integer.class);

        try {
            invocation.proceed();
        } catch (Throwable t) {
            if (retryCount < MAX_RETRIES) {
                extensionContext.getStore(NAMESPACE).put("retryCount", retryCount + 1);
                System.out.printf("重试第 %d 次...%n", retryCount + 1);
                interceptTestTemplateMethod(invocation, invocationContext, extensionContext);
            } else {
                throw t;
            }
        }
    }
}
```

使用自定义扩展：

```java
@ExtendWith(RetryExtension.class)
class FlakyTestDemo {

    @Test
    void testWithRetry() {
        // 如果失败会自动重试最多3次
    }
}
```

### 9.3 注册扩展的方式

```java
// 方式1：声明式注册
@ExtendWith(MockitoExtension.class)
class MyTest { }

// 方式2：编程式注册
@RegisterExtension
static MyCustomExtension customExt = new MyCustomExtension();

// 方式3：全局注册（META-INF/services）
// 文件：src/test/resources/META-INF/services/org.junit.jupiter.api.extension.Extension
// 内容：com.example.MyExtension
```

---

## 10. 最佳实践与常见陷阱

### 10.1 最佳实践

```java
// ✅ 好的实践：测试方法名表达意图，每个测试只验证一个行为
@DisplayName("用户注册")
class UserRegistrationTest {

    @Nested
    @DisplayName("输入验证")
    class InputValidation {
        @Test
        @DisplayName("空用户名应被拒绝")
        void shouldRejectEmptyUsername() { }

        @Test
        @DisplayName("短密码应被拒绝")
        void shouldRejectShortPassword() { }
    }

    @Nested
    @DisplayName("业务逻辑")
    class BusinessLogic {
        @Test
        @DisplayName("重复邮箱应被拒绝")
        void shouldRejectDuplicateEmail() { }
    }
}
```

### 10.2 常见陷阱

1. **不要在测试方法间共享状态**：JUnit 不保证执行顺序（除非显式配置），每个测试应独立。
2. **避免 `@TestInstance(PER_CLASS)` 滥用**：只有在确实需要共享实例状态时才用。
3. **`assertAll` vs 多个 `assertEquals`**：`assertAll` 会报告所有失败，而单个 `assertEquals` 在第一次失败时即停止。
4. **参数化测试的参数来源**：`@MethodSource` 引用的方法必须为 `static`（除非使用 `PER_CLASS`）。
5. **不要在测试中使用 `System.out.println` 做断言**：使用真正的断言方法。

---

## 11. 面试题速查

**Q1: JUnit 5 和 JUnit 4 的主要区别是什么？**
- 架构拆分为 Platform + Jupiter + Vintage 三层
- 注解从 `org.junit` 迁移到 `org.junit.jupiter.api`
- `@Test` 不再支持 `expected` 和 `timeout` 属性，改用 `assertThrows` 和 `assertTimeout`
- 新增 `@Nested`、`@ParameterizedTest`、`@DynamicTest` 等特性
- 扩展模型替代 `@RunWith` 和 `@Rule`

**Q2: @BeforeAll 和 @BeforeEach 的区别？**
- `@BeforeAll` 在所有测试方法前执行一次，必须是 `static`
- `@BeforeEach` 在每个测试方法前执行一次

**Q3: 参数化测试有哪些参数来源？**
- `@ValueSource`：简单值数组
- `@CsvSource`：CSV 格式多参数
- `@MethodSource`：工厂方法提供 Stream
- `@EnumSource`：枚举值
- `@ArgumentsSource`：自定义 ArgumentsProvider

**Q4: assertAll 的作用是什么？**
- 分组断言，即使前面的断言失败也会继续执行后续断言，最终一次性报告所有失败。

**Q5: 如何禁用测试？**
- 使用 `@Disabled` 注解，可附加原因说明。

**Q6: @Nested 注解的限制是什么？**
- 不支持 `@BeforeAll`/`@AfterAll`（默认生命周期下）
- 不能为 static 类
- 可以访问外部类的实例字段

**Q7: JUnit 5 扩展模型的核心接口有哪些？**
- `BeforeAllCallback`、`BeforeEachCallback`、`AfterEachCallback`、`AfterAllCallback`
- `ParameterResolver`、`InvocationInterceptor`、`TestExecutionExceptionHandler`

**Q8: assertTimeout 和 assertTimeoutPreemptively 的区别？**
- `assertTimeout`：在同一线程执行，超时后等任务完成再报告
- `assertTimeoutPreemptively`：在单独线程执行，超时后立即中断

*最后更新：2026-07-13*

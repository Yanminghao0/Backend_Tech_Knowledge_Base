# Clean Code精要

> "代码就像幽默——如果你必须解释它，那它就不够好。" —— Cory House。Robert C. Martin（Uncle Bob）的《Clean Code》是软件工程领域的经典著作，本文提炼其核心思想，涵盖命名、函数、注释、错误处理、类设计等关键主题。

---

## 📋 目录

1. [有意义的命名](#1-有意义的命名)
2. [函数原则](#2-函数原则)
3. [注释的艺术](#3-注释的艺术)
4. [错误处理](#4-错误处理)
5. [边界条件](#5-边界条件)
6. [类设计](#6-类设计)
7. [系统设计](#7-系统设计)
8. [面试题速查](#8-面试题速查)

---

## 1. 有意义的命名

### 1.1 名副其实

好的名字应该能回答三个问题：它为什么存在？它做什么？它如何使用？如果名称需要注释来补充说明，那它就不是一个好名字。

```java
// ❌ 不好的命名——名字没有传达意图
public List<int[]> getThem() {
    List<int[]> list1 = new ArrayList<>();
    for (int[] x : theList) {
        if (x[0] == 4) {
            list1.add(x);
        }
    }
    return list1;
}

// ✅ 有意义的命名——使用领域语言
public List<Cell> getFlaggedCells() {
    List<Cell> flaggedCells = new ArrayList<>();
    for (Cell cell : gameBoard) {
        if (cell.isFlagged()) {
            flaggedCells.add(cell);
        }
    }
    return flaggedCells;
}
```

### 1.2 避免误导

```java
// ❌ 使用保留字或特殊含义的名称
String accountList = "..."  // 不是List类型却叫List，误导读者
int hp = 350;               // hp可能被理解为 Hewlett-Packard

// ❌ 使用名称相近的变量
int xyzCoord1;  // 在同一作用域中很难区分
int xyzCoord2;
int XYZCoord;   // 大小写不同，但视觉上难以区分

// ✅ 使用准确且独特的名称
String accountNumbers;
int heatedPressure;
int xPosition;
int yPosition;
int zPosition;
```

### 1.3 有意义的区分

```java
// ❌ 无意义的区分
class Product {
    private String name;
    private String nameString;  // String后缀毫无意义
}
class ProductService {
    private Product[] products;
    private Product[] productsArray;  // Array后缀在Java中多余
}

// ❌ 数字命名
copyChars(char[] source, char[] destination)  // 尚可
copyChars(char[] a1, char[] a2)               // 糟糕

// ❌ 废话命名
class CustomerObject {}   // Object后缀多余
class CustomerInfo {}     // Info后缀通常无意义
class CustomerData {}     // Data后缀通常无意义
// 这三个类名实际表达的是同一个概念

// ✅ 有意义的区分
class Customer {}
class CustomerProfile {}   // 明确表示用户画像
class CustomerRecord {}    // 明确表示用户记录
```

### 1.4 使用可搜索的名称

```java
// ❌ 魔法数字不可搜索
for (int i = 0; i < 34; i++) {
    schedule[i] = new Task(4, 5);  // 34和4,5代表什么？
}

// ✅ 常量命名
private static final int NUMBER_OF_TASKS = 34;
private static final int WORK_DAYS_PER_WEEK = 5;
private static final int TASK_TYPE_NORMAL = 4;

for (int i = 0; i < NUMBER_OF_TASKS; i++) {
    schedule[i] = new Task(TASK_TYPE_NORMAL, WORK_DAYS_PER_WEEK);
}

// 变量名长度应与其作用域大小成正比
// 短作用域可以用短名称
for (int i = 0; i < n; i++) {
    process(items[i]);
}

// 长作用域应该用有描述性的名称
public class OrderPaymentProcessor {
    private PaymentGateway paymentGateway;
    private FraudDetectionService fraudDetectionService;
}
```

### 1.5 类名与方法名

```java
// 类名应该是名词或名词短语
class Customer { }
class OrderProcessor { }
class WikiPage { }
class Account { }

// ❌ 类名使用动词
class ProcessData { }  // 应改为 DataProcessor
class StartServer { }  // 应改为 ServerBootstrap

// 方法名应该是动词或动词短语
postPayment(payment);
deletePage(page);
savePage(page);

// 属性访问器使用get/set前缀
String getName();
void setName(String name);
boolean isPosted();  // 布尔用is前缀
```

---

## 2. 函数原则

### 2.1 短小精悍

函数应该尽可能短小。第一条规则是函数应该很矮小，第二条规则是它应该更矮小。

```java
// ❌ 长函数——一个函数做了太多事情
public void processOrder(Order order) {
    // 验证
    if (order.getItems() == null || order.getItems().isEmpty()) {
        throw new IllegalArgumentException("订单项不能为空");
    }
    if (order.getCustomer() == null) {
        throw new IllegalArgumentException("客户不能为空");
    }
    if (order.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
        throw new IllegalArgumentException("订单金额必须大于0");
    }
    
    // 计算折扣
    BigDecimal discount = BigDecimal.ZERO;
    if (order.getCustomer().isVip()) {
        discount = order.getAmount().multiply(new BigDecimal("0.1"));
    } else if (order.getAmount().compareTo(new BigDecimal("1000")) > 0) {
        discount = order.getAmount().multiply(new BigDecimal("0.05"));
    }
    
    // 扣库存
    for (OrderItem item : order.getItems()) {
        Product product = productRepository.findById(item.getProductId());
        if (product.getStock() < item.getQuantity()) {
            throw new BusinessException("库存不足: " + product.getName());
        }
        product.setStock(product.getStock() - item.getQuantity());
        productRepository.save(product);
    }
    
    // 保存订单
    order.setDiscount(discount);
    order.setFinalAmount(order.getAmount().subtract(discount));
    order.setStatus(OrderStatus.PROCESSED);
    orderRepository.save(order);
    
    // 发送通知
    emailService.sendOrderConfirmation(order.getCustomer().getEmail(), order);
    if (order.getCustomer().isVip()) {
        smsService.sendSms(order.getCustomer().getPhone(), "VIP订单已处理");
    }
}

// ✅ 短小精悍的函数——每个函数只做一件事
public void processOrder(Order order) {
    validateOrder(order);
    applyDiscount(order);
    deductStock(order);
    saveOrder(order);
    notifyCustomer(order);
}

private void validateOrder(Order order) {
    validateOrderItems(order);
    validateCustomer(order);
    validateAmount(order);
}

private void validateOrderItems(Order order) {
    if (CollectionUtils.isEmpty(order.getItems())) {
        throw new IllegalArgumentException("订单项不能为空");
    }
}

private void applyDiscount(Order order) {
    DiscountPolicy policy = discountPolicyFactory.getPolicy(order.getCustomer());
    BigDecimal discount = policy.calculate(order);
    order.setDiscount(discount);
    order.setFinalAmount(order.getAmount().subtract(discount));
}

private void deductStock(Order order) {
    for (OrderItem item : order.getItems()) {
        stockService.deduct(item.getProductId(), item.getQuantity());
    }
}

private void saveOrder(Order order) {
    order.setStatus(OrderStatus.PROCESSED);
    orderRepository.save(order);
}

private void notifyCustomer(Order order) {
    notificationService.notifyOrderProcessed(order);
}
```

### 2.2 单一职责

每个函数应该只做一件事。判断"一件事"的标准：函数中的所有语句应该在同一抽象层级。

```java
// ❌ 混合了不同抽象层级
public void renderPage(Page page) {
    // 高层抽象
    page.initialize();
    
    // 低层抽象——HTML拼接细节
    StringBuilder html = new StringBuilder();
    html.append("<html><head><title>");
    html.append(page.getTitle());
    html.append("</title></head><body>");
    
    // 中层抽象
    for (Paragraph paragraph : page.getParagraphs()) {
        html.append("<p>").append(paragraph.getText()).append("</p>");
    }
    
    html.append("</body></html>");
    page.setContent(html.toString());
    
    // 高层抽象
    page.render();
}

// ✅ 统一抽象层级
public void renderPage(Page page) {
    page.initialize();
    String html = buildHtml(page);
    page.setContent(html);
    page.render();
}

private String buildHtml(Page page) {
    String head = buildHead(page.getTitle());
    String body = buildBody(page.getParagraphs());
    return head + body;
}

private String buildHead(String title) {
    return String.format("<html><head><title>%s</title></head>", title);
}

private String buildBody(List<Paragraph> paragraphs) {
    StringBuilder body = new StringBuilder("<body>");
    paragraphs.forEach(p -> body.append("<p>").append(p.getText()).append("</p>"));
    body.append("</body></html>");
    return body.toString();
}
```

### 2.3 函数参数

函数参数最理想的数量是零，其次是一，再次是二，应尽量避免三个以上参数。

```java
// ❌ 零参数（如果函数有副作用，需要说明）
saveContext();  // 保存什么context？到处都叫context

// ✅ 零参数
save();
context.save();

// ❌ 一个参数但语义不清
process(order);  // 处理什么？返回什么？

// ✅ 清晰的单参数
OrderResult result = order.process();
boolean isValid = validator.validate(order);

// ❌ 多个布尔参数
createUser("张三", "zhangsan@test.com", true, false, true);
// 三个布尔参数：isAdmin, sendEmail, forceCreate —— 调用处完全看不懂

// ✅ 使用参数对象或枚举
createUser(CreateUserRequest.builder()
        .name("张三")
        .email("zhangsan@test.com")
        .role(Role.ADMIN)
        .sendNotification(true)
        .force(false)
        .build());

// ❌ 标志参数——函数不只做一件事
render(true);  // true表示什么？矩形还是圆形？测试模式还是生产模式？

// ✅ 拆分为两个函数
renderForTest();
renderForProduction();
```

### 2.4 无副作用

函数承诺做一件事，但同时也做了隐藏的另一件事，这会产生难以排查的bug。

```java
// ❌ 函数名说是检查密码，但还有初始化Session的副作用
public boolean checkPassword(String userName, String password) {
    User user = userRepository.findByName(userName);
    if (user != null) {
        String codedPhrase = user.getPhraseEncoded();
        String phrase = decrypt(codedPhrase, DECRYPTION_KEY);
        if (password.equals(phrase)) {
            Session.initialize();  // 副作用！调用者不知道这里初始化了Session
            return true;
        }
    }
    return false;
}

// ✅ 分离副作用
public boolean checkPassword(String userName, String password) {
    User user = userRepository.findByName(userName);
    if (user == null) return false;
    
    String expectedPhrase = decrypt(user.getPhraseEncoded(), DECRYPTION_KEY);
    return password.equals(expectedPhrase);
}

// 调用者显式初始化Session
if (checkPassword(userName, password)) {
    Session.initialize();
}
```

### 2.5 命令与查询分离

函数应该要么做什么事（命令），要么回答什么事（查询），但不能两者兼做。

```java
// ❌ 既设置属性又返回是否成功——命令与查询混合
public boolean set(String attribute, String value) {
    // 如果属性不存在则返回false
    // 如果设置成功则返回true
    // 调用者无法区分"属性不存在"和"设置失败"
    if (attributeExists(attribute)) {
        setAttribute(attribute, value);
        return true;
    }
    return false;
}

// 怎么用？
if (set("username", "admin")) {
    // 设置成功了？还是属性存在？
}

// ✅ 分离命令与查询
public boolean attributeExists(String attribute) {
    // 查询：属性是否存在
}

public void setAttribute(String attribute, String value) {
    // 命令：设置属性
}

// 调用清晰
if (attributeExists("username")) {
    setAttribute("username", "admin");
}
```

---

## 3. 注释的艺术

### 3.1 注释不是好代码的替代品

```java
// ❌ 用注释弥补糟糕的代码
// 检查员工是否满足退休条件：年龄大于60且工龄大于20
if (employee.age > 60 && employee.yearsOfService > 20 && 
    employee.department != "SALES" && employee.level < 5) {
    processRetirement(employee);
}

// ✅ 用代码表达意图，不需要注释
if (employee.isEligibleForRetirement()) {
    processRetirement(employee);
}

// Employee类中
public boolean isEligibleForRetirement() {
    return age > 60 && yearsOfService > 20 
           && department != Department.SALES 
           && level < 5;
}
```

### 3.2 好的注释

```java
// 法律性注释
// Copyright (C) 2024 Company Inc. All rights reserved.
// Licensed under the Apache License, Version 2.0

// 信息性注释——提供代码无法表达的信息
// 已知的性能问题：当数据量超过10万时，此算法会退化为O(n²)
// 待优化：计划在V2.0版本中替换为分治算法
public void sortLargeDataset(List<Data> dataset) { ... }

// 意图解释——解释为什么这样做，而不是做了什么
// 使用快速排序而非归并排序：内存受限环境下快速排序空间复杂度更优
// 参考：https://en.wikipedia.org/wiki/Quicksort#Space_complexity
public void sort(List<Data> data) { ... }

// 警示性注释
// 注意：此方法会修改传入的List参数，调用前请确保不需要原始数据
// TODO: 后续版本应该改为返回新List而非原地修改
public void filterInPlace(List<Data> data) { ... }

// 强调注释
// 这里的Thread.sleep(100)不是bug！外部系统需要时间完成状态刷新
// 去掉会导致间歇性的状态读取失败
Thread.sleep(100);

// 公共API的Javadoc
/**
 * 将订单状态更新为已完成。
 * 
 * <p>此方法会触发以下操作：
 * <ul>
 *   <li>更新订单状态</li>
 *   <li>发送完成通知</li>
 *   <li>记录审计日志</li>
 * </ul>
 *
 * @param orderId 订单ID，不能为null
 * @return 更新后的订单
 * @throws OrderNotFoundException 订单不存在时抛出
 * @throws IllegalStateException 订单状态不允许完成时抛出
 */
public Order completeOrder(Long orderId) { ... }
```

### 3.3 坏的注释

```java
// ❌ 多余的注释——代码本身已经很清楚
// 获取用户
User user = userRepository.findById(userId);

// ❌ 误导性注释——注释与代码不一致
// 此方法只会返回活跃用户
public List<User> getAllUsers() {
    return userRepository.findAll();  // 实际返回所有用户包括非活跃的
}

// ❌ 日志式注释——应该用版本控制
// 2024-01-15 张三 创建此方法
// 2024-01-20 李四 修改返回值
// 2024-02-01 王五 添加异常处理

// ❌ 位置标记——通常是不必要的噪音
/////// Properties ////////
private String name;
private int age;

// ❌ 闭合括号注释——函数太长的信号
public void process() {
    if (condition) {
        while (loop) {
            for (int i = 0; i < n; i++) {
                // ...
            } // for
        } // while
    } // if
} // process
// 如果需要这种注释，说明函数需要拆分
```

---

## 4. 错误处理

### 4.1 使用异常而非返回码

```java
// ❌ 返回错误码——调用者必须检查返回值
public int deletePage(Page page) {
    if (page == null) return E_NULL;
    if (!pageExists(page)) return E_NO_PAGE;
    // ...
    return E_OK;
}

// 调用者容易忘记检查
deletePage(page);
// 继续执行，不知道删除是否成功

// ✅ 使用异常
public void deletePage(Page page) {
    Objects.requireNonNull(page, "page不能为空");
    if (!pageExists(page)) {
        throw new PageNotFoundException(page.getId());
    }
    // ...
}

// 异常会中断执行流程，调用者必须处理
try {
    deletePage(page);
} catch (PageNotFoundException e) {
    log.warn("页面不存在: {}", page.getId(), e);
    handleMissingPage(page);
}
```

### 4.2 先写Try-Catch-Finally

```java
// 先定义异常边界，再实现逻辑
public List<Record> gatherRecords(String fileId) {
    List<Record> records = new ArrayList<>();
    try (InputStream in = openFile(fileId)) {
        readRecords(in, records);
    } catch (IOException e) {
        log.error("读取文件失败: fileId={}", fileId, e);
        throw new FileReadException(fileId, e);
    }
    return records;
}

// 然后逐步实现细节
private void readRecords(InputStream in, List<Record> records) throws IOException {
    BufferedReader reader = new BufferedReader(new InputStreamReader(in));
    String line;
    while ((line = reader.readLine()) != null) {
        records.add(parseRecord(line));
    }
}
```

### 4.3 提供异常的上下文

```java
// ❌ 异常信息不够
throw new IllegalArgumentException("Invalid input");

// ❌ 异常信息没有上下文
throw new RuntimeException("Error occurred");

// ✅ 提供操作上下文和具体数据
throw new IllegalArgumentException(
    String.format("无效的订单金额: %s, 订单号: %s, 用户ID: %s", 
        order.getAmount(), order.getOrderNo(), order.getUserId()));

// ✅ 自定义异常携带结构化信息
public class OrderValidationException extends RuntimeException {
    private final String orderNo;
    private final String field;
    private final String invalidValue;
    
    public OrderValidationException(String orderNo, String field, String invalidValue) {
        super(String.format("订单验证失败: 订单号=%s, 字段=%s, 无效值=%s", 
              orderNo, field, invalidValue));
        this.orderNo = orderNo;
        this.field = field;
        this.invalidValue = invalidValue;
    }
    
    // getters...
}
```

### 4.4 不返回null

```java
// ❌ 返回null
public List<Item> getCartItems(Long userId) {
    User user = userRepository.findById(userId);
    if (user == null) {
        return null;  // 调用者必须判空
    }
    return user.getCart().getItems();
}

// 调用者代码
List<Item> items = getCartItems(userId);
if (items != null) {  // 容易遗漏
    for (Item item : items) { ... }
}

// ✅ 返回空集合
public List<Item> getCartItems(Long userId) {
    User user = userRepository.findById(userId);
    if (user == null) {
        return Collections.emptyList();
    }
    return user.getCart().getItems();
}

// 调用者无需判空
List<Item> items = getCartItems(userId);
for (Item item : items) { ... }  // 空集合直接跳过循环

// ✅ 使用Optional表达可能不存在的值
public Optional<User> findUser(Long userId) {
    return Optional.ofNullable(userRepository.findById(userId));
}

// 调用者
findUser(userId)
    .map(User::getEmail)
    .ifPresent(emailService::sendWelcomeEmail);
```

---

## 5. 边界条件

### 5.1 第三方代码边界

```java
// 处理第三方库的边界——适配器模式
// 第三方库的Map返回可能为null
public class SensorDataAdapter {
    private final ThirdPartySensorClient client;
    
    // 封装第三方API的异常行为
    public List<SensorReading> getReadings() {
        try {
            List<SensorReading> readings = client.fetchReadings();
            return readings != null ? readings : Collections.emptyList();
        } catch (ThirdPartyException e) {
            log.warn("传感器数据获取失败", e);
            return Collections.emptyList();
        }
    }
    
    // 将第三方类型转换为本系统类型
    public List<SensorData> getSensorData() {
        return getReadings().stream()
                .map(this::toSensorData)
                .collect(Collectors.toList());
    }
    
    private SensorData toSensorData(SensorReading reading) {
        return SensorData.builder()
                .value(reading.getValue())
                .timestamp(Instant.ofEpochMilli(reading.getTimestamp()))
                .unit(reading.getUnit())
                .build();
    }
}
```

### 5.2 边界测试

```java
// 测试边界条件
@Test
@DisplayName("分页查询边界条件测试")
void testPaginationBoundaries() {
    // 空列表
    PageResult<Item> emptyResult = service.findByPage(PageRequest.of(0, 10));
    assertTrue(emptyResult.getItems().isEmpty());
    assertEquals(0, emptyResult.getTotal());
    
    // 刚好一页
    setupTestData(10);
    PageResult<Item> onePage = service.findByPage(PageRequest.of(0, 10));
    assertEquals(10, onePage.getItems().size());
    assertEquals(1, onePage.getTotalPages());
    
    // 最后一页不完整
    setupTestData(15);
    PageResult<Item> lastPage = service.findByPage(PageRequest.of(1, 10));
    assertEquals(5, lastPage.getItems().size());
    assertEquals(2, lastPage.getTotalPages());
    
    // 超出页码范围
    PageResult<Item> outOfRange = service.findByPage(PageRequest.of(100, 10));
    assertTrue(outOfRange.getItems().isEmpty());
}
```

---

## 6. 类设计

### 6.1 类的组织

```java
// 类应该按照以下顺序组织：
// 1. 静态常量
// 2. 静态变量
// 3. 实例变量
// 4. 公共方法
// 5. 私有方法（被公共方法调用）

public class OrderService {
    // 静态常量
    private static final int MAX_ITEMS = 100;
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    
    // 实例变量
    private final OrderRepository orderRepository;
    private final PaymentService paymentService;
    private final DiscountCalculator discountCalculator;
    
    // 构造器
    public OrderService(OrderRepository orderRepository, 
                        PaymentService paymentService,
                        DiscountCalculator discountCalculator) {
        this.orderRepository = orderRepository;
        this.paymentService = paymentService;
        this.discountCalculator = discountCalculator;
    }
    
    // 公共方法
    public OrderResult createOrder(CreateOrderRequest request) {
        Order order = buildOrder(request);
        applyDiscount(order);
        processPayment(order);
        return saveOrder(order);
    }
    
    public void cancelOrder(Long orderId) {
        Order order = findOrder(orderId);
        validateCancellable(order);
        order.cancel();
        orderRepository.save(order);
    }
    
    // 私有方法——按调用顺序排列
    private Order buildOrder(CreateOrderRequest request) { ... }
    
    private void applyDiscount(Order order) {
        BigDecimal discount = discountCalculator.calculate(order);
        order.setDiscount(discount);
    }
    
    private void processPayment(Order order) { ... }
    
    private OrderResult saveOrder(Order order) { ... }
}
```

### 6.2 SRP（单一职责原则）

```java
// ❌ 一个类承担了太多职责
public class OrderManager {
    // 订单创建
    public Order createOrder() { ... }
    
    // 数据库操作
    public void saveToDatabase(Order order) { ... }
    public Order loadFromDatabase(Long id) { ... }
    
    // 邮件发送
    public void sendConfirmationEmail(Order order) { ... }
    public void sendCancellationEmail(Order order) { ... }
    
    // 报表生成
    public byte[] generateInvoice(Order order) { ... }
    public byte[] generateShippingLabel(Order order) { ... }
    
    // 库存管理
    public void updateStock(Order order) { ... }
}

// ✅ 每个类只承担一个职责
public class OrderService {          // 订单业务逻辑
    public Order createOrder() { ... }
    public void cancelOrder(Long id) { ... }
}

public class OrderRepository {       // 数据持久化
    public void save(Order order) { ... }
    public Order findById(Long id) { ... }
}

public class OrderNotificationService {  // 通知服务
    public void sendConfirmation(Order order) { ... }
    public void sendCancellation(Order order) { ... }
}

public class OrderReportService {    // 报表生成
    public byte[] generateInvoice(Order order) { ... }
    public byte[] generateShippingLabel(Order order) { ... }
}

public class InventoryService {      // 库存管理
    public void deductStock(Order order) { ... }
}
```

### 6.3 内聚性

```java
// ❌ 低内聚——方法使用的字段不集中
public class Report {
    private String title;
    private String content;
    private int pageSize;
    private String printerName;
    private int copies;
    
    public void formatReport() {
        // 只使用 title 和 content
    }
    
    public void printReport() {
        // 只使用 printerName 和 copies
    }
    
    public void setPageLayout() {
        // 只使用 pageSize
    }
}
// 每个方法只用一部分字段，说明类应该拆分

// ✅ 高内聚——每个方法使用大部分或全部字段
public class Report {
    private String title;
    private String content;
    private LocalDateTime generatedAt;
    private String generatedBy;
    
    public String format() {
        // 使用所有字段
        return String.format("%s\n作者: %s\n时间: %s\n\n%s", 
            title, generatedBy, generatedAt, content);
    }
    
    public boolean isValid() {
        // 使用 title 和 content
        return title != null && !title.isEmpty() 
               && content != null && !content.isEmpty();
    }
}
```

---

## 7. 系统设计

### 7.1 依赖注入

```java
// ❌ 硬编码依赖——难以测试和维护
public class OrderService {
    private MySQLDatabase database = new MySQLDatabase();  // 硬编码
    private EmailSender emailSender = new SmtpEmailSender();  // 硬编码
    
    public void processOrder(Order order) {
        database.save(order);
        emailSender.send(order.getCustomerEmail());
    }
}

// ✅ 依赖注入——解耦
public class OrderService {
    private final OrderRepository orderRepository;  // 接口
    private final NotificationService notificationService;  // 接口
    
    // 构造器注入
    public OrderService(OrderRepository orderRepository, 
                        NotificationService notificationService) {
        this.orderRepository = orderRepository;
        this.notificationService = notificationService;
    }
    
    public void processOrder(Order order) {
        orderRepository.save(order);
        notificationService.notify(order);
    }
}

// 测试时可以注入Mock
@Test
void testProcessOrder() {
    OrderRepository mockRepo = mock(OrderRepository.class);
    NotificationService mockNotification = mock(NotificationService.class);
    OrderService service = new OrderService(mockRepo, mockNotification);
    
    service.processOrder(testOrder);
    
    verify(mockRepo).save(testOrder);
    verify(mockNotification).notify(testOrder);
}
```

### 7.2 分层架构

```
┌─────────────────────────────────────────┐
│           Controller Layer              │  ← 处理HTTP请求/响应
│  OrderController, UserController         │
├─────────────────────────────────────────┤
│            Service Layer                │  ← 业务逻辑
│  OrderService, PaymentService            │
├─────────────────────────────────────────┤
│          Repository Layer               │  ← 数据访问
│  OrderRepository, UserRepository         │
├─────────────────────────────────────────┤
│           Domain Layer                  │  ← 领域模型
│  Order, User, Payment                    │
└─────────────────────────────────────────┘

依赖方向：上层依赖下层，下层不感知上层

```java
// Controller Layer
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    private final OrderService orderService;
    
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(@RequestBody CreateOrderRequest request) {
        return ResponseEntity.ok(orderService.createOrder(request));
    }
}

// Service Layer
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final PaymentService paymentService;
    
    public OrderResponse createOrder(CreateOrderRequest request) {
        Order order = Order.create(request);
        paymentService.process(order);
        orderRepository.save(order);
        return OrderResponse.from(order);
    }
}

// Repository Layer
@Repository
public class JpaOrderRepository implements OrderRepository {
    private final SpringDataOrderRepository springDataRepo;
    
    public Order save(Order order) {
        OrderEntity entity = OrderEntity.from(order);
        return springDataRepo.save(entity).toDomain();
    }
}

// Domain Layer
public class Order {
    private final OrderId id;
    private final CustomerId customerId;
    private final List<OrderItem> items;
    private OrderStatus status;
    
    public static Order create(CreateOrderRequest request) {
        // 领域逻辑封装在领域对象中
    }
    
    public void cancel() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("只有待处理订单可以取消");
        }
        this.status = OrderStatus.CANCELLED;
    }
}
```

### 7.3 系统构建与运行分离

```java
// ❌ 在业务逻辑中构建依赖
public class Application {
    public void start() {
        Database db = new MySQLDatabase("localhost", 3306);
        Cache cache = new RedisCache("localhost", 6379);
        OrderService orderService = new OrderService(db, cache);
        // 启动应用
    }
}

// ✅ 分离构建与运行
public class Application {
    private final OrderService orderService;
    
    // 依赖通过构造器注入
    public Application(OrderService orderService) {
        this.orderService = orderService;
    }
    
    // 运行逻辑
    public void start() {
        orderService.startProcessing();
    }
    
    // 构建逻辑在单独的工厂/容器中
    public static void main(String[] args) {
        Application app = createApplication();
        app.start();
    }
    
    private static Application createApplication() {
        // DI容器负责构建对象图
        ApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
        return context.getBean(Application.class);
    }
}
```

---

## 8. 面试题速查

**Q1: Clean Code的核心原则是什么？**
> 核心原则包括：有意义的命名、函数短小且只做一件事（SRP）、避免重复（DRY）、表达意图而非实现、最小化副作用、适当的错误处理、保持类的内聚性。总体目标是让代码"对人友好"，而不仅仅是让机器能执行。

**Q2: 如何判断一个函数是否只做了一件事？**
> 如果一个函数中的语句可以按功能分组到不同的区域，或者你能在函数内部提取出另一个有意义的函数名，那它可能做了不止一件事。另一个判断标准：函数中的所有操作是否在同一抽象层级——混合抽象层级通常意味着做了多件事。

**Q3: 为什么应该避免返回null？**
> 返回null要求每个调用者都进行null检查，遗漏检查会导致NullPointerException。替代方案：返回空集合、使用Optional、使用Null Object模式。返回null本质上是把错误处理的负担转嫁给了调用者，容易导致防御性编程泛滥和代码臃肿。

**Q4: 注释的恰当使用场景有哪些？**
> 适当的注释场景：法律声明、公共API文档（Javadoc）、解释"为什么"而非"是什么"的意图说明、对外部约束或已知问题的警告、TODO标记。不恰当的场景：用注释弥补糟糕的代码（应重构代码）、多余的注释（代码已自解释）、日志式变更记录（应由VCS管理）、位置标记噪音。

**Q5: 命令-查询分离原则（CQS）是什么？**
> 一个方法应该要么是执行动作的命令（改变状态，无返回值），要么是返回信息的查询（不改变状态，有返回值），但不能两者兼是。混合命令和查询的方法容易导致歧义和难以理解的行为，例如`set()`方法返回布尔值让人困惑它是设置成功还是检查存在。

**Q6: 类的内聚性如何衡量？**
> 内聚性衡量类中方法和字段的关联程度。高内聚的类中每个方法使用大部分或全部实例字段。低内聚的类中方法只用一小部分字段，这通常意味着类应该拆分。衡量方法：计算方法使用的字段比例，比例越低内聚性越差。

**Q7: 依赖注入的好处是什么？**
> 1）解耦：依赖接口而非实现，降低模块间耦合度。2）可测试性：测试时可注入Mock对象，隔离被测单元。3）可维护性：更换实现只需修改注入配置，无需修改业务代码。4）生命周期管理：DI容器统一管理对象的创建和销毁。5）消除重复的构建代码。

**Q8: 函数参数为什么应该尽量少？**
> 参数越多，函数理解越困难，测试组合越多（参数数量是组合爆炸的基础）。最理想的参数数量是零，单参数函数次之。三参数函数应尽量避免。避免布尔参数（标志参数），因为它意味着函数做了不止一件事。多参数可以用参数对象封装。

---

*最后更新：2026-07-13*
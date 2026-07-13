# 阿里Java开发手册精读

> 阿里巴巴Java开发手册是业界最广泛采用的Java编码规范之一，涵盖了从命名到部署的全生命周期规约。本文对手册核心章节进行深度解读，结合实际开发场景给出最佳实践。

---

## 📋 目录

1. [命名规范](#1-命名规范)
2. [常量定义](#2-常量定义)
3. [格式规约](#3-格式规约)
4. [OOP规约](#4-oop规约)
5. [集合处理](#5-集合处理)
6. [并发处理](#6-并发处理)
7. [异常处理](#7-异常处理)
8. [日志规约](#8-日志规约)
9. [MySQL规约](#9-mysql规约)
10. [面试题速查](#10-面试题速查)

---

## 1. 命名规范

### 1.1 基本原则

命名是代码可读性的第一道关卡。阿里手册强制要求：

- **类名**：UpperCamelCase，如 `UserService`、`OrderController`
- **方法名/变量名**：lowerCamelCase，如 `getUserById`、`userName`
- **常量名**：全大写，下划线分隔，如 `MAX_RETRY_COUNT`、`DEFAULT_PAGE_SIZE`
- **包名**：全小写，连续单数，如 `com.alibaba.user`（不使用 `users`）
- **抽象类名**：以 `Abstract` 或 `Base` 开头
- **异常类名**：以 `Exception` 结尾
- **测试类名**：以被测类名开头，`Test` 结尾

```java
// ✅ 正确示例
public class OrderServiceImpl extends AbstractOrderService {
    private static final int MAX_ORDER_ITEMS = 100;
    private OrderRepository orderRepository;
    
    public OrderResult createOrder(CreateOrderRequest request) { ... }
}

// ❌ 错误示例
public class orderService {  // 类名首字母应大写
    private static final int maxOrderItems = 100;  // 常量应全大写
    public orderResult CreateOrder(createorderrequest request) { ... }  // 方法名/类名混乱
}
```

### 1.2 常见命名陷阱

```java
// ❌ 使用拼音命名
private String dingdanBianHao;  // 应使用 orderNumber

// ❌ 使用缩写导致歧义
private List<User> us;  // 应使用 userList 或 users

// ❌ 布尔变量使用 is 前缀但在序列化时出问题
private boolean isDeleted;  // RPC框架可能序列化为 deleted，导致字段不一致

// ✅ 推荐做法
private boolean deleted;
```

### 1.3 接口与实现命名

```java
// 接口名：简洁表达行为
public interface UserRepository {
    User findById(Long id);
}

// 实现类名：接口名 + Impl，或者根据技术栈命名
public class UserRepositoryImpl implements UserRepository { }
public class UserJpaRepository implements UserRepository { }  // 也可用技术栈标识
```

> **核心要点**：命名应做到"见名知意"，避免过度缩写，杜绝拼音和中文。好的命名胜过注释。

---

## 2. 常量定义

### 2.1 常量分层管理

阿里手册要求常量按层级管理，避免魔法值散落代码各处：

```java
// 第一层：跨应用共享常量
// 放在二方库中，如 com.alibaba.common.constant.OrderConstants
public class OrderConstants {
    public static final String ORDER_STATUS_PAID = "PAID";
    public static final String ORDER_STATUS_CANCELLED = "CANCELLED";
}

// 第二层：应用内共享常量
// 放在应用内部的 constant 包中
public class AppConstants {
    public static final int DEFAULT_PAGE_SIZE = 20;
    public static final int MAX_BATCH_SIZE = 500;
}

// 第三层：子工程内共享常量
// 第四层：类内私有常量
public class OrderService {
    private static final int RETRY_THRESHOLD = 3;
    private static final long LOCK_TIMEOUT_MS = 5000L;
}
```

### 2.2 枚举替代常量

```java
// ❌ 使用常量表示状态
public static final int STATUS_PENDING = 1;
public static final int STATUS_PROCESSING = 2;
public static final int STATUS_COMPLETED = 3;

// 调用时
if (order.getStatus() == 1) { ... }  // 魔法值，可读性差

// ✅ 使用枚举
public enum OrderStatus {
    PENDING(1, "待处理"),
    PROCESSING(2, "处理中"),
    COMPLETED(3, "已完成");
    
    private final int code;
    private final String description;
    
    OrderStatus(int code, String description) {
        this.code = code;
        this.description = description;
    }
    
    public int getCode() { return code; }
    public String getDescription() { return description; }
    
    public static OrderStatus fromCode(int code) {
        for (OrderStatus status : values()) {
            if (status.code == code) {
                return status;
            }
            }
        throw new IllegalArgumentException("未知状态码: " + code);
    }
}
```

### 2.3 long型字面量

```java
// ❌ 小写 l 容易和数字 1 混淆
long value = 10000l;

// ✅ 使用大写 L
long value = 10000L;
```

---

## 3. 格式规约

### 3.1 代码缩进与换行

```java
// 大括号：K&R 风格（左括号不换行）
public void processOrder(Order order) {
    if (order == null) {
        throw new IllegalArgumentException("订单不能为空");
    }
    
    // 单行不超过120字符，超出需换行
    OrderResult result = orderService.process(order, OrderProcessOptions.builder()
            .withNotification(true)
            .withRetryCount(3)
            .build());
}
```

### 3.2 if语句规范

```java
// ❌ 缺少大括号（即使单行也必须加大括号）
if (order.isValid())
    process(order);

// ✅ 必须使用大括号
if (order.isValid()) {
    process(order);
}

// ❌ 多条件判断时使用魔法值
if (order.getType() == 1) { ... }

// ✅ 提取为有意义的变量或常量
final int TYPE_NORMAL = 1;
if (order.getType() == TYPE_NORMAL) { ... }
```

### 3.3 注释格式

```java
/**
 * 创建订单
 * 
 * @param request 创建订单请求
 * @return 订单创建结果
 * @throws BusinessException 当库存不足时抛出
 */
public OrderResult createOrder(CreateOrderRequest request) {
    // 库存检查：需要同时校验实物库存和预售库存
    int availableStock = stockService.getAvailableStock(request.getSkuId());
    if (availableStock < request.getQuantity()) {
        // 库存不足时记录日志并抛出异常，触发库存预警
        log.warn("库存不足, skuId={}, requested={}, available={}", 
                request.getSkuId(), request.getQuantity(), availableStock);
        throw new BusinessException(StockErrorCode.INSUFFICIENT_STOCK);
    }
    
    // TODO: 2024-01-15 后续需要支持分仓发货
    // FIXME: 并发场景下库存可能超卖，需引入分布式锁
    return orderRepository.save(buildOrder(request));
}
```

---

## 4. OOP规约

### 4.1 包装类使用

```java
// ❌ 使用 == 比较包装类对象
Integer a = 100;
Integer b = 100;
System.out.println(a == b);  // true（缓存范围-128~127内）

Integer c = 200;
Integer d = 200;
System.out.println(c == d);  // false（超出缓存范围）

// ✅ 使用 equals 比较
System.out.println(c.equals(d));  // true

// ❌ POJO类属性使用包装类型，但局部变量使用基本类型
// 数据库字段可能为null，基本类型无法表达null语义

// ✅ POJO类属性必须使用包装类型
public class Order {
    private Long id;
    private Integer status;
    private BigDecimal amount;
    private String orderNo;
}

// ✅ 局部变量使用基本类型
public void process() {
    int count = 0;  // 局部变量用基本类型
    long startTime = System.currentTimeMillis();
}
```

### 4.2 构造方法规约

```java
// ❌ 在构造方法中调用可被覆盖的方法
public class BaseService {
    public BaseService() {
        init();  // 危险！子类构造方法尚未执行
    }
    
    protected void init() { }
}

public class OrderService extends BaseService {
    private OrderRepository repo;
    
    public OrderService(OrderRepository repo) {
        this.repo = repo;
    }
    
    @Override
    protected void init() {
        repo.findAll();  // NPE！此时 repo 还是 null
    }
}

// ✅ 使用工厂方法或初始化方法
public class OrderService {
    private OrderRepository repo;
    
    private OrderService() { }
    
    public static OrderService create(OrderRepository repo) {
        OrderService service = new OrderService();
        service.repo = repo;
        service.init();
        return service;
    }
    
    private void init() {
        repo.findAll();
    }
}
```

### 4.3 equals方法规范

```java
// ❌ 常量在后面可能NPE
if (str.equals("hello")) { }  // str为null时NPE

// ✅ 常量在前面或使用Objects.equals
if ("hello".equals(str)) { }
if (Objects.equals(str, "hello")) { }

// 自定义equals
public class Money {
    private final BigDecimal amount;
    private final String currency;
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Money money = (Money) o;
        return amount.compareTo(money.amount) == 0  // BigDecimal用compareTo
                && currency.equals(money.currency);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }
}
```

---

## 5. 集合处理

### 5.1 集合转Map

```java
// ❌ key重复时会抛异常（Java 8的toMap默认使用抛异常的merge函数）
List<Order> orders = getOrders();
Map<Long, Order> orderMap = orders.stream()
        .collect(Collectors.toMap(Order::getUserId, o -> o));  // userId重复时抛异常

// ✅ 指定merge函数处理冲突
Map<Long, Order> orderMap = orders.stream()
        .collect(Collectors.toMap(
                Order::getUserId, 
                o -> o, 
                (existing, replacement) -> existing  // 保留已存在的
        ));

// ✅ 或者使用groupingBy
Map<Long, List<Order>> orderByUser = orders.stream()
        .collect(Collectors.groupingBy(Order::getUserId));
```

### 5.2 forEach中修改集合

```java
// ❌ 在forEach中使用外部变量
List<String> results = new ArrayList<>();
orders.forEach(order -> {
    results.add(process(order));  // 非线程安全，且可读性差
});

// ✅ 使用流操作
List<String> results = orders.stream()
        .map(this::process)
        .collect(Collectors.toList());

// ❌ 使用Iterator的remove但错误遍历
for (Order order : orders) {
    if (order.isExpired()) {
        orders.remove(order);  // ConcurrentModificationException
    }
}

// ✅ 使用removeIf
orders.removeIf(Order::isExpired);

// ✅ 或使用Iterator
Iterator<Order> iterator = orders.iterator();
while (iterator.hasNext()) {
    if (iterator.next().isExpired()) {
        iterator.remove();
    }
}
```

### 5.3 集合空值处理

```java
// ❌ 返回null
public List<Order> getOrdersByUser(Long userId) {
    if (userId == null) {
        return null;  // 调用方需要判空，容易遗漏
    }
    return orderRepository.findByUserId(userId);
}

// ✅ 返回空集合
public List<Order> getOrdersByUser(Long userId) {
    if (userId == null) {
        return Collections.emptyList();
    }
    return orderRepository.findByUserId(userId);
}

// 判断集合为空
// ❌
if (orders.size() == 0) { }
if (orders.size() < 1) { }

// ✅
if (orders.isEmpty()) { }
if (CollectionUtils.isEmpty(orders)) { }
```

---

## 6. 并发处理

### 6.1 线程池创建

```java
// ❌ 使用Executors创建线程池（队列无界，可能OOM）
ExecutorService executor = Executors.newFixedThreadPool(10);
ExecutorService cachedPool = Executors.newCachedThreadPool();

// ✅ 使用ThreadPoolExecutor，明确参数
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    10,                                          // 核心线程数
    20,                                          // 最大线程数
    60L,                                         // 空闲存活时间
    TimeUnit.SECONDS,                            // 时间单位
    new LinkedBlockingQueue<>(1000),             // 有界队列
    new ThreadFactoryBuilder()
        .setNameFormat("order-pool-%d")
        .build(),                                // 命名线程，便于排查
    new ThreadPoolExecutor.CallerRunsPolicy()    // 拒绝策略：由调用线程执行
);
```

### 6.2 SimpleDateFormat线程安全

```java
// ❌ SimpleDateFormat非线程安全
private static final SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
// 多线程下format/parse会出错

// ✅ 方案1：使用DateTimeFormatter（线程安全）
private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
String formatted = LocalDate.now().format(formatter);

// ✅ 方案2：ThreadLocal
private static final ThreadLocal<SimpleDateFormat> threadLocalSdf = 
    ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));

// ✅ 方案3：每次创建（简单但性能差）
public String formatDate(Date date) {
    return new SimpleDateFormat("yyyy-MM-dd").format(date);
}
```

### 6.3 HashMap并发问题

```java
// ❌ 多线程下HashMap可能导致死循环（JDK7）或数据丢失（JDK8）
private static final Map<String, String> cache = new HashMap<>();

// ✅ 使用ConcurrentHashMap
private static final Map<String, String> cache = new ConcurrentHashMap<>();

// ✅ 双重检查锁
public class Singleton {
    private static volatile Singleton instance;
    
    public static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
// volatile防止指令重排序，避免获取到未完全初始化的对象
```

### 6.4 线程安全集合选用

```java
// CopyOnWriteArrayList：读多写少场景
private final List<EventListener> listeners = new CopyOnWriteArrayList<>();

// ConcurrentHashMap：高并发读写
private final ConcurrentHashMap<String, User> userCache = new ConcurrentHashMap<>();

// AtomicLong：原子计数
private final AtomicLong counter = new AtomicLong(0);
public void increment() {
    counter.incrementAndGet();
}

// LongAdder：高竞争计数（性能优于AtomicLong）
private final LongAdder adder = new LongAdder();
public void increment() {
    adder.increment();
}
```

---

## 7. 异常处理

### 7.1 异常分类与使用

```java
// 异常分类：
// 1. Checked Exception（受检异常）：必须捕获或声明抛出，如 IOException
// 2. RuntimeException（运行时异常）：不强制处理，如 NullPointerException
// 3. Error（错误）：不应捕获，如 OutOfMemoryError

// ❌ 捕获大范围异常
try {
    // 业务逻辑
} catch (Exception e) {
    log.error("发生异常", e);
    // 吞掉异常，不处理也不抛出
}

// ✅ 精确捕获，分类处理
try {
    orderService.process(order);
} catch (InsufficientStockException e) {
    log.warn("库存不足: orderId={}", order.getId(), e);
    throw new BusinessException(StockErrorCode.INSUFFICIENT_STOCK, e);
} catch (PaymentFailedException e) {
    log.error("支付失败: orderId={}", order.getId(), e);
    throw new BusinessException(PaymentErrorCode.PAYMENT_FAILED, e);
} catch (Exception e) {
    log.error("未知异常: orderId={}", order.getId(), e);
    throw new BusinessException(SystemErrorCode.INTERNAL_ERROR, e);
}
```

### 7.2 try-with-resources

```java
// ❌ 手动关闭资源
BufferedReader reader = null;
try {
    reader = new BufferedReader(new FileReader("data.txt"));
    String line;
    while ((line = reader.readLine()) != null) {
        process(line);
    }
} catch (IOException e) {
    log.error("读取文件失败", e);
} finally {
    if (reader != null) {
        try {
            reader.close();
        } catch (IOException e) {
            log.error("关闭reader失败", e);
        }
    }
}

// ✅ try-with-resources
try (BufferedReader reader = new BufferedReader(new FileReader("data.txt"))) {
    String line;
    while ((line = reader.readLine()) != null) {
        process(line);
    }
} catch (IOException e) {
    log.error("读取文件失败", e);
}
```

### 7.3 自定义异常设计

```java
// ✅ 业务异常基类
public class BusinessException extends RuntimeException {
    private final String errorCode;
    private final String errorMessage;
    
    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode.getCode();
        this.errorMessage = errorCode.getMessage();
    }
    
    public BusinessException(ErrorCode errorCode, Throwable cause) {
        super(errorCode.getMessage(), cause);
        this.errorCode = errorCode.getCode();
        this.errorMessage = errorCode.getMessage();
    }
    
    public String getErrorCode() { return errorCode; }
}

// ✅ 错误码枚举
public enum OrderErrorCode implements ErrorCode {
    ORDER_NOT_FOUND("ORDER_001", "订单不存在"),
    ORDER_ALREADY_CANCELLED("ORDER_002", "订单已取消"),
    ORDER_AMOUNT_INVALID("ORDER_003", "订单金额异常");
    
    private final String code;
    private final String message;
    
    OrderErrorCode(String code, String message) {
        this.code = code;
        this.message = message;
    }
    
    @Override
    public String getCode() { return code; }
    @Override
    public String getMessage() { return message; }
}
```

---

## 8. 日志规约

### 8.1 日志框架使用

```java
// ❌ 使用API直接调用日志框架
import org.apache.log4j.Logger;
private static final Logger logger = Logger.getLogger(OrderService.class);

// ✅ 使用SLF4J门面
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
private static final Logger log = LoggerFactory.getLogger(OrderService.class);

// 或使用Lombok
@Slf4j
public class OrderService { }
```

### 8.2 日志级别与占位符

```java
// ❌ 字符串拼接
log.debug("Processing order: " + order.getId() + ", items: " + order.getItems());

// ✅ 占位符
log.debug("Processing order: {}, items: {}", order.getId(), order.getItems());

// ❌ debug日志未判断级别（拼接已执行，浪费性能）
log.debug("Expensive data: " + expensiveOperation());

// ✅ 条件判断
if (log.isDebugEnabled()) {
    log.debug("Expensive data: {}", expensiveOperation());
}

// 日志级别使用规范：
// ERROR：系统异常，影响业务功能，需要立即处理（如数据库连接失败）
// WARN：可预见的异常，系统可自动恢复（如重试成功、限流降级）
// INFO：重要业务操作（如订单创建、支付完成）
// DEBUG：调试信息，生产环境关闭
// TRACE：详细执行流程，开发环境使用
```

### 8.3 异常日志规范

```java
// ❌ 只打印异常消息，丢失堆栈
try {
    orderService.process(order);
} catch (Exception e) {
    log.error("处理订单失败: " + e.getMessage());
    // e.getMessage() 可能为null，且丢失堆栈信息
}

// ✅ 打印完整异常堆栈
try {
    orderService.process(order);
} catch (Exception e) {
    log.error("处理订单失败: orderId={}", order.getId(), e);
    // 注意：异常对象作为最后一个参数，不需要占位符
}
```

---

## 9. MySQL规约

### 9.1 建表规约

```sql
-- ❌ 不规范建表
CREATE TABLE order (
    id int,
    name varchar,
    status int,
    create_time date
);

-- ✅ 规范建表
CREATE TABLE `t_order` (
    `id`          BIGINT       UNSIGNED  NOT NULL  AUTO_INCREMENT  COMMENT '主键ID',
    `order_no`    VARCHAR(32)            NOT NULL                  COMMENT '订单编号',
    `user_id`     BIGINT                 NOT NULL                  COMMENT '用户ID',
    `amount`      DECIMAL(12,2)          NOT NULL  DEFAULT 0.00    COMMENT '订单金额',
    `status`      TINYINT                NOT NULL  DEFAULT 0       COMMENT '状态：0-待支付 1-已支付 2-已取消',
    `created_at`  DATETIME               NOT NULL  DEFAULT CURRENT_TIMESTAMP                 COMMENT '创建时间',
    `updated_at`  DATETIME               NOT NULL  DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  COMMENT '更新时间',
    `is_deleted`  TINYINT                NOT NULL  DEFAULT 0       COMMENT '逻辑删除标识',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_no` (`order_no`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status_created` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';
```

### 9.2 索引规约

```sql
-- ❌ 在区分度低的字段建索引
SELECT * FROM t_order WHERE is_deleted = 0;  -- is_deleted只有0/1，不适合单独建索引

-- ✅ 在区分度高的字段建索引
SELECT * FROM t_order WHERE order_no = 'ORD20240101001';  -- order_no区分度高

-- ❌ 索引失效场景
SELECT * FROM t_order WHERE DATE(created_at) = '2024-01-01';  -- 函数操作导致索引失效
SELECT * FROM t_order WHERE order_no LIKE '%ORD';  -- 前模糊导致索引失效
SELECT * FROM t_order WHERE amount / 2 = 100;  -- 运算操作导致索引失效

-- ✅ 优化写法
SELECT * FROM t_order WHERE created_at >= '2024-01-01' AND created_at < '2024-01-02';
SELECT * FROM t_order WHERE order_no LIKE 'ORD%';
SELECT * FROM t_order WHERE amount = 200;

-- 联合索引遵循最左前缀原则
-- 索引 idx_status_created (status, created_at)
-- ✅ 能命中索引
SELECT * FROM t_order WHERE status = 1;
SELECT * FROM t_order WHERE status = 1 AND created_at > '2024-01-01';
-- ❌ 不能命中索引（跳过了status）
SELECT * FROM t_order WHERE created_at > '2024-01-01';
```

### 9.3 SQL优化要点

```sql
-- ❌ SELECT *
SELECT * FROM t_order WHERE user_id = 100;

-- ✅ 只查需要的字段
SELECT id, order_no, amount, status FROM t_order WHERE user_id = 100;

-- ❌ IN条件过多
SELECT * FROM t_order WHERE id IN (1, 2, 3, ..., 10000);  -- 超过1000个建议分批

-- ❌ 大表使用LIMIT偏移量分页
SELECT * FROM t_order ORDER BY id LIMIT 1000000, 20;  -- 偏移量越大越慢

-- ✅ 游标分页（延迟关联）
SELECT * FROM t_order t
INNER JOIN (SELECT id FROM t_order ORDER BY id LIMIT 1000000, 20) tmp
ON t.id = tmp.id;

-- ✅ 或使用游标
SELECT * FROM t_order WHERE id > 1000000 ORDER BY id LIMIT 20;

-- ❌ count(*) 在大表上很慢（InnoDB需要扫描聚簇索引）
-- ✅ 使用估算值或维护计数表
SELECT COUNT(*) FROM t_order;  -- 慢
SELECT table_rows FROM information_schema.tables WHERE table_name = 't_order';  -- 估算值
```

### 9.4 ORM规约

```java
// ❌ MyBatis中使用${}（SQL注入风险）
@Select("SELECT * FROM t_order WHERE order_no = '${orderNo}'")
Order findByOrderNo(String orderNo);

// ✅ 使用#{}（预编译参数）
@Select("SELECT * FROM t_order WHERE order_no = #{orderNo}")
Order findByOrderNo(String orderNo);

// ❌ 大批量插入
for (Order order : orders) {
    orderMapper.insert(order);  // 逐条插入，性能差
}

// ✅ 批量插入
@Insert("<script>" +
    "INSERT INTO t_order (order_no, user_id, amount) VALUES " +
    "<foreach collection='orders' item='order' separator=','>" +
    "(#{order.orderNo}, #{order.userId}, #{order.amount})" +
    "</foreach>" +
    "</script>")
void batchInsert(@Param("orders") List<Order> orders);
```

---

## 10. 面试题速查

**Q1: 为什么POJO类属性要使用包装类型而不是基本类型？**
> 数据库查询结果可能为null，基本类型无法表达null语义。int默认值为0，无法区分"未设置"和"实际为0"。包装类Integer默认为null，能正确表达数据库的null值。

**Q2: 为什么禁止使用Executors创建线程池？**
- `newFixedThreadPool`和`newSingleThreadExecutor`使用无界队列`LinkedBlockingQueue`，队列长度为Integer.MAX_VALUE，可能堆积大量请求导致OOM。
- `newCachedThreadPool`最大线程数为Integer.MAX_VALUE，可能创建大量线程导致OOM。
- 应使用`ThreadPoolExecutor`明确指定参数。

**Q3: ConcurrentHashMap的size方法是否准确？**
> JDK8中ConcurrentHashMap的size方法是估算值。由于并发统计的复杂性，size方法返回的是一个近似值，在并发修改时可能不完全准确。如果需要精确值，可以使用`mappingCount()`方法。

**Q4: 为什么HashMap在多线程下会死循环？**
> JDK7中HashMap扩容时使用头插法，多线程并发扩容可能导致链表成环，get操作时形成死循环。JDK8改为尾插法解决了死循环问题，但仍非线程安全，多线程下可能出现数据丢失。

**Q5: 联合索引的"最左前缀原则"是什么？**
> 联合索引(a, b, c)相当于创建了(a)、(a,b)、(a,b,c)三个索引。查询条件必须包含最左列a才能使用索引。如果跳过a直接查询b或c，索引无法生效。范围查询（>、<、LIKE）右侧的列索引失效。

**Q6: try-with-resources的原理是什么？**
> 编译器会自动在finally块中调用资源的close()方法。资源对象必须实现AutoCloseable接口。多个资源可以用分号分隔，关闭顺序与声明顺序相反。即使close()方法抛出异常，也会通过addSuppressed附加到主异常上。

**Q7: 为什么推荐使用SLF4J而不是直接使用Log4j/Logback？**
> SLF4J是日志门面（Facade），通过桥接器可以无缝切换底层实现。代码中只依赖SLF4J API，更换日志框架只需修改依赖和配置，不需要改代码。此外SLF4J支持占位符`{}`，避免不必要的字符串拼接。

**Q8: 为什么禁止在foreach循环中对元素进行remove/add操作？**
> foreach底层使用Iterator遍历，同时调用集合的remove/add方法会修改modCount。Iterator的next()方法会检查modCount是否与预期一致（fail-fast机制），不一致则抛出ConcurrentModificationException。应使用Iterator.remove()或Java8的removeIf()。

---

*最后更新：2026-07-13*

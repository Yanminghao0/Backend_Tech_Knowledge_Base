# Spring事务管理

> 深入理解Spring事务抽象、传播行为、隔离级别、失效场景与最佳实践

---

## 📋 目录

1. [事务ACID特性](#1-事务acid特性)
2. [Spring事务抽象](#2-spring事务抽象)
3. [声明式事务](#3-声明式事务)
4. [七种传播行为详解](#4-七种传播行为详解)
5. [四种隔离级别](#5-四种隔离级别)
6. [@Transactional失效场景](#6-transactional失效场景)
7. [编程式事务](#7-编程式事务)
8. [分布式事务概览](#8-分布式事务概览)
9. [最佳实践](#9-最佳实践)
10. [面试题速查](#10-面试题速查)

---

## 1. 事务ACID特性

| 特性 | 全称 | 含义 | 示例 |
|------|------|------|------|
| 原子性 | Atomicity | 事务内操作全部成功或全部回滚 | 转账：扣款+加款必须同时成功 |
| 一致性 | Consistency | 事务前后数据状态一致 | 转账前后总金额不变 |
| 隔离性 | Isolation | 并发事务互不干扰 | 两人同时转账互不影响 |
| 持久性 | Durability | 事务提交后数据永久保存 | 提交后断电不丢失 |

```
转账场景：
  账户A → 转出1000元 → 账户B

  原子性：扣款和加款要么都成功，要么都失败
  一致性：A + B的总金额不变
  隔离性：C同时给A转账，不影响A→B的操作
  持久性：提交后，数据库中数据已持久化
```

---

## 2. Spring事务抽象

### 2.1 核心接口体系

```
Spring事务抽象：
┌─────────────────────────────────────────────────┐
│           PlatformTransactionManager             │ ← 事务管理器接口
│  ├─ getTransaction(TransactionDefinition)        │
│  ├─ commit(TransactionStatus)                    │
│  └─ rollback(TransactionStatus)                  │
└──────────────────┬──────────────────────────────┘
                   │
    ┌──────────────┼──────────────────┐
    ▼              ▼                  ▼
DataSourceTxMgr  JtaTxMgr        JpaTxMgr
(DataSource)     (分布式)        (JPA)

TransactionDefinition（事务定义）         TransactionStatus（事务状态）
├─ isolation: 隔离级别                    ├─ isNewTransaction: 是否新事务
├─ propagation: 传播行为                  ├─ hasSavepoint: 是否有保存点
├─ timeout: 超时时间                       ├─ isRollbackOnly: 是否只回滚
├─ readOnly: 是否只读                      └─ isCompleted: 是否已完成
└─ name: 事务名称
```

### 2.2 事务管理器配置

```java
// Spring Boot自动配置DataSourceTransactionManager
// 只需配置DataSource即可

@Configuration
public class TransactionConfig {

    @Bean
    public PlatformTransactionManager transactionManager(DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
}

// 多数据源场景
@Configuration
public class MultiDataSourceTxConfig {

    @Bean
    public PlatformTransactionManager primaryTxManager(@Qualifier("primaryDataSource") DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }

    @Bean
    public PlatformTransactionManager secondaryTxManager(@Qualifier("secondaryDataSource") DataSource ds) {
        return new DataSourceTransactionManager(ds);
    }
}
```

---

## 3. 声明式事务

### 3.1 @Transactional注解

```java
@Service
public class OrderService {

    @Autowired
    private OrderMapper orderMapper;
    @Autowired
    private AccountService accountService;

    // 基本用法
    @Transactional
    public void createOrder(Order order) {
        orderMapper.insert(order);
        accountService.deduct(order.getUserId(), order.getAmount());
    }

    // 完整参数
    @Transactional(
        propagation = Propagation.REQUIRED,          // 传播行为
        isolation = Isolation.READ_COMMITTED,         // 隔离级别
        timeout = 30,                                  // 超时时间（秒）
        readOnly = false,                              // 是否只读
        rollbackFor = Exception.class,                 // 哪些异常回滚
        noRollbackFor = BusinessException.class,       // 哪些异常不回滚
        transactionManager = "transactionManager"      // 指定事务管理器
    )
    public void updateOrder(Order order) {
        orderMapper.update(order);
    }
}
```

### 3.2 @Transactional注解位置

```java
// ✅ 标在类上：所有public方法都启用事务
@Service
@Transactional
public class OrderService {
    public void createOrder() { ... }    // 有事务
    public void updateOrder() { ... }    // 有事务
}

// ✅ 标在方法上（推荐，更精确）
@Service
public class OrderService {
    @Transactional
    public void createOrder() { ... }    // 有事务

    public void queryOrder() { ... }     // 无事务（查询不需要）
}

// ✅ 方法级覆盖类级
@Service
@Transactional(timeout = 30)
public class OrderService {
    @Transactional(timeout = 60)  // 方法级覆盖类级
    public void batchImport() { ... }

    @Transactional(readOnly = true)  // 只读事务
    public List<Order> list() { ... }
}
```

---

## 4. 七种传播行为详解

### 4.1 传播行为一览

| 传播行为 | 当前有事务 | 当前无事务 | 常用度 |
|----------|-----------|-----------|--------|
| REQUIRED（默认） | 加入当前事务 | 新建事务 | ⭐⭐⭐⭐⭐ |
| REQUIRES_NEW | 挂起当前事务，新建事务 | 新建事务 | ⭐⭐⭐⭐ |
| NESTED | 创建嵌套事务（保存点） | 新建事务 | ⭐⭐⭐ |
| SUPPORTS | 加入当前事务 | 非事务执行 | ⭐⭐ |
| NOT_SUPPORTED | 挂起当前事务，非事务执行 | 非事务执行 | ⭐⭐ |
| MANDATORY | 加入当前事务 | 抛异常 | ⭐ |
| NEVER | 抛异常 | 非事务执行 | ⭐ |

### 4.2 REQUIRED（默认，最常用）

```java
// 场景：方法A调用方法B，B使用REQUIRED
@Service
public class ServiceA {
    @Autowired
    private ServiceB serviceB;

    @Transactional  // 开启事务T1
    public void methodA() {
        // 在事务T1中执行
        serviceB.methodB();
        // 如果B抛异常，A也回滚
    }
}

@Service
public class ServiceB {
    @Transactional(propagation = Propagation.REQUIRED)
    public void methodB() {
        // A有事务 → 加入A的事务T1（不新建）
        // A无事务 → 新建事务
    }
}

// 结果：A和B在同一个事务中，任一失败全部回滚
```

### 4.3 REQUIRES_NEW（独立事务）

```java
// 场景：日志记录不受主事务影响
@Service
public class OrderService {

    @Autowired
    private LogService logService;

    @Transactional  // 事务T1
    public void createOrder(Order order) {
        orderMapper.insert(order);
        logService.recordLog(order);  // 事务T2（独立）
        // 即使T1回滚，T2的日志也保留
    }
}

@Service
public class LogService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordLog(Order order) {
        // 挂起T1，新建独立事务T2
        // T2提交/回滚不影响T1
        logMapper.insert(buildLog(order));
    }
}

// 执行流程：
// 1. 开启T1
// 2. 插入订单（T1）
// 3. 挂起T1 → 开启T2 → 记录日志 → 提交T2 → 恢复T1
// 4. 提交T1
```

### 4.4 NESTED（嵌套事务）

```java
// 场景：批量导入，部分失败不影响整体
@Service
public class ImportService {

    @Transactional  // 事务T1
    public void batchImport(List<UserDTO> list) {
        for (UserDTO dto : list) {
            try {
                importOne(dto);  // 嵌套事务
            } catch (Exception e) {
                log.error("导入失败: {}", dto, e);
                // 单条失败不回滚整体
            }
        }
    }

    @Transactional(propagation = Propagation.NESTED)
    public void importOne(UserDTO dto) {
        // 创建保存点
        // 失败时回滚到保存点，而不是回滚整个T1
        userMapper.insert(dto);
    }
}

// NESTED vs REQUIRES_NEW：
// NESTED：子事务回滚不影响父事务，但父事务回滚会回滚子事务
// REQUIRES_NEW：子事务完全独立，互不影响
```

### 4.5 传播行为决策树

```
当前有事务？
├── 是
│   ├── REQUIRED      → 加入当前事务
│   ├── REQUIRES_NEW  → 挂起当前，新建独立事务
│   ├── NESTED        → 创建保存点，嵌套执行
│   ├── SUPPORTS      → 加入当前事务
│   ├── NOT_SUPPORTED → 挂起当前，非事务执行
│   ├── MANDATORY     → 加入当前事务
│   └── NEVER         → 抛异常
└── 否
    ├── REQUIRED      → 新建事务
    ├── REQUIRES_NEW  → 新建事务
    ├── NESTED        → 新建事务
    ├── SUPPORTS      → 非事务执行
    ├── NOT_SUPPORTED → 非事务执行
    ├── MANDATORY     → 抛异常
    └── NEVER         → 非事务执行
```

---

## 5. 四种隔离级别

### 5.1 隔离级别与问题

| 隔离级别 | 脏读 | 不可重复读 | 幻读 | 性能 |
|----------|------|-----------|------|------|
| READ_UNCOMMITTED | 可能 | 可能 | 可能 | 最高 |
| READ_COMMITTED | 避免 | 可能 | 可能 | 高 |
| REPEATABLE_READ（MySQL默认） | 避免 | 避免 | 可能(InnoDB已避免) | 中 |
| SERIALIZABLE | 避免 | 避免 | 避免 | 最低 |

```
三种并发问题：
┌─────────────────────────────────────────────────────────────┐
│ 脏读：事务A读到了事务B未提交的数据，B回滚后A读到的就是脏数据    │
│   A: 读余额 → 1000                                           │
│   B: 修改余额 → 2000（未提交）                                 │
│   A: 读余额 → 2000 ← 脏读！                                   │
│   B: 回滚 → 余额恢复1000                                      │
├─────────────────────────────────────────────────────────────┤
│ 不可重复读：事务A两次读同一行数据，结果不同（被B修改了）         │
│   A: 读余额 → 1000                                           │
│   B: 修改余额 → 2000（已提交）                                 │
│   A: 读余额 → 2000 ← 不可重复读！                              │
├─────────────────────────────────────────────────────────────┤
│ 幻读：事务A两次范围查询，结果集不同（被B新增/删除了行）          │
│   A: SELECT * WHERE age > 20 → 5行                           │
│   B: INSERT age=25（已提交）                                   │
│   A: SELECT * WHERE age > 20 → 6行 ← 幻读！                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Spring隔离级别配置

```java
@Service
public class OrderService {

    // 读未提交（最低隔离，性能最高）
    @Transactional(isolation = Isolation.READ_UNCOMMITTED)
    public void method1() { ... }

    // 读已提交（Oracle默认）
    @Transactional(isolation = Isolation.READ_COMMITTED)
    public void method2() { ... }

    // 可重复读（MySQL默认，InnoDB通过MVCC+间隙锁解决幻读）
    @Transactional(isolation = Isolation.REPEATABLE_READ)
    public void method3() { ... }

    // 串行化（最高隔离，性能最低）
    @Transactional(isolation = Isolation.SERIALIZABLE)
    public void method4() { ... }

    // 使用数据库默认隔离级别
    @Transactional(isolation = Isolation.DEFAULT)
    public void method5() { ... }
}
```

---

## 6. @Transactional失效场景

### 6.1 经典失效场景汇总

```java
// ❌ 场景1：同类内部方法调用（不走代理）
@Service
public class OrderService {

    public void createOrder(Order order) {
        // 直接this调用，不经过Spring代理
        this.saveOrder(order);  // @Transactional不生效！
    }

    @Transactional
    public void saveOrder(Order order) {
        orderMapper.insert(order);
    }

    // ✅ 解决方案1：注入自身代理
    @Autowired
    @Lazy
    private OrderService self;

    public void createOrder(Order order) {
        self.saveOrder(order);  // 通过代理调用
    }

    // ✅ 解决方案2：AopContext
    public void createOrder(Order order) {
        ((OrderService) AopContext.currentProxy()).saveOrder(order);
    }
}
```

```java
// ❌ 场景2：方法不是public
@Service
public class OrderService {

    @Transactional
    void createOrder(Order order) {  // 包级私有，代理不生效！
        orderMapper.insert(order);
    }

    @Transactional
    private void saveOrder(Order order) {  // private，代理不生效！
        orderMapper.insert(order);
    }
}
```

```java
// ❌ 场景3：异常被catch吞掉
@Service
public class OrderService {

    @Transactional
    public void createOrder(Order order) {
        try {
            orderMapper.insert(order);
            accountService.deduct(order.getUserId(), order.getAmount());
        } catch (Exception e) {
            log.error("下单失败", e);
            // 异常被吞掉，事务无法感知 → 不回滚！
        }
    }

    // ✅ 解决：catch后手动标记回滚，或重新抛出
    @Transactional
    public void createOrder(Order order) {
        try {
            orderMapper.insert(order);
            accountService.deduct(order.getUserId(), order.getAmount());
        } catch (Exception e) {
            log.error("下单失败", e);
            TransactionAspectSupport.currentTransactionStatus()
                .setRollbackOnly();  // 手动标记回滚
        }
    }
}
```

```java
// ❌ 场景4：异常类型不匹配
@Service
public class OrderService {

    // 默认只回滚RuntimeException和Error
    @Transactional
    public void createOrder(Order order) throws Exception {
        orderMapper.insert(order);
        if (order.getStock() < 0) {
            throw new Exception("库存不足");  // 受检异常，不回滚！
        }
    }

    // ✅ 解决：指定rollbackFor
    @Transactional(rollbackFor = Exception.class)
    public void createOrder(Order order) throws Exception {
        orderMapper.insert(order);
        if (order.getStock() < 0) {
            throw new Exception("库存不足");  // 现在会回滚
        }
    }
}
```

```java
// ❌ 场景5：类没有被Spring管理
// 没有@Service/@Component注解的类，不被Spring管理，没有代理
public class OrderService {  // 没有注解！
    @Transactional
    public void createOrder(Order order) {  // 不生效！
        orderMapper.insert(order);
    }
}
```

```java
// ❌ 场景6：数据库引擎不支持事务
// MyISAM引擎不支持事务，需要使用InnoDB
// CREATE TABLE orders (...) ENGINE=InnoDB;
```

### 6.2 失效原因总结

```
@Transactional失效根因分析：
┌──────────────────────────────────────────────────┐
│  根因：AOP代理未生效或不满足事务条件                  │
├──────────────────────────────────────────────────┤
│  1. 同类调用     → 不走代理                        │
│  2. 非public    → 代理只拦截public方法              │
│  3. 异常被吞     → 事务管理器感知不到异常             │
│  4. 异常类型     → 默认只回滚RuntimeException       │
│  5. 未被Spring管理 → 没有代理对象                    │
│  6. 数据库不支持  → MyISAM不支持事务                │
│  7. 传播行为     → NOT_SUPPORTED/SUPPORTS非事务执行 │
│  8. 多线程      → 事务绑定线程，跨线程不共享          │
└──────────────────────────────────────────────────┘
```

---

## 7. 编程式事务

### 7.1 TransactionTemplate（推荐）

```java
@Service
public class OrderService {

    @Autowired
    private TransactionTemplate transactionTemplate;

    public void createOrder(Order order) {
        transactionTemplate.execute(status -> {
            try {
                orderMapper.insert(order);
                accountService.deduct(order.getUserId(), order.getAmount());
                return true;
            } catch (Exception e) {
                status.setRollbackOnly();  // 手动回滚
                return false;
            }
        });
    }

    // 带返回值
    public Order createOrderWithReturn(Order order) {
        return transactionTemplate.execute(status -> {
            orderMapper.insert(order);
            inventoryService.deduct(order.getProductId());
            return order;
        });
    }

    // 自定义隔离级别和传播行为
    public void batchImport(List<Order> orders) {
        transactionTemplate.setIsolationLevel(
            TransactionDefinition.ISOLATION_READ_COMMITTED);
        transactionTemplate.setPropagationBehavior(
            TransactionDefinition.PROPAGATION_REQUIRES_NEW);

        transactionTemplate.execute(status -> {
            for (Order order : orders) {
                orderMapper.insert(order);
            }
            return null;
        });
    }
}
```

### 7.2 PlatformTransactionManager

```java
@Service
public class OrderService {

    @Autowired
    private PlatformTransactionManager txManager;

    public void createOrder(Order order) {
        DefaultTransactionDefinition def = new DefaultTransactionDefinition();
        def.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRED);
        def.setIsolationLevel(TransactionDefinition.ISOLATION_READ_COMMITTED);
        def.setTimeout(30);

        TransactionStatus status = txManager.getTransaction(def);
        try {
            orderMapper.insert(order);
            accountService.deduct(order.getUserId(), order.getAmount());
            txManager.commit(status);
        } catch (Exception e) {
            txManager.rollback(status);
            throw e;
        }
    }
}
```

### 7.3 声明式 vs 编程式

| 维度 | 声明式(@Transactional) | 编程式(TransactionTemplate) |
|------|----------------------|---------------------------|
| 简洁性 | 高（注解即可） | 低（需写模板代码） |
| 灵活性 | 低（粒度固定） | 高（可精确控制范围） |
| 适用场景 | 常规CRUD | 复杂事务控制、批量操作 |
| 性能 | 略低（AOP代理开销） | 略高（直接调用） |

---

## 8. 分布式事务概览

### 8.1 分布式事务方案对比

| 方案 | 一致性 | 性能 | 复杂度 | 适用场景 |
|------|--------|------|--------|----------|
| 2PC（XA） | 强一致 | 低 | 中 | 传统企业应用 |
| 3PC | 强一致 | 低 | 高 | 理论方案，少用 |
| TCC | 强一致 | 中 | 高 | 金融场景 |
| Saga | 最终一致 | 高 | 中 | 长事务 |
| 本地消息表 | 最终一致 | 高 | 低 | 异步场景 |
| MQ事务消息 | 最终一致 | 高 | 中 | 异步场景 |
| Seata AT | 准强一致 | 中 | 低 | 微服务通用 |

### 8.2 Seata示例

```java
// Seata AT模式（最常用，对业务零侵入）
@Service
public class OrderService {

    @Autowired
    private StorageService storageService;  // 远程调用
    @Autowired
    private AccountService accountService;  // 远程调用

    @GlobalTransactional  // Seata全局事务
    public void createOrder(Order order) {
        // 1. 创建订单（本地事务）
        orderMapper.insert(order);

        // 2. 扣减库存（远程事务）
        storageService.deduct(order.getProductId(), order.getCount());

        // 3. 扣减余额（远程事务）
        accountService.debit(order.getUserId(), order.getMoney());

        // 任一步骤失败，全部回滚（自动生成反向SQL）
    }
}
```

---

## 9. 最佳实践

### 9.1 事务使用原则

```java
// 1. 事务范围最小化
// ✅ 好：只包必要操作
@Transactional
public void createOrder(Order order) {
    orderMapper.insert(order);
    accountMapper.deduct(order.getUserId(), order.getAmount());
}

// ❌ 差：包含远程调用、耗时操作（占用事务连接过久）
@Transactional
public void createOrder(Order order) {
    orderMapper.insert(order);
    accountMapper.deduct(order.getUserId(), order.getAmount());
    // 远程调用超时会导致事务长时间挂起
    notifyService.sendNotification(order);  // 不应放在事务内
    generateReport(order);                   // 耗时操作不应放在事务内
}

// 2. 查询方法用只读事务
@Transactional(readOnly = true)
public List<Order> listOrders(Long userId) {
    return orderMapper.selectByUserId(userId);
}

// 3. 指定rollbackFor
@Transactional(rollbackFor = Exception.class)
public void createOrder(Order order) throws Exception { ... }

// 4. 合理使用传播行为
// 核心业务：REQUIRED（默认）
// 日志记录：REQUIRES_NEW（独立事务）
// 批量导入：NESTED（部分失败可回滚到保存点）
```

### 9.2 事务超时配置

```java
// 合理设置超时，避免长事务
@Transactional(timeout = 10)  // 10秒超时
public void createOrder(Order order) { ... }

// 批量操作适当延长
@Transactional(timeout = 60)
public void batchImport(List<User> users) { ... }
```

---

## 10. 面试题速查

**Q1: Spring事务的实现原理？**
```
基于AOP动态代理：
1. Spring为@Transactional标注的类创建代理对象
2. 调用方法时，代理拦截请求
3. TransactionInterceptor开启事务
4. 执行目标方法
5. 正常返回 → commit
6. 抛出异常 → 根据rollbackFor判断是否rollback
```

**Q2: 7种传播行为最常用的是哪些？**
```
REQUIRED（默认）：加入当前事务或新建，适用于大多数场景
REQUIRES_NEW：独立事务，适用于日志记录等不受主事务影响的场景
NESTED：嵌套事务（保存点），适用于批量操作部分失败场景
```

**Q3: @Transactional为什么不建议标注在类上？**
```
1. 所有方法都开启事务，查询方法不需要事务，浪费连接
2. 事务范围过大，影响并发性能
3. 建议标注在需要事务的方法上，查询方法加readOnly=true
```

**Q4: @Transactional失效的根本原因是什么？**
```
AOP代理未生效：
1. 同类内部调用（不走代理）
2. 非public方法（代理不拦截）
3. 异常被catch（代理感知不到）
4. 异常类型不匹配（默认只回滚RuntimeException）
5. 未被Spring管理（没有代理对象）
```

**Q5: REQUIRES_NEW和NESTED的区别？**
```
REQUIRES_NEW：
  - 新建完全独立的事务
  - 子事务提交/回滚不影响父事务
  - 父事务回滚也不影响已提交的子事务

NESTED：
  - 基于保存点的嵌套事务
  - 子事务回滚不影响父事务（回滚到保存点）
  - 但父事务回滚会回滚所有子事务
```

**Q6: 事务和锁的关系？**
```
事务：保证多个操作的原子性（全部成功或全部回滚）
锁：保证并发访问的数据一致性

Spring事务管理的是事务的范围（开始/提交/回滚）
数据库锁由数据库自己管理（行锁/表锁/间隙锁）
事务隔离级别影响锁的行为
```

---

*最后更新：2026-07-13*

# DDD战术设计实战

> 聚合根、值对象、领域事件、领域服务的代码级实现

---

## 📋 目录

1. [战术设计概述](#1-战术设计概述)
2. [实体与值对象](#2-实体与值对象)
3. [聚合与聚合根](#3-聚合与聚合根)
4. [领域服务](#4-领域服务)
5. [领域事件](#5-领域事件)
6. [仓储模式](#6-仓储模式)
7. [限界上下文映射](#7-限界上下文映射)
8. [面试题速查](#8-面试题速查)

---

## 1. 战术设计概述

```
DDD战略设计：限界上下文、子域划分（"做什么"）
DDD战术设计：实体、值对象、聚合、领域服务、领域事件（"怎么做"）

战术设计构件：
  ┌──────────────────────────────────┐
  │           领域层(Domain)           │
  │  ├── 实体(Entity) — 有唯一标识    │
  │  ├── 值对象(Value Object) — 无标识│
  │  ├── 聚合(Aggregate) — 一致性边界  │
  │  ├── 聚合根(Aggregate Root) — 入口 │
  │  ├── 领域服务(Domain Service)      │
  │  ├── 领域事件(Domain Event)        │
  │  └── 仓储(Repository) — 持久化抽象 │
  └──────────────────────────────────┘
```

---

## 2. 实体与值对象

### 2.1 实体（Entity）

```java
// 实体：有唯一标识，即使属性相同也是不同对象
public class Order extends BaseEntity {
    private OrderId id;           // 唯一标识（值对象）
    private CustomerId customerId;
    private List<OrderItem> items;
    private Money totalAmount;
    private OrderStatus status;
    
    // 实体的equals/hashCode基于标识
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Order)) return false;
        Order other = (Order) o;
        return id.equals(other.id);
    }
    
    @Override
    public int hashCode() {
        return id.hashCode();
    }
    
    // 业务行为（不是setter，而是表达业务语义的方法）
    public void confirm() {
        if (status != OrderStatus.CREATED) {
            throw new DomainException("只有待确认订单才能确认");
        }
        this.status = OrderStatus.CONFIRMED;
        DomainEvents.publish(new OrderConfirmedEvent(this.id));
    }
    
    public void addItem(ProductId productId, int quantity, Money price) {
        OrderItem item = new OrderItem(productId, quantity, price);
        this.items.add(item);
        recalculateTotal();
    }
    
    private void recalculateTotal() {
        this.totalAmount = items.stream()
            .map(OrderItem::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }
}
```

### 2.2 值对象（Value Object）

```java
// 值对象：无唯一标识，通过属性判断相等，不可变
public final class Money implements ValueObject {
    private final BigDecimal amount;
    private final Currency currency;
    
    public Money(BigDecimal amount, Currency currency) {
        this.amount = amount.setScale(2, RoundingMode.HALF_UP);
        this.currency = currency;
    }
    
    // 不可变：返回新对象而非修改自身
    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new DomainException("币种不一致");
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
    
    public Money multiply(int quantity) {
        return new Money(this.amount.multiply(BigDecimal.valueOf(quantity)), this.currency);
    }
    
    // 值对象的equals基于属性
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Money)) return false;
        Money money = (Money) o;
        return amount.equals(money.amount) && currency.equals(money.currency);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }
    
    public static final Money ZERO = new Money(BigDecimal.ZERO, Currency.getInstance("CNY"));
}

// 值对象：地址
public final class Address implements ValueObject {
    private final String province;
    private final String city;
    private final String street;
    private final String zipCode;
    // 不可变，equals基于属性
}
```

---

## 3. 聚合与聚合根

```java
// 聚合：一组相关对象的集合，聚合根是唯一外部入口
// 聚合内保证一致性，聚合间通过领域事件保证最终一致性

// Order聚合：Order是聚合根，OrderItem是聚合内实体
public class Order extends BaseEntity {  // 聚合根
    
    private OrderId id;
    private List<OrderItem> items;  // 聚合内实体
    private Money totalAmount;
    private OrderStatus status;
    
    // 外部只能通过聚合根操作聚合内对象
    // 不暴露OrderItem的引用（或只暴露只读视图）
    
    public void changeItemQuantity(OrderItemId itemId, int newQty) {
        OrderItem item = findItem(itemId);
        item.changeQuantity(newQty);  // 通过聚合根委托
        recalculateTotal();
    }
    
    // 聚合内业务规则
    public void submit() {
        if (items.isEmpty()) {
            throw new DomainException("订单至少需要一个商品");
        }
        if (totalAmount.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new DomainException("订单金额必须大于0");
        }
        this.status = OrderStatus.SUBMITTED;
        DomainEvents.publish(new OrderSubmittedEvent(this.id, this.totalAmount));
    }
}

// 聚合设计原则：
// 1. 聚合要小：只包含必须保证强一致性的对象
// 2. 通过ID引用其他聚合：Order引用CustomerId，不直接引用Customer对象
// 3. 一个事务只修改一个聚合：跨聚合用领域事件
// 4. 聚合内所有操作通过聚合根
```

---

## 4. 领域服务

```java
// 领域服务：不属于任何实体的业务逻辑
// 当一个操作涉及多个聚合时，放在领域服务中

@DomainService
public class TransferService {
    
    private final AccountRepository accountRepository;
    
    public void transfer(AccountId fromId, AccountId toId, Money amount) {
        Account from = accountRepository.findById(fromId)
            .orElseThrow(() -> new AccountNotFoundException(fromId));
        Account to = accountRepository.findById(toId)
            .orElseThrow(() -> new AccountNotFoundException(toId));
        
        // 跨聚合操作
        from.withdraw(amount);
        to.deposit(amount);
        
        accountRepository.save(from);
        accountRepository.save(to);
        
        DomainEvents.publish(new MoneyTransferredEvent(fromId, toId, amount));
    }
}

// 注意：领域服务是无状态的，不要把实体的业务逻辑搬到领域服务
// 原则：能放实体的放实体，涉及多聚合的才放领域服务
```

---

## 5. 领域事件

```java
// 领域事件：聚合间通信的解耦机制
public abstract class DomainEvent {
    private final Instant occurredAt;
    private final String eventId;
    
    protected DomainEvent() {
        this.occurredAt = Instant.now();
        this.eventId = UUID.randomUUID().toString();
    }
}

// 具体事件
public class OrderSubmittedEvent extends DomainEvent {
    private final OrderId orderId;
    private final Money totalAmount;
    
    public OrderSubmittedEvent(OrderId orderId, Money totalAmount) {
        super();
        this.orderId = orderId;
        this.totalAmount = totalAmount;
    }
}

// 事件发布（Spring事件机制）
@Component
public class DomainEventPublisher {
    @Autowired
    private ApplicationEventPublisher publisher;
    
    public void publish(DomainEvent event) {
        publisher.publishEvent(event);
    }
}

// 事件处理（跨聚合、跨限界上下文）
@Component
public class OrderEventHandler {
    
    @Autowired
    private InventoryService inventoryService;
    @Autowired
    private PointsService pointsService;
    
    @EventListener
    @Async
    public void onOrderSubmitted(OrderSubmittedEvent event) {
        // 扣减库存（跨聚合）
        inventoryService.deductByOrder(event.getOrderId());
        // 加积分（跨限界上下文）
        pointsService.awardPoints(event.getOrderId(), event.getTotalAmount());
    }
}
```

---

## 6. 仓储模式

```java
// 仓储：聚合持久化的抽象接口，领域层定义，基础设施层实现

// 领域层：接口
public interface OrderRepository {
    Order findById(OrderId id);
    void save(Order order);
    List<Order> findByCustomerId(CustomerId customerId);
}

// 基础设施层：JPA实现
@Repository
public class JpaOrderRepository implements OrderRepository {
    
    @Autowired
    private OrderJpaRepository jpaRepository;
    @Autowired
    private OrderMapper mapper;
    
    @Override
    public Order findById(OrderId id) {
        OrderPO po = jpaRepository.findById(id.getValue())
            .orElseThrow(() -> new OrderNotFoundException(id));
        return mapper.toDomain(po);
    }
    
    @Override
    @Transactional
    public void save(Order order) {
        OrderPO po = mapper.toPO(order);
        jpaRepository.save(po);
    }
}

// 仓储设计原则：
// 1. 一个聚合一个仓储
// 2. 仓储接口在领域层，实现在基础设施层
// 3. 仓储只负责聚合的存取，不含业务逻辑
// 4. 仓储返回的是领域对象（不是PO/DTO）
```

---

## 7. 限界上下文映射

```
限界上下文间的关系模式：

  ┌──────────┐                    ┌──────────┐
  │  订单上下文 │ ── ACL(防腐层) ──→ │  支付上下文 │
  │  Order BC  │                    │ Payment BC │
  └──────────┘                    └──────────┘
       │                               │
       │ 共享内核                       │
       ▼                               ▼
  ┌──────────┐                    ┌──────────┐
  │  库存上下文 │ ← 客户/供应商 ──  │  商品上下文 │
  │Inventory BC│                    │Product BC  │
  └──────────┘                    └──────────┘

映射模式：
  1. 共享内核（Shared Kernel）：两个上下文共享部分模型
  2. 客户/供应商（Customer/Supplier）：下游依赖上游
  3. 防腐层（ACL）：翻译外部模型，隔离变化
  4. 开放主机服务（OHS）：对外提供标准API
  5. 发布语言（PL）：事件/消息的共享Schema
```

---

## 8. 面试题速查

**Q1: 实体和值对象的区别？**
```
实体：有唯一标识，属性可变，equals基于ID
值对象：无标识，不可变，equals基于属性值
示例：Order是实体，Money/Address是值对象
```

**Q2: 聚合根的作用？**
```
1. 聚合的唯一入口：外部只能通过聚合根操作
2. 保证聚合内一致性：聚合内强一致
3. 事务边界：一个事务只修改一个聚合
4. 引用边界：聚合间通过ID引用，不直接引用对象
```

**Q3: 领域服务和应用服务的区别？**
```
领域服务：业务逻辑，无状态，涉及多聚合的领域操作
应用服务：用例编排，事务管理，DTO转换，调用领域服务
领域服务在领域层，应用服务在应用层
```

**Q4: 领域事件解决什么问题？**
```
跨聚合/跨上下文的解耦通信：
1. 聚合A产生事件 → 聚合B监听处理
2. 避免聚合间直接调用
3. 支持最终一致性
4. 支持异步处理
```

---

*最后更新：2026-07-13*

# Sentinel流量控制详解

> 阿里开源流量防卫兵，微服务高可用保障利器

---

## 📋 目录

- [1. Sentinel简介](#1-sentinel简介)
- [2. 核心概念](#2-核心概念)
- [3. 流量控制](#3-流量控制)
- [4. 熔断降级](#4-熔断降级)
- [5. 热点参数限流](#5-热点参数限流)
- [6. 系统自适应保护](#6-系统自适应保护)
- [7. 集群流控](#7-集群流控)
- [8. 网关限流](#8-网关限流)
- [9. 规则持久化](#9-规则持久化)
- [10. 实战案例](#10-实战案例)

---

## 🎯 学习目标

通过本文档，你将掌握：
- ✅ Sentinel核心概念与架构
- ✅ 流量控制策略（QPS、线程数、关联、链路）
- ✅ 熔断降级机制（慢调用、异常比例、异常数）
- ✅ 热点参数限流实战
- ✅ 系统自适应保护
- ✅ 集群流控原理与实现
- ✅ Spring Cloud Gateway集成
- ✅ 规则持久化方案（Nacos、Apollo）
- ✅ 生产环境实战案例

---

## 1. Sentinel简介

### 1.1 什么是Sentinel

**Sentinel** 是阿里巴巴开源的面向分布式服务架构的**流量控制组件**，主要以流量为切入点，从**流量控制、熔断降级、系统负载保护**等多个维度保护服务的稳定性。

**核心定位**：
- 🛡️ **流量防卫兵**：保护系统免受突发流量冲击
- 🔥 **熔断降级**：快速失败，防止雪崩
- ⚡ **实时监控**：秒级监控，快速定位问题
- 🎯 **精准控制**：支持QPS、线程数、慢调用等多维度限流

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| **丰富的应用场景** | 秒杀、消息削峰、集群流控、实时熔断下游不可用应用等 |
| **完备的实时监控** | 实时监控，查看单机秒级数据，甚至500台以下规模的集群汇总运行情况 |
| **广泛的开源生态** | 与Spring Cloud、Dubbo、gRPC无缝整合 |
| **完善的SPI扩展点** | 提供简单易用、完善的SPI扩展接口 |

### 1.3 Sentinel vs Hystrix

| 特性 | Sentinel | Hystrix |
|------|----------|---------|
| **隔离策略** | 信号量隔离 | 线程池隔离/信号量隔离 |
| **熔断降级策略** | 基于慢调用比例、异常比例、异常数 | 基于失败比率 |
| **实时指标** | 滑动窗口（LeapArray） | 滑动窗口（基于RxJava） |
| **规则配置** | 支持多种数据源 | 支持多种数据源 |
| **扩展性** | 多个扩展点 | 插件形式 |
| **限流** | 基于QPS，支持多种流控模式 | 有限的支持 |
| **流量整形** | 支持慢启动、匀速排队 | 不支持 |
| **系统负载保护** | 支持 | 不支持 |
| **控制台** | 功能强大，开箱即用 | 功能简单 |
| **维护状态** | ✅ 活跃维护 | ❌ 已停止维护 |

### 1.4 应用场景

**1. 秒杀场景**
```
正常流量：1000 QPS
秒杀流量：100000 QPS

→ Sentinel限流：5000 QPS
→ 超出部分：快速失败/排队等待
```

**2. 服务降级**
```
订单服务 → 库存服务（慢调用）
         → 积分服务（正常）
         
→ Sentinel熔断库存服务
→ 返回默认值，保证主流程可用
```

**3. 消息削峰**
```
消息队列 → Consumer（限流1000 QPS）
→ 匀速消费，防止下游服务崩溃
```

**4. 系统保护**
```
系统负载：CPU > 80%
→ Sentinel自适应限流
→ 保护系统不被打垮
```

---

## 2. 核心概念

### 2.1 资源（Resource）

**资源**是Sentinel的关键概念，可以是Java中的任何内容：
- 方法
- 代码块
- URL
- RPC接口

**定义资源的方式**：

**1. 注解方式（推荐）**
```java
@Service
public class OrderService {
    
    @SentinelResource(
        value = "createOrder",  // 资源名
        blockHandler = "handleBlock",  // 限流/降级处理
        fallback = "handleFallback"    // 异常处理
    )
    public Order createOrder(Long userId, Long productId) {
        // 业务逻辑
        return orderRepository.save(new Order(userId, productId));
    }
    
    // 限流/降级处理方法
    public Order handleBlock(Long userId, Long productId, BlockException ex) {
        log.warn("createOrder被限流: userId={}, productId={}", userId, productId);
        return Order.FALLBACK_ORDER;
    }
    
    // 异常处理方法
    public Order handleFallback(Long userId, Long productId, Throwable ex) {
        log.error("createOrder异常: userId={}, productId={}", userId, productId, ex);
        return Order.ERROR_ORDER;
    }
}
```

**2. API方式**
```java
// 定义资源
Entry entry = null;
try {
    entry = SphU.entry("resourceName");
    // 业务逻辑
    doSomething();
} catch (BlockException e) {
    // 限流/降级处理
    handleBlock(e);
} finally {
    if (entry != null) {
        entry.exit();
    }
}
```

**3. 自动资源定义（Web、RPC）**
```java
// Spring MVC自动定义
@RestController
public class OrderController {
    @GetMapping("/order/{id}")  // 自动成为资源：GET:/order/{id}
    public Order getOrder(@PathVariable Long id) {
        return orderService.getOrder(id);
    }
}

// Dubbo自动定义
@DubboService  // 接口方法自动成为资源
public class OrderServiceImpl implements OrderService {
    public Order getOrder(Long id) {
        return orderRepository.findById(id);
    }
}
```

### 2.2 规则（Rule）

**规则类型**：

| 规则 | 作用 |
|------|------|
| **FlowRule** | 流量控制规则 |
| **DegradeRule** | 熔断降级规则 |
| **ParamFlowRule** | 热点参数限流规则 |
| **SystemRule** | 系统保护规则 |
| **AuthorityRule** | 访问控制规则 |

**规则配置示例**：
```java
@Configuration
public class SentinelConfig {
    
    @PostConstruct
    public void initRules() {
        // 流量控制规则
        List<FlowRule> flowRules = new ArrayList<>();
        FlowRule rule = new FlowRule();
        rule.setResource("createOrder");
        rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        rule.setCount(100);  // QPS 100
        flowRules.add(rule);
        FlowRuleManager.loadRules(flowRules);
        
        // 熔断降级规则
        List<DegradeRule> degradeRules = new ArrayList<>();
        DegradeRule degradeRule = new DegradeRule();
        degradeRule.setResource("queryInventory");
        degradeRule.setGrade(CircuitBreakerStrategy.SLOW_REQUEST_RATIO.getType());
        degradeRule.setCount(500);  // 响应时间 > 500ms
        degradeRule.setSlowRatioThreshold(0.5);  // 慢调用比例 > 50%
        degradeRule.setTimeWindow(10);  // 熔断持续10秒
        degradeRules.add(degradeRule);
        DegradeRuleManager.loadRules(degradeRules);
    }
}
```

### 2.3 滑动窗口（LeapArray）

**原理**：将时间划分为多个小窗口，统计每个窗口的指标

```
时间窗口：1秒，分为2个小窗口（500ms）

┌─────────────┬─────────────┐
│  Window 1   │  Window 2   │
│  500ms      │  500ms      │
│  QPS: 50    │  QPS: 60    │
└─────────────┴─────────────┘
      ↓             ↓
   总QPS = 110

每500ms滑动一次：
T0-T1: [W1, W2] = 110
T1-T2: [W2, W3] = 120  ← 窗口滑动
```

**LeapArray数据结构**：
```java
public class LeapArray<T> {
    // 窗口时间长度（毫秒）
    protected int windowLengthInMs;
    
    // 采样窗口数量
    protected int sampleCount;
    
    // 总时间间隔（毫秒）= windowLengthInMs * sampleCount
    protected int intervalInMs;
    
    // 采样窗口数组
    protected final AtomicReferenceArray<WindowWrap<T>> array;
    
    // 获取当前窗口
    public WindowWrap<T> currentWindow() {
        return currentWindow(TimeUtil.currentTimeMillis());
    }
}
```

**窗口数据统计**：
```java
public class MetricBucket {
    // 统计数据
    private final LongAdder[] counters;
    
    // 最小RT
    private volatile long minRt;
    
    // 增加通过数量
    public void addPass(int n) {
        add(MetricEvent.PASS, n);
    }
    
    // 增加阻塞数量
    public void addBlock(int n) {
        add(MetricEvent.BLOCK, n);
    }
    
    // 增加异常数量
    public void addException(int n) {
        add(MetricEvent.EXCEPTION, n);
    }
}
```

---

## 3. 流量控制

### 3.1 QPS限流

**场景**：限制每秒请求数

**配置**：
```java
FlowRule rule = new FlowRule();
rule.setResource("createOrder");
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);  // QPS模式
rule.setCount(100);  // 每秒100次
FlowRuleManager.loadRules(Collections.singletonList(rule));
```

**流量效果**：

**1. 快速失败（默认）**
```java
rule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_DEFAULT);

效果：
QPS > 100 → 立即抛出 FlowException
```

**2. Warm Up（预热/冷启动）**
```java
rule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_WARM_UP);
rule.setWarmUpPeriodSec(10);  // 预热时间10秒

效果：
初始QPS = 100 / 3 = 33
10秒后逐渐达到 100 QPS

适用场景：系统启动、定时任务
```

**3. 匀速排队**
```java
rule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_RATE_LIMITER);
rule.setMaxQueueingTimeMs(500);  // 最大排队时间500ms

效果：
固定速度处理请求（令牌桶算法）
QPS=100 → 每10ms处理1个请求
排队超过500ms → 快速失败

适用场景：消息队列消费、批量处理
```

**对比**：

```
请求到达：150 QPS

快速失败：
前100个请求 → 通过
后50个请求  → 拒绝

Warm Up（10秒内）：
T0-T1:  33 QPS通过
T1-T5:  50 QPS通过
T5-T10: 80 QPS通过
T10+:   100 QPS通过

匀速排队：
所有请求均匀处理（100 QPS）
排队超过500ms的请求 → 拒绝
```

### 3.2 线程数限流

**场景**：限制并发线程数（适用于慢调用场景）

**配置**：
```java
FlowRule rule = new FlowRule();
rule.setResource("queryInventory");
rule.setGrade(RuleConstant.FLOW_GRADE_THREAD);  // 线程数模式
rule.setCount(10);  // 最多10个线程
```

**原理**：
```
线程池：100个线程
Sentinel限制：10个线程处理 queryInventory

第1-10个请求  → 通过（10个线程）
第11个请求    → 拒绝（超过限制）
第1个请求完成  → 第11个请求可以进入
```

**QPS vs 线程数**：

| 维度 | QPS限流 | 线程数限流 |
|------|---------|-----------|
| **限制对象** | 每秒请求数 | 并发线程数 |
| **适用场景** | 快速接口 | 慢调用接口 |
| **示例** | 查询缓存（1ms） | 调用第三方API（500ms） |
| **优势** | 精准控制QPS | 防止线程耗尽 |

### 3.3 关联限流

**场景**：关联资源达到阈值时，限流当前资源

**配置**：
```java
FlowRule rule = new FlowRule();
rule.setResource("write");  // 当前资源：写操作
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(100);
rule.setStrategy(RuleConstant.STRATEGY_RELATE);
rule.setRefResource("read");  // 关联资源：读操作

效果：
当 read 的QPS > 100时，限流 write
```

**应用场景**：
```
场景：读多写少的系统

read  QPS: 1000
write QPS: 100

当read压力过大时（QPS > 5000）：
→ 限流write，优先保证read
→ 写请求返回"系统繁忙，请稍后重试"
```

### 3.4 链路限流

**场景**：只针对特定调用链路限流

**配置**：
```java
FlowRule rule = new FlowRule();
rule.setResource("queryProduct");
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(100);
rule.setStrategy(RuleConstant.STRATEGY_CHAIN);
rule.setRefResource("OrderService");  // 只限流从OrderService调用的

效果：
OrderService → queryProduct（限流100）
CartService  → queryProduct（不限流）
```

**调用链路示例**：
```
API网关
  │
  ├── OrderController → queryProduct (限流)
  │
  └── CartController → queryProduct (不限流)
```

**配置文件开启链路限流**：
```yaml
spring:
  cloud:
    sentinel:
      web-context-unify: false  # 关闭context整合
```

---

## 4. 熔断降级

### 4.1 熔断策略

**Sentinel支持3种熔断策略**：

| 策略 | 触发条件 | 场景 |
|------|----------|------|
| **慢调用比例** | 慢调用比例 > 阈值 | 下游服务响应慢 |
| **异常比例** | 异常比例 > 阈值 | 下游服务不稳定 |
| **异常数** | 异常数 > 阈值 | 下游服务偶发异常 |

### 4.2 慢调用比例熔断

**场景**：下游服务响应变慢，触发熔断

**配置**：
```java
DegradeRule rule = new DegradeRule();
rule.setResource("queryInventory");
rule.setGrade(CircuitBreakerStrategy.SLOW_REQUEST_RATIO.getType());
rule.setCount(500);  // RT阈值：500ms
rule.setSlowRatioThreshold(0.5);  // 慢调用比例：50%
rule.setMinRequestAmount(10);  // 最小请求数：10
rule.setStatIntervalMs(1000);  // 统计时长：1秒
rule.setTimeWindow(10);  // 熔断时长：10秒
```

**熔断流程**：
```
1秒内的请求统计：
请求总数：20个
慢调用数（RT>500ms）：12个
慢调用比例：12/20 = 60% > 50%

→ 触发熔断（10秒内拒绝所有请求）
→ 10秒后进入半开状态
→ 放行1个请求探测
   - 成功（RT<500ms）→ 关闭熔断
   - 失败（RT>500ms）→ 再次熔断10秒
```

**状态转换**：
```
┌─────────┐
│  关闭   │ ← 正常状态
│ CLOSED  │
└─────────┘
     │
     │ 慢调用比例 > 50%
     ▼
┌─────────┐
│  打开   │ ← 熔断中（拒绝所有请求）
│  OPEN   │
└─────────┘
     │
     │ 10秒后
     ▼
┌─────────┐
│ 半开    │ ← 探测状态（放行1个请求）
│HALF_OPEN│
└─────────┘
     │
     ├── 成功 → CLOSED
     └── 失败 → OPEN
```

### 4.3 异常比例熔断

**配置**：
```java
DegradeRule rule = new DegradeRule();
rule.setResource("payOrder");
rule.setGrade(CircuitBreakerStrategy.ERROR_RATIO.getType());
rule.setCount(0.5);  // 异常比例：50%
rule.setMinRequestAmount(10);
rule.setStatIntervalMs(1000);
rule.setTimeWindow(10);
```

**触发条件**：
```
1秒内的请求统计：
请求总数：20个
异常数：12个
异常比例：12/20 = 60% > 50%

→ 触发熔断
```

### 4.4 异常数熔断

**配置**：
```java
DegradeRule rule = new DegradeRule();
rule.setResource("sendSMS");
rule.setGrade(CircuitBreakerStrategy.ERROR_COUNT.getType());
rule.setCount(10);  // 异常数：10
rule.setStatIntervalMs(60000);  // 统计时长：60秒
rule.setTimeWindow(10);
```

**触发条件**：
```
60秒内异常数 > 10 → 触发熔断
```

### 4.5 降级处理

**方式1：注解方式**
```java
@SentinelResource(
    value = "queryInventory",
    blockHandler = "handleBlock",  // 限流/熔断处理
    fallback = "handleFallback"    // 异常处理
)
public Integer queryInventory(Long productId) {
    // 调用库存服务
    return inventoryClient.query(productId);
}

// 熔断降级处理
public Integer handleBlock(Long productId, BlockException ex) {
    log.warn("queryInventory被熔断: productId={}", productId);
    return 0;  // 返回默认库存0
}

// 异常处理
public Integer handleFallback(Long productId, Throwable ex) {
    log.error("queryInventory异常: productId={}", productId, ex);
    return 0;
}
```

**方式2：全局降级处理**
```java
@Component
public class GlobalBlockExceptionHandler implements BlockExceptionHandler {
    
    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response, 
                       BlockException e) throws Exception {
        response.setStatus(429);
        response.setContentType("application/json;charset=utf-8");
        
        Map<String, Object> result = new HashMap<>();
        if (e instanceof FlowException) {
            result.put("code", 1001);
            result.put("msg", "系统繁忙，请稍后重试");
        } else if (e instanceof DegradeException) {
            result.put("code", 1002);
            result.put("msg", "服务降级，请稍后重试");
        } else if (e instanceof ParamFlowException) {
            result.put("code", 1003);
            result.put("msg", "热点参数限流");
        }
        
        response.getWriter().write(JSON.toJSONString(result));
    }
}
```

---

## 5. 热点参数限流

### 5.1 基本概念

**热点参数限流**：针对特定参数值进行限流

**场景**：
- 商品ID限流（爆款商品）
- 用户ID限流（刷单用户）
- IP限流（恶意攻击）

### 5.2 配置示例

**基础限流**：
```java
@SentinelResource(
    value = "queryProduct",
    blockHandler = "handleBlock"
)
public Product queryProduct(@RequestParam Long productId) {
    return productService.query(productId);
}

// 配置规则
ParamFlowRule rule = new ParamFlowRule();
rule.setResource("queryProduct");
rule.setParamIdx(0);  // 第0个参数（productId）
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(100);  // 每个productId限流100 QPS
ParamFlowRuleManager.loadRules(Collections.singletonList(rule));
```

**高级限流（特殊参数值）**：
```java
ParamFlowRule rule = new ParamFlowRule();
rule.setResource("queryProduct");
rule.setParamIdx(0);
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(100);  // 默认限流100

// 针对特定商品（爆款商品ID=1001）限流1000
ParamFlowItem item = new ParamFlowItem();
item.setObject("1001");
item.setClassType(Long.class.getName());
item.setCount(1000);

rule.setParamFlowItemList(Collections.singletonList(item));
```

**效果**：
```
productId=1001: 限流1000 QPS（爆款商品）
productId=1002: 限流100 QPS（普通商品）
productId=1003: 限流100 QPS（普通商品）
```

### 5.3 多参数限流

```java
@SentinelResource("placeOrder")
public Order placeOrder(@RequestParam Long userId, 
                        @RequestParam Long productId) {
    return orderService.create(userId, productId);
}

// 针对userId限流
ParamFlowRule rule1 = new ParamFlowRule();
rule1.setResource("placeOrder");
rule1.setParamIdx(0);  // userId
rule1.setCount(10);  // 每个用户限流10 QPS

// 针对productId限流
ParamFlowRule rule2 = new ParamFlowRule();
rule2.setResource("placeOrder");
rule2.setParamIdx(1);  // productId
rule2.setCount(100);  // 每个商品限流100 QPS

ParamFlowRuleManager.loadRules(Arrays.asList(rule1, rule2));
```

---

## 6. 系统自适应保护

### 6.1 系统规则

**Sentinel可以根据系统指标自动限流**：

| 指标 | 说明 |
|------|------|
| **Load** | 系统负载（仅Linux） |
| **CPU使用率** | CPU使用百分比 |
| **平均RT** | 所有入口流量的平均响应时间 |
| **并发线程数** | 所有入口流量的并发线程数 |
| **入口QPS** | 所有入口流量的QPS |

### 6.2 配置示例

**CPU保护**：
```java
SystemRule rule = new SystemRule();
rule.setHighestSystemLoad(3.0);  // Load > 3.0时限流（仅Linux）
rule.setHighestCpuUsage(0.8);    // CPU > 80%时限流
SystemRuleManager.loadRules(Collections.singletonList(rule));
```

**RT保护**：
```java
SystemRule rule = new SystemRule();
rule.setAvgRt(100);  // 平均RT > 100ms时限流
```

**原理**：
```
系统检测（每秒）：
CPU: 85% > 80% → 触发限流
  ↓
计算通过QPS：
maxQPS = currentQPS * (0.8 / 0.85) = currentQPS * 0.94
  ↓
限流部分请求，降低CPU
```

### 6.3 自适应限流算法

**BBR算法（Bottleneck Bandwidth and RTT）**：

```java
// 最大容量（并发数）
maxCapacity = maxQPS * minRt

// 当前容量
currentCapacity = currentThreadCount

// 判断限流
if (currentCapacity >= maxCapacity) {
    // 限流
} else {
    // 通过
}
```

**示例**：
```
系统容量：
maxQPS = 1000
minRt = 10ms
maxCapacity = 1000 * 0.01 = 10（最多10个并发线程）

当前状态：
currentThreadCount = 12 > 10

→ 限流2个请求
```

---

## 7. 集群流控

### 7.1 为什么需要集群流控

**单机限流问题**：

```
场景：秒杀接口限流1000 QPS
部署：10台服务器

单机限流：
每台限流100 QPS
总QPS = 100 * 10 = 1000 QPS

问题：
- 流量不均匀（某台服务器200 QPS，某台50 QPS）
- 实际总QPS可能 < 1000（资源浪费）
- 实际总QPS可能 > 1000（超出预期）
```

**集群流控**：

```
Token Server（集中管理配额）
    ↓
分配Token给各个服务器
    ↓
总QPS精准控制在1000
```

### 7.2 架构设计

**架构模式**：

```
┌─────────────────────────────────────────┐
│          Token Server (Embedded)        │
│        ┌──────────────────────┐         │
│        │   Token管理           │         │
│        │   规则管理             │         │
│        └──────────────────────┘         │
└─────────────────────────────────────────┘
         ▲         ▲         ▲
         │         │         │
    Token请求 Token请求 Token请求
         │         │         │
    ┌────┴────┬────┴────┬────┴────┐
    │ Client1 │ Client2 │ Client3 │
    │ (实例1) │ (实例2) │ (实例3) │
    └─────────┴─────────┴─────────┘
```

### 7.3 配置示例

**Token Server配置**：
```yaml
spring:
  cloud:
    sentinel:
      transport:
        port: 8719
      cluster:
        server:
          port: 18730  # Token Server端口
```

**Token Client配置**：
```yaml
spring:
  cloud:
    sentinel:
      cluster:
        client:
          server-host: 192.168.1.100  # Token Server地址
          server-port: 18730
```

**集群流控规则**：
```java
FlowRule rule = new FlowRule();
rule.setResource("秒杀接口");
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(1000);  // 总QPS 1000
rule.setClusterMode(true);  // 开启集群模式

ClusterFlowConfig config = new ClusterFlowConfig();
config.setThresholdType(ClusterRuleConstant.FLOW_THRESHOLD_GLOBAL);
rule.setClusterConfig(config);
```

### 7.4 Token分配策略

**均匀分配**：
```
总QPS: 1000
实例数: 10
每个实例: 100 QPS
```

**动态分配（根据负载）**：
```
实例1负载: 20% → 分配200 QPS
实例2负载: 15% → 分配150 QPS
实例3负载: 10% → 分配100 QPS
...
```

---

## 8. 网关限流

### 8.1 Spring Cloud Gateway集成

**依赖**：
```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-alibaba-sentinel-gateway</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway</artifactId>
</dependency>
```

**配置**：
```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/order/**
        - id: product-service
          uri: lb://product-service
          predicates:
            - Path=/api/product/**
    sentinel:
      transport:
        dashboard: localhost:8080
      scg:
        fallback:
          mode: response  # 降级响应模式
          response-status: 429
          response-body: '{"code": 429, "msg": "系统繁忙，请稍后重试"}'
```

### 8.2 网关限流规则

**Route维度限流**：
```java
// 针对路由限流
GatewayFlowRule rule = new GatewayFlowRule("order-service");
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(100);  // order-service限流100 QPS
GatewayRuleManager.loadRules(Collections.singletonList(rule));
```

**API分组限流**：
```java
// 定义API分组
ApiDefinition api = new ApiDefinition("order_api");
api.setPredicateItems(new HashSet<ApiPredicateItem>() {{
    add(new ApiPathPredicateItem().setPattern("/api/order/**"));
}});
GatewayApiDefinitionManager.loadApiDefinitions(Collections.singleton(api));

// 针对API分组限流
GatewayFlowRule rule = new GatewayFlowRule("order_api");
rule.setResourceMode(SentinelGatewayConstants.RESOURCE_MODE_CUSTOM_API_NAME);
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(200);
```

**参数限流（IP限流）**：
```java
GatewayFlowRule rule = new GatewayFlowRule("order-service");
rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
rule.setCount(10);  // 每个IP限流10 QPS

GatewayParamFlowItem item = new GatewayParamFlowItem();
item.setParseStrategy(SentinelGatewayConstants.PARAM_PARSE_STRATEGY_CLIENT_IP);
rule.setParamItem(item);
```

### 8.3 自定义降级响应

```java
@Configuration
public class GatewayConfig {
    
    @PostConstruct
    public void initBlockHandlers() {
        BlockRequestHandler blockHandler = (exchange, t) -> {
            Map<String, Object> result = new HashMap<>();
            result.put("code", 429);
            result.put("msg", "系统繁忙，请稍后重试");
            result.put("timestamp", System.currentTimeMillis());
            
            return ServerResponse.status(HttpStatus.TOO_MANY_REQUESTS)
                .contentType(MediaType.APPLICATION_JSON)
                .body(BodyInserters.fromValue(result));
        };
        
        GatewayCallbackManager.setBlockHandler(blockHandler);
    }
}
```

---

## 9. 规则持久化

### 9.1 为什么需要持久化

**问题**：
```
Sentinel规则默认存储在内存中
→ 服务重启后规则丢失
→ 每次重启都需要重新配置
```

**解决方案**：
- Nacos（推荐）
- Apollo
- ZooKeeper
- Redis
- 文件

### 9.2 Nacos持久化

**依赖**：
```xml
<dependency>
    <groupId>com.alibaba.csp</groupId>
    <artifactId>sentinel-datasource-nacos</artifactId>
</dependency>
```

**配置**：
```yaml
spring:
  cloud:
    sentinel:
      datasource:
        # 流控规则
        flow:
          nacos:
            server-addr: 127.0.0.1:8848
            dataId: ${spring.application.name}-flow-rules
            groupId: SENTINEL_GROUP
            rule-type: flow
        # 降级规则
        degrade:
          nacos:
            server-addr: 127.0.0.1:8848
            dataId: ${spring.application.name}-degrade-rules
            groupId: SENTINEL_GROUP
            rule-type: degrade
        # 热点规则
        param-flow:
          nacos:
            server-addr: 127.0.0.1:8848
            dataId: ${spring.application.name}-param-flow-rules
            groupId: SENTINEL_GROUP
            rule-type: param-flow
```

**Nacos规则配置**（JSON格式）：
```json
[
  {
    "resource": "createOrder",
    "limitApp": "default",
    "grade": 1,
    "count": 100,
    "strategy": 0,
    "controlBehavior": 0,
    "clusterMode": false
  }
]
```

### 9.3 动态更新

**Nacos规则修改后自动生效**：
```
Nacos修改规则
    ↓
Sentinel监听配置变化
    ↓
自动更新内存规则
    ↓
新规则立即生效（无需重启）
```

### 9.4 双向同步（控制台 ↔ Nacos）

**问题**：
```
Sentinel控制台修改规则 → 不会写入Nacos
Nacos修改规则 → 控制台不感知
```

**解决**：改造Sentinel控制台

```java
@Component
public class NacosConfigSender implements ConfigurationRepository {
    
    @Autowired
    private ConfigService configService;
    
    @Override
    public void save(List<FlowRuleEntity> rules) {
        try {
            String json = JSON.toJSONString(rules);
            configService.publishConfig(
                "order-service-flow-rules",
                "SENTINEL_GROUP",
                json
            );
        } catch (Exception e) {
            log.error("保存规则到Nacos失败", e);
        }
    }
}
```

---

## 10. 实战案例

### 10.1 秒杀系统限流

**场景**：
```
正常流量：1000 QPS
秒杀流量：100000 QPS
服务器：10台
目标：保护系统，限流5000 QPS
```

**架构**：
```
Nginx (限流10000)
    ↓
Gateway (集群限流5000)
    ↓
Order Service (热点参数限流)
    ↓
Inventory Service (熔断保护)
```

**配置**：

**1. Gateway集群限流**：
```java
// Token Server配置（选择1台服务器）
@Configuration
@ConditionalOnProperty(name = "sentinel.cluster.server.enabled", havingValue = "true")
public class ClusterServerConfig {
    
    @PostConstruct
    public void init() throws Exception {
        // 启动Token Server
        ClusterTokenServer tokenServer = new SentinelDefaultTokenServer();
        tokenServer.start();
        
        // 配置集群规则
        GatewayFlowRule rule = new GatewayFlowRule("秒杀接口");
        rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        rule.setCount(5000);  // 集群总QPS 5000
        rule.setClusterMode(true);
        
        ClusterFlowConfig config = new ClusterFlowConfig();
        config.setThresholdType(ClusterRuleConstant.FLOW_THRESHOLD_GLOBAL);
        rule.setClusterConfig(config);
        
        GatewayRuleManager.loadRules(Collections.singleton(rule));
    }
}
```

**2. 热点参数限流（防刷）**：
```java
@RestController
public class SeckillController {
    
    @SentinelResource(
        value = "seckill",
        blockHandler = "handleBlock"
    )
    @PostMapping("/seckill")
    public Result seckill(@RequestParam Long userId, 
                          @RequestParam Long productId) {
        return seckillService.execute(userId, productId);
    }
    
    public Result handleBlock(Long userId, Long productId, BlockException ex) {
        return Result.fail("手速太快了，请稍后再试");
    }
}

// 规则配置
ParamFlowRule rule1 = new ParamFlowRule();
rule1.setResource("seckill");
rule1.setParamIdx(0);  // userId
rule1.setCount(5);  // 每个用户限流5次/秒（防刷）

ParamFlowRule rule2 = new ParamFlowRule();
rule2.setResource("seckill");
rule2.setParamIdx(1);  // productId
rule2.setCount(1000);  // 每个商品限流1000次/秒
```

**3. 库存服务熔断**：
```java
@Service
public class InventoryService {
    
    @SentinelResource(
        value = "deductInventory",
        blockHandler = "handleBlock",
        fallback = "handleFallback"
    )
    public boolean deduct(Long productId, Integer quantity) {
        // 调用库存服务
        return inventoryClient.deduct(productId, quantity);
    }
    
    public boolean handleBlock(Long productId, Integer quantity, BlockException ex) {
        log.warn("库存服务被熔断: productId={}", productId);
        return false;  // 快速失败
    }
    
    public boolean handleFallback(Long productId, Integer quantity, Throwable ex) {
        log.error("库存服务异常: productId={}", productId, ex);
        return false;
    }
}

// 熔断规则
DegradeRule rule = new DegradeRule();
rule.setResource("deductInventory");
rule.setGrade(CircuitBreakerStrategy.SLOW_REQUEST_RATIO.getType());
rule.setCount(200);  // RT > 200ms
rule.setSlowRatioThreshold(0.5);  // 慢调用比例 > 50%
rule.setMinRequestAmount(10);
rule.setStatIntervalMs(1000);
rule.setTimeWindow(10);  // 熔断10秒
```

**效果**：
```
压测结果：
- 总QPS：5000（精准控制）
- 每个用户QPS：5（防刷成功）
- P99延迟：<50ms
- 成功率：99.9%
- 库存服务熔断：2次（快速恢复）
```

### 10.2 API网关限流

**场景**：
```
API网关：对外提供100+个API
限流策略：
- 普通用户：100 QPS
- VIP用户：1000 QPS
- IP限流：10 QPS
```

**配置**：

**1. API分组**：
```java
// 普通API
ApiDefinition normalApi = new ApiDefinition("normal_api");
normalApi.setPredicateItems(new HashSet<ApiPredicateItem>() {{
    add(new ApiPathPredicateItem().setPattern("/api/normal/**"));
}});

// VIP API
ApiDefinition vipApi = new ApiDefinition("vip_api");
vipApi.setPredicateItems(new HashSet<ApiPredicateItem>() {{
    add(new ApiPathPredicateItem().setPattern("/api/vip/**"));
}});

GatewayApiDefinitionManager.loadApiDefinitions(
    new HashSet<>(Arrays.asList(normalApi, vipApi))
);
```

**2. 限流规则**：
```java
// 普通用户限流
GatewayFlowRule normalRule = new GatewayFlowRule("normal_api");
normalRule.setResourceMode(SentinelGatewayConstants.RESOURCE_MODE_CUSTOM_API_NAME);
normalRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
normalRule.setCount(100);

// VIP用户限流
GatewayFlowRule vipRule = new GatewayFlowRule("vip_api");
vipRule.setResourceMode(SentinelGatewayConstants.RESOURCE_MODE_CUSTOM_API_NAME);
vipRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
vipRule.setCount(1000);

// IP限流
GatewayFlowRule ipRule = new GatewayFlowRule("normal_api");
ipRule.setResourceMode(SentinelGatewayConstants.RESOURCE_MODE_CUSTOM_API_NAME);
ipRule.setGrade(RuleConstant.FLOW_GRADE_QPS);
ipRule.setCount(10);

GatewayParamFlowItem item = new GatewayParamFlowItem();
item.setParseStrategy(SentinelGatewayConstants.PARAM_PARSE_STRATEGY_CLIENT_IP);
ipRule.setParamItem(item);

GatewayRuleManager.loadRules(Arrays.asList(normalRule, vipRule, ipRule));
```

### 10.3 微服务链路保护

**场景**：
```
Order Service
    ↓
Inventory Service (慢)
    ↓
Product Service

当Inventory Service响应变慢时：
→ 熔断Inventory Service
→ 返回默认库存值
→ 保证Order Service可用
```

**配置**：

**1. Inventory Service熔断**：
```java
@FeignClient(
    name = "inventory-service",
    fallback = InventoryFallback.class
)
public interface InventoryClient {
    
    @GetMapping("/inventory/query")
    Integer query(@RequestParam Long productId);
}

@Component
public class InventoryFallback implements InventoryClient {
    
    @Override
    public Integer query(Long productId) {
        log.warn("库存服务降级: productId={}", productId);
        return 0;  // 返回默认库存0
    }
}

// Sentinel熔断规则
DegradeRule rule = new DegradeRule();
rule.setResource("GET:http://inventory-service/inventory/query");
rule.setGrade(CircuitBreakerStrategy.SLOW_REQUEST_RATIO.getType());
rule.setCount(300);
rule.setSlowRatioThreshold(0.5);
rule.setMinRequestAmount(5);
rule.setStatIntervalMs(1000);
rule.setTimeWindow(10);
```

**2. 链路监控**：
```
Sentinel Dashboard → 实时监控
    ↓
发现Inventory Service RT上升
    ↓
自动触发熔断
    ↓
快速失败，调用Fallback
    ↓
保证Order Service可用
```

---

## 🎯 总结

### 核心要点

**流量控制**：
- ✅ QPS限流、线程数限流
- ✅ 快速失败、Warm Up、匀速排队
- ✅ 关联限流、链路限流

**熔断降级**：
- ✅ 慢调用比例、异常比例、异常数
- ✅ CLOSED → OPEN → HALF_OPEN状态转换
- ✅ blockHandler、fallback降级处理

**高级特性**：
- ✅ 热点参数限流（爆款商品、刷单防护）
- ✅ 系统自适应保护（CPU、Load、RT）
- ✅ 集群流控（精准控制总QPS）

**网关集成**：
- ✅ Spring Cloud Gateway集成
- ✅ Route维度、API分组、IP限流
- ✅ 自定义降级响应

**规则持久化**：
- ✅ Nacos动态配置
- ✅ 实时生效，无需重启

### 面试高频

1. **Sentinel vs Hystrix有什么区别**？
   - Sentinel支持更多限流策略（QPS、线程数、慢启动、匀速排队）
   - Sentinel提供实时监控和动态规则配置
   - Hystrix已停止维护，Sentinel是更好的选择

2. **Sentinel如何实现限流**？
   - 滑动窗口统计（LeapArray）
   - 令牌桶算法（匀速排队）
   - 计数器（快速失败）

3. **Sentinel熔断降级的原理**？
   - 慢调用比例、异常比例、异常数三种策略
   - CLOSED → OPEN → HALF_OPEN状态机
   - 探测机制恢复

4. **如何实现Sentinel规则持久化**？
   - Nacos、Apollo、ZooKeeper、Redis
   - 监听配置变化，动态更新规则

5. **集群流控如何工作**？
   - Token Server集中管理配额
   - Token Client请求Token
   - 精准控制集群总QPS

### 最佳实践

1. **限流策略选择**：
   - 快速接口 → QPS限流
   - 慢接口 → 线程数限流
   - 批量处理 → 匀速排队

2. **熔断配置**：
   - 慢调用阈值：P99延迟的2倍
   - 慢调用比例：50%
   - 熔断时长：10-30秒

3. **规则持久化**：
   - 使用Nacos（推荐）
   - 双向同步（控制台 ↔ Nacos）

4. **监控告警**：
   - Sentinel Dashboard实时监控
   - Prometheus + Grafana可视化
   - 熔断事件告警

5. **降级处理**：
   - 返回默认值
   - 返回缓存数据
   - 友好的错误提示

---

*最后更新：2025-10-27*  
*文档状态：v1.0 完成*  
*作者：技术知识库团队*

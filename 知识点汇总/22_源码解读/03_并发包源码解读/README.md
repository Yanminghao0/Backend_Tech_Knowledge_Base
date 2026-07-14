# 并发包源码解读

> JUC（java.util.concurrent）并发包核心源码深度解析，Java并发编程的基石

---

## 📚 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| [AQS源码解析](./3.1_AQS源码解析.md) | 同步状态state、CLH队列、独占/共享模式 | ⭐⭐⭐⭐⭐ | ✅ |
| [ReentrantLock源码解析](./3.2_ReentrantLock源码解析.md) | 公平锁/非公平锁、可重入、Condition条件变量 | ⭐⭐⭐⭐⭐ | ✅ |
| [ThreadPoolExecutor源码解析](./3.3_ThreadPoolExecutor源码解析.md) | 核心参数、Worker线程、任务队列、拒绝策略 | ⭐⭐⭐⭐⭐ | ✅ |
| [ConcurrentHashMap源码解析](./3.4_ConcurrentHashMap源码解析.md) | CAS+synchronized、分段锁演进、扩容迁移 | ⭐⭐⭐⭐⭐ | ✅ |
| [CountDownLatch源码解析](./3.5_CountDownLatch源码解析.md) | 倒计时门闩、AQS共享模式、一次性使用 | ⭐⭐⭐⭐ | ✅ |
| [CyclicBarrier源码解析](./3.6_CyclicBarrier源码解析.md) | 循环栅栏、ReentrantLock实现、可重用 | ⭐⭐⭐⭐ | ✅ |
| [Semaphore源码解析](./3.7_Semaphore源码解析.md) | 信号量、AQS共享模式、限流应用 | ⭐⭐⭐⭐ | ✅ |
| [ReentrantReadWriteLock源码解析](./3.8_ReentrantReadWriteLock源码解析.md) | 读写锁、锁降级、公平性、高16位读/低16位写 | ⭐⭐⭐⭐⭐ | ✅ |
| [AtomicInteger源码解析](./3.9_AtomicInteger源码解析.md) | CAS、Unsafe、ABA问题、原子操作 | ⭐⭐⭐⭐⭐ | ✅ |
| [BlockingQueue源码解析](./3.10_BlockingQueue源码解析.md) | 阻塞队列、生产者消费者、Condition实现 | ⭐⭐⭐⭐⭐ | ✅ |
| [CompletableFuture源码解析](./3.11_CompletableFuture源码解析.md) | 异步编程、链式组合、异常处理、CompletionStage | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习目标

1. **掌握AQS框架**：理解Java并发的基石——CLH队列、state同步状态、独占/共享模式
2. **深入锁实现**：ReentrantLock公平/非公平、ReentrantReadWriteLock读写分离
3. **理解并发容器**：ConcurrentHashMap从分段锁到CAS+synchronized的演进
4. **掌握线程池原理**：ThreadPoolExecutor核心参数、Worker线程模型、任务调度流程
3. **异步编程模型**：CompletableFuture的CompletionStage链式组合
6. **同步工具类**：CountDownLatch/CyclicBarrier/Semaphore的原理与使用场景

---

## 📊 JUC核心组件架构

```
java.util.concurrent
├── 锁框架
│   ├── AQS (AbstractQueuedSynchronizer) — 并发基石
│   │   ├── ReentrantLock        — 可重入独占锁
│   │   ├── ReentrantReadWriteLock — 读写锁
│   │   ├── Semaphore            — 信号量
│   │   ├── CountDownLatch       — 倒计时门闩
│   │   └── CyclicBarrier        — 循环栅栏
│   └── LockSupport              — 线程阻塞/唤醒
├── 原子类
│   ├── AtomicInteger/AtomicLong — CAS原子操作
│   ├── LongAdder/LongAccumulator — 分段累加
│   └── AtomicReference          — 引用原子更新
├── 并发容器
│   ├── ConcurrentHashMap        — 并发哈希表
│   ├── CopyOnWriteArrayList     — 写时复制
│   ├── ConcurrentLinkedQueue    — 无锁并发队列
│   └── BlockingQueue系列        — 阻塞队列
│   ├── ArrayBlockingQueue
│   ├── LinkedBlockingQueue
│   ├── SynchronousQueue
│   └── DelayQueue
├── 线程池
│   ├── ThreadPoolExecutor       — 核心线程池
│   ├── ScheduledThreadPoolExecutor — 定时任务
│   └── ForkJoinPool             — 分治线程池
└── 异步编程
    ├── CompletableFuture        — 异步编排
    └── FutureTask               — 异步任务
```

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- AQS的核心原理？CLH队列如何工作？state的作用？
- ReentrantLock和synchronized区别？公平锁vs非公平锁？
- ConcurrentHashMap如何保证线程安全？（JDK7分段锁 vs JDK8 CAS+sync）
- 线程池核心参数？任务执行流程？拒绝策略有哪些？
- CAS原理？ABA问题如何解决？

⭐⭐⭐⭐ 高频：
- 读写锁的读写分离原理？锁降级？
- CountDownLatch vs CyclicBarrier区别？
- Semaphore的使用场景？如何实现限流？
- 线程池如何合理配置参数？（CPU密集 vs IO密集）
- CompletableFuture vs Future？链式编排？
- BlockingQueue的实现类对比？
- 为什么阿里巴巴不推荐使用Executors创建线程池？
```

---

## 📈 推荐阅读顺序

```
1. AQS               — 并发包基石，先理解CLH队列和state
      ↓
2. ReentrantLock     — 基于AQS的独占锁实现
      ↓
3. ReentrantReadWriteLock — 读写锁，AQS共享模式
      ↓
4. AtomicInteger     — CAS原子操作基础
      ↓
3. ConcurrentHashMap — 并发容器核心
      ↓
6. ThreadPoolExecutor — 线程池原理
      ↓
7. BlockingQueue     — 阻塞队列，生产者消费者
      ↓
8. CountDownLatch/Semaphore/CyclicBarrier — 同步工具三件套
      ↓
9. CompletableFuture — 异步编程
```

---

*最后更新：2026-07-13*

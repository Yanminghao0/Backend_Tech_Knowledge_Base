# 并发包源码解读

> JUC（java.util.concurrent）并发包核心源码深度解析

## 📚 目录

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| [AQS源码解析](./5.1_AQS源码解析.md) | 同步状态、CLH队列、独占/共享模式 | ⭐⭐⭐⭐⭐ | ✅ |
| [ReentrantLock源码解析](./5.2_ReentrantLock源码解析.md) | 公平锁/非公平锁、可重入、Condition | ⭐⭐⭐⭐⭐ | ✅ |
| [ConcurrentHashMap源码解析](./5.4_ConcurrentHashMap源码解析.md) | CAS、synchronized、扩容机制 | ⭐⭐⭐⭐⭐ | ✅ |
| [ThreadPoolExecutor源码解析](./5.3_ThreadPoolExecutor源码解析.md) | 核心参数、Worker线程、拒绝策略 | ⭐⭐⭐⭐⭐ | ✅ |
| [CompletableFuture源码解析](./5.11_CompletableFuture源码解析.md) | 异步编程、组合操作、异常处理 | ⭐⭐⭐⭐ | ✅ |
| [CountDownLatch源码解析](./5.5_CountDownLatch源码解析.md) | 倒计时门闩、AQS共享模式 | ⭐⭐⭐⭐ | ✅ |
| [Semaphore源码解析](./5.7_Semaphore源码解析.md) | 信号量、限流、资源池 | ⭐⭐⭐⭐ | ✅ |
| [CyclicBarrier源码解析](./5.6_CyclicBarrier源码解析.md) | 循环栅栏、多线程同步、可重用 | ⭐⭐⭐⭐ | ✅ |
| [ReentrantReadWriteLock源码解析](./5.8_ReentrantReadWriteLock源码解析.md) | 读写锁、锁降级、公平性 | ⭐⭐⭐⭐⭐ | ✅ |
| [AtomicInteger源码解析](./5.9_AtomicInteger源码解析.md) | CAS、Unsafe、原子操作 | ⭐⭐⭐⭐⭐ | ✅ |
| [BlockingQueue源码解析](./5.10_BlockingQueue源码解析.md) | 阻塞队列、生产者消费者 | ⭐⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习目标

1. **理解AQS框架**：掌握Java并发的基石
2. **掌握锁实现原理**：ReentrantLock、读写锁
3. **理解并发容器**：ConcurrentHashMap的演进
4. **掌握线程池原理**：任务调度、线程复用
5. **异步编程模型**：CompletableFuture实战
6. **同步工具类**：CountDownLatch、Semaphore、CyclicBarrier

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- AQS的核心原理？CLH队列？
- ReentrantLock和synchronized区别？
- ConcurrentHashMap如何保证线程安全？
- 线程池核心参数？执行流程？
- 为什么用CAS而不是锁？

⭐⭐⭐⭐ 高频：
- 公平锁和非公平锁区别？
- ConcurrentHashMap的size()如何实现？
- 线程池的拒绝策略？
- CompletableFuture vs Future？
- CountDownLatch vs CyclicBarrier？
- Semaphore的使用场景？
```

---

*最后更新：2025-12-28*

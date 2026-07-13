# JVM源码解读

> JVM核心组件源码解析：类加载、GC算法、JIT编译器、内存模型、锁优化

---

## 📋 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 19.1_ClassLoader源码解析.md | 双亲委派、WebappClassLoader、线程上下文类加载器 | ⭐⭐⭐⭐ | 📄 待补充 |
| 19.2_GC算法源码解析.md | 分代收集、G1Region、ZGC染色指针、并发标记 | ⭐⭐⭐⭐⭐ | 📄 待补充 |
| 19.3_JIT编译器源码解析.md | C1/C2编译器、热点探测、逃逸分析、内联优化 | ⭐⭐⭐⭐ | 📄 待补充 |
| 19.4_内存模型源码解析.md | JMM、内存屏障、happens-before、Cache Line | ⭐⭐⭐⭐⭐ | 📄 待补充 |
| 19.5_synchronized源码解析.md | 对象头Mark Word、偏向锁→轻量级锁→重量级锁升级 | ⭐⭐⭐⭐⭐ | 📄 待补充 |
| 19.6_volatile源码解析.md | 内存屏障实现、可见性保证、禁止重排序、DCL应用 | ⭐⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **掌握GC实现**：G1的Region划分、SATB标记、Mixed GC、ZGC的染色指针
2. **理解JIT优化**：方法内联、逃逸分析、锁消除、循环展开
3. **深入锁实现**：synchronized的锁升级全过程、Lock Record、ObjectMonitor
4. **理解JMM**：happens-before规则、StoreLoad/StoreStore/LoadLoad/LoadStore屏障

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- synchronized的锁升级过程？偏向锁→轻量级锁→重量级锁
- volatile的两层语义？为什么不能保证原子性？
- G1 GC的工作原理？和CMS的区别？
- JMM的happens-before规则？
- 什么是逃逸分析？栈上分配？

⭐⭐⭐⭐ 高频：
- 双亲委派模型及打破场景（SPI/Tomcat/热部署）
- JIT的C1和C2编译器区别？
- ZGC为什么能做到<1ms停顿？
- 内存屏障的四种类型？
```

---

## 📈 推荐阅读顺序

```
1. ClassLoader     — 理解类加载机制（基础）
      ↓
2. 内存模型        — 理解JMM和happens-before
      ↓
3. volatile        — 理解内存屏障和可见性
      ↓
4. synchronized    — 理解锁升级（对象头Mark Word）
      ↓
5. GC算法          — 理解G1/ZGC实现
      ↓
6. JIT编译器       — 理解即时编译优化
```

---

*最后更新：2026-07-13*

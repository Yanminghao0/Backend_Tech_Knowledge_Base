# 数据访问层源码解读

> 深入理解数据库连接池和分库分表中间件的实现原理

---

## 📚 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| [HikariCP源码解析](./6.1_HikariCP源码解析.md) | 连接池管理、ConcurrentBag、FastList、连接泄漏检测 | ⭐⭐⭐⭐⭐ | ✅ |
| Druid源码解析 | 阿里连接池、SQL解析、监控统计、WallFilter | ⭐⭐⭐⭐ | 📄 待补充 |
| ShardingSphere源码解析 | 分库分表路由、SQL解析改写、读写分离 | ⭐⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **理解连接池原理**：连接的获取、归还、验证、泄漏检测机制
2. **掌握HikariCP优势**：为什么HikariCP是最快的连接池（ConcurrentBag、FastList、无锁设计）
3. **对比连接池实现**：HikariCP vs Druid vs C3P0的设计差异
4. **理解分库分表**：ShardingSphere的SQL路由、改写、归并原理

---

## 📊 连接池对比

| 特性 | HikariCP | Druid | C3P0 | Tomcat JDBC |
|------|----------|-------|------|-------------|
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| 监控 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| SQL防火墙 | ❌ | ✅ WallFilter | ❌ | ❌ |
| 慢SQL记录 | ❌ | ✅ | ❌ | ✅ |
| 代码量 | ~130KB | ~2MB | ~600KB | ~300KB |
| Spring Boot默认 | ✅ | ❌ | ❌ | ❌ |
| 核心设计 | ConcurrentBag | 生产消费队列 | 同步锁 | 阻塞队列 |

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- 连接池的工作原理？连接如何复用？
- HikariCP为什么性能最好？（ConcurrentBag无锁、FastList优化、字节码优化）
- 连接泄漏如何检测？（leakDetectionThreshold）
- 连接池如何合理配置参数？（maxPoolSize、minIdle、connectionTimeout）

⭐⭐⭐⭐ 高频：
- Druid和HikariCP的选型考虑？
- 连接池的连接验证机制？（isValid、connectionTestQuery）
- 如何选择分库分表中间件？（ShardingSphere vs MyCat）
- 读写分离如何实现？
```

---

## 📈 推荐阅读顺序

```
1. HikariCP源码解析 — 理解高性能连接池设计
      ↓
2. Druid源码解析（待补充）— 对比监控能力
      ↓
3. ShardingSphere源码解析（待补充）— 分库分表路由
```

---

*最后更新：2026-07-13*

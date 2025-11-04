# MyBatis源码解读

> 💡 深入理解MyBatis ORM框架核心原理，从SQL执行到缓存机制的完整源码分析

---

## 📚 目录结构

```
MyBatis源码解读/
├── README.md                    # 本文档
├── SqlSession源码解析.md        # SqlSession核心原理 ✅
├── Mapper代理源码解析.md        # Mapper动态代理机制 ✅
├── 一二级缓存源码解析.md        # 缓存体系详解 ✅
└── 插件机制源码解析.md          # 插件拦截器原理 📄 待完成
```

---

## 🎯 学习目标

### 核心问题
1. MyBatis是如何执行SQL的？
2. Mapper接口没有实现类，是如何工作的？
3. 一级缓存和二级缓存的区别是什么？
4. MyBatis插件是如何实现的？
5. SqlSession是线程安全的吗？

### 面试高频问题
- ⭐⭐⭐⭐⭐ Mapper接口工作原理
- ⭐⭐⭐⭐⭐ 一级缓存与二级缓存
- ⭐⭐⭐⭐⭐ #{}和${}的区别
- ⭐⭐⭐⭐ 插件机制原理
- ⭐⭐⭐⭐ 延迟加载原理

---

## 📖 核心内容

### 1️⃣ SqlSession源码解析 ✅
📄 [SqlSession源码解析.md](./SqlSession源码解析.md)

**核心内容**：
- ✅ SqlSessionFactory创建过程
- ✅ DefaultSqlSession实现原理
- ✅ Executor执行器体系
- ✅ 事务管理机制
- ✅ 一级缓存作用域

**核心类**：
```
SqlSessionFactory          # 会话工厂
SqlSession                 # 会话接口
DefaultSqlSession          # 默认实现
Executor                   # 执行器接口
SimpleExecutor             # 简单执行器
ReuseExecutor              # 复用执行器
BatchExecutor              # 批量执行器
```

### 2️⃣ Mapper代理源码解析 ✅
📄 [Mapper代理源码解析.md](./Mapper代理源码解析.md)

**核心内容**：
- ✅ MapperRegistry注册机制
- ✅ MapperProxyFactory代理工厂
- ✅ MapperProxy动态代理
- ✅ MapperMethod方法执行
- ✅ 参数解析与结果映射

**核心类**：
```
MapperRegistry             # Mapper注册表
MapperProxyFactory         # 代理工厂
MapperProxy                # 代理类
MapperMethod               # 方法封装
SqlCommand                 # SQL命令
MethodSignature            # 方法签名
```

### 3️⃣ 一二级缓存源码解析 ✅
📄 [一二级缓存源码解析.md](./一二级缓存源码解析.md)

**核心内容**：
- ✅ 一级缓存（本地缓存）原理
- ✅ 二级缓存（全局缓存）原理
- ✅ 缓存Key生成策略
- ✅ 缓存失效机制
- ✅ 分布式环境缓存问题

**核心类**：
```
Cache                      # 缓存接口
PerpetualCache             # 永久缓存
LruCache                   # LRU缓存
TransactionalCache         # 事务缓存
CacheKey                   # 缓存键
CachingExecutor            # 缓存执行器
```

### 4️⃣ 插件机制源码解析 📄
📄 [插件机制源码解析.md](./插件机制源码解析.md) - 待完成

**核心内容**：
- 📄 Interceptor接口设计
- 📄 责任链模式应用
- 📄 插件开发实战
- 📄 分页插件原理

**核心类**：
```
Interceptor                # 拦截器接口
InterceptorChain           # 拦截器链
Plugin                     # 插件代理
Invocation                 # 调用封装
```

---

## 🚀 学习路径

### 阶段1：SqlSession（2-3天）
```
学习顺序：
1. SqlSessionFactory创建
2. Configuration配置解析
3. DefaultSqlSession实现
4. Executor执行器体系
5. 事务管理机制

重点掌握：
- SQL执行完整流程
- 执行器类型选择
- 一级缓存作用域
```

### 阶段2：Mapper代理（2-3天）
```
学习顺序：
1. MapperRegistry注册
2. MapperProxyFactory创建
3. MapperProxy代理调用
4. MapperMethod执行
5. 参数解析与结果映射

重点掌握：
- 动态代理实现原理
- 接口方法如何执行SQL
- 参数和结果处理
```

### 阶段3：缓存机制（2-3天）
```
学习顺序：
1. 一级缓存实现
2. 二级缓存实现
3. CacheKey生成
4. 缓存失效场景
5. 分布式缓存问题

重点掌握：
- 缓存作用域区别
- 缓存失效条件
- 生产环境最佳实践
```

### 阶段4：插件机制（1-2天）
```
学习顺序：
1. Interceptor接口
2. 责任链模式
3. 插件代理生成
4. 自定义插件开发

重点掌握：
- 插件拦截点
- 分页插件原理
- 自定义插件开发
```

---

## 💡 核心知识点速查

### MyBatis架构
```
┌─────────────────────────────────────────┐
│              SqlSession                  │
├─────────────────────────────────────────┤
│              Executor                    │
│  ┌─────────┬─────────┬─────────┐       │
│  │ Simple  │  Reuse  │  Batch  │       │
│  └─────────┴─────────┴─────────┘       │
├─────────────────────────────────────────┤
│           StatementHandler               │
├─────────────────────────────────────────┤
│           ParameterHandler               │
├─────────────────────────────────────────┤
│            ResultSetHandler              │
├─────────────────────────────────────────┤
│              TypeHandler                 │
└─────────────────────────────────────────┘
```

### SQL执行流程
```
1. SqlSession.selectList()
   ↓
2. Executor.query()
   ↓
3. 查询一级缓存
   ↓ (未命中)
4. 查询二级缓存
   ↓ (未命中)
5. StatementHandler.query()
   ↓
6. ParameterHandler.setParameters()
   ↓
7. JDBC执行SQL
   ↓
8. ResultSetHandler.handleResultSets()
   ↓
9. 结果放入缓存
   ↓
10. 返回结果
```

### 一级缓存 vs 二级缓存
```
┌────────────────┬─────────────────┬─────────────────┐
│     特性       │    一级缓存      │    二级缓存      │
├────────────────┼─────────────────┼─────────────────┤
│ 作用域         │ SqlSession      │ Mapper/namespace│
│ 默认开启       │ 是              │ 否              │
│ 生命周期       │ 会话级别        │ 应用级别        │
│ 存储位置       │ 内存            │ 内存/磁盘       │
│ 线程安全       │ 否              │ 是              │
│ 失效条件       │ 增删改/close    │ 增删改          │
└────────────────┴─────────────────┴─────────────────┘
```

### 插件拦截点
```java
// 可拦截的四大对象
Executor           // 执行器（增删改查、事务）
StatementHandler   // SQL语句处理器
ParameterHandler   // 参数处理器
ResultSetHandler   // 结果集处理器

// 常见插件应用
- 分页插件：拦截Executor.query()
- SQL打印：拦截StatementHandler.prepare()
- 数据权限：拦截Executor.query()
- 性能监控：拦截Executor所有方法
```

---

## 📚 参考资料

### 推荐书籍
- 📘 《MyBatis技术内幕》- 徐郡明
- 📘 《MyBatis从入门到精通》- 刘增辉

### 在线资源
- 🌐 [MyBatis官方文档](https://mybatis.org/mybatis-3/zh/)
- 🌐 [MyBatis源码](https://github.com/mybatis/mybatis-3)

---

**深入MyBatis源码，掌握ORM框架精髓！** 🚀

*最后更新：2025-12-28*

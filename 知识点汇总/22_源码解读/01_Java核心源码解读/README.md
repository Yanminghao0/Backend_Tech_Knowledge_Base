# Java核心源码解读

> Java基础核心类的源码解析入口，涵盖Object、String、Thread、ClassLoader等

---

## 📋 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| 3.1_Object源码解析.md | equals/hashCode/clone/notify/wait/finalize | ⭐⭐⭐⭐ | 📄 待补充 |
| 3.2_String源码解析.md | 不可变性、字符串常量池、StringBuilder对比 | ⭐⭐⭐⭐ | 📄 待补充 |
| 3.3_Thread源码解析.md | 线程生命周期、sleep/yield/join/wait、中断机制 | ⭐⭐⭐⭐ | 📄 待补充 |
| 3.4_ClassLoader源码解析.md | 双亲委派、URLClassLoader、自定义类加载器 | ⭐⭐⭐⭐ | 📄 待补充 |
| 3.5_异常体系源码解析.md | Throwable体系、Checked vs Unchecked、异常表 | ⭐⭐⭐ | 📄 待补充 |
| 3.6_注解机制源码解析.md | Annotation接口、RetentionPolicy、反射读取 | ⭐⭐⭐ | 📄 待补充 |

---

## 🎯 学习目标

1. **理解Object设计**：为什么equals和hashCode必须一起重写
2. **掌握String不可变性**：字符串常量池、编译期优化
3. **理解线程机制**：Thread的状态转换、中断协作机制
4. **掌握类加载**：双亲委派模型及打破方式

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- equals和hashCode的关系？为什么必须一起重写？
- String为什么不可变？String常量池原理？
- new String("abc")创建了几个对象？
- Thread的start()和run()区别？

⭐⭐⭐⭐ 高频：
- wait/notify/notifyAll的使用场景？
- 双亲委派模型？为什么要打破？
- 异常处理的最佳实践？
```

---

## 📈 与其他目录的关系

```
03_Java核心源码 → 基础类（Object/String/Thread/ClassLoader）
04_集合框架源码 → 容器类（HashMap/ArrayList/...）
05_并发包源码  → JUC并发类（AQS/线程池/锁/...）
```

---

*最后更新：2026-07-13*

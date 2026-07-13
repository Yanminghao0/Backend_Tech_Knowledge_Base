# Java核心源码解读

> Java基础核心类的源码解析入口，涵盖Object、String、Thread、ClassLoader、异常体系、注解机制等

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

1. **理解Object设计**：为什么equals和hashCode必须一起重写，clone的浅拷贝陷阱，finalize为什么被废弃
2. **掌握String不可变性**：字符串常量池、编译期优化、StringBuilder/StringBuffer的扩容机制（`int newCapacity = oldCapacity << 1 + 2`）
3. **理解线程机制**：Thread的状态转换（NEW→RUNNABLE→BLOCKED→WAITING→TIMED_WAITING→TERMINATED）、中断协作机制、守护线程与用户线程的区别
4. **掌握类加载**：双亲委派模型（Bootstrap→Extension→Application）、打破方式（SPI/ThreadContextClassLoader、OSGi、热部署）、类加载器的命名空间隔离
5. **异常体系**：Throwable→Error/Exception层级、Checked Exception的设计争议、try-with-resources的语法糖原理
6. **注解机制**：RetentionPolicy三阶段（SOURCE/CLASS/RUNTIME）、注解继承的局限性、Spring的注解组合原理

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- equals和hashCode的关系？为什么必须一起重写？
- String为什么不可变？String常量池原理？
- new String("abc")创建了几个对象？
- Thread的start()和run()区别？为什么不能直接调run()？
- 双亲委派模型？如何打破？

⭐⭐⭐⭐ 高频：
- wait/notify/notifyAll的使用场景？为什么必须在synchronized块中？
- Thread.sleep()和Object.wait()的区别？
- ThreadLocal的内存泄漏问题？
- 异常处理的最佳实践？try-catch-finally执行顺序？
- @Override注解的作用？不写会怎样？
```

### equals/hashCode 契约代码片段

```java
// 重写equals必须同时重写hashCode，否则HashMap中会出问题
public class Person {
    private String name;
    private int age;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Person person = (Person) o;
        return age == person.age && Objects.equals(name, person.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, age); // JDK7+ 推荐写法
    }
}
// 契约：equals相等的两个对象，hashCode必须相等
//       hashCode相等，equals不一定相等（哈希冲突）
```

### Thread中断协作机制

```java
// 正确的中断响应方式：检查中断标志 + 恢复中断状态
public void run() {
    try {
        while (!Thread.currentThread().isInterrupted()) {
            // 业务逻辑
            Thread.sleep(1000); // 阻塞方法会抛InterruptedException并清除中断标志
        }
    } catch (InterruptedException e) {
        // sleep/wait/join被中断时会清除中断标志，需重新设置
        Thread.currentThread().interrupt();
    }
}
```

---

## 📐 核心原理图

### JVM对象头结构（64位JVM）

```
┌─────────────────────────────────────────────────────────┐
│                    Object Header (128 bit)               │
├──────────────────────┬──────────────────────────────────┤
│   Mark Word (64 bit) │  Klass Pointer (64 bit, 压缩32) │
├──────────────────────┴──────────────────────────────────┤
│  Mark Word 内容（按锁状态变化）：                         │
│                                                          │
│  无锁:    [hashcode(31) | age(4) | biased(1) | 0(1) | 01]│
│  偏向锁:  [threadId(54) | epoch(2) | age(4) | 1(1) | 01]│
│  轻量级锁:[ptr_to_lock_record(62) | 00]                  │
│  重量级锁:[ptr_to_heavyweight_monitor(62) | 10]          │
│  GC标记: [空(63) | 11]                                   │
└─────────────────────────────────────────────────────────┘
  → 锁升级路径：无锁 → 偏向锁 → 轻量级锁(CAS自旋) → 重量级锁(OS Mutex)
```

### String常量池原理

```
┌─────────────── String Pool（堆中, JDK7+） ───────────────┐
│                                                           │
│   引用表 (Hashtable)                                      │
│   ┌──────────────────────────────────────┐               │
│   │ "abc" ──→ String对象(char[]{'a','b','c'}) │          │
│   │ "hello" ──→ String对象(...)                │          │
│   │ "xyz" ──→ String对象(...)                  │          │
│   └──────────────────────────────────────┘               │
│                                                           │
│   String s1 = "abc";           // 字面量 → 常量池查找     │
│   String s2 = "ab" + "c";      // 编译期常量折叠 → 常量池 │
│   String s3 = new String("abc"); // 堆上新对象 + 常量池   │
│   s3.intern();                 // 放入/返回常量池引用     │
│                                                           │
│   s1 == s2       → true  (同一常量池引用)                │
│   s1 == s3       → false (s3是堆上新对象)                │
│   s1 == s3.intern() → true (intern返回常量池引用)         │
│                                                           │
│   JDK6: 常量池在PermGen   JDK7+: 常量池在堆中            │
└───────────────────────────────────────────────────────────┘
```

### Thread状态转换图

```
                        ┌─────────────┐
                        │     NEW     │  new Thread()
                        └──────┬──────┘
                               │ start()
                               ▼
                    ┌─────────────────────┐
          ┌────────│      RUNNABLE        │────────┐
          │         │ (Ready ↔ Running)   │        │
          │         └──────────┬──────────┘        │
          │                    │                   │
     wait()             join()/sleep()      synchronized
          │                    │              (未获锁)
          ▼                    ▼                   ▼
  ┌───────────────┐  ┌──────────────────┐  ┌───────────┐
  │    WAITING    │  │  TIMED_WAITING   │  │  BLOCKED  │
  │ (无超时等待)   │  │  (有超时等待)     │  │ (等监视器锁)│
  └───────┬───────┘  └────────┬─────────┘  └─────┬─────┘
          │ notify()/            │ 超时/notify()    │ 获得锁
          │ notifyAll()          │                  │
          └──────────┬───────────┘                  │
                     │                              │
                     └──────────┬───────────────────┘
                                ▼
                        ┌───────────────┐
                        │  TERMINATED   │  run()正常结束/异常退出
                        └───────────────┘
```

### ClassLoader双亲委派模型

```
┌─────────────────────────────────────────────────────┐
│  Bootstrap ClassLoader (C++实现, 加载rt.jar)         │
│  → java.lang.* / java.util.* / java.io.*            │
│  → 父加载器为null                                    │
├─────────────────────────────────────────────────────┤
│  Extension ClassLoader (加载ext/*.jar)              │
│  → javax.* / 扩展库                                  │
│  → 父加载器 = Bootstrap                              │
├─────────────────────────────────────────────────────┤
│  Application ClassLoader (加载classpath)            │
│  → 用户类和第三方库                                   │
│  → 父加载器 = Extension                              │
├─────────────────────────────────────────────────────┤
│  Custom ClassLoader (自定义)                         │
│  → 热部署 / 加密类 / 隔离加载                         │
│  → 父加载器 = Application                            │
└─────────────────────────────────────────────────────┘

双亲委派流程：
  loadClass() → 委托父加载器 → 父加载器再委托 → 直到Bootstrap
  → 父加载器无法加载 → 子加载器自己加载

打破双亲委派的方式：
  1. 重写loadClass()（不推荐，重写findClass()更安全）
  2. SPI机制: ThreadContextClassLoader
  3. OSGi: 网状类加载结构
  4. Tomcat: 每个WebApp独立ClassLoader
```

---

## 📊 核心类对比表

| 类/概念 | 不可变性 | 线程安全 | 核心特点 | 常见面试问法 |
|---------|----------|----------|----------|-------------|
| String | ✅ 不可变 | ✅ 安全 | 常量池、编译优化 | new String创建几个对象？ |
| StringBuilder | ❌ 可变 | ❌ 不安全 | 非同步、性能高 | 和StringBuffer区别？ |
| StringBuffer | ❌ 可变 | ✅ 安全 | synchronized同步 | 为什么性能比Builder低？ |
| Object.clone() | — | — | 浅拷贝 | 深拷贝怎么实现？ |
| Thread | — | — | 协作式中断 | 为什么不能直接调run()？ |

### 异常体系对比

| 维度 | Checked Exception | Unchecked Exception | Error |
|------|-------------------|---------------------|-------|
| 继承 | Exception（非RuntimeException） | RuntimeException | Error |
| 编译检查 | 必须try-catch或throws | 不强制处理 | 不强制处理 |
| 代表 | IOException/SQLException | NPE/ClassCastException | OOM/StackOverflow |
| 设计理念 | 可恢复的异常 | 编程错误 | 系统级错误 |
| 推荐处理 | catch + 恢复 | 修复代码 | 无法处理，让JVM退出 |

---

## 📖 推荐阅读顺序

```
阶段一（基础）: Object → String → 异常体系
  ↓  理解Java对象模型、不可变设计、错误处理
阶段二（并发）: Thread → （跳转到05_并发包源码）
  ↓  理解线程生命周期，再深入JUC
阶段三（高级）: ClassLoader → 注解机制
  ↓  理解类加载机制，为框架源码打基础
```

---

## 📈 与其他目录的关系

```
01_Java核心源码 → 基础类（Object/String/Thread/ClassLoader）
02_集合框架源码 → 容器类（HashMap/ArrayList/...）
05_并发包源码  → JUC并发类（AQS/线程池/锁/...）
```

---

## 🔗 配套知识点

- [01_Java核心/07_Java注解与反射](../../01_Java核心/07_Java注解与反射.md) — 注解与反射的实战应用
- [05_并发包源码/AQS源码](../05_并发包源码/) — Thread源码的延伸
- [04_并发编程核心](../../04_并发编程核心/) — 并发编程实战

---

*最后更新：2026-07-13*

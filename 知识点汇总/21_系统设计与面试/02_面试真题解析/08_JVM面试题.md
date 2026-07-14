# JVM面试题

> JVM面试高频真题：内存模型、GC算法、调优实战、类加载机制

---

## 📋 目录

1. [内存模型与区域](#1-内存模型与区域)
2. [垃圾回收算法与收集器](#2-垃圾回收算法与收集器)
3. [GC调优实战](#3-gc调优实战)
4. [类加载机制](#4-类加载机制)
5. [JVM参数与监控](#5-jvm参数与监控)
6. [面试题速查](#6-面试题速查)

---

## 1. 内存模型与区域

**Q: 说说JVM内存结构(运行时数据区)**

```
线程私有:                          线程共享:
  程序计数器(PC)                     堆(Heap)
  虚拟机栈(VM Stack)                  ├── 新生代(Eden+S0+S1)
  本地方法栈(Native Stack)            └── 老年代(Old)
                                   方法区(Metaspace)
                                    ├── 类元信息
                                    ├── 常量池
                                    └── JIT编译缓存
```

**Q: 堆和栈的区别？**

| 维度 | 堆(Heap) | 栈(VM Stack) |
|------|---------|-------------|
| 存储 | 对象实例、数组 | 局部变量、操作数栈、动态链接 |
| 线程 | 共享 | 私有 |
| 生命周期 | GC管理 | 方法调用结束自动释放 |
| 大小 | Xmx/Xms配置 | Xss配置(默认1MB) |
| 异常 | OOM | StackOverflowError |

**Q: 方法区和永久代/元空间的区别？**

```
永久代(JDK 7): JVM规范中方法区的一种实现，位于堆中，大小固定容易OOM
元空间(JDK 8+): 方法区的新实现，使用本地内存，大小受限于物理内存
  - 字符串常量池: JDK 7已移到堆中
  - 类元信息: JDK 8+移到Metaspace
  - 优势: 不再容易出现OOM(但可能耗尽物理内存)
```

**Q: 对象在内存中的布局？**

```
对象头(Object Header):
  - Mark Word: 32/64位，存hashCode/GC分代年龄/锁状态
  - Klass Pointer: 指向类元数据的指针(压缩指针4B，否则8B)
  - 数组长度(仅数组对象): 4B

实例数据(Instance Data):
  - 各字段的值(包括继承的)

对齐填充(Padding):
  - 保证对象大小是8字节的整数倍

HotSpot对象大小计算(64位+压缩指针):
  Object: 16B (12头 + 4对齐)
  Integer: 16B (12头 + 4int)
  Long: 24B (12头 + 对齐4 + 8long)
```

---

## 2. 垃圾回收算法与收集器

**Q: GC Roots有哪些？**

```
1. 虚拟机栈中引用的对象(局部变量表)
2. 方法区中类静态属性引用的对象
3. 方法区中常量引用的对象
4. 本地方法栈中JNI引用的对象
5. JVM内部引用(基本类型对应的Class对象/常驻异常/类加载器)
6. 同步锁(synchronized)持有的对象
```

**Q: 说说四种GC算法？**

| 算法 | 原理 | 优点 | 缺点 | 适用 |
|------|------|------|------|------|
| 标记-清除 | 标记可达→清除不可达 | 简单 | 碎片多 | 老年代(CMS) |
| 标记-整理 | 标记→向一端移动 | 无碎片 | 移动开销大 | 老年代(Serial Old/Parallel Old) |
| 复制算法 | 分两块，存活对象复制到另一块 | 无碎片、高效 | 空间减半 | 新生代(Serial/ParNew/Parallel) |
| 分代收集 | 新生代复制+老年代标记整理 | 综合最优 | 实现复杂 | 所有现代收集器 |

**Q: 新生代为什么用复制算法？老年代为什么不用？**

```
新生代: 98%对象朝生夕死，只需复制少量存活对象。Eden:S0:S1=8:1:1只浪费10%
老年代: 存活率高，复制算法需要复制大量对象，效率低且浪费50%空间
```

**Q: 对象何时进入老年代？**

```
1. 年龄达到阈值(默认15，CMS默认6): 每次Minor GC年龄+1
2. 大对象直接分配(-XX:PretenureSizeThreshold): 超过阈值的对象直接进老年代
3. 动态年龄判断: Survivor中同年龄对象总和>Survivor空间一半，>=该年龄的进老年代
4. 空间分配担保: Minor GC后Survivor放不下，通过担保机制进入老年代
```

**Q: 主要垃圾收集器对比？**

| 收集器 | 算法 | 区域 | 特点 | STW |
|--------|------|------|------|-----|
| Serial | 复制 | 新生代 | 单线程，Client模式 | 长 |
| ParNew | 复制 | 新生代 | Serial多线程版 | 中 |
| Parallel Scavenge | 复制 | 新生代 | 吞吐量优先 | 中 |
| CMS | 标记-清除 | 老年代 | 低延迟(JDK 9废弃) | 短 |
| G1 | 分区+复制+整理 | 全堆 | JDK 9+默认，平衡延迟和吞吐 | 可控 |
| ZGC | 着色指针+读屏障 | 全堆 | 目标<1ms(JDK 15+生产可用) | 极短 |

**Q: G1收集器核心原理？**

```
Region分区: 堆划分为等大Region(1~32MB)，每个Region可以是Eden/Survivor/Old/Humongous
Mixed GC: 同时回收新生代+部分老年代(收益最高的Region优先回收)
IHOP: -XX:InitiatingHeapOccupancyPercent(默认45%)，堆占用达此比例触发Mixed GC
可预测停顿: -XX:MaxGCPauseMillis=200ms，G1尽量在目标时间内回收

流程:
  Young GC → 并发标记 → Mixed GC → Full GC(回退)
```

**Q: CMS的四个阶段？为什么被废弃？**

```
1. 初始标记(STW): 标记GC Roots直接引用
2. 并发标记: 从GC Roots遍历(与用户线程并发)
3. 重新标记(STW): 修正并发标记期间变动的引用(写屏障+增量更新)
4. 并发清除: 清除未标记对象(与用户线程并发)

缺点:
  - CPU敏感: 并发阶段占用CPU
  - 浮动垃圾: 并发清除阶段产生的新垃圾下次才能清
  - 内存碎片: 标记-清除不整理
  - Concurrent Mode Failure: 老年代预留空间不足→退回Serial Old(STW很长)

JDK 9废弃原因: 维护成本高，G1已成熟替代
```

---

## 3. GC调优实战

**Q: 如何选择垃圾收集器？**

```
单核/小内存: Serial
多核/吞吐优先: Parallel Scavenge + Parallel Old
低延迟/中等堆: G1(-XX:+UseG1GC)
超低延迟/大堆: ZGC(-XX:+UseZGC)
```

**Q: 常见GC调优场景？**

```bash
# 1. 频繁Full GC
# 排查: jstat -gcutil <pid> 1000
# 原因: 老年代空间不足/Metaspace不足/显式System.gc()
# 解决: 增大老年代/排查内存泄漏/禁用显式GC(-XX:+DisableExplicitGC)

# 2. GC停顿过长
# G1调优: -XX:MaxGCPauseMillis=100 -XX:G1HeapRegionSize=8m
# ZGC: -XX:+UseZGC -Xmx16g -XX:SoftMaxHeapSize=12g

# 3. 元空间溢出
# -XX:MaxMetaspaceSize=256m -XX:MetaspaceSize=128m
```

**Q: 如何排查内存泄漏？**

```
1. jmap -histo:live <pid> → 查看对象统计
2. jmap -dump:format=b,file=heap.hprof <pid> → 导出堆转储
3. MAT/VisualVM分析 → 找到GC Root引用链
4. 常见泄漏场景:
   - ThreadLocal未remove
   - 静态集合持续增长
   - 资源未关闭(Connection/Stream)
   - 监听器/回调未注销
   - 内部类持有外部类引用
```

---

## 4. 类加载机制

**Q: 类加载过程？**

```
加载(Loading) → 验证(Verification) → 准备(Preparation) → 解析(Resolution) → 初始化(Initialization)

加载: 通过全限定名获取二进制字节流 → 生成Class对象
验证: 文件格式/元数据/字节码/符号引用验证
准备: 为静态变量分配内存并赋零值(非代码中的初始值)
      static int a = 123; → 准备阶段a=0，初始化阶段a=123
      static final int b = 123; → 准备阶段b=123(编译期常量)
解析: 符号引用 → 直接引用
初始化: 执行<clinit>()方法(静态变量赋值+static块)
```

**Q: 双亲委派模型？为什么？被破坏的例子？**

```
模型:
  BootstrapClassLoader(_rt.jar_)
    ↑
  ExtClassLoader(_ext/*.jar_)
    ↑
  AppClassLoader(_classpath_)
    ↑
  自定义ClassLoader

为什么: 保证核心类安全(如java.lang.Object始终由Bootstrap加载)
       避免重复加载(父加载器已加载的类子加载器不再加载)

被破坏的例子:
  1. SPI机制: JDBC的Driver由Bootstrap加载，但实现类在classpath
     → 使用线程上下文类加载器(Thread.getContextClassLoader)
  2. Tomcat: 每个WebApp独立类加载器(优先自己加载再委托父)
     → 保证不同应用隔离，同库不同版本共存
  3. OSGi: 网状加载(模块间按需委托)
```

---

## 5. JVM参数与监控

**Q: 常用JVM参数？**

```bash
# 堆
-Xms4g -Xmx4g              # 初始/最大堆(生产环境设相同避免扩容)
-Xmn2g                       # 新生代大小
-XX:NewRatio=2               # 老年代:新生代=2:1
-XX:SurvivorRatio=8          # Eden:S0:S1=8:1:1

# GC
-XX:+UseG1GC                 # 使用G1
-XX:MaxGCPauseMillis=200     # 目标停顿时间
-XX:+PrintGCDetails          # 打印GC详情
-XX:+PrintGCDateStamps       # GC时间戳
-Xloggc:gc.log               # GC日志文件

# 元空间
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m

# OOM时自动dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/tmp/heap.hprof
```

**Q: 常用监控命令？**

```bash
jps          # 查看Java进程
jstat -gc <pid> 1000    # GC统计每秒刷新
jmap -histo:live <pid>  # 存活对象统计
jstack <pid>            # 线程堆栈(查死锁/线程阻塞)
jinfo -flags <pid>      # 查看JVM参数
```

---

## 6. 面试题速查

**Q1: JVM内存模型？**
```
PC/栈/本地方法栈(私有) + 堆/方法区(共享)
堆=新生代(Eden+S0+S1)+老年代，方法区=Metaspace
```

**Q2: 对象何时进老年代？**
```
年龄达阈值(15/CMS6) + 大对象 + 动态年龄 + 空间担保
```

**Q3: G1 vs CMS？**
```
G1: 分区+可预测停顿+整理无碎片，JDK9+默认
CMS: 标记-清除+并发+有碎片+可能Concurrent Mode Failure，JDK9废弃
```

**Q4: 双亲委派？**
```
子→父→祖父加载，保证核心类安全。SPI/Tomcat/OSGi破坏此模型
```

**Q5: 排查OOM？**
```
jmap -histo:live → jmap -dump → MAT分析 → 找GC Root引用链
```

---

*最后更新: 2026-07-14*

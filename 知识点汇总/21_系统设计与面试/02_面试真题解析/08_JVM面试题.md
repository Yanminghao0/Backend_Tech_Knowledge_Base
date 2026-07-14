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

**Q: 程序计数器为什么不会OOM？**

```
程序计数器(PC Register)是唯一不会OOM的区域:
  1. 它只存当前线程执行的字节码行号(很小，一个int)
  2. 线程私有，不需要分配大空间
  3. JVM规范中明确不会抛OOM
  4. 如果执行native方法，PC值为undefined
```

**Q: 虚拟机栈栈帧结构？**

```
每个方法调用创建一个栈帧(Stack Frame)，包含:

1. 局部变量表(Local Variable Table):
   - 存方法参数和方法内局部变量
   - 槽位(Slot): 32位类型占1个Slot, long/double占2个
   - this引用在Slot 0

2. 操作数栈(Operand Stack):
   - 执行字节码指令的工作区(如iadd弹出两个值压入结果)
   - 最大深度编译期确定

3. 动态链接(Dynamic Linking):
   - 指向运行时常量池中方法的引用
   - 支持多态(运行时确定具体方法)

4. 返回地址(Return Address):
   - 方法正常返回: 调用者的PC计数器值
   - 异常返回: 异常表确定返回位置
```

**Q: 为什么要有Survivor区？为什么有两个？**

```
没有Survivor: Eden GC后存活对象直接进老年代 → 老年代很快填满 → 频繁Full GC
有Survivor: Eden GC后存活对象进Survivor, 下次Minor GC时如果还存活再进老年代
  → 让"短命对象"在Minor GC中被回收, 避免"过早晋升"

为什么两个Survivor(S0/S1):
  复制算法需要一块空区. 如果只有一个Survivor, Eden和Survivor同时有存活对象
  无法用复制算法. 两个Survivor交替使用, 一个存数据时另一个为空:
  Eden+S0 → GC → 存活对象复制到S1 → 清空Eden和S0 → 下次Eden+S1 → GC → 复制到S0
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

**Q: 三色标记法？**

```
三色标记并发标记的核心算法:

白色: 尚未被标记(GC结束后仍为白色的会被回收)
灰色: 已标记但引用还未扫描(中间状态)
黑色: 已标记且引用已全部扫描(存活)

流程:
  1. 初始: 所有对象白色, GC Roots灰色
  2. 灰色对象引用的对象标灰 → 自身标黑
  3. 重复直到无灰色对象
  4. 回收白色对象

并发标记问题(用户线程同时运行):
  漏标: 黑色对象新增了指向白色对象的引用(白色被误回收!)
  解决:
    写屏障(Write Barrier): 黑色对象新增引用时, 把新引用标灰
      CMS用增量更新(Incremental Update): 记录新增引用, 重新标记阶段处理
      G1/ZGC用SATB(Snapshot At The Beginning): 标记开始时的快照
    读屏障(Read Barrier): 读取引用时检查并标记
      ZGC用着色指针+读屏障实现并发整理
```

**Q: Card Table和记忆集(Remembered Set)？**

```
问题: 跨代引用(老年代引用新生代)导致Minor GC时需要扫描整个老年代

Card Table(卡表):
  - 老年代分为固定大小(512B)的Card
  - 每个Card对应一个bit(脏/干净)
  - 写引用时把对应Card标记为脏
  - Minor GC只扫描脏Card → 避免扫描整个老年代

Remembered Set(记忆集):
  - 记录"谁引用了我"(非收集区指向收集区的引用)
  - G1中每个Region有RSet, 记录其他Region对自己的引用
  - 用于Mixed GC时知道哪些Region有跨Region引用

G1的RSet实现:
  - 每个Region一个hash表, key=引用者Region, value=Card列表
  - 通过写屏障维护(每次写引用更新RSet)
  - 空间换时间, 避免GC时全堆扫描
```

**Q: ZGC核心原理？**

```
ZGC目标: 停顿<1ms(不论堆大小), JDK 15+生产可用

核心技术:
1. 着色指针(Colored Pointer):
   64位指针的高4位作为标记位:
     Marked0/Marked1/Remapped/Finalizable
   指针本身就包含GC状态, 不需要额外内存

2. 读屏障(Read Barrier):
   每次读取对象引用时检查指针颜色
   如果指针"过期"(指向旧地址) → 转发到新地址
   实现并发移动对象(不需要STW)

3. 并发整理:
   标记/转移/重定位全部并发执行
   只有3个极短的STW: 初始标记/再标记/再分配集选择(各<1ms)

4. 分代ZGC(JDK 21+):
   JDK 21引入分代ZGC(默认), 进一步减少扫描范围
   -XX:+UseZGC -XX:+ZGenerational
```

**Q: 空间分配担保机制？**

```
Minor GC前检查:
  老年代最大可用连续空间 > 新生代所有对象总空间?

  是 → 安全, 直接Minor GC
  否 → 检查是否允许担保失败(-XX:-HandlePromotionFailure)
    允许 → 检查 老年代最大可用 > 历次晋升平均大小
      是 → 尝试Minor GC(有风险)
      否 → Full GC(回收老年代+新生代)
    不允许 → Full GC

JDK 6 Update 24后: HandlePromotionFailure默认开启
  只要老年代连续空间 > 新生代对象总大小 或 > 平均晋升大小, 就尝试Minor GC
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

**Q: JIT编译器(C1/C2/分层编译)？**

```
JVM执行模式: 解释执行 + JIT编译执行(热点代码编译为机器码)

热点探测: 方法调用计数器 + 回边计数器
  超过阈值(-XX:CompileThreshold=10000) → 触发JIT编译

C1编译器(Client):
  - 快速编译, 简单优化
  - 适用于启动速度敏感的场景

C2编译器(Server):
  - 编译慢, 激进优化(逃逸分析/标量替换/锁消除/内联)
  - 适用于长期运行的服务端

分层编译(Tiered Compilation, JDK 10+默认):
  0: 解释执行
  1: C1编译(简单优化+profiling)
  2: C1编译(更多优化+profiling)
  3: C2编译(激进优化)
  先用C1快速达到性能可用 → 后台C2编译替换 → 最佳性能

逃逸分析(C2优化):
  方法内创建的对象如果没有逃逸(不被外部引用) → 栈上分配(不进堆) / 标量替换(拆为基本类型)
```

**Q: 强软弱虚引用？**

```
1. 强引用(Strong): Object obj = new Object()
   只要强引用还在就永不回收, OOM也不回收

2. 软引用(Soft): SoftReference<Object>
   内存不足时才回收(适合缓存)
   SoftReference<byte[]> cache = new SoftReference<>(new byte[1024*1024]);

3. 弱引用(Weak): WeakReference<Object>
   下次GC就回收(不管内存够不够)
   WeakHashMap的key用弱引用 → key被GC后entry自动清除

4. 虚引用(Phantom): PhantomReference<Object>
   不影响对象生命周期, 只在对象被回收时收到通知
   必须配合ReferenceQueue使用
   用途: 跟踪对象被GC的时机(NIO DirectByteBuffer清理)

ReferenceQueue: 软/弱/虚引用指向的对象被GC后, 引用对象本身会被放入队列
  → 可以从队列中取出做清理(如清理堆外内存)
```

**Q: 一次完整的GC日志解读？**

```
[GC (Allocation Failure)]
  [ParNew: 279616K->34870K(314560K), 0.0234567 secs]
  279616K->75550K(1013632K), 0.0235678 secs]
  [Times: user=0.08 sys=0.01, real=0.02 secs]

解读:
  GC (Allocation Failure): Minor GC, 触发原因=分配失败
  ParNew: 新生代使用ParNew收集器
  279616K->34870K: 新生代GC前279MB→GC后34MB
  (314560K): 新生代总容量314MB
  0.0234567 secs: 新生代GC耗时
  279616K->75550K: 整个堆GC前279MB→GC后75MB(新生代回收了204MB, 老年代没有变化)
  (1013632K): 整个堆总容量1013MB
  Times: user(用户态CPU) sys(内核态) real(实际时间, 并行所以user>real)

Full GC日志:
  [Full GC (Allocation Failure)]
  [ParNew: 314559K->314559K(314560K), 0.0123 secs]
  [CMS: 681680K->414819K(699072K), 0.4567890 secs]
  996240K->414819K(1013632K), 0.4690123 secs]
  → CMS回收老年代681MB→414MB
```

**Q: 生产环境JVM参数模板(8G堆/G1)？**

```bash
# 堆(生产环境Xms=Xmx避免动态扩容)
-Xms8g -Xmx8g
-XX:MaxDirectMemorySize=2g           # 堆外内存限制

# G1
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200              # 目标停顿200ms
-XX:G1HeapRegionSize=16m              # Region大小(1/2/4/8/16/32MB)
-XX:InitiatingHeapOccupancyPercent=45 # 堆占用45%触发并发标记
-XX:G1ReservePercent=20               # 保留空间防疏散失败

# Metaspace
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m

# GC日志(JDK 9+统一日志)
-Xlog:gc*:file=/app/logs/gc.log:time,uptime,level,tags:filecount=10,filesize=100m

# OOM自动dump
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/app/logs/heapdump/
-XX:OnOutOfMemoryError="kill -9 %p"   # OOM后杀进程(容器环境)

# 其他
-XX:+DisableExplicitGC                # 禁用System.gc()
-Dfile.encoding=UTF-8
-Duser.timezone=Asia/Shanghai
```

**Q: arthas常用命令？**

```bash
# 安装
curl -O https://arthas.aliyun.com/arthas-boot.jar
java -jar arthas-boot.jar <pid>

# 常用命令:
dashboard          # 实时面板(CPU/内存/GC/线程)
thread -n 3        # CPU最高的3个线程
thread -b          # 找阻塞其他线程的线程(死锁)
thread <id>        # 查看某线程堆栈
jad ClassName      # 反编译类(看实际加载的代码)
watch Class method '{params, returnObj, throwExp}' '#cost > 100'  # 观察方法入参/返回/异常
trace Class method '#cost > 100'     # 逐层追踪方法耗时
stack Class method                    # 查看方法被谁调用
monitor Class method                  # 统计方法调用次数/耗时
vmopt                # 查看JVM参数
heapdump /tmp/h.hprof # 导出堆转储
ognl '@System@getProperty("java.version")'  # 执行表达式
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

**Q: 类初始化顺序？**

```java
class Parent {
    static { System.out.println("1.父类静态块"); }
    { System.out.println("3.父类实例块"); }
    Parent() { System.out.println("4.父类构造器"); }
}
class Child extends Parent {
    static { System.out.println("2.子类静态块"); }
    { System.out.println("5.子类实例块"); }
    Child() { System.out.println("6.子类构造器"); }
}
// new Child() 输出: 1→2→3→4→5→6
// 父类静态 → 子类静态 → 父类实例块 → 父类构造 → 子类实例块 → 子类构造

// 注意:
// 1. 静态块只在类加载时执行一次
// 2. 实例块每次new都执行, 先于构造器
// 3. 父类先于子类初始化
```

**Q: 什么情况会触发类加载(初始化)？**

```
主动引用(触发初始化):
  1. new实例化对象
  2. 访问静态字段(final常量除外)
  3. 调用静态方法
  4. 反射(Class.forName)
  5. 初始化子类时父类先初始化
  6. main方法所在类

被动引用(不触发初始化):
  1. 通过子类访问父类静态字段 → 只初始化父类
  2. 创建数组 → 不初始化(MyClass[] arr = new MyClass[10])
  3. 访问final常量(编译期常量直接进常量池)
```

**Q: 自定义ClassLoader场景和步骤？**

```java
// 场景: 类隔离(Tomcat)/加密解密/热部署/从网络/数据库加载

public class MyClassLoader extends ClassLoader {
    private String classPath;

    public MyClassLoader(String classPath) {
        this.classPath = classPath;
    }

    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        byte[] classData = loadClassData(name);
        if (classData == null) {
            throw new ClassNotFoundException(name);
        }
        // defineClass: 把字节数组转为Class对象
        return defineClass(name, classData, 0, classData.length);
    }

    private byte[] loadClassData(String name) {
        String path = classPath + "/" + name.replace('.', '/') + ".class";
        try (InputStream is = new FileInputStream(path)) {
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024];
            int len;
            while ((len = is.read(buffer)) != -1) {
                baos.write(buffer, 0, len);
            }
            return baos.toByteArray();
        } catch (IOException e) {
            return null;
        }
    }
}

// 打破双亲委派: 重写loadClass而不是findClass
@Override
protected Class<?> loadClass(String name, boolean resolve) {
    // 先自己加载(不委托父)
    Class<?> c = findClass(name);
    if (c != null) return c;
    // 加载不了再委托父
    return super.loadClass(name, resolve);
}
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

**Q6: JIT分层编译？**
```
C1快速编译(简单优化) → C2激进优化(逃逸分析/标量替换/锁消除)
先C1快速可用 → 后台C2替换 → 最佳性能
```

**Q7: 三色标记+写屏障？**
```
白→灰→黑标记, 写屏障防止漏标(CMS增量更新, G1用SATB)
```

**Q8: 强软弱虚引用？**
```
强(永不回收) > 软(内存不足回收, 缓存) > 弱(下次GC回收, WeakHashMap) > 虚(回收通知, DirectByteBuffer)
```

**Q9: ZGC为什么停顿<1ms？**
```
着色指针(指针自带GC状态) + 读屏障(并发转发) + 并发整理(标记/转移/重定位全并发)
```

**Q10: 双亲委派被破坏的场景？**
```
SPI(线程上下文类加载器) / Tomcat(WebApp类加载器优先自己加载) / OSGi(网状加载)
```

**Q11: 线上CPU高排查完整步骤？**
```
top → top -Hp → printf %x → jstack → 定位代码行 → arthas thread -n
```

**Q12: G1调优关键参数？**
```
MaxGCPauseMillis(目标停顿) + G1HeapRegionSize(Region大小) + IHOP(触发并发标记的堆占用比)
```

---

*最后更新: 2026-07-14*

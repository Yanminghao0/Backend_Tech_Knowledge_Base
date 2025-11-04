# JVM调优实战

> 深入理解JVM参数、GC调优、内存分析、故障排查

---

## 📋 目录

1. [JVM参数配置](#1-jvm参数配置)
2. [GC调优](#2-gc调优)
3. [内存分析](#3-内存分析)
4. [故障排查](#4-故障排查)
5. [性能监控](#5-性能监控)
6. [实战案例](#6-实战案例)

---

## 1. JVM参数配置

### 1.1 内存参数

```bash
# 堆内存设置
-Xms4g          # 初始堆大小4G
-Xmx4g          # 最大堆大小4G（建议与Xms相同，避免动态扩展）
-Xmn2g          # 新生代大小2G
-Xss256k        # 每个线程栈大小256K

# 方法区（元空间）
-XX:MetaspaceSize=256m       # 初始元空间大小
-XX:MaxMetaspaceSize=512m    # 最大元空间大小

# 直接内存
-XX:MaxDirectMemorySize=1g   # 最大直接内存

# 示例：生产环境配置（8G内存服务器）
java -Xms4g -Xmx4g -Xmn2g -Xss256k \
     -XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m \
     -jar app.jar
```

**内存分配建议**：
```
服务器总内存：8G

JVM堆内存：4G（50%）
├── 新生代：2G
│   ├── Eden：1.6G（80%）
│   ├── Survivor0：0.2G（10%）
│   └── Survivor1：0.2G（10%）
└── 老年代：2G

元空间：512M
操作系统：2G
其他：1.5G（缓冲）
```

### 1.2 GC参数

```bash
# === G1 GC（推荐，JDK 9+默认）===
-XX:+UseG1GC                        # 使用G1垃圾回收器
-XX:MaxGCPauseMillis=200           # 最大GC停顿时间200ms
-XX:G1HeapRegionSize=16m           # Region大小16M
-XX:InitiatingHeapOccupancyPercent=45  # 触发Mixed GC的堆占用阈值

# === CMS GC（老版本常用）===
-XX:+UseConcMarkSweepGC            # 使用CMS回收器
-XX:+UseCMSInitiatingOccupancyOnly # 只基于占用率触发CMS
-XX:CMSInitiatingOccupancyFraction=70  # 老年代占用70%触发CMS
-XX:+CMSParallelRemarkEnabled      # 并行Remark
-XX:+UseCMSCompactAtFullCollection # Full GC时压缩

# === ZGC（JDK 11+，超低延迟）===
-XX:+UseZGC                        # 使用ZGC
-XX:ZCollectionInterval=120        # GC间隔120秒
-XX:ZAllocationSpikeTolerance=5    # 内存分配容忍度

# === 通用参数 ===
-XX:+DisableExplicitGC             # 禁止System.gc()
-XX:ParallelGCThreads=8            # 并行GC线程数
-XX:ConcGCThreads=2                # 并发GC线程数
```

### 1.3 日志参数

```bash
# JDK 8
-XX:+PrintGCDetails                # 打印GC详情
-XX:+PrintGCDateStamps            # 打印GC时间戳
-XX:+PrintGCApplicationStoppedTime # 打印应用停顿时间
-Xloggc:/var/log/gc.log           # GC日志路径
-XX:+UseGCLogFileRotation         # 日志轮转
-XX:NumberOfGCLogFiles=5          # 保留5个日志文件
-XX:GCLogFileSize=100M            # 每个日志文件100M

# JDK 9+（统一日志）
-Xlog:gc*:file=/var/log/gc.log:time,uptime,level,tags:filecount=5,filesize=100m
```

### 1.4 故障排查参数

```bash
# OOM时自动Dump堆
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump/

# 发生OOM时执行脚本（告警）
-XX:OnOutOfMemoryError="sh /path/to/alert.sh %p"

# 打印类加载信息
-XX:+TraceClassLoading
-XX:+TraceClassUnloading

# 打印JIT编译信息
-XX:+PrintCompilation
```

### 1.5 完整生产环境配置

```bash
#!/bin/bash
# 生产环境JVM启动脚本

JAVA_OPTS="-server \
-Xms4g -Xmx4g -Xmn2g -Xss256k \
-XX:MetaspaceSize=256m -XX:MaxMetaspaceSize=512m \
-XX:+UseG1GC \
-XX:MaxGCPauseMillis=200 \
-XX:G1HeapRegionSize=16m \
-XX:InitiatingHeapOccupancyPercent=45 \
-XX:+ParallelRefProcEnabled \
-XX:+DisableExplicitGC \
-XX:+HeapDumpOnOutOfMemoryError \
-XX:HeapDumpPath=/var/log/heapdump/ \
-Xlog:gc*:file=/var/log/gc.log:time,uptime,level,tags:filecount=5,filesize=100m \
-Duser.timezone=Asia/Shanghai \
-Dfile.encoding=UTF-8"

java $JAVA_OPTS -jar app.jar
```

---

## 2. GC调优

### 2.1 GC问题诊断

```
常见GC问题：

1. 频繁Minor GC：
   现象：Eden区快速填满
   原因：对象分配速率过快
   
2. 频繁Full GC：
   现象：老年代频繁满
   原因：对象晋升过快、内存泄漏
   
3. GC停顿时间长：
   现象：STW时间过长
   原因：堆太大、垃圾对象过多
   
4. 内存泄漏：
   现象：Full GC后内存不下降
   原因：对象无法回收
```

### 2.2 GC日志分析

**G1 GC日志示例**：
```
[2025-10-27T10:30:15.123+0800][info][gc] GC(123) Pause Young (Normal) (G1 Evacuation Pause)
[2025-10-27T10:30:15.123+0800][info][gc] GC(123) Using 8 workers of 8 for evacuation
[2025-10-27T10:30:15.145+0800][info][gc] GC(123) Pause Young (Normal) 2048M->512M(4096M) 22.456ms
                                                                        ↑      ↑    ↑      ↑
                                                                   GC前大小 GC后  总大小  耗时
```

**关键指标**：
```
1. GC频率：
   - Minor GC：每分钟<10次
   - Full GC：每小时<1次

2. GC停顿时间：
   - Minor GC：<50ms
   - Full GC：<200ms（G1 GC）

3. 吞吐量：
   - 应用运行时间 / (应用运行时间 + GC时间) > 95%
```

### 2.3 G1 GC调优

```bash
# 基础配置
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200           # 目标停顿时间

# Region大小调整
-XX:G1HeapRegionSize=16m           # Region越大，适合大对象多的场景

# Mixed GC触发条件
-XX:InitiatingHeapOccupancyPercent=45  # 堆占用45%触发

# 并发标记线程数
-XX:ConcGCThreads=2                # 并发标记线程数

# 老年代占比
-XX:G1OldCGenOccupancyThreshold=75 # 老年代占用75%触发Mixed GC

# 大对象阈值
-XX:G1HeapRegionSize=16m           # 超过Region一半的对象为大对象
```

**调优策略**：
```
问题1：Minor GC频繁
解决：增大新生代 -Xmn

问题2：Mixed GC频繁
解决：降低 InitiatingHeapOccupancyPercent

问题3：Full GC发生
解决：增大堆内存、检查内存泄漏

问题4：停顿时间长
解决：降低 MaxGCPauseMillis、增大堆内存
```

### 2.4 CMS GC调优

```bash
# 基础配置
-XX:+UseConcMarkSweepGC
-XX:+UseCMSInitiatingOccupancyOnly
-XX:CMSInitiatingOccupancyFraction=70  # 老年代占用70%触发

# 优化配置
-XX:+CMSParallelRemarkEnabled      # 并行Remark
-XX:+UseCMSCompactAtFullCollection # Full GC时压缩
-XX:CMSFullGCsBeforeCompaction=5   # 5次Full GC后压缩
-XX:+CMSScavengeBeforeRemark       # Remark前Minor GC

# 类卸载
-XX:+CMSClassUnloadingEnabled      # 允许卸载类
```

**CMS问题**：
```
问题1：Concurrent Mode Failure
原因：老年代空间不足
解决：降低CMSInitiatingOccupancyFraction、增大堆

问题2：Promotion Failed
原因：Survivor区对象无法晋升到老年代
解决：增大Survivor区、增大老年代

问题3：内存碎片
原因：CMS不压缩
解决：定期Full GC压缩
```

---

## 3. 内存分析

### 3.1 Heap Dump分析

**生成Heap Dump**：
```bash
# 方式1：主动生成
jmap -dump:format=b,file=heap.hprof <pid>

# 方式2：OOM时自动生成
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/heapdump/

# 方式3：通过JMX
jcmd <pid> GC.heap_dump heap.hprof
```

**使用MAT分析**：
```
1. 下载Eclipse MAT
2. 打开heap.hprof文件
3. 查看Leak Suspects（内存泄漏疑点）
4. 分析对象引用链
5. 找到根本原因
```

**常见内存泄漏场景**：
```java
// 1. 静态集合未清理
public class Cache {
    private static Map<String, Object> cache = new HashMap<>();
    
    public void put(String key, Object value) {
        cache.put(key, value);  // 永远不清理，导致OOM
    }
}

// 2. 监听器未移除
public class EventManager {
    private List<EventListener> listeners = new ArrayList<>();
    
    public void addListener(EventListener listener) {
        listeners.add(listener);  // 监听器未移除，导致内存泄漏
    }
}

// 3. ThreadLocal未清理
public class Context {
    private static ThreadLocal<User> userContext = new ThreadLocal<>();
    
    public void setUser(User user) {
        userContext.set(user);  // 线程池场景下，ThreadLocal未清理
    }
}

// 4. 连接未关闭
public void query() {
    Connection conn = DriverManager.getConnection(url);
    // ... 未关闭连接
}
```

### 3.2 内存占用优化

```java
/**
 * 对象内存占用计算
 */
public class MemoryCalculator {
    
    // 示例1：简单对象
    class User {
        private long id;        // 8 bytes
        private int age;        // 4 bytes
        private String name;    // 4 bytes（引用）+ String对象
        // 对象头：12 bytes
        // 对齐填充：4 bytes
        // 总计：32 bytes + String对象大小
    }
    
    // 示例2：优化前
    class Order {
        private Long orderId;        // 包装类：16 bytes对象
        private Integer userId;      // 16 bytes对象
        private Double amount;       // 16 bytes对象
        // 总计：48 bytes + 对象头 = 60+ bytes
    }
    
    // 示例3：优化后
    class OrderOptimized {
        private long orderId;        // 基本类型：8 bytes
        private int userId;          // 4 bytes
        private double amount;       // 8 bytes
        // 总计：20 bytes + 对象头 = 32 bytes
    }
}
```

**优化建议**：
```java
// 1. 使用基本类型代替包装类
// ❌ 不好
private Integer count = 0;

// ✅ 好
private int count = 0;

// 2. 字符串优化
// ❌ 不好
String s = new String("hello");  // 创建2个对象

// ✅ 好
String s = "hello";  // 字符串常量池，只创建1个

// 3. 集合初始化容量
// ❌ 不好
List<String> list = new ArrayList<>();  // 默认10，可能扩容

// ✅ 好
List<String> list = new ArrayList<>(100);  // 预估大小，减少扩容

// 4. 使用StringBuilder
// ❌ 不好
String s = "";
for (int i = 0; i < 1000; i++) {
    s += i;  // 创建1000个String对象
}

// ✅ 好
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 1000; i++) {
    sb.append(i);  // 只创建1个StringBuilder
}
```

---

## 4. 故障排查

### 4.1 CPU飙高排查

```bash
# 1. 找到CPU占用高的进程
top
# PID  %CPU  COMMAND
# 1234  300   java

# 2. 找到CPU占用高的线程
top -Hp 1234
# PID   %CPU
# 1250  150
# 1251  150

# 3. 将线程ID转为16进制
printf "%x\n" 1250
# 4e2

# 4. 查看线程堆栈
jstack 1234 | grep 4e2 -A 50

# 5. 分析堆栈，找到问题代码
```

**常见原因**：
```
1. 死循环
2. 正则表达式回溯
3. 频繁GC
4. 大量对象创建
5. 序列化/反序列化
```

### 4.2 内存溢出排查

```bash
# 1. 查看堆内存使用
jmap -heap <pid>

# 2. 查看对象占用
jmap -histo:live <pid> | head -20

# 3. 生成Heap Dump
jmap -dump:format=b,file=heap.hprof <pid>

# 4. 使用MAT分析
# - 找到占用内存最大的对象
# - 分析对象引用链
# - 定位内存泄漏点
```

### 4.3 线程死锁排查

```bash
# 1. 生成线程Dump
jstack <pid> > thread.dump

# 2. 查找死锁信息
grep -A 20 "Found one Java-level deadlock" thread.dump

# 3. 分析死锁原因
```

**死锁示例**：
```java
public class DeadlockDemo {
    private static Object lock1 = new Object();
    private static Object lock2 = new Object();
    
    public static void main(String[] args) {
        // 线程1：先锁lock1，再锁lock2
        new Thread(() -> {
            synchronized (lock1) {
                System.out.println("Thread 1: holding lock1...");
                sleep(100);
                synchronized (lock2) {
                    System.out.println("Thread 1: holding lock1 & lock2...");
                }
            }
        }).start();
        
        // 线程2：先锁lock2，再锁lock1
        new Thread(() -> {
            synchronized (lock2) {
                System.out.println("Thread 2: holding lock2...");
                sleep(100);
                synchronized (lock1) {
                    System.out.println("Thread 2: holding lock2 & lock1...");
                }
            }
        }).start();
    }
}

// jstack输出：
// Found one Java-level deadlock:
// "Thread-1":
//   waiting to lock monitor 0x00007f8b1c005e78 (object 0x00000007e0000010, a java.lang.Object),
//   which is held by "Thread-0"
// "Thread-0":
//   waiting to lock monitor 0x00007f8b1c005dc8 (object 0x00000007e0000020, a java.lang.Object),
//   which is held by "Thread-1"
```

### 4.4 常用诊断命令

```bash
# === jps：查看Java进程 ===
jps -lvm
# 1234 com.example.App -Xms4g -Xmx4g

# === jstat：查看GC统计 ===
jstat -gc <pid> 1000 10  # 每秒输出GC统计，共10次
# S0C    S1C    S0U    S1U      EC       EU        OC         OU       MC
# 10240  10240  0      9216     81920    50000     204800     150000   51200

jstat -gcutil <pid>  # 百分比显示
# S0     S1     E      O      M     CCS
# 0.00   90.00  61.05  73.24  98.50  95.23

# === jmap：内存映射 ===
jmap -heap <pid>               # 堆配置和使用情况
jmap -histo <pid>              # 对象统计
jmap -dump:live,format=b,file=heap.hprof <pid>  # Dump堆

# === jstack：线程堆栈 ===
jstack <pid>                   # 所有线程堆栈
jstack -l <pid>                # 包含锁信息

# === jinfo：JVM配置 ===
jinfo -flags <pid>             # 查看JVM参数
jinfo -flag MaxHeapSize <pid>  # 查看特定参数

# === jcmd：综合命令 ===
jcmd <pid> help                # 查看可用命令
jcmd <pid> VM.flags            # 查看JVM参数
jcmd <pid> GC.heap_info        # 查看堆信息
jcmd <pid> Thread.print        # 打印线程
```

---

## 5. 性能监控

### 5.1 JMX监控

```java
/**
 * 开启JMX监控
 */
// JVM参数
-Dcom.sun.management.jmxremote
-Dcom.sun.management.jmxremote.port=9999
-Dcom.sun.management.jmxremote.ssl=false
-Dcom.sun.management.jmxremote.authenticate=false

// 使用JConsole/VisualVM连接
jconsole localhost:9999
```

### 5.2 Prometheus + Grafana

```xml
<!-- 引入依赖 -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: prometheus
  metrics:
    export:
      prometheus:
        enabled: true
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'spring-boot-app'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['localhost:8080']
```

### 5.3 Arthas诊断工具

```bash
# 1. 下载Arthas
curl -O https://arthas.aliyun.com/arthas-boot.jar

# 2. 启动Arthas
java -jar arthas-boot.jar

# 3. 选择要诊断的进程
[1]: 1234 com.example.App

# 4. 常用命令

# 查看JVM信息
dashboard

# 查看线程
thread

# 查看方法调用
watch com.example.UserService getUser '{params, returnObj, throwExp}' -x 2

# 反编译
jad com.example.UserService

# 查看类加载信息
sc -d com.example.UserService

# 性能分析
profiler start
profiler stop --format html
```

---

## 6. 实战案例

### 案例1：Full GC频繁

**问题现象**：
```
应用每5分钟Full GC一次
Full GC停顿2-3秒
老年代使用率始终在80%以上
```

**排查步骤**：
```bash
# 1. 查看GC日志
tail -f /var/log/gc.log
# [Full GC (Allocation Failure) 3584M->3400M(4096M), 2.5 secs]

# 2. Dump堆分析
jmap -dump:live,format=b,file=heap.hprof <pid>

# 3. MAT分析
# 发现：大量ThreadLocal对象占用2G内存
```

**根本原因**：
```java
// 问题代码
public class UserContext {
    private static ThreadLocal<Map<String, Object>> context = 
        new ThreadLocal<>();
    
    public static void set(String key, Object value) {
        Map<String, Object> map = context.get();
        if (map == null) {
            map = new HashMap<>();
            context.set(map);
        }
        map.put(key, value);  // 从未清理！
    }
}

// 在线程池场景下，ThreadLocal永远不清理，导致内存泄漏
```

**解决方案**：
```java
// 修复代码
public class UserContext {
    private static ThreadLocal<Map<String, Object>> context = 
        new ThreadLocal<>();
    
    public static void set(String key, Object value) {
        Map<String, Object> map = context.get();
        if (map == null) {
            map = new HashMap<>();
            context.set(map);
        }
        map.put(key, value);
    }
    
    // 添加清理方法
    public static void clear() {
        context.remove();  // 必须清理！
    }
}

// 使用Filter清理
@WebFilter
public class ContextCleanFilter implements Filter {
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) {
        try {
            chain.doFilter(request, response);
        } finally {
            UserContext.clear();  // 请求结束后清理
        }
    }
}
```

**效果**：
```
Full GC频率：5分钟/次 → 2小时/次
老年代使用率：80% → 40%
应用停顿：2-3秒 → 200ms
```

### 案例2：接口响应慢

**问题现象**：
```
某接口P99延迟500ms
CPU使用率50%
无明显GC问题
```

**排查步骤**：
```bash
# 1. 使用Arthas分析
java -jar arthas-boot.jar

# 2. 监控方法耗时
trace com.example.OrderService createOrder -n 10

# 3. 查看方法调用树
# 发现：UserService.getUser()耗时400ms
```

**根本原因**：
```java
// 问题代码
@Service
public class UserService {
    
    @Autowired
    private UserMapper userMapper;
    
    public User getUser(Long id) {
        // N+1查询问题
        User user = userMapper.selectById(id);
        
        // 逐个查询订单（N次数据库查询）
        List<Order> orders = new ArrayList<>();
        for (Long orderId : user.getOrderIds()) {
            Order order = orderMapper.selectById(orderId);  // N次查询
            orders.add(order);
        }
        user.setOrders(orders);
        
        return user;
    }
}
```

**解决方案**：
```java
// 修复代码
@Service
public class UserService {
    
    @Autowired
    private UserMapper userMapper;
    
    @Autowired
    private OrderMapper orderMapper;
    
    public User getUser(Long id) {
        User user = userMapper.selectById(id);
        
        // 批量查询（1次数据库查询）
        List<Order> orders = orderMapper.selectBatchIds(user.getOrderIds());
        user.setOrders(orders);
        
        return user;
    }
}
```

**效果**：
```
P99延迟：500ms → 50ms
数据库查询：N+1次 → 2次
吞吐量：200 QPS → 2000 QPS
```

---

## 📚 参考资料

- 🔗 [Oracle JVM调优指南](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/gctuning/)
- 🔗 [Eclipse MAT文档](https://www.eclipse.org/mat/)
- 🔗 [Arthas官方文档](https://arthas.aliyun.com/)
- 📖 《深入理解Java虚拟机》
- 📖 《Java性能权威指南》

---

*最后更新：2025-10-27*

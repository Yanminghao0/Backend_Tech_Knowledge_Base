# CPU高负载排查

> 实战指南：如何排查CPU飙高、线程死循环、热点代码等CPU问题

## 📋 目录
- [常见问题类型](#常见问题类型)
- [CPU飙高排查](#cpu飙高排查)
- [线程死循环](#线程死循环)
- [热点代码](#热点代码)
- [排查工具](#排查工具)

---

## 常见问题类型

### 1. CPU使用率高

**症状**：
```
✅ CPU使用率持续>80%
✅ 应用响应变慢
✅ 系统负载高
```

### 2. CPU飙高

**症状**：
```
✅ CPU使用率突然飙升到100%
✅ 系统响应变慢
✅ 应用无响应
```

### 3. 线程死循环

**症状**：
```
✅ CPU使用率100%
✅ 单个线程CPU使用率高
✅ 应用响应变慢
```

---

## CPU飙高排查

### 排查方法

**1. 查看CPU使用率**

```bash
# 查看CPU使用率
top
htop
vmstat 1

# 查看Java进程CPU使用率
top -H -p <pid>
```

**2. 查看线程堆栈**

```bash
# 查看线程堆栈
jstack <pid>

# 查看CPU使用率高的线程
top -H -p <pid> | head -20
# 将线程ID转换为16进制
printf "%x\n" <thread_id>
# 在jstack输出中查找该线程
```

**3. 使用Arthas**

```bash
# 启动Arthas
java -jar arthas-boot.jar

# 查看CPU使用率高的线程
thread

# 查看热点方法
profiler start
profiler stop
```

### 常见原因

**1. 死循环**

```java
// ❌ 死循环
while (true) {
    // 无限循环
}

// ✅ 添加条件
while (condition) {
    // 循环逻辑
}
```

**2. 频繁计算**

```java
// ❌ 频繁计算
for (int i = 0; i < 1000000; i++) {
    complexCalculation();  // 复杂计算
}

// ✅ 优化
// 1. 减少计算次数
// 2. 使用缓存
// 3. 优化算法
```

**3. 线程死锁**

```java
// 线程死锁导致CPU使用率高
// 排查方法：jstack查看线程堆栈
```

### 解决方案

**1. 修复死循环**

```java
// 添加退出条件
while (condition) {
    // 循环逻辑
    if (shouldExit()) {
        break;
    }
}
```

**2. 优化热点代码**

```java
// 1. 减少计算次数
// 2. 使用缓存
// 3. 优化算法
// 4. 使用异步处理
```

**3. 限制线程数**

```java
// 限制线程池大小
ExecutorService executor = Executors.newFixedThreadPool(10);
```

---

## 线程死循环

### 排查方法

**1. 查看线程堆栈**

```bash
# 查看线程堆栈
jstack <pid> | grep -A 20 "线程名"

# 查看CPU使用率高的线程
top -H -p <pid>
```

**2. 使用Arthas**

```bash
# 查看线程堆栈
thread <thread_id>

# 查看热点方法
profiler start
```

### 常见原因

**1. while(true)循环**

```java
// ❌ 死循环
while (true) {
    // 无限循环
}

// ✅ 添加条件
while (condition) {
    // 循环逻辑
    if (shouldExit()) {
        break;
    }
}
```

**2. 递归调用**

```java
// ❌ 无限递归
public void recursive() {
    recursive();  // 无限递归
}

// ✅ 添加终止条件
public void recursive(int depth) {
    if (depth <= 0) {
        return;
    }
    recursive(depth - 1);
}
```

### 解决方案

**1. 修复死循环**

```java
// 添加退出条件
while (condition) {
    // 循环逻辑
    if (shouldExit()) {
        break;
    }
}
```

**2. 限制循环次数**

```java
// 限制循环次数
int maxIterations = 1000;
int count = 0;
while (condition && count < maxIterations) {
    // 循环逻辑
    count++;
}
```

---

## 热点代码

### 排查方法

**1. 使用Arthas**

```bash
# 启动Arthas
java -jar arthas-boot.jar

# 查看热点方法
profiler start
# 等待一段时间
profiler stop
# 查看分析结果
```

**2. 使用JProfiler**

```bash
# 使用JProfiler分析热点代码
# 1. 启动JProfiler
# 2. 连接应用
# 3. 查看CPU使用情况
# 4. 分析热点方法
```

### 常见原因

**1. 频繁计算**

```java
// ❌ 频繁计算
for (int i = 0; i < 1000000; i++) {
    complexCalculation();  // 复杂计算
}

// ✅ 优化
// 1. 减少计算次数
// 2. 使用缓存
// 3. 优化算法
```

**2. 频繁字符串操作**

```java
// ❌ 频繁字符串拼接
String result = "";
for (int i = 0; i < 10000; i++) {
    result += i;  // 频繁创建对象
}

// ✅ 使用StringBuilder
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 10000; i++) {
    sb.append(i);
}
String result = sb.toString();
```

**3. 频繁IO操作**

```java
// ❌ 频繁IO操作
for (int i = 0; i < 1000; i++) {
    File file = new File("file" + i);
    file.createNewFile();  // 频繁IO
}

// ✅ 批量操作
// 1. 批量处理
// 2. 使用异步IO
// 3. 使用缓冲
```

### 解决方案

**1. 优化算法**

```java
// 1. 优化算法复杂度
// 2. 减少计算次数
// 3. 使用缓存
```

**2. 使用缓存**

```java
// 缓存计算结果
private Map<String, Object> cache = new HashMap<>();

public Object compute(String key) {
    if (cache.containsKey(key)) {
        return cache.get(key);
    }
    Object result = expensiveComputation(key);
    cache.put(key, result);
    return result;
}
```

**3. 异步处理**

```java
// 异步处理耗时操作
CompletableFuture.supplyAsync(() -> {
    return expensiveComputation();
});
```

---

## 排查工具

### 1. 系统工具

```bash
# top - 查看CPU使用率
top
top -H -p <pid>

# htop - 交互式查看
htop

# vmstat - 系统统计
vmstat 1
```

### 2. Java工具

```bash
# jstack - 线程堆栈
jstack <pid>

# Arthas - Java诊断工具
java -jar arthas-boot.jar
thread
profiler start
```

### 3. 性能分析工具

```bash
# JProfiler - Java性能分析
# 1. 启动JProfiler
# 2. 连接应用
# 3. 查看CPU使用情况

# VisualVM - Java性能分析
# 1. 启动VisualVM
# 2. 连接应用
# 3. 查看CPU使用情况
```

---

## 📚 相关文档

- [性能问题排查](./01_性能问题排查.md)
- [内存泄漏排查](./08_内存泄漏排查.md)
- [JVM调优实战](../11_性能优化/01_JVM调优实战.md)

---

**最后更新**: 2025-10-29  
**文档状态**: ✅ 框架已搭建，内容持续完善中


## CPU高负载具体案例分析

### 案例一：电商秒杀场景CPU飙高

**问题描述**：秒杀活动开始后，系统CPU使用率瞬间飙升至100%，导致部分用户无法下单。

**排查过程**：
1. 使用top命令定位高CPU进程：
```bash
top -H -p <pid>
```
2. 发现多个线程CPU使用率超过90%
3. 线程堆栈分析显示大量线程阻塞在库存检查方法

**关键代码分析**：
```java
// ❌ 低效的库存检查实现
public synchronized boolean checkStock(Long productId, int quantity) {
    Product product = productMapper.selectById(productId);
    if (product.getStock() >= quantity) {
        product.setStock(product.getStock() - quantity);
        productMapper.updateById(product);
        return true;
    }
    return false;
}
```

**解决方案**：
```java
// ✅ 优化方案
// 1. 引入Redis预扣减库存
// 2. 使用Lua脚本保证原子性
// 3. 异步更新数据库
public boolean checkStock(Long productId, int quantity) {
    String key = "seckill:stock:" + productId;
    // Lua脚本原子操作
    String luaScript = "if redis.call('exists', KEYS[1]) == 1 then " +
                     "local stock = tonumber(redis.call('get', KEYS[1])) " +
                     "if stock >= tonumber(ARGV[1]) then " +
                     "redis.call('decrby', KEYS[1], ARGV[1]) " +
                     "return 1 " +
                     "end " +
                     "return 0 " +
                     "end " +
                     "return -1";
                      
    Long result = (Long) redisTemplate.execute(
        new DefaultRedisScript<>(luaScript, Long.class),
        Collections.singletonList(key),
        String.valueOf(quantity)
    );
    
    if (result == 1) {
        // 异步更新数据库
        asyncUpdateStock(productId, quantity);
        return true;
    }
    return false;
}
```

### 案例二：正则表达式回溯导致CPU飙升

**问题描述**：日志解析服务CPU使用率持续90%以上，响应时间延长。

**排查过程**：
1. 使用Arthas profiler生成火焰图：
```bash
profiler start --event cpu
# 等待30秒
profiler stop --format html
```
2. 火焰图显示`java.util.regex.Pattern`占用大量CPU
3. 定位到复杂正则表达式匹配日志内容

**关键代码分析**：
```java
// ❌ 问题正则表达式
String regex = "^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)$";
Pattern pattern = Pattern.compile(regex);

// 处理大量日志时CPU飙升
while ((line = br.readLine()) != null) {
    Matcher matcher = pattern.matcher(line);
    if (matcher.matches()) {
        // 处理日志
    }
}
```

**解决方案**：
```java
// ✅ 优化方案
// 1. 简化正则表达式
// 2. 使用字符串操作替代部分正则功能
// 3. 预编译Pattern
private static final Pattern LOG_PATTERN = Pattern.compile("^(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}) (.*)$");

public void parseLog(String line) {
    // 先快速判断前缀
    if (line.length() < 19) return;
    if (!Character.isDigit(line.charAt(0))) return;
    
    Matcher matcher = LOG_PATTERN.matcher(line);
    if (matcher.matches()) {
        String time = matcher.group(1);
        String content = matcher.group(2);
        // 处理日志
    }
}
```

## 高级排查技术

### 使用AsyncProfiler生成CPU火焰图

**1. 安装AsyncProfiler**
```bash
# 下载最新版本
wget https://github.com/jvm-profiling-tools/async-profiler/releases/download/v2.9/async-profiler-2.9-linux-x64.tar.gz

tar -zxvf async-profiler-2.9-linux-x64.tar.gz
cd async-profiler-2.9-linux-x64
```

**2. 生成CPU火焰图**
```bash
# 记录CPU使用情况，持续30秒
./profiler.sh -d 30 -o flamegraph.html <pid>

# 查看生成的火焰图
open flamegraph.html
```

**3. 火焰图分析技巧**
- 横向宽度表示CPU时间占比
- 纵向表示调用栈深度
- 平顶表示CPU热点函数
- 红色区域表示Java代码
- 黄色区域表示C++/JVM代码

### 使用Perf工具分析

**1. 安装perf**
```bash
# Ubuntu/Debian
sudo apt-get install linux-tools-common

# CentOS/RHEL
sudo yum install perf
```

**2. 采集CPU数据**
```bash
# 采集Java进程CPU数据
perf record -g -p <pid> sleep 30

# 生成报告
perf report
```

**3. 分析Java代码**
```bash
# 结合jstack分析
perf script | grep -A 20 java
```

## 监控告警配置

### Prometheus + Grafana监控CPU指标

**1. 添加Micrometer依赖**
```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
    <version>1.10.0</version>
</dependency>
```

**2. 配置CPU监控指标**
```java
@Configuration
public class CpuMetricsConfig {
    @Bean
    public MeterRegistryCustomizer<MeterRegistry> metricsCommonTags() {
        return registry -> registry.config()
            .commonTags("application", "your-application-name")
            .meterFilter(MeterFilter.deny(id ->
                id.getName().startsWith("jvm.cpu") &&
                id.getTag("region").equals("test")));
    }
}
```

**3. 关键CPU监控指标**
- `system.cpu.usage`：系统CPU使用率
- `process.cpu.usage`：进程CPU使用率
- `jvm.threads.live`：活跃线程数
- `jvm.threads.peak`：峰值线程数
- `executorService.activeThreads`：线程池活跃线程数

**4. Grafana告警规则**
```yaml
groups:
- name: cpu_alerts
  rules:
  - alert: HighCpuUsage
    expr: process.cpu.usage > 0.8
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is above 80% for 5 minutes"

  - alert: ThreadCountExceeded
    expr: jvm.threads.live > 500
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Too many live threads"
      description: "Live threads count is above 500 for 5 minutes"
```

**最后更新**: 2025-10-29  
**文档状态**: ✅ 框架已搭建，内容持续完善中
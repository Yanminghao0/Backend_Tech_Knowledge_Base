# 生产环境问题排查手册

> 实战手册：生产环境常见问题排查方法与思路

## 📋 目录

### 核心文档
- [问题排查方法论](#问题排查方法论)
- [通用排查流程](#通用排查流程)
- [问题分类索引](#问题分类索引)

### 问题排查专题
- [01_性能问题排查](./01_性能问题排查.md) - 接口慢、响应时间长、QPS低
- [02_错误日志分析](./02_错误日志分析.md) - 异常堆栈、错误码、日志分析
- [03_系统故障排查](./03_系统故障排查.md) - 服务不可用、宕机、重启
- [04_数据库问题排查](./04_数据库问题排查.md) - 慢SQL、连接池、死锁、主从延迟
- [05_缓存问题排查](./05_缓存问题排查.md) - Redis连接、缓存穿透、击穿、雪崩
- [06_消息队列问题排查](./06_消息队列问题排查.md) - 消息积压、消费延迟、重复消费
- [07_网络问题排查](./07_网络问题排查.md) - 连接超时、网络延迟、丢包
- [08_内存泄漏排查](./08_内存泄漏排查.md) - OOM、内存持续增长、GC频繁
- [09_CPU高负载排查](./09_CPU高负载排查.md) - CPU飙高、线程死循环、热点代码
- [10_磁盘IO问题排查](./10_磁盘IO问题排查.md) - 磁盘满、IO等待、文件句柄泄露
- [11_分布式系统问题排查](./11_分布式系统问题排查.md) - 服务调用失败、分布式事务、配置中心
- [12_常见问题速查手册](./12_常见问题速查手册.md) - 快速定位问题的命令和脚本

---

## 问题排查方法论

### 黄金法则

```
1. 先看监控，再看日志
2. 先看整体，再看局部
3. 先看现象，再找原因
4. 先恢复，再排查
5. 记录问题，总结经验
```

### 排查思路

```
现象 → 假设 → 验证 → 结论
  ↓       ↓      ↓      ↓
监控指标  可能原因  排查工具  解决方案
```

---

## 通用排查流程

### 第一步：问题确认（5分钟）

**确认问题现象**：
```
✅ 问题是什么？（接口慢、服务不可用、数据错误）
✅ 什么时候开始？（时间点、触发条件）
✅ 影响范围？（单个服务、多个服务、全部用户）
✅ 严重程度？（P0紧急、P1重要、P2一般）
```

**收集基础信息**：
```
✅ 错误日志（最近30分钟）
✅ 监控指标（CPU、内存、QPS、RT）
✅ 用户反馈（错误信息、操作步骤）
✅ 最近变更（代码发布、配置修改、扩容）
```

### 第二步：快速定位（10分钟）

**查看监控大盘**：
```
1. 应用监控：
   - QPS是否下降？
   - RT是否上升？
   - 错误率是否增加？
   - 成功率是否下降？

2. 系统监控：
   - CPU使用率
   - 内存使用率
   - 磁盘IO
   - 网络IO

3. 中间件监控：
   - 数据库连接数
   - Redis连接数
   - 消息队列积压
   - 缓存命中率
```

**查看错误日志**：
```
1. 应用日志：
   - ERROR级别日志
   - Exception堆栈
   - 业务异常信息

2. 系统日志：
   - /var/log/messages
   - dmesg（系统消息）
   - journalctl（systemd日志）

3. 中间件日志：
   - MySQL慢查询日志
   - Redis日志
   - Nginx访问日志
```

### 第三步：深入分析（20分钟）

**根据问题类型选择排查方法**：

| 问题类型 | 排查重点 | 常用工具 |
|---------|---------|---------|
| 性能问题 | RT、QPS、线程池、数据库慢SQL | Arthas、jstack、EXPLAIN |
| 内存问题 | 堆内存、GC、OOM | jmap、MAT、jstat |
| CPU问题 | 热点代码、线程死循环 | top、jstack、Arthas |
| 网络问题 | 连接数、超时、丢包 | netstat、tcpdump、ping |
| 数据库问题 | 慢SQL、锁等待、连接池 | EXPLAIN、SHOW PROCESSLIST |
| 缓存问题 | 命中率、连接、大key | redis-cli、redis-stat |

### 第四步：解决方案（10分钟）

**临时方案（快速恢复）**：
```
✅ 重启服务（谨慎使用）
✅ 扩容（增加实例）
✅ 降级（关闭非核心功能）
✅ 限流（保护系统）
✅ 回滚（代码回滚）
```

**根本方案（彻底解决）**：
```
✅ 修复代码bug
✅ 优化SQL查询
✅ 调整JVM参数
✅ 优化系统配置
✅ 架构优化
```

### 第五步：总结复盘（5分钟）

**问题记录**：
```
✅ 问题描述
✅ 根本原因
✅ 解决方案
✅ 预防措施
✅ 经验总结
```

---

## 问题分类索引

### 🔴 紧急问题（P0）

**症状**：服务不可用、数据丢失、安全漏洞

**排查重点**：
- [ ] 服务是否完全宕机？
- [ ] 数据库是否可连接？
- [ ] 是否有安全攻击？
- [ ] 是否有数据损坏？

**快速恢复**：
1. 查看监控告警
2. 检查服务状态
3. 查看错误日志
4. 必要时重启服务

### 🟡 重要问题（P1）

**症状**：性能下降、部分功能异常、用户体验差

**排查重点**：
- [ ] 接口响应时间是否异常？
- [ ] 错误率是否上升？
- [ ] 是否有资源瓶颈？
- [ ] 是否有慢查询？

**排查方法**：
1. 查看APM监控
2. 分析慢请求
3. 检查数据库性能
4. 查看缓存命中率

### 🟢 一般问题（P2）

**症状**：偶发错误、性能轻微下降、告警频繁

**排查重点**：
- [ ] 是否有规律性？
- [ ] 是否影响核心功能？
- [ ] 是否需要优化？

---

## 常用排查工具

### Java应用排查

```bash
# 查看Java进程
jps -lvm

# 查看线程堆栈
jstack <pid>

# 查看堆内存
jmap -heap <pid>
jmap -histo <pid>

# 查看GC情况
jstat -gc <pid> 1000 10

# 生成堆转储
jmap -dump:format=b,file=heap.hprof <pid>
```

### 系统资源排查

```bash
# CPU使用率
top -H -p <pid>
htop

# 内存使用
free -h
cat /proc/meminfo

# 磁盘IO
iostat -x 1
iotop

# 网络连接
netstat -antp | grep <port>
ss -antp | grep <port>
```

### 日志分析

```bash
# 实时查看日志
tail -f application.log
tail -f -n 1000 application.log | grep ERROR

# 搜索关键字
grep -r "Exception" logs/
grep -A 10 -B 10 "ERROR" application.log

# 统计错误数量
grep "ERROR" application.log | wc -l
grep "ERROR" application.log | grep -o "Exception.*" | sort | uniq -c
```

### 数据库排查

```sql
-- 查看当前连接
SHOW PROCESSLIST;

-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query%';
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 查看锁等待
SELECT * FROM information_schema.innodb_locks;
SELECT * FROM information_schema.innodb_lock_waits;

-- 查看表状态
SHOW TABLE STATUS LIKE 'table_name';
```

### Redis排查

```bash
# 连接Redis
redis-cli -h <host> -p <port>

# 查看连接数
CLIENT LIST

# 查看内存使用
INFO memory

# 查看慢查询
SLOWLOG GET 10

# 查看大key
redis-cli --bigkeys

# 查看热key
redis-cli --hotkeys
```

---

## 快速命令速查

### 查看进程和端口

```bash
# 根据端口查进程
lsof -i :8080
netstat -tlnp | grep 8080
ss -tlnp | grep 8080

# 根据进程名查端口
ps aux | grep java
jps -lvm
```

### 查看系统资源

```bash
# CPU
top
htop
vmstat 1

# 内存
free -h
cat /proc/meminfo

# 磁盘
df -h
du -sh *
iostat -x 1

# 网络
ifconfig
netstat -i
iftop
```

### 日志分析

```bash
# 实时日志
tail -f app.log

# 最近100行
tail -n 100 app.log

# 搜索关键字
grep "ERROR" app.log
grep -A 10 "Exception" app.log

# 统计
grep "ERROR" app.log | wc -l
awk '{print $1}' app.log | sort | uniq -c
```

---

## 问题排查检查清单

### 应用层检查

- [ ] 服务是否正常运行？（进程是否存在）
- [ ] 端口是否监听？（netstat -tlnp）
- [ ] 健康检查是否通过？（/health接口）
- [ ] 日志是否有异常？（ERROR、Exception）
- [ ] JVM参数是否合理？（-Xmx、-Xms）
- [ ] 线程数是否正常？（jstack查看）
- [ ] 连接池是否满？（数据库、Redis）

### 系统层检查

- [ ] CPU使用率是否正常？（< 80%）
- [ ] 内存使用率是否正常？（< 80%）
- [ ] 磁盘空间是否充足？（> 20%）
- [ ] 磁盘IO是否正常？（iostat）
- [ ] 网络连接数是否正常？（netstat）
- [ ] 系统负载是否正常？（load average < CPU核心数）

### 中间件检查

- [ ] 数据库连接是否正常？（SHOW PROCESSLIST）
- [ ] 是否有慢查询？（慢查询日志）
- [ ] Redis连接是否正常？（CLIENT LIST）
- [ ] 缓存命中率是否正常？（> 80%）
- [ ] 消息队列是否积压？（队列长度）
- [ ] Nginx是否正常？（nginx -t）

---

## 📚 相关文档

- [系统设计方法论](../系统设计方法论.md)
- [高并发系统设计](../高并发系统设计.md)
- [性能监控与系统优化](../../11_性能优化/性能监控与系统优化.md)
- [JVM调优实战](../../11_性能优化/JVM调优实战.md)

---

**最后更新**: 2025-10-29  
**文档状态**: ✅ 框架已搭建，内容持续完善中

💡 **记住**: 生产环境问题排查要快、准、稳！先恢复服务，再深入分析！


# Linux与运维面试题

> Java后端必问Linux/运维知识：常用命令/问题排查/Shell脚本/进程管理

---

## 📋 目录

1. [常用命令](#1-常用命令)
2. [问题排查](#2-问题排查)
3. [网络与安全](#3-网络与安全)
4. [Shell脚本场景](#4-shell脚本场景)
5. [面试题速查](#5-面试题速查)

---

## 1. 常用命令

**Q: 文件查找/文本搜索？**

```bash
# find: 按文件名/大小/时间查找
find /app -name "*.log" -mtime +7        # 7天前的日志
find /app -name "*.log" -size +100M      # 大于100MB
find /app -type f -name "*.java" | wc -l # 统计Java文件数

# grep: 文本搜索(常配合管道)
grep -rn "ERROR" /app/logs/               # 递归+行号搜索ERROR
grep -c "Exception" app.log               # 统计异常出现次数
grep -v "INFO" app.log | grep "ERROR"     # 排除INFO只看ERROR

# awk: 文本处理
awk '{print $1, $4}' access.log           # 打印第1、4列
awk -F',' '{sum+=$2} END{print sum}' data.csv  # 求和

# sed: 文本替换
sed -i 's/old/new/g' config.yml           # 全局替换
sed -n '10,20p' file.txt                  # 打印10-20行
```

**Q: 如何快速查看大文件？**

```bash
head -n 100 file.log    # 前100行
tail -n 100 file.log    # 后100行
tail -f file.log        # 实时追踪(看日志最常用)
less file.log           # 分页查看(可搜索/前后翻)
wc -l file.log          # 统计行数
```

---

## 2. 问题排查

**Q: CPU飙高怎么排查？**

```bash
# 步骤1: 找到CPU高的Java进程
top -c          # 按P按CPU排序，找到PID

# 步骤2: 找到CPU高的线程
top -Hp <PID>   # 查看进程内各线程CPU，找到TID

# 步骤3: 线程ID转16进制
printf "%x\n" <TID>    # 如TID=12345 → 0x3039

# 步骤4: dump线程堆栈找对应线程
jstack <PID> | grep -A 30 "0x3039"   # 看这个线程在执行什么代码

# 或者用arthas(更方便)
arthas → thread -n 3   # 直接看CPU最高的3个线程
```

**Q: 内存溢出(OOM)怎么排查？**

```bash
# 步骤1: 确认OOM类型
dmesg | grep -i "out of memory"    # 系统级OOM
jstat -gcutil <PID> 1000           # 看各区域使用率

# 步骤2: 导出堆转储
jmap -dump:format=b,file=heap.hprof <PID>
# 或JVM启动参数: -XX:+HeapDumpOnOutOfMemoryError

# 步骤3: MAT/VisualVM分析
# 找到占用最大的对象 → 查看GC Root引用链 → 定位泄漏点

# 常见原因:
# 1. 静态集合无限增长
# 2. ThreadLocal未remove
# 3. 资源未关闭(Connection/Stream)
# 4. 线程无限创建(new Thread不shutdown)
```

**Q: 磁盘满怎么排查？**

```bash
df -h                  # 查看各挂载点使用率
du -sh /app/*          # 找大目录
du -sh /app/logs/* | sort -rh | head -10  # 最大的10个文件/目录

# 常见原因:
# 日志文件过大 → logrotate切割 / 定时清理
# 已删除文件被进程持有 → lsof | grep deleted → kill进程
# Docker镜像/容器占满 → docker system prune
```

**Q: 线上接口慢怎么排查？**

```
排查链路:
  1. 网络层: ping/telnet/mtr → 排除网络延迟
  2. 应用层: APM(SkyWalking/Prometheus)看耗时分布
  3. 代码层: arthas trace命令逐层耗时
     trace com.example.OrderService createOrder
  4. 数据库: 慢查询日志 + EXPLAIN分析执行计划
  5. 外部依赖: HTTP调用/Redis/MQ超时
  6. JVM: GC频繁(jstat -gcutil) → STW导致停顿
  7. 锁竞争: jstack看线程BLOCKED状态
```

**Q: 如何排查线程死锁？**

```bash
jstack <PID> | grep -A 20 "Found .* deadlock"
# 或
jcmd <PID> Thread.print

# arthas
thread -b    # 直接找阻塞其他线程的线程

# 日志特征:
# "Thread-1" BLOCKED (on object monitor)
# waiting to lock <0x000000076b> (a java.lang.Object)
# held by "Thread-2"
```

---

## 3. 网络与安全

**Q: 常用网络排查命令？**

```bash
netstat -tlnp          # 查看监听端口
netstat -an | grep ESTABLISHED | wc -l  # 当前连接数
ss -tlnp               # netstat替代(更快)

tcpdump -i eth0 port 8080 -nn -w capture.pcap  # 抓包

# 连接状态分析
netstat -an | awk '/tcp/ {print $NF}' | sort | uniq -c | sort -rn
# TIME_WAIT过多 → 调整tcp_tw_reuse/短连接改长连接
```

**Q: 防火墙配置？**

```bash
# firewalld(CentOS 7+)
firewall-cmd --list-ports                    # 查看开放端口
firewall-cmd --add-port=8080/tcp --permanent  # 开放端口
firewall-cmd --reload                         # 生效

# iptables
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT  # 放行8080
iptables -L -n                                   # 查看规则
```

---

## 4. Shell脚本场景

**Q: 写一个监控脚本：CPU超过80%发告警？**

```bash
#!/bin/bash
THRESHOLD=80
HOSTNAME=$(hostname)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
CPU_INT=${CPU_USAGE%.*}

if [ "$CPU_INT" -gt "$THRESHOLD" ]; then
    curl -s "https://api.dingtalk.com/robot/send" \
         -H "Content-Type: application/json" \
         -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"告警: ${HOSTNAME} CPU=${CPU_USAGE}%\"}}"
fi
```

**Q: 写一个日志清理脚本：保留最近7天？**

```bash
#!/bin/bash
LOG_DIR="/app/logs"
DAYS=7

# 方法1: find删除
find "$LOG_DIR" -name "*.log" -mtime +${DAYS} -exec rm -f {} \;

# 方法2: logrotate配置(更规范)
# /etc/logrotate.d/app
# /app/logs/*.log {
#     daily
#     rotate 7
#     compress
#     missingok
#     notifempty
#     copytruncate  # 不停止应用的情况下切割
# }
```

**Q: 统计Nginx访问日志中IP出现次数Top10？**

```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 说明:
# awk '{print $1}'  → 取第一列(IP)
# sort              → 排序(为uniq准备)
# uniq -c           → 去重并计数
# sort -rn          → 按数字倒序
# head -10          → 取前10
```

---

## 5. 面试题速查

**Q1: CPU高排查？**
```
top找进程 → top -Hp找线程 → printf %x转16进制 → jstack看堆栈
```

**Q2: OOM排查？**
```
jstat看GC → jmap -dump导出 → MAT找GC Root引用链
```

**Q3: 磁盘满排查？**
```
df -h看挂载点 → du -sh找大目录 → lsof找已删除未释放文件
```

**Q4: 死锁排查？**
```
jstack | grep deadlock 或 arthas thread -b
```

**Q5: TIME_WAIT过多？**
```
tcp_tw_reuse=1 / 短连接改长连接 / 调整tcp_max_tw_buckets
```

**Q6: 统计日志Top IP？**
```
awk '{print $1}' | sort | uniq -c | sort -rn | head
```

**Q7: 端口被占用？**
```
netstat -tlnp | grep :8080 或 lsof -i:8080
```

**Q8: 查看Java进程JVM参数？**
```
jinfo -flags <PID> 或 jcmd <PID> VM.flags
```

---

*最后更新: 2026-07-14*

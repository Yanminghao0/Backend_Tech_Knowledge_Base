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

## 6. 补充面试题

**Q: 文件权限rwx详解？**

```
drwxr-xr-- 2 user group 4096 Jul 14 dir/

第1位: d=目录, -=文件, l=链接
第2-4位: 所有者权限 rwx (读/写/执行)
第5-7位: 所属组权限 r-x
第8-10位: 其他用户 r--

数字表示: r=4, w=2, x=1
  rwx = 7, r-x = 5, r-- = 4
  chmod 755 = rwxr-xr-x
  chmod 644 = rw-r--r--

特殊权限:
  SUID(4): 执行时以文件所有者身份执行 (如/usr/bin/passwd)
  SGID(2): 在目录下创建的文件继承目录的组
  Sticky(1): 只有文件所有者能删除 (如/tmp)
```

**Q: 如何查看系统负载？**

```bash
# load average: 1分钟/5分钟/15分钟的平均负载
uptime           # load average: 1.50, 1.20, 0.80
# 负载 > CPU核数 → 过载

# CPU核数
nproc            # 如8

# vmstat: 查看CPU/内存/IO综合状态
vmstat 1 5       # 每秒1次共5次
# r列: 运行队列(>CPU核数说明CPU不够)
# us: 用户态CPU, sy: 内核态, wa: IO等待(高说明磁盘瓶颈)
# bi/bo: 块设备读写(高说明IO密集)

# iostat: 磁盘IO
iostat -x 1      # %util高说明磁盘满载
```

**Q: 如何查看内存使用？**

```bash
free -h
#              total        used        free      shared  buff/cache   available
# Mem:           16G         8G        2G        512M        6G        7G
# available = free + 可回收的buff/cache
# Linux会把空闲内存用作文件缓存(buff/cache), 需要时自动释放

# 进程内存排序
ps aux --sort=-%mem | head -10

# 查看进程的内存映射
pmap <PID> | sort -rn | head
```

**Q: 日志分析常用命令组合？**

```bash
# 1. 统计各HTTP状态码数量
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# 2. 找出4xx/5xx错误的请求
awk '$9 >= 400 {print $7, $9}' access.log | sort | uniq -c | sort -rn | head -20

# 3. 统计每秒QPS
awk '{print $4}' access.log | cut -c2-20 | sort | uniq -c

# 4. 找出响应最慢的10个请求
awk '{print $NF, $7}' access.log | sort -rn | head -10

# 5. 实时过滤错误日志并高亮
tail -f app.log | grep --color=always "ERROR\|Exception"

# 6. 多文件搜索关键字
grep -rn "OutOfMemoryError" /app/logs/ --include="*.log"

# 7. 按时间范围提取日志
sed -n '/2026-07-14 10:00/,/2026-07-14 11:00/p' app.log

# 8. 去重统计访问IP的地理分布
awk '{print $1}' access.log | sort -u | while read ip; do
    echo "$ip $(curl -s ipinfo.io/$ip/region)"
done
```

**Q: 环境变量配置？**

```bash
# 临时生效(当前终端)
export JAVA_HOME=/usr/lib/jvm/java-17
export PATH=$JAVA_HOME/bin:$PATH

# 永久生效(当前用户)
echo 'export JAVA_HOME=/usr/lib/jvm/java-17' >> ~/.bashrc
source ~/.bashrc

# 全局生效(所有用户)
echo 'export JAVA_HOME=/usr/lib/jvm/java-17' >> /etc/profile

# 查看环境变量
env              # 所有
echo $JAVA_HOME  # 单个
```

**Q: crontab定时任务？**

```bash
# 格式: 分 时 日 月 周 命令
crontab -e       # 编辑
crontab -l       # 查看

# 常用示例:
*/5 * * * * /script/health-check.sh        # 每5分钟
0 2 * * * /script/backup.sh                # 每天凌晨2点
0 0 1 * * /script/cleanup.sh               # 每月1号
0 9-18 * * 1-5 /script/workday.sh          # 工作日9-18点每小时

# 注意:
# 1. 路径用绝对路径(crontab环境变量不全)
# 2. 日志重定向: >> /var/log/cron.log 2>&1
# 3. 错误处理: 脚本加 set -e
```

**Q: systemd服务管理？**

```bash
systemctl status nginx          # 查看状态
systemctl start nginx           # 启动
systemctl stop nginx            # 停止
systemctl restart nginx         # 重启
systemctl enable nginx          # 开机自启
systemctl disable nginx         # 禁用自启
systemctl daemon-reload         # 修改service文件后重新加载

# 查看日志
journalctl -u nginx -f          # 实时日志
journalctl -u nginx --since today
```

---

## 7. 更多面试题

**Q: 如何排查线上Java进程突然消失？**

```
可能原因:
  1. OOM Killer: dmesg | grep -i "killed process"
     → 系统内存不足, OS杀掉Java进程
     → 解决: 增加内存/限制JVM堆/Xmx

  2. 容器OOM: kubectl describe pod / docker inspect
     → 容器内存limit太低
     → 解决: 调整resources.limits.memory

  3. 健康检查失败: K8s liveness probe连续失败 → kill
     → kubectl describe pod看Events

  4. 外部kill: 脚本/人为 kill -9
     → 查看bash_history/审计日志

排查:
  1. dmesg | grep -i "killed process"
  2. kubectl describe pod <name>
  3. 应用日志最后几行(是否OOM/异常)
  4. GC日志(是否Full GC导致STW超时)
```

**Q: Java应用在线上CPU正常但响应慢？**

```
CPU不高但慢的常见原因:
  1. IO等待: 数据库慢查询/磁盘IO高
     → iostat -x看%util, SHOW PROCESSLIST
  2. 线程阻塞: 锁竞争/外部调用超时
     → jstack看WAITING/BLOCKED线程
  3. GC停顿: 频繁Full GC(STW)
     → jstat -gcutil, GC日志
  4. 网络延迟: 跨机房调用/DNS解析慢
     → ping/mtr排查
  5. 连接池满: 请求排队等待
     → HikariCP监控/Druid监控
  6. 线程池满: 任务排队
     → 自定义线程池监控
```

**Q: 生产环境发布后出问题怎么回滚？**

```
快速回滚:
  1. K8s: kubectl rollout undo deployment/app --to-revision=N
  2. 虚机: 切换Nginx upstream到上一版本(蓝绿发布)
  3. 数据库: 如有DDL需提前准备回滚SQL
  4. 配置: Nacos配置回滚(版本历史)

回滚注意事项:
  1. 数据兼容: 新版本可能已写入新格式数据 → 回滚后不兼容
  2. DDL: 加列可以回滚, 删列/改类型不可回滚
  3. 消息: 已发送的消息无法撤回(需幂等)
  4. 缓存: 新版本可能写入新格式缓存 → flush

最佳实践: 金丝雀发布(先5%流量验证) → 全量
```

---

*最后更新: 2026-07-14*

# Hadoop生态概览

> HDFS分布式存储、MapReduce计算模型、YARN资源调度、Hive数据仓库、HBase列式存储的完整生态体系

---

## 📋 目录

1. [Hadoop概述](#1-hadoop概述)
2. [HDFS分布式文件系统](#2-hdfs分布式文件系统)
3. [MapReduce计算模型](#3-mapreduce计算模型)
4. [YARN资源调度](#4-yarn资源调度)
5. [Hive数据仓库](#5-hive数据仓库)
6. [HBase列式存储](#6-hbase列式存储)
7. [面试题速查](#7-面试题速查)

---

## 1. Hadoop概述

```
Hadoop三大核心组件：

  ┌──────────────────────────────────────────────────┐
  │  HDFS    │  MapReduce  │  YARN                   │
  │  存储     │  计算        │  资源调度               │
  │  分布式   │  分而治之    │  统一资源管理           │
  └──────────────────────────────────────────────────┘

Hadoop生态圈：
  HDFS (存储) → MapReduce (计算) → YARN (调度)
    ↓
  Hive (SQL on Hadoop)
  HBase (NoSQL on Hadoop)
  Pig (脚本语言)
  Sqoop (数据导入导出)
  Flume (日志采集)
  Oozie (工作流调度)
  ZooKeeper (协调服务)
  Spark (内存计算，逐步替代MR)
  Flink (流计算)
```

```xml
<!-- Maven依赖 -->
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-client</artifactId>
    <version>3.3.6</version>
</dependency>
<dependency>
    <groupId>org.apache.hadoop</groupId>
    <artifactId>hadoop-hdfs</artifactId>
    <version>3.3.6</version>
</dependency>
```

---

## 2. HDFS分布式文件系统

### 2.1 架构

```
HDFS Master-Slave架构：

  ┌─────────────────────────────────────────────────────┐
  │                    NameNode (Master)                 │
  │  ├── 文件目录树 (FSImage + EditLog)                  │
  │  ├── Block映射表 (Block → DataNode列表)              │
  │  ├── 心跳管理 (接收DataNode心跳)                     │
  │  └── 副本放置策略                                   │
  └──────────────┬──────────────────────────────────────┘
                 │ 心跳 + Block Report
     ┌───────────┼───────────┐
     ↓           ↓           ↓
  ┌──────┐  ┌──────┐  ┌──────┐
  │ DN1  │  │ DN2  │  │ DN3  │
  │ Block │  │ Block │  │ Block │
  │ 128MB │  │ 128MB │  │ 128MB │
  └──────┘  └──────┘  └──────┘
  DataNode (Slave)

  Secondary NameNode: 定期合并FSImage+EditLog（非热备）
```

### 2.2 核心概念

```java
// HDFS文件操作
public class HDFSExample {

    private static FileSystem getFileSystem() throws Exception {
        Configuration conf = new Configuration();
        conf.set("fs.defaultFS", "hdfs://namenode:9000");
        return FileSystem.get(conf);
    }

    // 上传文件
    public static void uploadFile(String localPath, String hdfsPath) throws Exception {
        FileSystem fs = getFileSystem();
        fs.copyFromLocalFile(new Path(localPath), new Path(hdfsPath));
        fs.close();
    }

    // 下载文件
    public static void downloadFile(String hdfsPath, String localPath) throws Exception {
        FileSystem fs = getFileSystem();
        fs.copyToLocalFile(new Path(hdfsPath), new Path(localPath));
        fs.close();
    }

    // 创建目录
    public static void mkdir(String hdfsPath) throws Exception {
        FileSystem fs = getFileSystem();
        fs.mkdirs(new Path(hdfsPath));
        fs.close();
    }

    // 列出文件
    public static void listFiles(String hdfsPath) throws Exception {
        FileSystem fs = getFileSystem();
        FileStatus[] statuses = fs.listStatus(new Path(hdfsPath));
        for (FileStatus status : statuses) {
            System.out.println(
                (status.isDirectory() ? "DIR " : "FILE") + " " +
                status.getPath().getName() + " " +
                status.getLen() + " " +
                status.getReplication()
            );
        }
        fs.close();
    }
}
```

```
HDFS核心参数：

  Block大小：128MB（默认），大文件场景可设256MB
  副本数：3（默认）
  心跳间隔：3秒
  Block Report间隔：6小时

  副本放置策略（机架感知）：
    副本1 → 本机架节点A
    副本2 → 不同机架节点B
    副本3 → 节点B同机架节点C
    → 容错性 + 网络效率平衡
```

### 2.3 HDFS写流程

```
写流程：
  1. Client → NameNode: 请求创建文件
  2. NameNode检查权限和目录，返回可写的DataNode列表
  3. Client → DataNode1: 建立pipeline
  4. DataNode1 → DataNode2 → DataNode3: pipeline链式连接
  5. Client将数据分成Packet(64KB)，流式写入pipeline
  6. 各DataNode返回ACK
  7. 所有副本写入完成，Client关闭文件
  8. Client → NameNode: 关闭文件

  ┌───────┐     ┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐
  │Client │────→│ DN1  │────→│ DN2  │────→│ DN3  │     │ NN   │
  └───────┘     └──────┘     └──────┘     └──────┘     └──────┘
     │  Packet流     │  Packet流     │                  ↑
     └──────────────────────────────────────────────────┘
                        ACK回传
```

---

## 3. MapReduce计算模型

### 3.1 编程模型

```java
// WordCount — MapReduce经典案例
public class WordCount {

    public static class TokenizerMapper
            extends Mapper<LongWritable, Text, Text, IntWritable> {

        private final static IntWritable one = new IntWritable(1);
        private Text word = new Text();

        @Override
        protected void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {
            // value = 一行文本
            String line = value.toString();
            StringTokenizer tokenizer = new StringTokenizer(line);
            while (tokenizer.hasMoreTokens()) {
                word.set(tokenizer.nextToken());
                context.write(word, one);  // 输出 <word, 1>
            }
        }
    }

    public static class IntSumReducer
            extends Reducer<Text, IntWritable, Text, IntWritable> {

        private IntWritable result = new IntWritable();

        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context)
                throws IOException, InterruptedException {
            int sum = 0;
            for (IntWritable val : values) {
                sum += val.get();
            }
            result.set(sum);
            context.write(key, result);  // 输出 <word, count>
        }
    }

    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "word count");
        job.setJarByClass(WordCount.class);
        job.setMapperClass(TokenizerMapper.class);
        job.setCombinerClass(IntSumReducer.class);  // Combiner本地预聚合
        job.setReducerClass(IntSumReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
```

### 3.2 Shuffle机制

```
MapReduce执行流程：

  ┌─────────┐    ┌───────────┐    ┌──────────┐    ┌─────────┐
  │  Input  │───→│   Map     │───→│ Shuffle  │───→│  Reduce │
  │ Format  │    │  (用户)    │    │ (框架)   │    │  (用户) │
  └─────────┘    └───────────┘    └──────────┘    └─────────┘
                       │               │
                  Partition          Sort
                  (按Key分区)      (Key排序)
                       │               │
                  Spill             Merge
                  (写磁盘)         (合并文件)

  Shuffle详细过程：
  1. Map端输出 → 环形缓冲区(100MB, 80%阈值spill)
  2. Partitioner分区 → 按Key的hash%reduce数
  3. Sort排序 → 按Key排序
  4. Spill to disk → 写入临时文件
  5. Merge → 合并所有spill文件
  6. Combiner(可选) → 本地预聚合减少传输量
  7. Reduce端拉取 → HTTP拉取Map端输出
  8. Merge → 合并多Map端数据
  9. GroupingComparator → 按Key分组
  10. Reduce处理

  ┌────────────────────────────────────────────┐
  │  Shuffle是MR性能关键！                     │
  │  - 数据量大时Shuffle产生大量磁盘IO          │
  │  - Combiner可减少80%+传输量                 │
  │  - 压缩Map输出可减少网络传输                │
  │  - Spark的Shuffle机制借鉴MR但优化很多       │
  └────────────────────────────────────────────┘
```

---

## 4. YARN资源调度

### 4.1 架构

```
YARN (Yet Another Resource Negotiator)：

  ┌─────────────────────────────────────────────────┐
  │              ResourceManager (RM)                │
  │  ├── Scheduler: 资源调度（容量/公平调度器）      │
  │  └── ApplicationsManager: 任务管理              │
  └──────────┬──────────────────────────────────────┘
             │
     ┌───────┴────────┐
     ↓                ↓
  ┌──────────┐    ┌──────────┐
  │  NM (1)  │    │  NM (2)  │  ...
  │ NodeMgr  │    │ NodeMgr  │
  │ ├── Container│  ├── Container
  │ └── AM    │  │ └── AM   │
  └──────────┘    └──────────┘

  ResourceManager: 全局资源管理
  NodeManager: 单节点资源管理+Container生命周期
  ApplicationMaster(AM): 单个应用的任务调度
  Container: 资源隔离单元(CPU+内存)
```

### 4.2 调度器

```
YARN三种调度器：

1. FIFO Scheduler（先进先出）
   ┌───┬───┬───┬───┐
   │ J1│ J2│ J3│ J4│  按提交顺序执行
   └───┴───┴───┴───┘
   缺点：小任务可能被大任务阻塞

2. Capacity Scheduler（容量调度器，默认）
   ┌──────────────────────────────┐
   │      集群总资源               │
   ├──────────────┬───────────────┤
   │  生产队列60%  │  开发队列40%   │
   ├──────┬───────┼───────┬───────┤
   │ 高优 │ 低优  │ 离线  │ 临时  │
   │ 40%  │ 20%  │ 30%   │ 10%   │
   └──────┴───────┴───────┴───────┘
   多队列，队列内FIFO，支持弹性容量

3. Fair Scheduler（公平调度器）
   ┌──────────────────────────────┐
   │      集群总资源               │
   ├──────────────┬───────────────┤
   │  Job A 50%   │  Job B 50%     │
   └──────────────┴───────────────┘
   所有应用公平分享资源
   新提交应用立即获得资源
```

```yaml
# capacity-scheduler.xml
yarn.scheduler.capacity.maximum-applications: 10000
yarn.scheduler.capacity.maximum-am-resource-percent: 0.1

# 队列配置
yarn.scheduler.capacity.root.queues: production,development
yarn.scheduler.capacity.root.production.capacity: 60
yarn.scheduler.capacity.root.development.capacity: 40
yarn.scheduler.capacity.root.production.maximum-capacity: 80
```

---

## 5. Hive数据仓库

### 5.1 架构

```
Hive架构：

  ┌──────────┐     ┌──────────────┐     ┌──────────┐
  │  Client  │────→│  Hive Server │────→│ Driver   │
  │ (JDBC/   │     │  (Thrift)    │     │ (编译执行)│
  │  CLI/    │     └──────────────┘     └────┬─────┘
  │  Beeline)│                               │
  └──────────┘                    ┌──────────┴──────────┐
                                  ↓                     ↓
                            ┌──────────┐         ┌───────────┐
                            │ Metastore│         │  MapReduce │
                            │ (MySQL)  │         │  /Spark/Tez│
                            └──────────┘         └───────────┘
                                                  ↓
                                            ┌──────────┐
                                            │   HDFS    │
                                            └──────────┘

  Metastore: 存储表结构、分区、列类型等元数据
  Driver: 解析SQL → 生成AST → 逻辑计划 → 物理计划 → MR/Spark任务
```

### 5.2 HiveQL实战

```sql
-- 创建内部表
CREATE TABLE IF NOT EXISTS user_log (
    user_id BIGINT,
    action STRING,
    ts TIMESTAMP
)
PARTITIONED BY (dt STRING)  -- 分区表
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE;

-- 创建外部表（推荐，删除表不删数据）
CREATE EXTERNAL TABLE IF NOT EXISTS user_log_ext (
    user_id BIGINT,
    action STRING,
    ts TIMESTAMP
)
PARTITIONED BY (dt STRING)
STORED AS ORC;  -- 列式存储，压缩+查询快

-- 加载数据
LOAD DATA INPATH '/user/data/20260713.log' 
INTO TABLE user_log PARTITION (dt='2026-07-13');

-- 分区修复（自动加载HDFS目录数据）
MSCK REPAIR TABLE user_log_ext;

-- 聚合查询
SELECT
    dt,
    action,
    COUNT(*) AS cnt,
    COUNT(DISTINCT user_id) AS uv
FROM user_log
WHERE dt >= '2026-07-01'
GROUP BY dt, action
ORDER BY dt, cnt DESC;

-- JOIN优化：小表JOIN大表
SELECT /*+ MAPJOIN(dim_city) */  -- MapJoin: 小表加载到内存
    u.user_id,
    u.action,
    c.city_name
FROM user_log u
JOIN dim_city c ON u.city_id = c.city_id;
```

```
Hive文件格式对比：

  格式        压缩  查询  写入  适用场景
  TEXTFILE    否    慢    快    原始数据/临时
  SEQUENCE    否    中    中    不推荐
  RCFILE      是    中    慢    早期列存(过时)
  ORC         是    快    中    ★推荐(默认)
  PARQUET     是    快    中    ★推荐(跨生态)
```

---

## 6. HBase列式存储

### 6.1 架构

```
HBase架构：

  ┌──────────────────────────────────────────────────┐
  │                 HMaster                            │
  │  ├── 表/Region管理                                 │
  │  ├── 负载均衡                                      │
  │  └── 元数据管理                                    │
  └──────────┬───────────────────────────────────────┘
             │
     ┌───────┴────────────────┐
     ↓                        ↓
  ┌──────────────┐     ┌──────────────┐
  │ RegionServer │     │ RegionServer │  ...
  │  ├── Region1 │     │  ├── Region3 │
  │  │   ├── MemStore │  │   ├── MemStore
  │  │   └── HFile    │  │   └── HFile
  │  ├── Region2 │     │  ├── Region4 │
  │  └── WAL     │     │  └── WAL     │
  └──────┬───────┘     └──────────────┘
         │
  ┌──────┴──────┐
  │   ZooKeeper  │  协调服务
  │   HDFS       │  底层存储
  └─────────────┘

  Region: HBase分片单元，按RowKey范围切分
  MemStore: 写缓冲区(内存)，满了flush到HFile
  HFile: HDFS上的列式存储文件
  WAL: Write-Ahead Log，故障恢复用
```

### 6.2 Java操作

```java
public class HBaseExample {

    private static Connection getConnection() throws IOException {
        Configuration config = HBaseConfiguration.create();
        config.set("hbase.zookeeper.quorum", "zk1,zk2,zk3");
        config.set("hbase.zookeeper.property.clientPort", "2181");
        return ConnectionFactory.createConnection(config);
    }

    // 建表
    public static void createTable() throws IOException {
        try (Connection conn = getConnection();
             Admin admin = conn.getAdmin()) {

            TableDescriptorBuilder tableDesc = TableDescriptorBuilder
                .newBuilder(TableName.valueOf("user_action"));

            ColumnFamilyDescriptor cf = ColumnFamilyDescriptorBuilder
                .newBuilder(Bytes.toBytes("info"))
                .setMaxVersions(3)            // 保留3个版本
                .setTimeToLive(86400 * 30)    // TTL 30天
                .setCompressionType(Compression.Algorithm.SNAPPY)
                .build();

            tableDesc.setColumnFamily(cf);
            admin.createTable(tableDesc.build());
        }
    }

    // 插入数据
    public static void putData() throws IOException {
        try (Connection conn = getConnection();
             Table table = conn.getTable(TableName.valueOf("user_action"))) {

            // RowKey设计: 反转userId + 时间戳 → 避免热点
            Put put = new Put(Bytes.toBytes("1001_20260713150000"));
            put.addColumn(
                Bytes.toBytes("info"),
                Bytes.toBytes("action"),
                Bytes.toBytes("click")
            );
            put.addColumn(
                Bytes.toBytes("info"),
                Bytes.toBytes("amount"),
                Bytes.toBytes("99.9")
            );
            table.put(put);
        }
    }

    // 扫描查询
    public static void scanData() throws IOException {
        try (Connection conn = getConnection();
             Table table = conn.getTable(TableName.valueOf("user_action"))) {

            Scan scan = new Scan();
            scan.setRowPrefixFilter(Bytes.toBytes("1001_"));  // 前缀扫描
            scan.setLimit(100);

            try (ResultScanner scanner = table.getScanner(scan)) {
                for (Result result : scanner) {
                    String rowKey = Bytes.toString(result.getRow());
                    String action = Bytes.toString(
                        result.getValue(Bytes.toBytes("info"), Bytes.toBytes("action"))
                    );
                    System.out.println(rowKey + " → " + action);
                }
            }
        }
    }
}
```

```
RowKey设计原则：
  1. 散列性 — 避免热点(不要用自增ID或时间戳开头)
  2. 单调性 — 范围查询效率
  3. 长度控制 — 10-100字节
  4. 常用查询条件编码到RowKey

  常见技巧：
    反转 → 反转userId前缀，打散热点
    Hash → userId取hash前缀 + 原始userId
    Salt → 预分区数 + RowKey
```

---

## 7. 面试题速查

**Q1: HDFS的Block为什么默认128MB？**

```
1. 减少元数据量 — NameNode内存有限，Block大则Block数少
2. 减少寻址时间 — 寻址时间/传输时间比例降低
3. 适合大文件 — HDFS设计目标是大文件批处理
小文件问题：大量小文件会撑爆NameNode内存
  每个文件/Block约150字节元数据
  → HAR/SequenceFile/合并小文件
```

**Q2: MapReduce的Shuffle过程？**

```
Map端：输出→环形缓冲区→Partition→Sort→Spill→Combiner→Merge
Reduce端：拉取→Merge→Group→Reduce

Shuffle是性能瓶颈：
  磁盘IO：spill和merge
  网络IO：Reduce拉取Map输出
优化：Combiner、压缩、增大缓冲区、调整Partition
```

**Q3: YARN的调度器有哪些？**

```
FIFO：简单但小任务被阻塞
Capacity：多队列，队列内FIFO，容量百分比，生产推荐
Fair：所有应用公平分享资源，适合多用户共享集群
```

**Q4: Hive内部表和外部表的区别？**

```
内部表(MANAGED)：Hive管理数据和元数据，DROP删除两者
外部表(EXTERNAL)：Hive只管元数据，DROP只删元数据不删数据
推荐用外部表 — 数据安全，可被多个计算引擎共享
```

**Q5: HBase的RowKey如何设计？**

```
三大原则：散列性(防热点) + 单调性(范围查询) + 简短性
技巧：反转、Hash前缀、加盐
反面案例：时间戳开头 → 所有写集中到一个Region
```

**Q6: HBase vs Hive的区别？**

```
HBase：NoSQL数据库，实时读写，RowKey查询，毫秒级
Hive：数据仓库，批处理分析，SQL查询，分钟~小时级
定位不同：HBase适合在线服务，Hive适合离线分析
两者可互补：HBase做实时读写，Hive做离线分析
```

---

*最后更新：2026-07-13*

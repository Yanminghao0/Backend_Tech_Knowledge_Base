# Lucene原理深入

> Elasticsearch的底层引擎，倒排索引的极致工程实现

---

## 📋 目录

1. [Lucene概述](#1-lucene概述)
2. [倒排索引实现](#2-倒排索引实现)
3. [Segment与合并](#3-segment与合并)
4. [FST词典](#4-fst词典)
5. [面试要点](#5-面试要点)
6. [倒排索引写入流程详解](#6-倒排索引写入流程详解)
7. [Segment合并策略详解(TieredMergePolicy)](#7-segment合并策略详解tieredmergepolicy)
8. [Doc Values列式存储](#8-doc-values列式存储)
9. [BKD树空间索引](#9-bkd树空间索引)
10. [Near Real-Time搜索原理](#10-near-real-time搜索原理)

---

## 1. Lucene概述

```
Lucene = Apache开源全文搜索引擎库
ES = 分布式Lucene（Lucene + 分布式协调）

Lucene核心概念：
  - Document：文档（一条记录）
  - Field：字段（文档属性）
  - Term：词项（分词后的最小单元）
  - Segment：段（不可变的索引文件集合）
  - Index：索引（多个Segment组成）
```

---

## 2. 倒排索引实现

### 写入流程

```
1. 文档 → Analyzer分词 → Term列表
2. Term → Term Dictionary（词典）
3. Term → Posting List（倒排链表）
4. 文档原文 → Stored Fields（存储字段）
5. 排序/聚合字段 → Doc Values（列式存储）

文件结构：
  .si     Segment Info（段信息）
  .cfs    Compound File（段数据）
  .cfe    Compound File Entry（段数据索引）
  .liv    Live Documents（存活文档标记）
  .doc    Frequencies（词频）
  .pos    Positions（位置信息）
  .tim    Term Dictionary（词典）
  .tip    Term Index（词典索引FST）
  .fdt    Field Data（存储字段）
  .fdx    Field Index（存储字段索引）
  .dvd    Doc Values Data（列式数据）
  .dvm    Doc Values Metadata（列式元数据）
```

### Posting List压缩

```
Posting List存储格式：
  DocId列表：[1, 3, 7, 12, 15, 22, 30, 45, 70]

压缩方式：
  1. Delta编码：存差值 [1, 2, 4, 5, 3, 7, 8, 15, 25]
  2. Split+RoaringBitmap：分块存储，稀疏用数组，密集用Bitmap

效果：1亿DocId从约400MB压缩到约50MB
```

---

## 3. Segment与合并

### Segment不可变性

```
Segment一旦生成不可修改：
  - 查询无需加锁
  - 缓存友好（不需失效）
  - 删除 = 标记.del文件（物理删除在merge时）

写入 → refresh → 新Segment（1秒）
合并 → merge → 小Segment合并为大Segment
```

### Merge策略

```
Tiered Merge Policy（分层合并）：
  - 每层最多10个Segment
  - 当某层Segment数超过阈值，触发合并
  - 合并到上层（更大的Segment）
  - 最终形成金字塔结构

合并代价：
  - IO密集：读取多个Segment → 写入新Segment
  - CPU密集：重新构建索引结构
  - 影响：合并期间IO负载增加
```

### Force Merge

```json
// 强制合并为单个Segment（优化查询性能）
POST /my_index/_forcemerge?max_num_segments=1

// 适用：索引不再更新（日志类只读索引）
// 不适用：频繁更新的索引（合并后新Segment又会产生）
```

---

## 4. FST词典

### FST原理

```
FST (Finite State Transducer) 有限状态转换器

特点：
  - 共享前缀和后缀，极高压缩比
  - O(len(term))查询复杂度
  - 内存常驻（mmap）

示例：
  词汇: cat, can, dog, door

  FST结构:
       c → a → {n|t}
       d → o → {g|o → r}

  存储：原始15字节 → FST约7字节

效果：
  - 1亿Term的词典从约2GB压缩到约100MB
  - 全部加载到内存，查询极快
```

### Term Index → Term Dictionary → Posting List

```
查询流程：
  1. Term Index (.tip) → FST找到Term在Dictionary中的位置块
  2. Term Dictionary (.tim) → 在位置块中找到Term
  3. Posting List (.doc) → 获取DocId列表

Tip文件常驻内存，Tim文件mmap到内存，Doc按需读取
```

---

## 5. 面试要点

### Q1: Lucene的Segment为什么不可变？

```
1. 查询无需加锁 → 并发读性能高
2. 缓存友好 → 不需要失效缓存
3. 简化实现 → 不需要处理并发修改
4. 删除用标记 → merge时物理删除
```

### Q2: FST为什么能压缩词典？

```
1. 共享前缀：cat/can共享"ca"前缀
2. 共享后缀：dog/door共享"o"后缀
3. 最终状态机比原始字符串小很多
4. 1亿Term从2GB压缩到100MB
```

### Q3: ES的refresh和merge区别？

```
refresh：In-memory Buffer → Segment文件（1秒）
  - 让新写入的数据可被搜索
  - 生成小Segment

merge：多个小Segment → 大Segment
  - 减少Segment数量，提升查询性能
  - 物理删除标记为删除的文档
  - IO和CPU密集
```

### Q4: Doc Values和FieldCache的区别？

```
FieldCache（Lucene 6前，已废弃）：
  - 运行时从倒排索引构建，存JVM堆内存
  - 首次访问加载慢，导致Full GC
  - 可能OOM（字段基数大时）

Doc Values（Lucene 4+，默认启用）：
  - 写入时构建，磁盘持久化列式存储
  - mmap映射到进程地址空间，不占堆内存
  - 列式压缩，IO高效
  - 访问按需读取Page Cache

结论：Doc Values解决了FieldCache的内存和GC问题
```

### Q5: BKD树为什么比倒排索引更适合范围查询？

```
倒排索引做范围查询（如 age>=20 AND age<=30）：
  - 对范围内每个Term查Posting List再合并
  - 或全扫描所有DocId取值过滤
  - 范围越大效率越低

BKD树范围查询：
  - 多维空间递归切分
  - 剪枝：跳过与查询范围不相交的子树
  - 只访问相交的叶子节点
  - 复杂度O(n^(1-1/k))，远优于全扫描

ES自动路由：
  - range查询 → BKD树
  - term查询 → 倒排索引（FST）
  - 数值类型7.x+默认两者都建
```

### Q6: ES数据写入到可搜索经历了哪些阶段？

```
1. 写入In-memory Buffer + Translog（毫秒级）
2. refresh（默认1s）：Buffer → Segment(Page Cache)，可搜索
3. translog fsync（默认5s）：translog持久化到磁盘
4. flush（默认30min/512MB）：Segment fsync + 新commit点 + 清translog

关键区分：
  - refresh → 可搜索（不持久）
  - flush → 可持久化（断电不丢）
  - translog → 写入即记录，保证flush前数据可恢复
```

### Q7: TieredMergePolicy如何选择合并的Segment？

```
1. 按Segment大小分层（Tier）
2. 找到超过segments_per_tier(默认10)的层
3. 该层中选择合并代价最小的Segment组：
   - score = 合并总大小 / (删除比例 × reclaim_deletes_weight)
   - score最小（代价最低）的优先合并
4. 优先合并：
   - 删除比例高的Segment（回收空间）
   - 大小相近的Segment（合并效率高）
5. 合并后Segment进入更高Tier（更大层）
6. 超过max_merged_segment(5GB)的不参与合并
```

### Q8: 如何优化ES写入吞吐量？

```
1. 批量写入：bulk API，每批1000-5000文档
2. 调大refresh_interval（如30s）减少Segment生成
3. 导入期间副本数设为0
4. 禁用不必要的索引/Doc Values
5. translog调优：增大flush_threshold_size
6. 写入完成后force_merge（只读索引）

写入吞吐关键瓶颈：
  - refresh频率 → Segment数量 → merge压力
  - 副本同步 → 网络IO
  - translog fsync → 磁盘IO
```

---

## 6. 倒排索引写入流程详解

### 6.1 写入流水线

```
Document写入完整流程：

1. IndexWriter.write()
   ↓
2. Document → Analyzer分析链
   - CharFilter：字符过滤（如HTML剥离）
   - Tokenizer：分词（如StandardTokenizer）
   - TokenFilter：词项过滤（小写、停用词、词干）
   ↓
3. 构建IndexedField（每个需要索引的字段）
   - 生成Token Stream
   - 记录 Term + Position + Offset + Payload
   ↓
4. 写入DocumentsWriterPerThread（DWPT）
   - 每个线程一个DWPT，独立缓冲区
   - 避免写入锁竞争
   ↓
5. DWPT内存缓冲区构建
   - FieldsHash：字段哈希表（Field → Term → Posting）
   - 存储DocId、TermFreq、Position、Offset
   ↓
6. Flush触发条件
   - 内存达到ram_buffer_size（默认16MB）
   - 文档数达到max_buffered_docs
   - 显式commit()
   ↓
7. Flush：内存索引 → Segment文件
   - 对Term排序
   - 构建FST（Term Index）
   - 写入.tim/.tip/.doc/.pos等文件
   - 生成新Segment（不可变）
```

### 6.2 DWPT与线程并发

```
IndexWriter
  ├── DWPT-1 (Thread-1) → Segment-A
  ├── DWPT-2 (Thread-2) → Segment-B
  └── DWPT-3 (Thread-3) → Segment-C

特点：
  - 每个线程独立写入自己的DWPT，无锁竞争
  - Flush时各自生成独立Segment
  - 后续merge合并这些Segment

并发写入模型 = 多生产者 + 单Flush调度
  - DocumentsWriterThreadPool管理线程分配
  - Flush由IndexWriter统一调度
  - 同一时刻只有一个Flush执行（串行化Segment生成）
```

### 6.3 写入与持久化层次

```
写入层次（从内存到磁盘）：

1. In-memory Buffer（DWPT缓冲区）
   - 内存中，refresh后可被搜索

2. Segment File（refresh后）
   - 写入文件系统缓存（OS Page Cache）
   - 数据可见但未fsync，断电可能丢失

3. Commit Point（commit/flush后）
   - fsync到磁盘
   - 写入segments_N文件（提交点）
   - 断电不丢失

4. Translog（ES层，非Lucene）
   - 写入即记录translog
   - 用于崩溃恢复（重放未flush的数据）
   - translog默认每5秒fsync
```

---

## 7. Segment合并策略详解（TieredMergePolicy）

### 7.1 为什么需要合并

```
问题：refresh每秒生成新Segment
  → Segment数量持续增长
  → 查询需扫描所有Segment
  → 文件句柄、内存占用增加
  → 查询性能下降

解决：后台合并小Segment → 大Segment
  - 减少Segment总数
  - 物理删除已标记删除的文档
  - 合并后旧Segment文件被清理
```

### 7.2 TieredMergePolicy核心参数

```
TieredMergePolicy（ES默认）：

  segments_per_tier = 10
    每层允许的最大Segment数，超过触发合并

  max_merge_at_once = 10
    一次最多合并的Segment数

  floor_segment = 2MB
    小于此值的Segment视为floor_segment大小
    （防止微小Segment过多，统一提升到floor）

  max_merged_segment = 5GB
    单个Segment最大大小，超过不参与合并

  reclaim_deletes_weight = 2.0
    删除文档比例对合并的影响权重
    （删除比例高更倾向合并）

  max_merge_at_once_explicit = 30
    forceMerge时一次合并的最大数
```

### 7.3 分层合并算法

```
Segment按大小分层（示例）：

  Tier 0: < 50MB     （新生成的小Segment）
  Tier 1: 50MB-5GB   （合并后的中Segment）
  Tier 2: 5GB-50GB   （大Segment）
  Tier 3: > 50GB     （超大Segment，少参与合并）

合并触发流程：
  1. 统计各Tier的Segment数量
  2. 找到超过segments_per_tier的Tier
  3. 从该Tier选择合并收益最大的Segment组
     - 优先合并删除比例高的
     - 优先合并大小相近的
  4. 合并后Segment进入更高Tier

合并代价估算（score简化公式）：
  score = 合并总大小 / (删除比例 × reclaim_deletes_weight)
  score越小 → 代价越低 → 越优先合并
```

### 7.4 合并调度与限流

```
ConcurrentMergeScheduler（并发合并调度器）：

  - 后台线程执行合并
  - max_merge_count：最大同时合并任务数
  - max_thread_count：合并线程数

IO限流（ES层）：
  index.merge.scheduler.max_thread_count
  - SSD：默认 max(1, min(4, cpu/2))
  - HDD：默认1（机械盘串行避免IO竞争）

  当合并IO超过限流：
  - IndexWriter暂停接收写入
  - 产生限流日志
  - 合并完成后恢复写入
```

---

## 8. Doc Values列式存储

### 8.1 为什么需要Doc Values

```
问题：倒排索引擅长正向查询（Term → DocId）
     但排序、聚合、脚本需要反向查询（DocId → Field Value）

方案1: FieldCache（已废弃）
  - 运行时把倒排索引加载到堆内存
  - 导致OOM和GC问题
  - Lucene 6后移除

方案2: Doc Values（Lucene 4+）
  - 正排索引：DocId → Field Value
  - 列式存储，磁盘持久化
  - 不占用堆内存（通过mmap访问）
  - 默认对所有非text字段启用
```

### 8.2 列式存储格式

```
Doc Values存储格式（.dvd + .dvm）：

行式 vs 列式对比：
  行式：  Doc1[name=A, age=20, city=BJ]
          Doc2[name=B, age=25, city=SH]

  列式：  name:  [A, B, ...]      ← 只存name列
          age:   [20, 25, ...]    ← 只存age列
          city:  [BJ, SH, ...]    ← 只存city列

列式优势：
  - 聚合某列只读取该列数据，IO少
  - 同列数据类型一致，压缩率高
  - 向量化处理（SIMD指令加速）

三种编码方式：
  1. Numeric（数值型）
     - delta + block-packed（块压缩）
     - 每块128个值，用最少bit存储

  2. Sorted（字符串有序型）
     - 值字典排序 → 存ord（序号）
     - ord用Numeric方式压缩

  3. SortedSet / SortedNumeric
     - 多值字段（如tags数组）
```

### 8.3 访问方式与内存映射

```
Doc Values访问流程：

  1. 查询获取DocId列表（来自倒排索引）
  2. DocId → DocValues读取（.dvd文件）
  3. mmap映射到进程地址空间
  4. 按需读取（OS Page Cache管理热点）

内存模型：
  - .dvd文件通过mmap映射
  - 不占用JVM堆内存
  - 使用进程虚拟地址空间
  - OS Page Cache缓存热点数据

禁用Doc Values（节省空间，失去聚合能力）：
  PUT /my_index
  {
    "mappings": {
      "properties": {
        "raw_field": {
          "type": "keyword",
          "doc_values": false    ← 禁用，不可聚合/排序/脚本
        }
      }
    }
  }
```

---

## 9. BKD树空间索引

### 9.1 BKD树原理

```
BKD-Tree (Balanced K-Dimension Tree)：
  - 多维空间数据结构
  - Lucene用于数值型、地理坐标、IP的范围查询
  - 替代了早期的trie实现

适用字段类型：
  - long, integer, double, float（数值范围查询）
  - date（时间范围）
  - geo_point, geo_shape（地理查询）
  - ip（IP范围查询）

核心思想：
  - 将多维空间递归切分
  - 每次选择一个维度，按中位数切分
  - 构建平衡KD树
  - 叶子节点存储多个点（提升缓存局部性）
```

### 9.2 BKD树构建与查询

```
构建过程（以2D点为例）：

  点集: (1,3), (2,5), (3,8), (4,1), (5,7), (6,2)

  第1层：按X轴中位数(3.5)切分
    左子树: (1,3),(2,5),(3,8)
    右子树: (4,1),(5,7),(6,2)

  第2层：按Y轴切分
    左子树按Y中位数(5):
      (1,3) | (2,5),(3,8)
    右子树按Y中位数(2):
      (4,1),(6,2) | (5,7)

  叶子节点：每叶存2-3个点

范围查询流程：
  1. 从根节点开始，判断查询范围与切分超平面是否相交
  2. 相交 → 递归搜索两个子树
  3. 不相交 → 剪枝（跳过该子树）
  4. 叶子节点内线性扫描匹配点

复杂度：
  - 构建：O(n log n)
  - 范围查询：O(n^(1-1/k) + m)，k=维度，m=结果数
  - 远优于倒排索引的全扫描方式
```

### 9.3 Lucene中的BKD实现

```
Lucene BKD实现文件：

  .kdd - BKD Data（点数据）
  .kdi - BKD Index（内部节点索引）
  .kdm - BKD Metadata（元数据）

特点：
  - 叶子节点堆叠存储，最大化顺序IO
  - 内部节点紧凑存储
  - 支持十亿级点数据

与倒排索引配合：
  - 数值范围查询 → 走BKD树（高效剪枝）
  - 精确值查询 → 走倒排索引（FST+PostingList）

  ES自动选择查询路径：
  - range查询 → BKD
  - term查询 → 倒排索引
  - ES 7.x+ 数值类型默认同时建两者
```

---

## 10. Near Real-Time搜索原理

### 10.1 NRT核心机制

```
传统搜索 vs Near Real-Time：

  传统全文检索：写入 → commit(fsync) → 可搜索
    延迟：秒级到分钟级

  Lucene NRT：写入 → refresh(不fsync) → 可搜索
    延迟：默认1秒（ES）

关键：refresh生成Segment但不持久化
  - Segment写入OS Page Cache即可搜索
  - 不等待磁盘fsync
  - 用translog保证数据不丢

三阶段时间线：
  t=0ms    写入In-memory Buffer + Translog
  t=1s     refresh: Buffer → Segment(Page Cache)，可搜索
  t=5s     translog fsync（ES默认每5秒）
  t=30min  flush: Segment fsync + translog清空 + 新commit点
```

### 10.2 refresh vs flush vs commit

```
  操作           触发频率       作用                     fsync?
  ──────────────────────────────────────────────────────────────
  refresh        1秒(默认)      Buffer→Segment可搜索      否
  translog sync  5秒(默认)      translog持久化            是
  flush          30min/512MB    Segment持久化+清translog   是

  refresh：
    - 生成新Segment + 新IndexReader
    - 搜索可见，但断电可能丢失（Page Cache未fsync）

  flush（=Lucene commit）：
    - Segment文件fsync到磁盘
    - 写segments_N提交点
    - 清空translog
    - 崩溃恢复：从commit点 + 重放translog
```

### 10.3 IndexReader与搜索可见性

```
Lucene搜索可见性模型：

  DirectoryReader (open)
       ↓
  SegmentReader × N （每个Segment一个Reader）
       ↓
  搜索时遍历所有SegmentReader

refresh后的Reader切换：
  旧Reader：引用计数管理
    - 已打开的搜索继续用旧Reader
    - 搜索完成后close，引用归零回收

  新Reader：包含新Segment
    - 新搜索请求使用新Reader

实现：SearcherManager
  - acquire()：获取最新Reader
  - release()：归还Reader（引用计数-1）
  - maybeRefresh()：后台刷新

ES封装：
  - 每个shard一个IndexShard
  - Engine管理Reader生命周期
  - refresh_interval控制刷新频率
```

### 10.4 NRT性能权衡

```
refresh_interval调优：

  默认1秒：
    - 搜索延迟1秒，适合大多数场景

  调大（如30秒）：
    - 减少Segment生成 → 减少merge压力
    - 适合批量写入场景（日志导入）
    - 写入完成后可手动refresh

  禁用自动（-1）：
    - 写入时不生成Segment
    - 手动refresh控制可见性
    - 适合大批量索引重建

  PUT /my_index/_settings
  {
    "index.refresh_interval": "30s"
  }

  批量导入最佳实践：
    1. settings: refresh_interval=-1, number_of_replicas=0
    2. 批量写入（bulk API）
    3. 恢复: refresh_interval=1s, number_of_replicas=1
    4. POST /_forcemerge?max_num_segments=1
```

---

## 📚 相关阅读

- [01_Elasticsearch核心原理](./01_Elasticsearch核心原理.md)
- [02_Elasticsearch深度实战](./02_Elasticsearch深度实战.md)
- [MySQL核心机制详解](../03_数据库/04_MySQL核心机制详解.md)

### 官方文档

- [Apache Lucene Documentation](https://lucene.apache.org/core/docs/)
- [Elasticsearch Reference - Indexing Speed](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-indexing-speed.html)
- [Lucene TieredMergePolicy Javadoc](https://lucene.apache.org/core/9_x/core/org/apache/lucene/index/TieredMergePolicy.html)

### 深入阅读

- Lucene源码：`org.apache.lucene.index.IndexWriter`、`DocumentsWriterPerThread`
- BKD-Tree论文：The Priority R-Tree (STOC 2003)
- FST论文：Direct Construction of Minimal Acyclic Subsequential Transducers (2003)
- 《Elasticsearch: The Definitive Guide》- 深入理解索引生命周期
- 《Lucene in Action》- 倒排索引与查询原理

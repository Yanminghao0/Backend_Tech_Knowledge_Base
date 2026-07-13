# Lucene原理深入

> Elasticsearch的底层引擎，倒排索引的极致工程实现

---

## 📋 目录

1. [Lucene概述](#1-lucene概述)
2. [倒排索引实现](#2-倒排索引实现)
3. [Segment结构与合并](#3-segment结构与合并)
4. [FST词典](#4-fst词典)
5. [DocValues列式存储](#5-docvalues列式存储)
6. [BKD树与空间索引](#6-bkd树与空间索引)
7. [BM25打分机制](#7-bm25打分机制)
8. [IndexWriter与IndexSearcher](#8-indexwriter与indexsearcher)
9. [Near Real-Time搜索](#9-near-real-time搜索)
10. [面试要点](#10-面试要点)

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

设计哲学：
  - Segment不可变 → 无锁并发读、缓存友好
  - 追加写入 → 写入快，读取需合并多Segment
  - 分层合并 → 自动优化Segment数量
```

---

## 2. 倒排索引实现

### 2.1 写入流程

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

### 2.2 倒排链表结构

```
Posting List 包含的信息：
  ┌────────────────────────────────────────────┐
  │  Term: "elasticsearch"                      │
  │                                              │
  │  DocId列表: [3, 7, 12, 15, 22, 30, 45]      │
  │  词频(TF):  [2,  1,  3,  1,  2,  1,  4]      │
  │  位置信息:  [[12,18],[5],[8,15,22],...]      │
  │  偏移量:    [[0,13],[0,13],...]              │
  │  Payload:  [null, null, "weight=2", ...]    │
  └────────────────────────────────────────────┘

  - DocId: 文档编号（用于获取文档）
  - 词频TF: Term在文档中出现的次数（影响打分）
  - 位置Position: Term在文档中的位置（短语查询需要）
  - 偏移Offset: Term的起止字符位置（高亮显示需要）
  - Payload: 自定义负载（如同义词权重）
```

### 2.3 Posting List压缩

```
Posting List存储格式：
  DocId列表：[1, 3, 7, 12, 15, 22, 30, 45, 70]

压缩方式：
  1. Delta编码：存差值 [1, 2, 4, 5, 3, 7, 8, 15, 25]
  2. Split+RoaringBitmap：分块存储，稀疏用数组，密集用Bitmap

Lucene的PForDelta优化：
  - 将DocId数组分成块（每块128个DocId）
  - 大部分值用较少bit存储（如7bit）
  - 异常值单独存储（Exception Array）
  - 结合Bit Packing，压缩率极高

效果：1亿DocId从约400MB压缩到约50MB
```

---

## 3. Segment结构与合并

### 3.1 Segment不可变性

```
Segment一旦生成不可修改：
  - 查询无需加锁
  - 缓存友好（不需失效）
  - 删除 = 标记.del文件（物理删除在merge时）

写入 → refresh → 新Segment（1秒）
合并 → merge → 小Segment合并为大Segment
```

### 3.2 Segment内部结构

```
┌─────────────────── 一个Segment ──────────────────────┐
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ Term Index  │  │ Term Dict   │  │ Posting List │ │
│  │ (.tip, FST) │→ │ (.tim)      │→ │ (.doc/.pos)  │ │
│  │ 内存常驻     │  │ mmap        │  │ 按需读取      │ │
│  └─────────────┘  └─────────────┘  └──────────────┘ │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ Stored      │  │ Doc Values  │  │ Live Docs    │ │
│  │ Fields      │  │ (列式)      │  │ (.liv)       │ │
│  │ (.fdt/.fdx) │  │ (.dvd/.dvm) │  │ 位图         │ │
│  └─────────────┘  └─────────────┘  └──────────────┘ │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐                   │
│  │ Norms       │  │ Term Vectors│                   │
│  │ (.nvd/.nvm) │  │ (.tvx/.tvd) │                   │
│  └─────────────┘  └─────────────┘                   │
└───────────────────────────────────────────────────────┘

各文件作用：
  - Term Index/Dict/Posting List: 倒排索引核心
  - Stored Fields: 文档原文（_source字段）
  - Doc Values: 列式存储，用于排序/聚合
  - Live Docs: 存活文档位图（删除标记）
  - Norms: 文档长度归一化值（打分用）
  - Term Vectors: 每个文档的词项向量（相似文档查找）
```

### 3.3 Merge策略

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

### 3.4 Force Merge

```json
// 强制合并为单个Segment（优化查询性能）
POST /my_index/_forcemerge?max_num_segments=1

// 适用：索引不再更新（日志类只读索引）
// 不适用：频繁更新的索引（合并后新Segment又会产生）
```

### 3.5 合并过程中的优化

```
合并时的优化策略：
  1. 已删除文档在合并时被物理删除 → 减少空间
  2. 多个Segment的Posting List合并为一个 → 减少查询时需扫描的Segment数
  3. DocValues合并 → 加速聚合
  4. 合并是后台线程，不影响写入

合并选择算法（Tiered Policy）：
  - 找出大小最接近的一组Segment
  - 优先合并小Segment
  - 避免合并超大Segment（代价高，收益低）
  - max_merged_size限制最大合并Segment大小

合并限速：
  - indices.store.throttle.type: merge
  - indices.store.throttle.max_bytes_per_sec: 50mb
  - 防止合并IO影响正常查询
```

---

## 4. FST词典

### 4.1 FST原理

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

### 4.2 Term Index → Term Dictionary → Posting List

```
查询流程：
  1. Term Index (.tip) → FST找到Term在Dictionary中的位置块
  2. Term Dictionary (.tim) → 在位置块中找到Term
  3. Posting List (.doc) → 获取DocId列表

Tip文件常驻内存，Tim文件mmap到内存，Doc按需读取

详细查询过程：
  ┌──────────────────────────────────────────────┐
  │  查询词: "elasticsearch"                       │
  │                                                │
  │  Step 1: FST查找(.tip)                        │
  │    输入: e→l→a→s→t→i→c→...                    │
  │    输出: Term在.tim文件中的Block位置 = 0x4A20   │
  │                                                │
  │  Step 2: Block内查找(.tim)                     │
  │    在0x4A20位置读取Block                       │
  │    Block内二分查找 → 找到Term "elasticsearch"  │
  │    获取Posting List指针 = 0x8B30               │
  │                                                │
  │  Step 3: 读取Posting List(.doc)                │
  │    在0x8B30位置读取Posting List                │
  │    解压 → DocId列表 [3,7,12,15,22,30,45]       │
  └──────────────────────────────────────────────┘
```

### 4.3 FST vs HashMap vs Trie

```
| 维度       | FST          | HashMap     | Trie        |
|------------|--------------|-------------|-------------|
| 内存占用   | 极小(共享前后缀)| 大(哈希表)   | 大(节点多)   |
| 查询复杂度 | O(len)       | O(len)均摊  | O(len)      |
| 前缀查询   | 支持         | 不支持      | 支持        |
| 磁盘友好   | 是(顺序存储) | 否          | 否          |
| 适用场景   | 词典索引     | 精确查找    | 自动补全    |

Lucene选择FST的原因：
  1. 内存占用极小 → 1亿Term仅需~100MB
  2. 支持前缀查询（如 "elastic*"）
  3. 可持久化到磁盘，加载快
```

---

## 5. DocValues列式存储

### 5.1 为什么需要DocValues

```
倒排索引的问题：
  Term → DocId列表（适合全文搜索）
  但排序/聚合/分组需要 DocId → Field Value（正排）

如果用倒排索引做排序：
  1. 查到10000个DocId
  2. 对每个DocId去Stored Fields取排序字段
  3. 排序
  → 大量随机IO，极慢

DocValues解决方案：
  额外维护一个 DocId → Field Value 的列式存储
  直接按DocId快速获取字段值，O(1)随机访问
```

### 5.2 DocValues存储格式

```
┌─────────────── DocValues (numeric类型) ───────────────┐
│                                                        │
│  方式1: Numeric DocValues                              │
│  ┌──────────────────────────────────────────────┐     │
│  │  DocId │ 0  │ 1  │ 2  │ 3  │ 4  │ ...        │     │
│  │  Value │ 25 │ 30 │ 18 │ 42 │ 35 │ ...        │     │
│  └──────────────────────────────────────────────┘     │
│  → 按DocId顺序存储，支持位压缩                        │
│  → 排序/聚合时按DocId直接定位                          │
│                                                        │
│  方式2: Sorted Numeric DocValues                      │
│  ┌──────────────────────────────────────────────┐     │
│  │  1. 提取所有唯一值并排序: [18,25,30,35,42]     │     │
│  │  2. 存储每个DocId的值索引: [1,2,0,4,3,...]    │     │
│  │  3. 唯一值表 + Ordinal列表                    │     │
│  └──────────────────────────────────────────────┘     │
│  → 压缩率更高（索引值用更少bit）                      │
│                                                        │
│  方式3: Sorted Set DocValues (keyword类型)             │
│  ┌──────────────────────────────────────────────┐     │
│  │  唯一值: ["apple","banana","cherry"]          │     │
│  │  DocId→Ordinal: [0,1,0,2,1,...]              │     │
│  │  Ordinal→DocId: 0→[0,2,...], 1→[1,4,...]     │     │
│  └──────────────────────────────────────────────┘     │
│  → 同时支持terms聚合和docId查找                        │
└───────────────────────────────────────────────────────┘

DocValues vs FieldData（旧方案）：
  - FieldData: 将倒排索引加载到JVM堆内存 → GC压力大，OOM风险
  - DocValues: 磁盘列式存储，mmap映射到堆外内存 → 无GC压力
  - ES 6.0+ 完全用DocValues替代FieldData
```

### 5.3 使用建议

```json
// 默认所有支持DocValues的字段类型都开启
// 可显式关闭不需要排序/聚合的字段以节省空间
PUT /my_index
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "doc_values": false  // 不需要聚合/排序时关闭
          }
        }
      },
      "price": {
        "type": "double",
        "doc_values": true  // 需要排序，保持开启
      }
    }
  }
}
```

---

## 6. BKD树与空间索引

### 6.1 BKD树原理

```
BKD树 (Block KD-Tree) 用于数值型和地理坐标的快速范围查询

结构：
  - 多维空间数据结构
  - 每次按某一维度切分空间
  - 叶子节点存储数据点

示例（1维数值，如price字段）：
  数据: [10, 15, 20, 25, 30, 35, 40, 45]

  BKD树:
           [25]
          /     \
      [15]       [35]
      /  \       /  \
   [10] [20]  [30]  [40,45]

  范围查询 price >= 20 AND price <= 35:
  → 从根节点25开始
  → 左子树15: 20在右子树 [20]
  → 右子树35: 30在左子树 [30], 35 [35]
  → 结果: [20, 25, 30, 35]
```

### 6.2 BKD树在Lucene中的应用

```
适用字段类型：
  - 数值型: long, integer, double, float
  - 日期型: date (底层是long时间戳)
  - IP类型: ip (底层是long)
  - 地理坐标: geo_point (2维BKD树)
  - 地理形状: geo_shape

查询类型支持：
  - 范围查询: range query (price >= 100 AND price <= 500)
  - 地理距离: geo_distance query (距离某个点5km以内)
  - 地理边界: geo_bounding_box query
  - 多边形查询: geo_polygon query

BKD vs 倒排索引（数值型字段）：
  ┌────────────┬──────────────────┬─────────────────┐
  │ 维度       │ BKD树            │ 倒排索引         │
  ├────────────┼──────────────────┼─────────────────┤
  │ 范围查询   │ O(logN) 高效     │ 需遍历所有Term   │
  │ 精确查询   │ O(logN)          │ O(1) 直接定位    │
  │ 排序/聚合  │ 需DocValues辅助  │ 直接可用         │
  │ 存储效率   │ 高(排序后压缩)   │ 中等(每个值独立) │
  └────────────┴──────────────────┴─────────────────┘

  → Lucene 7+ 数值型字段默认用BKD树
  → 精确查询场景可同时启用keyword（倒排索引）
```

---

## 7. BM25打分机制

### 7.1 BM25算法

```
BM25 (Best Matching 25) 是Lucene默认的相关性打分算法

公式：
  score(D, Q) = Σ IDF(qi) × (f(qi,D) × (k1 + 1))
                          / (f(qi,D) + k1 × (1 - b + b × |D| / avgdl))

参数说明：
  - f(qi, D): 词qi在文档D中的词频(TF)
  - |D|: 文档D的长度
  - avgdl: 所有文档的平均长度
  - k1: 词频饱和参数（默认1.2），控制TF的增长速度
  - b: 文档长度归一化参数（默认0.75），控制长度惩罚力度
  - IDF(qi): 逆文档频率 = ln(1 + (N - n(qi) + 0.5) / (n(qi) + 0.5))
```

### 7.2 BM25 vs TF-IDF

```
TF-IDF的问题：
  1. TF线性增长 → 词频越高分数无限增长，长文档占优势
  2. 文档长度归一化不够 → 长文档天然得分高

BM25的改进：
  1. TF饱和：f(qi,D) × (k1+1) / (f(qi,D) + k1)
     → 词频增长到一定程度后，分数增长变缓（渐近线 k1+1）
     → 防止高频词过度影响

  2. 文档长度惩罚：1 - b + b × |D| / avgdl
     → 文档越长，分母越大，分数越低
     → b=0.75时，适度惩罚超长文档

对比示例：
  词频: 1 → 5 → 10 → 20 → 50
  
  TF-IDF: 1.0 → 5.0 → 10.0 → 20.0 → 50.0  (线性增长)
  BM25:   1.0 → 2.3 → 2.8  → 3.1  → 3.3   (渐近饱和)
  
  → BM25更合理：出现50次的词不比10次重要5倍
```

### 7.3 BM25参数调优

```json
// 索引级别设置BM25参数
PUT /my_index
{
  "settings": {
    "index": {
      "similarity": {
        "custom_bm25": {
          "type": "BM25",
          "k1": 1.2,
          "b": 0.75
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "similarity": "custom_bm25"
      }
    }
  }
}

// 调参建议：
// k1=0: 完全忽略词频（只看是否出现）
// k1=2.0: 词频影响增大（适合专业搜索）
// b=0: 不做文档长度归一化（文档长度不影响分数）
// b=1: 完全按文档长度归一化（严格惩罚长文档）
```

---

## 8. IndexWriter与IndexSearcher

### 8.1 IndexWriter写入流程

```
IndexWriter写入管线：

  Document
      │
      ▼
  ┌──────────┐
  │ Analyzer │ 分词（StandardAnalyzer/IKAnalyzer等）
  └────┬─────┘
       │ Terms
       ▼
  ┌──────────────┐
  │ IndexingChain│ 构建索引结构
  │  ├─ Inverted │ → 倒排索引（Term→DocId）
  │  ├─ Stored   │ → 存储字段（文档原文）
  │  ├─ DocValues│ → 列式存储（排序/聚合）
  │  ├─ Norms    │ → 归一化值（打分用）
  │  └─ TermVec  │ → 词项向量
  └────┬─────────┘
       │
       ▼
  ┌──────────┐
  │ DocumentsWriterPerThread │ 每线程独立Buffer
  └────┬─────┘
       │ Buffer满 / flush
       ▼
  ┌──────────┐
  │ Segment  │ 生成新的Segment文件
  │ Flush    │
  └──────────┘

关键机制：
  - 每线程独立Buffer → 无锁写入
  - Buffer满自动flush → 生成新Segment
  - 多线程flush → 多个Segment → 后台合并
```

```java
// IndexWriter使用示例
Directory directory = FSDirectory.open(Paths.get("/index"));
IndexWriterConfig config = new IndexWriterConfig(new StandardAnalyzer());
config.setOpenMode(IndexWriterConfig.OpenMode.CREATE_OR_APPEND);
// 合并策略
config.setMergeStrategy(new TieredMergePolicy());
// 内存Buffer大小（影响flush频率）
config.setRAMBufferSizeMB(64);

IndexWriter writer = new IndexWriter(directory, config);

// 添加文档
Document doc = new Document();
doc.add(new TextField("title", "Lucene原理", Field.Store.YES));
doc.add(new TextField("content", "倒排索引是核心", Field.Store.YES));
doc.add(new SortedDocValuesField("price", new BytesRef("99")));
writer.addDocument(doc);

// 提交（持久化到磁盘）
writer.commit();

// 删除文档
writer.deleteDocuments(new Term("id", "123"));

// 更新文档（先删后加）
writer.updateDocument(new Term("id", "123"), newDoc);

writer.close();
```

### 8.2 IndexSearcher查询流程

```
IndexSearcher查询流程：

  Query (如: BooleanQuery)
      │
      ▼
  ┌──────────────┐
  │ Query Rewrite │ 重写查询（如通配符展开为TermQuery）
  └────┬─────────┘
       │
       ▼
  ┌──────────────┐
  │ Create Weight │ 创建权重（计算IDF等）
  └────┬─────────┘
       │
       ▼
  ┌──────────────┐
  │ Build Scorer  │ 构建Scorer（遍历Posting List）
  └────┬─────────┘
       │
       ▼  遍历各Segment
  ┌──────────────────────────┐
  │ For each Segment:         │
  │  1. 查FST → 定位Term      │
  │  2. 读Posting List        │
  │  3. BM25打分              │
  │  4. 收集DocId+Score        │
  └────┬─────────────────────┘
       │
       ▼
  ┌──────────────┐
  │ Collector    │ 收集结果
  │  ├─ TopDocs  │ → TopN排序
  │  ├─ Filter   │ → 过滤
  │  └─ Aggregate│ → 聚合
  └────┬─────────┘
       │
       ▼
  ┌──────────────┐
  │ Fetch Source │ 从Stored Fields取文档原文
  └──────────────┘
```

```java
// IndexSearcher使用示例
IndexReader reader = DirectoryReader.open(directory);
IndexSearcher searcher = new IndexSearcher(reader);

// 构建查询
Query query = new BooleanQuery.Builder()
    .add(new TermQuery(new Term("title", "lucene")), BooleanClause.Occur.MUST)
    .add(new TermQuery(new Term("content", "倒排")), BooleanClause.Occur.SHOULD)
    .build();

// 搜索Top10
TopDocs topDocs = searcher.search(query, 10);

// 遍历结果
for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
    Document doc = searcher.doc(scoreDoc.doc);
    System.out.println("Score: " + scoreDoc.score + 
                       ", Title: " + doc.get("title"));
}

reader.close();
```

---

## 9. Near Real-Time搜索

### 9.1 NRT机制

```
Lucene的Near Real-Time（NRT）搜索：

传统流程：
  写入 → Buffer → flush到磁盘 → 新Segment → 可搜索
  flush代价高（涉及磁盘IO）→ 写入到可搜索延迟较长

NRT优化：
  写入 → Buffer → refresh → 生成Segment（内存中）→ 可搜索
  refresh不刷盘，只是把Buffer转为可读的Segment

  ┌──────────────────────────────────────────────┐
  │  IndexWriter Buffer (RAM)                     │
  │  ┌─────────────────────────────┐             │
  │  │ DocumentsWriterPerThread     │             │
  │  │ (写入Buffer)                 │             │
  │  └──────────┬──────────────────┘             │
  │             │ refresh (1秒, 可配置)            │
  │             ▼                                 │
  │  ┌─────────────────────────────┐             │
  │  │ Segment (内存, 未刷盘)        │ ← NRT Reader可读│
  │  └──────────┬──────────────────┘             │
  │             │ flush (translog持久化)          │
  │             ▼                                 │
  │  ┌─────────────────────────────┐             │
  │  │ Segment (磁盘, 已持久化)      │ ← 所有Reader可读│
  │  └─────────────────────────────┘             │
  └──────────────────────────────────────────────┘

ES中的三个时间参数：
  - refresh_interval (默认1s): Buffer → Segment(内存)，数据可搜索
  - flush (translog满512MB): Segment → 磁盘，translog清除
  - fsync: 确保数据写入物理磁盘
```

### 9.2 ES中的写入可靠性

```
写入流程（ES）：
  1. 请求到达Primary Shard
  2. 写入IndexWriter Buffer + 写入Translog
  3. refresh → 生成内存Segment（可搜索，但未持久化）
  4. Replica Shard同步
  5. 返回客户端确认
  6. Translog满 → flush → Segment刷盘 + Translog清除

可靠性保证：
  - Translog在返回前已写入（默认每请求fsync）
  - 即使内存Segment丢失，可从Translog恢复
  - Replica Shard提供高可用

性能权衡：
  - refresh_interval=1s → 近实时搜索，但生成大量小Segment
  - refresh_interval=30s → 减少Segment数量，搜索延迟增加
  - index.translog.durability=async → 提升写入吞吐，但有数据丢失风险
```

---

## 10. 面试要点

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

### Q4: DocValues解决了什么问题？

```
问题：倒排索引（Term→DocId）不适合排序/聚合（需要DocId→Value）

DocValues方案：
  - 额外维护DocId→FieldValue的列式存储
  - 磁盘存储+mmap映射到堆外内存
  - 无GC压力（对比旧的FieldData方案）

效果：
  - 排序/聚合性能提升10x+
  - 内存占用可控，不会OOM
```

### Q5: BM25相比TF-IDF有什么优势？

```
1. 词频饱和：防止高频词过度影响分数
   - TF-IDF: 词频线性增长
   - BM25: 词频渐近饱和（k1参数控制）

2. 文档长度归一化：惩罚过长的文档
   - b参数控制惩罚力度
   - 防止长文档天然得分高

3. 更符合信息检索理论
   - 基于概率检索模型
   - 实验证明BM25优于TF-IDF
```

### Q6: BKD树和倒排索引在数值型字段上的选择？

```
BKD树（Lucene 7+默认）：
  - 范围查询高效 O(logN)
  - 存储压缩好
  - 精确查询不如倒排索引

倒排索引（旧方案）：
  - 精确查询O(1)
  - 范围查询需遍历所有Term，慢
  - 高基数字段（如price）占用大量Term

结论：
  - Lucene 7+数值型默认BKD树
  - 需要精确查询+聚合时，可同时建keyword类型
```

### Q7: Lucene的NRT搜索原理？

```
NRT = Near Real-Time，近实时搜索

原理：
  1. 写入到IndexWriter Buffer
  2. refresh：Buffer → 内存中的Segment（不刷盘）
  3. NRT Reader可以直接读取内存Segment
  4. 数据可搜索延迟约1秒

对比：
  - 传统：需要flush到磁盘才能搜索（秒级到分钟级延迟）
  - NRT：refresh生成内存Segment即可搜索（~1秒）

代价：
  - 大量小Segment需要merge
  - 内存Segment未持久化，崩溃后需从Translog恢复
```

---

## 📚 相关阅读

- [01_Elasticsearch核心原理](./01_Elasticsearch核心原理.md)
- [02_Elasticsearch深度实战](./02_Elasticsearch深度实战.md)
- [MySQL核心机制详解](../03_数据库/04_MySQL核心机制详解.md)

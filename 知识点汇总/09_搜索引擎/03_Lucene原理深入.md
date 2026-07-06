# Lucene原理深入

> Elasticsearch的底层引擎，倒排索引的极致工程实现

---

## 📋 目录

1. [Lucene概述](#1-lucene概述)
2. [倒排索引实现](#2-倒排索引实现)
3. [Segment与合并](#3-segment与合并)
4. [FST词典](#4-fst词典)
5. [面试要点](#5-面试要点)

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

---

## 📚 相关阅读

- [01_Elasticsearch核心原理](./01_Elasticsearch核心原理.md)
- [02_Elasticsearch深度实战](./02_Elasticsearch深度实战.md)
- [MySQL核心机制详解](../03_数据库/04_MySQL核心机制详解.md)

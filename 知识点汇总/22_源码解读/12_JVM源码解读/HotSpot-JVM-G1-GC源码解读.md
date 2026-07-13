# HotSpot JVM G1 GC 源码深度解读：分区回收与停顿预测模型

> "G1 的设计目标不是成为最快的 GC，而是成为最可预测的 GC——在大堆内存下仍然能控制停顿时间，这是 G1 区别于 CMS 的根本所在。" —— 内存管理团队

---

## 📋 目录

1. [G1 整体架构与核心概念](#1-g1-整体架构与核心概念)
2. [堆内存 Region 划分源码解析](#2-堆内存-region-划分源码解析)
3. [RSet 记忆集源码解析](#3-rset-记忆集源码解析)
4. [卡表与写屏障源码](#4-卡表与写屏障源码)
5. [G1 年轻代回收流程源码](#5-g1-年轻代回收流程源码)
6. [G1 混合回收源码解析](#6-g1-混合回收源码解析)
7. [停顿预测模型 Pause Prediction Model](#7-停顿预测模型-pause-prediction-model)
8. [并发标记阶段源码解析](#8-并发标记阶段源码解析)
9. [Full GC 兜底机制](#9-full-gc-兜底机制)
10. [面试题速查](#10-面试题速查)

---

## 1. G1 整体架构与核心概念

G1（Garbage First）是面向服务端应用的垃圾收集器，引入了 Region 化的堆内存布局，将连续的堆内存划分为多个大小相等的 Region，每个 Region 可以动态扮演 Eden、Survivor、Old 或 Humongous 角色。

```
G1 堆内存布局：
┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
│ E  │ S  │ O  │ H  │ H  │ E  │ O  │ O  │ .. │ F  │
├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ O  │ E  │ E  │ S  │ O  │ O  │ H  │ O  │ .. │ E  │
├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ .. │ O  │ E  │ O  │ O  │ S  │ O  │ E  │ .. │ O  │
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘

E = Eden    S = Survivor    O = Old
H = Humongous (大对象)       F = Free
```

G1 的核心设计思想：
- **分代回收**：保留年轻代/老年代概念，但不再物理连续
- **Region 化**：堆被划分为 2048 个左右的 Region（1~32MB）
- **垃圾优先**：优先回收垃圾最多的 Region（Garbage First）
- **可预测停顿**：基于历史数据预测停顿时间，在目标范围内回收

G1 GC 的回收周期：

```
                   ┌─────────── 并发标记 ───────────┐
                   │                                 │
 ──► 年轻代GC ──► 年轻代GC ──► 初始标记 ──► 并发标记 ──► 最终标记 ──► 筛选回收 ──► 混合GC ──► ...
     (Young)      (Young)      (Initial      (Concurrent   (Final      (Cleanup/    (Mixed)
                                Mark)         Mark)         Mark)        Evacuation)
     │ STW │       │ STW │      │ STW │       │  并发  │      │ STW │      │ STW │
```

---

## 2. 堆内存 Region 划分源码解析

### 2.1 G1CollectedHeap 堆初始化

```cpp
// g1CollectedHeap.cpp
jint G1CollectedHeap::initialize() {
  // ...
  
  // 1. 确定 Region 大小
  // MIN_REGION_SIZE = 1MB, MAX_REGION_SIZE = 32MB
  // 默认为堆大小的 1/2048，且在 [1MB, 32MB] 范围内，且为 2 的幂
  size_t region_size = MAX2(MAX2(MIN_REGION_SIZE, _max_heap_size / (size_t)TargetPLABSize),
                            MAX_REGION_SIZE);
  if (align_up(region_size, MIN_REGION_SIZE) != region_size) {
    region_size = align_up(region_size, MIN_REGION_SIZE);
  }
  // 确保是 2 的幂
  if (!is_power_of_2(region_size)) {
    region_size = round_up_power_of_2(region_size);
  }
  // 限制范围
  region_size = clamp(region_size, MIN_REGION_SIZE, MAX_REGION_SIZE);

  // 2. 初始化堆布局
  HeapRegion::setup_heap_region_size(region_size);
  
  // 3. 创建堆区管理器
  _hrm = new HeapRegionManager(_bot, _g1h);
  
  // 4. 分配堆内存
  ReservedSpace heap_rs = ReservedSpace(_max_heap_size);
  _reserved.set_word_size(_max_heap_size / HeapWordSize);
  _reserved.set_start((HeapWord*)heap_rs.base());
  
  // 5. 创建所有 Region
  _hrm->initialize(heap_rs);
  
  // 6. 初始化卡表
  _card_table = new G1CardTable(_reserved);
  
  // ...
  return JNI_OK;
}
```

### 2.2 HeapRegion 数据结构

```cpp
// heapRegion.hpp
class HeapRegion : public ContiguousSpace {
  // Region 在堆中的索引
  uint _hrm_index;
  
  // Region 类型
  enum RegionType {
    Free,           // 空闲
    Eden,           // Eden 区
    Survivor,       // Survivor 区
    Old,            // 老年代
    Humongous,      // 大对象（可能跨多个 Region）
    Pinned,         // 被钉住（不能移动）
    Archive         // 归档区
  };
  RegionType _type;
  
  // 是否在 Collection Set（待回收集合）中
  bool _in_collection_set;
  
  // GC 年龄
  uint _gc_age;
  
  // RSet（记忆集）指针
  HeapRegionRemSet* _rem_set;
  
  // 上一次回收后的存活数据统计
  size_t _recorded_rs_length;
  size_t _predicted_elapsed_time_ms;  // 预测回收该 Region 耗时
  
  // 获取 Region 起始地址
  HeapWord* bottom() const { return ContiguousSpace::bottom(); }
  HeapWord* end() const { return ContiguousSpace::end(); }
  HeapWord* top() const { return ContiguousSpace::top(); }
  
  // Region 大小
  static size_t GrainBytes;
  static size_t LogOfHRGrainBytes;
  
  // 判断对象是否在本 Region
  bool is_in(const void* p) const {
    return p >= bottom() && p < end();
  }
};
```

### 2.3 Region 大小选择算法

```cpp
// heapRegion.cpp
void HeapRegion::setup_heap_region_size(size_t max_heap_size) {
  // 根据 max_heap_size 计算 Region 大小
  // 目标：约 2048 个 Region
  
  uint region_size_log = log2_long(max_heap_size) - 11;  // 除以 2048 ≈ 减 11 位
  
  if (region_size_log < MIN_REGION_SIZE_LOG) {
    region_size_log = MIN_REGION_SIZE_LOG;  // 最小 1MB = 2^20
  } else if (region_size_log > MAX_REGION_SIZE_LOG) {
    region_size_log = MAX_REGION_SIZE_LOG;  // 最大 32MB = 2^25
  }
  
  GrainBytes = (size_t)1 << region_size_log;
  LogOfHRGrainBytes = region_size_log;
}
```

例如：4GB 堆 → Region 大小 = 4GB / 2048 = 2MB；32GB 堆 → Region 大小 = 32MB。

### 2.4 大对象 Humongous Region

```cpp
// heapRegion.cpp
bool HeapRegion::is_humongous(size_t obj_size) {
  // 大于 Region 一半的对象即为 Humongous
  return obj_size > _hrm->region_size_in_words() / 2;
}

// 大对象可能占用连续的多个 Region
void G1CollectedHeap::allocate_humongous(size_t word_size) {
  uint num_regions = (uint)align_up(word_size, HeapRegion::GrainWords) 
                     / HeapRegion::GrainWords;
  
  // 找到连续的 num_regions 个空闲 Region
  uint start = _hrm->find_contiguous_free(num_regions);
  if (start == G1_NO_HRMRS) {
    // 没有足够的连续空间，可能触发 GC
    return NULL;
  }
  
  // 将这些 Region 标记为 Humongous
  for (uint i = start; i < start + num_regions; i++) {
    HeapRegion* hr = _hrm->at(i);
    hr->set_type(HeapRegion::Humongous);
    if (i == start) {
      hr->set_starts_humongous();
    } else {
      hr->set_continues_humongous();
    }
  }
}
```

---

## 3. RSet 记忆集源码解析

### 3.1 RSet 的作用

RSet（Remembered Set）记录"谁引用了我"，即指向当前 Region 的外部引用。这使得 G1 在回收单个 Region 时不需要扫描整个堆，只需扫描该 Region 的 RSet。

```
Region A (Old)          Region B (Eden)        Region C (Old)
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ obj1 ────────┼──────►│ obj3         │       │ obj5 ────────┼──┐
│ obj2 ────────┼──┐    │              │       │              │  │
└──────────────┘  │    └──────────────┘       └──────────────┘  │
                  │                                              │
                  ▼                                              ▼
            Region B 的 RSet                          Region C 的 RSet
            ┌──────────────┐                          ┌──────────────┐
            │ Region A     │                          │ Region A     │
            │ (Card: obj1) │                          │ (Card: obj5) │
            └──────────────┘                          └──────────────┘
```

### 3.2 HeapRegionRemSet 数据结构

```cpp
// heapRegionRemSet.hpp
class HeapRegionRemSet : public CHeapObj<mtGC> {
  // 当前 Region
  HeapRegion* _hr;
  
  // 强引用 RSet（真正影响存活性的引用）
  OtherRegionsTable _other_regions;
  
  // 弱引用 RSet（用于并发标记阶段）
  OtherRegionsTable _other_regions_weak;
  
  // ... 方法 ...
};

// otherRegionsTable.hpp
class OtherRegionsTable {
  // 使用细粒度表 + 粗粒度表两级结构
  
  // 细粒度表：按 Region 索引存储卡表
  // 使用 SparsePRT（稀疏表）和 PerRegionTable（每 Region 表）
  
  // 粗粒度位图：当引用太多时，直接标记整个 Region
  BitMap _coarse_map;  // 每个 bit 对应一个 Region
  
  // 稀疏表：少量引用时使用
  SparsePRT* _sparse_table;
  
  // 第一层细粒度表
  PerRegionTable** _fine_grains;
  size_t _n_fine_entries;
};
```

RSet 的三级存储策略：
1. **Sparse PRT**（稀疏表）：引用很少时使用，每个条目存储 Region + 卡片索引
2. **Fine PRT**（细粒度表）：引用较多时使用，每个被引用 Region 对应一个 PerRegionTable（位图）
3. **Coarse Map**（粗粒度位图）：引用极多时使用，直接标记整个 Region 有引用

这种分层设计在精度和内存开销之间取得了平衡。

### 3.3 RSet 引用记录

```cpp
// heapRegionRemSet.cpp
void OtherRegionsTable::add_reference(OopOrNarrowOopStar from, uint tid) {
  // 获取引用来源所在的 Region
  HeapRegion* from_hr = _g1h->heap_region_containing(from);
  if (from_hr == NULL) return;  // 引用在堆外
  
  uint from_hr_index = from_hr->hrm_index();
  
  // 获取引用来源所在的 Card 索引
  size_t card_index = _ct->index_for(from);
  
  if (_coarse_map.at(from_hr_index)) {
    // 已经在粗粒度表中，无需更细粒度记录
    return;
  }
  
  // 查找细粒度表
  PerRegionTable** p = find_fine_grain_prt(from_hr_index);
  if (p != NULL) {
    // 已有该 Region 的细粒度表，添加卡片
    (*p)->add_card(card_index);
  } else {
    // 检查是否需要升级到粗粒度表
    if (_n_fine_entries >= _max_fine_entries) {
      // 细粒度表满了，升级到粗粒度
      _coarse_map.set_bit(from_hr_index);
      // 删除对应的细粒度表
      delete_fine_grain_prt(from_hr_index);
    } else {
      // 尝试稀疏表
      if (_sparse_table->add_card(from_hr_index, card_index)) {
        // 添加成功
      } else {
        // 稀疏表满了，迁移到细粒度表
        PerRegionTable* prt = new PerRegionTable(from_hr);
        prt->add_card(card_index);
        add_fine_grain_prt(from_hr_index, prt);
        _sparse_table->delete_entry(from_hr_index);
      }
    }
  }
}
```

### 3.4 RSet 遍历与更新

在 GC 过程中，G1 会通过 RSet 快速找到跨 Region 引用：

```cpp
// heapRegionRemSet.cpp
void HeapRegionRemSet::scrub(CardTableRS* ct, BitMap* region_bm, BitMap* card_bm) {
  // 清理无效的 RSet 条目
  // 在 GC 后调用，移除已回收 Region 的引用记录
  
  _other_regions.scrub(ct, region_bm, card_bm);
}

// 在对象转移时更新引用
void G1RemSet::update_rem_set_after_scan(HeapRegion* from_region) {
  // 扫描 Region 中所有存活对象的引用
  // 如果引用目标在其他 Region，更新目标的 RSet
  HeapWord* obj_addr = from_region->bottom();
  while (obj_addr < from_region->top()) {
    oop obj = oop(obj_addr);
    int sz = obj->size();
    // 遍历对象的每个引用字段
    obj->oop_iterate([&](oop* p) {
      oop referent = *p;
      if (referent != NULL) {
        HeapRegion* to_region = _g1h->heap_region_containing(referent);
        if (to_region != from_region) {
          // 跨 Region 引用，添加到目标 Region 的 RSet
          to_region->rem_set()->add_reference(p, from_region->hrm_index());
        }
      }
    });
    obj_addr += sz;
  }
}
```

---

## 4. 卡表与写屏障源码

### 4.1 G1 卡表结构

```cpp
// g1CardTable.hpp
class G1CardTable : public CardTable {
  // 继承自 CardTable，使用字节数组
  // 每个 Card 对应 512 字节的堆内存
  // Card 值：
  //   G1CardTable::CleanCard     = 0x01  - 干净
  //   G1CardTable::DirtyCard     = 0x00  - 脏（有引用变更）
  //   G1CardTable::LastFreeCard  = 0x0F  - 最后一个空闲 Card
  //   G1CardTable::ClaimedCard   = 0x10  - 已被 GC 线程认领
  //   G1CardTable::VerifyCard    = 0x20  - 验证用
  
  static const size_t CardSize = 512;  // 每个 Card 对应 512 字节
};
```

### 4.2 写屏障

G1 使用写后屏障来维护 RSet 和并发标记的卡表：

```cpp
// g1BarrierSet.cpp

// 写后屏障入口
void G1BarrierSet::write_ref_field_post(volatile oop* field, oop new_val) {
  // 获取 Card 在卡表中的索引
  CardValue* card = _card_table->byte_for(field);
  
  // 如果 Card 不是脏的，标记为脏
  if (*card != G1CardTable::dirty_card_val()) {
    *card = G1CardTable::dirty_card_val();
    // 将脏卡片加入 DCQS（Dirty Card Queue Set）
    // 后台线程 RefineThread 会异步处理这些脏卡片，更新 RSet
    G1DirtyCardQueue& dcq = G1ThreadLocalData::dirty_card_queue(thread);
    dcq.enqueue(card);
  }
}
```

### 4.3 DCQS 脏卡队列

```cpp
// g1DirtyCardQueue.hpp
class G1DirtyCardQueueSet : public PtrQueueSet {
  // 全局脏卡队列集合
  // 每个 GC 线程有一个本地队列
  // 本地队列满了后提交到全局队列
  
  // 后台 RefineThread 处理脏卡
  // 当 RSet 更新跟不上速度时，会在 GC 时同步处理
  
  void process_card(CardValue* card) {
    // 1. 找到 Card 对应的 Region
    HeapRegion* hr = _g1h->heap_region_containing(card_addr);
    
    // 2. 找到被引用对象所在的 Region
    //    扫描 Card 中的所有引用
    //    对于每个跨 Region 引用，更新目标 Region 的 RSet
    
    // 3. 将 Card 标记为已处理
    *card = G1CardTable::clean_card_val();
  }
};

// G1RefineThread 后台处理
void G1RemSet::refine_cards_concurrently() {
  while (!_dcqs.is_empty()) {
    CardValue* card = _dcqs.dequeue();
    if (card != NULL) {
      refine_card(card);
    }
  }
}
```

---

## 5. G1 年轻代回收流程源码

### 5.1 GC 触发判断

```cpp
// g1CollectedHeap.cpp
bool G1CollectedHeap::should_do_young_gc() {
  // 检查 Eden 是否需要扩展
  size_t young_list_target_length = young_list_target_length();
  size_t young_list_length = _young_list->length();
  
  if (young_list_length < young_list_target_length) {
    return false;  // 还没到目标大小
  }
  
  // 检查是否有足够的 Survivor Region
  // 检查是否需要触发并发标记
  if (should_start_concurrent_mark()) {
    return true;
  }
  
  return true;
}

bool G1CollectedHeap::should_start_concurrent_mark() {
  // 当堆使用率超过 InitiatingHeapOccupancyPercent (默认45%)
  size_t used = used_unlocked();
  size_t capacity = capacity_unlocked();
  double used_percent = (double)used / capacity * 100;
  return used_percent > _ihop * 100;
}
```

### 5.2 年轻代 GC 主流程

```cpp
// g1CollectedHeap.cpp
void G1CollectedHeap::young_g_collect(bool should_start_mark_cycle) {
  // 1. GC 前准备
  {
    G1YoungGCPrologueClosure cl;
    heap_region_iterate(&cl);
  }
  
  // 2. 构建 Collection Set（CSet）
  //    年轻代 GC 只包含 Eden 和 Survivor Region
  collection_set()->build_young_cset();
  
  // 3. 执行 GC
  {
    G1EvacPhase1EvacuateRegions evac_phase1(this);
    evac_phase1.work();  // 1. 复制存活对象
    
    G1EvacPhase2PrepareRegions evac_phase2(this);
    evac_phase2.work();  // 2. 更新 Region 状态
    
    G1EvacPhase3RebuildRSets evac_phase3(this);
    evac_phase3.work();  // 3. 重建 RSet
  }
  
  // 4. GC 后处理
  post_evacuate_cleanup();
  
  // 5. 如果需要，启动并发标记周期
  if (should_start_mark_cycle) {
    start_concurrent_mark_cycle();
  }
}
```

### 5.3 对象转移 Evacuation

```cpp
// g1EvacuateRegionsTask.cpp
class G1EvacuateRegionsTask : public AbstractGangTask {
  void work(uint worker_id) {
    // 1. 获取 PLAB（Promotion Local Allocation Buffer）
    //    每个 GC 线程有自己的 PLAB，用于存放复制的对象
    G1PLAB* plab = get_plab(worker_id);
    
    // 2. 遍历 CSet 中的 Region
    for (HeapRegion* hr : cset_regions) {
      // 扫描 Region 中的存活对象
      G1ScanClosure scan_cl(this, plab);
      
      // 扫描根引用（RSet 中的引用）
      scan_rem_set(hr, scan_cl);
      
      // 扫描 Region 内部对象
      scan_region(hr, scan_cl);
    }
  }
};

// 对象复制核心逻辑
void G1ParScanThreadState::copy_to_survivor_space(HeapRegion* from_region,
                                                   oop old) {
  // 获取对象年龄
  uint age = old->age();
  
  // 判断晋升还是存活
  if (age < max_tenuring_threshold) {
    // 复制到 Survivor Region
    HeapWord* obj_addr = survivor_plab()->allocate_aligned(obj_size);
    if (obj_addr == NULL) {
      // PLAB 满了，重新分配
      obj_addr = allocate_in_survivor(obj_size);
    }
    // 复制对象
    Copy::aligned_conjoint_words((HeapWord*)old, obj_addr, obj_size);
    oop new_obj = oop(obj_addr);
    new_obj->set_age(age + 1);
    // 记录转发指针
    old->forward_to(new_obj);
  } else {
    // 晋升到 Old Region
    HeapWord* obj_addr = old_plab()->allocate_aligned(obj_size);
    if (obj_addr == NULL) {
      obj_addr = allocate_in_old(obj_size);
    }
    Copy::aligned_conjoint_words((HeapWord*)old, obj_addr, obj_size);
    oop new_obj = oop(obj_addr);
    old->forward_to(new_obj);
  }
}
```

### 5.4 Forwarding Pointer 转发指针

G1 使用对象头中的 Mark Word 来存储转发指针（在 GC 期间）：

```cpp
// markWord.hpp
class markWord {
  // 正常状态：存储 hashCode、GC age、锁状态
  // GC 期间：存储转发地址
  
  bool is_forwarded() const {
    return (value() & markWord::marked_value) == markWord::marked_value;
  }
  
  markWord forward_to(oop p) const {
    // 在对象头中设置转发指针
    // 使用最低两位标记为 forwarded 状态
    return markWord((uintptr_t)p | markWord::marked_value);
  }
  
  oop forwardee() const {
    return oop(clear_lock_bits());
  }
};
```

对象在复制后，原位置的 Mark Word 被修改为转发指针，后续访问该对象的引用都会被重定向到新位置。

---

## 6. G1 混合回收源码解析

混合回收是 G1 的特色功能，在年轻代 GC 的基础上，额外回收一部分垃圾最多的老年代 Region。

### 6.1 CSet 构建策略

```cpp
// g1CollectionSet.cpp
void G1CollectionSet::finalize_mixed_recording() {
  // 1. 获取所有候选老年代 Region（并发标记阶段标记为可回收的）
  //    按垃圾比例排序（Garbage First）
  
  CollectionSetCandidates* candidates = _candidates;
  
  // 2. 根据停顿时间目标选择 Region
  double predicted_pause_time_ms = 0.0;
  double target_pause_time_ms = _policy->max_pause_time_ms();
  
  uint selected_count = 0;
  while (candidates->num_remaining() > 0) {
    HeapRegion* hr = candidates->pop_front();  // 垃圾最多的优先
    
    // 预测回收该 Region 的耗时
    double predicted_time = predict_region_noncopy_time_ms(hr);
    predicted_pause_time_ms += predicted_time;
    
    if (predicted_pause_time_ms > target_pause_time_ms) {
      // 超过停顿目标，停止添加
      break;
    }
    
    // 添加到 CSet
    _collection_set_regions[selected_count++] = hr->hrm_index();
    _bytes_used_before += hr->used();
  }
  
  _num_optional_regions = selected_count;
}
```

### 6.2 Region 价值评估

```cpp
// g1Policy.cpp
double G1Policy::predict_region_noncopy_time_ms(HeapRegion* hr) const {
  // 预测回收该 Region 的时间
  // 考虑因素：
  //   1. Region 中存活对象数量（影响复制时间）
  //   2. RSet 大小（影响扫描时间）
  //   3. 历史回收时间数据
  
  size_t live_bytes = hr->live_bytes();
  size_t rs_length = hr->rem_set()->occupied();
  
  // 使用回归模型预测
  double scan_time = predict_rs_scan_time_ms(rs_length);
  double copy_time = predict_copy_time_ms(live_bytes);
  
  return scan_time + copy_time;
}

double G1Policy::predict_rs_scan_time_ms(size_t rs_length) const {
  // 基于 RSet 大小预测扫描时间
  // 使用指数加权移动平均
  return rs_length * _scan_rs_length_ratio * _recent_avg_scan_time_ms;
}

double G1Policy::predict_copy_time_ms(size_t live_bytes) const {
  // 基于存活数据量预测复制时间
  return live_bytes * _bytes_per_copy_ms;
}
```

---

## 7. 停顿预测模型 Pause Prediction Model

### 7.1 衰减均值模型

G1 使用衰减均值（Decaying Average）来预测 GC 停顿时间，核心思想是近期数据权重更高：

```cpp
// g1Analytics.hpp
class G1Predictions {
  // 衰减因子（默认 0.95）
  double _decay_factor;
  
  // 各种历史数据
  TruncatedSeq _recent_gc_times_ms;           // 近期 GC 耗时
  TruncatedSeq _recent_rs_sizes;              // 近期 RSet 大小
  TruncatedSeq _recent_scan_rs_times_ms;      // 近期 RSet 扫描耗时
  TruncatedSeq _recent_copy_times_ms;         // 近期对象复制耗时
  TruncatedSeq _recent_constant_other_times;  // 近期固定开销
  TruncatedSeq _recent_other_times;           // 近期其他开销
};

// g1Predictions.cpp
class TruncatedSeq {
  double _alpha;       // 衰减因子
  double _average;     // 当前平均值
  double _last;        // 最近一次值
  size_t _num;         // 数据点数量
  
  void add(double val) {
    if (_num == 0) {
      _average = val;
    } else {
      // 指数加权移动平均：EWMA
      _average = _alpha * _average + (1 - _alpha) * val;
    }
    _last = val;
    _num++;
  }
  
  double predict() const {
    return _average;
  }
};
```

### 7.2 停顿时间预测

```cpp
// g1Policy.cpp
double G1Policy::predict_base_elapsed_time_ms(uint num_regions) const {
  // 预测基础耗时（不含对象复制）
  
  double rs_time = predict_rs_scan_time_ms();
  double other_time = predict_other_time_ms();
  double constant_other_time = predict_constant_other_time_ms();
  
  return rs_time + other_time + constant_other_time;
}

double G1Policy::predict_region_elapsed_time_ms(HeapRegion* hr) const {
  // 预测单个 Region 的回收耗时
  size_t live_bytes = hr->live_bytes();
  size_t rs_length = hr->rem_set()->occupied();
  
  // RSet 扫描时间
  double rs_time = _analytics->predict_scan_rs_time_ms(rs_length);
  
  // 对象复制时间（仅存活对象需要复制）
  double copy_time = _analytics->predict_object_copy_time_ms(live_bytes);
  
  // 固定开销分摊
  double constant_other = _analytics->predict_constant_other_time_ms() / num_regions;
  
  return rs_time + copy_time + constant_other;
}

// 判断是否还能在目标停顿时间内添加更多 Region
bool G1Policy::will_fit_in_target_pause(double predicted_time,
                                        double target_pause_time) const {
  return predicted_time <= target_pause_time;
}
```

### 7.3 年轻代大小动态调整

```cpp
// g1Policy.cpp
uint G1Policy::calculate_young_list_desired_min_length(uint base_min_length) const {
  // 最小年轻代大小（至少满足 Survivor 需求）
  uint desired_min_length = base_min_length;
  return MAX2(desired_min_length, (uint)1);
}

uint G1Policy::calculate_young_list_desired_max_length() const {
  // 最大年轻代大小 = 总 Region 数 - 保留老年代 Region 数
  uint reserve_regions = _analytics->predict_rs_length();
  uint max_young_length = _g1h->num_regions() - reserve_regions;
  return max_young_length;
}

uint G1Policy::young_list_target_length() const {
  // 基于停顿目标计算年轻代目标大小
  // 通过二分搜索找到最大的年轻代大小使得预测停顿时间 <= 目标
  
  double target_pause_time_ms = _max_pause_time_ms;
  
  uint min_young = calculate_young_list_desired_min_length();
  uint max_young = calculate_young_list_desired_max_length();
  
  // 二分搜索
  while (min_young < max_young) {
    uint mid = (min_young + max_young + 1) / 2;
    double predicted = predict_young_collection_time_ms(mid);
    if (predicted <= target_pause_time_ms) {
      min_young = mid;  // 可以更大
    } else {
      max_young = mid - 1;  // 需要更小
    }
  }
  
  return min_young;
}
```

这种动态调整保证了 G1 在设定的停顿时间目标内尽可能多地回收垃圾。

---

## 8. 并发标记阶段源码解析

### 8.1 并发标记总览

```
初始标记 (Initial Mark)  ─ STW ─ 借助年轻代 GC 的 STW
     │
并发标记 (Concurrent Mark) ─ 并发 ─ 从根开始标记存活对象
     │
重新标记 (Remark) ─ STW ─ 处理并发期间的引用变更
     │
清理   (Cleanup)   ─ 部分 STW ─ 统计每个 Region 的存活数据
```

### 8.2 初始标记

```cpp
// g1ConcurrentMark.cpp
void G1ConcurrentMark::checkpoint_roots_initial_pre() {
  // 1. 设置标记位图（Next BitMap）
  _next_mark_bitmap->clear();
  
  // 2. 初始化标记上下文
  _mark_stack_context.reset();
}

void G1ConcurrentMark::checkpoint_roots_initial_post() {
  // 从根集合开始标记
  // G1 的初始标记通常搭载在一次年轻代 GC 中完成
  // 这就是为什么叫 "Initial Mark Piggybacking"
  
  G1CMRootClosure root_cl(this);
  _g1h->process_strong_roots(&root_cl);
}
```

### 8.3 并发标记

```cpp
// g1ConcurrentMarkThread.cpp
void G1ConcurrentMarkThread::run_service() {
  while (!should_terminate()) {
    // 等待标记周期开始
    sleep_before_next_cycle();
    
    // 并发标记
    cm()->mark_from_roots();
    
    // 重新标记
    cm()->checkpoint_roots_final();
    
    // 清理
    cm()->cleanup();
  }
}

// g1ConcurrentMark.cpp
void G1ConcurrentMark::mark_from_roots() {
  // 并发标记线程工作循环
  uint active_workers = calculate_active_workers();
  
  G1CMConcurrentMarkingTask marking_task(this, active_workers);
  _workers->run_task(&marking_task);
}

void G1ConcurrentMark::scan_region(HeapRegion* hr, uint worker_id) {
  // 扫描 Region 中的对象
  HeapWord* p = hr->bottom();
  while (p < hr->top()) {
    oop obj = oop(p);
    if (is_marked(obj)) {
      // 对象已标记，扫描其引用
      obj->oop_iterate([&](oop* field) {
        oop referent = *field;
        if (referent != NULL && !is_marked(referent)) {
          // 标记引用对象并压入标记栈
          mark(referent);
          _mark_stack->push(referent);
        }
      });
    }
    p += obj->size();
  }
}
```

### 8.4 SATB（Snapshot At The Beginning）

G1 使用 SATB 算法在并发标记期间保证正确性：

```cpp
// g1ConcurrentMark.cpp
// SATB 写前屏障：在修改引用前，记录旧引用
void G1ConcurrentMark::satb_enqueue(oop old_val) {
  if (old_val != NULL && is_marked(old_val)) {
    // 将旧引用加入 SATB 队列
    // 后续在 Remark 阶段处理这些引用
    G1SATBQueue& satb_q = G1ThreadLocalData::satb_queue(Thread::current());
    satb_q.enqueue(old_val);
  }
}

// 写前屏障
void G1BarrierSet::write_ref_field_pre(oop* field, oop old_val) {
  G1ConcurrentMark::satb_enqueue(old_val);
}
```

SATB 保证了：并发标记期间被覆盖的引用所指向的对象，如果在标记开始时是存活的，在本次 GC 中就不会被误回收。

### 8.5 重新标记 Remark

```cpp
// g1ConcurrentMark.cpp
void G1ConcurrentMark::checkpoint_roots_final() {
  // 1. 处理 SATB 队列中的引用
  drain_satb_queues();
  
  // 2. 重新扫描根集合（并发期间可能有变更）
  rescan_roots();
  
  // 3. 处理弱引用
  process_weak_references();
  
  // 4. 统计标记结果
  //    交换 Next BitMap 和 Prev BitMap
  _next_mark_bitmap->swap(_prev_mark_bitmap);
}
```

### 8.6 清理阶段 Cleanup

```cpp
// g1ConcurrentMark.cpp
void G1ConcurrentMark::cleanup() {
  // 统计每个 Region 的存活数据
  // 标记完全为空的 Region（可以直接回收）
  // 构建 Collection Set 候选列表
  
  G1CleanupTask cleanup_task(this, _g1h->workers());
  cleanup_task.work(active_workers);
  
  // 完全为空的 Region 直接加入可回收列表
  // 部分存活的 Region 按垃圾比例排序，作为混合 GC 的候选
}
```

---

## 9. Full GC 兜底机制

当 G1 无法在目标停顿时间内完成回收（或内存分配失败）时，会退化为 Serial Full GC：

```cpp
// g1CollectedHeap.cpp
void G1CollectedHeap::do_full_collection(bool clear_all_soft_refs) {
  // 取消所有并发任务
  if (concurrent_mark()->cm_thread()->during_cycle()) {
    concurrent_mark()->abort();
  }
  
  // 执行 Serial Full GC
  // 使用单线程标记-压缩算法
  G1MarkSweep::invoke_synchronous(clear_all_soft_refs);
}

// g1MarkSweep.cpp
void G1MarkSweep::invoke_synchronous(bool clear_all_soft_refs) {
  // 1. 标记阶段：从根集合开始标记所有存活对象
  G1MarkSweep::mark_phase(clear_all_soft_refs);
  
  // 2. 计算新地址：为每个存活对象计算转移后的新地址
  G1MarkSweep::calculate_new_addresses();
  
  // 3. 更新引用：将所有引用更新为新地址
  G1MarkSweep::adjust_pointers();
  
  // 4. 压缩移动：将存活对象移动到新地址
  G1MarkSweep::compact();
}
```

Full GC 是 G1 最后的兜底手段，性能很差：
- **单线程**执行（JDK 10 后改为并行）
- **全堆扫描**和**全堆压缩**
- **停顿时间不可控**，可能数秒甚至更长

应通过合理配置避免 Full GC：
- 调大 `-XX:G1HeapRegionSize` 减少 Humongous 分配
- 调低 `-XX:InitiatingHeapOccupancyPercent` 更早启动并发标记
- 调大 `-XX:MaxGCPauseMillis` 给 G1 更多回收空间

---

## 10. 面试题速查

### Q1: G1 和 CMS 的主要区别是什么？
| 特性 | CMS | G1 |
|------|-----|-----|
| 堆布局 | 物理分代 | Region 化（逻辑分代） |
| 回收算法 | 标记-清除 | 复制（Region 间） |
| 碎片问题 | 有碎片 | 无碎片（压缩式回收） |
| 停顿可控 | 不可预测 | 可设目标停顿时间 |
| 回收范围 | 老年代 | 年轻代 + 混合 |
| 适用堆大小 | 中小堆（<8GB） | 大堆（8GB+） |

### Q2: G1 的 RSet 是什么？为什么需要？
RSet（Remembered Set）记录"谁引用了我"，即指向当前 Region 的外部引用。G1 回收单个 Region 时，通过 RSet 快速找到跨 Region 引用，避免扫描整个堆。RSet 采用三级存储（稀疏表 → 细粒度表 → 粗粒度位图）平衡精度和内存。

### Q3: G1 如何实现可预测停顿？
1. 将堆划分为 Region，GC 可以只回收部分 Region
2. 维护每个 Region 的回收成本历史数据（RSet 大小、存活数据、回收耗时）
3. 使用衰减均值模型（EWMA）预测回收耗时
4. 在 CSet 构建时，贪心地添加 Region 直到预测停顿时间接近目标
5. 动态调整年轻代大小，使其在目标停顿时间内完成回收

### Q4: G1 的 SATB 是什么？
SATB（Snapshot At The Beginning）在并发标记开始时创建存活对象快照。通过写前屏障，在引用被覆盖前将旧引用加入 SATB 队列。Remark 阶段处理这些队列。SATB 保证了标记开始时存活的对象不会被误回收，代价是可能多标一些实际已死亡的对象（浮动垃圾）。

### Q5: G1 的混合回收是什么？
在并发标记完成后，G1 除了回收年轻代 Region，还额外回收一部分垃圾最多的老年代 Region。回收哪些老年代 Region 基于"Garbage First"策略——垃圾比例高的优先。混合回收通过多次 GC 逐步清理老年代。

### Q6: G1 什么时候会触发 Full GC？
1. 并发标记速度跟不上分配速度，老年代耗尽
2. Humongous 对象分配失败
3. 晋升失败（Survivor 或 Old 区空间不足）
4. Metaspace 空间不足
Full GC 使用 Serial 单线程（JDK 10 前），停顿时间很长，应尽量避免。

### Q7: G1 的写屏障做了什么？
G1 有两个写屏障：
- **写前屏障**（Pre-write barrier）：维护 SATB 队列，记录被覆盖的旧引用
- **写后屏障**（Post-write barrier）：标记 Card 为脏，加入 DCQS 队列，后台线程异步更新 RSet

### Q8: G1 的 Region 大小如何确定？
Region 大小 = max(1MB, min(32MB, 堆大小/2048))，且为 2 的幂。4GB 堆 → 2MB Region，32GB 堆 → 32MB Region。可通过 `-XX:G1HeapRegionSize` 手动指定。大于 Region 一半的对象为 Humongous，占用连续多个 Region。

### Q9: G1 的 CSet（Collection Set）是什么？
CSet 是本次 GC 要回收的 Region 集合。年轻代 GC 的 CSet 包含所有 Eden + Survivor Region；混合 GC 的 CSet 额外包含部分老年代 Region。CSet 的构建基于停顿时间预测——贪心地添加高垃圾比例的 Region 直到预测停顿时间接近目标。

### Q10: G1 如何处理大对象？
大对象（≥ Region/2）分配为 Humongous Region，占用连续多个 Region。大对象直接分配在老年代区域，不经过年轻代。大对象的回收在并发标记阶段处理（如果整个 Humongous 对象无引用，对应的 Region 直接回收）。大量 Humongous 分配可能导致 Full GC，应考虑增大 Region 大小或避免大对象分配。

---

> **总结**：G1 GC 的源码设计精髓在于**可预测性**——通过 Region 化的堆布局实现选择性回收，通过 RSet 实现精准的跨 Region 引用追踪，通过衰减均值模型实现停顿时间预测，通过 SATB 实现并发标记的正确性。理解这些机制的源码实现，不仅有助于 G1 调优，更对理解现代 GC 设计（如 ZGC、Shenandoah）的演进方向有重要参考价值。G1 的设计哲学是：在大堆内存下，用适度的吞吐量换取可控的停顿时间，这使其成为目前生产环境中最主流的 GC 选择。

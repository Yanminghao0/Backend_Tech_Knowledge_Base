# 集合框架源码解读

> Java集合框架核心源码深度解析，涵盖List、Set、Map、Queue等核心容器

---

## 📚 文档列表

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| [HashMap源码解析](./4.1_HashMap源码解析.md) | 哈希算法、红黑树转换、扩容机制、线程安全 | ⭐⭐⭐⭐⭐ | ✅ |
| [ArrayList源码解析](./4.2_ArrayList源码解析.md) | 动态扩容(1.5倍)、随机访问、批量操作 | ⭐⭐⭐⭐ | ✅ |
| [LinkedList源码解析](./4.3_LinkedList源码解析.md) | 双向链表、头尾操作、Deque实现 | ⭐⭐⭐ | ✅ |
| [LinkedHashMap源码解析](./4.5_LinkedHashMap源码解析.md) | 有序Map、accessOrder、LRU缓存实现 | ⭐⭐⭐⭐ | ✅ |
| [TreeMap源码解析](./4.6_TreeMap源码解析.md) | 红黑树实现、有序遍历、范围查询 | ⭐⭐⭐ | ✅ |
| [HashSet源码解析](./4.7_HashSet源码解析.md) | 基于HashMap、去重原理、add/contains | ⭐⭐⭐ | ✅ |
| [PriorityQueue源码解析](./4.8_PriorityQueue源码解析.md) | 堆结构、堆化调整、TopK问题 | ⭐⭐⭐⭐ | ✅ |
| [ArrayDeque源码解析](./4.9_ArrayDeque源码解析.md) | 循环数组、双端队列、Stack替代 | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习目标

1. **深入HashMap**：put/get流程、哈希冲突解决、红黑树转换阈值、扩容rehash
2. **掌握ArrayList**：1.5倍扩容机制、System.arraycopy、Fail-Fast机制
3. **理解LinkedList**：双向链表Node结构、头尾O(1)操作、与ArrayList性能对比
4. **掌握TreeMap**：红黑树平衡规则、左旋右旋、有序性保证
5. **理解LinkedHashMap**：双向链表维护顺序、accessOrder模式、LRU缓存实现
6. **掌握PriorityQueue**：小顶堆结构、siftUp/siftDown、Comparator定制

---

## 📊 集合架构总览

```
Collection
├── List（有序、可重复）
│   ├── ArrayList     — 数组实现，随机访问O(1)
│   ├── LinkedList    — 双向链表，头尾操作O(1)
│   └── Vector        — 线程安全ArrayList（已过时）
├── Set（无序、不可重复）
│   ├── HashSet       — 基于HashMap
│   ├── LinkedHashSet — 有序HashSet
│   └── TreeSet       — 基于TreeMap，有序
└── Queue（队列）
    ├── PriorityQueue — 堆实现，优先级出队
    ├── ArrayDeque    — 循环数组双端队列
    └── LinkedList    — 也实现Deque

Map（键值对）
├── HashMap          — 数组+链表+红黑树
├── LinkedHashMap    — HashMap+双向链表
├── TreeMap          — 红黑树，有序
├── Hashtable        — 线程安全（已过时）
└── ConcurrentHashMap — 线程安全（CAS+synchronized）
```

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- HashMap的put完整流程？
- HashMap如何解决哈希冲突？（链表→红黑树）
- HashMap什么时候链表转红黑树？（≥8 + 桶数≥64）
- HashMap的扩容机制？（2倍扩容、rehash）
- HashMap为什么线程不安全？（JDK7环链、JDK8数据覆盖）

⭐⭐⭐⭐ 高频：
- ArrayList和LinkedList区别？各自适用场景？
- ArrayList的1.5倍扩容机制？
- HashMap和Hashtable区别？
- ConcurrentHashMap如何保证线程安全？（见并发包源码）
- LinkedHashMap如何实现LRU缓存？
- PriorityQueue的堆结构原理？
```

---

## 📈 推荐阅读顺序

```
1. HashMap        — 面试第一重点，理解哈希表+红黑树
      ↓
2. ArrayList      — 理解动态数组扩容
      ↓
3. LinkedList     — 理解链表结构，与ArrayList对比
      ↓
4. LinkedHashMap  — 理解顺序维护，扩展到LRU
      ↓
5. TreeMap        — 深入红黑树实现
      ↓
6. PriorityQueue  — 理解堆结构
      ↓
7. HashSet        — 基于HashMap，快速过
      ↓
8. ArrayDeque     — 理解循环数组
```

---

*最后更新：2026-07-13*

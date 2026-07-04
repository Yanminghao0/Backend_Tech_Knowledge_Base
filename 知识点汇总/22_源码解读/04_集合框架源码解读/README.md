# 集合框架源码解读

> Java集合框架核心源码深度解析

## 📚 目录

| 文档 | 核心内容 | 面试重要度 | 状态 |
|------|----------|------------|------|
| [HashMap源码解析](./4.1_HashMap源码解析.md) | 哈希算法、红黑树、扩容机制 | ⭐⭐⭐⭐⭐ | ✅ |
| [ArrayList源码解析](./4.2_ArrayList源码解析.md) | 动态扩容、快速随机访问 | ⭐⭐⭐⭐ | ✅ |
| [LinkedList源码解析](./4.3_LinkedList源码解析.md) | 双向链表、头尾操作 | ⭐⭐⭐ | ✅ |
| [TreeMap源码解析](./4.6_TreeMap源码解析.md) | 红黑树、有序遍历 | ⭐⭐⭐ | ✅ |
| [HashSet源码解析](./4.7_HashSet源码解析.md) | 基于HashMap、去重原理 | ⭐⭐⭐ | ✅ |
| [LinkedHashMap源码解析](./4.5_LinkedHashMap源码解析.md) | 有序Map、LRU缓存 | ⭐⭐⭐⭐ | ✅ |
| [PriorityQueue源码解析](./4.8_PriorityQueue源码解析.md) | 堆结构、优先级队列 | ⭐⭐⭐⭐ | ✅ |
| [ArrayDeque源码解析](./4.9_ArrayDeque源码解析.md) | 循环数组、双端队列 | ⭐⭐⭐⭐ | ✅ |

---

## 🎯 学习目标

1. **理解HashMap原理**：哈希冲突、红黑树转换
2. **掌握ArrayList扩容**：1.5倍扩容机制
3. **理解LinkedList结构**：双向链表操作
4. **了解TreeMap排序**：红黑树实现
5. **掌握HashSet去重**：基于HashMap实现
6. **理解LinkedHashMap**：有序Map、LRU缓存实现

---

## 🔥 面试高频考点

```
⭐⭐⭐⭐⭐ 必问：
- HashMap的put流程？
- HashMap如何解决哈希冲突？
- HashMap什么时候转红黑树？
- HashMap的扩容机制？
- HashMap为什么线程不安全？

⭐⭐⭐⭐ 高频：
- ArrayList和LinkedList区别？
- ArrayList扩容机制？
- HashMap和Hashtable区别？
```

---

*最后更新：2025-12-28*

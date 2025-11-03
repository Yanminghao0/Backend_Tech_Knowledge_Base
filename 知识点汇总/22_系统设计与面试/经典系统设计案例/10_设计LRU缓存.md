# 设计LRU缓存

> LeetCode 146：设计一个LRU缓存淘汰算法

## 📋 核心要求
- get(key)：O(1)
- put(key, value)：O(1)
- 容量满时淘汰最久未使用

## 数据结构
- HashMap + 双向链表
- LinkedHashMap（Java内置）

## 代码实现
```java
class LRUCache {
    private Map<Integer, Node> cache;
    private int capacity;
    private Node head, tail;
    
    // 详细实现见文档
}
```

**详细内容待补充** ⏳

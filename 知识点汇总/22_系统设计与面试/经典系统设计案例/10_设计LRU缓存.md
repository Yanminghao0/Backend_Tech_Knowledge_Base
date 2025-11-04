# 设计LRU缓存

> 高频面试题：设计一个LRU（最近最少使用）缓存

## 📋 面试题目

```
设计一个LRU缓存，支持以下操作：
1. get(key)：获取缓存值，O(1)时间复杂度
2. put(key, value)：设置缓存值，O(1)时间复杂度
3. 容量满时淘汰最久未使用的数据
```

---

## 一、核心实现

### 1.1 HashMap + 双向链表

```java
/**
 * LRU缓存实现
 * 使用HashMap + 双向链表
 */
public class LRUCache<K, V> {
    
    // 缓存容量
    private final int capacity;
    // 存储键值对
    private final Map<K, Node<K, V>> cache;
    // 双向链表头尾节点
    private final Node<K, V> head;
    private final Node<K, V> tail;
    
    // 双向链表节点
    private static class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;
        
        Node() {}
        
        Node(K key, V value) {
            this.key = key;
            this.value = value;
        }
    }
    
    public LRUCache(int capacity) {
        this.capacity = capacity;
        this.cache = new HashMap<>();
        
        // 初始化虚拟头尾节点
        this.head = new Node<>();
        this.tail = new Node<>();
        head.next = tail;
        tail.prev = head;
    }
    
    /**
     * 获取缓存值
     */
    public V get(K key) {
        Node<K, V> node = cache.get(key);
        if (node == null) {
            return null;
        }
        
        // 移动到链表头部（最近使用）
        moveToHead(node);
        return node.value;
    }
    
    /**
     * 设置缓存值
     */
    public void put(K key, V value) {
        Node<K, V> node = cache.get(key);
        
        if (node != null) {
            // 更新值并移动到头部
            node.value = value;
            moveToHead(node);
        } else {
            // 创建新节点
            Node<K, V> newNode = new Node<>(key, value);
            cache.put(key, newNode);
            addToHead(newNode);
            
            // 超出容量，删除尾部节点
            if (cache.size() > capacity) {
                Node<K, V> removed = removeTail();
                cache.remove(removed.key);
            }
        }
    }
    
    /**
     * 添加节点到头部
     */
    private void addToHead(Node<K, V> node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }
    
    /**
     * 删除节点
     */
    private void removeNode(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
    
    /**
     * 移动节点到头部
     */
    private void moveToHead(Node<K, V> node) {
        removeNode(node);
        addToHead(node);
    }
    
    /**
     * 删除尾部节点
     */
    private Node<K, V> removeTail() {
        Node<K, V> node = tail.prev;
        removeNode(node);
        return node;
    }
    
    /**
     * 获取缓存大小
     */
    public int size() {
        return cache.size();
    }
}
```

### 1.2 使用LinkedHashMap

```java
/**
 * 基于LinkedHashMap的LRU缓存
 */
public class LRUCacheLinkedHashMap<K, V> extends LinkedHashMap<K, V> {
    
    private final int capacity;
    
    public LRUCacheLinkedHashMap(int capacity) {
        // accessOrder=true表示按访问顺序排序
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }
    
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
    
    public V get(Object key) {
        return super.getOrDefault(key, null);
    }
}
```

---

## 二、线程安全版本

### 2.1 加锁实现

```java
/**
 * 线程安全的LRU缓存
 */
public class ConcurrentLRUCache<K, V> {
    
    private final int capacity;
    private final Map<K, Node<K, V>> cache;
    private final Node<K, V> head;
    private final Node<K, V> tail;
    private final ReentrantReadWriteLock lock = new ReentrantReadWriteLock();
    private final Lock readLock = lock.readLock();
    private final Lock writeLock = lock.writeLock();
    
    // ... Node类定义同上
    
    public V get(K key) {
        readLock.lock();
        try {
            Node<K, V> node = cache.get(key);
            if (node == null) {
                return null;
            }
            // 需要升级为写锁来移动节点
            readLock.unlock();
            writeLock.lock();
            try {
                // 双重检查
                node = cache.get(key);
                if (node != null) {
                    moveToHead(node);
                    return node.value;
                }
                return null;
            } finally {
                writeLock.unlock();
                readLock.lock();
            }
        } finally {
            readLock.unlock();
        }
    }
    
    public void put(K key, V value) {
        writeLock.lock();
        try {
            Node<K, V> node = cache.get(key);
            if (node != null) {
                node.value = value;
                moveToHead(node);
            } else {
                Node<K, V> newNode = new Node<>(key, value);
                cache.put(key, newNode);
                addToHead(newNode);
                
                if (cache.size() > capacity) {
                    Node<K, V> removed = removeTail();
                    cache.remove(removed.key);
                }
            }
        } finally {
            writeLock.unlock();
        }
    }
}
```

### 2.2 分段锁实现

```java
/**
 * 分段锁LRU缓存（高并发优化）
 */
public class SegmentedLRUCache<K, V> {
    
    private final int segmentCount;
    private final LRUCache<K, V>[] segments;
    private final ReentrantLock[] locks;
    
    @SuppressWarnings("unchecked")
    public SegmentedLRUCache(int capacity, int segmentCount) {
        this.segmentCount = segmentCount;
        this.segments = new LRUCache[segmentCount];
        this.locks = new ReentrantLock[segmentCount];
        
        int segmentCapacity = (capacity + segmentCount - 1) / segmentCount;
        for (int i = 0; i < segmentCount; i++) {
            segments[i] = new LRUCache<>(segmentCapacity);
            locks[i] = new ReentrantLock();
        }
    }
    
    private int getSegmentIndex(K key) {
        return (key.hashCode() & 0x7FFFFFFF) % segmentCount;
    }
    
    public V get(K key) {
        int index = getSegmentIndex(key);
        locks[index].lock();
        try {
            return segments[index].get(key);
        } finally {
            locks[index].unlock();
        }
    }
    
    public void put(K key, V value) {
        int index = getSegmentIndex(key);
        locks[index].lock();
        try {
            segments[index].put(key, value);
        } finally {
            locks[index].unlock();
        }
    }
}
```

---

## 三、LRU变体

### 3.1 LRU-K

```java
/**
 * LRU-K：访问K次才进入缓存
 */
public class LRUKCache<K, V> {
    
    private final int k;
    private final int capacity;
    private final LRUCache<K, V> mainCache;
    private final Map<K, Integer> accessCount;
    private final Map<K, V> historyBuffer;
    
    public LRUKCache(int capacity, int k) {
        this.k = k;
        this.capacity = capacity;
        this.mainCache = new LRUCache<>(capacity);
        this.accessCount = new HashMap<>();
        this.historyBuffer = new HashMap<>();
    }
    
    public V get(K key) {
        // 先从主缓存获取
        V value = mainCache.get(key);
        if (value != null) {
            return value;
        }
        
        // 从历史缓冲区获取
        value = historyBuffer.get(key);
        if (value != null) {
            int count = accessCount.getOrDefault(key, 0) + 1;
            accessCount.put(key, count);
            
            // 达到K次访问，移入主缓存
            if (count >= k) {
                historyBuffer.remove(key);
                accessCount.remove(key);
                mainCache.put(key, value);
            }
        }
        
        return value;
    }
    
    public void put(K key, V value) {
        // 如果已在主缓存，直接更新
        if (mainCache.get(key) != null) {
            mainCache.put(key, value);
            return;
        }
        
        // 放入历史缓冲区
        historyBuffer.put(key, value);
        accessCount.put(key, 1);
    }
}
```

### 3.2 带过期时间的LRU

```java
/**
 * 带过期时间的LRU缓存
 */
public class ExpirableLRUCache<K, V> {
    
    private final int capacity;
    private final long defaultTTL;
    private final Map<K, CacheEntry<V>> cache;
    private final Node<K> head;
    private final Node<K> tail;
    
    private static class CacheEntry<V> {
        V value;
        long expireTime;
        Node<K> node;
        
        CacheEntry(V value, long expireTime, Node<K> node) {
            this.value = value;
            this.expireTime = expireTime;
            this.node = node;
        }
        
        boolean isExpired() {
            return System.currentTimeMillis() > expireTime;
        }
    }
    
    public V get(K key) {
        CacheEntry<V> entry = cache.get(key);
        if (entry == null) {
            return null;
        }
        
        // 检查是否过期
        if (entry.isExpired()) {
            remove(key);
            return null;
        }
        
        moveToHead(entry.node);
        return entry.value;
    }
    
    public void put(K key, V value) {
        put(key, value, defaultTTL);
    }
    
    public void put(K key, V value, long ttlMs) {
        long expireTime = System.currentTimeMillis() + ttlMs;
        // ... 实现逻辑
    }
}
```

---

## 四、面试要点

### 常见问题

**Q1: LRU的时间复杂度？**
```
get: O(1) - HashMap查找 + 链表移动
put: O(1) - HashMap操作 + 链表操作
```

**Q2: 为什么用双向链表？**
```
1. 删除节点需要O(1)，需要知道前驱节点
2. 单向链表删除需要O(n)遍历找前驱
```

**Q3: LRU和LFU的区别？**
```
LRU：淘汰最久未使用的
LFU：淘汰使用频率最低的
LRU更简单，LFU更精确但实现复杂
```

---

## 📚 扩展阅读

1. [Redis LRU实现](https://redis.io/docs/manual/eviction/)
2. [Caffeine缓存源码](https://github.com/ben-manes/caffeine)

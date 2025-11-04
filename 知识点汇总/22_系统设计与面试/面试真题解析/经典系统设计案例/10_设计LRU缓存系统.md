# 10_设计LRU缓存系统.md

## 一、应用场景分析

### 1.1 使用场景
- 数据库查询缓存
- Web浏览器缓存
- 操作系统内存管理
- 分布式缓存系统
- 移动端应用资源缓存

### 1.2 核心功能
- 数据的增删改查操作
- 基于访问频率的缓存淘汰
- 缓存大小限制
- 缓存命中率统计
- 过期数据处理

## 二、需求分析

### 2.1 功能需求
- **基础操作**：支持get(key)、put(key, value)、delete(key)操作
- **淘汰策略**：当缓存满时，删除最近最少使用的数据
- **容量控制**：支持设置最大缓存容量
- **过期策略**：支持设置数据过期时间
- **统计功能**：记录缓存命中率、访问次数等指标

### 2.2 非功能需求
- **高性能**：get和put操作时间复杂度为O(1)
- **线程安全**：支持多线程并发访问
- **内存效率**：低内存开销
- **可扩展性**：支持分布式扩展
- **可靠性**：数据不丢失（可选持久化）

## 三、数据结构设计

### 3.1 LRU核心数据结构
LRU (Least Recently Used) 缓存需要满足以下特性：
- 快速访问数据
- 快速插入数据
- 快速删除最少使用的数据
- 记录数据的访问顺序

### 3.2 哈希表+双向链表组合
```
HashMap + Doubly Linked List

哈希表：提供O(1)时间复杂度的查找
双向链表：维护数据的访问顺序，头部为最近使用，尾部为最少使用
```

### 3.3 数据结构图示
```
head <-> node1 <-> node2 <-> ... <-> nodeN <-> tail
  ^
  |
HashMap: key -> node
```

## 四、Java实现

### 4.1 手动实现LRU缓存
```java
public class LRUCache<K, V> {
    // 节点类
    private static class Node<K, V> {
        K key;
        V value;
        Node<K, V> prev;
        Node<K, V> next;

        public Node(K key, V value) {
            this.key = key;
            this.value = value;
        }
    }

    private final int capacity; // 缓存容量
    private final Map<K, Node<K, V>> cache; // 哈希表
    private final Node<K, V> head; // 头节点（哨兵）
    private final Node<K, V> tail; // 尾节点（哨兵）
    private int size; // 当前大小

    public LRUCache(int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("Capacity must be positive");
        }
        this.capacity = capacity;
        this.cache = new HashMap<>(capacity);
        // 初始化哨兵节点
        this.head = new Node<>(null, null);
        this.tail = new Node<>(null, null);
        head.next = tail;
        tail.prev = head;
        this.size = 0;
    }

    // 获取数据
    public V get(K key) {
        if (!cache.containsKey(key)) {
            return null;
        }
        Node<K, V> node = cache.get(key);
        // 移动到头部（最近使用）
        moveToHead(node);
        return node.value;
    }

    // 存入数据
    public void put(K key, V value) {
        if (cache.containsKey(key)) {
            // 更新已有节点
            Node<K, V> node = cache.get(key);
            node.value = value;
            moveToHead(node);
            return;
        }

        // 创建新节点
        Node<K, V> newNode = new Node<>(key, value);
        cache.put(key, newNode);
        addToHead(newNode);
        size++;

        // 如果超出容量，删除尾部节点
        if (size > capacity) {
            Node<K, V> tailNode = removeTail();
            cache.remove(tailNode.key);
            size--;
        }
    }

    // 删除数据
    public void delete(K key) {
        if (!cache.containsKey(key)) {
            return;
        }
        Node<K, V> node = cache.get(key);
        removeNode(node);
        cache.remove(key);
        size--;
    }

    // 将节点移到头部
    private void moveToHead(Node<K, V> node) {
        removeNode(node);
        addToHead(node);
    }

    // 添加节点到头部
    private void addToHead(Node<K, V> node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }

    // 移除节点
    private void removeNode(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    // 移除尾部节点
    private Node<K, V> removeTail() {
        Node<K, V> res = tail.prev;
        removeNode(res);
        return res;
    }

    // 获取缓存大小
    public int size() {
        return size;
    }

    // 获取缓存容量
    public int capacity() {
        return capacity;
    }

    // 清空缓存
    public void clear() {
        cache.clear();
        head.next = tail;
        tail.prev = head;
        size = 0;
    }
}
```

### 4.2 使用LinkedHashMap实现LRU缓存
```java
public class LRUCacheWithLinkedHashMap<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    public LRUCacheWithLinkedHashMap(int capacity) {
        // accessOrder=true表示按访问顺序排序
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }

    // 当size超过capacity时，删除最老的元素
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }

    // 重写get方法，保持与父类一致
    @Override
    public V get(Object key) {
        return super.get(key);
    }

    // 重写put方法
    @Override
    public V put(K key, V value) {
        return super.put(key, value);
    }
}
```

### 4.3 线程安全的LRU缓存
```java
public class ConcurrentLRUCache<K, V> {
    private final LRUCache<K, V> lruCache;
    private final ReentrantLock lock = new ReentrantLock();

    public ConcurrentLRUCache(int capacity) {
        this.lruCache = new LRUCache<>(capacity);
    }

    public V get(K key) {
        lock.lock();
        try {
            return lruCache.get(key);
        } finally {
            lock.unlock();
        }
    }

    public void put(K key, V value) {
        lock.lock();
        try {
            lruCache.put(key, value);
        } finally {
            lock.unlock();
        }
    }

    public void delete(K key) {
        lock.lock();
        try {
            lruCache.delete(key);
        } finally {
            lock.unlock();
        }
    }

    public int size() {
        lock.lock();
        try {
            return lruCache.size();
        } finally {
            lock.unlock();
        }
    }
}
```

## 五、核心操作流程

### 5.1 Get操作流程
1. 检查缓存中是否存在key
2. 若不存在，返回null
3. 若存在，将该节点移到链表头部（表示最近使用）
4. 返回节点value

### 5.2 Put操作流程
1. 检查缓存中是否存在key
2. 若存在，更新value并移到头部
3. 若不存在，创建新节点并添加到头部
4. 若缓存大小超过容量，删除尾部节点并从哈希表中移除

### 5.3 缓存淘汰流程
1. 当新增数据导致缓存溢出
2. 定位链表尾部节点（最少使用）
3. 从链表中移除尾部节点
4. 从哈希表中删除对应的key
5. 添加新节点到头部

## 六、性能分析

### 6.1 时间复杂度
- get操作：O(1)（哈希表查找+链表节点移动）
- put操作：O(1)（哈希表插入+链表操作）
- delete操作：O(1)（哈希表删除+链表操作）

### 6.2 空间复杂度
- O(n)，其中n为缓存容量

### 6.3 缓存命中率优化
- 增大缓存容量
- 结合其他淘汰策略（如LFU）
- 热点数据永存
- 预加载常用数据

## 七、扩展与优化

### 7.1 LRU-K改进
LRU-K（Least Recently Used K times）需要最近K次访问才将数据加入缓存，减少缓存抖动

### 7.2 2Q（Two Queues）算法
维护FIFO和LRU两个队列，提高缓存命中率

### 7.3 分布式LRU缓存
- Redis实现：使用expire和LRU策略
- Memcached：支持LRU淘汰策略
- 一致性哈希：解决分布式缓存数据分布

### 7.4 持久化LRU缓存
```java
public class PersistentLRUCache<K, V> extends LRUCache<K, V> {
    private final String filePath;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public PersistentLRUCache(int capacity, String filePath) {
        super(capacity);
        this.filePath = filePath;
        loadFromDisk();
    }

    // 从磁盘加载缓存
    private void loadFromDisk() {
        File file = new File(filePath);
        if (!file.exists()) return;

        try {
            Map<K, V> data = objectMapper.readValue(file, new TypeReference<Map<K, V>>() {});
            for (Map.Entry<K, V> entry : data.entrySet()) {
                super.put(entry.getKey(), entry.getValue());
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // 保存缓存到磁盘
    public void saveToDisk() {
        try {
            Map<K, V> data = new HashMap<>();
            // 遍历缓存数据
            // ...
            objectMapper.writeValue(new File(filePath), data);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void put(K key, V value) {
        super.put(key, value);
        // 异步保存到磁盘
        new Thread(this::saveToDisk).start();
    }
}
```

## 八、实际应用场景

### 8.1 数据库查询缓存
```java
@Service
public class UserService {
    private final LRUCache<Long, User> userCache;
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
        // 创建容量为1000的用户缓存
        this.userCache = new LRUCache<>(1000);
    }

    public User getUserById(Long id) {
        // 先查缓存
        User user = userCache.get(id);
        if (user != null) {
            return user;
        }

        // 缓存未命中，查数据库
        user = userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));

        // 存入缓存
        userCache.put(id, user);
        return user;
    }
}
```

### 8.2 HTTP请求缓存
```java
@Component
public class ApiCacheManager {
    private final ConcurrentLRUCache<String, ApiResponse> apiCache;

    public ApiCacheManager() {
        // 创建线程安全的API缓存，容量500，过期时间5分钟
        this.apiCache = new ConcurrentLRUCache<>(500);
    }

    public ApiResponse getCachedResponse(String url) {
        return apiCache.get(url);
    }

    public void cacheResponse(String url, ApiResponse response) {
        apiCache.put(url, response);
    }
}
```

## 九、总结
LRU缓存是一种高效的缓存淘汰策略，通过哈希表和双向链表的组合实现了O(1)时间复杂度的增删改查操作。在实际应用中，需要根据业务需求选择合适的实现方式，考虑线程安全、持久化、分布式等因素。对于Java开发者，可以直接使用LinkedHashMap快速实现LRU缓存，也可以手动实现以满足特定需求。LRU缓存广泛应用于数据库查询缓存、HTTP请求缓存、分布式缓存系统等场景，是提升系统性能的重要手段。

## 十、扩展阅读
1. 《Redis设计与实现》- 黄健宏
2. 《Java并发编程实战》- Brian Goetz
3. 《高性能MySQL》- Baron Schwartz
4. 《分布式服务架构：原理、设计与实战》- 李艳鹏
5. 《操作系统概念》- Abraham Silberschatz
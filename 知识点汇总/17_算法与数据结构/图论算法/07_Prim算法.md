# Prim算法

> Prim算法是一种构造最小生成树的贪心算法，通过逐步添加最短边来构建最小生成树

---

## 📋 基本信息

### 定义
Prim算法（也称为普里姆算法）是一种用于在加权无向图中找到最小生成树（MST）的贪心算法。它从一个顶点开始，逐步添加与当前生成树相连的最短边，直到所有顶点都被包含。

### 核心思想
1. 从任意顶点开始，初始化一个只包含该顶点的生成树
2. 重复以下步骤直到所有顶点都被包含：
   - 找到连接生成树内外顶点的所有边中权重最小的边
   - 将这条边和对应的外部顶点添加到生成树中
3. 生成树构建完成，包含n-1条边（n为顶点数）

### 与Kruskal算法的比较
| 特性 | Prim算法 | Kruskal算法 |
|------|----------|-------------|
| 核心策略 | 从顶点扩展生成树 | 按权重排序边并添加 |
| 数据结构 | 优先队列、邻接矩阵/表 | 并查集、排序算法 |
| 时间复杂度 | O(E log V) 或 O(V²) | O(E log E) |
| 空间复杂度 | O(V) | O(V + E) |
| 适用场景 | 稠密图 | 稀疏图 |
| 处理方式 | 增量式构建 | 全局排序后选择 |

---

## 🎯 算法原理

### 基本步骤
1. **初始化**：
   - 选择起始顶点s
   - 创建两个数组：key[]（存储顶点到生成树的最小权重）和parent[]（存储生成树中顶点的父节点）
   - 初始化key[]为无穷大，parent[]为-1
   - 设置key[s] = 0（起始顶点到自身的权重为0）

2. **构建最小生成树**：
   - 重复n次：
     - 从key[]中选择权重最小且未被包含的顶点u
     - 将u添加到生成树
     - 更新所有与u相邻且未被包含的顶点v的key[v]值：
       如果边(u,v)的权重小于key[v]，则更新key[v] = 权重(u,v)，并设置parent[v] = u

3. **结果**：parent[]数组包含了最小生成树的边

### 数据结构选择
- **优先队列**：用于高效获取权重最小的顶点，通常使用最小堆
- **邻接矩阵**：适用于稠密图，查找相邻顶点的时间复杂度为O(V)
- **邻接表**：适用于稀疏图，存储效率更高
- **布尔数组**：标记顶点是否已被包含在生成树中

### 图解说明
![Prim算法图解](https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Prim%27s_algorithm.svg/800px-Prim%27s_algorithm.svg.png)
*图：Prim算法构建最小生成树的过程，从顶点A开始逐步扩展* 

---

## 💻 代码实现

### 基于邻接矩阵的实现
```python
def prim_matrix(graph):
    V = len(graph)
    key = [float('inf')] * V  # 存储最小权重
    parent = [-1] * V         # 存储生成树的父节点
    key[0] = 0                # 从第一个顶点开始
    mst_set = [False] * V     # 标记顶点是否在生成树中

    for _ in range(V):
        # 找到key值最小且未被包含的顶点
        min_key = float('inf')
        u = 0
        for v in range(V):
            if key[v] < min_key and not mst_set[v]:
                min_key = key[v]
                u = v

        mst_set[u] = True  # 将顶点u添加到生成树

        # 更新与u相邻的顶点的key值
        for v in range(V):
            # graph[u][v] > 0 表示存在边
            # not mst_set[v] 表示顶点v不在生成树中
            # graph[u][v] < key[v] 表示找到更短的路径
            if graph[u][v] > 0 and not mst_set[v] and graph[u][v] < key[v]:
                key[v] = graph[u][v]
                parent[v] = u

    return parent

# 示例使用
if __name__ == "__main__":
    # 邻接矩阵表示的图
    # 0表示没有边，其他值表示边的权重
    graph = [
        [0, 2, 0, 6, 0],
        [2, 0, 3, 8, 5],
        [0, 3, 0, 0, 7],
        [6, 8, 0, 0, 9],
        [0, 5, 7, 9, 0]
    ]

    parent = prim_matrix(graph)

    # 打印最小生成树的边
    print("最小生成树的边：")
    for i in range(1, len(parent)):
        print(f"边 {parent[i]} - {i}，权重: {graph[i][parent[i]]}")
```

### 基于邻接表和优先队列的优化实现
```python
import heapq

def prim_adjacency_list(graph, start=0):
    V = len(graph)
    key = [float('inf')] * V
    parent = [-1] * V
    key[start] = 0
    mst_set = [False] * V

    # 使用优先队列（最小堆）存储 (权重, 顶点) 对
    heap = []
    heapq.heappush(heap, (0, start))

    while heap:
        weight, u = heapq.heappop(heap)

        if mst_set[u]:
            continue

        mst_set[u] = True

        # 遍历所有与u相邻的顶点
        for v, w in graph[u]:
            if not mst_set[v] and w < key[v]:
                key[v] = w
                parent[v] = u
                heapq.heappush(heap, (w, v))

    return parent

# 示例使用
if __name__ == "__main__":
    # 邻接表表示的图
    # graph[u] 包含 (v, weight) 元组
    graph = [
        [(1, 2), (3, 6)],          # 顶点0的邻居
        [(0, 2), (2, 3), (3, 8), (4, 5)],  # 顶点1的邻居
        [(1, 3), (4, 7)],          # 顶点2的邻居
        [(0, 6), (1, 8), (4, 9)],  # 顶点3的邻居
        [(1, 5), (2, 7), (3, 9)]   # 顶点4的邻居
    ]

    parent = prim_adjacency_list(graph)

    # 打印最小生成树的边
    print("最小生成树的边：")
    total_weight = 0
    for i in range(1, len(parent)):
        # 查找边的权重
        weight = 0
        for v, w in graph[i]:
            if v == parent[i]:
                weight = w
                break
        total_weight += weight
        print(f"边 {parent[i]} - {i}，权重: {weight}")
    print(f"最小生成树的总权重: {total_weight}")
```

---

## 📊 复杂度分析

| 实现方式 | 时间复杂度 | 空间复杂度 | 适用场景 |
|----------|------------|------------|----------|
| 邻接矩阵+线性查找 | O(V²) | O(V) | 稠密图 |
| 邻接表+二叉堆 | O(E log V) | O(V + E) | 稀疏图 |
| 邻接表+斐波那契堆 | O(E + V log V) | O(V + E) | 理论最优，实现复杂 |

### 复杂度说明
- **时间复杂度**：
  - 邻接矩阵实现：主要是因为需要O(V)时间查找最小key值，共需V次，加上更新邻接顶点O(V)，总O(V²)
  - 优先队列实现：每个边会被处理一次(O(E))，每次堆操作O(log V)，总O(E log V)
- **空间复杂度**：主要用于存储key、parent数组和图表示
- **优化方向**：使用更高效的优先队列（如斐波那契堆）可降低理论复杂度

---

## 🔍 应用场景

1. **网络设计**：构建代价最小的通信网络、计算机网络
2. **电路设计**：印刷电路板布线，最小化导线总长度
3. **交通系统规划**：设计最小成本的道路、铁路网络
4. **聚类分析**：用于数据聚类，找到数据点间的最小连接
5. **资源分配**：在分布式系统中优化资源分配
6. **图像处理**：图像分割、特征点匹配
7. **旅行商问题近似解**：通过最小生成树构建近似最优路径
8. **电力网格规划**：优化电网布局，减少传输损耗

---

## ⚠️ 注意事项

1. **图的连通性**：Prim算法仅适用于连通图，对非连通图只能找到连通分量的最小生成树
2. **负权边处理**：Prim算法可以处理负权边，但不适用于含负权环的图
3. **有向图问题**：Prim算法用于无向图，有向图的最小生成树问题需要其他算法
4. **起始顶点选择**：不同起始顶点可能生成不同的最小生成树，但总权重相同
5. **数据结构选择**：
   - 稠密图适合用邻接矩阵+线性查找(O(V²))
   - 稀疏图适合用邻接表+优先队列(O(E log V))
6. **并行化困难**：相比Kruskal算法，Prim算法更难并行实现

---

## 🎓 最佳实践

1. **数据结构优化**：
   - 对于稠密图，使用邻接矩阵配合线性查找更高效
   - 对于稀疏图，优先使用邻接表+二叉堆实现
   - 考虑使用索引优先队列减少不必要的堆操作

2. **算法选择策略**：
   - 顶点少而边多的图（稠密图）：选择Prim算法
   - 顶点多而边少的图（稀疏图）：选择Kruskal算法
   - 需要处理断开连接的图：考虑Kruskal算法

3. **实现技巧**：
   - 使用布尔数组跟踪已加入生成树的顶点
   - 对于大型图，考虑增量式更新而非重建整个数据结构
   - 实现时注意处理自环和重边

4. **扩展应用**：
   - 最小瓶颈生成树：Prim算法可直接用于求解
   - 最大生成树：将边权重取反后应用Prim算法
   - 次小生成树：在最小生成树基础上进行修改

---

### 相关链接
- [Prim算法 - Wikipedia](https://en.wikipedia.org/wiki/Prim%27s_algorithm)
- [最小生成树 - 算法对比](https://en.wikipedia.org/wiki/Minimum_spanning_tree#Comparison_of_algorithms)
- [Prim算法可视化演示](https://visualgo.net/en/mst)

> **更新日期**: 2023-11-15
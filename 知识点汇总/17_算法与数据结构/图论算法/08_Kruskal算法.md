# Kruskal算法

> Kruskal算法是一种通过排序边并使用并查集避免环的贪心算法，用于构造最小生成树

---

## 📊 基本信息

### 定义
Kruskal算法是一种用于在加权无向图中寻找最小生成树（MST）的贪心算法。它通过将所有边按权重排序，然后从小到大依次添加边，同时使用并查集（Union-Find）数据结构确保不会形成环，直至生成树包含所有顶点。

### 核心思想
1. 将图中所有边按权重从小到大排序
2. 初始化并查集，每个顶点自成一个集合
3. 按权重顺序遍历所有边：
   - 如果边的两个顶点属于不同集合，将该边加入生成树，并合并两个集合
   - 如果边的两个顶点属于同一集合，跳过该边（避免形成环）
4. 当生成树包含n-1条边（n为顶点数）时停止

### 与Prim算法的对比
| 特性 | Kruskal算法 | Prim算法 |
|------|-------------|----------|
| 核心策略 | 排序边后选择性添加 | 从顶点扩展生成树 |
| 关键数据结构 | 并查集、排序算法 | 优先队列、邻接矩阵/表 |
| 时间复杂度 | O(E log E) | O(E log V) 或 O(V²) |
| 空间复杂度 | O(V + E) | O(V) |
| 适用场景 | 稀疏图（边少顶点多） | 稠密图（边多顶点少） |
| 实现难度 | 较低（排序+并查集） | 较高（优先队列操作） |
| 并行性 | 易于并行处理 | 难以并行处理 |

---

## 🎯 算法原理

### 基本步骤
1. **边排序**：将所有边按权重升序排列
2. **并查集初始化**：每个顶点初始化为独立集合
3. **边选择与添加**：
   - 遍历排序后的边，对每条边(u, v)：
     - 查找u和v的根节点
     - 若根节点不同，将边加入生成树，合并两个集合
     - 若根节点相同，跳过该边（会形成环）
4. **终止条件**：生成树包含n-1条边时停止

### 并查集工作原理
并查集（Union-Find）是实现Kruskal算法的关键，用于高效管理和合并集合：
- **查找（Find）**：找到元素所在集合的根节点，路径压缩优化可将时间复杂度接近O(1)
- **合并（Union）**：将两个集合合并，按秩合并优化可保持树的平衡性
- **作用**：快速判断两个顶点是否已连通，避免生成树中出现环

### 图解说明
![Kruskal算法图解](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Kruskal%27s_algorithm.svg/800px-Kruskal%27s_algorithm.svg.png)
*图：Kruskal算法构建最小生成树过程，按权重依次添加边并使用并查集检测环*

---

## 💻 代码实现

### 基础实现（含并查集）
```python
class UnionFind:
    def __init__(self, size):
        self.parent = list(range(size))  # 父节点数组
        self.rank = [0] * size          # 秩数组（用于按秩合并）

    def find(self, x):
        """带路径压缩的查找"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 路径压缩
        return self.parent[x]

    def union(self, x, y):
        """带按秩合并的合并"""
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False  # 已在同一集合

        # 按秩合并：将秩小的树合并到秩大的树
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        else:
            self.parent[root_y] = root_x
            if self.rank[root_x] == self.rank[root_y]:
                self.rank[root_x] += 1
        return True

# Kruskal算法实现
def kruskal(graph):
    # 提取边并排序
    edges = []
    for u in range(len(graph)):
        for v, weight in graph[u]:
            if u < v:  # 避免重复边
                edges.append((weight, u, v))
    edges.sort()  # 按权重升序排序

    uf = UnionFind(len(graph))
    mst = []
    total_weight = 0

    for weight, u, v in edges:
        if uf.union(u, v):
            mst.append((u, v, weight))
            total_weight += weight
            if len(mst) == len(graph) - 1:  # MST有n-1条边
                break

    return mst, total_weight

# 示例使用
if __name__ == "__main__":
    # 邻接表表示的图: graph[u] = [(v, weight), ...]
    graph = [
        [(1, 2), (3, 6)],          # 顶点0
        [(0, 2), (2, 3), (3, 8), (4, 5)],  # 顶点1
        [(1, 3), (4, 7)],          # 顶点2
        [(0, 6), (1, 8), (4, 9)],  # 顶点3
        [(1, 5), (2, 7), (3, 9)]   # 顶点4
    ]

    mst, total_weight = kruskal(graph)

    print("最小生成树的边：")
    for u, v, weight in mst:
        print(f"边 {u}-{v}，权重: {weight}")
    print(f"最小生成树总权重: {total_weight}")
```

### 优化实现（处理大型图）
```python
import heapq

# 使用堆排序优化边排序过程
def kruskal_heap_optimized(graph):
    edges = []
    # 使用堆收集并排序边
    for u in range(len(graph)):
        for v, weight in graph[u]:
            if u < v:
                heapq.heappush(edges, (weight, u, v))

    uf = UnionFind(len(graph))
    mst = []
    total_weight = 0

    while edges and len(mst) < len(graph) - 1:
        weight, u, v = heapq.heappop(edges)
        if uf.union(u, v):
            mst.append((u, v, weight))
            total_weight += weight

    return mst, total_weight

# 处理带顶点标签的图（非数字顶点）
def kruskal_with_labels(vertex_labels, edges):
    # 将顶点标签映射到索引
    label_to_idx = {label: i for i, label in enumerate(vertex_labels)}
    idx_to_label = {i: label for label, i in label_to_idx.items()}

    # 转换边为索引表示
    indexed_edges = [(w, label_to_idx[u], label_to_idx[v]) for u, v, w in edges]
    indexed_edges.sort()

    uf = UnionFind(len(vertex_labels))
    mst = []
    total_weight = 0

    for weight, u_idx, v_idx in indexed_edges:
        if uf.union(u_idx, v_idx):
            mst.append((idx_to_label[u_idx], idx_to_label[v_idx], weight))
            total_weight += weight
            if len(mst) == len(vertex_labels) - 1:
                break

    return mst, total_weight
```

---

## 📊 复杂度分析

| 操作 | 时间复杂度 | 说明 |
|------|------------|------|
| 边排序 | O(E log E) | 主要耗时步骤，基于比较的排序算法 |
| 并查集操作 | O(E α(V)) | α是反阿克曼函数，实际接近O(1) |
| 总时间复杂度 | O(E log E) | 由排序步骤主导 |
| 空间复杂度 | O(V + E) | 存储边和并查集数据结构 |

### 复杂度说明
- **时间复杂度**：
  - 排序边：O(E log E)，当E≈V²时（稠密图），可简化为O(V² log V)
  - 并查集操作：几乎为线性时间，α(V)是增长极慢的反阿克曼函数，对于实际应用中的V，α(V)≤5
  - 总体：O(E log E)，通常优于Prim算法的O(V²)实现（适用于稀疏图）
- **空间复杂度**：主要用于存储边列表和并查集数组，为O(V + E)
- **优化方向**：使用基数排序可将边排序时间降至O(E)，但实际应用中较少使用

---

## 🔍 应用场景

1. **网络设计**：构建低成本通信网络、计算机网络
2. **电路布线**：PCB板设计中的最小布线长度规划
3. **交通规划**：城市间道路、铁路网络的最小成本建设
4. **数据聚类**：基于距离的聚类分析（如Kruskal算法构建最小生成树后切割得到聚类）
5. **图像分割**：根据像素相似度构建最小生成树，实现图像分割
6. **分布式系统**：节点间通信路径优化
7. **GIS系统**：地理信息系统中的最优路径规划
8. **资源分配**：在有限资源下最大化覆盖范围

---

## ⚠️ 注意事项

1. **图的连通性**：对非连通图，Kruskal算法只能找到连通分量的最小生成森林
2. **边的处理**：
   - 需避免处理重复边（无向图中(u,v)和(v,u)是同一条边）
   - 自环边应提前过滤，它们不会被加入生成树
3. **并查集实现**：
   - 必须实现路径压缩和按秩合并优化，否则性能会显著下降
   - 初始化时每个顶点必须属于独立集合
4. **负权边处理**：支持负权边，但不适用于含负权环的图
5. **有向图限制**：仅适用于无向图，有向图最小生成树需使用其他算法
6. **边排序稳定性**：当存在相同权重边时，排序稳定性不影响最终生成树权重总和，但可能影响边的选择

---

## 🎓 最佳实践

1. **并查集优化**：
   - 必须同时实现路径压缩和按秩合并，这是Kruskal算法高效的关键
   - 对于大规模图，考虑使用路径压缩的迭代实现而非递归

2. **边处理策略**：
   - 输入预处理：过滤自环和重复边
   - 边存储：稀疏图使用邻接表，稠密图可考虑边列表
   - 大型图：使用堆排序或外部排序处理无法全部载入内存的边

3. **算法选择指南**：
   - 稀疏图（E≈V）：优先选择Kruskal算法（O(E log E)）
   - 稠密图（E≈V²）：可比较Kruskal（O(V² log V)）和Prim邻接矩阵实现（O(V²)）
   - 分布式环境：Kruskal算法更易于并行实现

4. **扩展应用**：
   - 最大生成树：将边权重取反后应用Kruskal算法
   - 最小瓶颈生成树：Kruskal算法可直接用于求解
   - 多约束生成树：结合额外约束条件修改并查集判断逻辑

---

### 相关链接
- [Kruskal算法 - Wikipedia](https://en.wikipedia.org/wiki/Kruskal%27s_algorithm)
- [并查集数据结构 - Wikipedia](https://en.wikipedia.org/wiki/Disjoint-set_data_structure)
- [最小生成树算法比较](https://en.wikipedia.org/wiki/Minimum_spanning_tree#Comparison_of_algorithms)
- [Kruskal算法可视化演示](https://visualgo.net/en/mst)

> **更新日期**: 2023-11-15
# Rabin-Karp算法

> Rabin-Karp算法是一种基于哈希函数的字符串匹配算法，通过计算模式串和主串子串的哈希值来快速比较，特别适用于多模式匹配和大规模文本搜索场景。

---

## 📋 基本信息

### 定义
Rabin-Karp算法（由Rabin和Karp提出）是一种字符串搜索算法，它利用哈希函数将字符串转换为数值，通过比较哈希值来判断字符串是否匹配，从而减少直接字符比较的次数。

### 核心思想
1. **哈希函数**：将模式串和主串中的每个子串计算为哈希值
2. **滚动哈希**：使用滚动哈希技术高效计算主串子串的哈希值，避免重复计算
3. **哈希比较**：先比较哈希值，只有当哈希值相等时才进行实际字符比较，减少不必要的字符匹配
4. **冲突处理**：由于哈希函数可能存在冲突，需要在哈希值匹配时进行实际字符验证

### 与其他算法对比
| 算法 | 预处理时间 | 匹配时间(平均) | 匹配时间(最坏) | 空间复杂度 | 特点 |
|------|------------|----------------|----------------|------------|------|
| Rabin-Karp | O(m) | O(n + m) | O(nm) | O(1) | 适合多模式匹配，哈希冲突影响性能 |
| KMP | O(m) | O(n) | O(n) | O(m) | 无回溯，适合单模式匹配 |
| Boyer-Moore | O(m + k) | O(n/m) | O(nm) | O(k) | 实际应用效率最高，实现复杂 |
| 暴力匹配 | O(1) | O(nm) | O(nm) | O(1) | 简单但效率低 |

> 注：m为模式串长度，n为主串长度，k为字符集大小

---

## 🎯 算法原理

### 哈希函数设计
Rabin-Karp算法通常使用多项式滚动哈希函数：

对于字符串S = s₀s₁...sₘ₋₁，其哈希值定义为：
**hash(S) = (s₀×bᵐ⁻¹ + s₁×bᵐ⁻² + ... + sₘ₋₁×b⁰) mod q**

其中：
- b是基数（通常取字符集大小，如256或10）
- q是一个大素数，用于避免哈希值过大
- sᵢ是字符的ASCII值

### 滚动哈希计算
为高效计算主串子串的哈希值，Rabin-Karp算法使用滚动哈希技术：

已知主串子串text[i..i+m-1]的哈希值为hash_i，则子串text[i+1..i+m]的哈希值为：
**hash_{i+1} = (hash_i - text[i]×bᵐ⁻¹) × b + text[i+m] mod q**

其中：
- bᵐ⁻¹ mod q可预先计算，记为h
- 这样每个新子串的哈希值可在O(1)时间内计算

### 算法步骤
1. **预处理阶段**：
   - 计算模式串的哈希值hash_p
   - 计算基数b的(m-1)次幂mod q，即h = b^(m-1) mod q
2. **匹配阶段**：
   - 计算主串第一个子串(text[0..m-1])的哈希值hash_t
   - 比较hash_t与hash_p：
     - 若不相等，计算下一个子串的哈希值
     - 若相等，进行实际字符比较以避免哈希冲突
   - 当找到匹配或遍历完主串时结束

### 图解说明
```
主串: A B C D A B C
模式串: A B C (m=3)
取b=10, q=101

模式串哈希计算:
hash_p = (65×10² + 66×10¹ + 67×10⁰) mod 101
       = (6500 + 660 + 67) mod 101
       = 7227 mod 101 = 7227 - 71×101 = 7227 - 7171 = 56

h = 10^(3-1) mod 101 = 100 mod 101 = 100

主串子串哈希计算:
子串0-2 (A B C):
hash_t0 = (65×100 + 66×10 + 67) mod 101 = 7227 mod 101 = 56 → 与hash_p相等，验证字符匹配

子串1-3 (B C D):
hash_t1 = (56 - 65×100)×10 + 68 mod 101
       = (56 - 6500)×10 + 68 mod 101
       = (-6444×10 + 68) mod 101
       = (-64440 + 68) mod 101 = -64372 mod 101 = 73

子串2-4 (C D A):
hash_t2 = (73 - 66×100)×10 + 65 mod 101
       = (73 - 6600)×10 + 65 mod 101
       = (-6527×10 + 65) mod 101 = -65205 mod 101 = 45

子串3-5 (D A B):
hash_t3 = (45 - 67×100)×10 + 66 mod 101 = ... = 28

子串4-6 (A B C):
hash_t4 = (28 - 68×100)×10 + 67 mod 101 = ... = 56 → 与hash_p相等，验证字符匹配

最终匹配位置: 0和4
```

---

## 💻 代码实现

### 基本实现（含哈希冲突处理）
```python
def rabin_karp_search(text, pattern):
    """
    Rabin-Karp算法实现字符串匹配
    :param text: 主串
    :param pattern: 模式串
    :return: 匹配起始位置，未找到返回-1
    """
    n = len(text)
    m = len(pattern)
    
    if m == 0: return 0
    if n < m: return -1
    
    # 选择参数
    b = 101  # 基数，可根据字符集大小调整
    q = 10**9 + 7  # 大素数，减少哈希冲突
    
    # 预处理：计算b^(m-1) mod q
    h = 1
    for _ in range(m-1):
        h = (h * b) % q
    
    # 计算模式串哈希值
    hash_p = 0
    for c in pattern:
        hash_p = (hash_p * b + ord(c)) % q
    
    # 计算主串第一个子串哈希值
    hash_t = 0
    for i in range(m):
        hash_t = (hash_t * b + ord(text[i])) % q
    
    # 开始匹配
    for i in range(n - m + 1):
        # 哈希值匹配，进行实际字符比较
        if hash_p == hash_t:
            # 验证是否真的匹配（处理哈希冲突）
            match = True
            for j in range(m):
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                return i
        
        # 计算下一个子串的哈希值
        if i < n - m:
            hash_t = ( (hash_t - ord(text[i]) * h) * b + ord(text[i + m]) ) % q
            # 确保哈希值为正数
            if hash_t < 0:
                hash_t += q
    
    return -1
```

### 多模式匹配实现
```python
def rabin_karp_multiple(patterns, text):
    """
    Rabin-Karp算法实现多模式匹配
    :param patterns: 模式串列表
    :param text: 主串
    :return: 字典，key为模式串，value为匹配位置列表
    """
    n = len(text)
    if not patterns or n == 0:
        return {}
    
    # 所有模式串必须具有相同长度
    m = len(patterns[0])
    for p in patterns:
        if len(p) != m:
            raise ValueError("所有模式串必须具有相同长度")
    if m == 0 or n < m:
        return {p: [] for p in patterns}
    
    # 参数设置
    b = 911382629  # 大基数
    q = 10**18 + 3  # 极大素数
    
    # 预处理
    h = pow(b, m-1, q)
    
    # 计算所有模式串的哈希值
    pattern_hashes = {}
    for p in patterns:
        hash_p = 0
        for c in p:
            hash_p = (hash_p * b + ord(c)) % q
        if hash_p not in pattern_hashes:
            pattern_hashes[hash_p] = []
        pattern_hashes[hash_p].append(p)
    
    # 计算主串第一个子串哈希值
    hash_t = 0
    for i in range(m):
        hash_t = (hash_t * b + ord(text[i])) % q
    
    # 结果字典
    results = {p: [] for p in patterns}
    
    # 开始匹配
    for i in range(n - m + 1):
        # 检查当前哈希值是否在模式串哈希集合中
        if hash_t in pattern_hashes:
            # 对所有可能匹配的模式串进行验证
            current_sub = text[i:i+m]
            for p in pattern_hashes[hash_t]:
                if current_sub == p:
                    results[p].append(i)
        
        # 计算下一个子串哈希值
        if i < n - m:
            hash_t = ( (hash_t - ord(text[i]) * h) * b + ord(text[i + m]) ) % q
            if hash_t < 0:
                hash_t += q
    
    return results
```

### 带随机化的实现（减少哈希冲突）
```python
def rabin_karp_randomized(text, pattern):
    """
    带随机化的Rabin-Karp算法，降低哈希冲突概率
    使用双哈希函数进一步减少冲突
    """
    import random
    n = len(text)
    m = len(pattern)
    
    if m == 0: return 0
    if n < m: return -1
    
    # 随机选择两个不同的素数和基数
    q1 = random.getrandbits(64) + (1 << 63)  # 64位素数
    q2 = random.getrandbits(64) + (1 << 63)
    b1 = random.getrandbits(32) + 10**9
    b2 = random.getrandbits(32) + 10**9
    
    # 计算两个基数的(m-1)次幂
    h1 = pow(b1, m-1, q1)
    h2 = pow(b2, m-1, q2)
    
    # 计算模式串的双哈希值
    hp1, hp2 = 0, 0
    for c in pattern:
        hp1 = (hp1 * b1 + ord(c)) % q1
        hp2 = (hp2 * b2 + ord(c)) % q2
    
    # 计算主串第一个子串的双哈希值
    ht1, ht2 = 0, 0
    for i in range(m):
        ht1 = (ht1 * b1 + ord(text[i])) % q1
        ht2 = (ht2 * b2 + ord(text[i])) % q2
    
    # 开始匹配
    for i in range(n - m + 1):
        # 双哈希值都匹配才进行验证
        if ht1 == hp1 and ht2 == hp2:
            match = True
            for j in range(m):
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                return i
        
        # 计算下一个子串的双哈希值
        if i < n - m:
            ht1 = ( (ht1 - ord(text[i]) * h1) * b1 + ord(text[i + m]) ) % q1
            ht2 = ( (ht2 - ord(text[i]) * h2) * b2 + ord(text[i + m]) ) % q2
            if ht1 < 0: ht1 += q1
            if ht2 < 0: ht2 += q2
    
    return -1
```

---

## 📊 复杂度分析

### 时间复杂度
- **预处理阶段**: O(m)，其中m为模式串长度
- **匹配阶段**: 
  - 平均情况: O(n + m)，当哈希冲突较少时
  - 最坏情况: O(nm)，当所有子串哈希值都与模式串哈希值相等时
- **总体复杂度**: 平均O(n + m)，最坏O(nm)

### 空间复杂度
- **空间复杂度**: O(1)，基本实现只需常数空间
- **多模式匹配**: O(k)，其中k为模式串数量

### 复杂度对比表
| 操作 | 时间复杂度 | 空间复杂度 | 说明 |
|------|------------|------------|------|
| 哈希值计算 | O(m) | O(1) | 模式串和主串初始子串哈希计算 |
| 滚动哈希 | O(1) | O(1) | 每个后续子串的哈希值计算 |
| 哈希比较 | O(1) | O(1) | 仅比较哈希值 |
| 冲突验证 | O(m) | O(1) | 哈希值匹配时进行完整字符比较 |
| 最佳情况 | O(n + m) | O(1) | 无哈希冲突时 |
| 最坏情况 | O(nm) | O(1) | 所有子串都需验证时 |

---

## 🔍 应用场景

1. ** plagiarism detection **：论文抄袭检测系统
2. ** 搜索引擎 **：大规模文本索引和关键词搜索
3. ** 生物信息学 **：DNA序列匹配和基因分析
4. ** 网络安全 **：入侵检测和病毒特征码扫描
5. ** 文本编辑器 **：多关键词查找功能
6. ** 数据库 **：字符串匹配索引实现
7. ** 版本控制系统 **：文件差异比较
8. ** 自然语言处理 **：文本分类和信息提取

---

## ⚠️ 注意事项

1.** 哈希冲突 **：哈希值相等不代表字符串一定匹配，必须进行实际字符验证
2.** 参数选择 **：
   - 基数b应大于字符集大小
   - 素数q应尽可能大，减少冲突概率
   - 推荐使用双哈希（两个不同的b和q）进一步降低冲突
3.** 数值溢出 **：哈希计算可能产生大整数，需使用模运算和大整数类型
4.** 模式串长度 **：所有模式串必须具有相同长度（多模式匹配时）
5.** 预处理开销 **：对于极短模式串，预处理时间可能超过简单比较
6.** 非ASCII字符 **：需调整基数以适应更大的字符集（如Unicode）
7.** 性能调优 **：实际应用中可缓存常用模式串的哈希值

---

## 🎓 最佳实践

1.** 参数优化 **：
   - 选择合适的基数和素数：推荐使用大素数（如10^9+7）和大基数
   - 对不同应用场景调整参数，平衡效率和冲突率
2.** 冲突处理 **：
   - 始终实现哈希冲突验证步骤
   - 对关键应用使用双哈希或多重哈希
3.** 多模式匹配 **：
   - 将所有模式串哈希值存储在哈希表中
   - 一次扫描主串即可匹配多个模式串
4.** 性能优化 **：
   - 预计算并缓存b^(m-1) mod q值
   - 使用位运算和快速模运算优化计算
   - 对长文本使用分块处理
5.** 应用选择 **：
   - 单模式短文本：考虑KMP或Boyer-Moore
   - 多模式匹配：优先选择Rabin-Karp
   - 大规模文本：Rabin-Karp的滚动哈希优势明显

---

## 📚 扩展阅读
- [维基百科：Rabin-Karp算法](https://en.wikipedia.org/wiki/Rabin%E2%80%93Karp_algorithm)
- 《算法导论》第32章：字符串匹配
- 《计算机程序设计艺术》第3卷：排序与查找
- [Rabin-Karp算法原始论文](https://www.cs.princeton.edu/courses/archive/spr04/cos598B/bib/rabin-karp.pdf)
- [哈希函数设计指南](https://cp-algorithms.com/string/rabin-karp.html)
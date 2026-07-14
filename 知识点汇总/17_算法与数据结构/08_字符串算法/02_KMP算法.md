# KMP算法

> KMP算法（Knuth-Morris-Pratt算法）是一种高效的字符串匹配算法，通过预处理模式串构建前缀函数，避免了主串指针的回溯，从而提高匹配效率。

---

## 📋 基本信息

### 定义
KMP算法是一种改进的字符串匹配算法，由Knuth、Morris和Pratt共同提出，其核心思想是利用已匹配的信息，通过构建前缀函数（部分匹配表）来避免不必要的字符比较。

### 核心思想
通过预处理模式串，计算出一个前缀数组（next数组），该数组记录了模式串中每个位置的最长前缀后缀匹配长度。当匹配过程中出现不匹配时，利用前缀数组可以直接将模式串滑动到合适的位置，而无需回溯主串指针。

### 与其他算法对比
| 算法 | 时间复杂度(预处理) | 时间复杂度(匹配) | 空间复杂度 | 特点 |
|------|-------------------|------------------|------------|------|
| KMP算法 | O(m) | O(n) | O(m) | 无回溯，适合单模式匹配 |
| 暴力匹配 | O(1) | O(m*n) | O(1) | 简单但效率低 |
| Boyer-Moore | O(m+k) | O(n/m) | O(k) | 实际应用中效率最高 |
| Rabin-Karp | O(m) | O(n+m) | O(1) | 适合多模式匹配 |

---

## 🎯 算法原理

### 前缀函数（Next数组）
前缀函数是KMP算法的核心，对于模式串P，前缀函数next[i]表示P[0..i]的最长前缀同时也是后缀的长度（不包括整个子串本身）。

**计算示例**：
模式串: "ABABC"
- next[0] = 0（单个字符无前后缀）
- next[1] = 0（"AB"无前缀后缀匹配）
- next[2] = 1（"ABA"的前缀"A"与后缀"A"匹配）
- next[3] = 2（"ABAB"的前缀"AB"与后缀"AB"匹配）
- next[4] = 0（"ABABC"无前缀后缀匹配）

### 算法步骤
1. **预处理阶段**：计算模式串的前缀函数（next数组）
2. **匹配阶段**：
   - 初始化主串指针i=0，模式串指针j=0
   - 比较主串和模式串字符：text[i]与pattern[j]
   - 若匹配，i和j同时递增
   - 若不匹配：
     - j = next[j-1]（利用前缀函数回溯模式串指针）
     - 若j=0仍不匹配，则i递增
   - 当j等于模式串长度时，找到匹配位置

### 图解说明
```
主串: A B A B A B C
模式串: A B A B C
next数组: [0,0,1,2,0]

匹配过程:
初始状态: i=0, j=0
A B A B A B C
A B A B C
i=0,j=0: 匹配,i=1,j=1
A B A B A B C
  A B A B C
i=1,j=1: 匹配,i=2,j=2
A B A B A B C
    A B A B C
i=2,j=2: 匹配,i=3,j=3
A B A B A B C
      A B A B C
i=3,j=3: 匹配,i=4,j=4
A B A B A B C
        A B A B C
i=4,j=4: 不匹配(j=4, next[j-1]=next[3]=2), j=2
A B A B A B C
    A B A B C
i=4,j=2: 匹配,i=5,j=3
A B A B A B C
      A B A B C
i=5,j=3: 匹配,i=6,j=4
A B A B A B C
        A B A B C
i=6,j=4: 不匹配(j=4, next[j-1]=next[3]=2), j=2
A B A B A B C
    A B A B C
i=6,j=2: 不匹配(j=2, next[j-1]=next[1]=0), j=0
A B A B A B C
A B A B C
i=6,j=0: 不匹配,i=7(超出主串长度),匹配失败
```

---

## 💻 代码实现

### 基本实现（前缀函数与匹配）
```python
def kmp_search(text, pattern):
    """
    KMP算法实现字符串匹配
    :param text: 主串
    :param pattern: 模式串
    :return: 匹配起始位置，未找到返回-1
    """
    def compute_prefix(pattern):
        """计算模式串的前缀函数(next数组)"""
        m = len(pattern)
        next_arr = [0] * m
        j = 0  # 前缀长度
        
        for i in range(1, m):
            # 当不匹配时，回溯j到前一个前缀长度
            while j > 0 and pattern[i] != pattern[j]:
                j = next_arr[j-1]
            # 当匹配时，前缀长度+1
            if pattern[i] == pattern[j]:
                j += 1
                next_arr[i] = j
            else:
                next_arr[i] = 0
        return next_arr
    
    n = len(text)
    m = len(pattern)
    if m == 0:
        return 0
    
    next_arr = compute_prefix(pattern)
    j = 0  # 模式串指针
    
    for i in range(n):
        # 不匹配时，利用next数组回溯模式串指针
        while j > 0 and text[i] != pattern[j]:
            j = next_arr[j-1]
        # 匹配时，移动模式串指针
        if text[i] == pattern[j]:
            j += 1
        # 找到匹配
        if j == m:
            return i - m + 1
    
    return -1
```

### 带前缀函数打印的实现
```python
def kmp_with_prefix_print(pattern):
    """计算前缀函数并打印中间过程"""
    m = len(pattern)
    next_arr = [0] * m
    j = 0
    
    print("模式串:", pattern)
    print("索引 | 字符 | 前缀函数值")
    print(f"0 | {pattern[0]} | 0")
    
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = next_arr[j-1]
        
        if pattern[i] == pattern[j]:
            j += 1
            next_arr[i] = j
        else:
            next_arr[i] = 0
        
        print(f"{i} | {pattern[i]} | {next_arr[i]}")
    
    return next_arr
```

### 多模式匹配实现
```python
def kmp_multiple_matches(text, pattern):
    """
    KMP算法查找所有匹配位置
    :return: 所有匹配起始位置的列表
    """
    def compute_prefix(pattern):
        m = len(pattern)
        next_arr = [0] * m
        j = 0
        for i in range(1, m):
            while j > 0 and pattern[i] != pattern[j]:
                j = next_arr[j-1]
            if pattern[i] == pattern[j]:
                j += 1
                next_arr[i] = j
            else:
                next_arr[i] = 0
        return next_arr
    
    n = len(text)
    m = len(pattern)
    matches = []
    
    if m == 0 or n < m:
        return matches
    
    next_arr = compute_prefix(pattern)
    j = 0
    
    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = next_arr[j-1]
        
        if text[i] == pattern[j]:
            j += 1
        
        if j == m:
            matches.append(i - m + 1)
            j = next_arr[j-1]  # 继续查找下一个匹配
    
    return matches
```

---

## 📊 复杂度分析

### 时间复杂度
- **预处理阶段**: O(m)，其中m为模式串长度
- **匹配阶段**: O(n)，其中n为主串长度
- **总体复杂度**: O(m+n)

### 空间复杂度
- **空间复杂度**: O(m)，主要用于存储前缀函数数组

### 复杂度对比表
| 操作 | 时间复杂度 | 说明 |
|------|------------|------|
| 前缀函数计算 | O(m) | 只需遍历模式串一次 |
| 主串匹配 | O(n) | 主串指针只向前移动，不回溯 |
| 最坏情况 | O(m+n) | 比暴力匹配的O(m*n)有显著提升 |
| 平均情况 | O(m+n) | 实际应用中表现稳定 |

---

## 🔍 应用场景

1. **文本编辑器**：高效的查找替换功能
2. **生物信息学**：DNA序列匹配分析
3. **网络安全**：入侵检测系统中的特征匹配
4. **搜索引擎**：关键词匹配和索引构建
5. **编译器**：语法分析中的模式匹配
6. **数据压缩**：LZ77算法中的重复序列查找
7. **自然语言处理**：分词和语法检查

---

## ⚠️ 注意事项

1. **前缀函数理解难度**：KMP算法的核心难点在于前缀函数的理解和计算
2. **边界条件处理**：需特别注意空模式串、模式串长于主串等特殊情况
3. **前缀函数实现细节**：不同实现可能存在细微差异，需确保逻辑正确性
4. **多模式匹配限制**：KMP算法本身是单模式匹配算法，多模式匹配需额外处理
5. **内存使用**：对于极长模式串，前缀数组会占用较多内存
6. **调试难度**：算法逻辑相对复杂，调试时建议添加详细日志

---

## 🎓 最佳实践

1. **正确实现前缀函数**：确保前缀函数计算正确，这是KMP算法的核心
2. **处理重复匹配**：如需查找所有匹配位置，匹配成功后应使用next数组继续查找
3. **结合实际需求**：
   - 单模式匹配：使用基本KMP实现
   - 多模式匹配：考虑AC自动机或结合其他算法
4. **性能优化**：
   - 对于多次匹配同一模式串的场景，可缓存前缀函数
   - 对于字符集较小的情况，可考虑使用位运算优化
5. **代码可读性**：实现时添加详细注释，特别是前缀函数部分
6. **测试用例覆盖**：测试包括普通情况、边界情况、特殊模式串等

---

## 📚 扩展阅读
- [维基百科：KMP算法](https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm)
- 《算法导论》第32章：字符串匹配
- 《计算机程序设计艺术》第3卷：排序与查找
- [KMP算法详解](https://www.geeksforgeeks.org/kmp-algorithm-for-pattern-searching/)
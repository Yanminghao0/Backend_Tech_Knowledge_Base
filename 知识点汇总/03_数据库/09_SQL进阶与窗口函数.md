# SQL进阶与窗口函数

> 掌握窗口函数、CTE、行转列等SQL高级技巧，提升数据查询能力

---

## 📋 目录

1. [窗口函数概述](#1-窗口函数概述)
2. [排序窗口函数](#2-排序窗口函数)
3. [偏移窗口函数](#3-偏移窗口函数)
4. [聚合窗口函数](#4-聚合窗口函数)
5. [CTE公共表表达式](#5-cte公共表表达式)
6. [行转列与列转行](#6-行转列与列转行)
7. [实战案例](#7-实战案例)
8. [面试题速查](#8-面试题速查)

---

## 1. 窗口函数概述

```sql
-- 窗口函数语法
函数名(参数) OVER (
    PARTITION BY 分组字段    -- 类似GROUP BY但不合并行
    ORDER BY 排序字段        -- 窗口内排序
    ROWS/RANGE BETWEEN ...   -- 窗口帧范围
)

-- 窗口函数 vs 聚合函数
-- 聚合函数：GROUP BY后每组合并为一行
-- 窗口函数：每行都保留，额外附加计算结果

-- 示例：每个部门薪资排名
SELECT 
    emp_name, dept, salary,
    RANK() OVER (PARTITION BY dept ORDER BY salary DESC) as dept_rank
FROM employees;
```

---

## 2. 排序窗口函数

```sql
-- ROW_NUMBER()：唯一连续编号（1,2,3,4,5）
SELECT emp_name, salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) as row_num
FROM employees;

-- RANK()：并列跳号（1,2,2,4,5）— 并列后跳过
SELECT emp_name, salary,
    RANK() OVER (ORDER BY salary DESC) as rank_num
FROM employees;

-- DENSE_RANK()：并列不跳号（1,2,2,3,4）— 并列后不跳
SELECT emp_name, salary,
    DENSE_RANK() OVER (ORDER BY salary DESC) as dense_rank
FROM employees;

-- NTILE(n)：分桶（均匀分为n组）
SELECT emp_name, salary,
    NTILE(4) OVER (ORDER BY salary DESC) as quartile  -- 四分位
FROM employees;

-- 实战：取每个部门薪资前3名
SELECT * FROM (
    SELECT emp_name, dept, salary,
        ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) as rn
    FROM employees
) t WHERE rn <= 3;
```

---

## 3. 偏移窗口函数

```sql
-- LAG()：取前N行的值
SELECT emp_name, dept, salary,
    LAG(salary, 1) OVER (PARTITION BY dept ORDER BY hire_date) as prev_salary,
    salary - LAG(salary, 1) OVER (PARTITION BY dept ORDER BY hire_date) as diff
FROM employees;

-- LEAD()：取后N行的值
SELECT emp_name, hire_date,
    LEAD(emp_name, 1) OVER (ORDER BY hire_date) as next_employee
FROM employees;

-- FIRST_VALUE() / LAST_VALUE()：窗口内第一个/最后一个值
SELECT emp_name, dept, salary,
    FIRST_VALUE(salary) OVER (PARTITION BY dept ORDER BY salary DESC) as max_in_dept,
    LAST_VALUE(salary) OVER (
        PARTITION BY dept ORDER BY salary DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) as min_in_dept
FROM employees;

-- 实战：计算环比增长率
SELECT month, revenue,
    LAG(revenue, 1) OVER (ORDER BY month) as prev_month,
    ROUND((revenue - LAG(revenue, 1) OVER (ORDER BY month)) 
        / LAG(revenue, 1) OVER (ORDER BY month) * 100, 2) as growth_rate
FROM monthly_sales;
```

---

## 4. 聚合窗口函数

```sql
-- 累计求和
SELECT emp_name, dept, salary, hire_date,
    SUM(salary) OVER (
        PARTITION BY dept 
        ORDER BY hire_date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as running_total
FROM employees;

-- 移动平均（最近3个月）
SELECT month, revenue,
    ROUND(AVG(revenue) OVER (
        ORDER BY month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) as moving_avg_3m
FROM monthly_sales;

-- 窗口帧说明：
-- UNBOUNDED PRECEDING  — 从第一行开始
-- N PRECEDING          — 前N行
-- CURRENT ROW          — 当前行
-- N FOLLOWING          — 后N行
-- UNBOUNDED FOLLOWING  — 到最后一行

-- 部门薪资占比
SELECT emp_name, dept, salary,
    ROUND(salary * 100.0 / SUM(salary) OVER (PARTITION BY dept), 2) as pct_of_dept
FROM employees;
```

---

## 5. CTE公共表表达式

```sql
-- 基本CTE：提高可读性
WITH dept_avg AS (
    SELECT dept, AVG(salary) as avg_salary
    FROM employees
    GROUP BY dept
)
SELECT e.emp_name, e.dept, e.salary, d.avg_salary
FROM employees e
JOIN dept_avg d ON e.dept = d.dept
WHERE e.salary > d.avg_salary;

-- 递归CTE：组织架构树
WITH RECURSIVE org_tree AS (
    -- 锚点：顶层管理者
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    -- 递归：下属
    SELECT e.id, e.name, e.manager_id, t.level + 1
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.id
)
SELECT id, name, level FROM org_tree ORDER BY level;

-- 多CTE
WITH 
high_salary AS (
    SELECT * FROM employees WHERE salary > 20000
),
dept_count AS (
    SELECT dept, COUNT(*) as cnt FROM high_salary GROUP BY dept
)
SELECT dept, cnt FROM dept_count WHERE cnt >= 3 ORDER BY cnt DESC;
```

---

## 6. 行转列与列转行

```sql
-- 行转列：CASE WHEN
SELECT dept,
    SUM(CASE WHEN job = 'MANAGER' THEN 1 ELSE 0 END) as manager_count,
    SUM(CASE WHEN job = 'CLERK' THEN 1 ELSE 0 END) as clerk_count,
    SUM(CASE WHEN job = 'ANALYST' THEN 1 ELSE 0 END) as analyst_count
FROM employees
GROUP BY dept;

-- 行转列：PIVOT（MySQL 8.0+不支持，用条件聚合替代）
-- 列转行：UNION ALL
SELECT emp_name, 'salary' as item, salary as value FROM employees
UNION ALL
SELECT emp_name, 'bonus' as item, bonus as value FROM employees
ORDER BY emp_name, item;
```

---

## 7. 实战案例

```sql
-- 案例1：连续登录N天的用户
SELECT DISTINCT user_id FROM (
    SELECT user_id, login_date,
        login_date - INTERVAL ROW_NUMBER() OVER (
            PARTITION BY user_id ORDER BY login_date
        ) DAY as grp
    FROM user_login_log
) t 
GROUP BY user_id, grp 
HAVING COUNT(*) >= 7;

-- 案例2：每个用户最近3笔订单
SELECT * FROM (
    SELECT order_id, user_id, amount, create_time,
        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY create_time DESC) as rn
    FROM orders
) t WHERE rn <= 3;

-- 案例3：部门薪资Top1（含并列）
SELECT emp_name, dept, salary FROM (
    SELECT emp_name, dept, salary,
        DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) as rk
    FROM employees
) t WHERE rk = 1;
```

---

## 8. 面试题速查

**Q1: ROW_NUMBER、RANK、DENSE_RANK的区别？**
```
ROW_NUMBER: 1,2,3,4,5 — 唯一不重复
RANK: 1,2,2,4,5 — 并列后跳号
DENSE_RANK: 1,2,2,3,4 — 并列不跳号
```

**Q2: 窗口函数和GROUP BY的区别？**
```
GROUP BY：每组合并为一行，丢失明细
窗口函数：每行保留，额外附加聚合计算结果
窗口函数适合"既要明细又要聚合"的场景
```

**Q3: 如何取每组Top N？**
```sql
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY 分组字段 ORDER BY 排序字段 DESC) as rn
    FROM 表
) t WHERE rn <= N;
```

**Q4: LAG和LEAD的作用？**
```
LAG：取当前行之前第N行的值（前对比）
LEAD：取当前行之后第N行的值（后对比）
常用于计算环比、同比、差值
```

---

*最后更新：2026-07-13*

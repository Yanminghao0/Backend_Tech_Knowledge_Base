# HTML/CSS/JS速成

> 后端工程师的前端基础：HTML语义化、CSS布局、ES6+核心语法

---

## 📋 目录

1. [HTML基础](#1-html基础)
2. [CSS布局](#2-css布局)
3. [ES6+核心语法](#3-es6核心语法)
4. [DOM操作与事件](#4-dom操作与事件)
5. [面试题速查](#5-面试题速查)

---

## 1. HTML基础

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面标题</title>
</head>
<body>
    <!-- 语义化标签 -->
    <header>头部导航</header>
    <nav>导航栏</nav>
    <main>
        <article>文章内容</article>
        <aside>侧边栏</aside>
    </main>
    <section>内容区块</section>
    <footer>页脚</footer>

    <!-- 常用标签 -->
    <h1>~<h6> 标题
    <p>段落</p>
    <a href="url" target="_blank">链接</a>
    <img src="url" alt="描述">
    <ul><li>无序列表</li></ul>
    <ol><li>有序列表</li></ol>
    <table><tr><td>表格</td></tr></table>
    <div>块容器</div>
    <span>行内容器</span>

    <!-- 表单 -->
    <form action="/api/login" method="POST">
        <input type="text" name="username" placeholder="用户名">
        <input type="password" name="password" placeholder="密码">
        <input type="email" name="email">
        <input type="number" name="age">
        <input type="date" name="birthday">
        <input type="checkbox" name="agree">
        <input type="radio" name="gender" value="male">
        <select name="city">
            <option value="bj">北京</option>
            <option value="sh">上海</option>
        </select>
        <textarea name="bio"></textarea>
        <button type="submit">提交</button>
    </form>
</body>
</html>

<!-- 语义化的好处:
1. SEO友好 — 搜索引擎理解页面结构
2. 可访问性 — 屏幕阅读器更好解析
3. 代码可读性 — 比全是div更清晰
-->
```

---

## 2. CSS布局

### 2.1 Flex布局

```css
/* Flex — 一维布局(行或列) */
.container {
    display: flex;
    flex-direction: row;        /* row | column | row-reverse | column-reverse */
    justify-content: center;    /* 主轴对齐: flex-start|center|flex-end|space-between|space-around */
    align-items: center;        /* 交叉轴对齐: flex-start|center|flex-end|stretch */
    flex-wrap: wrap;            /* 换行: nowrap|wrap|wrap-reverse */
    gap: 10px;                  /* 间距 */
}

.item {
    flex: 1;                    /* flex-grow: 1, 占满剩余空间 */
    flex: 0 0 200px;            /* grow shrink basis */
    order: 2;                   /* 排序 */
    align-self: flex-end;       /* 单独对齐 */
}

/* 常见布局: 水平居中 */
.center { display: flex; justify-content: center; align-items: center; }

/* 常见布局: 两栏(左固定右自适应) */
.two-col { display: flex; }
.left { width: 200px; }
.right { flex: 1; }
```

### 2.2 Grid布局

```css
/* Grid — 二维布局(行+列) */
.grid-container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;  /* 三列, 比例1:2:1 */
    grid-template-rows: 100px auto 100px; /* 三行 */
    gap: 10px;
    /* 或 repeat(3, 1fr) = 三等分 */
    /* 或 repeat(auto-fill, minmax(200px, 1fr)) = 自适应列数 */
}

.item {
    grid-column: 1 / 3;   /* 跨1-2列 */
    grid-row: 1 / 2;      /* 第1行 */
}

/* 常见布局: 三栏(圣杯布局) */
.holy-grail {
    display: grid;
    grid-template-areas:
        "header header header"
        "left   main   right"
        "footer footer footer";
    grid-template-columns: 200px 1fr 200px;
    grid-template-rows: 60px 1fr 40px;
}
.header { grid-area: header; }
.left { grid-area: left; }
.main { grid-area: main; }
.right { grid-area: right; }
.footer { grid-area: footer; }
```

### 2.3 常用CSS

```css
/* 盒模型 */
.box {
    box-sizing: border-box;  /* width包含padding+border(推荐) */
    margin: 10px 20px;       /* 上下 左右 */
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 8px;
    width: 100%;
    height: auto;
}

/* 定位 */
.relative { position: relative; top: 10px; }
.absolute { position: absolute; top: 0; right: 0; }
.fixed { position: fixed; bottom: 0; width: 100%; }

/* 响应式 */
@media (max-width: 768px) {
    .container { flex-direction: column; }
}

/* 变量 */
:root {
    --primary-color: #409eff;
    --font-size: 14px;
}
.btn { color: var(--primary-color); font-size: var(--font-size); }

/* 过渡与动画 */
.transition { transition: all 0.3s ease; }
.transition:hover { transform: scale(1.05); }

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
.animate { animation: fadeIn 0.5s ease; }
```

---

## 3. ES6+核心语法

### 3.1 变量与作用域

```javascript
// var vs let vs const
var x = 1;       // 函数作用域, 可重复声明, 会变量提升
let y = 2;       // 块级作用域, 不可重复声明
const z = 3;     // 块级作用域, 不可重新赋值(但对象内容可改)

// const对象内容可变
const obj = { name: 'Alice' };
obj.name = 'Bob';     // OK, 修改属性
// obj = {};           // Error, 重新赋值

// 解构赋值
const { name, age } = user;           // 对象解构
const [first, second] = array;        // 数组解构
const { name: userName = 'default' } = user;  // 重命名+默认值
function foo({ name, age = 18 }) { }  // 函数参数解构

// 模板字符串
const greeting = `Hello, ${name}! You are ${age} years old.`;
const html = `
    <div>
        <p>${name}</p>
    </div>
`;

// 展开运算符
const arr1 = [1, 2, 3];
const arr2 = [...arr1, 4, 5];         // [1,2,3,4,5]
const merged = { ...obj1, ...obj2 };  // 合并对象
function sum(...args) { return args.reduce((a, b) => a + b, 0); }
```

### 3.2 箭头函数与this

```javascript
// 箭头函数
const add = (a, b) => a + b;
const square = x => x * x;
const greet = () => console.log('Hello');
const obj = { method() { return 42; } };

// 箭头函数 vs 普通函数的this
const obj = {
    name: 'Alice',
    // 普通函数: this指向调用者
    normalFunc: function() {
        console.log(this.name);  // 'Alice'
        setTimeout(function() {
            console.log(this.name);  // undefined (this指向window)
        }, 100);
    },
    // 箭头函数: this继承外层(词法作用域)
    arrowFunc: function() {
        console.log(this.name);  // 'Alice'
        setTimeout(() => {
            console.log(this.name);  // 'Alice' (继承外层this)
        }, 100);
    }
};

// 箭头函数特点:
// 1. 没有自己的this(继承外层)
// 2. 不能作为构造函数(new报错)
// 3. 没有arguments对象
// 4. 不能用作Generator
```

### 3.3 Promise与async/await

```javascript
// Promise — 异步操作
const fetchUser = (userId) => {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (userId > 0) {
                resolve({ id: userId, name: 'Alice' });
            } else {
                reject(new Error('Invalid userId'));
            }
        }, 1000);
    });
};

// 链式调用
fetchUser(1)
    .then(user => fetchOrders(user.id))
    .then(orders => console.log(orders))
    .catch(err => console.error(err))
    .finally(() => console.log('Done'));

// Promise.all — 全部完成
Promise.all([fetchUser(1), fetchUser(2), fetchUser(3)])
    .then(users => console.log(users))  // [user1, user2, user3]
    .catch(err => console.error(err));  // 任一失败则失败

// Promise.race — 最快完成
Promise.race([fetchUser(1), timeout(5000)])
    .then(user => console.log(user))
    .catch(err => console.error('Timeout or error'));

// async/await — 同步写法写异步代码
async function getUserOrders(userId) {
    try {
        const user = await fetchUser(userId);
        const orders = await fetchOrders(user.id);
        return orders;
    } catch (err) {
        console.error('Failed:', err);
        throw err;
    }
}

// 并发请求(不等一个个完成)
async function fetchAll() {
    const [user, settings, notifications] = await Promise.all([
        fetchUser(1),
        fetchSettings(),
        fetchNotifications()
    ]);
    return { user, settings, notifications };
}
```

### 3.4 数组与对象方法

```javascript
// 数组方法
const arr = [1, 2, 3, 4, 5];

arr.map(x => x * 2);           // [2,4,6,8,10] — 映射
arr.filter(x => x > 2);        // [3,4,5] — 过滤
arr.reduce((sum, x) => sum + x, 0);  // 15 — 聚合
arr.find(x => x > 3);          // 4 — 找第一个
arr.some(x => x > 3);          // true — 是否有满足的
arr.every(x => x > 0);         // true — 是否全部满足
arr.includes(3);               // true — 是否包含
arr.flat();                    // 扁平化
arr.flatMap(x => [x, x*2]);   // 映射+扁平化

// 对象方法
const obj = { a: 1, b: 2 };
Object.keys(obj);              // ['a', 'b']
Object.values(obj);            // [1, 2]
Object.entries(obj);           // [['a',1], ['b',2]]
Object.assign({}, obj, { c: 3 });  // 合并
const cloned = { ...obj };     // 浅拷贝
const { a, ...rest } = obj;   // 解构剩余

// Map/Set
const map = new Map([['key', 'value']]);
map.set('key2', 'value2');
map.get('key');
map.has('key');
map.forEach((v, k) => console.log(k, v));

const set = new Set([1, 2, 3, 2, 1]);  // {1, 2, 3} 去重
set.add(4);
set.has(1);
[...set];  // [1,2,3,4] 转数组
```

---

## 4. DOM操作与事件

```javascript
// DOM选择
document.getElementById('id');
document.querySelector('.class');        // CSS选择器, 第一个
document.querySelectorAll('.class');     // 所有匹配

// DOM操作
const el = document.createElement('div');
el.textContent = 'Hello';
el.innerHTML = '<span>HTML内容</span>';
el.classList.add('active');
el.classList.remove('hidden');
el.setAttribute('data-id', '123');
el.style.color = 'red';

const parent = document.querySelector('#container');
parent.appendChild(el);
parent.removeChild(el);

// 事件
el.addEventListener('click', (event) => {
    event.preventDefault();   // 阻止默认行为
    event.stopPropagation();  // 阻止冒泡
    console.log(event.target);  // 触发元素
});

// 事件委托(利用冒泡)
document.querySelector('#list').addEventListener('click', (e) => {
    if (e.target.tagName === 'LI') {
        console.log('Clicked:', e.target.textContent);
    }
});

// 防抖与节流
// 防抖: 连续触发只执行最后一次(搜索框输入)
function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}
const debouncedSearch = debounce(search, 300);
input.addEventListener('input', debouncedSearch);

// 节流: 固定频率执行(滚动事件)
function throttle(fn, interval) {
    let lastTime = 0;
    return function(...args) {
        const now = Date.now();
        if (now - lastTime >= interval) {
            lastTime = now;
            fn.apply(this, args);
        }
    };
}
const throttledScroll = throttle(onScroll, 100);
window.addEventListener('scroll', throttledScroll);
```

---

## 5. 面试题速查

**Q1: let/const/var的区别？**

```
var: 函数作用域, 可重复声明, 变量提升, 值可改
let: 块级作用域, 不可重复声明, 有暂时性死区, 值可改
const: 块级作用域, 不可重复声明, 不可重新赋值(对象属性可改)
推荐: 默认const, 需要改用let, 不用var
```

**Q2: 箭头函数和普通函数的区别？**

```
箭头函数: 没有this(继承外层), 不能new, 没有arguments
普通函数: 有自己的this(指向调用者), 可new, 有arguments
场景: 回调/简短逻辑用箭头函数, 对象方法/构造函数用普通函数
```

**Q3: Promise.all和Promise.race的区别？**

```
Promise.all: 全部成功才成功, 任一失败则失败, 返回数组
Promise.race: 最先完成的(成功或失败)作为结果
场景: all用于并行请求全部需要, race用于超时控制
```

**Q4: 防抖和节流的区别？**

```
防抖(debounce): 连续触发只执行最后一次 — 搜索框输入
节流(throttle): 固定间隔执行一次 — 滚动/resize
都是优化高频事件的方法
```

**Q5: ==和===的区别？**

```
==  松散比较, 会类型转换 (1 == '1' → true)
=== 严格比较, 不转换类型 (1 === '1' → false)
推荐: 始终用===
```

---

*最后更新：2026-07-13*

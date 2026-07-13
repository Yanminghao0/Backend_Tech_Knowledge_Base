# React核心原理

> JSX语法、Hooks体系、状态管理、React Router与Fiber架构

---

## 📋 目录

1. [React概述](#1-react概述)
2. [JSX与组件](#2-jsx与组件)
3. [Hooks体系](#3-hooks体系)
4. [状态管理](#4-状态管理)
5. [React Router](#5-react-router)
6. [Fiber架构](#6-fiber架构)
7. [面试题速查](#7-面试题速查)

---

## 1. React概述

```
React — Meta(Facebook)开源的UI库

  ┌──────────────────────────────────────────────────┐
  │  React               │  Vue                      │
  │  ─────              │  ────                     │
  │  JSX                │  模板语法                   │
  │  单向数据流           │  双向绑定(v-model)         │
  │  Hooks              │  Composition API           │
  │  Redux/Zustand      │  Pinia                     │
  │  生态丰富(大厂)       │  上手简单                  │
  │  灵活(只管UI)         │  全面(含路由/状态)         │
  └──────────────────────────────────────────────────┘

  React核心思想:
  1. 声明式UI — 描述状态, React自动更新DOM
  2. 组件化 — UI拆成可复用组件
  3. 单向数据流 — 数据从父到子, 不可逆
  4. 虚拟DOM — diff算法最小化DOM操作
```

```bash
# 创建React项目(Vite)
npm create vite@latest my-react-app -- --template react
cd my-react-app
npm install
npm run dev
```

---

## 2. JSX与组件

### 2.1 JSX语法

```jsx
// JSX = JavaScript + XML
// 在JS中写HTML-like语法

function Welcome({ name }) {
    // 表达式插值
    const age = 25;
    return (
        <div className="welcome">  {/* class → className */}
            <h1>Hello, {name}!</h1>
            <p>Age: {age}</p>
            <p>Next year: {age + 1}</p>

            {/* 条件渲染 */}
            {age >= 18 && <p>Adult</p>}
            {age < 18 ? <p>Minor</p> : <p>Adult</p>}

            {/* 列表渲染 */}
            <ul>
                {[1, 2, 3].map(n => (
                    <li key={n}>{n}</li>  {/* key必须唯一 */}
                ))}
            </ul>

            {/* 事件绑定 */}
            <button onClick={() => console.log('clicked')}>
                Click me
            </button>

            {/* 样式 */}
            <div style={{ color: 'red', fontSize: '14px' }}>
                Styled text
            </div>
        </div>
    );
}
```

### 2.2 函数组件

```jsx
import { useState, useEffect, useRef } from 'react';

// 函数组件 + Hooks
function Counter({ initialValue = 0, step = 1 }) {
    // useState — 状态
    const [count, setCount] = useState(initialValue);
    const [name, setName] = useState('');

    // useRef — 不触发重渲染的引用
    const inputRef = useRef(null);
    const renderCount = useRef(0);
    renderCount.current++;

    // useEffect — 副作用
    useEffect(() => {
        document.title = `Count: ${count}`;
        console.log(`Rendered ${renderCount.current} times`);

        // 清理函数
        return () => {
            console.log('Cleanup on unmount or before next effect');
        };
    }, [count]);  // 依赖数组: count变化时执行, 空数组=仅mount时, 无数组=每次渲染

    // 事件处理
    const handleIncrement = () => setCount(c => c + step);
    const handleDecrement = () => setCount(c => c - step);
    const handleReset = () => setCount(initialValue);
    const handleInput = (e) => setName(e.target.value);

    return (
        <div>
            <h2>Count: {count}</h2>
            <button onClick={handleIncrement}>+{step}</button>
            <button onClick={handleDecrement}>-{step}</button>
            <button onClick={handleReset}>Reset</button>

            <input ref={inputRef} value={name} onChange={handleInput} />
            <p>Hello, {name || 'Anonymous'}</p>
        </div>
    );
}

export default Counter;
```

---

## 3. Hooks体系

### 3.1 常用Hooks

```jsx
import { useState, useEffect, useMemo, useCallback, useRef, useContext, useReducer } from 'react';

// 1. useState — 状态管理
const [state, setState] = useState(initialValue);
setState(newState);           // 直接设值
setState(prev => prev + 1);   // 函数式更新(推荐)

// 2. useEffect — 副作用(订阅/定时器/请求)
useEffect(() => {
    const timer = setInterval(() => console.log('tick'), 1000);
    return () => clearInterval(timer);  // 清理
}, []);  // 空数组 = 仅mount执行一次

// 3. useMemo — 计算缓存(类似Vue computed)
const sortedList = useMemo(() => {
    return list.sort((a, b) => a - b);
}, [list]);  // list变化时才重新排序

// 4. useCallback — 函数缓存(避免子组件不必要重渲染)
const handleClick = useCallback(() => {
    console.log('clicked', count);
}, [count]);  // count变化时才重新创建函数

// 5. useRef — 可变引用(不触发重渲染)
const timerRef = useRef(null);
timerRef.current = setInterval(() => {}, 1000);

// 6. useContext — 跨组件数据
const theme = useContext(ThemeContext);

// 7. useReducer — 复杂状态(类似Redux)
const [state, dispatch] = useReducer(reducer, initialState);
dispatch({ type: 'INCREMENT' });
```

### 3.2 自定义Hook

```jsx
// useLocalStorage — 持久化状态
function useLocalStorage(key, initialValue) {
    const [value, setValue] = useState(() => {
        const stored = localStorage.getItem(key);
        return stored ? JSON.parse(stored) : initialValue;
    });

    useEffect(() => {
        localStorage.setItem(key, JSON.stringify(value));
    }, [key, value]);

    return [value, setValue];
}

// 使用
// const [token, setToken] = useLocalStorage('token', '');


// useFetch — 数据请求
function useFetch(url) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;
        const fetchData = async () => {
            setLoading(true);
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error('HTTP error');
                const json = await response.json();
                if (!cancelled) {
                    setData(json);
                    setError(null);
                }
            } catch (err) {
                if (!cancelled) setError(err.message);
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        fetchData();
        return () => { cancelled = true; };
    }, [url]);

    return { data, loading, error };
}

// 使用
// const { data, loading, error } = useFetch('/api/users');
```

### 3.3 useReducer — 复杂状态

```jsx
// 适合: 状态逻辑复杂, 下一个状态依赖前一个
function todoReducer(state, action) {
    switch (action.type) {
        case 'ADD':
            return [...state, {
                id: Date.now(),
                text: action.text,
                done: false
            }];
        case 'TOGGLE':
            return state.map(todo =>
                todo.id === action.id ? { ...todo, done: !todo.done } : todo
            );
        case 'DELETE':
            return state.filter(todo => todo.id !== action.id);
        case 'CLEAR_COMPLETED':
            return state.filter(todo => !todo.done);
        default:
            return state;
    }
}

function TodoApp() {
    const [todos, dispatch] = useReducer(todoReducer, []);
    const [input, setInput] = useState('');

    const addTodo = () => {
        if (input.trim()) {
            dispatch({ type: 'ADD', text: input });
            setInput('');
        }
    };

    return (
        <div>
            <input value={input} onChange={e => setInput(e.target.value)} />
            <button onClick={addTodo}>Add</button>
            <ul>
                {todos.map(todo => (
                    <li key={todo.id}>
                        <input
                            type="checkbox"
                            checked={todo.done}
                            onChange={() => dispatch({ type: 'TOGGLE', id: todo.id })}
                        />
                        <span style={{ textDecoration: todo.done ? 'line-through' : '' }}>
                            {todo.text}
                        </span>
                        <button onClick={() => dispatch({ type: 'DELETE', id: todo.id })}>
                            Delete
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
}
```

---

## 4. 状态管理

### 4.1 Context API

```jsx
import { createContext, useContext, useState } from 'react';

// 1. 创建Context
const AuthContext = createContext(null);

// 2. Provider组件
function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState('');

    const login = async (credentials) => {
        const response = await api.login(credentials);
        setUser(response.user);
        setToken(response.token);
    };

    const logout = () => {
        setUser(null);
        setToken('');
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

// 3. 使用
function Header() {
    const { user, logout } = useContext(AuthContext);
    return (
        <header>
            {user ? (
                <>
                    <span>{user.name}</span>
                    <button onClick={logout}>Logout</button>
                </>
            ) : (
                <a href="/login">Login</a>
            )}
        </header>
    );
}

// 4. 包裹App
function App() {
    return (
        <AuthProvider>
            <Header />
            <Main />
        </AuthProvider>
    );
}
```

### 4.2 Zustand(轻量状态管理)

```jsx
import { create } from 'zustand';

// 定义store
const useStore = create((set, get) => ({
    // state
    count: 0,
    user: null,

    // actions
    increment: () => set(state => ({ count: state.count + 1 })),
    decrement: () => set(state => ({ count: state.count - 1 })),
    setUser: (user) => set({ user }),

    // 计算属性
    getDoubleCount: () => get().count * 2,
}));

// 使用(自动订阅, 无需Provider)
function Counter() {
    const count = useStore(state => state.count);  // 选择性订阅
    const increment = useStore(state => state.increment);

    return (
        <div>
            <p>{count}</p>
            <button onClick={increment}>+1</button>
        </div>
    );
}
```

---

## 5. React Router

```jsx
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams, useLocation } from 'react-router-dom';

// 路由配置
function App() {
    return (
        <BrowserRouter>
            <nav>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
                <Link to="/user/123">User 123</Link>
            </nav>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/about" element={<About />} />
                <Route path="/user/:id" element={<UserPage />} />
                <Route path="/login" element={<Login />} />
                <Route
                    path="/admin/*"
                    element={
                        <ProtectedRoute>
                            <AdminLayout />
                        </ProtectedRoute>
                    }
                />
                <Route path="*" element={<NotFound />} />
            </Routes>
        </BrowserRouter>
    );
}

// 路由参数
function UserPage() {
    const { id } = useParams();        // URL参数
    const navigate = useNavigate();    // 编程导航
    const location = useLocation();    // 当前路由信息

    return (
        <div>
            <p>User ID: {id}</p>
            <button onClick={() => navigate('/')}>Go Home</button>
            <button onClick={() => navigate(-1)}>Go Back</button>
        </div>
    );
}

// 路由守卫
function ProtectedRoute({ children }) {
    const { token } = useAuth();
    const location = useLocation();

    if (!token) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }
    return children;
}
```

---

## 6. Fiber架构

```
React Fiber — React 16+的协调引擎

  核心思想: 将渲染拆分成小单元, 可中断/恢复

  ┌──────────────────────────────────────────────────┐
  │  传统Stack Reconciler   │  Fiber Reconciler      │
  │  ────────────────      │  ──────────────        │
  │  递归调用栈              │  链表结构               │
  │  不可中断                │  可中断/恢复            │
  │  大组件树卡顿            │  时间切片(5ms)          │
  │  同步渲染                │  异步渲染              │
  └──────────────────────────────────────────────────┘

  Fiber节点结构:
  {
    type: 'div',          // 组件类型
    key: null,
    child: Fiber | null,  // 第一个子节点
    sibling: Fiber | null,// 兄弟节点
    return: Fiber | null, // 父节点
    pendingProps: {},     // 待处理props
    memoizedProps: {},    // 已处理props
    memoizedState: {},    // 状态
    flags: 0,             // 副作用标记
  }

  双缓冲机制:
    current Fiber → workInProgress Fiber → DOM更新 → 切换

  两个阶段:
    1. Render阶段(可中断): 构建workInProgress Fiber树, 计算变更
    2. Commit阶段(不可中断): 应用变更到DOM, 执行副作用
```

```
React 18并发特性:

  1. useTransition — 标记非紧急更新
  const [isPending, startTransition] = useTransition();
  // 紧急更新: 输入框
  setInputValue(e.target.value);
  // 非紧急更新: 搜索结果(可中断)
  startTransition(() => {
    setSearchResults(results);
  });

  2. useDeferredValue — 延迟更新
  const deferredValue = useDeferredValue(value);
  // value变化时deferredValue延迟更新, 不阻塞输入

  3. Suspense — 异步组件
  <Suspense fallback={<Spinner />}>
    <LazyComponent />
  </Suspense>

  4. Automatic Batching — 自动批处理
  React 18自动合并多次状态更新为一次重渲染
```

---

## 7. 面试题速查

**Q1: React的虚拟DOM？**

```
虚拟DOM = JavaScript对象描述的DOM树
流程: JSX → 虚拟DOM → diff → 最小DOM操作
优势: 声明式编程, 跨平台, 批量更新
缺点: 首次渲染稍慢(多一层转换)
Fiber: React 16+拆分渲染为可中断的小单元
```

**Q2: useEffect的依赖数组？**

```
无数组: 每次渲染后执行
空数组[]: 仅mount时执行(类似mounted)
有依赖[a, b]: a或b变化时执行
返回清理函数: unmount或下次effect前执行
```

**Q3: useMemo和useCallback的区别？**

```
useMemo: 缓存计算结果(值), 类似computed
useCallback: 缓存函数引用, 避免子组件不必要重渲染
两者都是性能优化, 不要滥用(缓存本身有成本)
```

**Q4: React的key有什么作用？**

```
key帮助React识别哪些元素变化, 进行高效diff
无key: 默认按index, 可能导致状态错乱
有key: 精确匹配, 正确复用/销毁组件
规则: 唯一且稳定(不用index/random)
```

**Q5: React 18的并发特性？**

```
useTransition: 标记非紧急更新, 不阻塞输入
useDeferredValue: 延迟更新值
Suspense: 异步加载组件
Automatic Batching: 自动批处理状态更新
核心: 渲染可中断, 高优先级更新插队
```

---

*最后更新：2026-07-13*

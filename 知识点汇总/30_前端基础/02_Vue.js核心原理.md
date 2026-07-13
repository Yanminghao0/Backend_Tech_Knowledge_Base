# Vue.js核心原理

> 响应式系统、组件化、生命周期、路由与Pinia状态管理

---

## 📋 目录

1. [Vue概述](#1-vue概述)
2. [响应式系统](#2-响应式系统)
3. [组件化](#3-组件化)
4. [生命周期](#4-生命周期)
5. [Vue Router](#5-vue-router)
6. [Pinia状态管理](#6-pinia状态管理)
7. [面试题速查](#7-面试题速查)

---

## 1. Vue概述

```
Vue.js — 渐进式JavaScript框架

  ┌──────────────────────────────────────────────────┐
  │  Vue 2                │  Vue 3                    │
  │  ─────               │  ─────                    │
  │  Options API          │  Composition API          │
  │  Object.defineProperty│  Proxy                    │
  │  全局API(Vue.component)│  createApp               │
  │  mixin                │  composable(use函数)      │
  │  Vuex                 │  Pinia                    │
  │  单根节点              │  Fragment(多根)           │
  └──────────────────────────────────────────────────┘

  Vue 3优势:
  - 更快: Proxy代理, 编译优化, Tree-shaking
  - 更小: 按需引入, 打包体积小
  - 更强: TypeScript原生支持, Composition API
  - 更维护: 模块化架构, 自定义渲染器
```

```bash
# 创建Vue 3项目
npm create vue@latest my-app
cd my-app
npm install
npm run dev
```

---

## 2. 响应式系统

### 2.1 响应式原理

```javascript
// Vue 3 响应式 — 基于Proxy
import { ref, reactive, computed, watch, effect } from 'vue';

// ref — 基本类型响应式
const count = ref(0);
console.log(count.value);  // 0
count.value++;              // 触发更新

// reactive — 对象响应式
const state = reactive({
    name: 'Alice',
    age: 25
});
state.name = 'Bob';  // 直接触发更新, 不需要.value

// computed — 计算属性(缓存)
const doubleCount = computed(() => count.value * 2);
console.log(doubleCount.value);  // 0
count.value = 5;
console.log(doubleCount.value);  // 10

// watch — 侦听器
watch(count, (newVal, oldVal) => {
    console.log(`count: ${oldVal} → ${newVal}`);
});

// watchEffect — 自动追踪依赖
watchEffect(() => {
    console.log(`name is: ${state.name}`);  // 自动追踪state.name
});
```

### 2.2 响应式原理(简化版)

```javascript
// Vue 3 响应式核心 — Proxy + 依赖收集

let activeEffect = null;

function effect(fn) {
    activeEffect = fn;
    fn();          // 执行时触发依赖收集
    activeEffect = null;
}

function reactive(target) {
    const deps = new Map();  // key → Set<effect>

    return new Proxy(target, {
        get(obj, key) {
            // 依赖收集
            if (activeEffect) {
                if (!deps.has(key)) deps.set(key, new Set());
                deps.get(key).add(activeEffect);
            }
            return Reflect.get(obj, key);
        },
        set(obj, key, value) {
            const result = Reflect.set(obj, key, value);
            // 触发更新
            if (deps.has(key)) {
                deps.get(key).forEach(effect => effect());
            }
            return result;
        }
    });
}

// 使用
const state = reactive({ count: 0 });
effect(() => console.log('count:', state.count));  // count: 0
state.count = 1;  // count: 1 (自动触发)
```

---

## 3. 组件化

### 3.1 组合式API(Composition API)

```vue
<!-- Counter.vue -->
<script setup>
import { ref, computed, onMounted, watch } from 'vue';

// Props
const props = defineProps({
    initialValue: {
        type: Number,
        default: 0
    }
});

// Emits
const emit = defineEmits(['change']);

// 响应式数据
const count = ref(props.initialValue);

// 计算属性
const doubleCount = computed(() => count.value * 2);

// 方法
const increment = () => {
    count.value++;
    emit('change', count.value);
};
const decrement = () => {
    count.value--;
    emit('change', count.value);
};

// 侦听器
watch(count, (newVal) => {
    console.log('count changed:', newVal);
});

// 生命周期
onMounted(() => {
    console.log('Component mounted');
});

// 暴露给父组件
defineExpose({ count, increment });
</script>

<template>
    <div class="counter">
        <button @click="decrement">-</button>
        <span>{{ count }} (×2 = {{ doubleCount }})</span>
        <button @click="increment">+</button>
    </div>
</template>

<style scoped>
.counter {
    display: flex;
    align-items: center;
    gap: 10px;
}
</style>
```

### 3.2 父子组件通信

```vue
<!-- Parent.vue -->
<script setup>
import { ref } from 'vue';
import Child from './Child.vue';

const message = ref('Hello from parent');
const childData = ref('');

const handleChildEvent = (data) => {
    childData.value = data;
};
</script>

<template>
    <!-- Props传子 -->
    <Child
        :message="message"
        @send-data="handleChildEvent"
    />
    <p>From child: {{ childData }}</p>
</template>

<!-- Child.vue -->
<script setup>
const props = defineProps({
    message: String
});
const emit = defineEmits(['send-data']);

const sendData = () => {
    emit('send-data', 'Hello from child');
};
</script>

<template>
    <div>
        <p>{{ message }}</p>
        <button @click="sendData">Send to parent</button>
    </div>
</template>
```

### 3.3 组合式函数(Composable)

```javascript
// useCounter.js — 可复用的逻辑
import { ref, computed } from 'vue';

export function useCounter(initialValue = 0, step = 1) {
    const count = ref(initialValue);
    const double = computed(() => count.value * 2);

    const increment = () => { count.value += step; };
    const decrement = () => { count.value -= step; };
    const reset = () => { count.value = initialValue; };

    return { count, double, increment, decrement, reset };
}

// 使用
// <script setup>
// import { useCounter } from './useCounter';
// const { count, double, increment } = useCounter(0, 5);
// </script>

// useFetch.js — 异步数据获取
import { ref, onMounted } from 'vue';

export function useFetch(url) {
    const data = ref(null);
    const error = ref(null);
    const loading = ref(false);

    const fetchData = async () => {
        loading.value = true;
        error.value = null;
        try {
            const response = await fetch(url);
            data.value = await response.json();
        } catch (err) {
            error.value = err.message;
        } finally {
            loading.value = false;
        }
    };

    onMounted(fetchData);

    return { data, error, loading, refetch: fetchData };
}
```

---

## 4. 生命周期

```javascript
// Vue 3 生命周期(Composition API)

import {
    onBeforeMount, onMounted,
    onBeforeUpdate, onUpdated,
    onBeforeUnmount, onUnmounted,
    onErrorCaptured, onActivated, onDeactivated
} from 'vue';

// 组件生命周期顺序:
// 1. setup() — 组件创建(Composition API入口)
// 2. onBeforeMount — 挂载前
// 3. onMounted — 挂载完成(DOM可用)
//    ↕ (数据变化时循环)
// 4. onBeforeUpdate — 更新前
// 5. onUpdated — 更新完成
//    ↕
// 6. onBeforeUnmount — 卸载前
// 7. onUnmounted — 卸载完成

onMounted(() => {
    console.log('DOM已挂载, 可访问DOM元素');
    // 适合: 初始化第三方库、定时器、事件监听
});

onUnmounted(() => {
    console.log('组件卸载, 清理资源');
    // 必须: 清除定时器、移除事件监听、取消请求
});

// Vue 2 → Vue 3 对比:
// beforeCreate  → setup()
// created       → setup()
// beforeMount   → onBeforeMount
// mounted       → onMounted
// beforeUpdate  → onBeforeUpdate
// updated       → onUpdated
// beforeDestroy → onBeforeUnmount
// destroyed     → onUnmounted
```

---

## 5. Vue Router

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
    { path: '/', name: 'home', component: () => import('../views/Home.vue') },
    { path: '/about', name: 'about', component: () => import('../views/About.vue') },
    // 动态路由
    { path: '/user/:id', name: 'user', component: () => import('../views/User.vue') },
    // 嵌套路由
    {
        path: '/dashboard',
        component: () => import('../views/Dashboard.vue'),
        children: [
            { path: '', redirect: 'overview' },
            { path: 'overview', component: () => import('../views/Overview.vue') },
            { path: 'analytics', component: () => import('../views/Analytics.vue') },
        ]
    },
    // 路由守卫
    {
        path: '/admin',
        component: () => import('../views/Admin.vue'),
        meta: { requiresAuth: true, roles: ['admin'] }
    },
    // 404
    { path: '/:pathMatch(.*)*', name: 'notFound', component: () => import('../views/404.vue') }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});

// 全局前置守卫
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token');
    if (to.meta.requiresAuth && !token) {
        next({ name: 'login', query: { redirect: to.fullPath } });
    } else {
        next();
    }
});

export default router;
```

```vue
<!-- 组件中使用路由 -->
<script setup>
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

// 获取路由参数
const userId = route.params.id;
const query = route.query.search;

// 导航
const goHome = () => router.push('/');
const goUser = (id) => router.push({ name: 'user', params: { id } });
const goBack = () => router.back();
</script>

<template>
    <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink :to="{ name: 'user', params: { id: 1 } }">User 1</RouterLink>
    </nav>
    <RouterView />
</template>
```

---

## 6. Pinia状态管理

```javascript
// stores/counter.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

// Composition API风格(推荐)
export const useCounterStore = defineStore('counter', () => {
    // state
    const count = ref(0);
    const name = ref('Counter');

    // getters
    const doubleCount = computed(() => count.value * 2);
    const isPositive = computed(() => count.value > 0);

    // actions
    const increment = () => count.value++;
    const decrement = () => count.value--;
    const reset = () => { count.value = 0; };

    return { count, name, doubleCount, isPositive, increment, decrement, reset };
});

// stores/user.js — 用户状态
export const useUserStore = defineStore('user', () => {
    const token = ref(localStorage.getItem('token') || '');
    const userInfo = ref(null);

    const isLoggedIn = computed(() => !!token.value);

    const login = async (credentials) => {
        const response = await api.login(credentials);
        token.value = response.token;
        localStorage.setItem('token', response.token);
        userInfo.value = response.user;
    };

    const logout = () => {
        token.value = '';
        userInfo.value = null;
        localStorage.removeItem('token');
    };

    return { token, userInfo, isLoggedIn, login, logout };
});
```

```vue
<!-- 组件中使用Pinia -->
<script setup>
import { storeToRefs } from 'pinia';
import { useCounterStore, useUserStore } from '@/stores';

const counterStore = useCounterStore();
const userStore = useUserStore();

// 解构响应式数据(需要storeToRefs保持响应性)
const { count, doubleCount } = storeToRefs(counterStore);
// actions可以直接解构
const { increment, reset } = counterStore;

const { isLoggedIn, userInfo } = storeToRefs(userStore);
</script>

<template>
    <div>
        <p>Count: {{ count }} (×2 = {{ doubleCount }})</p>
        <button @click="increment">+1</button>
        <button @click="reset">Reset</button>

        <div v-if="isLoggedIn">
            Welcome, {{ userInfo?.name }}
            <button @click="userStore.logout()">Logout</button>
        </div>
    </div>
</template>
```

---

## 7. 面试题速查

**Q1: Vue 3的响应式原理？**

```
Vue 2: Object.defineProperty — 遍历对象属性, 递归劫持getter/setter
Vue 3: Proxy — 代理整个对象, 支持新增/删除属性, 性能更好
流程: 读取数据收集依赖(get) → 修改数据触发更新(set) → 重新渲染
```

**Q2: ref和reactive的区别？**

```
ref: 用于基本类型, 访问需.value, 模板中自动解包
reactive: 用于对象, 直接访问属性, 不需要.value
推荐: 基本类型用ref, 对象用reactive
```

**Q3: Composition API vs Options API？**

```
Options API: data/methods/computed按选项组织, 逻辑分散
Composition API: setup()内自由组织, 逻辑内聚, 可复用(composable)
Vue 3推荐Composition API, 逻辑复杂时优势明显
```

**Q4: Pinia vs Vuex？**

```
Pinia: Vue 3推荐, 更简洁, 无mutation, TypeScript支持好, 模块化
Vuex: Vue 2时代, state/mutation/action/getter, 较繁琐
Pinia优势: 去除mutation, 自动代码分割, 更好的TS支持
```

**Q5: Vue组件通信方式？**

```
父子: Props/Emits, ref(子组件暴露方法)
爷孙: provide/inject
兄弟: Pinia/Vuex状态管理
任意: 事件总线(mitt) / Pinia
```

---

*最后更新：2026-07-13*

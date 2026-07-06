# SSO单点登录方案

> 一次登录，全网通行——企业级SSO架构设计与实现

---

## 📋 目录

1. [SSO概述](#1-sso概述)
2. [CAS方案](#2-cas方案)
3. [OAuth2方案](#3-oauth2方案)
4. [JWT方案](#4-jwt方案)
5. [方案对比](#5-方案对比)
6. [前后端分离SSO](#6-前后端分离sso)
7. [面试要点](#7-面试要点)

---

## 1. SSO概述

### 什么是SSO

```
SSO (Single Sign-On)：用户只需登录一次，即可访问所有相互信任的应用系统。

无SSO：
  系统A → 登录 → 使用
  系统B → 登录 → 使用
  系统C → 登录 → 使用

有SSO：
  SSO中心 → 登录一次
  系统A → 免登录 → 使用
  系统B → 免登录 → 使用
  系统C → 免登录 → 使用
```

### 核心概念

```
IdP (Identity Provider)：身份提供者，SSO认证中心
SP (Service Provider)：服务提供者，各业务系统
Token/Ticket：认证凭证，用于在IdP和SP间传递身份信息
```

### 应用场景

```
- 企业内网：OA、CRM、ERP、HR系统统一登录
- SaaS平台：多租户系统统一认证
- 集团公司：各子系统统一登录
- 第三方登录：微信/Google/GitHub登录
```

---

## 2. CAS方案

### CAS协议流程

```
1. 用户访问系统A → 未登录 → 重定向到CAS Server
2. CAS Server展示登录页 → 用户输入账号密码
3. CAS Server验证成功 → 生成Ticket → 重定向回系统A（带Ticket）
4. 系统A拿Ticket向CAS Server验证 → 获取用户信息
5. 系统A创建本地Session → 用户使用系统A

6. 用户访问系统B → 未登录 → 重定向到CAS Server
7. CAS Server发现已有全局Session → 生成Ticket → 重定向回系统B
8. 系统B验证Ticket → 获取用户信息 → 用户免登录使用系统B
```

### Spring Security CAS集成

```java
@Configuration
@EnableWebSecurity
public class CasSecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated())
            .cas(cas -> cas
                .loginPage("https://sso.example.com/login")
                .service("https://app1.example.com/login/cas")
                .logout(logout -> logout
                    .logoutSuccessUrl("https://sso.example.com/logout"))
            );
        return http.build();
    }
}
```

### CAS优缺点

```
✅ 优点：
  - 成熟稳定，支持多种认证方式
  - 支持单点登出（Single Logout）
  - 代理票据（Proxy Ticket）支持服务间调用

❌ 缺点：
  - 需要独立部署CAS Server
  - 基于Session，不适合前后端分离
  - 重定向次数多，体验一般
```

---

## 3. OAuth2方案

### 授权码模式实现SSO

```
1. 用户访问系统A → 重定向到认证中心
2. 认证中心展示登录页 → 用户登录
3. 认证中心生成授权码 → 重定向回系统A（带code）
4. 系统A用code换取Access Token
5. 系统A用Token获取用户信息
6. 用户访问系统B → 重定向到认证中心
7. 认证中心检测到已登录 → 直接返回授权码
8. 系统B用code换取Token → 获取用户信息
```

### Spring Authorization Server

```java
@Configuration
public class AuthServerConfig {
    
    @Bean
    public RegisteredClientRepository registeredClientRepository() {
        return new InMemoryRegisteredClientRepository(
            RegisteredClient.withId("app1")
                .clientId("app1")
                .clientSecret("{bcrypt}$2a$10...")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://app1.example.com/login/oauth2/code/sso")
                .scope(OidcScopes.OPENID)
                .scope("profile")
                .build(),
            RegisteredClient.withId("app2")
                .clientId("app2")
                .clientSecret("{bcrypt}$22a$10...")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://app2.example.com/login/oauth2/code/sso")
                .scope(OidcScopes.OPENID)
                .build()
        );
    }
}

// 客户端配置
@Configuration
public class ClientSecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth
                .anyRequest().authenticated())
            .oauth2Login(Customizer.withDefaults())  // OAuth2 SSO
            .oauth2Client(Customizer.withDefaults());
        return http.build();
    }
}
```

---

## 4. JWT方案

### JWT实现SSO

```java
// SSO认证中心
@RestController
public class SsoController {
    
    @PostMapping("/sso/login")
    public LoginResponse login(@RequestBody LoginRequest request) {
        // 1. 验证账号密码
        User user = userService.authenticate(request.getUsername(), request.getPassword());
        
        // 2. 生成JWT
        String token = Jwts.builder()
            .subject(user.getId().toString())
            .claim("username", user.getUsername())
            .claim("roles", user.getRoles())
            .issuedAt(new Date())
            .expiration(new Date(System.currentTimeMillis() + 3600_000))  // 1小时
            .signWith(jwtSecretKey)
            .compact();
        
        // 3. 将Token存入Redis（用于全局Session管理和登出）
        redisTemplate.opsForValue().set("sso:token:" + token, user.getId(), 1, TimeUnit.HOURS);
        
        return new LoginResponse(token);
    }
    
    @PostMapping("/sso/logout")
    public void logout(@RequestHeader("Authorization") String token) {
        // 从Redis删除Token → 全局登出
        redisTemplate.delete("sso:token:" + token.substring(7));
    }
}

// 各业务系统验证Token
@Component
public class JwtAuthFilter extends OncePerRequestFilter {
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
            HttpServletResponse response, FilterChain chain) throws Exception {
        String token = extractToken(request);
        if (token != null) {
            try {
                // 1. 验证JWT签名和过期时间
                Claims claims = Jwts.parser()
                    .verifyWith(jwtSecretKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
                
                // 2. 验证Token是否在Redis中（支持主动登出）
                String userId = redisTemplate.opsForValue().get("sso:token:" + token);
                if (userId != null) {
                    // 设置当前用户上下文
                    SecurityContextHolder.getContext().setAuthentication(
                        new UsernamePasswordAuthenticationToken(
                            claims.get("username"), null, 
                            AuthorityUtils.createAuthorityList(
                                ((List<String>) claims.get("roles")).toArray(new String[0]))));
                }
            } catch (Exception e) {
                response.setStatus(401);
                return;
            }
        }
        chain.doFilter(request, response);
    }
}
```

---

## 5. 方案对比

| 维度 | CAS | OAuth2 | JWT |
|------|-----|--------|-----|
| 协议 | CAS协议 | OAuth2/OIDC | 自定义 |
| 状态管理 | Server端Session | Server端+Token | 无状态Token |
| 单点登出 | ✅ 原生支持 | ✅ 需额外实现 | ⚠️ 需Redis配合 |
| 前后端分离 | ❌ 不适合 | ✅ 适合 | ✅ 适合 |
| 移动端 | ❌ 不适合 | ✅ 适合 | ✅ 适合 |
| 部署复杂度 | 高（需CAS Server） | 中 | 低 |
| 安全性 | 高 | 高 | 中（Token泄露风险） |

### 选型建议

```
传统企业内网：CAS（成熟稳定）
SaaS/互联网：OAuth2（标准协议，生态好）
轻量级/移动端：JWT（简单灵活，无状态）
混合方案：OAuth2 + JWT（Token用JWT格式，走OAuth2流程）
```

---

## 6. 前后端分离SSO

### 跨域处理

```javascript
// 前端：拦截401，重定向到SSO
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response.status === 401) {
      // 重定向到SSO登录页
      const redirectUrl = encodeURIComponent(window.location.href);
      window.location.href = `https://sso.example.com/login?redirect=${redirectUrl}`;
    }
    return Promise.reject(error);
  }
);

// SSO登录成功后，重定向回前端，带上Token
// https://app1.example.com/callback?token=eyJhbG...
```

```java
// 后端：CORS配置
@Configuration
public class CorsConfig {
    
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of(
            "https://app1.example.com",
            "https://app2.example.com"
        ));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
        config.setAllowCredentials(true);
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
```

---

## 7. 面试要点

### Q1: SSO的原理是什么？

```
核心：认证中心(IdP)管理全局登录状态，各业务系统(SP)通过票据/Token验证身份。

流程：
1. 用户访问SP，未登录 → 重定向到IdP
2. IdP展示登录页，用户登录
3. IdP生成票据/Token，重定向回SP
4. SP验证票据/Token，创建本地会话
5. 访问其他SP时，IdP检测到已登录，直接发票据
```

### Q2: JWT如何实现单点登出？

```
JWT本身是无状态的，无法主动失效。实现单点登出的方案：

1. Redis黑名单：登出时将Token加入Redis黑名单
2. Redis白名单：Token必须在Redis中有效（推荐）
3. 短期Token + Refresh Token：Token有效期短（15分钟），登出时撤销Refresh Token
```

### Q3: CAS和OAuth2做SSO的区别？

```
CAS：
  - 专门为SSO设计的协议
  - 基于Session和Ticket
  - 适合传统Web应用
  - 支持代理票据（服务间调用）

OAuth2：
  - 授权框架，SSO是OAuth2+OIDC的应用
  - 基于Token
  - 适合前后端分离和移动端
  - 生态更丰富，第三方登录更方便
```

### Q4: 前后端分离如何实现SSO？

```
1. 前端拦截401响应 → 重定向到SSO认证中心
2. SSO中心登录成功 → 生成Token → 重定向回前端（URL参数或Fragment）
3. 前端存储Token（localStorage/cookie）
4. 后续请求携带Authorization: Bearer <token>
5. 后端验证Token → 返回数据
6. CORS配置允许跨域携带凭证
```

### Q5: Token存在哪里更安全？

```
localStorage：
  ✅ 不会自动发送到服务端（防CSRF）
  ❌ JavaScript可读取（防XSS要处理）

HttpOnly Cookie：
  ✅ JavaScript不可读取（防XSS）
  ❌ 自动发送到服务端（需防CSRF）

推荐：
  - Access Token：内存中存储（刷新页面丢失，用Refresh Token恢复）
  - Refresh Token：HttpOnly Cookie
  - 敏感操作：二次验证（短信/邮件验证码）
```

---

## 📚 相关阅读

- [02_Spring Security与JWT实战](./02_Spring Security与JWT实战.md)
- [01_OAuth2.0实战案例](./01_OAuth2.0实战案例.md)
- [Spring核心源码解析](../02_Spring生态/02_Spring核心源码解析.md)

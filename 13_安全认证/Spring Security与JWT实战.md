# Spring Security与JWT实战

> 企业级认证授权解决方案，从入门到实战

---

## 📋 目录

- [1. Spring Security简介](#1-spring-security简介)
- [2. 核心架构](#2-核心架构)
- [3. 认证机制](#3-认证机制)
- [4. 授权机制](#4-授权机制)
- [5. JWT详解](#5-jwt详解)
- [6. OAuth2.0](#6-oauth20)
- [7. RBAC权限模型](#7-rbac权限模型)
- [8. 单点登录](#8-单点登录)
- [9. 安全防护](#9-安全防护)
- [10. 实战案例](#10-实战案例)

---

## 🎯 学习目标

通过本文档，你将掌握：
- ✅ Spring Security核心架构与过滤器链
- ✅ 认证流程（用户名密码、手机号、第三方登录）
- ✅ 授权机制（URL权限、方法权限、数据权限）
- ✅ JWT原理与实现
- ✅ OAuth2.0四种授权模式
- ✅ RBAC权限模型设计与实现
- ✅ 单点登录（SSO）方案
- ✅ 会话管理（并发控制、踢人下线）
- ✅ 安全防护（CSRF、XSS、SQL注入）
- ✅ 企业级认证授权系统实战

---

## 1. Spring Security简介

### 1.1 什么是Spring Security

**Spring Security** 是Spring生态中用于**认证（Authentication）**和**授权（Authorization）**的安全框架。

**核心功能**：
- 🔐 **认证**：验证用户身份（登录）
- 🔑 **授权**：控制用户访问权限
- 🛡️ **防护**：CSRF、XSS、Session Fixation等

### 1.2 核心概念

| 概念 | 说明 |
|------|------|
| **Authentication** | 认证信息，包含用户名、密码、权限等 |
| **Principal** | 用户主体，通常是用户名 |
| **Credentials** | 凭证，通常是密码 |
| **Authorities** | 权限集合 |
| **SecurityContext** | 安全上下文，存储认证信息 |
| **SecurityContextHolder** | SecurityContext的持有者（ThreadLocal） |

### 1.3 快速开始

**依赖**：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

**配置**：
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            // 授权配置
            .authorizeRequests()
                .antMatchers("/public/**").permitAll()  // 公开接口
                .anyRequest().authenticated()  // 其他接口需要认证
            .and()
            // 登录配置
            .formLogin()
                .loginPage("/login")  // 登录页面
                .defaultSuccessUrl("/index")  // 登录成功跳转
            .and()
            // 登出配置
            .logout()
                .logoutUrl("/logout")
                .logoutSuccessUrl("/login")
            .and()
            // 关闭CSRF（API场景）
            .csrf().disable();
    }
    
    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        // 内存用户（测试用）
        auth.inMemoryAuthentication()
            .withUser("admin")
            .password("{noop}123456")  // {noop}表示不加密
            .roles("ADMIN");
    }
}
```

---

## 2. 核心架构

### 2.1 过滤器链

**Spring Security核心：过滤器链（Filter Chain）**

```
HTTP请求
    │
    ▼
SecurityContextPersistenceFilter  ← 1. 从Session中恢复SecurityContext
    │
    ▼
LogoutFilter  ← 2. 处理登出请求
    │
    ▼
UsernamePasswordAuthenticationFilter  ← 3. 处理用户名密码登录
    │
    ▼
BasicAuthenticationFilter  ← 4. 处理HTTP Basic认证
    │
    ▼
ExceptionTranslationFilter  ← 5. 处理认证/授权异常
    │
    ▼
FilterSecurityInterceptor  ← 6. 授权决策
    │
    ▼
Controller
```

**关键过滤器**：

| 过滤器 | 作用 |
|--------|------|
| **SecurityContextPersistenceFilter** | 从Session中恢复/保存SecurityContext |
| **UsernamePasswordAuthenticationFilter** | 处理表单登录（用户名+密码） |
| **BasicAuthenticationFilter** | 处理HTTP Basic认证 |
| **JwtAuthenticationFilter** | 处理JWT认证（自定义） |
| **ExceptionTranslationFilter** | 处理认证/授权异常，重定向到登录页 |
| **FilterSecurityInterceptor** | 授权决策，判断用户是否有权限访问 |

### 2.2 认证流程

**完整认证流程**：

```
1. 用户提交用户名+密码
   ↓
2. UsernamePasswordAuthenticationFilter拦截
   ↓
3. 创建UsernamePasswordAuthenticationToken（未认证）
   ↓
4. AuthenticationManager.authenticate()
   ↓
5. AuthenticationProvider认证
   ├─ UserDetailsService.loadUserByUsername()  ← 查询用户
   └─ PasswordEncoder.matches()  ← 校验密码
   ↓
6. 认证成功，返回Authentication（已认证）
   ↓
7. SecurityContextHolder.setContext()  ← 保存到ThreadLocal
   ↓
8. SecurityContextPersistenceFilter保存到Session
```

**代码示例**：

```java
// 1. 创建认证Token
UsernamePasswordAuthenticationToken token = 
    new UsernamePasswordAuthenticationToken(username, password);

// 2. 认证
Authentication authentication = authenticationManager.authenticate(token);

// 3. 保存到SecurityContext
SecurityContextHolder.getContext().setAuthentication(authentication);
```

### 2.3 核心组件

**AuthenticationManager**：
```java
public interface AuthenticationManager {
    Authentication authenticate(Authentication authentication) 
        throws AuthenticationException;
}
```

**AuthenticationProvider**：
```java
public interface AuthenticationProvider {
    // 执行认证
    Authentication authenticate(Authentication authentication) 
        throws AuthenticationException;
    
    // 是否支持该类型的认证
    boolean supports(Class<?> authentication);
}
```

**UserDetailsService**：
```java
public interface UserDetailsService {
    UserDetails loadUserByUsername(String username) 
        throws UsernameNotFoundException;
}
```

**UserDetails**：
```java
public interface UserDetails {
    String getUsername();  // 用户名
    String getPassword();  // 密码
    Collection<? extends GrantedAuthority> getAuthorities();  // 权限
    boolean isEnabled();  // 是否启用
    boolean isAccountNonExpired();  // 账户是否过期
    boolean isAccountNonLocked();  // 账户是否锁定
    boolean isCredentialsNonExpired();  // 密码是否过期
}
```

---

## 3. 认证机制

### 3.1 数据库认证

**用户表设计**：
```sql
CREATE TABLE sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    nickname VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    status TINYINT DEFAULT 1 COMMENT '0-禁用 1-启用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);
```

**UserDetailsService实现**：
```java
@Service
public class UserDetailsServiceImpl implements UserDetailsService {
    
    @Autowired
    private UserMapper userMapper;
    
    @Override
    public UserDetails loadUserByUsername(String username) 
            throws UsernameNotFoundException {
        // 1. 查询用户
        User user = userMapper.selectByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在: " + username);
        }
        
        // 2. 查询权限
        List<String> permissions = userMapper.selectPermissionsByUserId(user.getId());
        List<GrantedAuthority> authorities = permissions.stream()
            .map(SimpleGrantedAuthority::new)
            .collect(Collectors.toList());
        
        // 3. 返回UserDetails
        return new org.springframework.security.core.userdetails.User(
            user.getUsername(),
            user.getPassword(),
            user.getStatus() == 1,  // enabled
            true,  // accountNonExpired
            true,  // credentialsNonExpired
            true,  // accountNonLocked
            authorities
        );
    }
}
```

**配置**：
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
    
    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth.userDetailsService(userDetailsService)
            .passwordEncoder(passwordEncoder());
    }
}
```

### 3.2 自定义登录接口

**登录Controller**：
```java
@RestController
public class AuthController {
    
    @Autowired
    private AuthenticationManager authenticationManager;
    
    @Autowired
    private JwtTokenProvider jwtTokenProvider;
    
    @PostMapping("/login")
    public Result login(@RequestBody LoginRequest request) {
        try {
            // 1. 创建认证Token
            UsernamePasswordAuthenticationToken token = 
                new UsernamePasswordAuthenticationToken(
                    request.getUsername(), 
                    request.getPassword()
                );
            
            // 2. 认证
            Authentication authentication = authenticationManager.authenticate(token);
            
            // 3. 生成JWT
            String jwt = jwtTokenProvider.generateToken(authentication);
            
            return Result.success(jwt);
        } catch (AuthenticationException e) {
            return Result.fail("用户名或密码错误");
        }
    }
}
```

### 3.3 手机号登录

**自定义AuthenticationToken**：
```java
public class MobileAuthenticationToken extends AbstractAuthenticationToken {
    
    private final Object principal;  // 手机号
    private Object credentials;  // 验证码
    
    // 未认证
    public MobileAuthenticationToken(String mobile, String code) {
        super(null);
        this.principal = mobile;
        this.credentials = code;
        setAuthenticated(false);
    }
    
    // 已认证
    public MobileAuthenticationToken(Object principal, Object credentials,
                                     Collection<? extends GrantedAuthority> authorities) {
        super(authorities);
        this.principal = principal;
        this.credentials = credentials;
        setAuthenticated(true);
    }
}
```

**自定义Filter**：
```java
public class MobileAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
    
    public MobileAuthenticationFilter() {
        super(new AntPathRequestMatcher("/login/mobile", "POST"));
    }
    
    @Override
    public Authentication attemptAuthentication(HttpServletRequest request, 
                                                HttpServletResponse response) {
        String mobile = request.getParameter("mobile");
        String code = request.getParameter("code");
        
        MobileAuthenticationToken token = new MobileAuthenticationToken(mobile, code);
        return getAuthenticationManager().authenticate(token);
    }
}
```

**自定义Provider**：
```java
@Component
public class MobileAuthenticationProvider implements AuthenticationProvider {
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    @Override
    public Authentication authenticate(Authentication authentication) 
            throws AuthenticationException {
        MobileAuthenticationToken token = (MobileAuthenticationToken) authentication;
        
        String mobile = (String) token.getPrincipal();
        String code = (String) token.getCredentials();
        
        // 1. 校验验证码
        String cacheCode = redisTemplate.opsForValue().get("sms:code:" + mobile);
        if (!code.equals(cacheCode)) {
            throw new BadCredentialsException("验证码错误");
        }
        
        // 2. 查询用户
        UserDetails user = userDetailsService.loadUserByUsername(mobile);
        
        // 3. 返回已认证Token
        return new MobileAuthenticationToken(user, code, user.getAuthorities());
    }
    
    @Override
    public boolean supports(Class<?> authentication) {
        return MobileAuthenticationToken.class.isAssignableFrom(authentication);
    }
}
```

### 3.4 第三方登录（OAuth2）

**GitHub登录示例**：

**依赖**：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-client</artifactId>
</dependency>
```

**配置**：
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: your-client-id
            client-secret: your-client-secret
            scope: user:email
        provider:
          github:
            authorization-uri: https://github.com/login/oauth/authorize
            token-uri: https://github.com/login/oauth/access_token
            user-info-uri: https://api.github.com/user
```

**Security配置**：
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .oauth2Login()
                .loginPage("/login")
                .defaultSuccessUrl("/")
                .userInfoEndpoint()
                    .userService(oAuth2UserService);
    }
}
```

---

## 4. 授权机制

### 4.1 URL权限控制

**基于URL的权限配置**：
```java
@Override
protected void configure(HttpSecurity http) throws Exception {
    http.authorizeRequests()
        // 公开接口
        .antMatchers("/public/**", "/login", "/register").permitAll()
        
        // ADMIN角色才能访问
        .antMatchers("/admin/**").hasRole("ADMIN")
        
        // ADMIN或USER角色
        .antMatchers("/user/**").hasAnyRole("ADMIN", "USER")
        
        // 需要特定权限
        .antMatchers("/order/create").hasAuthority("order:create")
        .antMatchers("/order/delete").hasAuthority("order:delete")
        
        // 其他请求需要认证
        .anyRequest().authenticated();
}
```

**动态权限配置**（从数据库加载）：
```java
@Component
public class CustomFilterInvocationSecurityMetadataSource 
        implements FilterInvocationSecurityMetadataSource {
    
    @Autowired
    private PermissionMapper permissionMapper;
    
    @Override
    public Collection<ConfigAttribute> getAttributes(Object object) {
        // 获取请求URL
        String requestUrl = ((FilterInvocation) object).getRequestUrl();
        
        // 从数据库查询该URL需要的权限
        List<String> permissions = permissionMapper.selectByUrl(requestUrl);
        
        if (permissions.isEmpty()) {
            // 无需权限
            return null;
        }
        
        return permissions.stream()
            .map(SecurityConfig::new)
            .collect(Collectors.toList());
    }
}
```

### 4.2 方法权限控制

**启用方法权限**：
```java
@Configuration
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig {
}
```

**使用注解**：
```java
@Service
public class OrderService {
    
    // 需要 order:create 权限
    @PreAuthorize("hasAuthority('order:create')")
    public void createOrder(Order order) {
        // ...
    }
    
    // 需要 ADMIN 角色
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteOrder(Long orderId) {
        // ...
    }
    
    // 需要 ADMIN 或 USER 角色
    @PreAuthorize("hasAnyRole('ADMIN', 'USER')")
    public Order getOrder(Long orderId) {
        // ...
    }
    
    // 自定义表达式
    @PreAuthorize("@orderSecurity.canAccess(#orderId)")
    public void updateOrder(Long orderId, Order order) {
        // ...
    }
}
```

**自定义表达式**：
```java
@Component("orderSecurity")
public class OrderSecurityExpression {
    
    @Autowired
    private OrderMapper orderMapper;
    
    public boolean canAccess(Long orderId) {
        // 获取当前用户
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        Long userId = Long.parseLong(authentication.getName());
        
        // 查询订单
        Order order = orderMapper.selectById(orderId);
        
        // 判断是否是订单所有者
        return order != null && order.getUserId().equals(userId);
    }
}
```

### 4.3 数据权限

**场景**：用户只能查看自己部门的数据

**方案1：手动过滤**：
```java
@Service
public class UserService {
    
    public List<User> list() {
        // 获取当前用户
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        User currentUser = (User) authentication.getPrincipal();
        
        // 根据部门ID查询
        return userMapper.selectByDeptId(currentUser.getDeptId());
    }
}
```

**方案2：MyBatis拦截器**：
```java
@Intercepts({
    @Signature(type = Executor.class, method = "query", args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class})
})
public class DataPermissionInterceptor implements Interceptor {
    
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        MappedStatement ms = (MappedStatement) invocation.getArgs()[0];
        Object parameter = invocation.getArgs()[1];
        
        // 获取当前用户
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        User user = (User) authentication.getPrincipal();
        
        // 修改SQL，添加部门条件
        // SELECT * FROM user WHERE dept_id = #{deptId}
        
        return invocation.proceed();
    }
}
```

---

## 5. JWT详解

### 5.1 JWT简介

**JWT（JSON Web Token）**：一种无状态的认证方案

**结构**（三部分，用`.`分隔）：
```
Header.Payload.Signature

示例：
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Header（头部）**：
```json
{
  "alg": "HS256",  // 签名算法
  "typ": "JWT"     // 类型
}
```

**Payload（载荷）**：
```json
{
  "sub": "1234567890",  // 主题（用户ID）
  "name": "John Doe",   // 用户名
  "iat": 1516239022,    // 签发时间
  "exp": 1516242622     // 过期时间
}
```

**Signature（签名）**：
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

### 5.2 JWT生成与验证

**依赖**：
```xml
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt</artifactId>
    <version>0.9.1</version>
</dependency>
```

**JwtTokenProvider**：
```java
@Component
public class JwtTokenProvider {
    
    @Value("${jwt.secret}")
    private String secret;  // 密钥
    
    @Value("${jwt.expiration}")
    private long expiration;  // 过期时间（秒）
    
    // 生成Token
    public String generateToken(Authentication authentication) {
        UserDetails user = (UserDetails) authentication.getPrincipal();
        
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expiration * 1000);
        
        return Jwts.builder()
            .setSubject(user.getUsername())  // 用户名
            .setIssuedAt(now)  // 签发时间
            .setExpiration(expiryDate)  // 过期时间
            .signWith(SignatureAlgorithm.HS512, secret)  // 签名
            .compact();
    }
    
    // 从Token中获取用户名
    public String getUsernameFromToken(String token) {
        Claims claims = Jwts.parser()
            .setSigningKey(secret)
            .parseClaimsJws(token)
            .getBody();
        
        return claims.getSubject();
    }
    
    // 验证Token
    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(secret).parseClaimsJws(token);
            return true;
        } catch (SignatureException e) {
            log.error("Invalid JWT signature");
        } catch (MalformedJwtException e) {
            log.error("Invalid JWT token");
        } catch (ExpiredJwtException e) {
            log.error("Expired JWT token");
        } catch (UnsupportedJwtException e) {
            log.error("Unsupported JWT token");
        } catch (IllegalArgumentException e) {
            log.error("JWT claims string is empty");
        }
        return false;
    }
}
```

### 5.3 JWT过滤器

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    
    @Autowired
    private JwtTokenProvider jwtTokenProvider;
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
                                    HttpServletResponse response, 
                                    FilterChain filterChain) throws ServletException, IOException {
        try {
            // 1. 从请求头获取Token
            String jwt = getJwtFromRequest(request);
            
            if (StringUtils.hasText(jwt) && jwtTokenProvider.validateToken(jwt)) {
                // 2. 从Token中获取用户名
                String username = jwtTokenProvider.getUsernameFromToken(jwt);
                
                // 3. 查询用户详情
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);
                
                // 4. 创建认证对象
                UsernamePasswordAuthenticationToken authentication = 
                    new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities()
                    );
                
                // 5. 保存到SecurityContext
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        } catch (Exception e) {
            log.error("设置用户认证失败", e);
        }
        
        filterChain.doFilter(request, response);
    }
    
    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
```

**配置**：
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .csrf().disable()  // JWT不需要CSRF
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)  // 无状态
            .and()
            .authorizeRequests()
                .antMatchers("/login", "/register").permitAll()
                .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
    }
}
```

### 5.4 Refresh Token

**问题**：JWT过期后需要重新登录

**解决**：Refresh Token（刷新令牌）

**流程**：
```
1. 登录成功 → 返回 Access Token + Refresh Token
   - Access Token：有效期短（15分钟）
   - Refresh Token：有效期长（7天）

2. Access Token过期 → 使用Refresh Token刷新
   - POST /refresh {refreshToken: "xxx"}
   - 返回新的Access Token

3. Refresh Token过期 → 重新登录
```

**实现**：
```java
@RestController
public class AuthController {
    
    @PostMapping("/login")
    public Result login(@RequestBody LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
            new UsernamePasswordAuthenticationToken(
                request.getUsername(), 
                request.getPassword()
            )
        );
        
        // 生成Access Token（15分钟）
        String accessToken = jwtTokenProvider.generateToken(authentication, 15 * 60);
        
        // 生成Refresh Token（7天）
        String refreshToken = jwtTokenProvider.generateRefreshToken(authentication, 7 * 24 * 60 * 60);
        
        return Result.success(Map.of(
            "accessToken", accessToken,
            "refreshToken", refreshToken
        ));
    }
    
    @PostMapping("/refresh")
    public Result refresh(@RequestBody RefreshRequest request) {
        String refreshToken = request.getRefreshToken();
        
        // 验证Refresh Token
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            return Result.fail("Refresh Token无效");
        }
        
        // 生成新的Access Token
        String username = jwtTokenProvider.getUsernameFromToken(refreshToken);
        UserDetails user = userDetailsService.loadUserByUsername(username);
        
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            user, null, user.getAuthorities()
        );
        
        String accessToken = jwtTokenProvider.generateToken(authentication, 15 * 60);
        
        return Result.success(Map.of("accessToken", accessToken));
    }
}
```

---

## 6. OAuth2.0

### 6.1 四种授权模式

**1. 授权码模式（Authorization Code）**：
```
最安全，适用于有后端的Web应用

流程：
1. 用户点击"使用GitHub登录"
2. 跳转到GitHub授权页面
3. 用户同意授权
4. GitHub回调，返回授权码（code）
5. 后端用code换取access_token
6. 用后端用access_token获取用户信息
```

**2. 隐式模式（Implicit）**：
```
不推荐，直接返回token（不安全）

流程：
1. 用户点击"使用GitHub登录"
2. 跳转到GitHub授权页面
3. 用户同意授权
4. GitHub回调，直接返回access_token
```

**3. 密码模式（Password）**：
```
用户直接输入GitHub用户名密码（不推荐）

流程：
1. 用户输入GitHub用户名+密码
2. 后端向GitHub请求token
3. GitHub返回access_token
```

**4. 客户端模式（Client Credentials）**：
```
用于服务器间调用（无用户参与）

流程：
1. 后端向GitHub请求token（使用client_id + client_secret）
2. GitHub返回access_token
```

### 6.2 授权码模式实战

**GitHub OAuth应用配置**：
```
1. GitHub → Settings → Developer settings → OAuth Apps
2. 创建OAuth应用
3. 获取 Client ID 和 Client Secret
4. 设置 Authorization callback URL：http://localhost:8080/login/oauth2/code/github
```

**Spring Boot配置**：
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: your-client-id
            client-secret: your-client-secret
            scope:
              - user:email
              - read:user
```

**Security配置**：
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/", "/login/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .oauth2Login()
                .loginPage("/login")
                .defaultSuccessUrl("/")
                .userInfoEndpoint()
                    .userService(oAuth2UserService);
    }
    
    @Bean
    public OAuth2UserService<OAuth2UserRequest, OAuth2User> oAuth2UserService() {
        return new CustomOAuth2UserService();
    }
}
```

**自定义OAuth2UserService**：
```java
@Service
public class CustomOAuth2UserService extends DefaultOAuth2UserService {
    
    @Autowired
    private UserMapper userMapper;
    
    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);
        
        // 获取GitHub用户信息
        String githubId = oAuth2User.getAttribute("id").toString();
        String login = oAuth2User.getAttribute("login");
        String email = oAuth2User.getAttribute("email");
        
        // 查询本地用户
        User user = userMapper.selectByGithubId(githubId);
        if (user == null) {
            // 首次登录，创建用户
            user = new User();
            user.setGithubId(githubId);
            user.setUsername(login);
            user.setEmail(email);
            userMapper.insert(user);
        }
        
        return oAuth2User;
    }
}
```

---

## 7. RBAC权限模型

### 7.1 数据库设计

**5张表**：
```sql
-- 用户表
CREATE TABLE sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    status TINYINT DEFAULT 1
);

-- 角色表
CREATE TABLE sys_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    status TINYINT DEFAULT 1
);

-- 权限表
CREATE TABLE sys_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    perm_name VARCHAR(50) NOT NULL,
    perm_code VARCHAR(50) UNIQUE NOT NULL,
    url VARCHAR(200),
    type TINYINT COMMENT '1-菜单 2-按钮'
);

-- 用户-角色关联表
CREATE TABLE sys_user_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    UNIQUE KEY uk_user_role (user_id, role_id)
);

-- 角色-权限关联表
CREATE TABLE sys_role_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id BIGINT NOT NULL,
    perm_id BIGINT NOT NULL,
    UNIQUE KEY uk_role_perm (role_id, perm_id)
);
```

### 7.2 权限加载

```java
@Service
public class UserDetailsServiceImpl implements UserDetailsService {
    
    @Override
    public UserDetails loadUserByUsername(String username) {
        // 1. 查询用户
        User user = userMapper.selectByUsername(username);
        
        // 2. 查询角色
        List<Role> roles = roleMapper.selectByUserId(user.getId());
        
        // 3. 查询权限
        List<Permission> permissions = permissionMapper.selectByUserId(user.getId());
        
        // 4. 组装权限
        List<GrantedAuthority> authorities = new ArrayList<>();
        
        // 角色权限（ROLE_前缀）
        roles.forEach(role -> 
            authorities.add(new SimpleGrantedAuthority("ROLE_" + role.getRoleCode()))
        );
        
        // 菜单权限
        permissions.forEach(perm -> 
            authorities.add(new SimpleGrantedAuthority(perm.getPermCode()))
        );
        
        return new org.springframework.security.core.userdetails.User(
            user.getUsername(),
            user.getPassword(),
            authorities
        );
    }
}
```

### 7.3 权限使用

```java
@RestController
@RequestMapping("/user")
public class UserController {
    
    // 需要 ADMIN 角色
    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/list")
    public Result list() {
        return Result.success(userService.list());
    }
    
    // 需要 user:create 权限
    @PreAuthorize("hasAuthority('user:create')")
    @PostMapping("/create")
    public Result create(@RequestBody User user) {
        userService.save(user);
        return Result.success();
    }
    
    // 需要 user:delete 权限
    @PreAuthorize("hasAuthority('user:delete')")
    @DeleteMapping("/{id}")
    public Result delete(@PathVariable Long id) {
        userService.removeById(id);
        return Result.success();
    }
}
```

---

## 8. 单点登录

### 8.1 SSO简介

**单点登录（SSO）**：一次登录，多个系统免登录

**场景**：
```
电商系统：
- 商城系统（mall.example.com）
- 后台管理（admin.example.com）
- 客服系统（service.example.com）

用户在商城登录后，访问后台管理无需再次登录
```

### 8.2 实现方案

**方案1：共享Session（同域名）**
```
1. 设置Cookie domain为父域名：.example.com
2. Session存储到Redis
3. 所有子系统共享Session

优点：简单
缺点：只能同域名
```

**方案2：CAS（Central Authentication Service）**
```
架构：
┌────────────┐
│ CAS Server │  ← 认证中心
└────────────┘
      ▲
      │ 认证
      │
┌─────┴─────┬─────────┬─────────┐
│  商城      │  后台    │  客服    │
└───────────┴─────────┴─────────┘

流程：
1. 用户访问商城
2. 商城发现未登录，重定向到CAS Server
3. 用户在CAS Server登录
4. CAS Server重定向回商城（带ticket）
5. 商城用ticket向CAS Server验证
6. 验证通过，商城创建Session
7. 用户访问后台
8. 后台发现未登录，重定向到CAS Server
9. CAS Server发现已登录，直接返回ticket
10. 后台用ticket验证，创建Session
```

**方案3：JWT（推荐）**
```
1. 用户在商城登录
2. 认证中心生成JWT
3. 商城、后台、客服都验证JWT（无需请求认证中心）

优点：无状态、性能高
缺点：无法注销（需要黑名单）
```

### 8.3 JWT SSO实现

**认证中心**：
```java
@RestController
public class AuthController {
    
    @PostMapping("/login")
    public Result login(@RequestBody LoginRequest request) {
        // 认证
        Authentication authentication = authenticationManager.authenticate(
            new UsernamePasswordAuthenticationToken(
                request.getUsername(), 
                request.getPassword()
            )
        );
        
        // 生成JWT
        String token = jwtTokenProvider.generateToken(authentication);
        
        // 设置Cookie（domain=.example.com）
        Cookie cookie = new Cookie("token", token);
        cookie.setDomain(".example.com");
        cookie.setPath("/");
        cookie.setMaxAge(7 * 24 * 60 * 60);
        response.addCookie(cookie);
        
        return Result.success(token);
    }
}
```

**子系统**：
```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
                                    HttpServletResponse response, 
                                    FilterChain filterChain) {
        // 从Cookie获取Token
        String token = getCookieValue(request, "token");
        
        if (token != null && jwtTokenProvider.validateToken(token)) {
            // 验证通过，设置认证信息
            String username = jwtTokenProvider.getUsernameFromToken(token);
            UserDetails user = userDetailsService.loadUserByUsername(username);
            
            UsernamePasswordAuthenticationToken authentication = 
                new UsernamePasswordAuthenticationToken(user, null, user.getAuthorities());
            
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }
        
        filterChain.doFilter(request, response);
    }
}
```

---

## 9. 安全防护

### 9.1 密码加密

**BCryptPasswordEncoder**（推荐）：
```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}

// 注册时加密
String rawPassword = "123456";
String encodedPassword = passwordEncoder.encode(rawPassword);
user.setPassword(encodedPassword);

// 登录时验证
boolean matches = passwordEncoder.matches(rawPassword, encodedPassword);
```

**原理**：
```
BCrypt = Blowfish + Salt

每次加密结果不同：
123456 → $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
123456 → $2a$10$NaLlz.WZC0kAy/kVcJy8vOdEhL9c7UZp9.gPDd6UcJk9ZU1Q9qJhO

但验证都能通过（因为Salt存储在结果中）
```

### 9.2 CSRF防护

**CSRF（Cross-Site Request Forgery）**：跨站请求伪造

**攻击示例**：
```html
<!-- 恶意网站 evil.com -->
<img src="http://bank.com/transfer?to=hacker&amount=10000">

用户访问evil.com → 自动发起转账请求
如果用户已登录bank.com → 转账成功
```

**Spring Security防护**：
```java
@Override
protected void configure(HttpSecurity http) throws Exception {
    http
        .csrf()
            .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse());
}
```

**前端携带Token**：
```javascript
// 从Cookie获取CSRF Token
const csrfToken = Cookies.get('XSRF-TOKEN');

// 请求时携带
axios.post('/api/transfer', data, {
    headers: {
        'X-XSRF-TOKEN': csrfToken
    }
});
```

**API场景**：
```java
// JWT场景下禁用CSRF
http.csrf().disable();
```

### 9.3 XSS防护

**XSS（Cross-Site Scripting）**：跨站脚本攻击

**攻击示例**：
```
用户提交评论：<script>alert(document.cookie)</script>
其他用户查看评论 → 执行恶意脚本
```

**防护**：
```java
// 1. 输入过滤
public String sanitize(String input) {
    return HtmlUtils.htmlEscape(input);
}

// 2. HttpOnly Cookie
Cookie cookie = new Cookie("token", token);
cookie.setHttpOnly(true);  // JS无法访问

// 3. Content-Security-Policy
response.setHeader("Content-Security-Policy", "script-src 'self'");
```

### 9.4 SQL注入防护

**攻击示例**：
```sql
-- 原SQL
SELECT * FROM user WHERE username = '${username}' AND password = '${password}'

-- 恶意输入
username: admin' --
password: anything

-- 拼接后
SELECT * FROM user WHERE username = 'admin' --' AND password = 'anything'

-- 注释掉密码校验，登录成功！
```

**防护**：
```java
// 使用预编译（MyBatis）
@Select("SELECT * FROM user WHERE username = #{username} AND password = #{password}")
User selectByUsernameAndPassword(@Param("username") String username, 
                                 @Param("password") String password);

// #{} → PreparedStatement（自动转义）
// ${} → 字符串拼接（危险）
```

---

## 10. 实战案例

### 10.1 完整的认证授权系统

**技术栈**：
- Spring Boot + Spring Security
- JWT + Refresh Token
- RBAC权限模型
- Redis缓存

**项目结构**：
```
src/main/java/com/example/security/
├── config/
│   ├── SecurityConfig.java
│   ├── JwtConfig.java
│   └── RedisConfig.java
├── controller/
│   ├── AuthController.java
│   ├── UserController.java
│   └── RoleController.java
├── filter/
│   └── JwtAuthenticationFilter.java
├── service/
│   ├── UserDetailsServiceImpl.java
│   ├── UserService.java
│   └── RoleService.java
├── mapper/
│   ├── UserMapper.java
│   ├── RoleMapper.java
│   └── PermissionMapper.java
├── entity/
│   ├── User.java
│   ├── Role.java
│   └── Permission.java
└── util/
    └── JwtTokenProvider.java
```

**核心代码已在前面章节展示，这里总结功能**：

✅ **用户注册**：密码BCrypt加密  
✅ **用户登录**：JWT + Refresh Token  
✅ **权限控制**：RBAC模型，支持角色和权限  
✅ **方法权限**：@PreAuthorize注解  
✅ **会话管理**：Redis存储Token黑名单  
✅ **安全防护**：CSRF、XSS、SQL注入  

**性能优化**：
```
1. Redis缓存用户权限（减少数据库查询）
2. JWT无状态（减少Session存储）
3. 权限懒加载（只加载当前用户权限）
```

**监控告警**：
```
1. 登录失败次数（防暴力破解）
2. Token刷新频率（防滥用）
3. 权限拒绝次数（异常行为检测）
```

---

## 🎯 总结

### 核心要点

**Spring Security架构**：
- ✅ 过滤器链：SecurityContextPersistenceFilter → UsernamePasswordAuthenticationFilter → FilterSecurityInterceptor
- ✅ 认证流程：AuthenticationManager → AuthenticationProvider → UserDetailsService
- ✅ 授权：URL权限、方法权限、数据权限

**JWT**：
- ✅ 结构：Header.Payload.Signature
- ✅ 优点：无状态、跨域
- ✅ 缺点：无法注销（需要黑名单）

**OAuth2.0**：
- ✅ 授权码模式（最安全）
- ✅ 隐式模式（不推荐）
- ✅ 密码模式（不推荐）
- ✅ 客户端模式（服务器间调用）

**RBAC**：
- ✅ 用户 → 角色 → 权限
- ✅ 灵活的权限控制

**SSO**：
- ✅ 共享Session（同域名）
- ✅ CAS（异域名）
- ✅ JWT（推荐）

### 面试高频

1. **Spring Security的认证流程**？
   - UsernamePasswordAuthenticationFilter → AuthenticationManager → AuthenticationProvider → UserDetailsService

2. **JWT的优缺点**？
   - 优点：无状态、跨域、性能高
   - 缺点：无法注销、Token泄露风险

3. **如何防止JWT泄露**？
   - HttpOnly Cookie、HTTPS、Token过期时间短、Refresh Token

4. **OAuth2.0有哪些授权模式**？
   - 授权码、隐式、密码、客户端

5. **如何实现单点登录**？
   - 共享Session、CAS、JWT

### 最佳实践

1. **密码加密**：BCrypt（每次加密结果不同）
2. **JWT**：Access Token（15分钟） + Refresh Token（7天）
3. **权限模型**：RBAC
4. **安全防护**：CSRF、XSS、SQL注入
5. **监控**：登录失败次数、Token刷新频率

---

*最后更新：2025-10-27*  
*文档状态：v1.0 完成*  
*作者：技术知识库团队*

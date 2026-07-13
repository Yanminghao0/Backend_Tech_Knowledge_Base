# Spring Security 深度详解

> Spring Security 是 Spring 生态中最强大的安全框架，提供认证（Authentication）、授权（Authorization）、防护（CSRF/CORS/Session Fixation）等全面的安全能力。它基于 Servlet Filter 链实现，与 Spring Boot 深度集成，是企业级 Java 应用的安全首选方案。本文系统讲解 Spring Security 的架构设计、认证授权流程、密码编码、会话管理及 OAuth2/JWT 集成。

---

## 📋 目录

1. [Spring Security 架构总览](#1-spring-security-架构总览)
2. [认证流程详解](#2-认证流程详解)
3. [授权流程详解](#3-授权流程详解)
4. [密码编码与加密](#4-密码编码与加密)
5. [会话管理](#5-会话管理)
6. [CSRF 防护与 CORS 配置](#6-csrf-防护与-cors-配置)
7. [方法级安全](#7-方法级安全)
8. [OAuth2 集成](#8-oauth2-集成)
9. [JWT 无状态认证](#9-jwt-无状态认证)
10. [Spring Security 6 新特性](#10-spring-security-6-新特性)
11. [面试题速查](#11-面试题速查)

---

## 1. Spring Security 架构总览

### 1.1 核心组件关系图

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────┐
│        FilterChainProxy             │
│  (DelegatingFilterProxy)            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│     SecurityFilterChain             │
│  ┌─────┐ ┌──────┐ ┌──────┐ ┌─────┐ │
│  │CSRF │ │Auth  │ │Auth  │ │ ... │ │
│  │Filt │ │Filt  │ │Filt  │ │     │ │
│  │     │ │(User)│ │(Basic│ │     │ │
│  └─────┘ └──────┘ └──────┘ └─────┘ │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│       SecurityContext               │
│  ┌─────────────────────────────┐    │
│  │   Authentication            │    │
│  │  ┌───────────────────────┐  │    │
│  │  │ Principal             │  │    │
│  │  │ Credentials           │  │    │
│  │  │ Authorities           │  │    │
│  │  └───────────────────────┘  │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### 1.2 FilterChain —— 过滤器链

Spring Security 的核心是一组 Servlet Filter 链，每个请求依次经过多个安全过滤器。

```java
// 核心过滤器链顺序（Spring Security 5.x+）
SecurityFilterChain 包含的关键过滤器：

1. DisableEncodeUrlFilter          // 禁用 URL 编码
2. ForceEagerSessionCreationFilter // 强制创建 Session
3. ChannelProcessingFilter         // HTTP/HTTPS 通道处理
4. WebAsyncManagerIntegrationFilter // 异步请求安全集成
5. SecurityContextHolderFilter     // SecurityContext 持有者
6. HeaderWriterFilter              // 安全响应头写入
7. CsrfFilter                      // CSRF 防护
8. LogoutFilter                    // 登出处理
9. UsernamePasswordAuthenticationFilter  // 用户名密码认证
10. DefaultLoginPageGeneratingFilter     // 默认登录页
11. DefaultLogoutPageGeneratingFilter    // 默认登出页
12. ConcurrentSessionFilter         // 并发会话控制
13. RequestCacheAwareFilter         // 请求缓存
14. SecurityContextHolderAwareRequestFilter // 包装请求
15. AnonymousAuthenticationFilter   // 匿名用户认证
16. SessionManagementFilter         // 会话管理
17. ExceptionTranslationFilter      // 异常翻译
18. AuthorizationFilter             // 授权决策（Spring Security 6）
```

### 1.3 SecurityContext 与 SecurityContextHolder

`SecurityContext` 封装了当前用户的认证信息，`SecurityContextHolder` 是它的持有者，使用 `ThreadLocal` 实现。

```java
// SecurityContextHolder 存储当前线程的安全上下文
SecurityContext context = SecurityContextHolder.getContext();
Authentication authentication = context.getAuthentication();

// 获取当前用户信息
Object principal = authentication.getPrincipal();
String username = authentication.getName();
Collection<? extends GrantedAuthority> authorities = authentication.getAuthorities();

// 手动设置认证信息（登录成功后）
UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(
    userDetails,       // Principal
    null,              // Credentials（认证后清除）
    userDetails.getAuthorities()  // Authorities
);
SecurityContextHolder.getContext().setAuthentication(token);

// 清除上下文（登出时）
SecurityContextHolder.clearContext();
```

`SecurityContextHolder` 支持三种策略：

```java
// 1. MODE_THREADLOCAL（默认）：每个线程独立
SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_THREADLOCAL);

// 2. MODE_INHERITABLETHREADLOCAL：子线程可继承
SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_INHERITABLETHREADLOCAL);

// 3. MODE_GLOBAL：全局共享（JVM 级别）
SecurityContextHolder.setStrategyName(SecurityContextHolder.MODE_GLOBAL);
```

### 1.4 Authentication 接口

`Authentication` 是认证信息的核心接口：

```java
public interface Authentication extends Principal, Serializable {
    // 权限集合
    Collection<? extends GrantedAuthority> getAuthorities();
    
    // 凭证（密码），认证后通常被清除
    Object getCredentials();
    
    // 认证详情（IP、SessionId 等）
    Object getDetails();
    
    // 主体（用户名或 UserDetails 对象）
    Object getPrincipal();
    
    // 是否已认证
    boolean isAuthenticated();
    
    void setAuthenticated(boolean isAuthenticated);
}
```

### 1.5 UserDetailsService 与 UserDetails

```java
// UserDetails：用户信息接口
public interface UserDetails extends Serializable {
    Collection<? extends GrantedAuthority> getAuthorities();
    String getPassword();
    String getUsername();
    boolean isAccountNonExpired();    // 账号未过期
    boolean isAccountNonLocked();     // 账号未锁定
    boolean isCredentialsNonExpired(); // 凭证未过期
    boolean isEnabled();               // 账号启用
}

// UserDetailsService：用户加载接口
public interface UserDetailsService {
    UserDetails loadUserByUsername(String username) throws UsernameNotFoundException;
}

// 自定义实现
@Service
public class CustomUserDetailsService implements UserDetailsService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        User user = userRepository.findByUsername(username)
            .orElseThrow(() -> new UsernameNotFoundException("用户不存在: " + username));
        
        return org.springframework.security.core.userdetails.User.builder()
            .username(user.getUsername())
            .password(user.getPassword())
            .authorities(user.getRoles().stream()
                .map(role -> new SimpleGrantedAuthority("ROLE_" + role.getName()))
                .collect(Collectors.toList()))
            .accountExpired(!user.isActive())
            .accountLocked(user.isLocked())
            .credentialsExpired(false)
            .disabled(!user.isEnabled())
            .build();
    }
}
```

---

## 2. 认证流程详解

### 2.1 认证流程全景图

```
HTTP POST /login (username, password)
         │
         ▼
┌────────────────────────────────────┐
│ UsernamePasswordAuthenticationFilter│
│  提取用户名密码，创建 UsernamePassword │
│  AuthenticationToken（未认证）       │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ AuthenticationManager (ProviderManager) │
│  遍历 AuthenticationProvider 列表    │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ DaoAuthenticationProvider           │
│  1. 调用 UserDetailsService 加载用户 │
│  2. PasswordEncoder 校验密码         │
│  3. 创建已认证的 Authentication       │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ SecurityContextHolder               │
│  存储已认证的 Authentication         │
└────────────────────────────────────┘
```

### 2.2 UsernamePasswordAuthenticationFilter

```java
// 源码简化逻辑
public class UsernamePasswordAuthenticationFilter extends AbstractAuthenticationProcessingFilter {
    
    public static final String SPRING_SECURITY_FORM_USERNAME_KEY = "username";
    public static final String SPRING_SECURITY_FORM_PASSWORD_KEY = "password";
    
    @Override
    public Authentication attemptAuthentication(HttpServletRequest request,
            HttpServletResponse response) throws AuthenticationException {
        
        // 1. 只处理 POST 请求
        if (!request.getMethod().equals("POST")) {
            throw new AuthenticationServiceException("Authentication method not supported");
        }
        
        // 2. 提取用户名密码
        String username = obtainUsername(request);
        String password = obtainPassword(request);
        
        // 3. 创建未认证的 Token
        UsernamePasswordAuthenticationToken authRequest = 
            UsernamePasswordAuthenticationToken.unauthenticated(username, password);
        
        // 4. 交给 AuthenticationManager 认证
        return this.getAuthenticationManager().authenticate(authRequest);
    }
}
```

### 2.3 AuthenticationManager 与 AuthenticationProvider

```java
// AuthenticationManager：认证管理器
public interface AuthenticationManager {
    Authentication authenticate(Authentication authentication) throws AuthenticationException;
}

// ProviderManager：默认实现，委托给多个 Provider
public class ProviderManager implements AuthenticationManager {
    private List<AuthenticationProvider> providers;
    
    @Override
    public Authentication authenticate(Authentication authentication) {
        for (AuthenticationProvider provider : providers) {
            if (!provider.supports(authentication.getClass())) {
                continue;
            }
            Authentication result = provider.authenticate(authentication);
            if (result != null) {
                // 认证成功
                return result;
            }
        }
        throw new ProviderNotFoundException("No AuthenticationProvider found");
    }
}

// AuthenticationProvider：认证提供者
public interface AuthenticationProvider {
    Authentication authenticate(Authentication authentication) throws AuthenticationException;
    boolean supports(Class<?> authentication);
}
```

### 2.4 DaoAuthenticationProvider

```java
// DaoAuthenticationProvider 核心逻辑（简化）
public class DaoAuthenticationProvider extends AbstractUserDetailsAuthenticationProvider {
    
    private UserDetailsService userDetailsService;
    private PasswordEncoder passwordEncoder;
    
    @Override
    protected void additionalAuthenticationChecks(UserDetails userDetails,
            UsernamePasswordAuthenticationToken authentication) {
        
        String presentedPassword = authentication.getCredentials().toString();
        
        // 密码校验
        if (!passwordEncoder.matches(presentedPassword, userDetails.getPassword())) {
            throw new BadCredentialsException("Bad credentials");
        }
    }
    
    @Override
    protected UserDetails retrieveUser(String username,
            UsernamePasswordAuthenticationToken authentication) {
        return userDetailsService.loadUserByUsername(username);
    }
}
```

### 2.5 自定义认证流程

```java
// 1. 自定义登录过滤器
public class JwtAuthenticationFilter extends UsernamePasswordAuthenticationFilter {
    
    @Override
    public Authentication attemptAuthentication(HttpServletRequest request,
            HttpServletResponse response) {
        // 从 JSON Body 读取用户名密码
        try {
            LoginRequest loginRequest = new ObjectMapper()
                .readValue(request.getInputStream(), LoginRequest.class);
            UsernamePasswordAuthenticationToken token = 
                UsernamePasswordAuthenticationToken.unauthenticated(
                    loginRequest.getUsername(), loginRequest.getPassword());
            return getAuthenticationManager().authenticate(token);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
    
    @Override
    protected void successfulAuthentication(HttpServletRequest request,
            HttpServletResponse response, FilterChain chain, Authentication authResult) {
        // 认证成功，生成 JWT
        String token = JwtUtil.generateToken(authResult.getName());
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(
            new ObjectMapper().writeValueAsString(Map.of("token", token)));
    }
}

// 2. SecurityConfig 配置
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/login", "/public/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter(), 
                UsernamePasswordAuthenticationFilter.class)
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            );
        return http.build();
    }
}
```

---

## 3. 授权流程详解

### 3.1 授权流程图

```
HTTP Request (已认证)
         │
         ▼
┌────────────────────────────────────┐
│ AuthorizationFilter (Spring Sec 6)  │
│ FilterSecurityInterceptor (Sec 5)   │
│  提取 URL → 匹配安全规则             │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│ AuthorizationManager                │
│  (AccessDecisionManager in Sec 5)   │
│  决策：Affirmative / Consensus /    │
│         Unanimous                   │
└───────────────┬────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│Authority│ │Authority│ │Authority│
│Voter    │ │Voter    │ │Voter    │
│(ROLE_*)│ │(WebACL) │ │(Custom) │
└────────┘ └────────┘ └────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
    GRANTED          DENIED
```

### 3.2 基于角色的 URL 授权配置

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                // 公开接口
                .requestMatchers("/public/**", "/login", "/register").permitAll()
                // 静态资源
                .requestMatchers("/css/**", "/js/**", "/images/**").permitAll()
                // Swagger
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                // 角色控制
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .requestMatchers("/user/**").hasAnyRole("USER", "ADMIN")
                // 权限控制
                .requestMatchers("/api/orders/**").hasAuthority("ORDER_READ")
                .requestMatchers(HttpMethod.POST, "/api/orders/**").hasAuthority("ORDER_WRITE")
                // IP 控制
                .requestMatchers("/internal/**").hasIpAddress("192.168.1.0/24")
                // 其余需认证
                .anyRequest().authenticated()
            );
        return http.build();
    }
}
```

### 3.3 AccessDecisionManager（Spring Security 5）

```java
// 三种投票策略
// 1. AffirmativeBased（默认）：任一 Voter 投赞成票即通过
// 2. ConsensusBased：少数服从多数
// 3. UnanimousBased：全票通过才允许

// 自定义 AccessDecisionVoter
public class IpAddressVoter implements AccessDecisionVoter<Object> {
    
    @Override
    public boolean supports(ConfigAttribute attribute) {
        return "IP_LOCAL".equals(attribute.getAttribute());
    }
    
    @Override
    public int vote(Authentication authentication, Object object,
            Collection<ConfigAttribute> attributes) {
        // 返回 ACCESS_GRANTED(1), ACCESS_DENIED(-1), ACCESS_ABSTAIN(0)
        String remoteAddr = ((HttpServletRequest) object).getRemoteAddr();
        return "127.0.0.1".equals(remoteAddr) 
            ? ACCESS_GRANTED : ACCESS_ABSTAIN;
    }
}
```

### 3.4 AuthorizationManager（Spring Security 6）

```java
// Spring Security 6 使用 AuthorizationManager 替代 AccessDecisionManager
// 更简洁、函数式风格

// 自定义 AuthorizationManager
public class CustomAuthorizationManager implements AuthorizationManager<RequestAuthorizationContext> {
    
    @Override
    public AuthorizationDecision check(Supplier<Authentication> authentication,
            RequestAuthorizationContext context) {
        HttpServletRequest request = context.getRequest();
        String tenantId = request.getHeader("X-Tenant-Id");
        
        Authentication auth = authentication.get();
        boolean hasTenantAccess = auth.getAuthorities().stream()
            .anyMatch(a -> a.getAuthority().equals("TENANT_" + tenantId));
        
        return new AuthorizationDecision(hasTenantAccess);
    }
}

// 使用自定义 AuthorizationManager
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/api/tenant/**")
    .access(new CustomAuthorizationManager())
);
```

---

## 4. 密码编码与加密

### 4.1 PasswordEncoder 接口

```java
public interface PasswordEncoder {
    // 编码（加密）
    String encode(CharSequence rawPassword);
    
    // 校验
    boolean matches(CharSequence rawPassword, String encodedPassword);
    
    // 是否需要再次编码（用于升级密码格式）
    boolean upgradeEncoding(String encodedPassword);
}
```

### 4.2 BCryptPasswordEncoder

BCrypt 是 Spring Security 推荐的密码编码器，内置盐值，每次加密结果不同。

```java
@Bean
public PasswordEncoder passwordEncoder() {
    // strength：成本因子（4~31，默认10）
    return new BCryptPasswordEncoder(12);
}

// 使用示例
PasswordEncoder encoder = new BCryptPasswordEncoder();

// 加密（每次结果不同，因为内置随机盐）
String hash1 = encoder.encode("password123");
String hash2 = encoder.encode("password123");
// hash1 ≠ hash2，但都能通过 matches 校验

// 校验
boolean matches = encoder.matches("password123", hash1);  // true
boolean matches2 = encoder.matches("wrong", hash1);       // false
```

BCrypt 编码格式：

```
$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
│  │  │                      │
│  │  │                      └── 22位盐值 + 31位哈希结果
│  │  └── 成本因子（10 = 2^10 轮）
│  └── 算法版本（2a）
└── BCrypt 标识
```

### 4.3 其他编码器

```java
// Argon2PasswordEncoder（更安全，需要额外依赖）
PasswordEncoder argon2 = new Argon2PasswordEncoder(
    16,     // salt 长度
    32,     // hash 长度
    1,      // 并行度
    4096,   // 内存（KB）
    1       // 迭代次数
);

// SCryptPasswordEncoder
PasswordEncoder scrypt = new SCryptPasswordEncoder(
    16384,  // CPU cost
    8,      // memory cost
    1,      // parallelization
    32,     // key length
    16      // salt length
);

// Pbkdf2PasswordEncoder
PasswordEncoder pbkdf2 = new Pbkdf2PasswordEncoder(
    "secret-secret",  // secret
    16,               // salt length
    310000,           // iterations
    256               // key length
);
```

### 4.4 DelegatingPasswordEncoder —— 密码格式迁移

`DelegatingPasswordEncoder` 支持多种编码格式并存，便于密码算法升级。

```java
// 创建 DelegatingPasswordEncoder
String idForEncode = "bcrypt";
Map<String, PasswordEncoder> encoders = new HashMap<>();
encoders.put("bcrypt", new BCryptPasswordEncoder());
encoders.put("argon2", new Argon2PasswordEncoder());
encoders.put("scrypt", new SCryptPasswordEncoder());
encoders.put("pbkdf2", new Pbkdf2PasswordEncoder());
encoders.put("noop", NoOpPasswordEncoder.getInstance());
encoders.put("sha256", new StandardPasswordEncoder());

PasswordEncoder delegating = new DelegatingPasswordEncoder(idForEncode, encoders);

// 加密时使用默认编码器（bcrypt）
String encoded = delegating.encode("password");
// 结果: {bcrypt}$2a$10$N9qo8uLOickgx2ZMRZoMye...

// 校验时根据前缀自动选择编码器
boolean matches = delegating.matches("password", "{argon2}$argon2id$v=19$m=4096...");
boolean matches2 = delegating.matches("password", "{sha256}f2d81a260dea8a100...");
```

密码存储格式：`{algorithm}encodedPassword`，前缀标识使用的编码算法。

```java
// Spring Boot 默认提供（Spring Security 5+）
@Bean
public PasswordEncoder passwordEncoder() {
    return PasswordEncoderFactories.createDelegatingPasswordEncoder();
}

// 旧密码迁移示例
// 旧: 明文存储 "password"
// 新: {bcrypt}$2a$10$N9qo8uLOickgx2ZMRZoMye...

// 迁移策略：用户登录时检测旧格式，自动升级
@Override
protected void additionalAuthenticationChecks(UserDetails userDetails,
        UsernamePasswordAuthenticationToken authentication) {
    String presentedPassword = authentication.getCredentials().toString();
    String storedPassword = userDetails.getPassword();
    
    if (!passwordEncoder.matches(presentedPassword, storedPassword)) {
        throw new BadCredentialsException("Bad credentials");
    }
    
    // 密码格式升级
    if (passwordEncoder.upgradeEncoding(storedPassword)) {
        String newHash = passwordEncoder.encode(presentedPassword);
        userRepository.updatePassword(userDetails.getUsername(), newHash);
    }
}
```

---

## 5. 会话管理

### 5.1 会话创建策略

```java
http.sessionManagement(session -> session
    // ALWAYS：总是创建 Session
    // IF_REQUIRED：需要时创建（默认）
    // NEVER：不创建，但使用已有的
    // STATELESS：完全不使用 Session（JWT/REST 场景）
    .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
);
```

### 5.2 并发会话控制

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .sessionManagement(session -> session
                .maximumSessions(1)                          // 最大并发会话数
                .maxSessionsPreventsLogin(false)             // false=踢掉旧会话，true=阻止新登录
                .sessionRegistry(sessionRegistry())
                .expiredUrl("/login?expired=true")           // 会话过期跳转
            )
            .sessionManagement(session -> session
                .invalidSessionUrl("/login?invalid=true")    // 无效会话跳转
                .sessionFixation(fixation -> fixation
                    .changeSessionId()                       // 会话固定防护
                )
            );
        return http.build();
    }
    
    @Bean
    public SessionRegistry sessionRegistry() {
        return new SessionRegistryImpl();
    }
    
    @Bean
    public HttpSessionEventPublisher httpSessionEventPublisher() {
        return new HttpSessionEventPublisher();  // 必须配置，否则并发控制不生效
    }
}
```

### 5.3 会话固定防护

会话固定攻击（Session Fixation）是指攻击者获取一个会话 ID，诱导受害者使用该 ID 登录，从而劫持会话。

```java
// 四种防护策略
http.sessionManagement(session -> session
    .sessionFixation(fixation -> fixation
        // none：不做任何处理（不安全）
        // newSession：创建新 Session，但不复制旧数据
        // migrateSession：创建新 Session，复制旧数据（默认，Servlet 3.0-）
        // changeSessionId：只更改 Session ID，保留数据（默认，Servlet 3.1+）
        .changeSessionId()
    )
);
```

### 5.4 会话超时配置

```yaml
# application.yml
server:
  servlet:
    session:
      timeout: 30m          # 会话超时 30 分钟
      cookie:
        max-age: 30m
        http-only: true
        secure: true
        same-site: strict
```

```java
// 编程式配置
http.sessionManagement(session -> session
    .invalidSessionUrl("/login?timeout=true")
);
```

---

## 6. CSRF 防护与 CORS 配置

### 6.1 CSRF 防护

CSRF（Cross-Site Request Forgery）跨站请求伪造，Spring Security 默认开启 CSRF 防护。

```java
// 默认开启 CSRF（推荐生产环境）
http.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
    // 忽略特定路径
    .ignoringRequestMatchers("/api/public/**", "/h2-console/**")
);

// 禁用 CSRF（仅用于无状态 API 或测试环境）
http.csrf(csrf -> csrf.disable());
```

CSRF Token 工作流程：

```java
// CookieCsrfTokenRepository：Token 存储在 Cookie 中
// 1. 首次 GET 请求，服务器生成 CSRF Token，写入 Cookie XSRF-TOKEN
// 2. 后续 POST/PUT/DELETE 请求，前端从 Cookie 读取 Token，放入 Header X-XSRF-TOKEN
// 3. 服务器校验 Header 中的 Token 与 Cookie 中的是否一致

// 前端配合示例（Axios 拦截器）
axios.interceptors.request.use(config => {
    const csrfToken = getCookie('XSRF-TOKEN');
    if (csrfToken) {
        config.headers['X-XSRF-TOKEN'] = csrfToken;
    }
    return config;
});
```

```java
// Spring Security 6 中使用 CsrfTokenRequestHandler
http.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
    .csrfTokenRequestHandler(new CsrfTokenRequestAttributeHandler())
    .requireCsrfProtectionMatcher(
        new NegatedRequestMatcher(new RequestHeaderRequestMatcher("X-Requested-With"))
    )
);
```

### 6.2 CORS 配置

```java
// 方式一：全局 CORS 配置
@Bean
public WebMvcConfigurer corsConfigurer() {
    return new WebMvcConfigurer() {
        @Override
        public void addCorsMappings(CorsRegistry registry) {
            registry.addMapping("/api/**")
                .allowedOrigins("https://example.com")
                .allowedMethods("GET", "POST", "PUT", "DELETE")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
        }
    };
}

// 方式二：Spring Security CORS 配置（推荐）
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .cors(cors -> cors.configurationSource(corsConfigurationSource()))
        // ...其他配置
    ;
    return http.build();
}

@Bean
public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://example.com"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    config.setAllowedHeaders(List.of("*"));
    config.setAllowCredentials(true);
    config.setMaxAge(3600L);
    config.setExposedHeaders(List.of("Authorization", "X-Total-Count"));
    
    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", config);
    return source;
}
```

---

## 7. 方法级安全

### 7.1 启用方法级安全

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity  // Spring Security 6（替代 @EnableGlobalMethodSecurity）
public class SecurityConfig {
    // ...
}
```

### 7.2 @PreAuthorize —— 方法执行前授权

```java
@Service
public class OrderService {
    
    // 角色检查
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteOrder(Long orderId) { ... }
    
    // 权限检查
    @PreAuthorize("hasAuthority('ORDER_READ')")
    public Order getOrder(Long orderId) { ... }
    
    // 组合条件
    @PreAuthorize("hasRole('ADMIN') or hasAuthority('ORDER_WRITE')")
    public void updateOrder(Long orderId, OrderDTO dto) { ... }
    
    // 使用方法参数
    @PreAuthorize("#order.owner == authentication.principal.username")
    public void updateOrder(Order order) { ... }
    
    // 调用 Bean 方法
    @PreAuthorize("@orderSecurity.canAccess(#orderId, authentication)")
    public Order getOrder(Long orderId) { ... }
}

// 自定义安全检查 Bean
@Component("orderSecurity")
public class OrderSecurity {
    public boolean canAccess(Long orderId, Authentication auth) {
        // 自定义逻辑
        return orderRepository.findById(orderId)
            .map(order -> order.getOwner().equals(auth.getName()))
            .orElse(false);
    }
}
```

### 7.3 @PostAuthorize —— 方法执行后授权

```java
// 方法执行后，根据返回值判断
@PostAuthorize("returnObject.owner == authentication.principal.username")
public Order getOrder(Long orderId) {
    return orderRepository.findById(orderId);
}
// 如果返回的 Order 不属于当前用户，抛 AccessDeniedException
```

### 7.4 @Secured —— 角色检查

```java
// @Secured 只支持角色/权限，不支持 SpEL
@Secured("ROLE_ADMIN")
public void deleteAllOrders() { ... }

@Secured({"ROLE_ADMIN", "ROLE_SUPER_ADMIN"})
public void resetSystem() { ... }
```

### 7.5 @RolesAllowed —— JSR-250

```java
// JSR-250 标准注解
@RolesAllowed("ADMIN")
public void adminOperation() { ... }

@PermitAll
public void publicOperation() { ... }

@DenyAll
public void disabledOperation() { ... }
```

### 7.6 @PreFilter / @PostFilter —— 数据过滤

```java
// @PreFilter：过滤入参集合
@PreFilter("filterObject.owner == authentication.principal.username")
public void processOrders(List<Order> orders) {
    // 只处理属于当前用户的 Order
}

// @PostFilter：过滤返回值集合
@PostFilter("filterObject.owner == authentication.principal.username")
public List<Order> getAllOrders() {
    return orderRepository.findAll();
    // 自动过滤：只返回属于当前用户的 Order
}
```

---

## 8. OAuth2 集成

### 8.1 OAuth2 四种授权模式

| 模式 | 适用场景 | 特点 |
|------|---------|------|
| 授权码模式（Authorization Code） | Web 应用 | 最安全，最常用 |
| 简化模式（Implicit） | SPA/移动端 | 不推荐，已废弃 |
| 密码模式（Resource Owner Password） | 受信应用 | 需直接处理密码 |
| 客户端模式（Client Credentials） | 服务间调用 | 无用户参与 |

### 8.2 OAuth2 客户端配置

```java
// Maven 依赖
// spring-boot-starter-oauth2-client

@Configuration
@EnableWebSecurity
public class OAuth2SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/login**", "/error").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")
                .defaultSuccessUrl("/home")
                .failureUrl("/login?error=true")
            )
            .oauth2Client(Customizer.withDefaults())
            ;
        return http.build();
    }
}
```

```yaml
# application.yml —— OAuth2 Provider 配置
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: ${GITHUB_CLIENT_ID}
            client-secret: ${GITHUB_CLIENT_SECRET}
            scope: read:user, user:email
          google:
            client-id: ${GOOGLE_CLIENT_ID}
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: profile, email
          custom:
            client-id: custom-client
            client-secret: custom-secret
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/login/oauth2/code/{registrationId}"
            scope: read,write
            client-name: Custom OAuth2 Provider
            client-authentication-method: client_secret_basic
        provider:
          custom:
            authorization-uri: https://auth.example.com/oauth2/authorize
            token-uri: https://auth.example.com/oauth2/token
            user-info-uri: https://api.example.com/userinfo
            user-name-attribute: sub
            jwk-set-uri: https://auth.example.com/oauth2/jwks
```

### 8.3 OAuth2 资源服务器

```java
// Maven 依赖
// spring-boot-starter-oauth2-resource-server

@Configuration
@EnableWebSecurity
public class ResourceServerConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(Customizer.withDefaults())
            );
        return http.build();
    }
}
```

```yaml
# application.yml —— 资源服务器配置
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com
          jwk-set-uri: https://auth.example.com/oauth2/jwks
```

---

## 9. JWT 无状态认证

### 9.1 JWT 结构

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNj...  .SflKxwRJSMeKKF2QT4fwp...
│                      │                                                    │
│                      │                                                    └── Signature（签名）
│                      └── Payload（载荷，Base64 编码的 JSON）
└── Header（头部，算法和类型）
```

### 9.2 JWT 认证过滤器

```java
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    
    @Autowired
    private JwtTokenProvider jwtTokenProvider;
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response, FilterChain filterChain) 
            throws ServletException, IOException {
        
        // 1. 从请求头提取 Token
        String token = resolveToken(request);
        
        // 2. 验证 Token
        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
            // 3. 从 Token 提取用户名
            String username = jwtTokenProvider.getUsernameFromToken(token);
            
            // 4. 加载用户信息
            UserDetails userDetails = userDetailsService.loadUserByUsername(username);
            
            // 5. 创建认证对象
            UsernamePasswordAuthenticationToken authentication = 
                UsernamePasswordAuthenticationToken.authenticated(
                    userDetails, null, userDetails.getAuthorities());
            authentication.setDetails(
                new WebAuthenticationDetailsSource().buildDetails(request));
            
            // 6. 存入 SecurityContext
            SecurityContextHolder.getContext().setAuthentication(authentication);
        }
        
        filterChain.doFilter(request, response);
    }
    
    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
```

### 9.3 JWT Token 生成与验证

```java
@Component
public class JwtTokenProvider {
    
    @Value("${jwt.secret}")
    private String secret;
    
    @Value("${jwt.expiration:86400000}")  // 默认 24 小时
    private long expiration;
    
    // 生成 Token
    public String generateToken(Authentication authentication) {
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expiration);
        
        return Jwts.builder()
            .subject(userDetails.getUsername())
            .issuedAt(now)
            .expiration(expiryDate)
            .claim("roles", userDetails.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList()))
            .signWith(getSigningKey())
            .compact();
    }
    
    // 从 Token 提取用户名
    public String getUsernameFromToken(String token) {
        Claims claims = Jwts.parser()
            .verifyWith(getSigningKey())
            .build()
            .parseSignedClaims(token)
            .getPayload();
        return claims.getSubject();
    }
    
    // 验证 Token
    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                .verifyWith(getSigningKey())
                .build()
                .parseSignedClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }
    
    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
}
```

### 9.4 JWT 完整配置

```java
@Configuration
@EnableWebSecurity
public class JwtSecurityConfig {
    
    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/auth/login", "/auth/register").permitAll()
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter, 
                UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(jwtAuthenticationEntryPoint)
                .accessDeniedHandler(jwtAccessDeniedHandler)
            );
        return http.build();
    }
}
```

### 9.5 JWT 刷新机制

```java
@RestController
@RequestMapping("/auth")
public class AuthController {
    
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest request) {
        Authentication authentication = authenticationManager.authenticate(
            UsernamePasswordAuthenticationToken.unauthenticated(
                request.getUsername(), request.getPassword())
        );
        
        String accessToken = jwtTokenProvider.generateToken(authentication);
        String refreshToken = jwtTokenProvider.generateRefreshToken(authentication);
        
        return ResponseEntity.ok(Map.of(
            "accessToken", accessToken,
            "refreshToken", refreshToken,
            "tokenType", "Bearer",
            "expiresIn", jwtExpiration
        ));
    }
    
    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(@RequestBody RefreshRequest request) {
        String refreshToken = request.getRefreshToken();
        
        if (!jwtTokenProvider.validateToken(refreshToken)) {
            return ResponseEntity.status(401).body("Invalid refresh token");
        }
        
        String username = jwtTokenProvider.getUsernameFromToken(refreshToken);
        UserDetails userDetails = userDetailsService.loadUserByUsername(username);
        
        String newAccessToken = jwtTokenProvider.generateToken(
            UsernamePasswordAuthenticationToken.authenticated(
                userDetails, null, userDetails.getAuthorities()));
        
        return ResponseEntity.ok(Map.of(
            "accessToken", newAccessToken,
            "tokenType", "Bearer"
        ));
    }
}
```

---

## 10. Spring Security 6 新特性

### 10.1 WebSecurityConfigurerAdapter 移除

```java
// ❌ Spring Security 5.x（已废弃）
@Configuration
public class SecurityConfig extends WebSecurityConfigurerAdapter {
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests().anyRequest().authenticated();
    }
}

// ✅ Spring Security 6.x
@Configuration
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth.anyRequest().authenticated());
        return http.build();
    }
}
```

### 10.2 API 变更

```java
// 方法名变更
// authorizeRequests() → authorizeHttpRequests()
// antMatchers() → requestMatchers()
// mvcMatchers() → requestMatchers()
// regexMatchers() → requestMatchers().regexMatchers()

// Lambda DSL（推荐）
http.csrf(csrf -> csrf.disable())          // Lambda 风格
    .authorizeHttpRequests(auth -> auth     // Lambda 风格
        .requestMatchers("/public/**").permitAll()
        .anyRequest().authenticated()
    );

// 链式调用（不推荐，6.x 中已标记为 deprecated）
http.csrf().disable()
    .authorizeHttpRequests()
    .requestMatchers("/public/**").permitAll()
    .anyRequest().authenticated();
```

### 10.3 AuthorizationFilter 替代 FilterSecurityInterceptor

```java
// Spring Security 5: FilterSecurityInterceptor + AccessDecisionManager
// Spring Security 6: AuthorizationFilter + AuthorizationManager

// 更高效：在 Filter 链中更早执行，减少不必要的处理
// 更灵活：支持自定义 AuthorizationManager
http.authorizeHttpRequests(auth -> auth
    .anyRequest().access(
        (authentication, context) -> {
            // 自定义授权逻辑
            return new AuthorizationDecision(true);
        }
    )
);
```

### 10.4 OAuth2 改进

```java
// OAuth2 授权服务器（Spring Authorization Server）
@Bean
public SecurityFilterChain authServerSecurityFilterChain(HttpSecurity http) throws Exception {
    OAuth2AuthorizationServerConfiguration.applyDefaultSecurity(http);
    
    http.getConfigurer(OAuth2AuthorizationServerConfigurer.class)
        .oidc(Customizer.withDefaults());  // 启用 OpenID Connect 1.0
    
    http.exceptionHandling(ex -> ex
        .defaultAuthenticationEntryPointFor(
            new LoginUrlAuthenticationEntryPoint("/login"),
            new MediaTypeRequestMatcher(MediaType.TEXT_HTML)
        )
    );
    
    return http.build();
}

// 注册 OAuth2 客户端
@Bean
public RegisteredClientRepository registeredClientRepository() {
    RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
        .clientId("client")
        .clientSecret("{bcrypt}$2a$10$...")
        .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
        .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
        .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
        .redirectUri("http://127.0.0.1:8080/login/oauth2/code/client")
        .scope(OidcScopes.OPENID)
        .scope(OidcScopes.PROFILE)
        .tokenSettings(TokenSettings.builder()
            .accessTokenTimeToLive(Duration.ofMinutes(30))
            .refreshTokenTimeToLive(Duration.ofDays(7))
            .build())
        .clientSettings(ClientSettings.builder()
            .requireAuthorizationConsent(true)
            .build())
        .build();
    return new InMemoryRegisteredClientRepository(client);
}
```

### 10.5 DeferredSecurityContext

```java
// Spring Security 6 中 SecurityContext 延迟加载
// 提高性能：如果请求不需要安全上下文，则不加载

// 自定义 SecurityContextRepository
public class JwtSecurityContextRepository implements RequestAttributeSecurityContextRepository {
    
    @Override
    public Supplier<SecurityContext> loadDeferredContext(HttpServletRequest request) {
        return () -> {
            String token = extractToken(request);
            if (token != null && jwtTokenProvider.validateToken(token)) {
                Authentication auth = jwtTokenProvider.getAuthentication(token);
                return new SecurityContextImpl(auth);
            }
            return SecurityContextImpl.EMPTY;
        };
    }
}
```

---

## 11. 面试题速查

### Q1: Spring Security 的核心架构是什么？

Spring Security 基于 Servlet Filter 链实现。核心组件包括：`DelegatingFilterProxy` → `FilterChainProxy` → `SecurityFilterChain`（一组安全过滤器）。认证信息存储在 `SecurityContext` 中，通过 `SecurityContextHolder`（基于 ThreadLocal）在请求间传递。认证由 `AuthenticationManager` → `AuthenticationProvider` 完成，授权由 `AuthorizationManager` 完成。

### Q2: SecurityContextHolder 为什么使用 ThreadLocal？

`ThreadLocal` 确保每个线程有独立的 `SecurityContext`，避免线程安全问题。当请求线程处理完用户请求后，框架自动清除 `SecurityContext`。在异步场景下可使用 `MODE_INHERITABLETHREADLOCAL` 让子线程继承，或使用 `DelegatingSecurityContextExecutor` 手动传播。

### Q3: Authentication 和 Authorization 的区别？

Authentication（认证）是验证"你是谁"，通过用户名密码等凭证确认身份；Authorization（授权）是验证"你能做什么"，基于角色/权限决定是否允许访问资源。认证在前，授权在后。

### Q4: @PreAuthorize 和 @Secured 的区别？

`@PreAuthorize` 支持 SpEL 表达式，可使用方法参数、调用 Bean 方法、组合条件（and/or）；`@Secured` 只支持角色/权限字符串，不支持表达式。`@PreAuthorize` 功能更强大，是推荐的方式。

### Q5: BCrypt 密码编码的原理和优势？

BCrypt 使用自适应哈希函数，内置盐值（每次加密结果不同），成本因子可调（控制计算时间）。优势：1) 抗彩虹表攻击（随机盐）；2) 抗暴力破解（慢哈希）；3) 可调成本因子（随硬件升级增强安全性）；4) 无需单独存储盐值（盐嵌入在哈希结果中）。

### Q6: DelegatingPasswordEncoder 解决什么问题？

解决密码编码算法升级问题。通过 `{algorithm}` 前缀标识编码算法，系统可同时识别多种编码格式。新增用户用最新算法编码，老用户登录时自动检测旧算法并升级。实现了平滑的密码算法迁移。

### Q7: JWT 的优缺点？

**优点**：无状态（服务器不存储 Session）、可扩展、跨域支持好、适合微服务。**缺点**：1) 无法主动失效（需配合黑名单）；2) Token 过大（携带用户信息）；3) 续签复杂（需 Refresh Token 机制）；4) 安全性依赖 Token 存储（XSS/CSRF 防护仍然必要）。

### Q8: Spring Security 6 有哪些主要变化？

1) 移除 `WebSecurityConfigurerAdapter`，改为 `SecurityFilterChain` Bean；2) 全面使用 Lambda DSL；3) `AuthorizationFilter` 替代 `FilterSecurityInterceptor`；4) `AuthorizationManager` 替代 `AccessDecisionManager`；5) `requestMatchers()` 替代 `antMatchers()`/`mvcMatchers()`；6) 支持 `DeferredSecurityContext` 延迟加载；7) 集成 Spring Authorization Server 作为独立项目。

### Q9: 如何实现基于方法参数的授权？

使用 `@PreAuthorize` 配合 SpEL 表达式：`@PreAuthorize("#order.owner == authentication.principal.username")`。也可以调用自定义 Bean：`@PreAuthorize("@orderSecurity.canAccess(#orderId, authentication)")`。Spring Security 通过参数名（需 `-parameters` 编译选项或 `@P` 注解）引用方法参数。

### Q10: CSRF 防护的原理是什么？

CSRF 攻击利用用户已登录的身份，诱导用户在第三方网站发起请求。Spring Security 通过 CSRF Token 防护：1) 服务器生成随机 Token，存于 Session 或 Cookie；2) POST/PUT/DELETE 请求需携带 Token；3) 服务器校验 Token 一致性。对于无状态 API（JWT），可禁用 CSRF（因为不使用 Cookie 认证）。

### Q11: 并发会话控制如何实现？

通过 `SessionRegistry` 跟踪所有活跃会话。配置 `maximumSessions(1)` 限制每个用户只能有一个活跃会话。`maxSessionsPreventsLogin(true)` 阻止第二次登录，`false` 踢掉前一个会话。必须配置 `HttpSessionEventPublisher` 才能正确监听会话创建销毁事件。

### Q12: OAuth2 授权码模式的流程？

1) 客户端重定向用户到授权服务器的授权页面；2) 用户同意授权，授权服务器返回授权码（Authorization Code）到回调 URL；3) 客户端用授权码 + 客户端密钥向授权服务器换取 Access Token；4) 客户端使用 Access Token 访问资源服务器的受保护资源。授权码模式是最安全的模式，因为客户端密钥不经过浏览器。

*最后更新：2026-07-13*
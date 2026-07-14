# API安全实践

> 限流、防重放、签名验证，构建安全的API防护体系

---

## 📋 目录

1. [API安全威胁](#1-api安全威胁)
2. [认证与授权](#2-认证与授权)
3. [限流防刷](#3-限流防刷)
4. [防重放攻击](#4-防重放攻击)
5. [签名验证](#5-签名验证)
6. [数据安全](#6-数据安全)
7. [面试要点](#7-面试要点)

---

## 1. API安全威胁

| 威胁 | 说明 | 防护 |
|------|------|------|
| 未授权访问 | 无Token或Token伪造 | JWT认证 |
| 越权访问 | 普通用户访问管理接口 | RBAC权限控制 |
| 重放攻击 | 截获请求重复发送 | Timestamp + Nonce |
| 篡改攻击 | 修改请求参数 | 签名验证 |
| 暴力破解 | 撞库、密码穷举 | 限流 + 验证码 |
| SQL注入 | 恶意SQL参数 | 参数化查询 |
| XSS | 脚本注入 | 输入过滤 + 输出转义 |
| DDoS | 大量请求压垮服务 | 限流 + WAF |

---

## 2. 认证与授权

### JWT认证

```java
// API网关统一认证
@Component
public class JwtAuthFilter extends GlobalFilter {
    
    private static final List<String> WHITELIST = List.of(
        "/api/auth/login", "/api/auth/register", "/actuator/health"
    );
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        String path = exchange.getRequest().getURI().getPath();
        
        // 白名单放行
        if (WHITELIST.stream().anyMatch(path::startsWith)) {
            return chain.filter(exchange);
        }
        
        // 验证Token
        String token = exchange.getRequest().getHeaders().getFirst("Authorization");
        if (token == null || !token.startsWith("Bearer ")) {
            return unauthorized(exchange, "缺少认证Token");
        }
        
        try {
            Claims claims = Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token.substring(7))
                .getPayload();
            
            // 将用户信息传递给下游服务
            ServerHttpRequest request = exchange.getRequest().mutate()
                .header("X-User-Id", claims.getSubject())
                .header("X-User-Role", claims.get("role", String.class))
                .build();
            
            return chain.filter(exchange.mutate().request(request).build());
        } catch (Exception e) {
            return unauthorized(exchange, "Token无效或已过期");
        }
    }
}
```

### RBAC权限控制

```java
// 方法级权限注解
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/users/{id}")
public void deleteUser(@PathVariable Long id) {
    userMapper.deleteById(id);
}

@PreAuthorize("hasPermission(#orderId, 'order', 'read')")
@GetMapping("/orders/{orderId}")
public Order getOrder(@PathVariable Long orderId) {
    return orderService.getOrder(orderId);
}

// 数据级权限：只能查自己的订单
@GetMapping("/my-orders")
public List<Order> myOrders(@RequestHeader("X-User-Id") Long userId) {
    return orderMapper.findByUserId(userId);  // 强制加userId过滤
}
```

---

## 3. 限流防刷

### 多维度限流

```java
@Service
public class ApiRateLimiter {
    
    @Autowired
    private RedisTemplate<String, String> redis;
    
    // IP限流：每分钟100次
    public void checkIpRate(String ip, String api) {
        String key = "rate:ip:" + ip + ":" + api;
        Long count = redis.opsForValue().increment(key);
        if (count == 1) redis.expire(key, 60, TimeUnit.SECONDS);
        if (count > 100) throw new RateLimitException("请求过于频繁");
    }
    
    // 用户限流：每分钟60次
    public void checkUserRate(Long userId, String api) {
        String key = "rate:user:" + userId + ":" + api;
        Long count = redis.opsForValue().increment(key);
        if (count == 1) redis.expire(key, 60, TimeUnit.SECONDS);
        if (count > 60) throw new RateLimitException("操作过于频繁");
    }
    
    // 全局限流：每秒10000次
    public void checkGlobalRate(String api) {
        String key = "rate:global:" + api;
        Long count = redis.opsForValue().increment(key);
        if (count == 1) redis.expire(key, 1, TimeUnit.SECONDS);
        if (count > 10000) throw new RateLimitException("系统繁忙");
    }
}

// Sentinel限流
@SentinelResource(value = "api:createOrder", blockHandler = "rateLimitHandler")
@PostMapping("/orders")
public Order createOrder(@RequestBody OrderRequest request) {
    return orderService.create(request);
}
```

---

## 4. 防重放攻击

### Timestamp + Nonce方案

```
攻击场景：截获合法请求，重复发送（如重复下单）

防重放原理：
  1. 请求携带Timestamp（时间戳）和Nonce（随机数）
  2. 服务端校验Timestamp是否在有效期内（如5分钟）
  3. 服务端校验Nonce是否已使用过（Redis记录）
  4. Timestamp有效 + Nonce未使用 → 放行
```

```java
@Component
public class ReplayProtectionFilter extends OncePerRequestFilter {
    
    @Autowired
    private RedisTemplate<String, String> redis;
    
    private static final long VALID_WINDOW = 5 * 60 * 1000; // 5分钟
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
            HttpServletResponse response, FilterChain chain) throws Exception {
        
        String timestamp = request.getHeader("X-Timestamp");
        String nonce = request.getHeader("X-Nonce");
        
        if (timestamp == null || nonce == null) {
            response.setStatus(400);
            response.getWriter().write("缺少时间戳或随机数");
            return;
        }
        
        // 1. 校验时间戳
        long ts = Long.parseLong(timestamp);
        long now = System.currentTimeMillis();
        if (Math.abs(now - ts) > VALID_WINDOW) {
            response.setStatus(401);
            response.getWriter().write("请求已过期");
            return;
        }
        
        // 2. 校验Nonce是否已使用
        String nonceKey = "nonce:" + nonce;
        Boolean isNew = redis.opsForValue().setIfAbsent(
            nonceKey, "1", VALID_WINDOW, TimeUnit.MILLISECONDS);
        
        if (isNew == null || !isNew) {
            response.setStatus(401);
            response.getWriter().write("请求已处理，请勿重复提交");
            return;
        }
        
        chain.doFilter(request, response);
    }
}
```

### 幂等性设计

```java
// 业务层幂等：基于幂等键
@PostMapping("/orders")
public Order createOrder(@RequestBody CreateOrderRequest request) {
    String idempotentKey = request.getIdempotentKey();
    
    // 检查是否已处理
    Order existing = (Order) redis.opsForValue().get("idempotent:" + idempotentKey);
    if (existing != null) {
        return existing;  // 返回之前的处理结果
    }
    
    // 分布式锁防止并发重复
    String lockKey = "lock:order:" + idempotentKey;
    try {
        if (redisLock.tryLock(lockKey, 10, TimeUnit.SECONDS)) {
            // 再次检查（双重确认）
            existing = (Order) redis.opsForValue().get("idempotent:" + idempotentKey);
            if (existing != null) return existing;
            
            // 创建订单
            Order order = orderService.create(request);
            
            // 缓存结果（30分钟）
            redis.opsForValue().set("idempotent:" + idempotentKey, order, 30, TimeUnit.MINUTES);
            
            return order;
        } else {
            throw new BusinessException("请求处理中，请稍后");
        }
    } finally {
        redisLock.unlock(lockKey);
    }
}
```

---

## 5. 签名验证

### HMAC-SHA256签名

```
签名流程：
  1. 客户端：按固定顺序拼接参数 + 时间戳 + 密钥 → HMAC-SHA256 → 签名
  2. 服务端：用相同算法验签

签名格式：
  Signature = HMAC-SHA256(secretKey, method + path + params + timestamp + nonce)
```

```java
// 服务端验签
@Component
public class SignatureFilter extends OncePerRequestFilter {
    
    @Value("${api.secret-key}")
    private String secretKey;
    
    @Override
    protected void doFilterInternal(HttpServletRequest request, 
            HttpServletResponse response, FilterChain chain) throws Exception {
        
        String signature = request.getHeader("X-Signature");
        String timestamp = request.getHeader("X-Timestamp");
        String nonce = request.getHeader("X-Nonce");
        
        // 1. 读取请求体（缓存以便后续使用）
        ContentCachingRequestWrapper wrappedRequest = new ContentCachingRequestWrapper(request);
        
        // 2. 构建待签名字符串
        String method = request.getMethod();
        String path = request.getRequestURI();
        String queryString = request.getQueryString() != null ? request.getQueryString() : "";
        String body = IOUtils.toString(wrappedRequest.getInputStream(), StandardCharsets.UTF_8);
        
        String signContent = method + "\n" + path + "\n" + queryString + "\n" 
            + body + "\n" + timestamp + "\n" + nonce;
        
        // 3. 计算签名
        String computedSignature = HmacUtils.hmacSha256Hex(secretKey, signContent);
        
        // 4. 验签
        if (!MessageDigest.isEqual(
                computedSignature.getBytes(), 
                signature.getBytes())) {
            response.setStatus(401);
            response.getWriter().write("签名验证失败");
            return;
        }
        
        chain.doFilter(wrappedRequest, response);
    }
}

// 客户端签名
public class ApiSignUtil {
    
    public static String sign(String secretKey, String method, String path, 
            Map<String, String> params, String body, String timestamp, String nonce) {
        // 参数按key排序拼接
        String queryString = params.entrySet().stream()
            .sorted(Map.Entry.comparingByKey())
            .map(e -> e.getKey() + "=" + e.getValue())
            .collect(Collectors.joining("&"));
        
        String signContent = method + "\n" + path + "\n" + queryString + "\n"
            + body + "\n" + timestamp + "\n" + nonce;
        
        return HmacUtils.hmacSha256Hex(secretKey, signContent);
    }
}
```

---

## 6. 数据安全

### 传输安全

```yaml
# HTTPS配置
server:
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: ${SSL_PASSWORD}
    key-store-type: PKCS12
```

### 敏感数据脱敏

```java
// 响应脱敏
public class UserVO {
    private String name;
    
    @JsonSerialize(using = PhoneMaskSerializer.class)
    private String phone;  // 138****5678
    
    @JsonSerialize(using = EmailMaskSerializer.class)
    private String email;  // z***@example.com
    
    @JsonIgnore
    private String password;  // 不返回
    private String idCard;    // 不返回
}

// 日志脱敏
@LogMask(fields = {"phone", "idCard", "password"})
public void register(RegisterRequest request) {
    // 日志中phone显示为 138****5678
    log.info("用户注册: {}", request);
}
```

### SQL注入防护

```java
// ❌ 拼接SQL（危险）
String sql = "SELECT * FROM users WHERE name = '" + name + "'";

// ✅ 参数化查询（安全）
@Select("SELECT * FROM users WHERE name = #{name}")
User findByName(@Param("name") String name);

// ✅ QueryWrapper
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(User::getName, name);
```

---

## 7. 面试要点

### Q1: 如何防止API重放攻击？

```
Timestamp + Nonce方案：
1. 客户端请求携带时间戳和随机数
2. 服务端校验时间戳在5分钟有效期内
3. 服务端用Redis记录Nonce，5分钟内不重复使用
4. 同时满足时间有效+Nonce未使用才放行

效果：截获的请求5分钟后失效，5分钟内Nonce已记录无法重放
```

### Q2: API签名验证的流程？

```
客户端：
1. 按固定顺序拼接：HTTP方法 + 路径 + 参数 + 请求体 + 时间戳 + 随机数
2. 用密钥做HMAC-SHA256计算签名
3. 请求头携带签名、时间戳、随机数

服务端：
1. 按相同规则拼接待签名字符串
2. 用相同密钥计算签名
3. 对比两个签名是否一致
4. 不一致 → 拒绝（参数被篡改）
```

### Q3: 如何实现接口幂等性？

```
1. 唯一索引：数据库唯一约束（如订单号唯一）
2. 幂等键：客户端生成幂等键，服务端Redis记录处理结果
3. Token机制：获取Token → 提交时验证Token → 删除Token
4. 状态机：业务状态流转控制（待支付→已支付，不可重复支付）
5. 乐观锁：version版本号控制
```

### Q4: API限流怎么实现？

```
1. Sentinel：注解驱动，支持多种限流策略
2. Redis计数器：INCR + EXPIRE实现滑动窗口
3. 令牌桶：Guava RateLimiter或Sentinel
4. 多维度：IP限流 + 用户限流 + 接口限流 + 全局限流
5. 网关层限流：Spring Cloud Gateway + Redis限流
```

### Q5: JWT Token泄露怎么办？

```
1. 短期Token：Access Token有效期15分钟
2. Refresh Token：有效期7天，用于刷新Access Token
3. 黑名单：登出时将Token加入Redis黑名单
4. Token绑定：绑定IP/设备指纹，异常IP拒绝
5. 强制下线：通过Redis标记用户所有Token失效
6. HTTPS传输：防止中间人攻击截获Token
```

---

## 📚 相关阅读

- [02_Spring Security与JWT实战](./02_Spring Security与JWT实战.md)
- [03_SSO单点登录方案](./03_SSO单点登录方案.md)
- [01_OAuth2.0实战案例](./01_OAuth2.0实战案例.md)
- [Sentinel流量控制详解](../06_微服务/03_服务治理/01_Sentinel流量控制详解.md)

# RBAC权限模型

> 基于角色的访问控制：用户→角色→权限的三层授权体系

---

## 📋 目录

1. [RBAC概述](#1-rbac概述)
2. [RBAC模型体系](#2-rbac模型体系)
3. [数据库设计](#3-数据库设计)
4. [Spring Security实现](#4-spring-security实现)
5. [权限缓存方案](#5-权限缓存方案)
6. [动态权限加载](#6-动态权限加载)
7. [面试题速查](#7-面试题速查)

---

## 1. RBAC概述

```
RBAC = Role-Based Access Control（基于角色的访问控制）

核心思想：用户不直接拥有权限，而是通过角色间接获得权限

  用户(User) → 角色(Role) → 权限(Permission) → 资源(Resource)

优势：
  - 权限管理集中化（角色为中介）
  - 减少权限分配工作量（角色批量授权）
  - 权限变更灵活（修改角色权限即可）
  - 符合组织架构（角色对应岗位）

对比ACL（访问控制列表）：
  ACL：用户 → 权限（直接关联）
  问题：100个用户×10个权限 = 1000条授权记录
  RBAC：100个用户→5个角色→10个权限 = 105条记录
```

---

## 2. RBAC模型体系

### 2.1 RBAC0（基础模型）

```
RBAC0 = 用户 + 角色 + 权限 + 会话

  ┌──────┐    多对多    ┌──────┐    多对多    ┌──────────┐
  │ 用户  │ ←─────────→ │ 角色  │ ←─────────→ │  权限     │
  └──────┘              └──────┘              └──────────┘
                                                    │
                                                    ▼
                                              ┌──────────┐
                                              │  资源     │
                                              └──────────┘

关系：
  - 用户-角色：多对多（一个用户有多个角色，一个角色属于多个用户）
  - 角色-权限：多对多（一个角色有多个权限，一个权限属于多个角色）
```

### 2.2 RBAC1（角色继承）

```
RBAC1 = RBAC0 + 角色继承

  超级管理员
      │ 继承
  ┌───┴───┐
  部门管理员    系统管理员
      │           │ 继承
  ┌───┴───┐   ┌──┴──┐
  组长    主管   运维   开发

特点：
  - 子角色自动继承父角色的权限
  - 减少重复授权
  - 符合组织层级结构
```

### 2.3 RBAC2（责任分离）

```
RBAC2 = RBAC0 + 责任分离约束

三种约束：
  1. 互斥角色：一个用户不能同时拥有互斥角色
     例：制单人和审核人不能是同一人

  2. 基数约束：一个角色拥有的用户数量限制
     例：管理员最多3人

  3. 先决条件：获得角色B的前提是已有角色A
     例：获得"审核员"角色前必须已有"操作员"角色
```

### 2.4 RBAC3（完整模型）

```
RBAC3 = RBAC1 + RBAC2 = 完整模型

包含：用户、角色、权限、资源、角色继承、责任分离约束
企业级权限系统通常基于RBAC3实现
```

---

## 3. 数据库设计

### 3.1 表结构设计

```sql
-- 用户表
CREATE TABLE sys_user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    status TINYINT DEFAULT 1 COMMENT '1启用 0禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 角色表
CREATE TABLE sys_role (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_code VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码 如ROLE_ADMIN',
    role_name VARCHAR(50) NOT NULL COMMENT '角色名称',
    parent_id BIGINT DEFAULT 0 COMMENT '父角色ID（角色继承）',
    description VARCHAR(200),
    status TINYINT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
CREATE TABLE sys_permission (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    parent_id BIGINT DEFAULT 0 COMMENT '父权限ID（树形结构）',
    permission_code VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码 如user:create',
    permission_name VARCHAR(50) NOT NULL,
    type TINYINT COMMENT '1菜单 2按钮 3接口',
    url VARCHAR(200) COMMENT '访问路径',
    method VARCHAR(10) COMMENT 'HTTP方法',
    sort_order INT DEFAULT 0,
    status TINYINT DEFAULT 1
);

-- 用户-角色关联表
CREATE TABLE sys_user_role (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id)
);

-- 角色-权限关联表
CREATE TABLE sys_role_permission (
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, permission_id)
);

-- 索引
CREATE INDEX idx_user_role_user ON sys_user_role(user_id);
CREATE INDEX idx_user_role_role ON sys_user_role(role_id);
CREATE INDEX idx_role_permission_role ON sys_role_permission(role_id);
CREATE INDEX idx_role_permission_perm ON sys_role_permission(permission_id);
```

### 3.2 权限查询SQL

```sql
-- 查询用户的所有权限（含角色继承）
SELECT DISTINCT p.permission_code
FROM sys_user u
JOIN sys_user_role ur ON u.id = ur.user_id
JOIN sys_role r ON ur.role_id = r.id
-- 递归查询角色继承链
JOIN (
    WITH RECURSIVE role_tree AS (
        SELECT id FROM sys_role WHERE id = r.id
        UNION ALL
        SELECT r2.id FROM sys_role r2 
        JOIN role_tree rt ON r2.parent_id = rt.id
    )
    SELECT id FROM role_tree
) all_roles ON all_roles.id = r.id
JOIN sys_role_permission rp ON rp.role_id = all_roles.id
JOIN sys_permission p ON rp.permission_id = p.id
WHERE u.id = #{userId} AND p.status = 1;

-- 简化版（不含角色继承）
SELECT DISTINCT p.permission_code
FROM sys_user u
JOIN sys_user_role ur ON u.id = ur.user_id
JOIN sys_role_permission rp ON ur.role_id = rp.role_id
JOIN sys_permission p ON rp.permission_id = p.id
WHERE u.id = #{userId} AND u.status = 1 AND p.status = 1;
```

---

## 4. Spring Security实现

### 4.1 配置RBAC

```java
@Configuration
@EnableMethodSecurity  // 开启方法级权限控制
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth
            // 公开接口
            .requestMatchers("/login", "/register", "/public/**").permitAll()
            // 基于权限的访问控制
            .requestMatchers("/api/users/**").hasAuthority("user:manage")
            .requestMatchers("/api/orders/**").hasAuthority("order:manage")
            .requestMatchers(HttpMethod.GET, "/api/products/**").hasAuthority("product:read")
            .requestMatchers(HttpMethod.POST, "/api/products/**").hasAuthority("product:create")
            // 其余需要认证
            .anyRequest().authenticated()
        )
        .sessionManagement(session -> session
            .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
        )
        .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
```

### 4.2 自定义UserDetailsService

```java
@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    @Autowired private UserMapper userMapper;
    @Autowired private RoleMapper roleMapper;
    @Autowired private PermissionMapper permissionMapper;

    @Override
    public UserDetails loadUserByUsername(String username) {
        // 1. 查用户
        User user = userMapper.findByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在");
        }

        // 2. 查角色
        List<String> roles = roleMapper.findRoleCodesByUserId(user.getId());

        // 3. 查权限
        List<String> permissions = permissionMapper.findPermissionCodesByUserId(user.getId());

        // 4. 构建GrantedAuthority
        List<GrantedAuthority> authorities = new ArrayList<>();
        // 角色需要加ROLE_前缀
        roles.forEach(role -> authorities.add(new SimpleGrantedAuthority("ROLE_" + role)));
        // 权限直接使用
        permissions.forEach(perm -> authorities.add(new SimpleGrantedAuthority(perm)));

        return new org.springframework.security.core.userdetails.User(
            user.getUsername(),
            user.getPassword(),
            user.getStatus() == 1,  // enabled
            true, true, true,
            authorities
        );
    }
}
```

### 4.3 方法级权限控制

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @PreAuthorize("hasAuthority('user:read')")
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) { ... }

    @PreAuthorize("hasAuthority('user:create')")
    @PostMapping
    public User create(@RequestBody UserDTO dto) { ... }

    @PreAuthorize("hasAuthority('user:update')")
    @PutMapping("/{id}")
    public User update(@PathVariable Long id, @RequestBody UserDTO dto) { ... }

    @PreAuthorize("hasAuthority('user:delete')")
    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) { ... }

    // 角色判断
    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/admin/list")
    public List<User> adminList() { ... }

    // 组合判断
    @PreAuthorize("hasAuthority('user:read') and hasRole('ADMIN')")
    @GetMapping("/sensitive")
    public List<User> sensitiveList() { ... }
}
```

---

## 5. 权限缓存方案

```java
// 权限不频繁变更，适合缓存
@Service
public class PermissionService {

    @Autowired private PermissionMapper permissionMapper;
    @Autowired private RedisTemplate<String, Object> redisTemplate;

    private static final String PERM_KEY = "user:permissions:";
    private static final long PERM_TTL = 30; // 分钟

    @Cacheable(value = "permissions", key = "#userId")
    public Set<String> getUserPermissions(Long userId) {
        // 先查Redis
        Set<String> cached = (Set<String>) redisTemplate.opsForValue()
            .get(PERM_KEY + userId);
        if (cached != null) return cached;

        // 查DB
        List<String> perms = permissionMapper.findPermissionCodesByUserId(userId);
        Set<String> permSet = new HashSet<>(perms);

        // 回填缓存
        redisTemplate.opsForValue().set(PERM_KEY + userId, permSet, PERM_TTL, TimeUnit.MINUTES);
        return permSet;
    }

    // 权限变更时清除缓存
    public void clearPermissionCache(Long userId) {
        redisTemplate.delete(PERM_KEY + userId);
    }

    // 角色权限变更时，清除该角色所有用户的缓存
    public void clearRolePermissionCache(Long roleId) {
        List<Long> userIds = userMapper.findUserIdsByRoleId(roleId);
        userIds.forEach(uid -> redisTemplate.delete(PERM_KEY + uid));
    }
}
```

---

## 6. 动态权限加载

```java
// 启动时从DB加载所有URL→权限映射，运行时动态更新
@Component
public class DynamicSecurityService {

    @Autowired private PermissionMapper permissionMapper;

    private Map<String, String> urlPermissionMap = new ConcurrentHashMap<>();

    @PostConstruct
    public void loadUrlPermissions() {
        List<Permission> perms = permissionMapper.findAllUrlPermissions();
        urlPermissionMap = perms.stream()
            .collect(Collectors.toMap(
                p -> p.getMethod() + ":" + p.getUrl(),
                Permission::getPermissionCode
            ));
    }

    // 动态新增权限（不重启）
    public void addPermission(Permission perm) {
        urlPermissionMap.put(perm.getMethod() + ":" + perm.getUrl(), 
            perm.getPermissionCode());
    }

    // 动态删除权限
    public void removePermission(String method, String url) {
        urlPermissionMap.remove(method + ":" + url);
    }

    // 检查是否有权限
    public boolean hasPermission(String method, String url, Set<String> userPerms) {
        String requiredPerm = urlPermissionMap.get(method + ":" + url);
        if (requiredPerm == null) return true;  // 无需权限
        return userPerms.contains(requiredPerm);
    }
}
```

---

## 7. 面试题速查

**Q1: RBAC和ACL的区别？**
```
ACL：用户直接关联权限，简单但管理成本高
RBAC：用户→角色→权限，通过角色间接授权
RBAC优势：批量授权、角色继承、责任分离
```

**Q2: RBAC的四个模型？**
```
RBAC0：基础模型（用户-角色-权限）
RBAC1：RBAC0 + 角色继承
RBAC2：RBAC0 + 责任分离（互斥/基数/先决条件）
RBAC3：RBAC1 + RBAC2（完整模型）
```

**Q3: Spring Security中hasRole和hasAuthority的区别？**
```
hasRole("ADMIN")：检查ROLE_ADMIN（自动加ROLE_前缀）
hasAuthority("user:create")：直接检查权限码（不加前缀）
角色用hasRole，权限用hasAuthority
```

**Q4: 权限缓存如何设计？**
```
1. 用户权限缓存到Redis（key=user:permissions:{userId}）
2. TTL 30分钟
3. 权限/角色变更时清除相关用户缓存
4. 角色变更时清除该角色所有用户的缓存
```

---

*最后更新：2026-07-13*

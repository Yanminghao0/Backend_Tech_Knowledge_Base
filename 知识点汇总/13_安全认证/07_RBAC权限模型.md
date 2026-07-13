# RBAC权限模型详解

> RBAC（Role-Based Access Control，基于角色的访问控制）是企业级应用中最广泛使用的权限管理模型。它通过引入"角色"这一中间层，将用户与权限解耦——用户被分配角色，角色拥有权限，从而大幅简化权限管理复杂度。从RBAC0到RBAC3，模型逐步引入角色继承和责任分离机制，覆盖了从简单系统到高安全要求场景的全部需求。Spring Security对RBAC提供了原生支持，使其成为Java生态中的事实标准。

---

## 📋 目录

1. [RBAC核心概念](#1-rbac核心概念)
2. [RBAC0基础模型](#2-rbac0基础模型)
3. [RBAC1角色继承](#3-rbac1角色继承)
4. [RBAC2责任分离](#4-rbac2责任分离)
5. [RBAC3综合模型](#5-rbac3综合模型)
6. [RBAC与ACL对比](#6-rbac与acl对比)
7. [数据库表设计](#7-数据库表设计)
8. [Spring Security RBAC实现](#8-spring-security-rbac实现)
9. [权限缓存方案](#9-权限缓存方案)
10. [动态权限加载](#10-动态权限加载)
11. [面试题速查](#11-面试题速查)

---

## 1. RBAC核心概念

### 1.1 四大核心实体

RBAC模型围绕四个核心实体构建：

| 实体 | 英文 | 说明 | 示例 |
|------|------|------|------|
| **用户** | User | 系统的使用者，可以是真人或服务账号 | 张三、李四、order-service |
| **角色** | Role | 权限的集合，代表某种职能或职位 | 管理员、运营人员、财务审核员 |
| **权限** | Permission | 对资源执行某种操作的能力 | user:create、order:delete |
| **资源** | Resource | 被保护的对象 | 菜单、API接口、按钮、数据行 |

### 1.2 权限关系链

```
用户(User) ──分配──> 角色(Role) ──拥有──> 权限(Permission) ──作用于──> 资源(Resource)
```

核心思想：用户不直接拥有权限，而是通过角色间接获得权限。一个用户可以拥有多个角色，一个角色可以包含多个权限，多对多关系。

### 1.3 为什么需要角色这个中间层

考虑一个有1000个用户、50种权限的系统：

- **无角色（直接授权）**：每个用户逐一分配50种权限，共需管理5万条权限分配记录。某职位权限变更，需要修改所有该职位用户的权限。
- **有角色**：定义10个角色，每个角色绑定若干权限。用户只需分配角色（1000条记录），权限变更只需调整角色（10次修改），管理复杂度从O(用户数×权限数)降低到O(角色数×权限数 + 用户数)。

---

## 2. RBAC0基础模型

### 2.1 模型定义

RBAC0是RBAC家族的最基础模型，定义了用户-角色-权限的基本关系：

- 用户与角色：多对多
- 角色与权限：多对多
- 权限与资源：一对多（一个权限对应一种操作，可作用于多种资源）

### 2.2 模型结构图

```
    ┌──────┐         ┌──────┐         ┌────────────┐         ┌──────┐
    │ User │ ──N:M──>│ Role │ ──N:M──>│ Permission │ ──1:N──>│Resource│
    └──────┘         └──────┘         └────────────┘         └──────┘
       │                                                       │
       │         用户通过角色间接获得权限                          │
       │                                                       │
       └───────────────────────────────────────────────────────┘
```

### 2.3 访问控制流程

```java
// 权限校验核心流程
public class AccessControlService {

    private UserRoleService userRoleService;
    private RolePermissionService rolePermissionService;

    /**
     * 检查用户是否拥有指定权限
     */
    public boolean hasPermission(Long userId, String permissionCode) {
        // 1. 查询用户拥有的所有角色
        Set<Role> roles = userRoleService.getRolesByUserId(userId);
        if (roles.isEmpty()) {
            return false;
        }

        // 2. 查询这些角色拥有的所有权限
        Set<String> permissions = new HashSet<>();
        for (Role role : roles) {
            permissions.addAll(rolePermissionService.getPermissionCodesByRoleId(role.getId()));
        }

        // 3. 判断是否包含目标权限
        return permissions.contains(permissionCode);
    }

    /**
     * 检查用户是否拥有某个角色
     */
    public boolean hasRole(Long userId, String roleCode) {
        Set<Role> roles = userRoleService.getRolesByUserId(userId);
        return roles.stream()
                .anyMatch(role -> role.getCode().equals(roleCode));
    }
}
```

### 2.4 权限粒度

RBAC0支持不同粒度的权限控制：

| 粒度 | 说明 | 示例 |
|------|------|------|
| **菜单级** | 控制页面/菜单可见性 | 用户管理菜单、系统设置菜单 |
| **功能级** | 控制按钮/操作可见性 | 新增按钮、删除按钮 |
| **API级** | 控制接口访问权限 | `POST /api/users`、`DELETE /api/orders/{id}` |
| **数据级** | 控制数据范围 | 只能查看本部门数据、只能查看自己的订单 |

---

## 3. RBAC1角色继承

### 3.1 模型定义

RBAC1在RBAC0的基础上引入了**角色继承**（Role Hierarchy）机制。角色可以继承其他角色的权限，子角色自动拥有父角色的所有权限。

### 3.2 继承结构示例

```
          ┌────────────┐
          │  超级管理员  │ (拥有所有权限)
          └──────┬─────┘
                 │ 继承
         ┌───────┴───────┐
         │               │
  ┌──────┴──────┐ ┌──────┴──────┐
  │  系统管理员  │ │  业务管理员  │
  └──────┬──────┘ └──────┬──────┘
         │               │ 继承
  ┌──────┴──────┐ ┌──────┴──────┐
  │  运营人员    │ │  财务审核员  │
  └──────┬──────┘ └──────┬──────┘
         │               │ 继承
  ┌──────┴──────┐ ┌──────┴──────┐
  │  普通用户    │ │  财务录入员  │
  └─────────────┘ └─────────────┘
```

### 3.3 数据库设计

在角色表中增加`parent_id`字段表示继承关系：

```sql
-- 角色表（增加父角色字段）
CREATE TABLE sys_role (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(50) NOT NULL COMMENT '角色名称',
    code        VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
    parent_id   BIGINT COMMENT '父角色ID，为空表示顶级角色',
    sort        INT DEFAULT 0 COMMENT '排序',
    status      TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.4 递归查询权限

```java
public class RoleHierarchyService {

    /**
     * 获取角色及其所有祖先角色的全部权限（包含继承的权限）
     */
    public Set<String> getAllPermissionCodes(Long roleId) {
        Set<String> permissions = new HashSet<>();
        Set<Long> visitedRoleIds = new HashSet<>(); // 防止循环引用

        collectPermissions(roleId, permissions, visitedRoleIds);
        return permissions;
    }

    private void collectPermissions(Long roleId, Set<String> permissions, Set<Long> visited) {
        if (visited.contains(roleId)) {
            return; // 防止循环继承
        }
        visited.add(roleId);

        // 获取当前角色的直接权限
        permissions.addAll(rolePermissionService.getPermissionCodesByRoleId(roleId));

        // 递归获取父角色权限
        Role role = roleService.getById(roleId);
        if (role.getParentId() != null) {
            collectPermissions(role.getParentId(), permissions, visited);
        }
    }

    /**
     * 判断角色A是否是角色B的祖先（即角色B继承了角色A）
     */
    public boolean isAncestorOf(Long ancestorId, Long descendantId) {
        Role descendant = roleService.getById(descendantId);
        while (descendant.getParentId() != null) {
            if (descendant.getParentId().equals(ancestorId)) {
                return true;
            }
            descendant = roleService.getById(descendant.getParentId());
        }
        return false;
    }
}
```

---

## 4. RBAC2责任分离

### 4.1 模型定义

RBAC2在RBAC0的基础上引入了**约束**（Constraints）机制，用于防止权力滥用和利益冲突。这是高安全要求系统（如金融、军工）的关键特性。

### 4.2 三种核心约束

#### 4.2.1 职责互斥分离

互斥的角色不能同时分配给同一用户，防止权力集中。经典场景：制单人与审核人不能是同一人。

```java
public class MutuallyExclusiveConstraint {

    // 定义互斥角色对
    private static final Map<String, String> MUTUALLY_EXCLUSIVE_ROLES = Map.of(
        "invoice_creator",   "invoice_auditor",    // 制单人与审核人互斥
        "payment_initiator", "payment_approver",   // 付款发起人与审批人互斥
        "data_entry",        "data_audit"           // 数据录入与数据审核互斥
    );

    /**
     * 检查角色分配是否违反互斥约束
     */
    public void checkMutualExclusion(Long userId, String newRoleCode) {
        Set<String> userRoles = userRoleService.getRoleCodesByUserId(userId);

        String exclusiveRole = MUTUALLY_EXCLUSIVE_ROLES.get(newRoleCode);
        if (exclusiveRole != null && userRoles.contains(exclusiveRole)) {
            throw new PermissionException(
                String.format("角色[%s]与用户已有角色[%s]互斥，不能同时分配", newRoleCode, exclusiveRole)
            );
        }

        // 反向检查
        for (String userRole : userRoles) {
            String exclusive = MUTUALLY_EXCLUSIVE_ROLES.get(userRole);
            if (newRoleCode.equals(exclusive)) {
                throw new PermissionException(
                    String.format("角色[%s]与用户已有角色[%s]互斥，不能同时分配", newRoleCode, userRole)
                );
            }
        }
    }
}
```

#### 4.2.2 角色基数约束

限制一个角色可以被分配给多少个用户，或一个用户最多可以拥有多少个角色。

```java
public class CardinalityConstraint {

    /**
     * 检查角色基数：限制单个角色的最大用户数
     * 例如：超级管理员最多3人
     */
    public void checkRoleCardinality(Long roleId, int maxUsers) {
        int currentUsers = userRoleService.countUsersByRoleId(roleId);
        if (currentUsers >= maxUsers) {
            throw new PermissionException(
                String.format("角色用户数已达上限[%d]，无法继续分配", maxUsers)
            );
        }
    }

    /**
     * 检查用户角色数：限制单个用户最多拥有的角色数
     * 例如：普通用户最多3个角色
     */
    public void checkUserCardinality(Long userId, int maxRoles) {
        int currentRoles = userRoleService.countRolesByUserId(userId);
        if (currentRoles >= maxRoles) {
            throw new PermissionException(
                String.format("用户已拥有[%d]个角色，已达上限[%d]", currentRoles, maxRoles)
            );
        }
    }
}
```

#### 4.2.3 先决条件约束

用户必须先拥有角色A，才能被分配角色B。例如：必须先拥有"普通员工"角色，才能获得"组长"角色。

```java
public class PrerequisiteConstraint {

    // 角色先决条件映射：要获得角色B，必须先拥有角色A
    private static final Map<String, String> PREREQUISITE_ROLES = Map.of(
        "team_leader",    "employee",       // 要成为组长，必须先是员工
        "department_mgr", "team_leader",    // 要成为部门经理，必须先是组长
        "vp",             "department_mgr"  // 要成为VP，必须先是部门经理
    );

    /**
     * 检查先决条件
     */
    public void checkPrerequisite(Long userId, String newRoleCode) {
        String prerequisite = PREREQUISITE_ROLES.get(newRoleCode);
        if (prerequisite == null) {
            return; // 无先决条件
        }

        Set<String> userRoles = userRoleService.getRoleCodesByUserId(userId);
        if (!userRoles.contains(prerequisite)) {
            throw new PermissionException(
                String.format("分配角色[%s]需要先拥有角色[%s]", newRoleCode, prerequisite)
            );
        }
    }
}
```

---

## 5. RBAC3综合模型

### 5.1 模型定义

RBAC3 = RBAC1 + RBAC2，是最完整的RBAC模型，同时支持角色继承和约束机制。

### 5.2 完整的权限分配校验流程

```java
@Service
public class RoleAssignmentService {

    @Autowired private RoleHierarchyService roleHierarchyService;
    @Autowired private MutuallyExclusiveConstraint mutexConstraint;
    @Autowired private CardinalityConstraint cardinalityConstraint;
    @Autowired private PrerequisiteConstraint prerequisiteConstraint;

    /**
     * 分配角色（完整校验流程）
     */
    @Transactional
    public void assignRole(Long userId, Long roleId) {
        Role role = roleService.getById(roleId);
        if (role == null || role.getStatus() != 1) {
            throw new PermissionException("角色不存在或已禁用");
        }

        // RBAC2: 互斥检查
        mutexConstraint.checkMutualExclusion(userId, role.getCode());

        // RBAC2: 基数检查
        cardinalityConstraint.checkRoleCardinality(roleId, role.getMaxUsers());
        cardinalityConstraint.checkUserCardinality(userId, 5); // 用户最多5个角色

        // RBAC2: 先决条件检查
        prerequisiteConstraint.checkPrerequisite(userId, role.getCode());

        // 执行分配
        userRoleService.insert(userId, roleId);

        // 清除权限缓存
        permissionCacheService.evictUserPermissionCache(userId);
    }
}
```

---

## 6. RBAC与ACL对比

### 6.1 ACL（访问控制列表）

ACL是更底层的权限模型，直接在每个资源上维护一个访问控制列表，记录哪些用户/组对该资源有何种权限。

```java
// ACL模型示例
public class ACL {
    private Long resourceId;
    private Map<Long, Set<Permission>> userPermissions = new HashMap<>();
    // key: userId, value: 该用户对此资源的权限集合

    public boolean check(Long userId, Permission permission) {
        Set<Permission> perms = userPermissions.get(userId);
        return perms != null && perms.contains(permission);
    }
}
```

### 6.2 对比表

| 维度 | ACL | RBAC |
|------|-----|------|
| **授权方式** | 用户直接关联权限 | 用户→角色→权限 |
| **管理复杂度** | O(用户数×资源数)，高 | O(角色数×权限数+用户数)，低 |
| **权限变更** | 需要修改每个用户的权限 | 只需修改角色的权限 |
| **适用场景** | 用户少、资源固定的系统 | 用户多、角色明确的系统 |
| **权限继承** | 不支持 | 支持角色继承（RBAC1） |
| **约束机制** | 不支持 | 支持互斥/基数/先决条件（RBAC2） |
| **数据级权限** | 天然支持 | 需要额外扩展 |
| **灵活性** | 高（每个用户可独立配置） | 中（受角色约束） |
| **典型应用** | 文件系统权限、网络设备ACL | 企业应用、后台管理系统 |

### 6.3 混合模式

实际项目中常常混合使用ACL和RBAC：

```java
// RBAC管理功能权限 + ACL管理数据权限
public class HybridAccessControl {

    /**
     * 综合权限校验：先检查功能权限（RBAC），再检查数据权限（ACL）
     */
    public boolean canAccess(Long userId, String permissionCode, Long dataId) {
        // 1. RBAC检查：用户是否有操作权限
        if (!rbacService.hasPermission(userId, permissionCode)) {
            return false;
        }

        // 2. ACL检查：用户是否能访问该条数据
        DataPermission dataPerm = aclService.getDataPermission(userId, dataId);
        return dataPerm != null && dataPerm.canRead();
    }
}
```

---

## 7. 数据库表设计

### 7.1 完整表结构

```sql
-- ==========================================
-- 用户表
-- ==========================================
CREATE TABLE sys_user (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username    VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password    VARCHAR(100) NOT NULL COMMENT '密码（加密后）',
    nickname    VARCHAR(50) COMMENT '昵称',
    email       VARCHAR(100) COMMENT '邮箱',
    phone       VARCHAR(20) COMMENT '手机号',
    dept_id     BIGINT COMMENT '部门ID',
    status      TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dept_id (dept_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ==========================================
-- 角色表
-- ==========================================
CREATE TABLE sys_role (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    name        VARCHAR(50) NOT NULL COMMENT '角色名称',
    code        VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
    parent_id   BIGINT COMMENT '父角色ID（支持继承）',
    sort        INT DEFAULT 0 COMMENT '排序号',
    max_users   INT DEFAULT 0 COMMENT '最大用户数，0表示不限',
    status      TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    remark      VARCHAR(200) COMMENT '备注',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_parent_id (parent_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- ==========================================
-- 权限表
-- ==========================================
CREATE TABLE sys_permission (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    name        VARCHAR(50) NOT NULL COMMENT '权限名称',
    code        VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码，如 user:create',
    type        VARCHAR(20) NOT NULL COMMENT '类型：menu/button/api',
    parent_id   BIGINT COMMENT '父权限ID（菜单树）',
    path        VARCHAR(200) COMMENT '路由路径（菜单）',
    component   VARCHAR(200) COMMENT '组件路径（菜单）',
    icon        VARCHAR(50) COMMENT '图标',
    sort        INT DEFAULT 0 COMMENT '排序号',
    status      TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_parent_id (parent_id),
    INDEX idx_type (type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限表';

-- ==========================================
-- 资源表（可选，当权限需要细粒度关联资源时使用）
-- ==========================================
CREATE TABLE sys_resource (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL COMMENT '资源名称',
    type        VARCHAR(20) NOT NULL COMMENT '类型：api/button/data',
    uri         VARCHAR(200) COMMENT '资源URI',
    method      VARCHAR(10) COMMENT 'HTTP方法',
    description VARCHAR(200) COMMENT '描述',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资源表';

-- ==========================================
-- 用户-角色关联表
-- ==========================================
CREATE TABLE sys_user_role (
    id      BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- ==========================================
-- 角色-权限关联表
-- ==========================================
CREATE TABLE sys_role_permission (
    id            BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id       BIGINT NOT NULL COMMENT '角色ID',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联表';

-- ==========================================
-- 互斥角色表（RBAC2约束）
-- ==========================================
CREATE TABLE sys_role_mutex (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_id_a    BIGINT NOT NULL COMMENT '角色A',
    role_id_b    BIGINT NOT NULL COMMENT '角色B（与A互斥）',
    description  VARCHAR(200) COMMENT '互斥说明',
    UNIQUE KEY uk_mutex (role_id_a, role_id_b)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='互斥角色表';
```

### 7.2 查询用户完整权限的SQL

```sql
-- 查询用户拥有的所有权限编码（含角色继承）
WITH RECURSIVE role_tree AS (
    -- 起点：用户直接拥有的角色
    SELECT r.id, r.parent_id, r.code
    FROM sys_role r
    INNER JOIN sys_user_role ur ON ur.role_id = r.id
    WHERE ur.user_id = #{userId} AND r.status = 1

    UNION ALL

    -- 递归：向上查找父角色
    SELECT parent.id, parent.parent_id, parent.code
    FROM sys_role parent
    INNER JOIN role_tree rt ON rt.parent_id = parent.id
    WHERE parent.status = 1
)
SELECT DISTINCT p.code, p.name, p.type, p.path, p.component, p.icon
FROM role_tree rt
INNER JOIN sys_role_permission rp ON rp.role_id = rt.id
INNER JOIN sys_permission p ON p.id = rp.permission_id
WHERE p.status = 1
ORDER BY p.sort;
```

---

## 8. Spring Security RBAC实现

### 8.1 自定义UserDetails

```java
@Data
public class SecurityUser implements UserDetails {
    private Long id;
    private String username;
    private String password;
    private Boolean enabled;
    private Collection<SimpleGrantedAuthority> authorities;

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public boolean isAccountNonExpired() { return true; }

    @Override
    public boolean isAccountNonLocked() { return true; }

    @Override
    public boolean isCredentialsNonExpired() { return true; }

    @Override
    public boolean isEnabled() { return enabled; }
}
```

### 8.2 自定义UserDetailsService

```java
@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired private UserMapper userMapper;
    @Autowired private RoleMapper roleMapper;
    @Autowired private PermissionMapper permissionMapper;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // 1. 查询用户
        SysUser user = userMapper.selectByUsername(username);
        if (user == null) {
            throw new UsernameNotFoundException("用户不存在: " + username);
        }

        // 2. 查询角色
        List<SysRole> roles = roleMapper.selectByUserId(user.getId());
        // 角色编码加 ROLE_ 前缀（Spring Security约定）
        Set<SimpleGrantedAuthority> authorities = new HashSet<>();
        for (SysRole role : roles) {
            authorities.add(new SimpleGrantedAuthority("ROLE_" + role.getCode()));
        }

        // 3. 查询权限
        List<SysPermission> permissions = permissionMapper.selectByUserId(user.getId());
        for (SysPermission perm : permissions) {
            authorities.add(new SimpleGrantedAuthority(perm.getCode()));
        }

        // 4. 构建SecurityUser
        SecurityUser securityUser = new SecurityUser();
        securityUser.setId(user.getId());
        securityUser.setUsername(user.getUsername());
        securityUser.setPassword(user.getPassword());
        securityUser.setEnabled(user.getStatus() == 1);
        securityUser.setAuthorities(authorities);
        return securityUser;
    }
}
```

### 8.3 方法级权限控制

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    // 基于角色控制：只有管理员可以访问
    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping
    public Result listUsers() {
        return Result.success(userService.listAll());
    }

    // 基于权限编码控制
    @PreAuthorize("hasAuthority('user:create')")
    @PostMapping
    public Result createUser(@RequestBody UserDTO dto) {
        return Result.success(userService.create(dto));
    }

    // 组合条件：拥有user:update权限 OR 是管理员
    @PreAuthorize("hasAuthority('user:update') or hasRole('ADMIN')")
    @PutMapping("/{id}")
    public Result updateUser(@PathVariable Long id, @RequestBody UserDTO dto) {
        return Result.success(userService.update(id, dto));
    }

    // SpEL表达式：只能删除非管理员用户，且需要user:delete权限
    @PreAuthorize("hasAuthority('user:delete') and !#userDTO.admin")
    @DeleteMapping("/{id}")
    public Result deleteUser(@PathVariable Long id, @RequestBody UserDTO userDTO) {
        userService.delete(id);
        return Result.success();
    }
}
```

### 8.4 SecurityFilterChain配置

```java
@Configuration
@EnableMethodSecurity(prePostEnabled = true)  // 启用方法级注解
public class SecurityConfig {

    @Autowired private CustomUserDetailsService userDetailsService;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                // 公开接口
                .requestMatchers("/api/auth/login", "/api/auth/register").permitAll()
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                // 静态资源
                .requestMatchers("/static/**", "*.html", "*.css", "*.js").permitAll()
                // 角色控制
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/system/**").hasAnyRole("ADMIN", "SYS_OPERATOR")
                // 权限编码控制
                .requestMatchers(HttpMethod.GET, "/api/users/**").hasAuthority("user:read")
                .requestMatchers(HttpMethod.POST, "/api/users/**").hasAuthority("user:create")
                .requestMatchers(HttpMethod.PUT, "/api/users/**").hasAuthority("user:update")
                .requestMatchers(HttpMethod.DELETE, "/api/users/**").hasAuthority("user:delete")
                // 其余需要认证
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}
```

### 8.5 自定义权限校验

```java
@Component("permissionChecker")
public class PermissionChecker {

    @Autowired private PermissionService permissionService;

    /**
     * 检查当前用户是否拥有指定权限
     */
    public boolean check(String permissionCode) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return false;
        }
        return auth.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals(permissionCode));
    }

    /**
     * 检查当前用户是否拥有任意一个权限
     */
    public boolean checkAny(String... permissionCodes) {
        Set<String> codes = Set.of(permissionCodes);
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return auth.getAuthorities().stream()
                .anyMatch(a -> codes.contains(a.getAuthority()));
    }

    /**
     * 数据级权限：检查用户是否属于同一部门
     */
    public boolean checkDataScope(Long targetUserId) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        Long currentDeptId = userService.getDeptId(currentUserId);
        Long targetDeptId = userService.getDeptId(targetUserId);
        return currentDeptId.equals(targetDeptId);
    }
}

// 在控制器中使用
@RestController
public class OrderController {

    @PreAuthorize("@permissionChecker.check('order:export') and @permissionChecker.checkDataScope(#userId)")
    @GetMapping("/api/orders/export")
    public Result exportOrders(@RequestParam Long userId) {
        return Result.success(orderService.export(userId));
    }
}
```

---

## 9. 权限缓存方案

### 9.1 缓存策略

权限数据的特点：读多写少、一致性要求高（变更后需要及时生效）。常见缓存策略：

| 方案 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| **本地缓存** | Caffeine/Guava | 速度快、无网络开销 | 多节点不一致 |
| **分布式缓存** | Redis | 多节点共享、一致性好 | 有网络开销 |
| **多级缓存** | Caffeine + Redis | 兼顾速度与一致性 | 实现复杂 |
| **JWT内置** | Token中携带权限 | 无需查询 | 权限变更后需刷新Token |

### 9.2 Redis缓存实现

```java
@Service
public class PermissionCacheServiceImpl implements PermissionCacheService {

    @Autowired private StringRedisTemplate redisTemplate;

    private static final String PERMISSION_KEY = "user:permissions:";
    private static final String RO
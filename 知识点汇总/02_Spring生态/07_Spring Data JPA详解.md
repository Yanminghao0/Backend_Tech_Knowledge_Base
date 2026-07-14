# Spring Data JPA详解

> Repository/查询方法/Specification/JPA关系映射实战

---

## 📋 目录

1. [JPA概述](#1-jpa概述)
2. [实体映射](#2-实体映射)
3. [Repository查询](#3-repository查询)
4. [Specification动态查询](#4-specification动态查询)
5. [审计与分页](#5-审计与分页)
6. [面试题速查](#6-面试题速查)

---

## 1. JPA概述

```
JPA = Java Persistence API（Java持久化标准）
Hibernate = JPA的实现

Spring Data JPA = Spring对JPA的封装，简化Repository开发

  ┌────────────────────────────┐
  │     Spring Data JPA         │
  │  ├── Repository接口          │
  │  ├── 方法名查询              │
  │  ├── @Query注解查询          │
  │  └── Specification动态查询   │
  ├────────────────────────────┤
  │     JPA (Hibernate)         │
  │  ├── EntityManager          │
  │  ├── 实体生命周期            │
  │  └── 一级/二级缓存           │
  ├────────────────────────────┤
  │     JDBC                    │
  └────────────────────────────┘
```

---

## 2. 实体映射

```java
// 基本实体
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, length = 50)
    private String username;
    
    @Column(unique = true)
    private String email;
    
    @Enumerated(EnumType.STRING)
    private UserStatus status;
    
    @CreationTimestamp
    private LocalDateTime createTime;
    
    @UpdateTimestamp
    private LocalDateTime updateTime;
}

// 一对多关系
@Entity
public class Order {
    @Id @GeneratedValue
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;
    
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items = new ArrayList<>();
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "address_id")
    private Address shippingAddress;
}

// 多对多关系
@Entity
public class Role {
    @Id @GeneratedValue
    private Long id;
    
    @ManyToMany
    @JoinTable(
        name = "user_roles",
        joinColumns = @JoinColumn(name = "role_id"),
        inverseJoinColumns = @JoinColumn(name = "user_id")
    )
    private Set<User> users = new HashSet<>();
}
```

---

## 3. Repository查询

```java
// 1. 方法名查询（自动生成SQL）
public interface UserRepository extends JpaRepository<User, Long> {
    
    // 简单查询
    User findByUsername(String username);
    List<User> findByStatus(UserStatus status);
    
    // 多条件
    List<User> findByStatusAndAgeGreaterThan(UserStatus status, Integer age);
    
    // 排序
    List<User> findByStatusOrderByCreateTimeDesc(UserStatus status);
    
    // 去重
    List<User> findDistinctByEmailNotNull();
    
    // IN查询
    List<User> findByIdIn(List<Long> ids);
    
    // 模糊查询
    List<User> findByUsernameContaining(String keyword);
    
    // 范围查询
    List<User> findByCreateTimeBetween(LocalDateTime start, LocalDateTime end);
    
    // Top/Limit
    List<User> findTop10ByOrderByCreateTimeDesc();
}

// 2. @Query注解查询
public interface OrderRepository extends JpaRepository<Order, Long> {
    
    @Query("SELECT o FROM Order o WHERE o.user.id = :userId AND o.status = :status")
    List<Order> findByUserAndStatus(@Param("userId") Long userId, 
                                     @Param("status") OrderStatus status);
    
    // 原生SQL
    @Query(value = "SELECT * FROM orders WHERE amount > :amount", nativeQuery = true)
    List<Order> findByAmountGreaterThan(@Param("amount") BigDecimal amount);
    
    // 聚合查询
    @Query("SELECT COUNT(o) FROM Order o WHERE o.user.id = :userId")
    Long countByUserId(@Param("userId") Long userId);
    
    // 更新操作
    @Modifying
    @Query("UPDATE User u SET u.status = :status WHERE u.id = :id")
    int updateStatus(@Param("id") Long id, @Param("status") UserStatus status);
    
    // 投影查询（只查部分字段）
    @Query("SELECT new com.example.dto.UserDTO(u.id, u.username, u.email) FROM User u WHERE u.status = :status")
    List<UserDTO> findDTOByStatus(@Param("status") UserStatus status);
}
```

---

## 4. Specification动态查询

```java
// Specification用于动态条件查询
public class UserSpec {
    
    public static Specification<User> hasStatus(UserStatus status) {
        return (root, query, cb) -> status == null ? null : cb.equal(root.get("status"), status);
    }
    
    public static Specification<User> usernameLike(String keyword) {
        return (root, query, cb) -> 
            StringUtils.isEmpty(keyword) ? null : cb.like(root.get("username"), "%" + keyword + "%");
    }
    
    public static Specification<User> ageBetween(Integer min, Integer max) {
        return (root, query, cb) -> {
            if (min == null && max == null) return null;
            if (min == null) return cb.lessThanOrEqualTo(root.get("age"), max);
            if (max == null) return cb.greaterThanOrEqualTo(root.get("age"), min);
            return cb.between(root.get("age"), min, max);
        };
    }
}

// 使用
@Service
public class UserQueryService {
    @Autowired
    private UserRepository userRepository;
    
    public Page<User> search(UserSearchRequest req, Pageable pageable) {
        return userRepository.findAll(
            Specification.where(UserSpec.hasStatus(req.getStatus()))
                .and(UserSpec.usernameLike(req.getKeyword()))
                .and(UserSpec.ageBetween(req.getMinAge(), req.getMaxAge())),
            pageable
        );
    }
}
```

---

## 5. 审计与分页

```java
// 审计配置（自动填充创建/更新时间）
@EntityListeners(AuditingEntityListener.class)
@MappedSuperclass
public abstract class BaseEntity {
    @CreatedBy
    private String createdBy;
    
    @CreatedDate
    private LocalDateTime createTime;
    
    @LastModifiedBy
    private String updatedBy;
    
    @LastModifiedDate
    private LocalDateTime updateTime;
}

// 分页查询
Pageable pageable = PageRequest.of(0, 20, Sort.by("createTime").descending());
Page<User> page = userRepository.findByStatus(UserStatus.ACTIVE, pageable);

page.getContent();       // 当前页数据
page.getTotalElements(); // 总记录数
page.getTotalPages();    // 总页数
page.hasNext();          // 是否有下一页
```

---

## 6. 面试题速查

**Q1: JPA和MyBatis的区别？**
```
JPA：ORM框架，面向对象操作，自动生成SQL，跨数据库
MyBatis：半ORM，手写SQL，灵活控制SQL，性能可控
JPA适合简单CRUD+标准SQL，MyBatis适合复杂查询
```

**Q2: fetch = LAZY和EAGER的区别？**
```
EAGER：立即加载，查Order时同时查关联的User
LAZY：懒加载，用到User时才查（推荐）
LAZY需要事务内使用，否则LazyInitializationException
```

**Q3: N+1问题怎么解决？**
```
问题：查N个Order，每个Order查一次User → N+1次SQL
解决：
1. @EntityGraph指定fetch的字段
2. @Query("JOIN FETCH o.user")
3. 批量fetch（@BatchSize）
```

**Q4: Specification的作用？**
```
动态条件查询：根据不同参数组合不同的查询条件
避免拼接JPQL字符串，类型安全，可组合
```

---

*最后更新：2026-07-13*

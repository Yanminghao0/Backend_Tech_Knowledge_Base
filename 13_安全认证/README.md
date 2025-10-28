# 13_安全认证

> 企业级应用安全认证授权技术体系

---

## 📚 本目录包含

### 核心文档
1. **Spring Security与JWT实战** ⭐⭐⭐⭐⭐
   - 认证授权完整解决方案
   - JWT实战与最佳实践
   - OAuth2.0与第三方登录
   - RBAC权限模型
   - 单点登录（SSO）

---

## 🎯 学习路径

### 第一步：理解基础概念
- 认证（Authentication）vs 授权（Authorization）
- Session vs Token
- Cookie vs JWT

### 第二步：掌握Spring Security
- 核心架构
- 认证流程
- 权限控制

### 第三步：JWT实战
- JWT结构与原理
- Token生成与验证
- 刷新Token机制

### 第四步：RBAC权限设计
- 用户-角色-权限模型
- 数据库设计
- 动态权限控制

### 第五步：OAuth2.0
- 授权码模式
- 第三方登录
- 实战集成

### 第六步：安全最佳实践
- 密码加密
- XSS/CSRF防护
- SQL注入防护
- Token安全

---

## 🔥 面试高频考点

### 必考题（⭐⭐⭐⭐⭐）
1. **Spring Security认证流程**
   - FilterChain工作原理
   - SecurityContext如何存储用户信息
   - 认证与授权的区别

2. **JWT vs Session**
   - 各自的优缺点
   - 适用场景
   - 如何选择

3. **如何防止Token被盗用**
   - HTTPS传输
   - Token过期时间
   - 刷新Token机制
   - IP绑定

4. **RBAC权限模型**
   - 数据库表设计
   - 如何实现动态权限
   - 如何实现数据权限

5. **OAuth2.0授权码模式流程**
   - 各个步骤的作用
   - 为什么需要授权码
   - 与密码模式的区别

### 高频题（⭐⭐⭐⭐）
- JWT的结构（Header、Payload、Signature）
- 如何防止CSRF攻击
- 密码加密算法选择（BCrypt原理）
- 单点登录实现方案
- Token刷新策略

---

## 💡 实战建议

### 1. 从简单到复杂
```
第一阶段：基础认证
- 用户名密码登录
- Session管理
- 基础权限控制

第二阶段：Token认证
- JWT集成
- 前后端分离
- Token刷新

第三阶段：高级功能
- OAuth2.0第三方登录
- RBAC动态权限
- 单点登录

第四阶段：安全加固
- 密码加密
- XSS/CSRF防护
- 接口加密
```

### 2. 必做实战项目
- ✅ 完整的登录注册系统（用户名密码 + 手机验证码）
- ✅ JWT认证的前后端分离项目
- ✅ 微信/GitHub第三方登录
- ✅ 权限管理系统（动态菜单、按钮权限）

### 3. 常见坑点
- Token存储位置（localStorage vs sessionStorage vs cookie）
- Token刷新时机（何时刷新、如何刷新）
- 权限粒度设计（过粗vs过细）
- 密码加密算法选择（不要用MD5）

---

## 🛠️ 技术栈

### 核心框架
- Spring Security 5.x
- JWT（JJWT库）
- Spring Boot 2.x/3.x

### 常用工具
- BCrypt（密码加密）
- Hutool（工具类）
- Redis（Token存储）
- Nacos（配置中心）

### OAuth2.0客户端
- 微信开放平台
- GitHub OAuth
- 支付宝授权

---

## 📖 推荐学习资源

### 官方文档
- [Spring Security官方文档](https://spring.io/projects/spring-security)
- [JWT官网](https://jwt.io/)
- [OAuth2.0 RFC](https://oauth.net/2/)

### 开源项目
- [Jeecg-boot](https://github.com/jeecgboot/jeecg-boot) - 企业级快速开发平台
- [RuoYi-Vue](https://github.com/yangzongzhuan/RuoYi-Vue) - 权限管理系统
- [Spring Security官方示例](https://github.com/spring-projects/spring-security-samples)

---

## 🎯 学习成果检验

完成本目录学习后，你应该能够：
- ✅ 独立搭建Spring Security + JWT认证系统
- ✅ 设计并实现RBAC权限模型
- ✅ 集成OAuth2.0第三方登录
- ✅ 理解并实现单点登录（SSO）
- ✅ 掌握常见安全漏洞及防护措施
- ✅ 回答所有面试相关问题

---

## 📝 文档更新日志

### v1.0（2025-10-27）
- ✅ 创建安全认证目录
- ✅ 添加Spring Security与JWT实战文档框架
- 🔄 内容丰富中...

---

*建议学习时间：1-2周*  
*难度等级：⭐⭐⭐⭐*  
*重要程度：⭐⭐⭐⭐⭐（企业级应用必备）*


# 代码质量与SonarQube

> 静态代码分析、质量门禁与技术债量化管理

---

## 📋 目录

1. [SonarQube概述](#1-sonarqube概述)
2. [质量维度](#2-质量维度)
3. [安装与配置](#3-安装与配置)
4. [规则配置](#4-规则配置)
5. [CI集成与质量门禁](#5-ci集成与质量门禁)
6. [面试题速查](#6-面试题速查)

---

## 1. SonarQube概述

```
SonarQube = 持续代码质量检测平台

  ┌──────────┐     扫描      ┌──────────────┐
  │  代码仓库  │ ───────────→ │  SonarScanner │
  └──────────┘               └──────┬───────┘
                                     │ 上报结果
  ┌──────────────────────────────────▼─────────┐
  │              SonarQube Server                │
  │  ├── Bug检测（空指针/资源泄漏/SQL注入）       │
  │  ├── 漏洞检测（硬编码密码/XSS/CSRF）          │
  │  ├── Code Smell（重复代码/复杂度/命名）       │
  │  ├── 覆盖率（单元测试覆盖率）                 │
  │  └── 技术债（量化估算修复时间）               │
  └─────────────────────────────────────────────┘
```

---

## 2. 质量维度

| 维度 | 说明 | 示例 |
|------|------|------|
| Reliability (可靠性) | Bug：可能导致运行时错误 | 空指针、资源泄漏 |
| Security (安全性) | 漏洞：可能被利用的安全问题 | SQL注入、硬编码密码 |
| Security Hotspots | 安全敏感代码，需人工审查 | 加密算法选择、日志中的敏感信息 |
| Maintainability (可维护性) | Code Smell：影响可读性/可维护性 | 重复代码、圈复杂度过高 |
| Coverage (覆盖率) | 单元测试覆盖比例 | 行覆盖/分支覆盖 |
| Duplications (重复) | 重复代码块 | 相同逻辑出现在多处 |

```
质量等级：
  A: 0 Bug, 0 漏洞, ≤5% 重复率, 覆盖率≥80%
  B: 轻微问题
  C: 中等问题
  D: 较严重问题
  E: 严重问题
```

---

## 3. 安装与配置

```bash
# Docker Compose安装
version: "3"
services:
  sonarqube:
    image: sonarqube:latest
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://db:5432/sonar
      - SONAR_JDBC_USERNAME=sonar
      - SONAR_JDBC_PASSWORD=sonar
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=sonar
      - POSTGRES_PASSWORD=sonar
      - POSTGRES_DB=sonar
```

```xml
<!-- Maven配置 -->
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.11</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals><goal>report</goal></goals>
        </execution>
    </executions>
</plugin>
```

---

## 4. 规则配置

```
SonarQube内置规则集：
  - 阿里巴巴Java开发规范（P3C）
  - OWASP Top 10安全规则
  - CERT安全编码标准
  - 自定义规则

关键规则示例：
  - 空指针解引用（Blocker）
  - 资源未关闭（Critical）
  - SQL拼接（Critical）
  - 硬编码密码（Critical）
  - 圈复杂度>15（Major）
  - 方法超过50行（Minor）
  - 重复代码>30行（Major）
```

---

## 5. CI集成与质量门禁

```yaml
# GitLab CI集成
sonarqube-check:
  stage: test
  image: maven:3.8-openjdk-17
  script:
    - mvn verify sonar:sonar
        -Dsonar.projectKey=my-project
        -Dsonar.host.url=http://sonarqube:9000
        -Dsonar.login=$SONAR_TOKEN
        -Dsonar.qualitygate.wait=true  # 等待质量门禁结果
  only:
    - merge_requests
    - main
```

```
质量门禁（Quality Gate）配置：
  ┌────────────────────────────────────┐
  │         Quality Gate: Default       │
  ├────────────────────────────────────┤
  │  ✅ 新代码Bug数 = 0                  │
  │  ✅ 新代码漏洞数 = 0                 │
  │  ✅ 新代码Hotspot审查率 ≥ 80%       │
  │  ✅ 新代码覆盖率 ≥ 80%              │
  │  ✅ 新代码重复率 ≤ 3%               │
  │  ✅ 新代码Code Smell数 = 0          │
  └────────────────────────────────────┘
  
  门禁不通过 → CI流水线失败 → 阻止合并
```

---

## 6. 面试题速查

**Q1: SonarQube检测哪些维度？**
```
6大维度：Bug(可靠性)、漏洞(安全性)、安全热点、Code Smell(可维护性)、覆盖率、重复代码
```

**Q2: 质量门禁的作用？**
```
在CI流水线中设置质量门槛，不达标则阻止代码合并
新代码Bug=0、覆盖率≥80%、重复率≤3%
强制质量保障，防止技术债增长
```

**Q3: Code Smell是什么？**
```
不影响正确性但影响可维护性的代码问题：
- 圈复杂度过高
- 方法/类过长
- 重复代码
- 命名不规范
- 魔法数字
```

---

*最后更新：2026-07-13*

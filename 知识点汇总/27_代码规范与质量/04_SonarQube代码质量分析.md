# SonarQube代码质量分析

> SonarQube 是业界最流行的持续代码质量检查平台，覆盖了代码缺陷、安全漏洞、代码异味和技术债等多个维度。本文系统介绍 SonarQube 的规则配置、问题分类、CI集成和质量门禁机制。

---

## 📋 目录

1. [SonarQube架构概述](#1-sonarqube架构概述)
2. [规则配置](#2-规则配置)
3. [Bug检测](#3-bug检测)
4. [漏洞分析](#4-漏洞分析)
5. [Code Smell识别](#5-code-smell识别)
6. [技术债管理](#6-技术债管理)
7. [CI集成](#7-ci集成)
8. [质量门禁](#8-质量门禁)
9. [面试题速查](#9-面试题速查)

---

## 1. SonarQube架构概述

### 1.1 核心组件

```
┌──────────────────────────────────────────────────────────┐
│                    SonarQube Platform                     │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Web Server  │  │ Search      │  │ Compute     │      │
│  │  (UI/API)    │  │ Server      │  │ Engine      │      │
│  │              │  │ (Elastic    │  │ (Report     │      │
│  │  - Dashboard │  │  Search)    │  │  processing)│      │
│  │  - Rule Mgmt │  │             │  │             │      │
│  │  - Profile   │  └─────────────┘  └─────────────┘      │
│  │    Mgmt      │                                         │
│  └─────────────┘                                         │
│         │                                                 │
│         ▼                                                 │
│  ┌─────────────────────────────────────────────────┐     │
│  │            Database (PostgreSQL/MySQL)           │     │
│  │  - Rules, Profiles, Projects                     │     │
│  │  - Issues, Measures, Quality Gates               │     │
│  └─────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
         ▲
         │ HTTP (WebSocket API)
         │
┌────────┴────────┐
│  SonarScanner    │  ← 在CI/CD流水线中运行
│  (代码分析器)    │     分析代码并上传结果
└─────────────────┘
```

### 1.2 分析流程

```yaml
# SonarQube分析流程
1. SonarScanner获取源代码
2. 静态分析：
   - 语法分析：构建AST（抽象语法树）
   - 语义分析：类型检查、符号解析
   - 规则匹配：逐条规则检查
3. 覆盖率数据导入：
   - 读取JaCoCo/Cobertura报告
   - 计算行覆盖/分支覆盖
4. 复杂度计算：
   - 圈复杂度（Cyclomatic Complexity）
   - 认知复杂度（Cognitive Complexity）
5. 重复代码检测：
   - Token-based块匹配
6. 结果上传到SonarQube Server
7. Compute Engine处理报告
8. 更新Dashboard和Quality Gate状态
```

### 1.3 多语言支持

```properties
# SonarQube支持的主要语言
# Java        → SonarJava
# JavaScript  → SonarJS
# Python      → SonarPython
# Go          → SonarGo
# C/C++       → SonarCFamily
# C#          → SonarC#
# Kotlin      → SonarKotlin
# PHP         → SonarPHP
# Ruby        → SonarRuby
# TypeScript  → SonarTS

# 每种语言有独立的规则集和Analyzer
# Quality Profile按语言配置
```

---

## 2. 规则配置

### 2.1 规则体系

```yaml
# SonarQube规则分类
规则类型:
  Bug:           # 代码缺陷——可能导致程序错误的行为
    - 空指针风险
    - 资源泄漏
    - 并发问题
    - 逻辑错误
  
  Vulnerability: # 安全漏洞——可能被攻击者利用的安全问题
    - SQL注入
    - XSS
    - 硬编码密码
    - 不安全的加密
  
  Code Smell:    # 代码异味——影响可维护性的代码设计问题
    - 过长方法
    - 重复代码
    - 过多参数
    - 深层嵌套
  
  Hotspot:       # 安全热点——需要人工审查的安全相关代码
    - 加密使用
    - 权限检查
    - 外部输入处理

严重级别:
  Blocker:       # 阻断级——最严重，必须立即修复
  Critical:      # 关键级——高概率导致Bug或安全问题
  Major:         # 主要级——影响质量但不紧急
  Minor:         # 次要级——轻微问题
  Info:          # 提示级——信息性建议
```

### 2.2 Quality Profile配置

```xml
<!-- SonarQube Quality Profile示例：自定义Java规则集 -->
<?xml version="1.0" encoding="UTF-8"?>
<profile>
    <name>Company Java Rules</name>
    <language>java</language>
    
    <rules>
        <!-- 强制规则：必须遵守 -->
        <rule>
            <key>java:S2259</key>  <!-- NullPointerException -->
            <priority>BLOCKER</priority>
        </rule>
        
        <rule>
            <key>java:S2095</key>  <!-- 资源应被关闭 -->
            <priority>CRITICAL</priority>
        </rule>
        
        <!-- 安全规则 -->
        <rule>
            <key>java:S2077</key>  <!-- SQL注入 -->
            <priority>BLOCKER</priority>
        </rule>
        
        <rule>
            <key>java:S2068</key>  <!-- 硬编码密码 -->
            <priority>CRITICAL</priority>
        </rule>
        
        <!-- 代码质量规则 -->
        <rule>
            <key>java:S138</key>  <!-- 方法不超过75行 -->
            <priority>MAJOR</priority>
            <parameters>
                <parameter>
                    <key>max</key>
                    <value>75</value>
                </parameter>
            </parameters>
        </rule>
        
        <rule>
            <key>java:S134</key>  <!-- 嵌套不超过4层 -->
            <priority>MAJOR</priority>
        </rule>
        
        <rule>
            <key>java:S00107</key>  <!-- 参数不超过7个 -->
            <priority>MAJOR</priority>
        </rule>
    </rules>
</profile>
```

### 2.3 规则自定义

```java
// 自定义规则示例（Java）
// 继承SonarJava的Rule基类
@Rule(
    key = "CustomLogInjectionCheck",
    name = "日志注入检查",
    description = "不应将未清洗的用户输入直接写入日志",
    priority = Priority.CRITICAL,
    tags = {"security", "cert"}
)
public class LogInjectionCheck extends IssuableSubscriptionVisitor {
    
    @Override
    public List<Tree.Kind> nodesToVisit() {
        return ImmutableList.of(Tree.Kind.METHOD_INVOCATION);
    }
    
    @Override
    public void visitNode(Tree tree) {
        MethodInvocationTree methodInvocation = (MethodInvocationTree) tree;
        
        // 检查是否是日志方法调用
        if (isLogMethod(methodInvocation)) {
            // 检查参数是否来自用户输入
            for (ExpressionTree argument : methodInvocation.arguments()) {
                if (isUserInput(argument)) {
                    reportIssue(argument, 
                        "用户输入直接写入日志可能导致日志注入，请进行清洗");
                }
            }
        }
    }
    
    private boolean isLogMethod(MethodInvocationTree method) {
        String methodName = method.symbol().name();
        return Set.of("info", "debug", "warn", "error").contains(methodName);
    }
}
```

---

## 3. Bug检测

### 3.1 常见Bug规则

```java
// 规则 java:S2259 - NullPointerException风险
// ❌ SonarQube会报Bug
public String getUserName(User user) {
    return user.getName().trim();  // user可能为null
}

// ✅ 添加null检查
public String getUserName(User user) {
    if (user == null) {
        return "";
    }
    return user.getName().trim();
}

// 规则 java:S2095 - 资源应被关闭
// ❌ SonarQube会报Bug
public String readFile(String path) throws IOException {
    FileInputStream fis = new FileInputStream(path);  // 未关闭
    InputStreamReader reader = new InputStreamReader(fis);
    return reader.toString();
}

// ✅ try-with-resources
public String readFile(String path) throws IOException {
    try (FileInputStream fis = new FileInputStream(path);
         InputStreamReader reader = new InputStreamReader(fis)) {
        // ...
    }
}

// 规则 java:S2589 - 条件始终为true/false
// ❌ SonarQube会报Bug
public void process(Order order) {
    if (order != null) {
        if (order == null) {  // 这个条件永远为false
            // dead code
        }
        order.process();
    }
}

// 规则 java:S2755 - XML外部实体注入(XXE)
// ❌ SonarQube会报Bug
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
DocumentBuilder builder = factory.newDocumentBuilder();  // 未禁用XXE
Document doc = builder.parse(input);

// ✅ 禁用XXE
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
DocumentBuilder builder = factory.newDocumentBuilder();
```

### 3.2 并发Bug

```java
// 规则 java:S2445 - synchronized锁对象不一致
// ❌ SonarQube会报Bug
public class Cache {
    private Map<String, String> data = new HashMap<>();
    
    public synchronized void put(String key, String value) {
        data.put(key, value);  // 锁的是this
    }
    
    public void putAll(Map<String, String> entries) {
        synchronized (data) {  // 锁的是data对象，与put方法不一致
            data.putAll(entries);
        }
    }
}

// ✅ 统一锁对象
public class Cache {
    private final Map<String, String> data = new ConcurrentHashMap<>();
    
    public void put(String key, String value) {
        data.put(key, value);
    }
    
    public void putAll(Map<String, String> entries) {
        data.putAll(entries);
    }
}

// 规则 java:S3077 - 非线程安全的字段未正确同步
// ❌
public class Counter {
    private static int count = 0;  // 多线程下不安全
    
    public static void increment() {
        count++;
    }
}

// ✅ 使用AtomicInteger
public class Counter {
    private static final AtomicInteger count = new AtomicInteger(0);
    
    public static void increment() {
        count.incrementAndGet();
    }
}
```

### 3.3 资源泄漏检测

```java
// SonarQube能追踪资源生命周期
// ❌ 资源泄漏Bug
public List<String> readLines(String path) {
    BufferedReader reader = null;
    try {
        reader = new BufferedReader(new FileReader(path));
        List<String> lines = new ArrayList<>();
        String line;
        while ((line = reader.readLine()) != null) {
            lines.add(line);
        }
        return lines;
    } catch (IOException e) {
        throw new RuntimeException(e);
        // 这里return/throw后，reader不会被关闭
    }
    // 缺少finally块关闭reader
}

// SonarQube还会检测以下泄漏模式：
// 1. 方法返回前未关闭的流
// 2. 异常路径中的资源泄漏
// 3. 数据库连接未关闭
// 4. 线程池未关闭
```

---

## 4. 漏洞分析

### 4.1 安全漏洞规则

```java
// 规则 java:S2077 - SQL注入
// ❌ Vulnerability
@Query("SELECT * FROM users WHERE email = '" + email + "'")
User findByEmail(String email);

String query = "SELECT * FROM products WHERE name LIKE '%" + keyword + "%'";
jdbcTemplate.queryForList(query);

// ✅ 参数化查询
@Query("SELECT * FROM users WHERE email = :email")
User findByEmail(@Param("email") String email);

jdbcTemplate.queryForList(
    "SELECT * FROM products WHERE name LIKE ?", 
    "%" + keyword + "%"
);

// 规则 java:S2068 - 硬编码密码
// ❌ Vulnerability
private String dbPassword = "MyP@ssw0rd123";  // 硬编码
private String apiKey = "sk-abc123xyz";        // 硬编码API密钥

// ✅ 从配置或环境变量读取
@Value("${db.password}")
private String dbPassword;

@Value("${api.key}")
private String apiKey;

// 或使用Vault/KMS等密钥管理服务
// 规则 java:S4830 - 证书验证不充分
// ❌ Vulnerability
TrustManager[] trustAll = new TrustManager[] {
    new X509TrustManager() {
        public void checkClientTrusted(X509Certificate[] chain, String authType) {}
        public void checkServerTrusted(X509Certificate[] chain, String authType) {}
        public X509Certificate[] getAcceptedIssuers() { return new X509Certificate[0]; }
    }
};
SSLContext sc = SSLContext.getInstance("TLS");
sc.init(null, trustAll, new SecureRandom());  // 信任所有证书

// 规则 java:S4426 - 弱加密算法
// ❌ Vulnerability
Cipher cipher = Cipher.getInstance("DES");       // DES已不安全
MessageDigest md = MessageDigest.getInstance("MD5");  // MD5不安全
KeyGenerator kg = KeyGenerator.getInstance("AES");
kg.init(56);  // AES密钥太短

// ✅ 使用安全算法
Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
MessageDigest md = MessageDigest.getInstance("SHA-256");
KeyGenerator kg = KeyGenerator.getInstance("AES");
kg.init(256);  // 至少256位
```

### 4.2 安全热点

```java
// Security Hotspot需要人工审查——代码本身不一定是漏洞，但需要确认
// 常见Hotspot类型：

// 1. 命令执行
Process process = Runtime.getRuntime().exec(userInput);  // 需确认输入是否受控

// 2. 文件操作
new FileReader(userProvidedPath);  // 需确认路径是否校验

// 3. 反序列化
ObjectInputStream ois = new ObjectInputStream(inputStream);
Object obj = ois.readObject();  // 需确认数据来源是否可信

// 4. 随机数
Random random = new Random();  // 非加密安全，用于安全场景需用SecureRandom
String token = String.valueOf(random.nextInt());  // 弱Token

// 5. 重定向
response.sendRedirect(userInput);  // 开放重定向风险

// Hotspot审查流程：
// 1. 标记为"Review"——自动分配给开发者审查
// 2. 审查后标记为"Safe"或"Fixed"
// 3. 质量门禁可以要求0个未审查的Hotspot
```

---

## 5. Code Smell识别

### 5.1 可维护性问题

```java
// 规则 java:S138 - 方法过长
// ❌ Code Smell (Major)
public void processOrder(Order order) {
    // ... 200行代码 ...
    // SonarQube报告：方法过长，最大75行，实际200行
}
// 重构建议：提取方法，分解为多个小方法

// 规则 java:S134 - 嵌套层次过深
// ❌ Code Smell (Major)
public void processData(Data data) {
    if (data != null) {
        if (data.isValid()) {
            if (data.getType() == TYPE_A) {
                if (data.getPriority() > 5) {
                    if (data.getStatus() == ACTIVE) {  // 5层嵌套
                        // ...
                    }
                }
            }
        }
    }
}
// 重构建议：提前返回（guard clause）、提取方法

// 规则 java:S00107 - 参数过多
// ❌ Code Smell (Major)
public void createUser(String name, String email, String phone, 
    int age, String department, String role, String password, 
    boolean active, boolean sendEmail) {  // 9个参数
}
// 重构建议：使用参数对象

// 规则 java:S1192 - 字面量重复
// ❌ Code Smell (Minor)
public void process() {
    if ("PENDING".equals(status)) { ... }
    if ("PENDING".equals(oldStatus)) { ... }
    log.info("Status changed from PENDING to {}", status);
    // "PENDING"出现3次以上
}
// 重构建议：提取为常量
private static final String STATUS_PENDING = "PENDING";
```

### 5.2 复杂度分析

```java
// 圈复杂度（Cyclomatic Complexity）
// SonarQube对方法的圈复杂度阈值：
// 1-10: 简单，风险低
// 11-20: 允许，风险适中
// 21-50: 复杂，高风险
// 50+: 极复杂，必须重构

// ❌ 高圈复杂度
public double calculateShipping(Order order) {  // CC=15
    double cost = 0;
    if (order.isExpress()) {
        if (order.getWeight() > 10) {
            if (order.isInternational()) {
                cost = 50;
            } else {
                cost = 30;
            }
        } else {
            if (order.isInternational()) {
                cost = 25;
            } else {
                cost = 15;
            }
        }
    } else {
        if (order.getWeight() > 10) {
            if (order.isInternational()) {
                cost = 30;
            } else {
                cost = 20;
            }
        } else {
            if (order.isInternational()) {
                cost = 15;
            } else {
                cost = 10;
            }
        }
    }
    if (order.hasInsurance()) {
        cost += order.getAmount() * 0.05;
    }
    if (order.isMember()) {
        cost *= 0.9;
    }
    return cost;
}

// ✅ 重构后——使用策略表
private static final Map<ShippingKey, Double> SHIPPING_RATES = Map.of(
    new ShippingKey(true, true, true), 50.0,
    new ShippingKey(true, true, false), 30.0,
    new ShippingKey(true, false, true), 25.0,
    new ShippingKey(true, false, false), 15.0,
    new ShippingKey(false, true, true), 30.0,
    new ShippingKey(false, true, false), 20.0,
    new ShippingKey(false, false, true), 15.0,
    new ShippingKey(false, false, false), 10.0
);

public double calculateShipping(Order order) {  // CC=3
    double baseCost = SHIPPING_RATES.getOrDefault(
        new ShippingKey(order.isExpress(), order.getWeight() > 10, 
                        order.isInternational()),
        10.0
    );
    double cost = applyInsurance(baseCost, order);
    return applyMemberDiscount(cost, order);
}
```

---

## 6. 技术债管理

### 6.1 技术债计算

```
SonarQube技术债计算公式：
技术债时间 = Σ(每个Issue的修复时间)

修复时间估算：
  Blocker Bug:     1小时
  Critical Bug:    30分钟
  Major Bug:       20分钟
  Minor Bug:       10分钟
  Code Smell:      根据规则类型预估
    - 方法过长:    30分钟
    - 重复代码:    1小时
    - 命名问题:    5分钟
  
技术债比率 = 技术债时间 / 开发时间
  < 5%:   A级（优秀）
  5-10%:  B级（良好）
  10-20%: C级（一般）
  20-50%: D级（较差）
  > 50%:  E级（很差）
```

### 6.2 技术债可视化

```yaml
# SonarQube技术债Dashboard展示
整体视图:
  - 技术债总量: 125天
  - 技术债比率: 12.5% (C级)
  - 新代码技术债: 2天 (A级)

分类视图:
  Bug技术债:      45天 (36%)
  Code Smell技术债: 60天 (48%)
  漏洞技术债:      20天 (16%)

趋势视图:
  - 30天技术债变化趋势
  - 新增vs修复速率
  - 各模块技术债分布

# 技术债管理策略
策略1 - 新代码零债务:
  - 新增代码必须通过质量门禁
  - 不允许引入新的Blocker/Critical问题
  
策略2 - 逐步偿还旧债:
  - 每个Sprint分配10-20%时间偿还技术债
  - 优先修复高频修改文件中的问题
  - 使用"Boy Scout Rule"——每次修改让代码比之前更好
```

---

## 7. CI集成

### 7.1 Maven集成

```xml
<!-- pom.xml 中配置SonarScanner -->
<build>
    <plugins>
        <plugin>
            <groupId>org.jacoco</groupId>
            <artifactId>jacoco-maven-plugin</artifactId>
            <version>0.8.11</version>
            <executions>
                <execution>
                    <goals>
                        <goal>prepare-agent</goal>
                    </goals>
                </execution>
                <execution>
                    <id>report</id>
                    <phase>test</phase>
                    <goals>
                        <goal>report</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
        <plugin>
            <groupId>org.sonarsource.scanner.maven</groupId>
            <artifactId>sonar-maven-plugin</artifactId>
            <version>3.10.0</version>
        </plugin>
    </plugins>
</build>

<!-- 执行命令 -->
<!-- mvn clean verify sonar:sonar \
     -Dsonar.projectKey=my-project \
     -Dsonar.projectName="My Project" \
     -Dsonar.host.url=http://sonarqube.company.com \
     -Dsonar.login=your-token -->
```

### 7.2 GitLab CI集成

```yaml
# .gitlab-ci.yml
stages:
  - test
  - quality
  - deploy

sonarqube-analysis:
  stage: quality
  image: maven:3.9-eclipse-temurin-17
  variables:
    SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar"
    GIT_DEPTH: "0"
  cache:
    key: "${CI_JOB_NAME}"
    paths:
      - .sonar/cache
  script:
    - mvn verify sonar:sonar
        -Dsonar.projectKey=$CI_PROJECT_PATH
        -Dsonar.projectName=$CI_PROJECT_TITLE
        -Dsonar.host.url=$SONAR_HOST_URL
        -Dsonar.login=$SONAR_TOKEN
        -Dsonar.branch.name=$CI_COMMIT_REF_NAME
        -Dsonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

sonar-quality-gate:
  stage: quality
  image: maven:3.9-eclipse-temurin-17
  needs: ["sonarqube-analysis"]
  script:
    - |
      # 等待分析完成并检查质量门禁
      QUALITY_GATE_STATUS=$(curl -s -u $SONAR_TOKEN: \
        "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$CI_PROJECT_PATH&branch=$CI_COMMIT_REF_NAME" \
        | jq -r '.projectStatus.status')
      
      echo "Quality Gate Status: $QUALITY_GATE_STATUS"
      
      if [ "$QUALITY_GATE_STATUS" != "OK" ]; then
        echo "❌ 质量门禁未通过！"
        exit 1
      fi
      echo "✅ 质量门禁通过！"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### 7.3 GitHub Actions集成

```yaml
# .github/workflows/sonarqube.yml
name: SonarQube Analysis
on:
  push:
    branches: [main, develop]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # SonarQube需要完整历史用于blame分析
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
      
      - name: Cache SonarQube packages
        uses: actions/cache@v3
        with:
          path: ~/.sonar/cache
          key: ${{ runner.os }}-sonar
          restore-keys: ${{ runner.os }}-sonar
      
      - name: Cache Maven packages
        uses: actions/cache@v3
        with:
          path: ~/.m2
          key: ${{ runner.os }}-m2-${{ hashFiles('**/pom.xml') }}
      
      - name: Build and analyze
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        run: |
          mvn -B verify org.jacoco:jacoco-maven-plugin:report \
            org.sonarsource.scanner.maven:sonar-maven-plugin:sonar \
            -Dsonar.projectKey=com.company:my-project \
            -Dsonar.host.url=${{ secrets.SONAR_HOST_URL }} \
            -Dsonar.login=${{ secrets.SONAR_TOKEN }}
      
      - name: Check Quality Gate
        id: sonarqube-quality-gate
        uses: SonarSource/sonarqube-quality-gate-action@master
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          scan-metadata-report-path: target/sonar/report-task.txt
```

---

## 8. 质量门禁

### 8.1 质量门禁配置

```yaml
# SonarQube Quality Gate配置
# 路径: Quality Gates → Create

# 新代码质量门禁（推荐配置）
name: "Company Quality Gate"

conditions:
  # 1. 新Bug: 0个
  - metric: new_bugs
    operator: GREATER_THAN
    error_threshold: 0
    
  # 2. 新漏洞: 0个
  - metric: new_vulnerabilities
    operator: GREATER_THAN
    error_threshold: 0
    
  # 3. 新Code Smell: 不超过5个
  - metric: new_code_smells
    operator: GREATER_THAN
    error_threshold: 5
    
  # 4. 新代码覆盖率: >= 80%
  - metric: new_coverage
    operator: LESS_THAN
    error_threshold: 80
    
  # 5. 新代码重复率: <= 3%
  - metric: new_duplicated_lines_density
    operator: GREATER_THAN
    error_threshold: 3
    
  # 6. 新代码安全热点审查率: 100%
  - metric: new_security_hotspots_reviewed
    operator: LESS_THAN
    error_threshold: 100
    
  # 7. 新代码技术债比率: <= 5%
  - metric: new_technical_debt_ratio
    operator: GREATER_THAN
    error_threshold: 5
```

### 8.2 分支策略

```yaml
# SonarQube分支分析策略

# 主分支(main/master):
# - 每次push触发全量分析
# - 整体代码和新代码都检查
# - 质量门禁必须通过

# 开发分支(develop):
# - 每次push触发增量分析
# - 主要关注新代码
# - 质量门禁必须通过

# 功能分支(feature/*):
# - PR创建时触发分析
# - 仅分析PR中变更的代码
# - 在PR上展示质量门禁状态
# - 不通过则阻止合并

# 配置（sonar-project.properties）:
sonar.projectKey=com.company:my-project
sonar.projectName=My Project
sonar.sources=src/main/java
sonar.tests=src/test/java
sonar.java.binaries=target/classes
sonar.java.test.binaries=target/test-classes
sonar.coverage.jacoco.xmlReportPaths=target/site/jacoco/jacoco.xml
sonar.exclusions=**/generated/**,**/dto/**,**/entity/**
sonar.coverage.exclusions=**/config/**,**/dto/**
```

### 8.3 PR装饰

```yaml
# SonarQube会在PR上添加评论，展示分析结果
# PR评论示例:

📊 SonarQube Analysis Report

Quality Gate: ✅ PASSED

Issues:
  - 🐛 Bugs: 0
  - 🔒 Vulnerabilities: 0
  - 💩 Code Smells: 2 (1 Major, 1 Minor)
  - 🔥 Security Hotspots: 1 (Reviewed: 100%)

Coverage:
  - Overall: 85.2%
  - New Code: 92.1% ✅ (threshold: 80%)

Duplication:
  - Overall: 1.8%
  - New Code: 0.0% ✅ (threshold: 3%)

Detail:
  - 🔴 Major: Method processOrder() has 85 lines (max 75)
  - 🟡 Minor: Rename variable "d" to "duration"
```

---

## 9. 面试题速查

**Q1: SonarQube的Bug、Vulnerability和Code Smell有什么区别？**
> Bug是可能导致程序运行错误的代码缺陷（如NPE风险、资源泄漏）；Vulnerability是可能被攻击者利用的安全漏洞（如SQL注入、硬编码密码）；Code Smell是影响代码可维护性但不影响正确性的设计问题（如方法过长、嵌套过深）。Bug和Vulnerability直接影响系统质量，Code Smell影响开发效率。

**Q2: Quality Gate的作用是什么？如何配置？**
> Quality Gate是一组质量条件的集合，决定代码是否达到可发布标准。配置维度包括：新Bug数、新漏洞数、新代码覆盖率、重复代码率、技术债比率等。只有所有条件都满足时才判定为通过。在CI中，Quality Gate不通过可以阻断流水线，防止低质量代码合并。

**Q3: 什么是Security Hotspot？它和Vulnerability有什么区别？**
> Vulnerability是SonarQube已确认的安全漏洞，需要立即修复。Security Hotspot是安全敏感代码，需要人工审查后才能确定是否为漏洞——例如命令执行、反序列化等操作。Hotspot审查后标记为"Safe"或"Fixed"，不像Vulnerability直接计入Bug。

**Q4: SonarQube如何计算技术债？**
> 每个Issue根据类型和严重级别分配预估修复时间（Blocker=1h，Critical=30min等），所有Issue的修复时间之和即为技术债总量。技术债比率=技术债时间/估算开发时间。比率<5%为A级，>50%为E级。新代码和整体代码分别计算。

**Q5: 圈复杂度和认知复杂度有什么区别？**
> 圈复杂度（Cyclomatic Complexity）统计独立执行路径数量，每增加一个if/for/while/case加1。认知复杂度（Cognitive Complexity）更贴近人类理解难度——嵌套加分会更多，线性代码加分少。认知复杂度更能反映代码的可读性和维护难度。

**Q6: SonarScanner在CI中分析时为什么需要fetch-depth=0？**
> SonarQube使用git blame获取每行代码的作者和提交时间，用于区分"新代码"和"旧代码"。fetch-depth=0确保获取完整git历史。如果只获取最近一次提交，所有代码都会被认为是新代码，导致新代码指标失真。

**Q7: 如何在多模块Maven项目中配置SonarQube？**
> 在父POM中配置sonar-maven-plugin即可自动递归分析所有子模块。设置`sonar.modules`指定子模块，每个子模块可以独立配置源码路径和覆盖率报告路径。使用`-Dsonar.coverage.jacoco.xmlReportPaths`可以聚合多模块覆盖率报告。

---

*最后更新：2026-07-13*

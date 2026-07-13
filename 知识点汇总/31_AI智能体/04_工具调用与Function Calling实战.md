# 工具调用与Function Calling实战

> Function Calling原理、MCP协议、工具定义与Spring AI/LangChain4j实战

---

## 📋 目录

1. [工具调用概述](#1-工具调用概述)
2. [Function Calling原理](#2-function-calling原理)
3. [各厂商Function Calling对比](#3-各厂商function-calling对比)
4. [MCP协议](#4-mcp协议)
5. [Spring AI工具调用实战](#5-spring-ai工具调用实战)
6. [LangChain4j工具调用实战](#6-langchain4j工具调用实战)
7. [工具调用最佳实践](#7-工具调用最佳实践)
8. [面试题速查](#8-面试题速查)

---

## 1. 工具调用概述

### 1.1 为什么需要工具调用

```
LLM的局限性:
  1. 知识截止 — 训练数据有截止日期，不知道最新信息
  2. 无法计算 — 复杂数学计算容易出错
  3. 无法联网 — 不能搜索网页
  4. 无法操作 — 不能查数据库/调API/执行代码
  5. 幻觉 — 可能编造不存在的信息

  工具调用(Tool Use)解决这些问题:
  ┌──────────────────────────────────────────────────┐
  │  LLM能力          │  工具补充                     │
  │  ──────        │  ────                      │
  │  语言理解          │  搜索引擎(获取最新信息)        │
  │  推理规划          │  计算器(精确计算)             │
  │  知识(有截止日期)   │  数据库(实时数据)             │
  │  生成文本          │  代码执行(Python沙箱)         │
  │                  │  API调用(天气/股票/地图)      │
  └──────────────────────────────────────────────────┘

  LLM + 工具 = 大脑 + 手
  LLM负责决策(用什么工具/传什么参数)
  工具负责执行(精确/实时/可靠)
```

### 1.2 工具调用的流程

```
完整工具调用流程:

  ┌──────────────────────────────────────────────────┐
  │ 1. 用户输入: "北京明天天气怎么样？"                │
  │                                                  │
  │ 2. 应用构造请求:                                   │
  │    messages: [{role: "user", content: "..."}]    │
  │    tools: [{type: "function", function: {...}}]  │
  │                                                  │
  │ 3. LLM返回工具调用决策:                            │
  │    tool_calls: [{                                │
  │      name: "get_weather",                        │
  │      arguments: {"city": "北京", "date": "明天"}  │
  │    }]                                            │
  │                                                  │
  │ 4. 应用执行工具:                                   │
  │    result = get_weather("北京", "明天")            │
  │    → "晴，25-35°C，西北风3级"                      │
  │                                                  │
  │ 5. 应用将结果发回LLM:                              │
  │    messages: [                                   │
  │      {role: "user", content: "..."},             │
  │      {role: "assistant", tool_calls: [...]},     │
  │      {role: "tool", content: "晴，25-35°C..."}   │
  │    ]                                             │
  │                                                  │
  │ 6. LLM生成最终回答:                               │
  │    "北京明天天气晴朗，气温25-35°C，西北风3级。"     │
  └──────────────────────────────────────────────────┘

  关键点:
    步骤3: LLM不执行工具，只决定调什么+传什么参数
    步骤4: 应用代码执行工具
    步骤5: 把结果传回LLM
    步骤6: LLM基于工具结果生成自然语言回答
    可能多轮: LLM可能连续调用多个工具
```

---

## 2. Function Calling原理

### 2.1 工具定义(JSON Schema)

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "查询指定城市的天气预报",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名称，如'北京'、'上海'"
        },
        "date": {
          "type": "string",
          "description": "日期，格式YYYY-MM-DD，默认今天",
          "enum": ["今天", "明天", "后天"]
        },
        "unit": {
          "type": "string",
          "description": "温度单位",
          "enum": ["celsius", "fahrenheit"],
          "default": "celsius"
        }
      },
      "required": ["city"]
    }
  }
}
```

### 2.2 LLM如何选择工具

```
LLM工具选择依赖:
  1. 工具名称(name) — 简洁明确
  2. 工具描述(description) — 详细说明做什么
  3. 参数描述(description) — 每个参数的含义
  4. 参数类型(type) — string/number/boolean/array/object
  5. 枚举值(enum) — 限制取值范围
  6. 必填字段(required) — 哪些参数必须提供

  最佳实践:
    ✅ name: "get_weather" (动词_名词，清晰)
    ❌ name: "weather" (太模糊)

    ✅ description: "查询指定城市未来7天的天气预报"
    ❌ description: "天气" (太简短)

    ✅ param description: "城市名称，如'北京'、'上海'，不要传区县"
    ❌ param description: "城市" (缺少示例和约束)

  LLM选择工具的过程(内部):
    1. 理解用户意图 → "查天气"
    2. 匹配工具描述 → get_weather匹配
    3. 提取参数 → city="北京", date="明天"
    4. 生成JSON参数 → {"city": "北京", "date": "明天"}
    5. 输出tool_call
```

### 2.3 多工具调用

```json
// LLM可以一次返回多个工具调用
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_001",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"北京\"}"
      }
    },
    {
      "id": "call_002",
      "type": "function",
      "function": {
        "name": "get_weather",
        "arguments": "{\"city\": \"上海\"}"
      }
    }
  ]
}

// 应用并行执行两个工具调用
// 然后将两个结果一起发回LLM
```

---

## 3. 各厂商Function Calling对比

```
┌──────────────────────────────────────────────────────────────┐
  │  厂商        │  参数格式        │  多工具  │  并行调用  │  特点  │
  │  ──────    │  ──────      │  ────  │  ────  │  ──── │
  │  OpenAI     │  JSON Schema    │  ✅     │  ✅       │  标准  │
  │  Anthropic  │  JSON Schema    │  ✅     │  ✅       │  最强  │
  │  Qwen       │  JSON Schema    │  ✅     │  ✅       │  中文好│
  │  DeepSeek   │  JSON Schema    │  ✅     │  ✅       │  便宜  │
  │  Ollama     │  JSON Schema    │  ✅     │  部分     │  本地  │
  └──────────────────────────────────────────────────────────────┘

  OpenAI格式(业界标准):
    request: tools = [{"type": "function", "function": {...}}]
    response: tool_calls = [{"id": "...", "function": {"name": "...", "arguments": "..."}}]

  Anthropic格式:
    request: tools = [{"name": "...", "description": "...", "input_schema": {...}}]
    response: content = [{"type": "tool_use", "name": "...", "input": {...}}]

  Spring AI/LangChain4j抽象了这些差异，统一接口
```

---

## 4. MCP协议

### 4.1 MCP概述

```
MCP(Model Context Protocol) — Anthropic提出的工具标准协议

  问题: 每个AI应用的工具都是自己定义的，不能复用
    App A定义了"search_web"工具
    App B也需要"search_web"工具，但要重新定义
    → 工具碎片化，重复开发

  MCP解决:
    标准化工具提供方(MCP Server)和工具消费方(MCP Client)之间的协议
    一个MCP Server可以被任何支持MCP的AI应用使用

  ┌──────────────────────────────────────────────────┐
  │  MCP架构:                                         │
  │                                                  │
  │  ┌──────────┐    MCP协议    ┌──────────┐         │
  │  │ MCP      │◄───────────►│  AI App   │         │
  │  │ Server   │    JSON-RPC  │ (Client)  │         │
  │  │ (工具)    │              │ LangChain │         │
  │  └──────────┘              │ Claude    │         │
  │                            │ Cursor    │         │
  │  ┌──────────┐              └──────────┘         │
  │  │ MCP      │◄───────────►                      │
  │  │ Server   │                                   │
  │  │ (数据库)  │                                   │
  │  └──────────┘                                   │
  └──────────────────────────────────────────────────┘

  MCP Server提供三种能力:
    1. Tools(工具) — 可执行的功能(如搜索/查询)
    2. Resources(资源) — 可读取的数据(如文件/数据库)
    3. Prompts(提示) — 预定义的提示模板
```

### 4.2 MCP vs Function Calling

```
┌──────────────────────────────────────────────────────┐
  │  维度          │  Function Calling   │  MCP          │
  │  ──────     │  ──────────      │  ────        │
  │  定义方        │  各AI应用自定义      │  标准协议      │
  │  复用性        │  低(每个App重新定义) │  高(一次定义)  │
  │  协议          │  HTTP/SDK           │  JSON-RPC     │
  │  运行方式      │  进程内函数调用       │  独立进程通信  │
  │  生态          │  各自为政            │  MCP生态      │
  │  工具发现      │  手动注册            │  自动发现      │
  └──────────────────────────────────────────────────────┘

  类比:
    Function Calling = 每个App自己写数据库驱动
    MCP = 标准的JDBC/ODBC协议，一个驱动到处用

  现状:
    MCP刚起步(2024年底发布)
    Claude/Cursor已原生支持MCP
    LangChain/LangChain4j已集成MCP
    未来趋势: MCP可能成为Agent工具标准
```

---

## 5. Spring AI工具调用实战

### 5.1 函数注册方式

```java
// 方式1: @Bean + @Description
@Configuration
public class ToolConfig {

    @Bean
    @Description("查询指定城市的天气")
    public Function<WeatherRequest, WeatherResponse> getWeather() {
        return request -> {
            // 实际调用天气API
            return weatherService.query(request.city(), request.date());
        };
    }

    @Bean
    @Description("执行SQL查询")
    public Function<SqlRequest, SqlResponse> queryDatabase(JdbcTemplate jdbc) {
        return request -> {
            List<Map<String, Object>> rows = jdbc.queryForList(request.sql());
            return new SqlResponse(rows);
        };
    }

    @Bean
    @Description("发送邮件")
    public Function<EmailRequest, EmailResponse> sendEmail(JavaMailSender mailSender) {
        return request -> {
            // 发送邮件
            SimpleMailMessage msg = new SimpleMailMessage();
            msg.setTo(request.to());
            msg.setSubject(request.subject());
            msg.setText(request.body());
            mailSender.send(msg);
            return new EmailResponse(true, "邮件发送成功");
        };
    }
}

// 请求/响应DTO(Public字段用于JSON Schema生成)
public record WeatherRequest(
    @JsonProperty("city") @JsonPropertyDescription("城市名称") String city,
    @JsonProperty("date") @JsonPropertyDescription("日期") String date
) {}

public record WeatherResponse(
    String city, String weather, double temperature, String description
) {}
```

### 5.2 调用方式

```java
@Service
public class AgentService {

    @Autowired
    private ChatClient chatClient;

    // 方式1: 直接指定函数名
    public String chatWithTools(String userInput) {
        return chatClient.prompt()
            .user(userInput)
            .functions("getWeather", "queryDatabase", "sendEmail")
            .call()
            .content();
    }

    // 方式2: 使用Advisor自动注入工具
    public String chatWithAdvisor(String userInput) {
        return chatClient.prompt()
            .user(userInput)
            .advisors(FunctionCallbackContext)
            .call()
            .content();
    }

    // 方式3: 动态注册工具(运行时添加)
    public String chatWithDynamicTools(String userInput) {
        FunctionCallback weatherCallback = FunctionCallback.builder()
            .function("getWeather", (String city) -> weatherService.query(city))
            .description("查询天气")
            .build();

        return chatClient.prompt()
            .user(userInput)
            .functions(weatherCallback)
            .call()
            .content();
    }
}
```

### 5.3 多轮工具调用

```java
// Spring AI自动处理多轮工具调用
// 当LLM返回工具调用时，Spring AI自动:
// 1. 执行工具
// 2. 将结果加入对话
// 3. 再次调用LLM
// 4. 循环直到LLM返回最终回答

@Service
public class MultiStepAgent {

    @Autowired
    private ChatClient chatClient;

    @Autowired
    private ChatMemory chatMemory;

    public String execute(String sessionId, String userInput) {
        return chatClient.prompt()
            .user(userInput)
            .functions("getWeather", "calculator", "queryDatabase", "searchWeb")
            .advisors(MessageChatMemoryAdvisor.builder()
                .chatMemory(chatMemory)
                .conversationId(sessionId)
                .build())
            .call()
            .content();
        // Spring AI内部自动处理多轮:
        //   LLM: 我需要查天气 → getWeather("北京") → "35°C"
        //   LLM: 我需要计算 → calculator("35 * 2") → 70
        //   LLM: 最终回答: "北京35°C，两倍是70"
    }
}
```

---

## 6. LangChain4j工具调用实战

### 6.1 @Tool注解方式

```java
public class AgentTools {

    @Tool("搜索网页，获取最新信息")
    public String searchWeb(@P("搜索关键词") String query) {
        return webSearchService.search(query);
    }

    @Tool("查询指定城市的天气")
    public String getWeather(
        @P("城市名称") String city,
        @P("日期，如今天/明天") String date
    ) {
        return weatherService.query(city, date);
    }

    @Tool("执行数学计算")
    public double calculate(@P("数学表达式，如 1+2*3") String expression) {
        return calculator.evaluate(expression);
    }

    @Tool("查询数据库")
    public String queryDatabase(@P("SQL查询语句") String sql) {
        List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql);
        return JsonUtils.toJson(rows);
    }

    @Tool("发送HTTP请求")
    public String httpRequest(
        @P("请求URL") String url,
        @P("请求方法: GET/POST/PUT/DELETE") String method,
        @P("请求体JSON，GET请求传空") String body
    ) {
        return httpClient.request(url, method, body);
    }
}
```

### 6.2 声明式Agent

```java
// 声明式接口 — LangChain4j自动实现
interface SmartAgent {

    @SystemMessage("""
        你是一个智能助手，拥有以下工具:
        1. searchWeb - 搜索网页
        2. getWeather - 查询天气
        3. calculate - 数学计算
        4. queryDatabase - 查询数据库
        5. httpRequest - 发送HTTP请求

        请根据用户需求，选择合适的工具完成任务。
        每次只调必要的工具，调用后总结结果。
        """)
    String chat(@MemoryId Object sessionId, @V("message") String userMessage);
}

// 构建Agent
SmartAgent agent = AiServices.builder(SmartAgent.class)
    .chatLanguageModel(QwenChatModel.builder()
        .apiKey(System.getenv("DASHSCOPE_API_KEY"))
        .modelName("qwen-plus")
        .build())
    .tools(new AgentTools())
    .chatMemory(MessageWindowChatMemory.withMaxMessages(50))
    .build();

// 使用
String result1 = agent.chat("session1", "北京明天天气怎么样？");
String result2 = agent.chat("session1", "那上海呢？");  // 有上下文记忆
String result3 = agent.chat("session1", "两地的温差是多少？");  // 自动调用计算器
```

### 6.3 工具执行错误处理

```java
public class RobustAgentTools {

    @Tool("查询天气")
    public String getWeather(@P("城市") String city) {
        try {
            WeatherResponse response = weatherService.query(city);
            if (response == null) {
                return "未找到城市[" + city + "]的天气信息";
            }
            return String.format("%s: %s, 温度%.1f°C, %s",
                city, response.getWeather(), response.getTemp(), response.getDescription());
        } catch (TimeoutException e) {
            return "天气查询超时，请稍后重试";
        } catch (Exception e) {
            return "天气查询失败: " + e.getMessage();
        }
    }

    @Tool("执行SQL查询")
    public String queryDatabase(@P("SQL语句") String sql) {
        // 安全校验: 只允许SELECT
        if (!sql.trim().toUpperCase().startsWith("SELECT")) {
            return "安全限制: 只允许执行SELECT查询";
        }

        // 限制查询行数
        if (!sql.toUpperCase().contains("LIMIT")) {
            sql += " LIMIT 100";
        }

        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(sql);
            return JsonUtils.toJson(rows);
        } catch (DataAccessException e) {
            return "SQL执行失败: " + e.getMessage();
        }
    }

    @Tool("执行Python代码")
    public String executeCode(@P("Python代码") String code) {
        // 沙箱执行(重要! 安全)
        try {
            return codeSandbox.execute(code, timeout=10, memoryLimit="128m");
        } catch (SecurityException e) {
            return "代码执行被安全策略阻止: " + e.getMessage();
        }
    }
}
```

---

## 7. 工具调用最佳实践

### 7.1 工具设计原则

```
1. 单一职责 — 每个工具只做一件事
   ✅ get_weather + get_stock_price (分离)
   ❌ get_info (太通用)

2. 描述清晰 — LLM靠描述选择工具
   ✅ "查询指定城市未来7天的天气预报"
   ❌ "天气"

3. 参数明确 — 类型+描述+枚举+示例
   ✅ city: "城市名，如北京、上海，不要含区县"
   ❌ city: "城市"

4. 返回友好 — 返回LLM能理解的文本
   ✅ "北京明天晴，25-35°C"
   ❌ {"w":1,"t":30,...}(编码)

5. 错误信息 — 返回有意义的错误描述
   ✅ "城市[xxx]不存在，请检查拼写"
   ❌ "Error 500"

6. 幂等设计 — 相同参数返回相同结果(便于重试)

7. 超时保护 — 设置超时防止挂起

8. 安全隔离 — 危险操作(代码执行/SQL)用沙箱
```

### 7.2 工具数量管理

```
工具数量对LLM选择准确率的影响:
  1-5个工具  → 准确率 > 95%
  5-10个工具 → 准确率 90%+
  10-20个工具 → 准确率 80%+
  20+个工具  → 准确率下降明显

  策略:
  1. 按场景分组 — 不同场景只传相关工具
  2. 两级路由 — 先Router选子Agent，子Agent有少量工具
  3. 工具摘要 — 大量工具时先让LLM选类别

  示例(两级路由):
    Router选择 → 财务Agent(3个财务工具)
    Router选择 → 运维Agent(4个运维工具)
    Router选择 → 通用Agent(5个通用工具)
    → 每次LLM只看到4-5个工具，准确率高
```

---

## 8. 面试题速查

**Q1: Function Calling的流程？**

```
1. 应用定义工具(JSON Schema: name/description/parameters)
2. 用户输入 + 工具定义发给LLM
3. LLM返回工具调用决策(name + arguments)
4. 应用执行工具获取结果
5. 结果发回LLM
6. LLM基于结果生成最终回答
可能多轮(多个工具连续调用)
```

**Q2: LLM如何选择正确的工具？**

```
依赖工具的name和description
描述越清晰，选择越准确
参数description帮助LLM提取正确参数
最佳实践: 单一职责、描述详细、参数明确
工具太多(>10)准确率下降，需分组路由
```

**Q3: MCP和Function Calling的区别？**

```
Function Calling: 每个应用自定义工具，不能复用
MCP: 标准协议，MCP Server(工具)可被任何MCP Client(AI应用)使用
类比: Function Calling=各自实现数据库驱动, MCP=标准JDBC
MCP是工具复用的标准化方向
```

**Q4: 工具调用出错怎么处理？**

```
1. 返回友好的错误文本(不是Exception)
2. LLM看到错误后可以调整策略(换工具/改参数)
3. 重试机制(指数退避)
4. 超时保护(防挂起)
5. 安全隔离(代码执行用沙箱)
6. 幂等设计(便于重试)
```

**Q5: 如何设计好的工具？**

```
1. 单一职责(一个工具一件事)
2. 描述清晰(LLM靠描述选工具)
3. 参数明确(类型+描述+枚举+示例)
4. 返回友好(LLM能理解的文本)
5. 错误有意义(帮助LLM调整)
6. 超时+安全+幂等
```

---

*最后更新: 2026-07-13*

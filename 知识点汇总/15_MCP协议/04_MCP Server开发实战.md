# MCP Server开发实战

> 自定义MCP Server，将你的工具/数据/API接入AI生态

---

## 📋 目录

1. [MCP Server概述](#1-mcp-server概述)
2. [Server架构](#2-server架构)
3. [工具（Tools）开发](#3-工具tools开发)
4. [资源（Resources）开发](#4-资源resources开发)
5. [安全与权限](#5-安全与权限)
6. [多语言SDK](#6-多语言sdk)
7. [面试要点](#7-面试要点)

---

## 1. MCP Server概述

### 什么是MCP Server

```
MCP Server = 暴露工具/资源/提示词给AI Client的服务

AI Client（Cursor/Claude Desktop/自定义Agent）
  ↓ MCP协议
MCP Server（你开发的服务）
  ↓
数据库 / API / 文件系统 / 内部系统

价值：一次开发MCP Server，所有支持MCP的AI工具都能使用
```

### MCP Server能力

```
1. Tools（工具）：可执行操作（查询数据库、调用API、创建文件）
2. Resources（资源）：只读数据（文件内容、配置信息）
3. Prompts（提示词）：可复用模板（代码审查模板、文档生成模板）
```

---

## 2. Server架构

```
┌─────────────────────────────────────────┐
│           AI Client (Cursor/Claude)      │
└──────────────────┬──────────────────────┘
                   │ JSON-RPC 2.0
                   │ (stdio / SSE / WebSocket)
┌──────────────────┴──────────────────────┐
│           MCP Server                     │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │Tools注册  │ │Resources │ │Prompts  │ │
│  │          │ │注册      │ │注册     │ │
│  └──────────┘ └──────────┘ └─────────┘ │
│  ┌──────────────────────────────────┐   │
│  │        Handler执行层              │   │
│  └──────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
  数据库          API           文件系统
```

---

## 3. 工具开发

### Python MCP Server（官方SDK）

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-database-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_database",
            description="查询MySQL数据库，执行SELECT语句",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SELECT SQL语句"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回行数限制",
                        "default": 10
                    }
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="get_table_schema",
            description="获取数据库表结构",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {"type": "string"}
                },
                "required": ["table_name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "query_database":
        sql = arguments["sql"]
        limit = arguments.get("limit", 10)
        # 安全检查
        if not sql.strip().upper().startswith("SELECT"):
            return [TextContent(type="text", text="错误：只允许SELECT查询")]
        
        results = db.execute(f"{sql} LIMIT {limit}")
        return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False))]
    
    elif name == "get_table_schema":
        table = arguments["table_name"]
        schema = db.get_schema(table)
        return [TextContent(type="text", text=json.dumps(schema))]

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())
    
    asyncio.run(main())
```

### TypeScript MCP Server

```typescript
import { Server } from "@modelcontextprotocol/sdk/server";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";

const server = new Server(
  { name: "my-api-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 注册工具
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "search_users",
      description: "搜索系统用户",
      inputSchema: {
        type: "object",
        properties: {
          keyword: { type: "string", description: "搜索关键词" },
          page: { type: "integer", default: 1 }
        },
        required: ["keyword"]
      }
    }
  ]
}));

// 处理工具调用
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === "search_users") {
    const users = await userApi.search(args.keyword, args.page);
    return {
      content: [{ type: "text", text: JSON.stringify(users) }]
    };
  }
  
  throw new Error(`Unknown tool: ${name}`);
});

// 启动
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Java MCP Server（通过HTTP）

```java
@RestController
@RequestMapping("/mcp")
public class McpServerController {
    
    // MCP工具注册
    @PostMapping("/tools/list")
    public McpResponse listTools() {
        return McpResponse.tools(List.of(
            Map.of(
                "name", "query_order",
                "description", "查询订单状态",
                "inputSchema", Map.of(
                    "type", "object",
                    "properties", Map.of(
                        "orderId", Map.of("type", "string", "description", "订单ID")
                    ),
                    "required", List.of("orderId")
                )
            ),
            Map.of(
                "name", "create_ticket",
                "description", "创建工单",
                "inputSchema", Map.of(
                    "type", "object",
                    "properties", Map.of(
                        "title", Map.of("type", "string"),
                        "description", Map.of("type", "string"),
                        "priority", Map.of("type", "string", "enum", List.of("low","medium","high"))
                    ),
                    "required", List.of("title")
                )
            )
        ));
    }
    
    // 工具调用
    @PostMapping("/tools/call")
    public McpResponse callTool(@RequestBody McpToolCall request) {
        String toolName = request.getName();
        Map<String, Object> args = request.getArguments();
        
        return switch (toolName) {
            case "query_order" -> {
                String orderId = (String) args.get("orderId");
                Order order = orderService.getOrder(orderId);
                yield McpResponse.text(JSON.toJSONString(order));
            }
            case "create_ticket" -> {
                Ticket ticket = ticketService.create(
                    (String) args.get("title"),
                    (String) args.get("description"),
                    (String) args.getOrDefault("priority", "medium")
                );
                yield McpResponse.text("工单已创建: " + ticket.getId());
            }
            default -> McpResponse.error("未知工具: " + toolName);
        };
    }
}
```

---

## 4. 资源开发

```python
# Resources: 只读数据
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="config://app/settings",
            name="应用配置",
            description="当前应用配置信息",
            mimeType="application/json"
        ),
        Resource(
            uri="docs://api/spec",
            name="API文档",
            description="API接口规格文档",
            mimeType="text/markdown"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "config://app/settings":
        return json.dumps(config.get_all())
    elif uri == "docs://api/spec":
        return open("docs/api_spec.md").read()
```

---

## 5. 安全与权限

### 工具权限控制

```python
# 基于角色的工具访问控制
TOOL_PERMISSIONS = {
    "query_database": ["reader", "admin"],
    "execute_sql": ["admin"],
    "create_ticket": ["user", "admin"],
    "delete_data": ["admin"],  # 高危操作
}

async def call_tool(name: str, arguments: dict, context: dict) -> list[TextContent]:
    # 1. 权限检查
    user_role = context.get("role", "user")
    allowed_roles = TOOL_PERMISSIONS.get(name, [])
    if user_role not in allowed_roles:
        return [TextContent(type="text", text=f"权限不足：需要 {allowed_roles}")]
    
    # 2. 高危操作确认
    if name in HIGH_RISK_TOOLS:
        return [TextContent(type="text", text="⚠️ 高危操作，请确认后执行")]
    
    # 3. 参数验证
    if not validate_args(name, arguments):
        return [TextContent(type="text", text="参数验证失败")]
    
    # 4. 执行
    result = execute_tool(name, arguments)
    
    # 5. 审计日志
    audit_log.record(name, arguments, result, context)
    
    return [TextContent(type="text", text=result)]
```

### SQL注入防护

```python
# SQL安全检查
SQL_BLOCKLIST = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]

def validate_sql(sql: str) -> bool:
    upper = sql.strip().upper()
    # 1. 只允许SELECT
    if not upper.startswith("SELECT"):
        return False
    # 2. 禁止危险操作
    for keyword in SQL_BLOCKLIST:
        if keyword in upper:
            return False
    # 3. 禁止多语句
    if ";" in sql.rstrip(";"):
        return False
    # 4. 禁止子查询写入
    if "INTO OUTFILE" in upper or "INTO DUMPFILE" in upper:
        return False
    return True
```

---

## 6. Cursor/Claude Desktop配置

### Cursor配置

```json
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "my_mcp_server.database"],
      "env": {
        "DB_HOST": "localhost",
        "DB_NAME": "myapp"
      }
    },
    "api-server": {
      "command": "node",
      "args": ["./mcp-servers/api-server.js"],
      "env": {
        "API_BASE_URL": "https://api.example.com"
      }
    },
    "java-server": {
      "url": "http://localhost:8080/mcp",
      "transport": "sse"
    }
  }
}
```

### Claude Desktop配置

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["-m", "my_mcp_server.database"]
    }
  }
}
```

---

## 7. 面试要点

### Q1: MCP Server的作用是什么？

```
MCP Server将你的工具/数据/API标准化暴露给AI Client

价值：
1. 一次开发，所有MCP兼容的AI工具都能用（Cursor/Claude/自定义Agent）
2. 标准协议（JSON-RPC 2.0），不用每个AI工具单独集成
3. AI可以自主决定何时调用什么工具
```

### Q2: MCP的Tools和Resources区别？

```
Tools：可执行操作（有副作用）
  - 查询数据库、调用API、创建文件
  - AI决定何时调用

Resources：只读数据（无副作用）
  - 配置文件、文档内容
  - AI按需读取
```

### Q3: MCP Server怎么保证安全？

```
1. 权限控制：基于角色的工具访问
2. 参数验证：Schema校验 + 业务校验
3. SQL防护：白名单SELECT + 黑名单危险操作
4. 高危确认：DELETE/DROP等操作需二次确认
5. 审计日志：记录所有工具调用
6. 速率限制：防止AI高频调用
```

---

## 📚 相关阅读

- [03_MCP协议核心原理与实战](./03_MCP协议核心原理与实战.md)
- [02_MCP vs Function Calling 详细对比](./02_MCP vs Function Calling 详细对比.md)
- [01_Function Calling 机制和工作原理](./01_Function Calling 机制和工作原理.md)
- [12_Agent设计模式](../12_AI集成/12_Agent设计模式.md)

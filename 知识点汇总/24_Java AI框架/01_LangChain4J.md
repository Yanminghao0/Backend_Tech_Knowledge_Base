# LangChain4J

## 1. 框架介绍
LangChain4J是当前Java生态中最受欢迎的AI开发框架，根据JetBrains 2025年第一季度调研数据，其采用率达到68%，位居Java AI框架榜首。该框架专注于大语言模型(LLM)应用开发，提供了模型集成、提示词管理、链操作等核心能力，特别适合构建企业级AI应用<mcreference link="http://m.toutiao.com/group/7560904035847373348/" index="1">1</mcreference>。

## 2. 基本信息
| 项目 | 说明 |
|------|------|
| 框架类型 | 大语言模型应用开发框架 |
| 核心功能 | 模型集成、提示工程、链管理、记忆机制 |
| 最新版本 | 1.6 (2025年第一季度) |
| 采用率 | 68% (Java AI框架中排名第一) |
| 主要优势 | 企业级特性、多模型支持、简洁API |

## 3. 核心特性
- **多模型支持**：兼容OpenAI、Anthropic、Google Gemini等主流LLM
- **提示词管理**：支持模板化、动态参数和版本控制
- **链操作**：可组合的工作流组件，支持复杂AI任务编排
- **记忆机制**：内置对话状态管理，支持短期和长期记忆
- **工具集成**：可连接外部API、数据库和业务系统
- **安全特性**：包含输入验证、输出过滤和权限控制

## 4. Java实现示例
```java
// 基本LLM调用示例
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.output.Response;

public class LangChain4JExample {
    public static void main(String[] args) {
        // 创建模型实例
        OpenAiChatModel model = OpenAiChatModel.withApiKey("your-api-key");
        
        // 发送请求并获取响应
        Response<String> response = model.generate("解释什么是LangChain4J框架");
        
        // 处理响应
        System.out.println("AI响应: " + response.content());
    }
}

// 带记忆的对话示例
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.service.AiServices;

public class ChatWithMemoryExample {
    // 定义AI服务接口
    interface ChatService {
        String chat(String userMessage);
    }
    
    public static void main(String[] args) {
        // 创建聊天记忆(保留最近10条消息)
        ChatMemory memory = MessageWindowChatMemory.withMaxMessages(10);
        
        // 创建模型实例
        ChatLanguageModel model = OpenAiChatModel.withApiKey("your-api-key");
        
        // 创建AI服务
        ChatService chatService = AiServices.create(ChatService.class, model, memory);
        
        // 开始对话
        System.out.println(chatService.chat("你好，我叫小明"));
        System.out.println(chatService.chat("记住我的名字了吗？")); // 模型应能记住用户名
    }
}
```

## 5. 应用场景
1. 智能客服系统：构建自然语言交互的客户支持平台
2. 文档理解与分析：自动提取关键信息、生成摘要
3. 代码辅助开发：自动生成代码、解释代码功能
4. 企业知识库：构建智能问答系统，支持内部知识检索
5. 内容创作：辅助生成营销文案、产品描述等
6. 数据分析助手：将自然语言转换为数据分析查询
7. 智能工作流：自动化文档处理、报告生成等业务流程

## 6. 注意事项
- API密钥管理：避免硬编码，使用环境变量或配置中心
- 模型成本控制：设置请求频率限制和预算监控
- 响应处理：实现超时处理和重试机制
- 数据隐私：敏感信息需过滤或脱敏后再发送给LLM
- 版本兼容性：1.6版本有较多API变更，升级需注意迁移指南
- 性能优化：考虑使用本地缓存减少重复请求
- 错误处理：需处理模型不可用、速率限制等异常情况

## 7. 最佳实践
- 使用依赖注入：结合Spring等框架管理LangChain4J组件
- 实现可观测性：添加日志、指标监控AI交互过程
- 采用提示词工程：设计结构化提示模板提高响应质量
- 分层架构：将AI逻辑与业务逻辑分离，提高可维护性
- 测试策略：编写单元测试验证提示词和链逻辑
- 渐进式集成：从非关键业务场景开始试点
- 持续优化：监控并分析AI响应质量，不断改进提示词

## 8. 高级特性：Memory / Agent / Tool

LangChain4J 的高级特性围绕"让 LLM 具备状态、自主决策和外部能力"展开，是构建生产级 AI 应用的关键。本节按 Memory、Tool、Agent 三个维度展开，并补充 RAG 与 Embedding 相关能力。

### 8.1 Memory 记忆机制

记忆机制解决 LLM "无状态"问题，使多轮对话具备上下文延续能力。LangChain4J 提供两种开箱即用的 ChatMemory 实现：

- **MessageWindowChatMemory**：按消息条数保留（默认 10 条），实现简单，适合大多数对话场景
- **TokenWindowChatMemory**：按 Token 数保留（默认 1000），更精确控制上下文长度，避免超出模型窗口

两者均支持自定义 `ChatMemoryStore` 实现持久化（Redis、数据库等），并通过 `ChatMemoryProvider` 实现多用户隔离。

```java
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.memory.chat.TokenWindowChatMemory;
import dev.langchain4j.memory.ChatMemory;
import dev.langchain4j.memory.chat.ChatMemoryProvider;
import dev.langchain4j.store.memory.chat.InMemoryChatMemoryStore;
import dev.langchain4j.store.memory.chat.ChatMemoryStore;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

// 1. 自定义持久化存储（生产环境可替换为 Redis 实现）
public class RedisChatMemoryStore implements ChatMemoryStore {
    private final Map<String, String> cache = new ConcurrentHashMap<>();

    @Override public String getMessages(String sessionId) { return cache.get(sessionId); }
    @Override public void updateMessages(String sessionId, String messages) { cache.put(sessionId, messages); }
    @Override public void deleteMessages(String sessionId) { cache.remove(sessionId); }
}

// 2. 多用户记忆 Provider：每个 sessionId 拥有独立记忆
ChatMemoryProvider memoryProvider = memoryId -> MessageWindowChatMemory.builder()
        .id(memoryId)
        .maxMessages(20)
        .chatMemoryStore(new RedisChatMemoryStore())
        .build();

// 3. Token 窗口记忆：按 Token 数截断，适合长文本场景
ChatMemory tokenMemory = TokenWindowChatMemory.withMaxTokens(2000);
```

记忆机制选型建议：短对话用 MessageWindow，长文本/成本敏感场景用 TokenWindow；多租户场景必须用 ChatMemoryProvider 隔离上下文。

### 8.2 Tool 工具集成（Function Calling）

Tool 机制让 LLM 能够调用外部函数，实现"看时间、查数据库、调 API"等真实能力。LangChain4J 通过 `@Tool` 注解声明工具，框架自动将其注册为模型可调用的函数。

```java
import dev.langchain4j.agent.tool.Tool;
import dev.langchain4j.agent.tool.ToolSpecification;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.service.AiServices;

import java.time.LocalDateTime;

// 1. 定义工具类：每个 @Tool 方法即一个可被 LLM 调用的函数
class OrderTools {

    @Tool("根据订单号查询订单状态")
    public String queryOrderStatus(String orderId) {
        // 实际可调用数据库或订单服务
        return "订单 " + orderId + " 已发货，预计明日送达";
    }

    @Tool("获取当前系统时间")
    public String getCurrentTime() {
        return LocalDateTime.now().toString();
    }
}

// 2. 声明式 AI 服务：框架自动处理工具调用循环
interface Assistant {
    String chat(String userMessage);
}

ChatLanguageModel model = OpenAiChatModel.builder()
        .apiKey(System.getenv("OPENAI_API_KEY"))
        .build();

Assistant assistant = AiServices.builder(Assistant.class)
        .chatLanguageModel(model)
        .tools(new OrderTools())   // 注册工具
        .build();

// 3. 模型会自主判断是否调用工具，并基于返回结果作答
String answer = assistant.chat("帮我查一下订单 20250706001 的状态");
// 模型自动调用 queryOrderStatus("20250706001")，再用结果生成自然语言回复
```

Tool 调用流程：用户消息 → 模型决定是否调用工具 → 框架执行 Java 方法 → 将结果回传模型 → 模型生成最终回复。这一循环由 `AiServices` 自动编排，开发者只需关注 `@Tool` 方法实现。

### 8.3 Agent 智能体

LangChain4J 的 Agent 能力以 `AiServices` 为核心，配合 Memory + Tool 即可构建出具备"感知—决策—行动"闭环的智能体。框架内置工具调用循环（ReAct 模式），无需手写编排逻辑。

```java
import dev.langchain4j.service.AiServices;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;

// 通过 SystemMessage 设定 Agent 角色与行为约束
interface CustomerServiceAgent {

    @SystemMessage("""
        你是某电商平台的智能客服。
        - 优先使用工具查询订单、物流信息
        - 无法解决的问题应如实告知并建议转人工
        - 回答需简洁、专业、礼貌
        """)
    String chat(String userMessage);
}

CustomerServiceAgent agent = AiServices.builder(CustomerServiceAgent.class)
        .chatLanguageModel(model)
        .chatMemory(MessageWindowChatMemory.withMaxMessages(30))
        .tools(new OrderTools())        // 装配工具能力
        .build();

// Agent 自主完成多步任务：理解意图 → 调用工具 → 综合作答
String reply = agent.chat("我的订单 20250706001 到哪了？大概多久能到？");
```

Agent 设计要点：① 用 `@SystemMessage` 固定角色边界；② 工具粒度要适中，过粗难调用、过细易混淆；③ 配合 Memory 实现多轮任务跟进；④ 复杂场景可结合 RAG 注入私有知识，让 Agent 在"工具 + 知识"双驱动下工作。

### 8.4 RAG 检索增强生成与 Embedding

RAG（Retrieval-Augmented Generation）让 LLM 基于私有知识回答问题，是企业知识库的核心技术。LangChain4J 提供 Embedding、VectorStore、ContentRetriever 全套组件。

```java
import dev.langchain4j.data.segment.TextSegment;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.openai.OpenAiEmbeddingModel;
import dev.langchain4j.store.embedding.EmbeddingStore;
import dev.langchain4j.store.embedding.inmemory.InMemoryEmbeddingStore;
import dev.langchain4j.store.embedding.EmbeddingStoreContentRetriever;
import dev.langchain4j.document.Document;
import dev.langchain4j.document.loader.FileSystemDocumentLoader;
import dev.langchain4j.document.splitter.DocumentSplitters;

// 1. 加载文档并切片
Document doc = FileSystemDocumentLoader.loadDocument("knowledge.pdf");
List<TextSegment> segments = DocumentSplitters
        .recursive(300, 30)   // 每片约 300 token，重叠 30
        .split(doc);

// 2. 生成向量并写入向量库
EmbeddingModel embeddingModel = OpenAiEmbeddingModel.withApiKey(key);
EmbeddingStore<TextSegment> store = new InMemoryEmbeddingStore<>();
// 生产环境可替换为 PgVector / Chroma / Pinecone / Milvus 等

// 3. 构建检索器并装配到 AI 服务
ContentRetriever retriever = EmbeddingStoreContentRetriever.builder()
        .embeddingStore(store)
        .embeddingModel(embeddingModel)
        .maxResults(5)
        .build();

Assistant ragAssistant = AiServices.builder(Assistant.class)
        .chatLanguageModel(model)
        .contentRetriever(retriever)   // 注入知识检索
        .build();
```

支持的向量库：InMemory（测试）、PgVector、Chroma、Pinecone、Milvus、Weaviate、Qdrant、Elasticsearch 等。选型考量：数据规模、查询延迟、是否需要混合检索（向量 + 关键词）。

## 9. Spring Boot 集成

LangChain4J 提供官方 `langchain4j-spring-boot-starter`，可在 Spring Boot 项目中以依赖注入方式使用 AI 组件，与现有企业架构无缝整合。

### 9.1 依赖配置

```xml
<!-- pom.xml -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>dev.langchain4j</groupId>
            <artifactId>langchain4j-bom</artifactId>
            <version>1.6.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-spring-boot-starter</artifactId>
    </dependency>
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-open-ai-spring-boot-starter</artifactId>
    </dependency>
    <dependency>
        <groupId>dev.langchain4j</groupId>
        <artifactId>langchain4j-embeddings-all-minilm-l6-v2-spring-boot-starter</artifactId>
    </dependency>
</dependencies>
```

### 9.2 配置与 Bean 定义

```yaml
# application.yml
langchain4j:
  open-ai:
    chat-model:
      api-key: ${OPENAI_API_KEY}
      model-name: gpt-4o-mini
      temperature: 0.7
      timeout: PT60S
    embedding-model:
      api-key: ${OPENAI_API_KEY}
      model: text-embedding-3-small
```

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import dev.langchain4j.service.AiServices;
import dev.langchain4j.memory.chat.MessageWindowChatMemory;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.store.embedding.EmbeddingStore;

@Configuration
public class AiConfig {

    @Bean
    public Assistant assistant(ChatLanguageModel model,
                               EmbeddingStore store) {
        return AiServices.builder(Assistant.class)
                .chatLanguageModel(model)
                .chatMemory(MessageWindowChatMemory.withMaxMessages(20))
                .tools(new OrderTools())
                .build();
    }
}

// Controller 直接注入使用
@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final Assistant assistant;

    public ChatController(Assistant assistant) { this.assistant = assistant; }

    @PostMapping
    public String chat(@RequestBody Map<String, String> body) {
        return assistant.chat(body.get("message"));
    }
}
```

Spring Boot 集成优势：自动配置模型/嵌入 Bean；与 Spring 的配置中心、可观测性（Micrometer）、安全体系天然兼容；AI 服务接口可作为普通 Bean 注入业务层，便于分层与测试。

## 10. 与 Python LangChain 对比

LangChain4J 在设计理念上深受 Python LangChain 启发，但针对 Java 生态做了大量适配。理解差异有助于技术选型与跨语言协作。

| 对比维度 | Python LangChain | LangChain4J |
|---------|------------------|-------------|
| 语言生态 | Python，数据科学/AI 原生 | Java/JVM，企业级后端原生 |
| 类型系统 | 动态类型，灵活但易出错 | 强静态类型，IDE 重构与编译期检查友好 |
| API 风格 | 链式 LCEL 表达式为主 | 声明式 AiServices 接口 + Builder |
| 性能 | 解释执行，GIL 限制并发 | JIT 编译，多线程并发能力强 |
| 集成能力 | 库最丰富，新模型/工具跟进最快 | 集成数量稍少但质量稳定，跟进略滞后 |
| 部署形态 | 常配合 FastAPI 容器化 | 嵌入 Spring Boot/Quarkus，与现有 JVM 系统一体 |
| 企业适配 | 适合原型与数据团队 | 适合已有 Java 技术栈的企业落地 |
| 社区成熟度 | 起步早，社区与文档庞大 | 后发但增长快，企业采用率高 |
| 工程规范 | 需额外约束 | 天然契合 Java 工程规范（包/接口/测试） |

选型建议：① 团队以 Java 为主、需嵌入现有 JVM 后端 → LangChain4J；② 重数据科学/ML Pipeline、需快速验证 → Python LangChain；③ 大型企业可"前端/数据用 Python，核心后端用 LangChain4J"，两者通过 HTTP/gRPC 互补。注意 LangChain4J 并非 LangChain 的逐行移植，API 不完全对应，跨语言移植需按概念映射而非照搬代码。

## 11. 面试要点（5问）

**Q1：LangChain4J 的 ChatMemory 有哪两种实现？如何选型？**
答：MessageWindowChatMemory 按消息条数截断，TokenWindowChatMemory 按 Token 数截断。短对话、对成本不敏感选 MessageWindow；长文本、需精确控制上下文窗口与成本选 TokenWindow。多用户场景需配合 ChatMemoryProvider 按 sessionId 隔离，并通过自定义 ChatMemoryStore 实现持久化。

**Q2：`@Tool` 注解的工作原理是什么？模型如何"知道"该调哪个工具？**
答：`@Tool` 标注的方法会被框架解析为 ToolSpecification（含名称、描述、参数 schema），随请求一并发送给模型。模型基于函数描述与用户意图决定是否调用及调用参数；框架接收调用请求后通过反射执行对应 Java 方法，将返回值作为工具结果回传模型，由模型生成最终自然语言回复。描述质量直接决定调用准确率。

**Q3：AiServices 是什么？相比直接调用 ChatLanguageModel 有何优势？**
答：AiServices 是声明式 AI 服务封装，开发者只需定义 Java 接口，由框架代理实现。优势：① 自动管理记忆、工具调用循环、RAG 检索编排；② 用 `@SystemMessage`/`@UserMessage` 注解管理提示词，类型安全；③ 返回类型可自动反序列化（String/POJO/结构化对象）；④ 与 Spring 依赖注入无缝结合，把 AI 能力当作普通 Bean 使用。

**Q4：在 Spring Boot 中如何实现一个带 RAG 的智能客服？**
答：① 引入 `langchain4j-spring-boot-starter` 及模型 starter；② 用 `application.yml` 配置模型参数；③ 加载企业文档 → 切片 → 调用 EmbeddingModel 生成向量 → 存入 EmbeddingStore（如 PgVector）；④ 用 `EmbeddingStoreContentRetriever` 构建检索器；⑤ 通过 `AiServices.builder()` 装配模型 + 检索器 + Memory + Tools，生成 Assistant Bean；⑥ Controller 注入 Assistant 处理用户请求。检索结果会自动作为上下文注入提示词。

**Q5：LangChain4J 与 Python LangChain 该如何选？企业落地要关注哪些工程问题？**
答：技术栈以 Java 为主、需嵌入现有 JVM 后端选 LangChain4J；偏数据科学/快速原型选 Python LangChain。企业落地共性关注点：API 密钥管理（配置中心/ Vault，禁止硬编码）、成本控制（限流 + 预算监控 + 缓存）、可观测性（日志/Micrometer 指标/链路追踪）、安全合规（敏感数据脱敏、输出过滤、PII 检测）、容错（超时/重试/熔断/降级）、模型版本与 API 兼容性管理、提示词的版本化与回归测试。

## 12. 相关阅读

- 官方文档：https://docs.langchain4j.dev
- 官方 GitHub：https://github.com/langchain4j/langchain4j
- 官方示例库（含 Spring Boot/RAG/Tools 等完整示例）：https://github.com/langchain4j/langchain4j-examples
- Python LangChain（对比参考）：https://python.langchain.com
- 向量数据库选型：PgVector / Milvus / Qdrant / Chroma / Pinecone 官方文档
- 论文：Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", 2020（RAG 原始论文）
- 论文：Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", 2022（Agent 工具调用范式）
- Spring AI（另一 Spring 官方 AI 抽象，可与 LangChain4J 互补对比）：https://docs.spring.io/spring-ai/reference/

---

✅ 完成状态：本文件已包含LangChain4J框架核心知识点，包括基本介绍、实现示例、应用场景、最佳实践，并扩充了高级特性（Memory/Agent/Tool/RAG）、Spring Boot 集成、与 Python LangChain 对比、面试要点与相关阅读，可作为 Java AI 开发与面试参考资料。
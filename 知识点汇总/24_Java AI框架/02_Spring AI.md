# Spring AI

## 1. 框架介绍
Spring AI是Spring生态系统官方推出的AI开发框架，于2025年5月正式发布1.0版本。作为Spring家族的新成员，它提供了统一的AI模型访问接口和丰富的企业级功能，特别适合Java开发者快速构建AI应用。根据JetBrains 2025年第一季度调研，Spring AI的采用率达到52%，在Java AI框架中排名第二<mcreference link="http://m.toutiao.com/group/7560904035847373348/" index="1">1</mcreference><mcreference link="http://m.toutiao.com/group/7528416887677354531/" index="3">3</mcreference>。

## 2. 基本信息
| 项目 | 说明 |
|------|------|
| 框架类型 | 企业级AI应用开发框架 |
| 核心功能 | AI模型集成、提示词管理、向量存储、函数调用 |
| 最新版本 | 1.0 (2025年5月) |
| 采用率 | 52% (Java AI框架中排名第二) |
| 主要优势 | Spring生态集成、企业级特性、云原生支持 |

## 3. 核心特性
- **统一模型接口**：标准化访问各类AI模型，包括OpenAI、Azure OpenAI、阿里云通义等
- **Spring生态集成**：与Spring Boot、Spring Cloud等无缝衔接，支持自动配置
- **提示词模板**：基于Mustache的模板引擎，支持动态参数和国际化
- **向量存储抽象**：统一接口操作各类向量数据库，如Redis、PostgreSQL、Milvus
- **函数调用能力**：支持AI模型调用Java方法，实现工具集成
- **流式响应**：支持SSE (Server-Sent Events) 实现实时响应
- **云原生设计**：支持容器化部署、配置外部化、健康检查等企业特性

## 4. Java实现示例
```java
// Spring Boot集成OpenAI示例
import org.springframework.ai.openai.OpenAiChatClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AiController {

    private final OpenAiChatClient chatClient;

    // 自动注入AI客户端 (配置在application.properties中)
    @Autowired
    public AiController(OpenAiChatClient chatClient) {
        this.chatClient = chatClient;
    }

    @GetMapping("/ai/chat")
    public String chat(@RequestParam String message) {
        // 调用AI模型
        return chatClient.call(message);
    }
}

// 配置文件 (application.properties)
spring.ai.openai.api-key=your-api-key
spring.ai.openai.chat.model=gpt-4
spring.ai.openai.chat.temperature=0.7

// 向量存储示例
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class VectorStoreService {

    private final VectorStore vectorStore;

    @Autowired
    public VectorStoreService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    // 存储文档到向量数据库
    public void addDocument(String content, String metadata) {
        Document document = new Document(content);
        document.getMetadata().put("source", metadata);
        vectorStore.add(List.of(document));
    }

    // 相似性搜索
    public List<Document> search(String query) {
        return vectorStore.similaritySearch(query);
    }
}
```

## 5. 应用场景
1. 企业知识库：结合向量存储实现智能文档检索
2. 客户服务：构建AI客服系统，集成企业内部系统
3. 内容生成：自动生成报告、邮件、产品描述等
4. 智能助手：开发企业内部AI助手，支持自然语言交互
5. 数据分析：将自然语言查询转换为SQL执行并返回结果
6. 代码辅助：集成到IDE或开发平台，辅助代码生成和解释
7. 智能工作流：在Spring Cloud应用中添加AI决策节点

## 6. 注意事项
- 依赖管理：Spring AI 1.0需要Spring Boot 3.2+，注意版本兼容性
- API密钥安全：使用Spring Cloud Config或Vault管理敏感配置
- 模型选择：根据任务类型选择合适的模型，平衡效果与成本
- 性能考虑：添加缓存层减少重复AI请求，提高响应速度
- 错误处理：实现降级策略，处理模型服务不可用时的情况
- 云服务集成：阿里云、AWS等云厂商提供专用Spring AI starter
- 资源消耗：监控AI请求的资源占用，设置合理的超时和重试策略

## 7. 最佳实践
- 分层架构：将AI逻辑封装在服务层，与控制器层分离
- 配置外部化：使用Spring Environment抽象管理AI参数
- 测试策略：使用@SpringBootTest测试AI功能，可集成TestContainers
- 可观测性：添加Micrometer指标监控AI调用次数和响应时间
- 提示词管理：将复杂提示词存储为模板文件，便于维护
- 安全控制：实现请求速率限制，防止滥用AI服务
- 渐进式采用：从非关键业务场景开始，逐步扩展AI应用范围

## 8. ChatClient高级用法

ChatClient是Spring AI 1.0推荐的核心API，采用流式构建器（Fluent Builder）风格，相比直接使用ChatModel提供了更丰富的链式调用能力，支持系统消息、参数控制、Advisor拦截、流式响应等特性。它将提示词构建、模型调用、输出解析三步合一，是日常开发首选入口。

### 8.1 流式响应 (Streaming)

流式响应基于Reactor的Flux实现，逐Token返回结果，显著降低首字响应时间，适合聊天界面实时打字效果。

```java
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import reactor.core.publisher.Flux;

@GetMapping(value = "/ai/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<String> streamChat(@RequestParam String message) {
    return chatClient.prompt(message).stream().content();
}
```

### 8.2 系统消息与参数控制

通过.system()设定角色人设，通过.options()控制模型参数（温度、Token上限等），实现精细化调参。

```java
String response = chatClient.prompt()
    .system("你是一位资深Java技术专家，回答要专业、简洁")
    .user(message)
    .options(OpenAiChatOptions.builder()
        .withModel("gpt-4")
        .withTemperature(0.3)
        .withMaxTokens(2000)
        .build())
    .call()
    .content();
```

### 8.3 对话历史管理

多轮对话需要维护上下文，Spring AI提供ChatMemory抽象（如InMemoryChatMemory），可按会话ID隔离历史。

```java
// 使用ChatMemory管理多轮对话历史
@Bean
public ChatMemory chatMemory() {
    return new InMemoryChatMemory();
}

// 发送对话时携带历史消息
String response = chatClient.prompt()
    .messages(conversationHistory)   // 已有的历史消息
    .user(newMessage)
    .call()
    .content();
```

### 8.4 Advisor链 (拦截器模式)

Advisor是Spring AI的拦截器机制，类似Servlet Filter，可在请求前后插入自定义逻辑（日志、敏感词过滤、Prompt增强、限流等），多个Advisor组成链式调用，是扩展ChatClient行为的核心扩展点。

```java
// 使用Advisor增强请求
String response = chatClient.prompt()
    .user(message)
    .advisors(advisor -> advisor.param("conversationId", "user-123"))
    .call()
    .content();

// 自定义Advisor实现（请求前后拦截）
public class LoggingAdvisor implements BaseAdvisor {
    @Override
    public AdvisedRequest before(AdvisedRequest request) {
        log.info("调用模型: {}", request.userText());
        return request;
    }
    @Override
    public AdvisedResponse after(AdvisedResponse response) {
        log.info("模型响应: {}", response.response().getResult().getOutput().getText());
        return response;
    }
}
```

## 9. Function Calling实战

Function Calling（函数调用）允许AI模型在需要时调用Java方法获取外部数据或执行操作，是构建智能Agent的基础。Spring AI通过将Java函数注册为Bean，自动生成Schema传递给模型，实现透明的函数调用，开发者无需手动解析模型返回的函数调用指令。

### 9.1 定义函数

使用Record定义请求和响应类型，Spring AI会基于类型自动推导JSON Schema并传递给模型。

```java
import java.util.function.Function;

// 使用Record定义请求和响应，Spring AI自动推导JSON Schema
public record WeatherRequest(String city, String unit) {}
public record WeatherResponse(String city, int temperature, String condition) {}

// 实现Function接口
public class WeatherFunction implements Function<WeatherRequest, WeatherResponse> {
    @Override
    public WeatherResponse apply(WeatherRequest request) {
        // 调用真实天气API
        return new WeatherResponse(request.city(), 25, "晴");
    }
}
```

### 9.2 注册与调用

将函数注册为Spring Bean并标注@Description（告知模型函数用途），在ChatClient调用时通过.functions()指定可用函数。

```java
@Configuration
public class FunctionConfig {
    // 注册为Bean，@Description用于告知模型函数用途
    @Bean
    @Description("获取指定城市的当前天气信息")
    public Function<WeatherRequest, WeatherResponse> getCurrentWeather() {
        return new WeatherFunction();
    }
}

// 在ChatClient中指定可用函数
String response = chatClient.prompt()
    .user("北京今天天气怎么样？")
    .functions("getCurrentWeather")   // 传入Bean名称
    .call()
    .content();
// 模型返回："北京今天天气晴，气温25度。"
```

### 9.3 调用流程详解

1. 用户提问，模型分析是否需要调用函数
2. 模型返回函数名和参数（JSON格式）
3. Spring AI自动反序列化参数并调用对应Java方法
4. 将方法返回值序列化后回传给模型
5. 模型基于函数执行结果生成最终自然语言回答
6. 整个多轮交互对开发者透明，仅需声明函数Bean

注意：函数调用会增加一次额外的模型请求（先返回函数调用，再基于结果生成回答），需关注延迟和Token消耗。

## 10. RAG集成

RAG（Retrieval-Augmented Generation，检索增强生成）是企业AI应用的核心模式，通过检索私有知识库相关内容作为上下文，让模型基于专属数据回答问题，解决大模型知识滞后和幻觉问题。Spring AI提供了从文档加载、分割、向量化、存储到检索的完整ETL管线。

### 10.1 完整RAG流程

```java
@Service
public class RagService {

    private final VectorStore vectorStore;
    private final ChatClient chatClient;

    // 步骤1: 文档加载与分割
    public void loadDocuments(String filePath) {
        // 使用Tika解析多格式文档(PDF/Word/HTML等)
        DocumentReader reader = new TikaDocumentReader(filePath);
        List<Document> documents = reader.get();

        // 按Token数量切分，保留语义完整性
        TextSplitter splitter = new TokenTextSplitter();
        List<Document> chunks = splitter.apply(documents);

        // 向量化并存储到向量数据库
        vectorStore.add(chunks);
    }

    // 步骤2: 检索增强问答
    public String queryWithContext(String question) {
        // 检索Top-K相关文档片段
        List<Document> relevant = vectorStore.similaritySearch(
            SearchRequest.query(question).withTopK(3).withSimilarityThreshold(0.7)
        );

        // 拼接上下文
        String context = relevant.stream()
            .map(Document::getText)
            .collect(Collectors.joining("\n\n"));

        // 构建提示词模板并调用模型
        String prompt = """
            基于以下上下文回答问题，若上下文不包含答案请明确说明。

            上下文：
            {context}

            问题：{question}
            """;

        return chatClient.prompt()
            .user(u -> u.text(prompt)
                .param("context", context)
                .param("question", question))
            .call()
            .content();
    }
}
```

### 10.2 Embedding模型使用

EmbeddingModel负责将文本转为向量，是RAG向量检索的基础。支持OpenAI、通义千问、Ollama等多种实现。

```java
@Service
public class EmbeddingService {

    private final EmbeddingModel embeddingModel;

    // 单文本向量化
    public float[] embed(String text) {
        return embeddingModel.embed(text);
    }

    // 批量向量化（提高吞吐量）
    public List<float[]> embedBatch(List<String> texts) {
        EmbeddingResponse response = embeddingModel.embedForResponse(texts);
        return response.getResults().stream()
            .map(Embedding::getOutput)
            .collect(Collectors.toList());
    }
}
```

### 10.3 生产级RAG优化要点

- 文档预处理：使用Tika解析多格式，TokenTextSplitter按语义切分（建议500-1000 token/块）
- 混合检索：结合关键词搜索（BM25）与向量搜索，提升召回率
- 重排序：用Cross-Encoder对检索结果二次排序，提升精度
- 上下文管理：控制Token数量避免超出模型上下文窗口
- 引用溯源：记录答案来源文档，便于核验与合规审计

## 11. Output结构化输出

Spring AI支持将模型自由文本输出自动转换为Java对象，通过OutputConverter体系实现，避免手动解析JSON的繁琐。调用entity()方法时，框架自动在Prompt中注入目标类型的格式说明，引导模型输出规范结构化数据。

### 11.1 实体类输出 (BeanOutputConverter)

```java
public record ActorFilms(String actor, List<String> movies) {}

// 一行代码将输出转为POJO
ActorFilms result = chatClient.prompt()
    .user("推荐周星驰主演的5部经典电影")
    .call()
    .entity(ActorFilms.class);
// result.actor() = "周星驰", result.movies() = ["大话西游", "功夫", ...]
```

### 11.2 内置Converter对比

```java
// List输出 - 转为List<String>
List<String> movies = chatClient.prompt()
    .user("列出5部科幻电影名称")
    .call()
    .entity(new ParameterizedTypeReference<List<String>>() {});

// Map输出 - 转为Map
Map<String, Object> info = chatClient.prompt()
    .user("返回一部电影信息，包含name、director、year字段")
    .call()
    .entity(new ParameterizedTypeReference<Map<String, Object>>() {});
```

| Converter | 输出类型 | 适用场景 |
|-----------|---------|---------|
| BeanOutputConverter | POJO/Record | 复杂结构化对象 |
| ListOutputConverter | List<String> | 列表型结果 |
| MapOutputConverter | Map<String,Object> | 键值对结果 |

### 11.3 自定义Converter

当内置Converter无法满足需求时，可继承AbstractMessageOutputConverter实现自定义解析逻辑。

```java
public class MovieOutputConverter extends AbstractMessageOutputConverter<List<Movie>> {
    @Override
    public List<Movie> convert(String text) {
        // 自定义解析逻辑，处理模型输出
        return objectMapper.readValue(text, new TypeReference<>() {});
    }

    @Override
    public String getFormat() {
        // 自动注入到Prompt中，指导模型输出格式
        return "请严格返回JSON数组格式: [{\"title\":\"\",\"year\":0}]";
    }
}
```

## 12. 面试要点

### Q1: Spring AI与LangChain4j有什么区别？如何选型？

答：Spring AI是Spring官方框架，深度集成Spring生态（Boot自动配置、Cloud、Security、Micrometer等），适合企业级Spring Boot项目；LangChain4j是LangChain的Java移植版，更贴近Python生态设计理念，框架耦合度低、功能丰富。选型建议：已有Spring Boot技术栈选Spring AI以获得最佳集成体验；需要轻量级、跨框架集成多模型能力可考虑LangChain4j。两者并非互斥，部分项目会混用。

### Q2: Spring AI的Function Calling底层如何实现？

答：开发者将Java函数注册为Bean并标注@Description，Spring AI基于函数签名和注解自动生成JSON Schema作为tools参数传递给模型API。模型判断需要调用时返回函数名和参数JSON，Spring AI自动反序列化参数、调用对应方法，再将返回值序列化回传模型完成多轮交互。整个过程对开发者透明，开发者只需关注函数业务逻辑。底层支持OpenAI原生function calling协议及JSON模式兼容模型。

### Q3: 如何实现生产级RAG系统？有哪些优化点？

答：核心环节包括：(1) 文档预处理：Tika解析多格式，TokenTextSplitter按语义切分；(2) 向量化：选择合适Embedding模型；(3) 向量库选型：小数据量用PgVector/Redis，大规模用Milvus；(4) 混合检索：BM25关键词+向量检索提升召回；(5) 重排序：Cross-Encoder精排；(6) 上下文管理：控制Token避免超窗口；(7) 引用溯源：记录答案来源文档便于核验。此外需关注增量更新、权限隔离、评测指标（Faithfulness、Answer Relevance）等。

### Q4: ChatClient的Advisor机制有什么用？

答：Advisor是Spring AI的拦截器模式，类似Servlet Filter，可在请求前后插入自定义逻辑。典型用途：请求/响应日志、敏感词过滤、Prompt增强（自动注入上下文）、限流熔断、调用链追踪、结果缓存等。多个Advisor组成链式调用，是扩展ChatClient行为的核心扩展点，体现了Spring AOP理念，实现了业务逻辑与横切关注点分离。Spring AI内置了QuestionAnswerAdvisor（RAG增强）等开箱即用的Advisor。

### Q5: Spring AI如何保证模型输出结构化的可靠性？

答：通过OutputConverter体系实现：调用entity()方法时框架自动在Prompt中注入目标类型的JSON Schema格式说明，引导模型输出规范JSON；随后解析模型返回文本并反序列化为目标类型。若解析失败，可配置RetryTemplate重试机制，结合Temperature调低（如0.0-0.3）提升输出稳定性。复杂场景建议结合自定义Converter和校验逻辑双重保障。生产环境还需监控解析失败率，必要时回退到非结构化输出或人工兜底。

## 13. 相关阅读

- 官方文档：https://docs.spring.io/spring-ai/reference/
- 官方GitHub仓库：https://github.com/spring-projects/spring-ai
- 官方示例集：https://github.com/spring-projects/spring-ai-examples
- Spring AI 1.0 GA发布公告：https://spring.io/blog/2025/05/20/spring-ai-1-0-GA
- Baeldung Spring AI系列教程：https://www.baeldung.com/spring-ai
- 阿里云通义千问Spring AI集成：https://help.aliyun.com/zh/dashscope/developer-reference/spring-ai
- LangChain4j对比参考：https://docs.langchain4j.dev/
- Spring AI Cookbook（RAG实战章节）

---

✅ 完成状态：本文件已涵盖Spring AI核心知识点，包括框架集成、代码示例、应用场景和最佳实践，适合Java开发者快速上手企业级AI应用开发。扩展章节涵盖ChatClient高级用法、Function Calling实战、RAG集成、Output结构化输出、面试要点及相关阅读。

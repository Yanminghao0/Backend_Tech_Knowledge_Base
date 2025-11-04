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

---
✅ 完成状态：本文件已涵盖Spring AI核心知识点，包括框架集成、代码示例、应用场景和最佳实践，适合Java开发者快速上手企业级AI应用开发。
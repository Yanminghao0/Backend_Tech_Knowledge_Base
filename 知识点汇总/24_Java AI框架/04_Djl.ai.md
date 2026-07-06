# DJL (Deep Java Library) 知识点汇总

> DJL 是 AWS 于 2019 年开源的深度学习 Java 框架，提供引擎无关（Engine Agnostic）的统一 API。
> 仓库：https://github.com/deepjavalibrary/djl ，当前主版本 0.2x，支持 TensorFlow / PyTorch / MXNet / ONNX Runtime 等后端。

## 一、概述与定位

### 1.1 是什么
- DJL (Deep Java Library) 是 AWS 开源的深度学习 Java 框架，2019 年以 Apache 2.0 协议开源。
- 定位为 "Java 生态中的统一深度学习入口"，一套 API 可切换多种底层引擎。
- 核心思想：引擎无关（Engine Agnostic），开发者无需为切换 TF / PyTorch 改写业务代码。
- 名字 DJL 取自 Deep Java Library 首字母，强调在 JVM 上做深度学习的"标准库"愿景。

### 1.2 为什么需要它
- Java 深度学习长期痛点：
  - DL4J 自研后端，生态与 Python 主流模型不互通
  - 直接调 TensorFlow Java / PyTorch Java API 紧耦合，难切换
  - Python 进程间通信（Flask / TF Serving）带来部署与性能开销
- DJL 提供：
  - 统一的高层 API（训练 + 推理），风格与 PyTorch / TF 2.x 接近
  - Model Zoo 直接加载预训练模型（ResNet / MobileNet / BERT / SSD 等）
  - 原生 NDArray，与 NumPy 风格接近，支持自动求导
  - 自动选择可用引擎，可按需降级（PyTorch 优先 → MXNet → TF）

### 1.3 适用场景
- 企业 Java 后端做模型在线推理（图像分类、目标检测、NLP、推荐）
- 已有 TensorFlow / PyTorch 训练好的模型，希望在 JVM 内同进程加载，避免跨进程开销
- 需要在不同引擎间做 A/B 对比或灰度切换
- Spring Boot / Quarkus 微服务中嵌入深度学习能力
- 安卓端轻量推理（DJL 提供 Android 支持，可跑 MobileNet / 量化模型）

## 二、核心架构与概念

### 2.1 核心抽象
| 概念 | 说明 |
|------|------|
| Engine | 引擎抽象，对应 TF / PyTorch / MXNet / ONNX Runtime 等后端，单例 |
| Model | 加载后的模型，可创建 Predictor，封装权重与符号图 |
| Predictor | 推理器，线程安全（单实例可并发），输入数据返回预测结果 |
| Translator | 翻译器，把业务对象 ↔ NDArray 互转（预处理 + 后处理） |
| NDArray | 多维数组，引擎无关的张量操作 API，类似 NumPy ndarray |
| NDManager | NDArray 的内存管理器，管理原生资源生命周期，父子层级释放 |
| Model Zoo | 预训练模型仓库，按任务 / 引擎 / 架构检索 |
| Training | 训练 API（TrainingConfig / Trainer / EasyTrain / DefaultTrainingConfig） |
| Application | 任务抽象，如 ImageClassification / ObjectDetection / QuestionAnswering |

### 2.2 引擎无关设计
DJL 的关键设计：上层 API 不感知底层引擎。
```
Application (ResNet 图片分类)
        ↓
Model + Predictor + Translator   ← DJL 统一 API
        ↓
Engine (PyTorch / TensorFlow / MXNet / ONNX Runtime)
```
切换引擎只需更换 Maven 依赖与 `EngineName`，业务代码零改动。
`Engine` 通过 SPI（ServiceLoader）自动发现 classpath 上的引擎，调用 `Engine.getInstance()` 可拿到默认引擎，
`Engine.getEngine("PyTorch")` 可指定引擎。多引擎并存时按优先级自动选择。

### 2.3 Model Zoo 与 Criteria
DJL 内置多个 Model Zoo，按模型库组织：
- `ai.djl.mxnet` / `ai.djl.pytorch` / `ai.djl.tensorflow`：各引擎官方动物园
- `ai.djl.model-zoo`：跨引擎统一动物园，按 Application 检索
- 支持从 URL / 本地路径 / HuggingFace Hub 直接加载

检索统一用 `Criteria`（构建器模式），声明输入输出类型、Translator、引擎、模型来源：
```java
Criteria<Image, Classifications> criteria = Criteria.builder()
    .setTypes(Image.class, Classifications.class)
    .optModelUrls("file:///path/to/model")   // 或 ModelZoo
    .optTranslator(new MyTranslator())
    .optEngine("PyTorch")                    // 可选，默认自动
    .build();
try (Model model = criteria.loadModel();
     Predictor<Image, Classifications> predictor = model.newPredictor()) {
    Classifications result = predictor.predict(myImage);
}
```
`Criteria` 是 DJL 的"依赖注入"入口，便于在 Spring 中声明为 Bean。

### 2.4 NDArray 与 NDManager
`NDArray` 是引擎无关的张量，API 与 NumPy 高度对齐：
```java
NDManager manager = NDManager.newBaseManager();  // 根管理器
NDArray a = manager.create(new float[]{1, 2, 3, 4}, new Shape(2, 2));
NDArray b = a.transpose();
NDArray c = a.add(b).mul(2.0);
```
内存管理要点：
- 每个引擎的 NDArray 背后是原生内存（不归 GC 管），必须显式释放。
- `NDManager` 采用父子层级，`manager.newSubManager()` 创建子管理器，关闭父会级联关闭子。
- 推理热路径推荐 `try-with-resources` 包住子 manager，避免内存泄漏。
- `NDArray.attach_gradients()` 配合 `Trainer` 可做自动求导与训练。

---

## 三、多后端切换：TensorFlow / PyTorch / MXNet

DJL 的招牌能力是多后端无缝切换。三种主流引擎的依赖、特性、适用场景如下。

### 3.1 引擎依赖与配置
```xml
<!-- PyTorch 后端（推荐，模型生态最丰富） -->
<dependency>
  <groupId>ai.djl.pytorch</groupId>
  <artifactId>pytorch-engine</artifactId>
  <version>0.27.0</version>
</dependency>
<dependency>
  <groupId>ai.djl.pytorch</groupId>
  <artifactId>pytorch-native-auto</artifactId>
  <version>2.2.2</version>
  <classifier>osx-aarch64</classifier>  <!-- 按平台选 -->
</dependency>

<!-- TensorFlow 后端 -->
<dependency>
  <groupId>ai.djl.tensorflow</groupId>
  <artifactId>tensorflow-engine</artifactId>
  <version>0.27.0</version>
</dependency>

<!-- MXNet 后端（AWS 早期主推，现维护趋缓） -->
<dependency>
  <groupId>ai.djl.mxnet</groupId>
  <artifactId>mxnet-engine</artifactId>
  <version>0.27.0</version>
</dependency>
```
说明：
- 同时引入多个 engine 依赖时，DJL 按 SPI 优先级自动选默认引擎（PyTorch > MXNet > TensorFlow）。
- 可用 `-Dai.djl.default_engine=TensorFlow` 或 `Engine.getEngine("TensorFlow")` 显式指定。
- native 库按 OS / 架构自动选取，需为每个目标平台声明对应 classifier。

### 3.2 三引擎特性对比
| 维度 | PyTorch | TensorFlow | MXNet |
|------|---------|-----------|-------|
| 模型格式 | TorchScript (.pt/.pth) | SavedModel (.pb) | MXNet Params (.params) |
| 模型来源 | HuggingFace / TorchVision | TF Hub / Keras | Gluon Model Zoo |
| 训练 API | 支持 | 支持 | 支持 |
| 推理性能 | 中（可配 TensorRT） | 高（XLA / Serving 优化） | 高（符号图优化） |
| 社区活跃 | 最活跃 | 活跃 | 维护趋缓 |
| 移动端 | 支持 | 支持（Lite） | 支持 |
| 推荐场景 | NLP / 大模型推理 | 生产推理 / 移动端 | 老项目兼容 |

### 3.3 同模型多引擎 A/B
业务代码用 `Criteria` 加载，仅 `optEngine` 不同即可做 A/B：
```java
Criteria<Image, Classifications> base = Criteria.builder()
    .setTypes(Image.class, Classifications.class)
    .optModelUrls("file:///models/resnet50")
    .optTranslator(new ResNetTranslator())
    .optEngine("PyTorch");   // 切换为 "TensorFlow" 即可换后端
```
注意：跨引擎模型格式不通用（TorchScript ≠ SavedModel），需准备对应格式的模型文件；
DJL 不做格式转换，但 `ONNX Runtime` 后端可加载导出为 ONNX 的模型，作为通用中间格式。

### 3.4 ONNX Runtime 后端
当需要引擎无关的部署（如同时支持 Java / C# / Python 推理）时，把模型导出为 ONNX，用 DJL 的 ONNX Runtime 后端：
```xml
<dependency>
  <groupId>ai.djl.onnxruntime</groupId>
  <artifactId>onnxruntime-engine</artifactId>
  <version>0.27.0</version>
</dependency>
```
ONNX Runtime 后端不支持训练，仅推理，但跨平台、跨引擎兼容性最好。

---

## 四、模型推理实战：图片分类 ResNet

以 ResNet-50 图片分类为典型场景，演示 DJL 推理的完整链路：模型加载 → 图片预处理 → 推理 → 结果解析。

### 4.1 Maven 依赖
```xml
<dependency>
  <groupId>ai.djl</groupId>
  <artifactId>api</artifactId>
  <version>0.27.0</version>
</dependency>
<dependency>
  <groupId>ai.djl.pytorch</groupId>
  <artifactId>pytorch-engine</artifactId>
  <version>0.27.0</version>
</dependency>
<dependency>
  <groupId>ai.djl.pytorch</groupId>
  <artifactId>pytorch-model-zoo</artifactId>
  <version>0.27.0</version>
</dependency>
<dependency>
  <groupId>ai.djl</groupId>
  <artifactId>basicdataset</artifactId>
  <version>0.27.0</version>
</dependency>
```

### 4.2 Translator：预处理与后处理
DJL 的精髓是 `Translator`：把业务对象（Image）转成 NDArray 喂给模型，再把输出 NDArray 转成业务对象（Classifications）。
```java
public class ResNetTranslator implements NoopTranslator<Image, Classifications> {
    // 预处理：resize → 中心裁剪 → 归一化 → NCHW
    @Override
    public NDList processInput(TranslatorContext ctx, Image input) {
        NDManager manager = ctx.getNDManager();
        Image resized = input.resize(
            ImageNDUtils.centerCropResize(input, 224, 224));
        NDArray array = resized.toNDArray(manager, Image.Flag.COLOR);
        // HWC → CHW
        array = array.transpose(2, 0, 1);
        // 归一化：mean / std（ImageNet 标准）
        float[] mean = {0.485f, 0.456f, 0.406f};
        float[] std  = {0.229f, 0.224f, 0.225f};
        array = array.div(255f);
        array = array.sub(mean).div(std);
        return new NDList(array.expandDims(0));  // 加 batch 维
    }

    // 后处理：softmax → Top-K
    @Override
    public Classifications processOutput(TranslatorContext ctx, NDList list) {
        NDArray probabilities = list.singletonOrThrow().softmax(1);
        return new Classifications(LABELS, probabilities);
    }
}
```
也可直接用内置 `ImageClassificationTranslator.builder()`：
```java
Translator<Image, Classifications> translator =
    ImageClassificationTranslator.builder()
        .addTransform(new Resize(256))
        .addTransform(new CenterCrop(224, 224))
        .addTransform(new ToTensor())
        .build();
```
要点：
- 预处理必须与训练时一致（尺寸、归一化常量、通道顺序 NCHW / NHWC）。
- PyTorch 用 NCHW，TensorFlow 默认 NHWC，DJL 在 Translator 内自行对齐。
- 内置 `Transform` 体系（Resize / CenterCrop / ToTensor / Normalize）可组合复用。

### 4.3 加载模型与推理
```java
Criteria<Image, Classifications> criteria = Criteria.builder()
    .setTypes(Image.class, Classifications.class)
    .optModelUrls("file:///models/resnet50")    // 含 saved_model / synset.txt
    .optTranslator(translator)
    .optEngine("PyTorch")
    .build();

try (Model model = criteria.loadModel();
     Predictor<Image, Classifications> predictor = model.newPredictor()) {
    Image img = ImageFactory.getInstance().fromFile(Path.of("dog.jpg"));
    Classifications result = predictor.predict(img);
    List<Classifications.Item> top5 = result.topK(5);
    top5.forEach(i -> System.out.printf("%s : %.2f%%%n",
        i.getClassName(), i.getProbability() * 100));
}
```

### 4.4 性能与并发要点
- `Predictor` 是线程安全的，可单实例并发 `predict`（内部对 NDManager 加锁）。
- 高 QPS 场景建议预创建多个 `Predictor`，配合线程池并行批处理。
- 批处理：把多张图拼成一个 batch NDArray，一次 `predict` 提升吞吐。
- GPU：PyTorch / MXNet 后端通过 `Device.gpu()` 指定设备，需 CUDA 原生库。
- 预热：首次推理会触发图优化，建议服务启动后做一次 dummy 推理。

---

## 五、图片分类完整示例：可运行 Spring Boot 服务

把上面的链路封装成一个可运行的 Spring Boot REST 服务，体现 DJL 在生产中的典型用法。

### 5.1 服务入口与配置
```java
@SpringBootApplication
public class DjlImageApp {
    public static void main(String[] args) {
        SpringApplication.run(DjlImageApp.class, args);
    }
}
```
`application.yml`：
```yaml
djl:
  engine: PyTorch
  model-url: file:///models/resnet50
  labels: classpath:imagenet_classes.txt
```

### 5.2 模型 Bean（单例）
```java
@Configuration
public class DjlConfig {
    @Bean(destroyMethod = "close")
    public Predictor<Image, Classifications> predictor(
            @Value("${djl.engine}") String engine,
            @Value("${djl.model-url}") String modelUrl) throws Exception {
        Translator<Image, Classifications> t =
            ImageClassificationTranslator.builder()
                .addTransform(new Resize(256))
                .addTransform(new CenterCrop(224, 224))
                .addTransform(new ToTensor())
                .build();
        Criteria<Image, Classifications> criteria = Criteria.builder()
            .setTypes(Image.class, Classifications.class)
            .optModelUrls(modelUrl)
            .optTranslator(t)
            .optEngine(engine)
            .build();
        Model model = criteria.loadModel();
        return model.newPredictor();
    }
}
```
要点：`Predictor` 单例，Spring 容器关闭时调 `close` 释放原生资源。

### 5.3 Controller
```java
@RestController
public class ClassifyController {
    private final Predictor<Image, Classifications> predictor;
    public ClassifyController(Predictor<Image, Classifications> p) { this.predictor = p; }

    @PostMapping("/classify")
    public List<Map<String, Object>> classify(@RequestParam MultipartFile file) throws Exception {
        Image img = ImageFactory.getInstance().fromInputStream(file.getInputStream());
        Classifications result = predictor.predict(img);
        List<Classifications.Item> top5 = result.topK(5);
        return top5.stream().map(i -> Map.<String, Object>of(
            "class", i.getClassName(),
            "score", String.format("%.4f", i.getProbability())
        )).toList();
    }
}
```
调用：
```bash
curl -F "file=@dog.jpg" http://localhost:8080/classify
# [{"class":"golden_retriever","score":"0.9231"}, ...]
```

### 5.4 部署与运维
- 容器镜像需带上引擎 native 库（DJL 提供官方 `deepjavalibrary/djl-serving` 镜像）。
- 推理服务也可直接用 DJL 官方的 Model Server：`djl-serving`，支持多模型热加载、批量、指标。
- 监控：`predictor` 的延迟、QPS、NDManager 内存占用（`Engine.debugEnvironment()`）。
- 模型版本：通过 `modelUrl` 切换目录实现灰度，配合蓝绿部署。

---

## 六、面试要点（5 问）

**Q1：DJL 与 DL4J 的核心区别是什么？为什么选 DJL？**
答：DJL 是引擎无关的统一 API，背后可跑 PyTorch / TF / MXNet / ONNX Runtime，
直接复用 Python 训练的模型生态；DL4J 是自研后端，模型需用 DL4J 自己训练或转换，生态独立。
选 DJL 的核心原因是：能直接加载 PyTorch / TF 训练好的主流模型（ResNet / BERT 等），
切换引擎不改动业务代码，且 Apache 2.0 商用友好，与 Spring Boot 同进程部署省去跨进程开销。

**Q2：DJL 如何实现引擎无关？切换后端需要改什么？**
答：通过 `Engine` 抽象 + SPI（ServiceLoader）发现机制：上层 `Model` / `Predictor` / `NDArray`
都是引擎无关接口，底层各引擎实现自己的 `Engine` / `NDArray` 子类。
切换后端只需：① 更换 Maven engine 依赖（如 `pytorch-engine` → `tensorflow-engine`）；
② 准备对应格式的模型文件（TorchScript / SavedModel）；③ 在 `Criteria.optEngine(...)` 指定，
或用 `-Dai.djl.default_engine` 系统属性。业务代码、Translator 逻辑零改动。

**Q3：DJL 中 NDManager 的作用是什么？为什么重要？**
答：`NDManager` 是 NDArray 原生内存的生命周期管理器，采用父子层级结构。
因为引擎的 NDArray 背后是堆外原生内存，不归 Java GC 管，必须显式释放，否则内存泄漏。
父 manager 关闭会级联关闭所有子 manager 及其下 NDArray。
最佳实践：推理热路径用 `try-with-resources` 包住子 manager，根 manager 长驻服务生命周期；
避免在循环里反复创建根 manager，也避免 NDArray 跨 manager 引用导致提前释放。

**Q4：用 DJL 做图片分类，预处理有哪些关键步骤？为什么？**
答：核心五步：① Resize 到模型输入尺寸（如 256）；② CenterCrop 到目标尺寸（224×224）；
③ HWC → CHW 调整通道顺序（PyTorch 要求）；④ 像素值归一化到 [0,1]（除以 255）；
⑤ 用 ImageNet 均值方差做标准化（mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]）。
原因：预处理必须与训练时完全一致，否则分布偏移导致预测错乱；
DJL 用 `Translator` 封装这些步骤，内置 `Transform`（Resize / CenterCrop / ToTensor / Normalize）可组合复用。

**Q5：在生产环境用 DJL 部署推理服务有哪些最佳实践？**
答：① `Predictor` 注册为单例 Bean，配合 Spring 容器关闭释放原生资源；
② 服务启动后做一次 dummy 推理预热，避免首请求触发图优化延迟抖动；
③ 高 QPS 用多 `Predictor` + 线程池并行，或用 batch 推理提升吞吐；
④ GPU 场景用 `Device.gpu()`，注意 native 库与 CUDA 版本匹配；
⑤ 模型版本通过 `modelUrl` 目录切换做灰度，结合蓝绿 / 金丝雀发布；
⑥ 大型部署直接用 `djl-serving` Model Server，自带多模型热加载、批量聚合、Prometheus 指标；
⑦ 监控 NDManager 内存占用与推理延迟，防止原生内存泄漏。

---

## 七、相关阅读

- 官方仓库：https://github.com/deepjavalibrary/djl
- 官方文档：https://docs.djl.ai/
- DJL Model Zoo：https://docs.djl.ai/master/docs/model-zoo.html
- PyTorch 后端文档：https://docs.djl.ai/master/docs/engines/pytorch.html
- TensorFlow 后端文档：https://docs.djl.ai/master/docs/engines/tensorflow.html
- MXNet 后端文档：https://docs.djl.ai/master/docs/engines/mxnet.html
- ONNX Runtime 后端：https://docs.djl.ai/master/docs/engines/onnxruntime.html
- DJL Serving（模型服务器）：https://github.com/deepjavalibrary/djl-serving
- HuggingFace 模型加载：https://docs.djl.ai/master/docs/load_model.html#load-model-from-hugging-face
- 图片分类官方示例：https://github.com/deepjavalibrary/djl/tree/master/examples/src/main/java/ai/djl/examples/inference
- ImageClassificationTranslator API：https://javadoc.io/doc/ai.djl/api/latest/ai/djl/modality/cv/translator/ImageClassificationTranslator.html
- NDArray / NDManager 设计：https://docs.djl.ai/master/docs/developer_guide/ndarray.html
- AWS 官方博客首发：https://aws.amazon.com/blogs/opensource/introducing-djl-deep-java-library-and-d2l/
- 与 DL4J 对比讨论：DJL 重在引擎统一与模型生态复用，DL4J 重在自研训练栈与分布式
- 中文社区简介：Java 生态深度学习推理的事实标准之一，企业 JVM 在线推理首选

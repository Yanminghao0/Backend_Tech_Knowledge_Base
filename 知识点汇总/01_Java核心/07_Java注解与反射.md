# Java注解与反射

> 注解是元数据的载体，反射是运行时透视——框架底层的两大基石

---

## 📋 目录

1. [注解基础](#1-注解基础)
2. [元注解](#2-元注解)
3. [自定义注解](#3-自定义注解)
4. [反射API详解](#4-反射api详解)
5. [反射性能优化](#5-反射性能优化)
6. [注解处理器（APT）](#6-注解处理器apt)
7. [实战场景](#7-实战场景)
8. [面试题速查](#8-面试题速查)

---

## 1. 注解基础

### 1.1 什么是注解

```
注解（Annotation）= 代码中的元数据标记

作用：
  - 编译检查：@Override 检查方法重写
  - 代码生成：@Getter @Setter 自动生成代码
  - 运行时处理：@Autowired 依赖注入
  - 配置替代：@RequestMapping 替代XML配置

注解的本质：
  - 注解是一种接口，继承java.lang.annotation.Annotation
  - 编译后生成 interface XXX extends Annotation
  - 运行时通过反射获取注解信息

Java内置注解：
  @Override    → 检查方法重写
  @Deprecated  → 标记已过时
  @SuppressWarnings → 抑制警告
  @FunctionalInterface → 函数式接口标记
```

### 1.2 注解的分类

```
按生命周期分（RetentionPolicy）：
  1. SOURCE：仅源码中存在，编译后丢弃（@Override @SuppressWarnings）
  2. CLASS：编译到class文件中，运行时不可见（默认策略，较少使用）
  3. RUNTIME：运行时可通过反射读取（@Autowired @RequestMapping）

按来源分：
  1. 内置注解：Java SDK提供（@Override @Deprecated）
  2. 元注解：注解注解的注解（@Target @Retention @Inherited）
  3. 自定义注解：开发者自定义
  4. 框架注解：Spring/Lombok/Jackson等提供
```

---

## 2. 元注解

### 2.1 五大元注解

```java
/**
 * @Target: 注解可以应用的位置
 *   ElementType.TYPE        → 类、接口、枚举
 *   ElementType.FIELD       → 字段
 *   ElementType.METHOD      → 方法
 *   ElementType.PARAMETER   → 参数
 *   ElementType.CONSTRUCTOR → 构造方法
 *   ElementType.LOCAL_VARIABLE → 局部变量
 *   ElementType.ANNOTATION_TYPE → 注解类型
 *   ElementType.PACKAGE     → 包
 *   ElementType.TYPE_PARAMETER → 类型参数（Java 8+）
 *   ElementType.TYPE_USE    → 类型使用（Java 8+）
 */

/**
 * @Retention: 注解的保留策略
 *   RetentionPolicy.SOURCE  → 仅源码（编译后丢弃）
 *   RetentionPolicy.CLASS   → class文件（默认，运行时不可见）
 *   RetentionPolicy.RUNTIME → 运行时（反射可读）
 */

/**
 * @Documented: 注解包含在Javadoc中
 */

/**
 * @Inherited: 子类自动继承父类的注解
 *   注意：只对类继承有效，对接口实现无效
 */

/**
 * @Repeatable: 同一位置可重复使用（Java 8+）
 */
```

### 2.2 元注解使用示例

```java
// 定义一个运行时可读取的注解，用于方法上
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface MyAnnotation {
    String value() default "";
    String[] tags() default {};
}

// @Inherited示例
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Inherited
public @interface InheritedAnnotation {
    String value();
}

@InheritedAnnotation("parent")
public class Parent {}
public class Child extends Parent {}
// Child自动继承@InheritedAnnotation("parent")

// @Repeatable示例
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@Repeatable(Schedules.class)
public @interface Schedule {
    String cron();
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Schedules {
    Schedule[] value();
}

// 使用：同一方法多个@Schedule
@Schedule(cron = "0 0 * * *")
@Schedule(cron = "0 30 * * *")
public void runTask() {}
```

---

## 3. 自定义注解

### 3.1 注解定义语法

```java
// 注解定义 = @interface + 属性方法
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Table {
    String name() default "";  // 属性方法，default指定默认值
}

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Column {
    String name() default "";
    boolean nullable() default true;
    int length() default 255;
}

// 使用注解
@Table(name = "t_user")
public class User {
    @Column(name = "user_id", length = 36)
    private String userId;
    
    @Column(name = "user_name", nullable = false, length = 50)
    private String userName;
    
    @Column(name = "age")
    private Integer age;
}
```

### 3.2 注解属性规则

```java
public @interface Example {
    // 1. 属性类型只能是：基本类型、String、Class、枚举、注解、以上类型的数组
    int count();                    // 基本类型 ✓
    String name();                  // String  ✓
    Class<?> clazz();               // Class   ✓
    MyEnum mode();                  // 枚举    ✓
    MyAnnotation config();          // 注解    ✓
    String[] tags();                // 数组    ✓
    // List<String> list();         // ❌ 不支持
    
    // 2. 属性可以有默认值
    String value() default "default";
    
    // 3. 特殊属性名 value()
    //    如果只有一个属性且名为value，使用时可省略属性名
    //    @Example("test") 等价于 @Example(value = "test")
}
```

---

## 4. 反射API详解

### 4.1 获取Class对象

```java
// 三种获取Class对象的方式
// 1. 类名.class（编译时已知）
Class<String> clazz1 = String.class;

// 2. 实例.getClass()（运行时已知）
String str = "hello";
Class<?> clazz2 = str.getClass();

// 3. Class.forName()（动态加载）
Class<?> clazz3 = Class.forName("java.lang.String");

// 三种方式获取的是同一个Class对象（同一个类加载器下）
System.out.println(clazz1 == clazz2);  // true
System.out.println(clazz2 == clazz3);  // true
```

### 4.2 反射操作Class信息

```java
Class<?> clazz = User.class;

// 类基本信息
String name = clazz.getName();           // com.example.User
String simpleName = clazz.getSimpleName(); // User
int modifiers = clazz.getModifiers();    // 修饰符
Modifier.isPublic(modifiers);            // true
Package pkg = clazz.getPackage();        // com.example
Class<?> superClass = clazz.getSuperclass(); // 父类
Class<?>[] interfaces = clazz.getInterfaces(); // 实现的接口

// 获取注解
Table table = clazz.getAnnotation(Table.class);
String tableName = table.name();         // "t_user"
Annotation[] annotations = clazz.getAnnotations();
boolean hasTable = clazz.isAnnotationPresent(Table.class);
```

### 4.3 反射操作Field

```java
Class<?> clazz = User.class;

// 获取字段
Field[] fields = clazz.getDeclaredFields();  // 所有字段（含private）
Field[] publicFields = clazz.getFields();      // 仅public字段（含继承的）
Field field = clazz.getDeclaredField("userName");  // 指定字段

// 字段信息
String fieldName = field.getName();       // "userName"
Class<?> fieldType = field.getType();     // String.class
int mods = field.getModifiers();          // 修饰符
Column column = field.getAnnotation(Column.class);

// 读写字段值
User user = new User("u001", "Alice", 25);
field.setAccessible(true);  // 访问private字段需设置
String value = (String) field.get(user);  // 读取
field.set(user, "Bob");                    // 写入

// 批量反射字段示例
for (Field f : clazz.getDeclaredFields()) {
    f.setAccessible(true);
    Column col = f.getAnnotation(Column.class);
    if (col != null) {
        String columnName = col.name().isEmpty() ? f.getName() : col.name();
        Object columnValue = f.get(user);
        System.out.println(columnName + " = " + columnValue);
    }
}
```

### 4.4 反射操作Method

```java
Class<?> clazz = User.class;

// 获取方法
Method[] methods = clazz.getDeclaredMethods();  // 所有方法（含private）
Method[] publicMethods = clazz.getMethods();      // public方法（含继承的）
Method method = clazz.getDeclaredMethod("setName", String.class);  // 指定方法

// 方法信息
String methodName = method.getName();      // "setName"
Class<?>[] paramTypes = method.getParameterTypes();  // 参数类型
Class<?> returnType = method.getReturnType();        // 返回类型
Class<?>[] exceptions = method.getExceptionTypes();  // 异常类型

// 调用方法
User user = new User("u001", "Alice", 25);
method.setAccessible(true);  // private方法需设置
Object result = method.invoke(user, "Bob");  // user.setName("Bob")

// 调用静态方法
Method staticMethod = clazz.getDeclaredMethod("createUser", String.class);
staticMethod.setAccessible(true);
User newUser = (User) staticMethod.invoke(null, "u002");  // 静态方法，obj传null
```

### 4.5 反射操作Constructor

```java
Class<?> clazz = User.class;

// 获取构造方法
Constructor<?>[] constructors = clazz.getDeclaredConstructors();
Constructor<?> constructor = clazz.getDeclaredConstructor(String.class, String.class, int.class);

// 创建实例
constructor.setAccessible(true);
User user = (User) constructor.newInstance("u001", "Alice", 25);

// 无参构造（快捷方式）
User user2 = clazz.getDeclaredConstructor().newInstance();  // Java 9+推荐
// 旧方式（已废弃）：clazz.newInstance()
```

### 4.6 反射操作泛型

```java
// 获取字段的泛型类型
Field field = MyClass.class.getDeclaredField("list");
Type genericType = field.getGenericType();
if (genericType instanceof ParameterizedType) {
    ParameterizedType pt = (ParameterizedType) genericType;
    Type[] typeArgs = pt.getActualTypeArguments();
    System.out.println(typeArgs[0]);  // class java.lang.String
}

// 获取方法的泛型参数和返回值
Method method = MyClass.class.getDeclaredMethod("getMap");
Type returnType = method.getGenericReturnType();
```

---

## 5. 反射性能优化

### 5.1 反射的性能开销

```
反射操作比直接调用慢约10-50倍，原因：
  1. 方法查找：需要遍历方法表
  2. 安全检查：每次调用检查权限
  3. 参数装箱：基本类型需要装箱
  4. JIT优化受限：反射调用难以内联优化

性能对比（1亿次调用）：
  直接调用:        ~50ms
  反射调用:        ~2000ms（40x）
  setAccessible后: ~1500ms（30x）
```

### 5.2 优化方案

```java
// 1. 缓存反射对象（避免重复查找）
public class ReflectionCache {
    private static final ConcurrentHashMap<String, Method> METHOD_CACHE 
        = new ConcurrentHashMap<>();
    
    public static Method getMethod(Class<?> clazz, String name, Class<?>... params) {
        String key = clazz.getName() + "#" + name;
        return METHOD_CACHE.computeIfAbsent(key, k -> {
            try {
                Method m = clazz.getDeclaredMethod(name, params);
                m.setAccessible(true);
                return m;
            } catch (NoSuchMethodException e) {
                throw new RuntimeException(e);
            }
        });
    }
}

// 2. setAccessible(true) 减少安全检查
method.setAccessible(true);  // 跳过权限检查，提升约20-30%

// 3. MethodHandle（Java 7+，接近直接调用的性能）
MethodHandles.Lookup lookup = MethodHandles.lookup();
MethodHandle mh = lookup.findVirtual(User.class, "setName", 
    MethodType.methodType(void.class, String.class));
mh.invoke(user, "Bob");  // 性能接近直接调用

// 4. Lambda元工厂（Java 8+，动态生成接口实现）
MethodHandles.Lookup lookup = MethodHandles.lookup();
MethodHandle mh = lookup.findVirtual(User.class, "getName",
    MethodType.methodType(String.class));
Supplier<String> supplier = (Supplier<String>) LambdaMetafactory.metafactory(
    lookup, "get", MethodType.methodType(Supplier.class, User.class),
    MethodType.methodType(String.class), mh, MethodType.methodType(String.class)
).getTarget().invoke(user);
String name = supplier.get();  // JIT可优化为直接调用

// 5. 字节码生成（ASM/CGLib，最快）
// CGLib通过动态生成字节码创建代理类，反射调用转为直接调用
// Spring AOP默认使用CGLib

// 6. 使用ReflectionFactory绕过安全检查（谨慎使用）
ReflectionFactory factory = ReflectionFactory.getReflectionFactory();
// 可以创建不进行安全检查的MethodAccessor
```

### 5.3 框架中的优化实践

```java
// Spring的ReflectiveMethodAccessor优化策略：
// 1. 前15次使用NativeMethodAccessorImpl（JNI调用，慢）
// 2. 第16次后生成GeneratedMethodAccessor（字节码生成，快）
// 阈值: -Dsun.reflect.inflationThreshold=15

// Spring缓存优化：
// org.springframework.util.ReflectionUtils 缓存 Method 对象
// org.springframework.reflect.support 加速字段/方法访问

// MyBatis的反射优化：
// Reflector类缓存Class的反射信息
// 避免每次操作都重新查找Field/Method
```

---

## 6. 注解处理器（APT）

### 6.1 APT原理

```
注解处理器（Annotation Processing Tool）

工作阶段：
  编译期 → 注解处理器扫描注解 → 生成代码/修改代码

特点：
  1. 编译时处理，不影响运行时性能
  2. 可以生成新的Java文件
  3. 不能修改已有文件（但可以通过Lombok技巧实现）

应用：
  - Lombok: @Getter/@Setter 编译时生成方法
  - ButterKnife: @BindView 生成View绑定代码
  - Dagger: @Inject 生成依赖注入代码
  - MapStruct: @Mapper 生成对象转换代码
```

### 6.2 自定义注解处理器

```java
// 1. 定义注解
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.SOURCE)  // APT只需SOURCE级别
public @interface Builder {
}

// 2. 实现注解处理器
@SupportedAnnotationTypes("com.example.Builder")
@SupportedSourceVersion(SourceVersion.RELEASE_17)
public class BuilderProcessor extends AbstractProcessor {
    
    @Override
    public boolean process(Set<? extends TypeElement> annotations,
                           RoundEnvironment roundEnv) {
        // 遍历标注了@Builder的类
        for (Element element : roundEnv.getElementsAnnotatedWith(Builder.class)) {
            TypeElement typeElement = (TypeElement) element;
            String className = typeElement.getSimpleName().toString();
            String packageName = processingEnv.getElementUtils()
                .getPackageOf(typeElement).getQualifiedName().toString();
            
            // 生成Builder类
            try {
                JavaFileObject file = processingEnv.getFiler()
                    .createSourceFile(packageName + "." + className + "Builder");
                
                try (PrintWriter writer = new PrintWriter(file.openWriter())) {
                    writer.println("package " + packageName + ";");
                    writer.println("public class " + className + "Builder {");
                    
                    // 为每个字段生成setter
                    for (Element field : typeElement.getEnclosedElements()) {
                        if (field.getKind() == ElementKind.FIELD) {
                            String fieldName = field.getSimpleName().toString();
                            String fieldType = field.asType().toString();
                            writer.println("  private " + fieldType + " " + fieldName + ";");
                            writer.println("  public " + className + "Builder " + 
                                fieldName + "(" + fieldType + " " + fieldName + ") {");
                            writer.println("    this." + fieldName + " = " + fieldName + ";");
                            writer.println("    return this;");
                            writer.println("  }");
                        }
                    }
                    
                    writer.println("  public " + className + " build() {");
                    writer.println("    " + className + " obj = new " + className + "();");
                    // ... 设置字段
                    writer.println("    return obj;");
                    writer.println("  }");
                    writer.println("}");
                }
            } catch (IOException e) {
                processingEnv.getMessager().printMessage(
                    Diagnostic.Message.ERROR, e.getMessage());
            }
        }
        return true;
    }
}

// 3. 注册注解处理器
// 在META-INF/services/javax.annotation.processing.Processor文件中：
// com.example.BuilderProcessor
```

---

## 7. 实战场景

### 7.1 自定义ORM框架

```java
// 注解定义
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Table {
    String name();
}

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Column {
    String name();
    boolean primaryKey() default false;
}

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Id {
    boolean autoGenerate() default true;
}

// 实体类
@Table(name = "t_user")
public class User {
    @Id
    @Column(name = "id", primaryKey = true)
    private Long id;
    
    @Column(name = "username")
    private String username;
    
    @Column(name = "email")
    private String email;
    
    // getters/setters...
}

// ORM框架核心：通过反射+注解生成SQL
public class SimpleORM {
    
    public String buildInsertSQL(Object entity) throws Exception {
        Class<?> clazz = entity.getClass();
        Table table = clazz.getAnnotation(Table.class);
        String tableName = table.name();
        
        List<String> columns = new ArrayList<>();
        List<String> values = new ArrayList<>();
        
        for (Field field : clazz.getDeclaredFields()) {
            field.setAccessible(true);
            Column column = field.getAnnotation(Column.class);
            if (column != null) {
                columns.add(column.name());
                Object value = field.get(entity);
                if (value instanceof String) {
                    values.add("'" + value + "'");
                } else {
                    values.add(String.valueOf(value));
                }
            }
        }
        
        return String.format("INSERT INTO %s (%s) VALUES (%s)",
            tableName,
            String.join(", ", columns),
            String.join(", ", values));
    }
    
    public <T> T mapResultSet(ResultSet rs, Class<T> clazz) throws Exception {
        T entity = clazz.getDeclaredConstructor().newInstance();
        for (Field field : clazz.getDeclaredFields()) {
            field.setAccessible(true);
            Column column = field.getAnnotation(Column.class);
            if (column != null) {
                Object value = rs.getObject(column.name());
                field.set(entity, value);
            }
        }
        return entity;
    }
}
```

### 7.2 参数校验框架

```java
// 校验注解
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface NotNull {
    String message() default "不能为空";
}

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Length {
    int min() default 0;
    int max() default Integer.MAX_VALUE;
    String message() default "长度不合法";
}

@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface Range {
    long min() default Long.MIN_VALUE;
    long max() default Long.MAX_VALUE;
    String message() default "数值范围不合法";
}

// 校验对象
public class UserRequest {
    @NotNull(message = "用户名不能为空")
    @Length(min = 3, max = 20, message = "用户名长度3-20")
    private String username;
    
    @Range(min = 0, max = 150, message = "年龄必须在0-150之间")
    private Integer age;
    
    @NotNull(message = "邮箱不能为空")
    private String email;
}

// 校验框架核心
public class Validator {
    public static List<String> validate(Object obj) throws Exception {
        List<String> errors = new ArrayList<>();
        Class<?> clazz = obj.getClass();
        
        for (Field field : clazz.getDeclaredFields()) {
            field.setAccessible(true);
            Object value = field.get(obj);
            
            // @NotNull校验
            if (field.isAnnotationPresent(NotNull.class)) {
                if (value == null) {
                    errors.add(field.getAnnotation(NotNull.class).message());
                    continue;
                }
            }
            
            // @Length校验
            if (field.isAnnotationPresent(Length.class) && value instanceof String) {
                Length length = field.getAnnotation(Length.class);
                String strValue = (String) value;
                if (strValue.length() < length.min() || strValue.length() > length.max()) {
                    errors.add(length.message());
                }
            }
            
            // @Range校验
            if (field.isAnnotationPresent(Range.class) && value instanceof Number) {
                Range range = field.getAnnotation(Range.class);
                long numValue = ((Number) value).longValue();
                if (numValue < range.min() || numValue > range.max()) {
                    errors.add(range.message());
                }
            }
        }
        return errors;
    }
}
```

### 7.3 简易路由框架

```java
// 路由注解
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
public @interface Controller {
    String path() default "";
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface GetMapping {
    String value();
}

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface PostMapping {
    String value();
}

// 控制器
@Controller(path = "/api/users")
public class UserController {
    @GetMapping("/list")
    public String list() {
        return "user list";
    }
    
    @PostMapping("/create")
    public String create() {
        return "user created";
    }
}

// 路由扫描与分发
public class Router {
    private final Map<String, MethodHandler> routes = new HashMap<>();
    
    public void scan(String basePackage) throws Exception {
        // 扫描包下所有带@Controller的类
        Set<Class<?>> classes = ClassScanner.scan(basePackage);
        
        for (Class<?> clazz : classes) {
            if (!clazz.isAnnotationPresent(Controller.class)) continue;
            
            Controller ctrl = clazz.getAnnotation(Controller.class);
            String basePath = ctrl.path();
            Object instance = clazz.getDeclaredConstructor().newInstance();
            
            for (Method method : clazz.getDeclaredMethods()) {
                if (method.isAnnotationPresent(GetMapping.class)) {
                    String path = basePath + method.getAnnotation(GetMapping.class).value();
                    routes.put("GET " + path, new MethodHandler(instance, method));
                }
                if (method.isAnnotationPresent(PostMapping.class)) {
                    String path = basePath + method.getAnnotation(PostMapping.class).value();
                    routes.put("POST " + path, new MethodHandler(instance, method));
                }
            }
        }
    }
    
    public Object dispatch(String httpMethod, String path, Object... args) throws Exception {
        MethodHandler handler = routes.get(httpMethod + " " + path);
        if (handler == null) {
            throw new RuntimeException("No route: " + httpMethod + " " + path);
        }
        return handler.invoke(args);
    }
    
    static class MethodHandler {
        final Object instance;
        final Method method;
        
        MethodHandler(Object instance, Method method) {
            this.instance = instance;
            this.method = method;
            method.setAccessible(true);
        }
        
        Object invoke(Object... args) throws Exception {
            return method.invoke(instance, args);
        }
    }
}
```

---

## 8. 面试题速查

### Q1: 注解的本质是什么？

```
注解本质是一个继承Annotation接口的接口。
编译后生成 interface XXX extends Annotation {}
运行时通过反射获取注解信息。
注解本身不包含逻辑，逻辑由处理注解的代码实现。
```

### Q2: @Retention的三个策略区别？

```
SOURCE: 仅源码中存在，编译后丢弃（如@Override）
CLASS:  编译到class文件，JVM运行时不可见（默认值）
RUNTIME: 运行时可通过反射读取（如Spring注解）

框架注解通常使用RUNTIME，编译时注解处理器使用SOURCE。
```

### Q3: 反射的性能问题及优化方案？

```
性能问题：
  1. 方法查找开销
  2. 安全检查开销
  3. 参数装箱
  4. JIT优化受限

优化方案：
  1. 缓存Method/Field对象
  2. setAccessible(true)跳过安全检查
  3. MethodHandle（Java 7+）
  4. LambdaMetafactory（Java 8+）
  5. 字节码生成（CGLib/ASM）
  6. Spring的inflation机制（前15次JNI，之后生成字节码）
```

### Q4: @Inherited的作用和局限性？

```
作用：子类自动继承父类标注的@Inherited注解

局限性：
  1. 只对类继承有效，对接口实现无效
  2. 只对@Target(TYPE)的注解有效
  3. 子类自己标注同名注解会覆盖父类的
```

### Q5: 编译时注解处理器（APT）和运行时反射的区别？

```
APT（编译时）：
  - 编译期处理，不影响运行时性能
  - 可生成新代码（如Lombok生成getter）
  - 适用于代码生成场景
  - @Retention通常为SOURCE

运行时反射：
  - 运行时通过反射读取注解
  - 有性能开销
  - 适用于框架动态处理（如Spring IoC）
  - @Retention必须为RUNTIME
```

### Q6: 如何通过反射创建对象实例？

```
// 方式1: 无参构造
Object obj = clazz.getDeclaredConstructor().newInstance();

// 方式2: 有参构造
Constructor<?> constructor = clazz.getDeclaredConstructor(String.class, int.class);
constructor.setAccessible(true);
Object obj = constructor.newInstance("Alice", 25);

// 注意：
// - Java 9+推荐用getDeclaredConstructor().newInstance()
// - 旧方式clazz.newInstance()已废弃
// - private构造方法需要setAccessible(true)
```

### Q7: 什么是MethodHandle？比反射有什么优势？

```
MethodHandle（Java 7+）是对方法调用的低级抽象

优势：
  1. 性能接近直接调用（JIT可优化）
  2. 类型安全（编译时检查签名）
  3. 支持invokedynamic指令

对比：
  反射Method.invoke: ~2000ms / 1亿次调用
  MethodHandle:      ~100ms / 1亿次调用
  直接调用:            ~50ms / 1亿次调用
```

---

## 📚 相关阅读

- [01_Java基础核心](./01_Java基础核心.md)
- [03_集合框架核心](./03_集合框架核心.md)
- [04_并发编程核心](./04_并发编程核心.md)

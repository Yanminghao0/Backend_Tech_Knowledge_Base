# Java异常处理最佳实践

> 异常体系/自定义异常/异常链/全局异常处理的完整方案

---

## 📋 目录

1. [异常体系](#1-异常体系)
2. [异常处理原则](#2-异常处理原则)
3. [自定义异常设计](#3-自定义异常设计)
4. [全局异常处理](#4-全局异常处理)
5. [面试题速查](#5-面试题速查)

---

## 1. 异常体系

```
Throwable
  ├── Error（不应捕获）
  │    ├── OutOfMemoryError
  │    ├── StackOverflowError
  │    └── NoClassDefFoundError
  └── Exception
       ├── RuntimeException（非受检，可不catch）
       │    ├── NullPointerException
       │    ├── IllegalArgumentException
       │    ├── ClassCastException
       │    ├── ArrayIndexOutOfBoundsException
       │    └── ArithmeticException
       └── 其他Exception（受检，必须catch或throws）
            ├── IOException
            ├── SQLException
            └── ClassNotFoundException

受检异常 vs 非受检异常：
  受检异常：编译器强制处理（try-catch/throws），表示可恢复的外部条件
  非受检异常：编译器不强制，表示编程错误
```

---

## 2. 异常处理原则

```java
// 原则1：不要捕获不处理的异常
// ❌ 错误
try {
    doSomething();
} catch (Exception e) {
    e.printStackTrace();  // 吞掉异常，不处理
}
// ✅ 正确
try {
    doSomething();
} catch (Exception e) {
    log.error("操作失败", e);
    throw new BusinessException("操作失败，请重试", e);
}

// 原则2：不要catch Throwable
// ❌ 错误：会捕获Error（如OOM），不应处理
try { ... } catch (Throwable t) { ... }

// 原则3：精确捕获，不要catch Exception
// ❌ 错误
try {
    readFile();
    parseInt();
} catch (Exception e) { ... }  // 不知道哪个出错了
// ✅ 正确
try {
    readFile();
} catch (IOException e) { ... }
try {
    parseInt();
} catch (NumberFormatException e) { ... }

// 原则4：finally中不要return
// ❌ finally的return会覆盖try的return
try {
    return 1;
} finally {
    return 2;  // 返回2，不是1！
}

// 原则5：try-with-resources自动关闭
try (BufferedReader br = new BufferedReader(new FileReader("file.txt"))) {
    return br.readLine();
}  // 自动调用br.close()，即使出异常也会关闭

// 原则6：异常不要用于流程控制
// ❌ 用异常控制流程
try {
    User user = userService.findById(id);
    // findById抛UserNotFoundException
} catch (UserNotFoundException e) {
    return "用户不存在";
}
// ✅ 用返回值
User user = userService.findById(id);
if (user == null) {
    return "用户不存在";
}
```

---

## 3. 自定义异常设计

```java
// 业务异常基类
public class BusinessException extends RuntimeException {
    private int code;
    private String message;
    
    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }
    
    public BusinessException(int code, String message, Throwable cause) {
        super(message, cause);  // 保留异常链
        this.code = code;
        this.message = message;
    }
    
    public int getCode() { return code; }
}

// 具体业务异常
public class UserNotFoundException extends BusinessException {
    public UserNotFoundException(Long userId) {
        super(40401, "用户不存在: " + userId);
    }
}

public class InsufficientBalanceException extends BusinessException {
    public InsufficientBalanceException(Long userId, BigDecimal amount) {
        super(40001, String.format("用户%d余额不足，需要%s", userId, amount));
    }
}

public class DuplicateException extends BusinessException {
    public DuplicateException(String resource, String key) {
        super(40901, resource + "已存在: " + key);
    }
}

// 异常码设计：
// 4xx: 客户端错误
//   400xx: 参数错误
//   401xx: 认证错误
//   403xx: 授权错误
//   404xx: 资源不存在
//   409xx: 冲突
// 5xx: 服务端错误
//   500xx: 系统异常
//   503xx: 熔断降级
```

---

## 4. 全局异常处理

```java
// Spring Boot全局异常处理
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);
    
    // 业务异常
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Result<Void>> handleBusiness(BusinessException e) {
        log.warn("业务异常: code={}, msg={}", e.getCode(), e.getMessage());
        return ResponseEntity
            .status(HttpStatus.OK)
            .body(Result.fail(e.getCode(), e.getMessage()));
    }
    
    // 参数校验异常
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Result<Void>> handleValidation(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
            .map(f -> f.getField() + ": " + f.getDefaultMessage())
            .collect(Collectors.joining("; "));
        return ResponseEntity.ok(Result.fail(40000, msg));
    }
    
    // 权限异常
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<Result<Void>> handleAccessDenied(AccessDeniedException e) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
            .body(Result.fail(40300, "无权限访问"));
    }
    
    // 兜底异常
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Result<Void>> handleException(Exception e) {
        log.error("系统异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Result.fail(50000, "系统繁忙，请稍后重试"));
    }
}

// 统一返回结构
@Data
public class Result<T> {
    private int code;
    private String msg;
    private T data;
    
    public static <T> Result<T> ok(T data) {
        Result<T> r = new Result<>();
        r.code = 200;
        r.msg = "success";
        r.data = data;
        return r;
    }
    
    public static <T> Result<T> fail(int code, String msg) {
        Result<T> r = new Result<>();
        r.code = code;
        r.msg = msg;
        return r;
    }
}
```

---

## 5. 面试题速查

**Q1: checked和unchecked异常的区别？**
```
checked：编译器强制处理（try-catch/throws），如IOException
unchecked：编译器不强制，如NullPointerException
阿里规范：不要用checked异常，用RuntimeException+全局异常处理
```

**Q2: throw和throws的区别？**
```
throw：抛出异常对象（方法体内）
throws：声明可能抛出的异常（方法签名上）
throw new BusinessException("xxx");
public void readFile() throws IOException { ... }
```

**Q3: try-with-resources原理？**
```
Java 7+语法，自动调用AutoCloseable.close()
编译后等价于try-finally，但更简洁
即使try块抛异常，资源也会先关闭再抛出
```

**Q4: 异常链的作用？**
```
保留原始异常信息，避免信息丢失
new BusinessException("新消息", originalException)
getCause()可以获取原始异常
适用场景：低层异常翻译为业务异常时保留原因
```

---

*最后更新：2026-07-13*

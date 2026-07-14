# Java基础核心原理详解

> 从底层原理深入理解Java基础，面向高级开发工程师

---

## 📚 目录

1. [Java语言特性](#1-java语言特性)
   - JDK、JRE、JVM关系
   - 核心特性（WORA、GC、OOP）
   - Java程序执行流程
2. [面向对象核心](#2-面向对象核心)
   - 封装、继承、多态
   - 抽象类与接口
   - 内部类
3. [Java类型系统](#3-java类型系统)
   - 基本类型与包装类
   - 对象内存布局
   - 引用类型（强、软、弱、虚）
4. [字符串深度解析](#4-字符串深度解析)
   - String核心特性
   - 字符串常量池
   - 性能优化
   - 正则表达式
5. [集合框架核心原理](#5-集合框架核心原理)
   - ArrayList、LinkedList
   - HashMap、LinkedHashMap、TreeMap
   - ConcurrentHashMap
6. [异常处理机制](#6-异常处理机制)
7. [Java IO体系](#7-java-io体系)
8. [反射机制](#8-反射机制)
9. [泛型原理](#9-泛型原理)
10. [注解与处理器](#10-注解与处理器)
11. [Lambda与Stream API](#11-lambda与stream-api)
    - Lambda表达式
    - 方法引用
    - Stream API中间操作与终端操作
12. [Java新特性总结](#12-java新特性总结)
    - JDK 8-17主要特性
    - JDK 18-21新特性（Virtual Threads、Record模式匹配、Switch模式匹配、顺序集合等）
    - JDK 22-23新特性

---

## 1. Java语言特性

### 1.1 Java平台架构

```
┌─────────────────────────────────────┐
│      Java Application               │  应用程序
├─────────────────────────────────────┤
│      Java API (JDK)                 │  核心类库
├─────────────────────────────────────┤
│      JVM (Java Virtual Machine)     │  虚拟机
├─────────────────────────────────────┤
│      Operating System               │  操作系统
└─────────────────────────────────────┘
```

### 1.2 JDK、JRE、JVM关系

```
┌────────────────────── JDK (Java Development Kit) ─────────────────────┐
│                                                                        │
│  ┌──────────────────── JRE (Java Runtime Environment) ──────────────┐ │
│  │                                                                   │ │
│  │  ┌─────────────── JVM (Java Virtual Machine) ──────────────┐    │ │
│  │  │                                                        │     │ │
│  │  │  - 类加载器 (ClassLoader)                               │     │ │
│  │  │  - 执行引擎 (Execution Engine)                          │     │ │
│  │  │  - 运行时数据区 (Runtime Data Area)                      │     │ │
│  │  │  - 本地方法接口 (Native Interface)                       │    │ │
│  │  │                                                          │    │ │
│  │  └──────────────────────────────────────────────────────────┘    │ │
│  │                                                                   │ │
│  │  Java核心类库 (java.lang, java.util, java.io...)                │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  开发工具 (javac, java, jar, javadoc, jdb...)                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**对比**：
- **JDK**：开发工具包 = JRE + 开发工具（javac编译器、调试器等）
- **JRE**：运行环境 = JVM + 核心类库
- **JVM**：虚拟机，执行字节码

### 1.3 核心特性

**① Write Once, Run Anywhere（一次编写，到处运行）**
```java
// .java源文件 → javac编译 → .class字节码 → JVM执行
// 字节码是平台无关的，由不同平台的JVM解释执行

// 示例：
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}

// 编译：javac HelloWorld.java → HelloWorld.class
// 运行：java HelloWorld
```

**字节码示例**：
```bash
# 查看字节码
javap -c HelloWorld

Compiled from "HelloWorld.java"
public class HelloWorld {
  public HelloWorld();
    Code:
       0: aload_0
       1: invokespecial #1  // Method java/lang/Object."<init>":()V
       4: return

  public static void main(java.lang.String[]);
    Code:
       0: getstatic     #2  // Field java/lang/System.out:Ljava/io/PrintStream;
       3: ldc           #3  // String Hello World
       5: invokevirtual #4  // Method java/io/PrintStream.println:(Ljava/lang/String;)V
       8: return
}
```

**② 自动内存管理（GC）**
```java
/**
 * Java内存区域：
 * 
 * 线程共享：
 * - 堆（Heap）：对象实例
 * - 方法区（Method Area）：类信息、常量、静态变量（JDK 8改为元空间Metaspace）
 * 
 * 线程私有：
 * - 虚拟机栈（VM Stack）：局部变量、操作数栈、方法出口
 * - 本地方法栈（Native Method Stack）：本地方法
 * - 程序计数器（Program Counter）：当前线程执行的字节码行号
 */

public class MemoryDemo {
    private static int staticVar = 10;  // 方法区（元空间）
    
    public void method() {
        int localVar = 20;  // 虚拟机栈
        String str = new String("hello");  // str引用在栈，对象在堆
    }
}
```

**垃圾回收机制**：
```java
/**
 * 对象存活判断：
 * 1. 引用计数法（已淘汰）：循环引用问题
 * 2. 可达性分析（当前使用）：从GC Roots开始，不可达的对象会被回收
 * 
 * GC Roots包括：
 * - 虚拟机栈中引用的对象
 * - 方法区中类静态属性引用的对象
 * - 方法区中常量引用的对象
 * - 本地方法栈中JNI引用的对象
 */

public class GCDemo {
    public static void main(String[] args) {
        Object obj = new Object();  // obj是GC Root
        obj = null;  // 对象变成垃圾，会被GC回收
        
        // 手动建议GC（不保证立即执行）
        System.gc();
    }
}
```

**③ 面向对象**
- 封装、继承、多态
- 一切皆对象（除基本类型）

### 1.4 Java程序执行流程

```
源代码 (.java)
    ↓ javac编译
字节码 (.class)
    ↓ 类加载器
JVM内存
    ↓ 执行引擎
    ├→ 解释执行（逐行翻译成机器码）
    └→ JIT编译（热点代码编译成机器码，缓存）
    ↓
机器码执行
```

**JIT编译器优化**：
```java
/**
 * JIT (Just-In-Time) 即时编译
 * 
 * 执行过程：
 * 1. 初始：解释执行（慢）
 * 2. 热点代码检测：方法调用次数超过阈值（如10000次）
 * 3. JIT编译：编译成本地机器码（快）
 * 4. 缓存：下次直接执行机器码
 * 
 * 两种模式：
 * - C1（Client Compiler）：启动快，优化少
 * - C2（Server Compiler）：启动慢，优化多
 * - 分层编译（Tiered Compilation）：JDK 7+默认，结合C1+C2
 */

public class JITDemo {
    public static void main(String[] args) {
        // 循环10万次，触发JIT编译
        for (int i = 0; i < 100000; i++) {
            hotMethod();
        }
    }
    
    // 热点方法，会被JIT编译
    public static int hotMethod() {
        return 1 + 1;
    }
}
```

---

## 2. 面向对象核心

### 2.1 封装（Encapsulation）

**原理**：
- 隐藏对象的内部实现细节
- 通过访问控制符限制访问
- 提供公共接口操作对象

**访问控制符**：
```java
public    > protected > default(包级私有) > private
  ↓           ↓              ↓               ↓
所有类     子类+同包       同包内          仅本类
```

**实战示例**：
```java
public class BankAccount {
    // 私有字段，外部无法直接访问
    private String accountNumber;
    private double balance;
    
    // 公共接口，控制访问逻辑
    public void deposit(double amount) {
        if (amount > 0) {
            balance += amount;
        } else {
            throw new IllegalArgumentException("金额必须大于0");
        }
    }
    
    public boolean withdraw(double amount) {
        if (amount > 0 && balance >= amount) {
            balance -= amount;
            return true;
        }
        return false;
    }
    
    // 只读访问
    public double getBalance() {
        return balance;
    }
}
```

---

### 2.2 继承（Inheritance）

**原理**：
- 子类继承父类的属性和方法
- 实现代码复用
- 建立类型层次结构

**继承关系**：
```java
public class Animal {
    protected String name;
    
    public void eat() {
        System.out.println(name + " is eating");
    }
}

public class Dog extends Animal {
    // 继承了name字段和eat()方法
    
    // 扩展新方法
    public void bark() {
        System.out.println(name + " is barking");
    }
    
    // 方法重写（Override）
    @Override
    public void eat() {
        System.out.println(name + " is eating dog food");
    }
}
```

**关键点**：
- Java只支持单继承（extends一个类）
- 所有类都隐式继承`Object`类
- 构造方法不被继承，但子类构造会调用父类构造（super()）

---

### 2.3 多态（Polymorphism）

**原理**：
- 同一个引用类型，指向不同的对象，调用相同的方法，表现出不同的行为
- 编译时类型 vs 运行时类型

**实现方式**：
1. **方法重载（Overload）**：编译时多态
2. **方法重写（Override）**：运行时多态

**运行时多态示例**：
```java
public class PolymorphismDemo {
    public static void main(String[] args) {
        // 编译时类型：Animal，运行时类型：Dog
        Animal animal1 = new Dog();
        animal1.eat();  // 调用Dog的eat()方法
        
        // 编译时类型：Animal，运行时类型：Cat
        Animal animal2 = new Cat();
        animal2.eat();  // 调用Cat的eat()方法
        
        // 多态的好处：统一处理
        Animal[] animals = {new Dog(), new Cat(), new Bird()};
        for (Animal animal : animals) {
            animal.eat();  // 各自调用自己的eat()实现
        }
    }
}
```

**动态绑定原理**：
```java
// JVM在运行时根据对象的实际类型，动态绑定到对应的方法实现

// 查找顺序：
// 1. 先在运行时类型（实际对象类型）中查找方法
// 2. 找不到则在父类中查找
// 3. 一直向上查找到Object类

// 方法调用指令：invokevirtual（虚方法调用）
```

---

### 2.4 抽象类（Abstract Class）

**特点**：
- 不能被实例化
- 可以有抽象方法和具体方法
- 可以有构造方法（供子类调用）
- 可以有成员变量

**示例**：
```java
public abstract class Animal {
    private String name;
    
    // 构造方法
    public Animal(String name) {
        this.name = name;
    }
    
    // 抽象方法：子类必须实现
    public abstract void makeSound();
    
    // 具体方法：子类可以继承
    public void eat() {
        System.out.println(name + " is eating");
    }
    
    // getter
    public String getName() {
        return name;
    }
}

public class Dog extends Animal {
    public Dog(String name) {
        super(name);
    }
    
    @Override
    public void makeSound() {
        System.out.println(getName() + " says: Woof!");
    }
}

// 使用
Animal dog = new Dog("Buddy");
dog.makeSound();  // Buddy says: Woof!
dog.eat();        // Buddy is eating
```

---

### 2.5 接口（Interface）

**特点（JDK 8+）**：
- 接口中的变量默认是 `public static final`
- 可以有抽象方法（默认 `public abstract`）
- 可以有默认方法（`default`）
- 可以有静态方法（`static`）
- JDK 9+：可以有私有方法（`private`）

**示例**：
```java
public interface Flyable {
    // 常量（public static final）
    int MAX_SPEED = 1000;
    
    // 抽象方法（public abstract）
    void fly();
    
    // 默认方法（JDK 8+）
    default void takeOff() {
        checkWeather();
        System.out.println("Taking off...");
    }
    
    default void land() {
        System.out.println("Landing...");
    }
    
    // 静态方法（JDK 8+）
    static void printInfo() {
        System.out.println("Flyable interface");
    }
    
    // 私有方法（JDK 9+）
    private void checkWeather() {
        System.out.println("Checking weather...");
    }
}

// 实现接口
public class Airplane implements Flyable {
    @Override
    public void fly() {
        System.out.println("Airplane is flying");
    }
}

// 使用
Flyable airplane = new Airplane();
airplane.takeOff();  // 调用默认方法
airplane.fly();      // 调用实现的方法
Flyable.printInfo(); // 调用静态方法
```

**多接口实现**：
```java
public interface Swimmable {
    void swim();
}

public interface Runnable {
    void run();
}

// 多接口实现
public class Duck implements Flyable, Swimmable, Runnable {
    @Override
    public void fly() {
        System.out.println("Duck is flying");
    }
    
    @Override
    public void swim() {
        System.out.println("Duck is swimming");
    }
    
    @Override
    public void run() {
        System.out.println("Duck is running");
    }
}
```

---

### 2.6 抽象类 vs 接口

**对比**：
```java
┌──────────────┬─────────────────────┬─────────────────────┐
│   特性       │     抽象类          │      接口           │
├──────────────┼─────────────────────┼─────────────────────┤
│ 成员变量     │ 任意修饰符          │ public static final │
├──────────────┼─────────────────────┼─────────────────────┤
│ 构造方法     │ 可以有              │ 不能有              │
├──────────────┼─────────────────────┼─────────────────────┤
│ 方法实现     │ 可以有具体方法      │ default/static方法  │
├──────────────┼─────────────────────┼─────────────────────┤
│ 继承/实现    │ 单继承              │ 多实现              │
├──────────────┼─────────────────────┼─────────────────────┤
│ 设计目的     │ is-a 关系           │ can-do 关系         │
└──────────────┴─────────────────────┴─────────────────────┘
```

**选择建议**：
```java
// ✅ 使用抽象类：
// 1. 需要共享代码实现
// 2. 需要定义非public成员
// 3. 需要定义非静态、非final字段
// 4. 需要构造方法

public abstract class Vehicle {
    protected String brand;  // 共享字段
    
    public Vehicle(String brand) {  // 构造方法
        this.brand = brand;
    }
    
    // 共享实现
    public void start() {
        System.out.println(brand + " is starting");
    }
    
    // 抽象方法
    public abstract void move();
}

// ✅ 使用接口：
// 1. 定义能力（行为契约）
// 2. 需要多继承
// 3. 不相关的类需要实现相同的行为

public interface Chargeable {
    void charge();
}

// 电动车既是车，也可充电
public class ElectricCar extends Vehicle implements Chargeable {
    public ElectricCar(String brand) {
        super(brand);
    }
    
    @Override
    public void move() {
        System.out.println("Electric car is moving");
    }
    
    @Override
    public void charge() {
        System.out.println("Charging...");
    }
}
```

---

### 2.7 内部类

**① 成员内部类**：
```java
public class Outer {
    private String outerField = "outer";
    
    // 成员内部类
    public class Inner {
        private String innerField = "inner";
        
        public void print() {
            System.out.println(outerField);  // 可以访问外部类成员
            System.out.println(innerField);
        }
    }
    
    public void test() {
        Inner inner = new Inner();
        inner.print();
    }
}

// 使用
Outer outer = new Outer();
Outer.Inner inner = outer.new Inner();  // 需要外部类实例
inner.print();
```

**② 静态内部类**：
```java
public class Outer {
    private static String staticField = "static";
    private String instanceField = "instance";
    
    // 静态内部类
    public static class StaticInner {
        public void print() {
            System.out.println(staticField);  // 可以访问外部类静态成员
            // System.out.println(instanceField);  // ❌ 不能访问非静态成员
        }
    }
}

// 使用
Outer.StaticInner inner = new Outer.StaticInner();  // 不需要外部类实例
inner.print();
```

**③ 局部内部类**：
```java
public class Outer {
    public void method() {
        final int localVar = 10;  // JDK 8+可以省略final，但必须是effectively final
        
        // 局部内部类
        class LocalInner {
            public void print() {
                System.out.println(localVar);  // 可以访问final局部变量
            }
        }
        
        LocalInner inner = new LocalInner();
        inner.print();
    }
}
```

**④ 匿名内部类**：
```java
public class AnonymousDemo {
    public static void main(String[] args) {
        // 匿名内部类实现接口
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                System.out.println("Running");
            }
        };
        
        // 匿名内部类继承类
        Animal animal = new Animal("Cat") {
            @Override
            public void makeSound() {
                System.out.println("Meow");
            }
        };
        
        // JDK 8+ Lambda替代（针对函数式接口）
        Runnable r = () -> System.out.println("Running");
    }
}
```

---

## 3. Java类型系统

### 3.1 基本类型（Primitive Types）

**8种基本类型**：
```java
byte    -128 ~ 127                     (1字节)
short   -32768 ~ 32767                 (2字节)
int     -2^31 ~ 2^31-1                 (4字节)
long    -2^63 ~ 2^63-1                 (8字节)

float   IEEE 754单精度                 (4字节)
double  IEEE 754双精度                 (8字节)

char    0 ~ 65535（Unicode字符）       (2字节)
boolean true/false                     (JVM规范未明确定义，通常按1字节处理)
```

**存储位置**：
- 基本类型变量存储在**栈**中
- 对象引用存储在**栈**中，对象本身存储在**堆**中

---

### 3.2 包装类（Wrapper Classes）

**基本类型 → 包装类**：
```java
byte    → Byte
short   → Short
int     → Integer
long    → Long
float   → Float
double  → Double
char    → Character
boolean → Boolean
```

**自动装箱/拆箱（AutoBoxing/Unboxing）**：
```java
// 自动装箱：基本类型 → 包装类
Integer i = 100;  // 等价于 Integer.valueOf(100)

// 自动拆箱：包装类 → 基本类型
int j = i;  // 等价于 i.intValue()

// 注意空指针异常
Integer num = null;
int value = num;  // NPE！拆箱时num.intValue()报错
```

**Integer缓存机制**：
```java
public static Integer valueOf(int i) {
    // -128 ~ 127 范围内，返回缓存对象
    if (i >= IntegerCache.low && i <= IntegerCache.high)
        return IntegerCache.cache[i + (-IntegerCache.low)];
    // 超出范围，创建新对象
    return new Integer(i);
}

// 示例
Integer a = 100;
Integer b = 100;
System.out.println(a == b);  // true（同一个缓存对象）

Integer c = 200;
Integer d = 200;
System.out.println(c == d);  // false（不同对象）

// 正确比较方式：使用equals()
System.out.println(c.equals(d));  // true
```

**缓存范围**：
- `Byte`, `Short`, `Integer`, `Long`：-128 ~ 127
- `Character`：0 ~ 127
- `Boolean`：TRUE, FALSE（只有两个对象）

---

### 3.3 对象内存布局

**对象在内存中的结构（以HotSpot JVM为例）**：
```
┌────────────────────────────────────┐
│        对象头（Object Header）      │
├────────────────────────────────────┤
│  - Mark Word（8字节，64位JVM）      │  锁状态、GC标记、hashCode等
│  - Class Pointer（4/8字节）         │  指向类元数据的指针
│  - Array Length（4字节，仅数组）    │  数组长度
├────────────────────────────────────┤
│        实例数据（Instance Data）    │  字段数据
├────────────────────────────────────┤
│        对齐填充（Padding）          │  保证对象大小是8字节的倍数
└────────────────────────────────────┘
```

**Mark Word结构（64位JVM）**：
```java
/**
 * 无锁状态：
 * |  unused(25) | hashCode(31) | unused(1) | age(4) | biased_lock(1) | lock(2) |
 * 
 * 偏向锁：
 * |  thread_id(54) | epoch(2) | unused(1) | age(4) | biased_lock(1) | lock(2) |
 * 
 * 轻量级锁：
 * |  ptr_to_lock_record(62) | lock(2) |
 * 
 * 重量级锁：
 * |  ptr_to_heavyweight_monitor(62) | lock(2) |
 */
```

**对象大小计算示例**：
```java
public class User {
    private int id;        // 4字节
    private long phone;    // 8字节
    private String name;   // 4字节（引用）
}

/**
 * 对象布局（64位JVM，压缩指针开启）：
 * - 对象头：12字节（Mark Word 8字节 + Class Pointer 4字节）
 * - 实例数据：16字节（id:4 + phone:8 + name:4）
 * - 对齐填充：4字节（保证总大小是8的倍数：12+16+4=32）
 * 
 * 总大小：32字节
 */

// 使用JOL（Java Object Layout）工具查看对象布局
import org.openjdk.jol.info.ClassLayout;

public class ObjectLayoutDemo {
    public static void main(String[] args) {
        User user = new User();
        System.out.println(ClassLayout.parseInstance(user).toPrintable());
    }
}
```

**数组对象内存布局**：
```java
int[] arr = new int[3];  // {1, 2, 3}

/**
 * 数组对象布局：
 * - 对象头：16字节（Mark Word 8字节 + Class Pointer 4字节 + Array Length 4字节）
 * - 数组数据：12字节（3个int，每个4字节）
 * - 对齐填充：4字节
 * 
 * 总大小：32字节
 */
```

---

### 3.4 引用类型

**四种引用类型**：
```java
/**
 * 1. 强引用（Strong Reference）：默认引用
 *    - 垃圾回收器永远不会回收
 *    - 内存不足会抛OOM
 */
Object obj = new Object();  // 强引用

/**
 * 2. 软引用（Soft Reference）：内存不足时回收
 *    - 用于实现内存敏感的缓存
 */
SoftReference<byte[]> softRef = new SoftReference<>(new byte[1024 * 1024]);
byte[] data = softRef.get();  // 可能返回null

/**
 * 3. 弱引用（Weak Reference）：GC时回收
 *    - ThreadLocal内部使用
 *    - WeakHashMap
 */
WeakReference<User> weakRef = new WeakReference<>(new User());
User user = weakRef.get();  // GC后可能返回null

/**
 * 4. 虚引用（Phantom Reference）：任何时候都可能被回收
 *    - 用于跟踪对象被回收的状态
 *    - 必须配合ReferenceQueue使用
 */
ReferenceQueue<User> queue = new ReferenceQueue<>();
PhantomReference<User> phantomRef = new PhantomReference<>(new User(), queue);
// phantomRef.get() 永远返回null
```

**引用队列示例**：
```java
public class ReferenceQueueDemo {
    public static void main(String[] args) throws InterruptedException {
        ReferenceQueue<byte[]> queue = new ReferenceQueue<>();
        
        // 创建100个软引用
        List<SoftReference<byte[]>> refs = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            SoftReference<byte[]> ref = new SoftReference<>(
                new byte[1024 * 1024], queue
            );
            refs.add(ref);
        }
        
        // 触发GC
        System.gc();
        
        // 查看被回收的引用
        Reference<?> ref;
        int count = 0;
        while ((ref = queue.poll()) != null) {
            count++;
        }
        System.out.println("回收了 " + count + " 个软引用");
    }
}
```

**应用场景**：
```java
// ✅ 软引用：图片缓存
public class ImageCache {
    private Map<String, SoftReference<Image>> cache = new HashMap<>();
    
    public Image getImage(String path) {
        SoftReference<Image> ref = cache.get(path);
        if (ref != null) {
            Image image = ref.get();
            if (image != null) {
                return image;  // 缓存命中
            }
        }
        
        // 加载图片
        Image image = loadImage(path);
        cache.put(path, new SoftReference<>(image));
        return image;
    }
}

// ✅ 弱引用：WeakHashMap
public class WeakHashMapDemo {
    public static void main(String[] args) {
        WeakHashMap<User, String> map = new WeakHashMap<>();
        User key = new User("张三");
        map.put(key, "value");
        
        System.out.println(map.size());  // 1
        
        key = null;  // 解除强引用
        System.gc();
        
        Thread.sleep(1000);
        System.out.println(map.size());  // 0（key被回收，entry自动移除）
    }
}
```

---

### 3.5 基本类型性能优化

**装箱/拆箱性能开销**：
```java
public class BoxingPerformance {
    public static void main(String[] args) {
        long start, end;
        
        // 使用基本类型：快
        start = System.currentTimeMillis();
        long sum1 = 0;
        for (int i = 0; i < 10_000_000; i++) {
            sum1 += i;
        }
        end = System.currentTimeMillis();
        System.out.println("基本类型耗时: " + (end - start) + "ms");
        
        // 使用包装类型：慢（频繁装箱拆箱）
        start = System.currentTimeMillis();
        Long sum2 = 0L;
        for (int i = 0; i < 10_000_000; i++) {
            sum2 += i;  // 每次循环：拆箱 → 相加 → 装箱
        }
        end = System.currentTimeMillis();
        System.out.println("包装类型耗时: " + (end - start) + "ms");
    }
}

// 输出示例：
// 基本类型耗时: 5ms
// 包装类型耗时: 150ms
```

**最佳实践**：
```java
// ❌ 错误：不必要的装箱
Integer sum = 0;
for (int i = 0; i < 100; i++) {
    sum += i;  // 每次循环都装箱拆箱
}

// ✅ 正确：使用基本类型
int sum = 0;
for (int i = 0; i < 100; i++) {
    sum += i;
}

// ❌ 错误：不必要的拆箱
public void method(Integer num) {
    int value = num;  // 拆箱
    // ...
}

// ✅ 正确：直接使用基本类型
public void method(int num) {
    // ...
}
```

---

## 4. 字符串深度解析

### 4.1 String核心特性

**① 不可变性（Immutable）**：
```java
public final class String {
    // 字符数组被final修饰（JDK 9+改为byte[]）
    private final byte[] value; // JDK 9+改为byte[]
    
    // 没有提供修改value的方法
}
```

**为什么设计成不可变**：
1. **线程安全**：多线程共享字符串无需同步
2. **字符串常量池**：相同内容的字符串复用同一个对象
3. **安全性**：作为参数传递时，不会被修改
4. **HashCode缓存**：计���一次后缓存，提高HashMap等性能

---

### 4.2 字符串常量池（String Pool）

**原理**：
```java
// 在堆内存中维护一个字符串常量池（JDK 7+）
// 相同内容的字符串字面量，指向同一个对象

String s1 = "hello";  // 在常量池中创建
String s2 = "hello";  // 复用常量池中的对象
System.out.println(s1 == s2);  // true

String s3 = new String("hello");  // 在堆中创建新对象
System.out.println(s1 == s3);  // false

String s4 = s3.intern();  // 将s3指向常量池中的对象
System.out.println(s1 == s4);  // true
```

**intern()方法原理**：
```java
// JDK 6：将字符串复制到永久代的常量池
// JDK 7+：如果常量池没有该字符串，将堆中字符串的引用放入常量池

String s1 = new String("a") + new String("b");  // 堆中创建"ab"
String s2 = s1.intern();  // 将s1的引用放入常量池
String s3 = "ab";  // 从常量池获取
System.out.println(s1 == s2);  // true（JDK 7+）
System.out.println(s2 == s3);  // true
```

---

### 4.3 String vs StringBuilder vs StringBuffer

**对比**：
```java
// String：不可变，线程安全
String str = "hello";
str = str + " world";  // 创建新对象，原对象变成垃圾

// StringBuilder：可变，非线程安全，性能最好
StringBuilder sb = new StringBuilder("hello");
sb.append(" world");  // 在原对象上修改，不创建新对象

// StringBuffer：可变，线程安全（方法加synchronized），性能较差
StringBuffer sbf = new StringBuffer("hello");
sbf.append(" world");  // 线程安全，但有同步开销
```

**使用场景**：
- **String**：字符串不变的场景
- **StringBuilder**：单线程中大量字符串拼接
- **StringBuffer**：多线程中大量字符串拼接

**性能对比**：
```java
// 循环拼接10000次
// String：创建10000个对象，性能极差
// StringBuilder：只有1个对象，性能最好
// StringBuffer：只有1个对象，但有同步开销

// StringBuilder扩容机制：
// 默认容量16，扩容为 (oldCapacity << 1) + 2
```

---

### 4.4 字符串常见操作的原理

**substring()原理（JDK 7+）**：
```java
public String substring(int beginIndex, int endIndex) {
    // JDK 6：共享原字符串的char[]，可能导致内存泄漏
    // JDK 7+：创建新的char[]，复制字符
    return new String(value, beginIndex, subLen);
}
```

**split()原理**：
```java
// 基于正则表达式分割
String[] parts = "a,b,c".split(",");  // ["a", "b", "c"]

// 注意：如果分隔符是正则特殊字符，需要转义
String[] parts2 = "a.b.c".split("\\.");  // ["a", "b", "c"]
```

**equals()原理**：
```java
public boolean equals(Object anObject) {
    if (this == anObject) {
        return true;  // 同一个对象
    }
    if (anObject instanceof String) {
        String anotherString = (String)anObject;
        int n = value.length;
        if (n == anotherString.value.length) {
            char v1[] = value;
            char v2[] = anotherString.value;
            int i = 0;
            // 逐字符比较
            while (n-- != 0) {
                if (v1[i] != v2[i])
                    return false;
                i++;
            }
            return true;
        }
    }
    return false;
}
```

---

### 4.5 String性能优化

**① 字符串拼接优化**：
```java
// ❌ 错误：循环中使用+拼接
public String concat1(String[] words) {
    String result = "";
    for (String word : words) {
        result += word;  // 每次循环创建新String对象
    }
    return result;
}
// 性能：O(n²)，创建大量临时对象

// ✅ 正确：使用StringBuilder
public String concat2(String[] words) {
    StringBuilder sb = new StringBuilder();
    for (String word : words) {
        sb.append(word);  // 在同一个对象上修改
    }
    return sb.toString();
}
// 性能：O(n)，只创建一个StringBuilder对象

// 🔥 编译器优化（JDK 9+）：
// 对于简单的+拼接，编译器使用invokedynamic优化(JEP 280)
String s = "a" + "b" + "c";  // 编译时优化为常量"abc"
String s2 = str1 + str2;     // 编译后使用StringBuilder
```

**② 使用String.join()**：
```java
// ❌ 手动拼接
StringBuilder sb = new StringBuilder();
for (int i = 0; i < list.size(); i++) {
    sb.append(list.get(i));
    if (i < list.size() - 1) {
        sb.append(",");
    }
}
String result = sb.toString();

// ✅ 使用String.join()
String result = String.join(",", list);  // 简洁高效
```

**③ intern()使用场景**：
```java
/**
 * 使用场景：
 * 1. 大量重复字符串（如配置项、枚举值）
 * 2. 减少内存占用
 * 
 * 注意：
 * 1. intern()有性能开销（需要查找常量池）
 * 2. JDK 6的常量池在永久代，可能导致OOM
 * 3. JDK 7+常量池在堆中，相对安全
 */

// ✅ 适合使用intern()
public class ConfigManager {
    private Map<String, String> config = new HashMap<>();
    
    public void addConfig(String key, String value) {
        // 配置项通常重复较多，intern()节省内存
        config.put(key.intern(), value.intern());
    }
}

// ❌ 不适合使用intern()
public class LogProcessor {
    public void processLog(String log) {
        // 日志内容不重复，intern()反而降低性能
        String content = log.intern();  // 不推荐
    }
}
```

**④ 字符串分割性能**：
```java
// ❌ split()：基于正则，性能较差
String[] parts = "a,b,c,d,e".split(",");

// ✅ StringTokenizer：性能更好（不支持正则）
StringTokenizer st = new StringTokenizer("a,b,c,d,e", ",");
List<String> parts = new ArrayList<>();
while (st.hasMoreTokens()) {
    parts.add(st.nextToken());
}

// ✅ Guava Splitter：功能强大，性能好
List<String> parts = Splitter.on(',')
    .trimResults()
    .omitEmptyStrings()
    .splitToList("a, b, c, d, e");
```

---

### 4.6 正则表达式

**基本语法**：
```java
/**
 * 字符类：
 * .         任意字符
 * [abc]     a或b或c
 * [^abc]    除了a、b、c
 * [a-z]     a到z
 * \d        数字[0-9]
 * \D        非数字
 * \w        单词字符[a-zA-Z0-9_]
 * \W        非单词字符
 * \s        空白字符
 * \S        非空白字符
 * 
 * 数量词：
 * *         0次或多次
 * +         1次或多次
 * ?         0次或1次
 * {n}       恰好n次
 * {n,}      至少n次
 * {n,m}     n到m次
 * 
 * 边界匹配：
 * ^         行首
 * $         行尾
 * \b        单词边界
 * \B        非单词边界
 * 
 * 分组：
 * (pattern) 捕获分组
 * (?:pattern) 非捕获分组
 * |         或
 */
```

**Pattern和Matcher**：
```java
import java.util.regex.Pattern;
import java.util.regex.Matcher;

public class RegexDemo {
    public static void main(String[] args) {
        // 编译正则表达式
        Pattern pattern = Pattern.compile("\\d+");
        
        // 创建Matcher
        Matcher matcher = pattern.matcher("abc123def456");
        
        // 查找所有匹配
        while (matcher.find()) {
            System.out.println("找到: " + matcher.group());
            System.out.println("位置: " + matcher.start() + "-" + matcher.end());
        }
        // 输出：
        // 找到: 123
        // 位置: 3-6
        // 找到: 456
        // 位置: 9-12
    }
}
```

**常用正则示例**：
```java
public class RegexExamples {
    // 手机号
    public static final String PHONE = "^1[3-9]\\d{9}$";
    
    // 邮箱
    public static final String EMAIL = "^[\\w-]+(\\.[\\w-]+)*@[\\w-]+(\\.[\\w-]+)+$";
    
    // 身份证号
    public static final String ID_CARD = "^\\d{17}[\\dXx]$";
    
    // IP地址
    public static final String IP = "^((25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]?\\d)\\.){3}(25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]?\\d)$";
    
    // 日期（yyyy-MM-dd）
    public static final String DATE = "^\\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])$";
    
    // URL
    public static final String URL = "^(https?://)?([\\w-]+\\.)+[\\w-]+(/[\\w-./?%&=]*)?$";
    
    // 验证方法
    public static boolean validate(String input, String regex) {
        return Pattern.matches(regex, input);
    }
    
    public static void main(String[] args) {
        System.out.println(validate("13812345678", PHONE));  // true
        System.out.println(validate("test@example.com", EMAIL));  // true
        System.out.println(validate("192.168.1.1", IP));  // true
    }
}
```

**分组提取**：
```java
public class GroupExtraction {
    public static void main(String[] args) {
        String text = "张三：18，李四：25，王五：30";
        
        // 定义正则：捕获姓名和年龄
        Pattern pattern = Pattern.compile("(\\w+)：(\\d+)");
        Matcher matcher = pattern.matcher(text);
        
        while (matcher.find()) {
            String name = matcher.group(1);  // 第一个分组
            String age = matcher.group(2);   // 第二个分组
            System.out.println("姓名: " + name + ", 年龄: " + age);
        }
        // 输出：
        // 姓名: 张三, 年龄: 18
        // 姓名: 李四, 年龄: 25
        // 姓名: 王五, 年龄: 30
    }
}
```

**替换操作**：
```java
public class RegexReplace {
    public static void main(String[] args) {
        String text = "手机号：13812345678，电话：010-12345678";
        
        // 替换所有数字为*
        String result1 = text.replaceAll("\\d", "*");
        System.out.println(result1);
        // 手机号：***********，电话：***-********
        
        // 替换手机号中间4位
        String phone = "13812345678";
        String result2 = phone.replaceAll("(\\d{3})\\d{4}(\\d{4})", "$1****$2");
        System.out.println(result2);  // 138****5678
        
        // 使用Matcher.replaceAll()
        Pattern pattern = Pattern.compile("\\d+");
        Matcher matcher = pattern.matcher("abc123def456");
        String result3 = matcher.replaceAll("NUM");
        System.out.println(result3);  // abcNUMdefNUM
    }
}
```

**性能优化**：
```java
public class RegexPerformance {
    // ❌ 错误：每次都编译正则
    public boolean validate1(String email) {
        return email.matches("^[\\w-]+@[\\w-]+\\.[\\w-]+$");
    }
    
    // ✅ 正确：缓存Pattern对象
    private static final Pattern EMAIL_PATTERN = 
        Pattern.compile("^[\\w-]+@[\\w-]+\\.[\\w-]+$");
    
    public boolean validate2(String email) {
        return EMAIL_PATTERN.matcher(email).matches();
    }
    
    // 性能测试
    public static void main(String[] args) {
        String email = "test@example.com";
        long start, end;
        
        // 方式1：每次编译
        start = System.currentTimeMillis();
        RegexPerformance demo = new RegexPerformance();
        for (int i = 0; i < 100000; i++) {
            demo.validate1(email);
        }
        end = System.currentTimeMillis();
        System.out.println("每次编译耗时: " + (end - start) + "ms");
        
        // 方式2：缓存Pattern
        start = System.currentTimeMillis();
        for (int i = 0; i < 100000; i++) {
            demo.validate2(email);
        }
        end = System.currentTimeMillis();
        System.out.println("缓存Pattern耗时: " + (end - start) + "ms");
    }
}
```

---

## 5. 集合框架核心原理

### 5.1 集合框架体系

```
Collection（接口）
├── List（接口）：有序，可重复
│   ├── ArrayList：动态数组
│   ├── LinkedList：双向链表
│   └── Vector：线程安全的动态数组（已过时）
├── Set（接口）：无序，不可重复
│   ├── HashSet：基于HashMap
│   ├── LinkedHashSet：保持插入顺序
│   └── TreeSet：基于TreeMap，有序
└── Queue（接口）：队列
    ├── PriorityQueue：优先队列（堆）
    └── Deque（接口）：双端队列
        └── ArrayDeque：基于数组的双端队列

Map（接口）：键值对
├── HashMap：哈希表
├── LinkedHashMap：保持插入顺序
├── TreeMap：红黑树，有序
├── Hashtable：线程安全（已过时）
└── ConcurrentHashMap：线程安全，高并发
```

---

### 5.2 ArrayList核心原理

**底层结构**：
```java
public class ArrayList<E> {
    // 默认初始容量
    private static final int DEFAULT_CAPACITY = 10;
    
    // 底层数组
    transient Object[] elementData;
    
    // 实际元素个数
    private int size;
}
```

**扩容机制**：
```java
// 添加元素时，如果容量不足，触发扩容
public boolean add(E e) {
    ensureCapacityInternal(size + 1);  // 确保容量
    elementData[size++] = e;
    return true;
}

// 扩容为原来的1.5倍
private void grow(int minCapacity) {
    int oldCapacity = elementData.length;
    int newCapacity = oldCapacity + (oldCapacity >> 1);  // 1.5倍
    if (newCapacity < minCapacity)
        newCapacity = minCapacity;
    elementData = Arrays.copyOf(elementData, newCapacity);
}
```

**时间复杂度**：
- `get(index)`：O(1)
- `add(E e)`：平均O(1)，扩容时O(n)
- `add(index, E e)`：O(n)，需要移动元素
- `remove(index)`：O(n)，需要移动元素

**适用场景**：
- ✅ 频繁随机访问
- ✅ 在末尾添加/删除
- ❌ 频繁在中间插入/删除

---

### 5.3 LinkedList核心原理

**底层结构**：
```java
public class LinkedList<E> {
    transient int size = 0;
    transient Node<E> first;  // 头节点
    transient Node<E> last;   // 尾节点
    
    // 节点定义
    private static class Node<E> {
        E item;
        Node<E> next;
        Node<E> prev;
        
        Node(Node<E> prev, E element, Node<E> next) {
            this.item = element;
            this.next = next;
            this.prev = prev;
        }
    }
}
```

**操作原理**：
```java
// 添加到末尾：O(1)
public boolean add(E e) {
    linkLast(e);
    return true;
}

void linkLast(E e) {
    final Node<E> l = last;
    final Node<E> newNode = new Node<>(l, e, null);
    last = newNode;
    if (l == null)
        first = newNode;
    else
        l.next = newNode;
    size++;
}

// 根据索引获取：O(n)
public E get(int index) {
    checkElementIndex(index);
    return node(index).item;
}

// 优化：根据index选择从前或从后遍历
Node<E> node(int index) {
    if (index < (size >> 1)) {  // 前半部分
        Node<E> x = first;
        for (int i = 0; i < index; i++)
            x = x.next;
        return x;
    } else {  // 后半部分
        Node<E> x = last;
        for (int i = size - 1; i > index; i--)
            x = x.prev;
        return x;
    }
}
```

**时间复杂度**：
- `get(index)`：O(n)
- `add(E e)`：O(1)
- `add(index, E e)`：O(n)，需要先定位
- `remove(index)`：O(n)，需要先定位

**适用场景**：
- ✅ 频繁在头尾添加/删除
- ✅ 队列、栈的实现
- ❌ 频繁随机访问

---


### 5.4 HashMap核心原理（⭐⭐⭐⭐⭐）

**底层结构（JDK 8+）**：
```
数组 + 链表 + 红黑树

┌────┬────┬────┬────┐
│  0 │ 1  │ 2  │... │  数组（Node[]）
└─┬──┴────┴────┴────┘
  │
  ├─> Node → Node → Node  (链表，长度<8)
  │
  └─> TreeNode → TreeNode  (红黑树，长度≥8且数组长度≥64)
```

**核心数据结构**：
```java
public class HashMap<K,V> {
    // 默认初始容量：16
    static final int DEFAULT_INITIAL_CAPACITY = 1 << 4;
    
    // 默认负载因子：0.75
    static final float DEFAULT_LOAD_FACTOR = 0.75f;
    
    // 链表转红黑树阈值：8
    static final int TREEIFY_THRESHOLD = 8;
    
    // 红黑树转链表阈值：6
    static final int UNTREEIFY_THRESHOLD = 6;
    
    // 转红黑树的最小数组容量：64
    static final int MIN_TREEIFY_CAPACITY = 64;
    
    // 数组
    transient Node<K,V>[] table;
    
    // 元素个数
    transient int size;
    
    // 扩容阈值：capacity * loadFactor
    int threshold;
    
    // 节点定义
    static class Node<K,V> implements Map.Entry<K,V> {
        final int hash;
        final K key;
        V value;
        Node<K,V> next;
    }
}
```

**Hash计算（扰动函数）**：
```java
static final int hash(Object key) {
    int h;
    // key的hashCode与其高16位异或
    // 目的：让高位也参与到hash计算，减少碰撞
    return (key == null) ? 0 : (h = key.hashCode()) ^ (h >>> 16);
}

// 示例：
// hashCode = 0b 1111 1111 1111 1111 0000 1111 0000 1010
//         >>> 16 = 0b 0000 0000 0000 0000 1111 1111 1111 1111
//         异或后 = 0b 1111 1111 1111 1111 1111 0000 1111 0101
```

**put()原理**：
```java
public V put(K key, V value) {
    return putVal(hash(key), key, value, false, true);
}

final V putVal(int hash, K key, V value, boolean onlyIfAbsent,
               boolean evict) {
    Node<K,V>[] tab; Node<K,V> p; int n, i;
    
    // 1. 数组为空，初始化
    if ((tab = table) == null || (n = tab.length) == 0)
        n = (tab = resize()).length;
    
    // 2. 计算索引：(n - 1) & hash（等价于hash % n，但更快）
    if ((p = tab[i = (n - 1) & hash]) == null)
        tab[i] = newNode(hash, key, value, null);  // 直接放入
    else {
        // 3. 发生碰撞
        Node<K,V> e; K k;
        // 3.1 key相同，覆盖
        if (p.hash == hash &&
            ((k = p.key) == key || (key != null && key.equals(k))))
            e = p;
        // 3.2 红黑树节点
        else if (p instanceof TreeNode)
            e = ((TreeNode<K,V>)p).putTreeVal(this, tab, hash, key, value);
        // 3.3 链表节点
        else {
            for (int binCount = 0; ; ++binCount) {
                if ((e = p.next) == null) {
                    p.next = newNode(hash, key, value, null);
                    // 链表长度≥8，转红黑树
                    if (binCount >= TREEIFY_THRESHOLD - 1)
                        treeifyBin(tab, hash);
                    break;
                }
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    break;
                p = e;
            }
        }
        // 4. key存在，更新value
        if (e != null) {
            V oldValue = e.value;
            if (!onlyIfAbsent || oldValue == null)
                e.value = value;
            return oldValue;
        }
    }
    ++modCount;
    // 5. 超过阈值，扩容
    if (++size > threshold)
        resize();
    return null;
}
```

**扩容机制（resize）**：
```java
final Node<K,V>[] resize() {
    Node<K,V>[] oldTab = table;
    int oldCap = (oldTab == null) ? 0 : oldTab.length;
    int oldThr = threshold;
    int newCap, newThr = 0;
    
    // 1. 计算新容量（2倍扩容）
    if (oldCap > 0) {
        if (oldCap >= MAXIMUM_CAPACITY) {
            threshold = Integer.MAX_VALUE;
            return oldTab;
        }
        // 扩容为原来的2倍
        else if ((newCap = oldCap << 1) < MAXIMUM_CAPACITY &&
                 oldCap >= DEFAULT_INITIAL_CAPACITY)
            newThr = oldThr << 1;  // 阈值也翻倍
    }
    
    // 2. 创建新数组
    Node<K,V>[] newTab = (Node<K,V>[])new Node[newCap];
    table = newTab;
    
    // 3. 数据迁移
    if (oldTab != null) {
        for (int j = 0; j < oldCap; ++j) {
            Node<K,V> e;
            if ((e = oldTab[j]) != null) {
                oldTab[j] = null;
                // 3.1 单节点，直接迁移
                if (e.next == null)
                    newTab[e.hash & (newCap - 1)] = e;
                // 3.2 红黑树
                else if (e instanceof TreeNode)
                    ((TreeNode<K,V>)e).split(this, newTab, j, oldCap);
                // 3.3 链表
                else {
                    // 优化：根据hash值的高位，分成两条链表
                    // 低位链表：保持原索引
                    // 高位链表：索引 = 原索引 + oldCap
                    Node<K,V> loHead = null, loTail = null;
                    Node<K,V> hiHead = null, hiTail = null;
                    Node<K,V> next;
                    do {
                        next = e.next;
                        // (e.hash & oldCap) == 0 说明高位为0
                        if ((e.hash & oldCap) == 0) {
                            if (loTail == null)
                                loHead = e;
                            else
                                loTail.next = e;
                            loTail = e;
                        }
                        else {
                            if (hiTail == null)
                                hiHead = e;
                            else
                                hiTail.next = e;
                            hiTail = e;
                        }
                    } while ((e = next) != null);
                    if (loTail != null) {
                        loTail.next = null;
                        newTab[j] = loHead;
                    }
                    if (hiTail != null) {
                        hiTail.next = null;
                        newTab[j + oldCap] = hiHead;
                    }
                }
            }
        }
    }
    return newTab;
}
```

**为什么容量必须是2的幂**：
```java
// 1. 计算索引更高效：(n - 1) & hash 等价于 hash % n
// 例如：n = 16 = 0b 10000
//      n - 1 = 15 = 0b 01111
//      hash & 0b01111 = 取hash的低4位，等价于 hash % 16

// 2. 扩容时数据迁移更高效
// 容量扩大2倍，每个节点要么在原位置，要么在"原位置+oldCap"
```

**为什么负载因子是0.75**：
```
负载因子 = size / capacity

太小（如0.5）：空间利用率低，频繁扩容
太大（如1.0）：碰撞概率高，链表过长，性能下降

0.75：时间和空间的折中，泊松分布计算得出最优值
```

**时间复杂度**：
- `put()`：平均O(1)，最坏O(n)（JDK 8+红黑树优化为O(log n)）
- `get()`：平均O(1)，最坏O(n)（JDK 8+红黑树优化为O(log n)）

**线程安全问题**：
```java
// JDK 7：扩容时链表采用头插法，多线程可能形成环形链表，导致死循环
// JDK 8：改为尾插法，避免了环形链表，但仍不是线程安全的

// 解决方案：
// 1. Collections.synchronizedMap(new HashMap<>())
// 2. ConcurrentHashMap（推荐）
```

---

### 5.5 LinkedHashMap原理

**特点**：
- 继承HashMap
- 维护插入顺序或访问顺序

**底层结构**：
```java
static class Entry<K,V> extends HashMap.Node<K,V> {
    Entry<K,V> before, after;  // 双向链表，维护顺序
    Entry(int hash, K key, V value, Node<K,V> next) {
        super(hash, key, value, next);
    }
}

// 头尾指针
transient LinkedHashMap.Entry<K,V> head;
transient LinkedHashMap.Entry<K,V> tail;

// 访问顺序标志
final boolean accessOrder;  // true：访问顺序，false：插入顺序
```

**应用：实现LRU缓存**：
```java
class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private int capacity;
    
    public LRUCache(int capacity) {
        // 参数：初始容量、负载因子、true=访问顺序
        super(capacity, 0.75f, true);
        this.capacity = capacity;
    }
    
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        // 超过容量，删除最老的元素
        return size() > capacity;
    }
}

// 使用
LRUCache<Integer, String> cache = new LRUCache<>(3);
cache.put(1, "a");
cache.put(2, "b");
cache.put(3, "c");
cache.get(1);  // 访问1，1变成最新
cache.put(4, "d");  // 容量满，删除最久未访问的2
// 缓存：{3=c, 1=a, 4=d}
```

---

### 5.6 TreeMap原理

**特点**：
- 基于红黑树
- key有序（自然顺序或自定义比较器）

**底层结构**：
```java
static final class Entry<K,V> implements Map.Entry<K,V> {
    K key;
    V value;
    Entry<K,V> left;   // 左子节点
    Entry<K,V> right;  // 右子节点
    Entry<K,V> parent; // 父节点
    boolean color = BLACK;  // 红黑树节点颜色
}
```

**put()原理**：
```java
public V put(K key, V value) {
    Entry<K,V> t = root;
    if (t == null) {
        // 根节点
        root = new Entry<>(key, value, null);
        size = 1;
        return null;
    }
    int cmp;
    Entry<K,V> parent;
    // 1. 查找插入位置
    do {
        parent = t;
        cmp = compare(key, t.key);  // 比较key
        if (cmp < 0)
            t = t.left;
        else if (cmp > 0)
            t = t.right;
        else
            return t.setValue(value);  // key相同，更新value
    } while (t != null);
    
    // 2. 插入节点
    Entry<K,V> e = new Entry<>(key, value, parent);
    if (cmp < 0)
        parent.left = e;
    else
        parent.right = e;
    
    // 3. 红黑树平衡调整
    fixAfterInsertion(e);
    size++;
    return null;
}
```

**时间复杂度**：
- `put()`, `get()`, `remove()`：O(log n)

**适用场景**：
- ✅ 需要key有序
- ✅ 范围查询（firstKey, lastKey, subMap）

---

### 5.7 ConcurrentHashMap原理（JDK 8）

**JDK 7 vs JDK 8**：
```
JDK 7：Segment分段锁（16个段）
JDK 8：CAS + synchronized，锁粒度更小（锁到Node）
```

**JDK 8核心机制**：
```java
// 1. 数组初始化：CAS保证单次初始化
private final Node<K,V>[] initTable() {
    Node<K,V>[] tab; int sc;
    while ((tab = table) == null || tab.length == 0) {
        if ((sc = sizeCtl) < 0)
            Thread.yield();  // 其他线程在初始化，让出CPU
        // CAS设置sizeCtl为-1，表示正在初始化
        else if (U.compareAndSwapInt(this, SIZECTL, sc, -1)) {
            try {
                if ((tab = table) == null || tab.length == 0) {
                    int n = (sc > 0) ? sc : DEFAULT_CAPACITY;
                    Node<K,V>[] nt = (Node<K,V>[])new Node<?,?>[n];
                    table = tab = nt;
                    sc = n - (n >>> 2);  // 0.75n
                }
            } finally {
                sizeCtl = sc;
            }
            break;
        }
    }
    return tab;
}

// 2. put()：CAS + synchronized
final V putVal(K key, V value, boolean onlyIfAbsent) {
    if (key == null || value == null) throw new NullPointerException();
    int hash = spread(key.hashCode());
    int binCount = 0;
    for (Node<K,V>[] tab = table;;) {
        Node<K,V> f; int n, i, fh;
        if (tab == null || (n = tab.length) == 0)
            tab = initTable();  // 初始化
        else if ((f = tabAt(tab, i = (n - 1) & hash)) == null) {
            // 位置为空，CAS插入
            if (casTabAt(tab, i, null, new Node<K,V>(hash, key, value, null)))
                break;
        }
        else if ((fh = f.hash) == MOVED)
            tab = helpTransfer(tab, f);  // 正在扩容，帮助迁移
        else {
            V oldVal = null;
            // 锁住链表头节点或红黑树根节点
            synchronized (f) {
                if (tabAt(tab, i) == f) {
                    if (fh >= 0) {  // 链表
                        binCount = 1;
                        for (Node<K,V> e = f;; ++binCount) {
                            K ek;
                            if (e.hash == hash &&
                                ((ek = e.key) == key ||
                                 (ek != null && key.equals(ek)))) {
                                oldVal = e.val;
                                if (!onlyIfAbsent)
                                    e.val = value;
                                break;
                            }
                            Node<K,V> pred = e;
                            if ((e = e.next) == null) {
                                pred.next = new Node<K,V>(hash, key,
                                                          value, null);
                                break;
                            }
                        }
                    }
                    else if (f instanceof TreeBin) {  // 红黑树
                        Node<K,V> p;
                        binCount = 2;
                        if ((p = ((TreeBin<K,V>)f).putTreeVal(hash, key,
                                                       value)) != null) {
                            oldVal = p.val;
                            if (!onlyIfAbsent)
                                p.val = value;
                        }
                    }
                }
            }
            if (binCount != 0) {
                if (binCount >= TREEIFY_THRESHOLD)
                    treeifyBin(tab, i);
                if (oldVal != null)
                    return oldVal;
                break;
            }
        }
    }
    addCount(1L, binCount);  // 计数（CAS）
    return null;
}
```

**优势**：
1. **锁粒度小**：只锁单个Node，不影响其他位置的操作
2. **CAS无锁**：数组为空时，CAS插入，无需加锁
3. **扩容并发**：支持多线程协助扩容

**size()实现**：
```java
// 使用CounterCell数组 + baseCount，类似LongAdder
// 高并发下分散计数，避免CAS失败
public int size() {
    long n = sumCount();
    return ((n < 0L) ? 0 :
            (n > (long)Integer.MAX_VALUE) ? Integer.MAX_VALUE :
            (int)n);
}
```

---

## 6. 异常处理机制

### 6.1 异常体系

```
Throwable
├── Error（错误，不可恢复）
│   ├── OutOfMemoryError
│   ├── StackOverflowError
│   └── VirtualMachineError
└── Exception（异常，可处理）
    ├── RuntimeException（运行时异常，unchecked）
    │   ├── NullPointerException
    │   ├── ArrayIndexOutOfBoundsException
    │   ├── ClassCastException
    │   └── IllegalArgumentException
    └── CheckedException（编译时异常，checked）
        ├── IOException
        ├── SQLException
        └── ClassNotFoundException
```

**Checked vs Unchecked**：
```java
// Checked：必须显式处理（try-catch或throws）
public void readFile() throws IOException {
    FileInputStream fis = new FileInputStream("file.txt");
    fis.read();
}

// Unchecked：可以不处理
public void divide(int a, int b) {
    int result = a / b;  // 可能抛出ArithmeticException
}
```

---

### 6.2 异常处理原理

**try-catch-finally执行顺序**：
```java
public class ExceptionTest {
    public static int test() {
        try {
            System.out.println("try");
            return 1;
        } catch (Exception e) {
            System.out.println("catch");
            return 2;
        } finally {
            System.out.println("finally");
            // finally中的return会覆盖try/catch中的return
            // return 3;
        }
    }
    
    public static void main(String[] args) {
        System.out.println(test());
    }
}
// 输出：
// try
// finally
// 1
```

**return在finally中的陷阱**：
```java
public static int test() {
    int i = 0;
    try {
        i = 1;
        return i;  // 返回1
    } finally {
        i = 2;  // 不影响返回值（已经保存了i=1）
    }
}
// 返回：1

public static int test2() {
    int i = 0;
    try {
        i = 1;
        return i;
    } finally {
        return 2;  // finally中的return会覆盖
    }
}
// 返回：2
```

---

### 6.3 try-with-resources

**自动资源管理**：
```java
// JDK 7+：自动关闭资源
try (FileInputStream fis = new FileInputStream("file.txt");
     BufferedReader br = new BufferedReader(new InputStreamReader(fis))) {
    String line = br.readLine();
    System.out.println(line);
}  // 自动调用close()

// 等价于：
FileInputStream fis = null;
BufferedReader br = null;
try {
    fis = new FileInputStream("file.txt");
    br = new BufferedReader(new InputStreamReader(fis));
    String line = br.readLine();
    System.out.println(line);
} finally {
    if (br != null) br.close();
    if (fis != null) fis.close();
}
```

**原理**：
```java
// 资源必须实现AutoCloseable接口
public interface AutoCloseable {
    void close() throws Exception;
}

// 示例
public class MyResource implements AutoCloseable {
    @Override
    public void close() throws Exception {
        System.out.println("资源关闭");
    }
}
```

---

### 6.4 最佳实践

**① 不要吞掉异常**：
```java
// ❌ 错误：吞掉异常
try {
    // ...
} catch (Exception e) {
    // 什么都不做
}

// ✅ 正确：至少记录日志
try {
    // ...
} catch (Exception e) {
    log.error("操作失败", e);
}
```

**② 不要捕获所有异常**：
```java
// ❌ 错误：捕获所有异常
try {
    // ...
} catch (Throwable t) {  // 包括Error
    // ...
}

// ✅ 正确：只捕获预期的异常
try {
    // ...
} catch (IOException e) {
    // 处理IO异常
} catch (SQLException e) {
    // 处理SQL异常
}
```

**③ 自定义异常**：
```java
// 业务异常
public class BusinessException extends RuntimeException {
    private int errorCode;
    
    public BusinessException(int errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }
}

// 使用
if (balance < amount) {
    throw new BusinessException(1001, "余额不足");
}
```

---

## 7. Java IO体系

### 7.1 IO分类

```
IO流分类：
├── 按数据流向
│   ├── 输入流（InputStream/Reader）
│   └── 输出流（OutputStream/Writer）
├── 按数据类型
│   ├── 字节流（Stream）：8位字节
│   └── 字符流（Reader/Writer）：16位字符
└── 按功能
    ├── 节点流：直接操作数据源
    └── 处理流：包装节点流，提供额外功能
```

**核心类**：
```
字节流：
├── InputStream
│   ├── FileInputStream：文件输入
│   ├── ByteArrayInputStream：字节数组输入
│   └── BufferedInputStream：缓冲输入（处理流）
└── OutputStream
    ├── FileOutputStream：文件输出
    ├── ByteArrayOutputStream：字节数组输出
    └── BufferedOutputStream：缓冲输出（处理流）

字符流：
├── Reader
│   ├── FileReader：文件读取
│   ├── CharArrayReader：字符数组读取
│   ├── BufferedReader：缓冲读取（处理流）
│   └── InputStreamReader：字节流→字符流转换
└── Writer
    ├── FileWriter：文件写入
    ├── CharArrayWriter：字符数组写入
    ├── BufferedWriter：缓冲写入（处理流）
    └── OutputStreamWriter：字符流→字节流转换
```

---

### 7.2 字节流 vs 字符流

**使用场景**：
```java
// 字节流：处理二进制数据（图片、视频、音频等）
try (FileInputStream fis = new FileInputStream("image.jpg");
     FileOutputStream fos = new FileOutputStream("copy.jpg")) {
    byte[] buffer = new byte[1024];
    int len;
    while ((len = fis.read(buffer)) != -1) {
        fos.write(buffer, 0, len);
    }
}

// 字符流：处理文本数据
try (FileReader fr = new FileReader("file.txt");
     FileWriter fw = new FileWriter("copy.txt")) {
    char[] buffer = new char[1024];
    int len;
    while ((len = fr.read(buffer)) != -1) {
        fw.write(buffer, 0, len);
    }
}
```

**字符流编码**：
```java
// 指定编码
try (InputStreamReader isr = new InputStreamReader(
        new FileInputStream("file.txt"), StandardCharsets.UTF_8);
     OutputStreamWriter osw = new OutputStreamWriter(
        new FileOutputStream("output.txt"), StandardCharsets.UTF_8)) {
    // ...
}
```

---

### 7.3 缓冲流原理

**为什么需要缓冲流**：
- 减少系统调用次数
- 批量读写，提高效率

**BufferedInputStream原理**：
```java
public class BufferedInputStream extends FilterInputStream {
    // 默认缓冲区大小：8KB
    private static int DEFAULT_BUFFER_SIZE = 8192;
    
    // 缓冲区
    protected volatile byte buf[];
    
    public synchronized int read() throws IOException {
        if (pos >= count) {
            fill();  // 缓冲区读完，重新填充
            if (pos >= count)
                return -1;
        }
        return getBufIfOpen()[pos++] & 0xff;
    }
    
    private void fill() throws IOException {
        // 一次性从底层流读取8KB数据到缓冲区
        int n = getInIfOpen().read(buf, pos, buf.length - pos);
        if (n > 0)
            count = pos + n;
    }
}
```

**性能对比**：
```java
// 不使用缓冲：每次read()都是系统调用，慢
try (FileInputStream fis = new FileInputStream("file.txt")) {
    int b;
    while ((b = fis.read()) != -1) {  // 每次读1字节
        // ...
    }
}

// 使用缓冲：8KB缓冲区，减少系统调用
try (BufferedInputStream bis = new BufferedInputStream(
        new FileInputStream("file.txt"))) {
    int b;
    while ((b = bis.read()) != -1) {  // 实际从缓冲区读
        // ...
    }
}
```

---

### 7.4 NIO（New IO）

**核心概念**：
```
传统IO（BIO）：面向流，阻塞IO
NIO：面向缓冲区（Buffer），非阻塞IO，选择器（Selector）
```

**核心组件**：
```java
// 1. Buffer：数据缓冲区
ByteBuffer buffer = ByteBuffer.allocate(1024);

// 2. Channel：数据通道
FileChannel channel = FileChannel.open(Paths.get("file.txt"));

// 3. Selector：选择器（多路复用）
Selector selector = Selector.open();
channel.register(selector, SelectionKey.OP_READ);
```

**Buffer核心操作**：
```java
ByteBuffer buffer = ByteBuffer.allocate(10);

// 写模式
buffer.put("hello".getBytes());  // position移动
buffer.flip();  // 切换到读模式：limit=position, position=0

// 读模式
byte[] data = new byte[buffer.remaining()];
buffer.get(data);  // position移动

// 清空
buffer.clear();  // 切换到写模式：position=0, limit=capacity
```

**Channel读写**：
```java
// 读取文件
try (FileChannel channel = FileChannel.open(Paths.get("file.txt"))) {
    ByteBuffer buffer = ByteBuffer.allocate(1024);
    int bytesRead = channel.read(buffer);  // 从Channel读到Buffer
    buffer.flip();
    while (buffer.hasRemaining()) {
        System.out.print((char) buffer.get());
    }
}

// 写入文件
try (FileChannel channel = FileChannel.open(Paths.get("output.txt"),
        StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
    ByteBuffer buffer = ByteBuffer.wrap("hello".getBytes());
    channel.write(buffer);  // 从Buffer写到Channel
}
```

---

## 8. 反射机制

### 8.1 什么是反射

**定义**：
- 在运行时动态获取类的信息（类名、方法、字段等）
- 在运行时动态调用对象的方法、访问字段

**核心类**：
```java
Class<?>        // 类对象
Field           // 字段
Method          // 方法
Constructor     // 构造方法
```

---

### 8.2 获取Class对象

**三种方式**：
```java
// 1. Class.forName()
Class<?> clazz1 = Class.forName("java.lang.String");

// 2. 类名.class
Class<?> clazz2 = String.class;

// 3. 对象.getClass()
String str = "hello";
Class<?> clazz3 = str.getClass();

// 三者相同
System.out.println(clazz1 == clazz2);  // true
System.out.println(clazz2 == clazz3);  // true
```

---

### 8.3 反射操作

**① 创建对象**：
```java
Class<?> clazz = Class.forName("com.example.User");

// 无参构造
Object obj = clazz.newInstance();  // JDK 9已过时

// 推荐方式
Constructor<?> constructor = clazz.getConstructor();
Object obj2 = constructor.newInstance();

// 有参构造
Constructor<?> constructor2 = clazz.getConstructor(String.class, int.class);
Object obj3 = constructor2.newInstance("张三", 20);
```

**② 访问字段**：
```java
Class<?> clazz = User.class;
User user = new User("张三", 20);

// 获取字段
Field field = clazz.getDeclaredField("name");  // 包括private
field.setAccessible(true);  // 绕过访问控制

// 读取字段值
String name = (String) field.get(user);

// 设置字段值
field.set(user, "李四");
```

**③ 调用方法**：
```java
Class<?> clazz = User.class;
User user = new User("张三", 20);

// 获取方法
Method method = clazz.getDeclaredMethod("setName", String.class);
method.setAccessible(true);

// 调用方法
method.invoke(user, "王五");  // user.setName("王五")
```

---

### 8.4 反射原理

**Method.invoke()原理**：
```java
public Object invoke(Object obj, Object... args) {
    // 1. 权限检查
    if (!override) {
        if (!Reflection.quickCheckMemberAccess(clazz, modifiers)) {
            checkAccess(...);
        }
    }
    
    // 2. 方法调用
    // 前15次：使用JNI（本地方法）
    // 第16次及以后：生成字节码，直接调用（性能提升）
    MethodAccessor ma = acquireMethodAccessor();
    return ma.invoke(obj, args);
}
```

**性能优化**：
- 缓存Method对象，避免重复查找
- setAccessible(true)，避免权限检查

---

### 8.5 反射应用场景

**① 框架开发**：
```java
// Spring IOC：反射创建Bean
Class<?> clazz = Class.forName(beanClassName);
Object bean = clazz.newInstance();

// Spring AOP：反射调用方法
Method method = target.getClass().getMethod(methodName, paramTypes);
method.invoke(target, args);
```

**② 动态代理**：
```java
// JDK动态代理基于反射实现
Object proxy = Proxy.newProxyInstance(
    classLoader,
    interfaces,
    new InvocationHandler() {
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) {
            // 反射调用原方法
            return method.invoke(target, args);
        }
    }
);
```

**③ 注解处理**：
```java
// 获取注解
if (method.isAnnotationPresent(MyAnnotation.class)) {
    MyAnnotation annotation = method.getAnnotation(MyAnnotation.class);
    String value = annotation.value();
}
```

---

## 9. 泛型原理

### 9.1 什么是泛型

**定义**：
- 参数化类型
- 编译时类型检查
- 避免类型转换

**泛型类**：
```java
public class Box<T> {
    private T data;
    
    public void set(T data) {
        this.data = data;
    }
    
    public T get() {
        return data;
    }
}

// 使用
Box<String> box = new Box<>();
box.set("hello");
String str = box.get();  // 无需强转
```

---

### 9.2 类型擦除

**原理**：
- 泛型只在编译期存在
- 编译后，泛型信息被擦除，替换为Object或上界类型

**示例**：
```java
// 编译前
public class Box<T> {
    private T data;
    public T get() { return data; }
}

// 编译后（类型擦除）
public class Box {
    private Object data;  // T被擦除为Object
    public Object get() { return data; }
}

// 使用泛型时，编译器自动插入强转
Box<String> box = new Box<>();
String str = box.get();
// 编译后：String str = (String) box.get();
```

**有上界的泛型**：
```java
// 编译前
public class Box<T extends Number> {
    private T data;
    public T get() { return data; }
}

// 编译后
public class Box {
    private Number data;  // T被擦除为Number
    public Number get() { return data; }
}
```

---

### 9.3 泛型通配符

**① 无界通配符 `<?>`**：
```java
public void print(List<?> list) {
    for (Object obj : list) {
        System.out.println(obj);
    }
}
```

**② 上界通配符 `<? extends T>`**：
```java
// 只能读取，不能写入（除了null）
public double sum(List<? extends Number> list) {
    double sum = 0;
    for (Number num : list) {
        sum += num.doubleValue();  // 可以读取
    }
    // list.add(1);  // 编译错误！不能写入
    return sum;
}

List<Integer> ints = Arrays.asList(1, 2, 3);
sum(ints);  // 可以传入List<Integer>
```

**③ 下界通配符 `<? super T>`**：
```java
// 可以写入T及其子类，读取只能用Object接收
public void addNumbers(List<? super Integer> list) {
    list.add(1);  // 可以写入Integer
    list.add(2);
    // Integer num = list.get(0);  // 编译错误！
    Object obj = list.get(0);  // 只能用Object接收
}

List<Number> numbers = new ArrayList<>();
addNumbers(numbers);  // 可以传入List<Number>
```

**PECS原则**：
```
Producer Extends, Consumer Super

- 如果只需要从集合读取，使用 <? extends T>（生产者）
- 如果只需要向集合写入，使用 <? super T>（消费者）
```

---

### 9.4 泛型方法

**定义**：
```java
public class GenericMethod {
    // 泛型方法：<T>声明类型参数
    public <T> T get(List<T> list, int index) {
        return list.get(index);
    }
    
    // 多个类型参数
    public <K, V> void print(Map<K, V> map) {
        for (Map.Entry<K, V> entry : map.entrySet()) {
            System.out.println(entry.getKey() + " = " + entry.getValue());
        }
    }
    
    // 有上界的泛型方法
    public <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) > 0 ? a : b;
    }
}
```

---

## 10. 注解与处理器

### 10.1 注解基础

**定义注解**：
```java
@Target(ElementType.METHOD)  // 作用目标：方法
@Retention(RetentionPolicy.RUNTIME)  // 保留到运行时
public @interface MyAnnotation {
    String value() default "";  // 注解属性
    int age() default 0;
}
```

**元注解**：
```java
@Target：指定注解作用目标
    - ElementType.TYPE：类、接口、枚举
    - ElementType.FIELD：字段
    - ElementType.METHOD：方法
    - ElementType.PARAMETER：参数
    - ElementType.CONSTRUCTOR：构造方法

@Retention：指定注解保留策略
    - RetentionPolicy.SOURCE：源码期（编译后丢弃）
    - RetentionPolicy.CLASS：字节码期（默认，运行时不可见）
    - RetentionPolicy.RUNTIME：运行时（可通过反射获取）

@Documented：生成JavaDoc时包含注解信息
@Inherited：注解可被子类继承
```

---

### 10.2 注解处理

**运行时处理**：
```java
@MyAnnotation(value = "test", age = 20)
public void myMethod() {
    // ...
}

// 反射获取注解
Method method = clazz.getMethod("myMethod");
if (method.isAnnotationPresent(MyAnnotation.class)) {
    MyAnnotation annotation = method.getAnnotation(MyAnnotation.class);
    String value = annotation.value();  // "test"
    int age = annotation.age();  // 20
}
```

**编译时处理（注解处理器）**：
```java
@SupportedAnnotationTypes("com.example.MyAnnotation")
@SupportedSourceVersion(SourceVersion.RELEASE_8)
public class MyProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations,
                          RoundEnvironment roundEnv) {
        // 编译时处理注解，生成代码
        for (Element element : roundEnv.getElementsAnnotatedWith(MyAnnotation.class)) {
            // 处理逻辑
        }
        return true;
    }
}
```

---

### 10.3 常见注解

**JDK内置注解**：
```java
@Override：标记方法覆盖父类方法
@Deprecated：标记过时的API
@SuppressWarnings：抑制编译警告
@FunctionalInterface：标记函数式接口（只有一个抽象方法）
```

**Spring注解**：
```java
@Component, @Service, @Repository, @Controller：组件注解
@Autowired：自动注入
@RequestMapping：请求映射
@Transactional：事务管理
```

**Lombok注解**：
```java
@Data：自动生成getter/setter/toString/equals/hashCode
@Getter/@Setter：生成getter/setter
@NoArgsConstructor/@AllArgsConstructor：生成构造方法
@Builder：生成Builder模式代码
```

---

## 11. Lambda与Stream API

### 11.1 Lambda表达式

**什么是Lambda**：
```java
/**
 * Lambda表达式：匿名函数的简写形式
 * 
 * 语法：(参数列表) -> { 方法体 }
 * 
 * 要求：只能用于函数式接口（只有一个抽象方法的接口）
 */
```

**语法示例**：
```java
// 传统匿名内部类
Runnable r1 = new Runnable() {
    @Override
    public void run() {
        System.out.println("Hello");
    }
};

// Lambda表达式
Runnable r2 = () -> System.out.println("Hello");

// 多参数Lambda
Comparator<Integer> c1 = (a, b) -> a - b;

// 完整语法
Comparator<Integer> c2 = (Integer a, Integer b) -> {
    return a - b;
};

// 简化：类型推断 + 单语句省略return
Comparator<Integer> c3 = (a, b) -> a - b;
```

**函数式接口**：
```java
// @FunctionalInterface注解（可选，但推荐）
@FunctionalInterface
public interface MyFunction {
    void apply(String str);  // 只有一个抽象方法
    
    // 可以有默认方法
    default void defaultMethod() {
        System.out.println("default");
    }
    
    // 可以有静态方法
    static void staticMethod() {
        System.out.println("static");
    }
}

// 使用
MyFunction func = (str) -> System.out.println(str);
func.apply("Hello");  // Hello
```

**JDK内置函数式接口**：
```java
/**
 * 1. Consumer<T>：消费型接口
 *    void accept(T t)
 */
Consumer<String> consumer = str -> System.out.println(str);
consumer.accept("Hello");

/**
 * 2. Supplier<T>：供给型接口
 *    T get()
 */
Supplier<String> supplier = () -> "Hello";
String result = supplier.get();

/**
 * 3. Function<T, R>：函数型接口
 *    R apply(T t)
 */
Function<String, Integer> function = str -> str.length();
Integer length = function.apply("Hello");  // 5

/**
 * 4. Predicate<T>：断言型接口
 *    boolean test(T t)
 */
Predicate<Integer> predicate = num -> num > 10;
boolean isGreater = predicate.test(15);  // true

/**
 * 5. BiFunction<T, U, R>：二元函数
 *    R apply(T t, U u)
 */
BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;
Integer sum = add.apply(1, 2);  // 3
```

---

### 11.2 方法引用

**四种方法引用**：
```java
// 1. 静态方法引用：类名::静态方法
Function<String, Integer> parseInt1 = str -> Integer.parseInt(str);
Function<String, Integer> parseInt2 = Integer::parseInt;  // 简化

// 2. 实例方法引用：对象::实例方法
String str = "hello";
Supplier<String> upper1 = () -> str.toUpperCase();
Supplier<String> upper2 = str::toUpperCase;  // 简化

// 3. 类的实例方法引用：类名::实例方法
Function<String, Integer> length1 = str -> str.length();
Function<String, Integer> length2 = String::length;  // 简化

// 4. 构造方法引用：类名::new
Supplier<List<String>> list1 = () -> new ArrayList<>();
Supplier<List<String>> list2 = ArrayList::new;  // 简化

Function<Integer, String[]> array1 = size -> new String[size];
Function<Integer, String[]> array2 = String[]::new;  // 简化
```

**实战示例**：
```java
public class MethodReferenceDemo {
    public static void main(String[] args) {
        List<String> list = Arrays.asList("apple", "banana", "cherry");
        
        // 传统方式
        list.forEach(new Consumer<String>() {
            @Override
            public void accept(String s) {
                System.out.println(s);
            }
        });
        
        // Lambda
        list.forEach(s -> System.out.println(s));
        
        // 方法引用
        list.forEach(System.out::println);
    }
}
```

---

### 11.3 Stream API基础

**什么是Stream**：
```java
/**
 * Stream：元素流，用于对集合进行声明式操作
 * 
 * 特点：
 * 1. 不存储数据（数据在原集合中）
 * 2. 不修改数据源
 * 3. 惰性求值（中间操作不会立即执行）
 * 4. 一次性使用（流只能使用一次）
 */
```

**Stream创建**：
```java
// 1. 从集合创建
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> stream1 = list.stream();

// 2. 从数组创建
String[] array = {"a", "b", "c"};
Stream<String> stream2 = Arrays.stream(array);

// 3. 使用Stream.of()
Stream<String> stream3 = Stream.of("a", "b", "c");

// 4. 无限流
Stream<Integer> stream4 = Stream.iterate(0, n -> n + 2);  // 0, 2, 4, 6...
Stream<Double> stream5 = Stream.generate(Math::random);

// 5. 并行流
Stream<String> parallelStream = list.parallelStream();
```

---

### 11.4 Stream中间操作

**① filter：过滤**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6);

// 筛选偶数
List<Integer> even = numbers.stream()
    .filter(n -> n % 2 == 0)
    .collect(Collectors.toList());
// [2, 4, 6]
```

**② map：映射**：
```java
List<String> names = Arrays.asList("alice", "bob", "charlie");

// 转大写
List<String> upper = names.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());
// ["ALICE", "BOB", "CHARLIE"]

// 提取长度
List<Integer> lengths = names.stream()
    .map(String::length)
    .collect(Collectors.toList());
// [5, 3, 7]
```

**③ flatMap：扁平化映射**：
```java
List<List<String>> lists = Arrays.asList(
    Arrays.asList("a", "b"),
    Arrays.asList("c", "d")
);

// flatMap：将多个流合并为一个流
List<String> flat = lists.stream()
    .flatMap(Collection::stream)
    .collect(Collectors.toList());
// ["a", "b", "c", "d"]
```

**④ distinct：去重**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 2, 3, 3, 3);

List<Integer> distinct = numbers.stream()
    .distinct()
    .collect(Collectors.toList());
// [1, 2, 3]
```

**⑤ sorted：排序**：
```java
List<Integer> numbers = Arrays.asList(3, 1, 4, 1, 5, 9);

// 自然排序
List<Integer> sorted1 = numbers.stream()
    .sorted()
    .collect(Collectors.toList());
// [1, 1, 3, 4, 5, 9]

// 自定义排序
List<Integer> sorted2 = numbers.stream()
    .sorted((a, b) -> b - a)  // 降序
    .collect(Collectors.toList());
// [9, 5, 4, 3, 1, 1]
```

**⑥ limit / skip：截取**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

// 取前3个
List<Integer> limited = numbers.stream()
    .limit(3)
    .collect(Collectors.toList());
// [1, 2, 3]

// 跳过前2个
List<Integer> skipped = numbers.stream()
    .skip(2)
    .collect(Collectors.toList());
// [3, 4, 5]
```

**⑦ peek：调试**：
```java
// peek：不改变流，但可以查看元素
List<Integer> result = numbers.stream()
    .filter(n -> n > 2)
    .peek(n -> System.out.println("过滤后: " + n))
    .map(n -> n * 2)
    .peek(n -> System.out.println("映射后: " + n))
    .collect(Collectors.toList());
```

---

### 11.5 Stream终端操作

**① collect：收集**：
```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");

// 转List
List<String> list = names.stream().collect(Collectors.toList());

// 转Set
Set<String> set = names.stream().collect(Collectors.toSet());

// 转Map
Map<String, Integer> map = names.stream()
    .collect(Collectors.toMap(
        name -> name,           // key
        name -> name.length()   // value
    ));
// {Alice=5, Bob=3, Charlie=7}

// 拼接字符串
String joined = names.stream()
    .collect(Collectors.joining(", "));
// "Alice, Bob, Charlie"

// 分组
Map<Integer, List<String>> grouped = names.stream()
    .collect(Collectors.groupingBy(String::length));
// {3=[Bob], 5=[Alice], 7=[Charlie]}

// 分区（按boolean分组）
Map<Boolean, List<String>> partitioned = names.stream()
    .collect(Collectors.partitioningBy(name -> name.length() > 4));
// {false=[Bob], true=[Alice, Charlie]}
```

**② forEach：遍历**：
```java
names.stream().forEach(System.out::println);

// 注意：forEach是终端操作，流会被消费
```

**③ reduce：归约**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

// 求和
int sum = numbers.stream()
    .reduce(0, (a, b) -> a + b);  // 15

// 简化
int sum2 = numbers.stream().reduce(0, Integer::sum);

// 求最大值
Optional<Integer> max = numbers.stream()
    .reduce((a, b) -> a > b ? a : b);
// Optional[5]

// 字符串拼接
String concat = Stream.of("a", "b", "c")
    .reduce("", (a, b) -> a + b);  // "abc"
```

**④ count / min / max / sum / average**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

long count = numbers.stream().count();  // 5

Optional<Integer> min = numbers.stream().min(Integer::compareTo);  // 1
Optional<Integer> max = numbers.stream().max(Integer::compareTo);  // 5

// IntStream特有方法
IntStream intStream = numbers.stream().mapToInt(Integer::intValue);
int sum = intStream.sum();  // 15

OptionalDouble avg = numbers.stream()
    .mapToInt(Integer::intValue)
    .average();  // 3.0
```

**⑤ allMatch / anyMatch / noneMatch**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

boolean allEven = numbers.stream().allMatch(n -> n % 2 == 0);  // false
boolean anyEven = numbers.stream().anyMatch(n -> n % 2 == 0);  // true
boolean noneNegative = numbers.stream().noneMatch(n -> n < 0); // true
```

**⑥ findFirst / findAny**：
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

Optional<Integer> first = numbers.stream().findFirst();  // 1

// 并行流中findAny性能更好
Optional<Integer> any = numbers.parallelStream().findAny();
```

---

### 11.6 Stream实战案例

**案例1：员工数据处理**：
```java
class Employee {
    String name;
    int age;
    double salary;
    
    // 构造方法、getter、setter省略
}

List<Employee> employees = Arrays.asList(
    new Employee("Alice", 25, 5000),
    new Employee("Bob", 30, 6000),
    new Employee("Charlie", 35, 7000),
    new Employee("David", 28, 5500)
);

// 1. 筛选工资>5500的员工，按工资降序，取前2名
List<Employee> top2 = employees.stream()
    .filter(e -> e.getSalary() > 5500)
    .sorted((e1, e2) -> Double.compare(e2.getSalary(), e1.getSalary()))
    .limit(2)
    .collect(Collectors.toList());

// 2. 按年龄分组
Map<Integer, List<Employee>> byAge = employees.stream()
    .collect(Collectors.groupingBy(Employee::getAge));

// 3. 统计平均工资
double avgSalary = employees.stream()
    .mapToDouble(Employee::getSalary)
    .average()
    .orElse(0.0);

// 4. 提取所有员工姓名，逗号分隔
String names = employees.stream()
    .map(Employee::getName)
    .collect(Collectors.joining(", "));
```

**案例2：文件处理**：
```java
public class FileStreamDemo {
    public static void main(String[] args) throws IOException {
        // 读取文件所有行
        try (Stream<String> lines = Files.lines(Paths.get("data.txt"))) {
            // 统计包含"error"的行数
            long errorCount = lines
                .filter(line -> line.contains("error"))
                .count();
            System.out.println("错误行数: " + errorCount);
        }
        
        // 统计单词频率
        try (Stream<String> lines = Files.lines(Paths.get("data.txt"))) {
            Map<String, Long> wordFreq = lines
                .flatMap(line -> Arrays.stream(line.split("\\s+")))
                .map(String::toLowerCase)
                .collect(Collectors.groupingBy(
                    word -> word,
                    Collectors.counting()
                ));
            System.out.println(wordFreq);
        }
    }
}
```

**案例3：并行流性能优化**：
```java
public class ParallelStreamDemo {
    public static void main(String[] args) {
        List<Integer> numbers = IntStream.rangeClosed(1, 1000000)
            .boxed()
            .collect(Collectors.toList());
        
        // 顺序流
        long start = System.currentTimeMillis();
        long sum1 = numbers.stream()
            .filter(n -> n % 2 == 0)
            .mapToLong(Integer::longValue)
            .sum();
        System.out.println("顺序流耗时: " + (System.currentTimeMillis() - start) + "ms");
        
        // 并行流
        start = System.currentTimeMillis();
        long sum2 = numbers.parallelStream()
            .filter(n -> n % 2 == 0)
            .mapToLong(Integer::longValue)
            .sum();
        System.out.println("并行流耗时: " + (System.currentTimeMillis() - start) + "ms");
    }
}
```

**并行流注意事项**：
```java
/**
 * 适合并行流的场景：
 * 1. 数据量大（至少几千个元素）
 * 2. 每个元素处理耗时
 * 3. 操作无状态（不依赖外部变量）
 * 4. 数据结构易分割（ArrayList > LinkedList）
 * 
 * 不适合并行流的场景：
 * 1. 数据量小
 * 2. 操作有状态（如limit、sorted）
 * 3. 需要保持顺序
 * 4. 操作有副作用（修改外部变量）
 */

// ❌ 错误：并行流中修改外部变量
List<Integer> list = new ArrayList<>();
IntStream.range(1, 10000).parallel().forEach(list::add);  // 线程不安全！

// ✅ 正确：使用线程安全的容器
List<Integer> list2 = new CopyOnWriteArrayList<>();
IntStream.range(1, 10000).parallel().forEach(list2::add);

// ✅ 更好：使用collect
List<Integer> list3 = IntStream.range(1, 10000)
    .parallel()
    .boxed()
    .collect(Collectors.toList());
```

---

## 12. Java新特性总结

### 12.1 JDK 8特性

**① Lambda表达式**：
```java
// 函数式接口
list.forEach(item -> System.out.println(item));
list.sort((a, b) -> a.compareTo(b));
```

**② Stream API**：
```java
list.stream()
    .filter(s -> s.startsWith("A"))
    .map(String::toUpperCase)
    .collect(Collectors.toList());
```

**③ Optional**：
```java
Optional<String> opt = Optional.ofNullable(str);
String result = opt.orElse("default");

// 链式调用
opt.map(String::toUpperCase)
   .filter(s -> s.length() > 5)
   .ifPresent(System.out::println);
```

**④ 接口默认方法和静态方法**：
```java
interface MyInterface {
    default void defaultMethod() {
        System.out.println("default");
    }
    
    static void staticMethod() {
        System.out.println("static");
    }
}
```

**⑤ 新日期时间API**：
```java
// 替代Date和Calendar
LocalDate date = LocalDate.now();  // 2025-10-28
LocalTime time = LocalTime.now();  // 14:30:00
LocalDateTime dt = LocalDateTime.now();  // 2025-10-28T14:30:00

// 日期计算
LocalDate tomorrow = date.plusDays(1);
LocalDate lastMonth = date.minusMonths(1);

// 格式化
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
String formatted = dt.format(formatter);
```

---

### 12.2 JDK 9特性

**① 模块化系统（Jigsaw）**：
```java
// module-info.java
module com.example.myapp {
    requires java.sql;
    exports com.example.myapp.api;
}
```

**② 接口私有方法**：
```java
interface MyInterface {
    default void method1() {
        commonLogic();
    }
    
    default void method2() {
        commonLogic();
    }
    
    private void commonLogic() {
        System.out.println("common");
    }
}
```

**③ 集合工厂方法**：
```java
// 创建不可变集合
List<String> list = List.of("a", "b", "c");
Set<String> set = Set.of("a", "b", "c");
Map<String, Integer> map = Map.of("a", 1, "b", 2);
```

**④ Stream API增强**：
```java
// takeWhile：遇到不满足条件的元素就停止
Stream.of(1, 2, 3, 4, 5).takeWhile(n -> n < 4);  // [1, 2, 3]

// dropWhile：跳过满足条件的元素
Stream.of(1, 2, 3, 4, 5).dropWhile(n -> n < 4);  // [4, 5]

// ofNullable：允许单个null
Stream.ofNullable(null).count();  // 0
```

---

### 12.3 JDK 10特性

**① 局部变量类型推断（var）**：
```java
// 编译器自动推断类型
var list = new ArrayList<String>();  // ArrayList<String>
var str = "hello";  // String
var num = 10;  // int

// 不能用于：
// - 成员变量
// - 方法参数
// - 方法返回值
```

**② 不可变集合增强**：
```java
// copyOf：创建不可变副本
List<String> copy = List.copyOf(list);
```

---

### 12.4 JDK 11特性（LTS长期支持版本）

**① String新方法**：
```java
// isBlank：是否空白
" ".isBlank();  // true

// strip：去除首尾空白（支持Unicode）
" hello ".strip();  // "hello"

// lines：按行分割
"a\nb\nc".lines().count();  // 3

// repeat：重复
"ab".repeat(3);  // "ababab"
```

**② 文件操作增强**：
```java
// 直接读写文件
String content = Files.readString(Path.of("file.txt"));
Files.writeString(Path.of("file.txt"), "content");
```

**③ HTTP Client标准化**：
```java
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com"))
    .build();
HttpResponse<String> response = client.send(request, 
    HttpResponse.BodyHandlers.ofString());
```

---

### 12.5 JDK 14特性

**① Switch表达式（正式版）**：
```java
// 传统switch
String result;
switch (day) {
    case MONDAY:
    case TUESDAY:
        result = "Weekday";
        break;
    case SATURDAY:
    case SUNDAY:
        result = "Weekend";
        break;
    default:
        result = "Invalid";
}

// 新switch表达式
String result = switch (day) {
    case MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY -> "Weekday";
    case SATURDAY, SUNDAY -> "Weekend";
    default -> "Invalid";
};

// 使用yield返回值
String result = switch (day) {
    case MONDAY, TUESDAY -> {
        System.out.println("It's a weekday");
        yield "Weekday";
    }
    default -> "Other";
};
```

**② NullPointerException增强**：
```java
// 详细的空指针异常信息
user.getAddress().getCity().getName();
// 以前：NullPointerException
// 现在：NullPointerException: Cannot invoke "City.getName()" because the return value of "Address.getCity()" is null
```

---

### 12.6 JDK 15特性

**① 文本块（Text Blocks）**：
```java
// 传统多行字符串
String html = "<html>\n" +
              "  <body>\n" +
              "    <p>Hello</p>\n" +
              "  </body>\n" +
              "</html>";

// 文本块
String html = """
              <html>
                <body>
                  <p>Hello</p>
                </body>
              </html>
              """;

// JSON示例
String json = """
              {
                "name": "John",
                "age": 30
              }
              """;
```

---

### 12.7 JDK 16特性

**① Record类**：
```java
// 传统JavaBean
public class Point {
    private final int x;
    private final int y;
    
    public Point(int x, int y) {
        this.x = x;
        this.y = y;
    }
    
    public int getX() { return x; }
    public int getY() { return y; }
    
    @Override
    public boolean equals(Object o) { /* ... */ }
    @Override
    public int hashCode() { /* ... */ }
    @Override
    public String toString() { /* ... */ }
}

// Record类（自动生成构造方法、getter、equals、hashCode、toString）
public record Point(int x, int y) {
    // 可选：自定义构造方法
    public Point {
        if (x < 0 || y < 0) {
            throw new IllegalArgumentException("Coordinates must be positive");
        }
    }
    
    // 可选：自定义方法
    public double distanceFromOrigin() {
        return Math.sqrt(x * x + y * y);
    }
}

// 使用
Point p = new Point(3, 4);
System.out.println(p.x());  // 3
System.out.println(p);      // Point[x=3, y=4]
```

**② instanceof模式匹配**：
```java
// 传统方式
if (obj instanceof String) {
    String str = (String) obj;
    System.out.println(str.length());
}

// 模式匹配
if (obj instanceof String str) {
    System.out.println(str.length());  // 自动转换
}

// 结合逻辑运算
if (obj instanceof String str && str.length() > 5) {
    System.out.println(str.toUpperCase());
}
```

---

### 12.8 JDK 17特性（LTS长期支持版本）

**① Sealed Classes（密封类）**：
```java
// 限制哪些类可以继承
public sealed class Shape
    permits Circle, Rectangle, Triangle {
}

public final class Circle extends Shape {
    // final：不能再被继承
}

public non-sealed class Rectangle extends Shape {
    // non-sealed：可以被任意类继承
}

public sealed class Triangle extends Shape
    permits EquilateralTriangle {
    // sealed：继续限制子类
}
```

**② 恢复始终严格的浮点语义**：
```java
// 浮点运算结果在所有平台保持一致
```

### 12.8.2 JDK 18-21 新特性

#### JDK 18（2022.3）
**① 默认UTF-8编码**：
```java
// JDK 18之前：默认编码依赖操作系统
// JDK 18+：默认使用UTF-8
System.out.println(Charset.defaultCharset()); // UTF-8

// 可以通过系统属性覆盖
// -Dfile.encoding=COMPAT  // 恢复旧行为
```

**② Simple Web Server**：
```bash
# 启动最小HTTP服务器（无需第三方库）
jwebserver
# 默认端口8000，服务于当前目录
# 适用于开发测试、原型演示
```

**③ 代码片段标签（@snippet）**：
```java
/**
 * {@snippet :
 * var list = List.of("A", "B", "C"); // @highlight substring="List.of"
 * }
 */
```

#### JDK 19（2022.9）
**① 虚拟线程（Preview）**：
```java
// 首次预览虚拟线程（详见Java并发编程详解）
// 需要启用：--enable-preview
```

**② 结构化并发（Incubator）**：
```java
// 首次引入结构化并发API（Incubator阶段）
```

**③ Record模式匹配（Preview）**：
```java
// 预览阶段的Record解构
```

#### JDK 20（2023.3）
**① 作用域值（Scoped Values）（Incubator）**：
```java
// 首次引入作用域值，替代ThreadLocal的改进方案
```

**② Record模式匹配（第二次预览）**

**③ 虚拟线程（第二次预览）**

#### JDK 21（2023.9）⭐ LTS
**① 虚拟线程（Virtual Threads）正式发布**：
```java
// 创建虚拟线程的几种方式
// 方式1：Thread.startVirtualThread
Thread vt = Thread.startVirtualThread(() -> {
    System.out.println("虚拟线程: " + Thread.currentThread());
});

// 方式2：Thread.ofVirtual()
Thread vt2 = Thread.ofVirtual()
    .name("my-virtual-thread")
    .start(() -> System.out.println("Hello"));

// 方式3：Executors.newVirtualThreadPerTaskExecutor
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    // 每个任务分配一个虚拟线程
    executor.submit(() -> doTask());
}

// 虚拟线程 vs 平台线程
// 虚拟线程：轻量级（可创建百万级），自动挂起/恢复，适合IO密集型
// 平台线程：与OS线程1:1映射，数量有限（通常几千），适合CPU密集型
```

**② Record模式匹配（Pattern Matching）正式发布**：
```java
// JDK 16: instanceof模式匹配
if (obj instanceof String s) {
    System.out.println(s.length());
}

// JDK 21: Record解构
record Point(int x, int y) {}

// 解构Record
if (obj instanceof Point(int x, int y)) {
    System.out.println("x=" + x + ", y=" + y);
}

// 嵌套解构
record Rectangle(Point upperLeft, Point lowerRight) {}
if (obj instanceof Rectangle(Point(int x1, int y1), Point(int x2, int y2))) {
    System.out.println("矩形: (" + x1 + "," + y1 + ")-(" + x2 + "," + y2 + ")");
}

// switch中使用
switch (shape) {
    case Point(int x, int y) -> "点(" + x + "," + y + ")";
    case Rectangle(Point(int x1, int y1), Point(int x2, int y2)) -> 
        "矩形(" + x1 + "," + y1 + ")-(" + x2 + "," + y2 + ")";
    default -> "未知形状";
}
```

**③ Switch模式匹配正式发布**：
```java
// JDK 21: switch模式匹配
static String formatterPatternSwitch(Object obj) {
    return switch (obj) {
        case Integer i -> String.format("int %d", i);
        case Long l    -> String.format("long %d", l);
        case Double d  -> String.format("double %f", d);
        case String s  -> String.format("String %s", s);
        case null      -> "null";  // 直接匹配null
        default        -> obj.toString();
    };
}

// 带守卫条件的switch
switch (obj) {
    case String s when s.length() > 5 -> "长字符串: " + s;
    case String s                     -> "短字符串: " + s;
    default                           -> "非字符串";
}
```

**④ 顺序集合（Sequenced Collections）**：
```java
// 新接口体系
// SequencedCollection <- List, Deque, SortedSet等
// SequencedSet <- SortedSet, LinkedHashSet等
// SequencedMap <- SortedMap, LinkedHashMap等

// 新增方法
SequencedCollection<String> list = new ArrayList<>(List.of("A", "B", "C"));
list.addFirst("X");     // 头部添加
list.addLast("Z");      // 尾部添加
list.getFirst();        // 获取第一个
list.getLast();         // 获取最后一个
list.removeFirst();     // 移除第一个
list.removeLast();      // 移除最后一个
list.reversed();        // 反转视图（不影响原集合）

// SequencedMap
SequencedMap<String, Integer> map = new LinkedHashMap<>();
map.firstEntry();
map.lastEntry();
map.reversed();
```

**⑤ 字符串模板（String Templates）（Preview）**：
```java
// 预览阶段，需要--enable-preview
// 注意：JDK 22中继续预览，JDK 23中已移除该特性
var name = "World";
var msg = STR."Hello \{name}!";  // 模板表达式
```

### 12.8.3 JDK 22-23 新特性

#### JDK 22（2024.3）
**① 未命名变量与模式**：
```java
// 使用_表示不需要的变量
try {
    // ...
} catch (Exception _) {  // 不使用异常变量
    log.error("操作失败");
}

// lambda中忽略参数
BiPredicate<String, String> isEqual = (_, _) -> true;

// 模式中忽略组件
if (obj instanceof Point(int x, _)) {  // 只关心x
    System.out.println("x = " + x);
}
```

**② 外部函数与内存API（Foreign Function & Memory API）正式发布**：
```java
// 替代JNI的现代API（Panama项目）
// 支持调用C/C++库，无需编写JNI代码
// 更安全、更高效的内存访问
```

**③ Stream Gatherer（Preview）**：
```java
// 自定义中间操作，扩展Stream API
// 内置Gatherer：fold, mapConcurrent, scan, windowFixed等
```

#### JDK 23（2024.9）
**① 原始类型模式匹配（Preview）**：
```java
// 允许在instanceof和switch中匹配原始类型
if (obj instanceof int i) {
    System.out.println("整数: " + i);
}
```

**② ZGC Generational Mode默认启用**

**③ Markdown文档注释**：
```java
/// 这是一个Markdown格式的文档注释
/// 
/// - 支持列表
/// - 支持**粗体**和*斜体*
/// - 支持`代码`
///
/// @param value 输入值
/// @return 结果
public int process(int value) { ... }
```

---

### 12.9 新特性对比表

```
┌──────────┬────────────────────────────────────────────────────┐
│ JDK版本  │            主要特性                                 │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 8    │ Lambda、Stream、Optional、新日期API                │
│          │ 接口默认方法                                        │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 9    │ 模块化、接口私有方法、集合工厂方法                   │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 10   │ var局部变量类型推断                                  │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 11   │ String新方法、HTTP Client、文件操作增强             │
│   (LTS)  │                                                    │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 14   │ Switch表达式、NPE增强                               │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 15   │ 文本块（Text Blocks）                               │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 16   │ Record类、instanceof模式匹配                        │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 17   │ Sealed Classes密封类                                │
│   (LTS)  │                                                    │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 18   │ 默认UTF-8编码、Simple Web Server、@snippet          │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 19   │ 虚拟线程Preview、结构化并发Incubator                 │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 20   │ 作用域值Incubator、Record模式匹配Preview             │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 21   │ 虚拟线程正式版、Switch模式匹配、Record模式匹配       │
│   (LTS)  │ 顺序集合、字符串模板Preview                          │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 22   │ 未命名变量、外部函数与内存API、Stream Gatherer       │
├──────────┼────────────────────────────────────────────────────┤
│ JDK 23   │ 原始类型模式匹配Preview、ZGC分代默认启用              │
│          │ Markdown文档注释                                    │
└──────────┴────────────────────────────────────────────────────┘
```

---

## 📝 总结

### 核心要点

**1. Java平台架构**：
- JDK = JRE + 开发工具
- JRE = JVM + 核心类库
- JVM：类加载、执行引擎、运行时数据区
- JIT编译器：热点代码优化

**2. 面向对象**：
- 封装：隐藏实现细节，访问控制
- 继承：代码复用，类型层次
- 多态：动态绑定，统一处理
- 接口 vs 抽象类：行为契约 vs is-a关系
- 内部类：成员、静态、局部、匿名

**3. 类型系统**：
- 基本类型 vs 包装类
- 自动装箱/拆箱
- Integer缓存机制（-128~127）
- 对象内存布局：对象头+实例数据+对齐填充
- 四种引用：强、软、弱、虚

**4. String**：
- 不可变性：线程安全、常量池复用
- 字符串常量池（JDK 7+在堆中）
- intern()方法原理
- StringBuilder vs StringBuffer
- 性能优化：避免循环+拼接，使用String.join()
- 正则表达式：Pattern缓存

**5. 集合框架**：
- ArrayList：动态数组，扩容1.5倍，O(1)访问
- LinkedList：双向链表，O(1)头尾操作
- HashMap：数组+链表+红黑树，容量2的幂
  - 扩容2倍，负载因子0.75
  - JDK 8：链表长度≥8转红黑树
- ConcurrentHashMap：CAS + synchronized，锁粒度小

**6. 异常处理**：
- Checked vs Unchecked
- try-catch-finally执行顺序
- try-with-resources自动关闭资源
- 自定义异常

**7. IO体系**：
- 字节流 vs 字符流
- 缓冲流原理：8KB缓冲区，减少系统调用
- NIO：Buffer、Channel、Selector非阻塞IO

**8. 反射**：
- 运行时动态操作类、字段、方法
- Method.invoke()原理：前15次JNI，之后生成字节码
- 应用：框架开发、动态代理、注解处理

**9. 泛型**：
- 类型擦除：编译后替换为Object或上界类型
- 泛型通配符：?, extends, super
- PECS原则：Producer Extends, Consumer Super

**10. 注解**：
- 元注解：@Target, @Retention
- 运行时处理：反射获取注解
- 编译时处理：注解处理器生成代码

**11. Lambda与Stream**：
- Lambda表达式：函数式接口的简写
- 方法引用：类名::方法名
- Stream API：声明式集合操作
  - 中间操作：filter, map, flatMap, sorted
  - 终端操作：collect, forEach, reduce
- 并行流：适合大数据量、无状态操作

**12. Java新特性（JDK 8-23）**：
- JDK 8：Lambda、Stream、Optional、新日期API
- JDK 9：模块化、集合工厂方法
- JDK 10：var类型推断
- JDK 11（LTS）：String新方法、HTTP Client
- JDK 14：Switch表达式、NPE增强
- JDK 15：文本块
- JDK 16：Record类、instanceof模式匹配
- JDK 17（LTS）：Sealed Classes密封类
- JDK 18：默认UTF-8编码、Simple Web Server
- JDK 19：虚拟线程Preview、结构化并发Incubator
- JDK 20：作用域值Incubator
- JDK 21（LTS）：虚拟线程正式版、Switch模式匹配、Record模式匹配、顺序集合
- JDK 22：未命名变量、外部函数与内存API、Stream Gatherer
- JDK 23：原始类型模式匹配Preview、ZGC分代默认启用、Markdown文档注释

---

## 📚 学习路线建议

1. **基础阶段**：面向对象、集合框架、异常处理、IO
2. **进阶阶段**：反射、泛型、注解、Lambda/Stream
3. **高级阶段**：并发编程、JVM原理、性能优化
4. **实战阶段**：Spring框架、微服务、分布式系统

---

**相关文档**：
- 《Java并发编程详解》：深入并发机制
- 《JVM虚拟机详解》：深入JVM底层原理

*最后更新：2026-05-22*

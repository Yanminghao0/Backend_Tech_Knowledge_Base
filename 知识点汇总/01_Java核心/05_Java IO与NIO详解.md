# Java IO与NIO详解

> 从BIO到NIO到AIO，Java IO模型演进与Netty基础

---

## 📋 目录

1. [Java IO模型](#1-java-io模型)
2. [BIO（阻塞IO）](#2-bio阻塞io)
3. [NIO（非阻塞IO）](#3-nio非阻塞io)
4. [AIO（异步IO）](#4-aio异步io)
5. [零拷贝技术](#5-零拷贝技术)
6. [面试要点](#6-面试要点)

---

## 1. Java IO模型

### 三种IO模型对比

| 模型 | 全称 | 特点 | 适用场景 |
|------|------|------|---------|
| BIO | Blocking IO | 同步阻塞，一个连接一个线程 | 连接数少 |
| NIO | Non-blocking IO | 同步非阻塞，多路复用，一个线程处理多个连接 | 高并发 |
| AIO | Asynchronous IO | 异步非阻塞，回调通知 | 连接数极多(JDK21+虚拟线程替代) |

### IO模型演进

```
BIO (JDK 1.0)
  ServerSocket.accept() → 阻塞等待连接
  InputStream.read() → 阻塞等待数据
  问题：一个连接占一个线程，线程资源浪费

NIO (JDK 1.4)
  Selector多路复用 → 一个线程管理多个Channel
  Buffer面向缓冲区 → 数据块读写
  问题：API复杂，编程难度高

AIO (JDK 7)
  CompletionHandler回调 → OS完成IO后通知应用
  问题：Linux epoll实现不完善，实际很少用

虚拟线程 (JDK 21)
  回到BIO模型，但每个连接用虚拟线程 → 轻量级
  好处：BIO的简单 + NIO的性能
```

---

## 2. BIO（阻塞IO）

### 传统BIO服务器

```java
public class BioServer {
    public static void main(String[] args) throws IOException {
        ServerSocket serverSocket = new ServerSocket(8080);
        while (true) {
            Socket socket = serverSocket.accept();  // 阻塞等待连接
            new Thread(() -> handle(socket)).start();  // 每个连接一个线程
        }
    }
    
    private static void handle(Socket socket) {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(socket.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {  // 阻塞等待数据
                System.out.println("收到: " + line);
                socket.getOutputStream().write(("Echo: " + line + "\n").getBytes());
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

### BIO的问题

```
1. 线程资源浪费：99%时间在阻塞等待，线程却在占用
2. 线程数限制：一台机器最多几千个线程
3. 线程切换开销大：大量线程频繁上下文切换
4. 不适合高并发：C10K问题（1万并发连接）
```

### 线程池优化

```java
// 用线程池替代无限创建线程
ExecutorService pool = Executors.newFixedThreadPool(200);
while (true) {
    Socket socket = serverSocket.accept();
    pool.submit(() -> handle(socket));
}
// 仍有问题：线程池满后拒绝连接，并发上限受线程数限制
```

---

## 3. NIO（非阻塞IO）

### 三大核心组件

```
1. Channel（通道）：双向数据传输，可读可写
   - SocketChannel：TCP客户端
   - ServerSocketChannel：TCP服务端
   - DatagramChannel：UDP
   - FileChannel：文件

2. Buffer（缓冲区）：数据容器，读写都经过Buffer
   - ByteBuffer, CharBuffer, IntBuffer等
   - 三个指针：position, limit, capacity

3. Selector（选择器）：多路复用器，监控多个Channel的事件
   - OP_ACCEPT：连接就绪
   - OP_READ：读就绪
   - OP_WRITE：写就绪
   - OP_CONNECT：连接完成
```

### Buffer操作

```java
// Buffer读写流程
ByteBuffer buffer = ByteBuffer.allocate(1024);

// 写模式 → 读模式
buffer.put((byte) 1);      // position=1
buffer.put((byte) 2);      // position=2
buffer.flip();              // 切换为读模式：limit=position, position=0

byte b1 = buffer.get();    // b1=1, position=1
byte b2 = buffer.get();    // b2=2, position=2

buffer.clear();             // 清空：position=0, limit=capacity
// compact()：未读数据移到开头，position指向未读数据后

// Buffer核心方法
// allocate(1024)  分配
// put(data)       写入
// flip()          切换读模式
// get()           读取
// clear()         清空
// compact()       压缩（保留未读）
// rewind()        重置position=0（不改变limit）
```

### NIO服务器实现

```java
public class NioServer {
    public static void main(String[] args) throws IOException {
        Selector selector = Selector.open();
        ServerSocketChannel serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(8080));
        serverChannel.configureBlocking(false);  // 非阻塞模式
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);
        
        while (true) {
            selector.select();  // 阻塞直到有事件就绪
            Iterator<SelectionKey> keys = selector.selectedKeys().iterator();
            
            while (keys.hasNext()) {
                SelectionKey key = keys.next();
                keys.remove();
                
                if (key.isAcceptable()) {
                    // 新连接
                    SocketChannel client = serverChannel.accept();
                    client.configureBlocking(false);
                    client.register(selector, SelectionKey.OP_READ);
                } else if (key.isReadable()) {
                    // 数据可读
                    SocketChannel client = (SocketChannel) key.channel();
                    ByteBuffer buffer = ByteBuffer.allocate(1024);
                    int len = client.read(buffer);
                    if (len > 0) {
                        buffer.flip();
                        client.write(buffer);  // Echo
                    } else if (len == -1) {
                        client.close();
                    }
                }
            }
        }
    }
}
``### Selector多路复用原理

```
一个Selector线程管理多个Channel：

  Channel1 ─┐
  Channel2 ─┼─→ Selector（epoll_wait） ─→ 有事件就绪 → 处理
  Channel3 ─┤
  Channel4 ─┘

Linux底层使用epoll：
  - epoll_create：创建epoll实例
  - epoll_ctl：注册/修改/删除监听
  - epoll_wait：等待事件就绪（O(1)复杂度返回就绪事件）

优势：一个线程处理上万连接，线程不阻塞
```

### NIO vs BIO性能对比

```
BIO：1000连接 → 1000线程 → 大量上下文切换
NIO：1000连接 → 1个Selector线程 → 事件驱动

并发连接数：BIO < 5000, NIO > 50000
CPU利用率：BIO低(线程等待), NIO高(事件驱动)
```

---

## 4. AIO（异步IO）

### AIO模型

```java
// AIO：真正的异步IO，OS完成IO后回调通知
public class AioServer {
    public static void main(String[] args) throws IOException {
        AsynchronousServerSocketChannel serverChannel = 
            AsynchronousServerSocketChannel.open()
                .bind(new InetSocketAddress(8080));
        
        // 异步接受连接，回调通知
        serverChannel.accept(null, new CompletionHandler<>() {
            @Override
            public void completed(AsynchronousSocketChannel client, Void attachment) {
                serverChannel.accept(null, this);  // 继续接受下一个连接
                handleClient(client);
            }
            
            @Override
            public void failed(Throwable exc, Void attachment) {
                exc.printStackTrace();
            }
        });
        
        Thread.currentThread().join();  // 保持主线程不退出
    }
    
    private static void handleClient(AsynchronousSocketChannel client) {
        ByteBuffer buffer = ByteBuffer.allocate(1024);
        // 异步读取，回调通知
        client.read(buffer, null, new CompletionHandler<>() {
            @Override
            public void completed(Integer result, Void attachment) {
                buffer.flip();
                client.write(buffer);  // 异步写
            }
            
            @Override
            public void failed(Throwable exc, Void attachment) {
                exc.printStackTrace();
            }
        });
    }
}
```

### AIO的局限性

```
1. Linux平台AIO实现不完善（epoll模拟）
2. 编程模型复杂（回调地狱）
3. 实际生产很少用（Netty用NIO + 自己的异步封装）
4. JDK 21+虚拟线程更简单：BIO写法 + NIO性能
```

---

## 5. 零拷贝技术

### 传统数据传输流程

```
文件 → 内核缓冲区 → 用户缓冲区 → Socket缓冲区 → 网卡

4次上下文切换：
  用户态→内核态(read) → 内核态→用户态(read返回)
  用户态→内核态(write) → 内核态→用户态(write返回)

4次数据拷贝：
  磁盘→内核缓冲区 → 内核缓冲区→用户缓冲区
  用户缓冲区→Socket缓冲区 → Socket缓冲区→网卡
```

### sendfile零拷贝

```
sendfile系统调用：
  文件 → 内核缓冲区 → 网卡（DMA直接传输）

2次上下文切换：
  用户态→内核态(sendfile) → 内核态→用户态(sendfile返回)

2次数据拷贝：
  磁盘→内核缓冲区 → 内核缓冲区→网卡（DMA）

优势：减少2次数据拷贝和2次上下文切换
```

### Java零拷贝API

```java
// FileChannel.transferTo → 底层调用sendfile
FileChannel fileChannel = new FileInputStream("data.txt").getChannel();
SocketChannel socketChannel = SocketChannel.open(
    new InetSocketAddress("localhost", 8080));

// 零拷贝传输
fileChannel.transferTo(0, fileChannel.size(), socketChannel);

// Kafka使用零拷贝：日志文件直接传输到网卡
// Netty使用零拷贝：FileRegion封装transferTo

// MappedByteBuffer → 内存映射文件
MappedByteBuffer mapped = new RandomAccessFile("data.txt", "r")
    .getChannel()
    .map(FileChannel.MapMode.READ_ONLY, 0, 1024);
// 文件直接映射到内存，读取不需要内核态→用户态拷贝
```

### 零拷贝对比

| 方式 | 上下文切换 | 数据拷贝 | 适用场景 |
|------|----------|---------|---------|
| 传统read+write | 4次 | 4次 | - |
| sendfile | 2次 | 2次 | 文件→网络 |
| mmap+write | 4次 | 3次 | 需要修改数据 |
| sendfile+SG-DMA | 2次 | 0次(硬件支持) | 最优 |

---

## 6. 面试要点

### Q1: BIO、NIO、AIO的区别？

```
BIO：同步阻塞，一个连接一个线程，线程在read时阻塞
NIO：同步非阻塞，Selector多路复用，一个线程管理多个连接
AIO：异步非阻塞，OS完成IO后回调通知

性能：BIO < NIO ≈ AIO
编程复杂度：BIO < AIO < NIO
适用：BIO适合少量连接，NIO适合高并发，AIO实际很少用
```

### Q2: NIO的Selector原理？

```
Selector = 多路复用器

1. Channel注册到Selector，指定关注的事件（OP_READ/OP_WRITE等）
2. Selector.select()阻塞等待事件就绪
3. 底层调用OS的epoll_wait（Linux）
4. 有事件就绪时返回就绪的SelectionKey集合
5. 遍历处理每个就绪事件

一个Selector线程可以管理上万Channel，实现高并发
```

### Q3: 零拷贝是什么？为什么能提升性能？

```
零拷贝：减少内核态和用户态之间的数据拷贝

传统：文件→内核缓冲区→用户缓冲区→Socket缓冲区→网卡（4次拷贝）
sendfile：文件→内核缓冲区→网卡（2次拷贝）

减少：2次数据拷贝 + 2次上下文切换
应用：Kafka消息传输、Netty文件下载
```

### Q4: Java NIO的Buffer有哪几个核心属性？

```
capacity：缓冲区容量（固定不变）
position：当前位置（读写指针）
limit：限制位置（写模式=capacity，读模式=之前写入的数据量）

flip()：写→读，position=0, limit=旧position
clear()：清空，position=0, limit=capacity
compact()：保留未读数据，移到开头
```

### Q5: 虚拟线程对IO模型有什么影响？

```
JDK 21虚拟线程让BIO重新成为最佳选择：

1. 虚拟线程极轻量（几KB），可以一个连接一个虚拟线程
2. 虚拟线程在IO阻塞时自动让出，不占用OS线程
3. BIO写法（简单直观）+ NIO性能（不阻塞OS线程）
4. 不再需要复杂的NIO Selector编程
5. Netty等框架仍然用NIO（极致性能场景）
```

---

## 📚 相关阅读

- [03_Java并发编程详解](./03_Java并发编程详解.md)
- [01_JVM虚拟机详解](./01_JVM虚拟机详解.md)
- [02_Netty核心原理详解](../08_网络通信/02_Netty核心原理详解.md)
- [03_RPC原理与实现](../08_网络通信/03_RPC原理与实现.md)

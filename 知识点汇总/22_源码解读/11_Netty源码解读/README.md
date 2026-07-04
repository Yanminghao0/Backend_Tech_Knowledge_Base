# Netty源码解读

> 💡 深入理解Netty高性能网络框架的核心实现原理

---

## 📚 目录结构

```
Netty源码解读/
├── README.md                    # 本文档
├── 核心架构解析.md              # Netty整体架构 ✅
├── EventLoop源码解析.md         # 事件循环机制 ✅
├── Pipeline源码解析.md          # 责任链模式 ✅
├── 内存管理源码解析.md          # ByteBuf与内存池 ✅
├── Bootstrap源码解析.md         # 启动器源码 ✅
├── ChannelHandler源码解析.md    # 处理器源码 ✅
├── 编解码器源码解析.md          # 编解码器源码 ✅
└── 零拷贝源码解析.md            # 零拷贝实现 ✅
```

---

## 🎯 学习目标

### 核心问题
1. Netty的线程模型是怎样的？
2. EventLoop是如何工作的？
3. Pipeline责任链是如何实现的？
4. Netty的内存管理有什么特点？
5. Bootstrap启动器如何工作？
6. ChannelHandler如何处理事件？
7. 编解码器如何实现数据转换？
8. Netty如何实现零拷贝？

### 面试高频问题
- ⭐⭐⭐⭐⭐ Reactor线程模型
- ⭐⭐⭐⭐⭐ EventLoop工作原理
- ⭐⭐⭐⭐⭐ Bootstrap启动流程
- ⭐⭐⭐⭐ Pipeline责任链
- ⭐⭐⭐⭐ ChannelHandler机制
- ⭐⭐⭐⭐ ByteBuf内存管理
- ⭐⭐⭐⭐ 编解码器原理
- ⭐⭐⭐⭐ 零拷贝实现

---

## 📖 核心内容

### 1️⃣ 核心架构解析
📄 [核心架构解析.md](./11.1_核心架构解析.md)

**核心内容**：
- ✅ Netty整体架构
- ✅ Reactor线程模型
- ✅ 核心组件关系
- ✅ 启动流程分析

### 2️⃣ EventLoop源码解析
📄 [EventLoop源码解析.md](./11.3_EventLoop源码解析.md)

**核心内容**：
- ✅ EventLoop继承体系
- ✅ 事件循环机制
- ✅ 任务调度
- ✅ 线程模型

### 3️⃣ Pipeline源码解析
📄 [Pipeline源码解析.md](./11.4_Pipeline源码解析.md)

**核心内容**：
- ✅ Pipeline结构
- ✅ Handler链
- ✅ 事件传播机制
- ✅ 入站出站处理

### 4️⃣ 内存管理源码解析
📄 [内存管理源码解析.md](./11.6_内存管理源码解析.md)

**核心内容**：
- ✅ ByteBuf体系
- ✅ 内存池设计
- ✅ 引用计数
- ✅ 零拷贝实现

### 5️⃣ Bootstrap源码解析
📄 [Bootstrap源码解析.md](./11.2_Bootstrap源码解析.md)

**核心内容**：
- ✅ 启动器设计模式
- ✅ ServerBootstrap vs Bootstrap
- ✅ 启动流程分析
- ✅ 配置参数详解

### 6️⃣ ChannelHandler源码解析
📄 [ChannelHandler源码解析.md](./11.5_ChannelHandler源码解析.md)

**核心内容**：
- ✅ Handler接口体系
- ✅ ChannelHandlerContext
- ✅ ChannelPipeline管理
- ✅ 事件传播机制

### 7️⃣ 编解码器源码解析
📄 [编解码器源码解析.md](./11.8_编解码器源码解析.md)

**核心内容**：
- ✅ ByteToMessageDecoder
- ✅ MessageToByteEncoder
- ✅ 内置编解码器
- ✅ 自定义编解码器

### 8️⃣ 零拷贝源码解析
📄 [零拷贝源码解析.md](./11.7_零拷贝源码解析.md)

**核心内容**：
- ✅ 零拷贝原理
- ✅ CompositeByteBuf
- ✅ FileRegion文件传输
- ✅ DirectByteBuffer优化

---

## 🚀 快速入门

### Netty服务端示例

```java
public class NettyServer {
    public static void main(String[] args) throws Exception {
        // Boss线程组：接收连接
        EventLoopGroup bossGroup = new NioEventLoopGroup(1);
        // Worker线程组：处理IO
        EventLoopGroup workerGroup = new NioEventLoopGroup();
        
        try {
            ServerBootstrap bootstrap = new ServerBootstrap();
            bootstrap.group(bossGroup, workerGroup)
                .channel(NioServerSocketChannel.class)
                .option(ChannelOption.SO_BACKLOG, 128)
                .childOption(ChannelOption.SO_KEEPALIVE, true)
                .childHandler(new ChannelInitializer<SocketChannel>() {
                    @Override
                    protected void initChannel(SocketChannel ch) {
                        ch.pipeline()
                            .addLast(new StringDecoder())
                            .addLast(new StringEncoder())
                            .addLast(new ServerHandler());
                    }
                });
            
            // 绑定端口
            ChannelFuture future = bootstrap.bind(8080).sync();
            System.out.println("Server started on port 8080");
            
            // 等待关闭
            future.channel().closeFuture().sync();
        } finally {
            bossGroup.shutdownGracefully();
            workerGroup.shutdownGracefully();
        }
    }
}

class ServerHandler extends SimpleChannelInboundHandler<String> {
    @Override
    protected void channelRead0(ChannelHandlerContext ctx, String msg) {
        System.out.println("Received: " + msg);
        ctx.writeAndFlush("Echo: " + msg);
    }
}
```

---

## 💡 核心知识点速查

### Reactor线程模型

```
单线程模型：
┌─────────────────────────────────────┐
│           Reactor Thread            │
│  ┌─────────┐  ┌─────────────────┐  │
│  │ Accept  │  │  Read/Write     │  │
│  └─────────┘  └─────────────────┘  │
└─────────────────────────────────────┘

主从多线程模型（Netty默认）：
┌─────────────────────────────────────┐
│         Boss EventLoopGroup         │
│  ┌─────────────────────────────┐   │
│  │     Accept Connections      │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│        Worker EventLoopGroup        │
│  ┌─────────┐ ┌─────────┐ ┌─────┐  │
│  │EventLoop│ │EventLoop│ │ ... │  │
│  │Read/Write│ │Read/Write│ │     │  │
│  └─────────┘ └─────────┘ └─────┘  │
└─────────────────────────────────────┘
```

### 核心组件

```
Channel：网络通道，代表一个连接
EventLoop：事件循环，处理IO事件
EventLoopGroup：EventLoop组
ChannelPipeline：处理器链
ChannelHandler：事件处理器
ByteBuf：字节缓冲区
Bootstrap：启动引导类
```

### Pipeline事件传播

```
入站事件（Inbound）：从Head到Tail
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────┐
│ Head │ -> │ Handler1 │ -> │ Handler2 │ -> │ Tail │
└──────┘    └──────────┘    └──────────┘    └──────┘

出站事件（Outbound）：从Tail到Head
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────┐
│ Head │ <- │ Handler1 │ <- │ Handler2 │ <- │ Tail │
└──────┘    └──────────┘    └──────────┘    └──────┘
```

---

## 📚 参考资料

### 推荐书籍
- 📘 《Netty实战》- Norman Maurer
- 📘 《Netty权威指南》- 李林锋

### 在线资源
- 🌐 [Netty官方文档](https://netty.io/wiki/)
- 🌐 [Netty源码](https://github.com/netty/netty)

---

**深入Netty源码，掌握高性能网络编程！** 🚀

*最后更新：2025-12-28*

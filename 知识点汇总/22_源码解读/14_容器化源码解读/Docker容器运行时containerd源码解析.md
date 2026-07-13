# Docker 容器运行时 containerd 源码深度解析

> "容器技术的本质不是虚拟化，而是命名空间隔离 + Cgroups 资源限制 + 联合文件系统。" —— containerd 作为 Docker 捐赠给 CNCF 的核心容器运行时，是连接上层编排系统（Kubernetes）和底层容器技术（runc）的关键桥梁。深入其源码，能真正理解一个容器从镜像到运行的完整生命周期。

---

## 📋 目录

1. [containerd 架构总览](#1-containerd-架构总览)
2. [核心数据结构与接口](#2-核心数据结构与接口)
3. [容器创建全链路](#3-容器创建全链路)
4. [镜像管理机制](#4-镜像管理机制)
5. [快照与分层文件系统](#5-快照与分层文件系统)
6. [OCI Runtime 调用](#6-oci-runtime-调用)
7. [容器监控与事件系统](#7-容器监控与事件系统)
8. [CRI 插件实现](#8-cri-插件实现)
9. [垃圾回收机制](#9-垃圾回收机制)
10. [安全与隔离机制](#10-安全与隔离机制)
11. [面试题速查](#11-面试题速查)

---

## 1. containerd 架构总览

containerd 是一个高度模块化的容器运行时，其架构分为多个子系统，通过 gRPC 接口对外提供服务。

```
┌─────────────────────────────────────────────────────┐
│              Kubernetes / Docker                     │
│                   (上层调用方)                        │
├─────────────────────────────────────────────────────┤
│            CRI Plugin (gRPC)                        │
├──────┬──────┬──────┬──────┬──────────┬──────────────┤
│ Meta │ Image│ Cont. │Snap- │ Diff/    │  Events/    │
│ API  │ API  │ API  │ shot │ Mount    │  Tasks      │
├──────┴──────┴──────┴──────┴──────────┴──────────────┤
│              containerd 核心                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ boltdb   │ │content   │ │snapshot  │            │
│  │ metadata │ │ store    │ │ store    │            │
│  └──────────┘ └──────────┘ └──────────┘            │
├─────────────────────────────────────────────────────┤
│              OCI Runtime Layer                      │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│     │  runc    │  │  kata    │  │  gVisor  │       │
│     └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────┤
│              Linux Kernel                           │
│   namespaces | cgroups | seccomp | overlayfs        │
└─────────────────────────────────────────────────────┘
```

核心子系统：
- **Metadata**：容器和镜像的元数据存储（boltdb）
- **Content Store**：镜像层内容存储（基于文件系统）
- **Snapshot Store**：快照管理，构建容器根文件系统
- **Runtime**：调用 OCI Runtime（默认 runc）创建和运行容器
- **Events**：容器生命周期事件发布

## 2. 核心数据结构与接口

### 2.1 容器数据模型

```go
// github.com/containerd/containerd/metadata/containers.go

// Container 代表一个容器的元数据
type Container struct {
    ID        string            // 容器唯一标识
    Labels    map[string]string // 标签
    Image     string            // 镜像引用
    Runtime   string            // 运行时名称（如 io.containerd.runc.v2）
    Spec      []byte            // OCI Runtime Spec（JSON）
    Snapshotter string          // 快照驱动（如 overlayfs）
    SnapshotKey string          // 快照键
    CreatedAt time.Time
    UpdatedAt time.Time
    Extensions map[string]typeurl.Any // 扩展信息
}

// Task 代表一个运行中的容器实例
type Task struct {
    container *Container
    task      task.TaskService
    // ...
}
```

### 2.2 核心服务接口

```go
// github.com/containerd/containerd/services/services.go

// Containers 服务接口
type ContainerClient interface {
    Create(ctx context.Context, req *CreateContainerRequest) (*CreateContainerResponse, error)
    Delete(ctx context.Context, req *DeleteContainerRequest) (*DeleteContainerResponse, error)
    Get(ctx context.Context, req *GetContainerRequest) (*GetContainerResponse, error)
    List(ctx context.Context, req *ListContainersRequest) (*ListContainersResponse, error)
}

// Image 服务接口
type ImageClient interface {
    Pull(ctx context.Context, req *PullImageRequest) (*PullImageResponse, error)
    Push(ctx context.Context, req *PushImageRequest) (*PushImageResponse, error)
    List(ctx context.Context, req *ListImagesRequest) (*ListImagesResponse, error)
}

// Task 服务接口
type TaskClient interface {
    Create(ctx context.Context, req *CreateTaskRequest) (*CreateTaskResponse, error)
    Start(ctx context.Context, req *StartTaskRequest) (*StartTaskResponse, error)
    Delete(ctx context.Context, req *DeleteTaskRequest) (*DeleteTaskResponse, error)
    Kill(ctx context.Context, req *KillRequest) (*KillResponse, error)
    Exec(ctx context.Context, req *ExecProcessRequest) (*ExecProcessResponse, error)
    Pids(ctx context.Context, req *PidsRequest) (*PidsResponse, error)
}
```

### 2.3 Snapshot 接口

```go
// github.com/containerd/containerd/snapshot/snapshotter.go

type Snapshotter interface {
    // 准备一个可写的快照（用于容器运行时层）
    Prepare(ctx context.Context, key, parent string, opts ...Opt) ([]mount.Mount, error)

    // 视图层（只读快照）
    View(ctx context.Context, key, parent string, opts ...Opt) ([]mount.Mount, error)

    // 提交快照（将可写层变为只读层）
    Commit(ctx context.Context, name, key string, opts ...Opt) error

    // 删除快照
    Remove(ctx context.Context, key string) error

    // 获取挂载信息
    Mounts(ctx context.Context, key string) ([]mount.Mount, error)

    // 统计信息
    Stat(ctx context.Context, key string) (Info, error)
    Update(ctx context.Context, info Info, fieldpaths ...string) (Info, error)
}
```

## 3. 容器创建全链路

### 3.1 客户端 API 调用

```go
// 用户代码示例
ctx := namespaces.WithNamespace(context.Background(), "default")

// 1. 拉取镜像
image, err := client.Pull(ctx, "docker.io/library/nginx:latest",
    containerd.WithPullUnpack)

// 2. 创建容器
container, err := client.NewContainer(ctx, "my-nginx",
    containerd.WithImage(image),
    containerd.WithNewSnapshot("my-nginx-snapshot", image),
    containerd.WithNewSpec(
        oci.WithImageConfig(image),
        oci.WithProcessArgs("nginx", "-g", "daemon off;"),
    ),
)

// 3. 创建任务（真正启动容器进程）
task, err := container.NewTask(ctx, cio.NewCreator(cio.WithStdio))
err = task.Start(ctx)
```

### 3.2 NewContainer 源码追踪

```go
// github.com/containerd/containerd/client.go

func (c *Client) NewContainer(ctx context.Context, id string,
    opts ...NewContainerOpts) (*Container, error) {

    container := containers.Container{
        ID: id,
        Runtime: defaultRuntime, // "io.containerd.runc.v2"
    }

    // 应用配置选项
    for _, o := range opts {
        if err := o(ctx, c, &container); err != nil {
            return nil, err
        }
    }

    // 通过 gRPC 创建容器元数据
    resp, err := c.ContainerService().Create(ctx,
        &containers.CreateContainerRequest{
            Container: container,
        })
    if err != nil {
        return nil, err
    }

    return &Container{
        client:    c,
        id:        resp.Container.ID,
        metadata:  resp.Container,
    }, nil
}
```

### 3.3 WithNewSnapshot 实现

```go
// github.com/containerd/containerd/container_opts.go

func WithNewSnapshot(key string, image Image, opts ...snapshot.Opt) NewContainerOpts {
    return func(ctx context.Context, client *Client, c *containers.Container) error {
        // 1. 获取镜像的根快照键
        diffIDs, err := image.RootFS(ctx)
        if err != nil {
            return err
        }

        // 2. 确保镜像层已经解包到快照存储
        if err := image.Unpack(ctx, c.Snapshotter); err != nil {
            return err
        }

        // 3. 创建可写快照层（基于镜像根层作为 parent）
        parent := identity.ChainID(diffIDs).String()
        mounts, err := client.SnapshotService(c.Snapshotter).Prepare(
            ctx, key, parent, opts...)
        if err != nil {
            return err
        }

        c.SnapshotKey = key
        c.Runtime = defaultRuntime
        return nil
    }
}
```

### 3.4 WithNewSpec —— 生成 OCI Spec

```go
// github.com/containerd/containerd/oci/spec.go

func WithImageConfig(image Image) SpecOpts {
    return func(ctx context.Context, client *Client,
        container *containers.Container, s *Spec) error {

        // 1. 获取镜像配置
        ic, err := image.Config(ctx)
        if err != nil {
            return err
        }

        var imageOCI ocispec.Image
        if err := json.Unmarshal(ic.Config, &imageOCI); err != nil {
            return err
        }

        // 2. 设置根文件系统
        s.Root = &Root{
            Path: "rootfs",        // 相对于 bundle 目录
            Readonly: false,        // 可写
        }

        // 3. 设置进程信息
        s.Process = &Process{
            Terminal: imageOCI.Config.Tty,
            Args:     imageOCI.Config.Entrypoint,
            Env:      imageOCI.Config.Env,
            Cwd:      imageOCI.Config.WorkingDir,
            User:     User{
                UID:      uint32(imageOCI.Config.User.UID),
                GID:      uint32(imageOCI.Config.User.GID),
            },
        }

        // 4. 设置默认命名空间
        s.Linux = &Linux{
            Namespaces: []Namespace{
                {Type: NamespacePID},
                {Type: NamespaceIPC},
                {Type: NamespaceUTS},
                {Type: NamespaceMount},
                {Type: NamespaceNetwork},
            },
        }

        return nil
    }
}
```

## 4. 镜像管理机制

### 4.1 镜像拉取流程

```go
// github.com/containerd/containerd/pull.go

func (c *Client) Pull(ctx context.Context, ref string,
    opts ...RemoteOpt) (_ Image, retErr error) {

    // 1. 解析镜像引用
    resolver := docker.NewResolver(docker.ResolverOptions{})

    name, desc, err := resolver.Resolve(ctx, ref)
    if err != nil {
        return nil, err
    }

    // 2. 根据 descriptor 类型处理
    // desc 可以是 manifest（单架构）或 manifest list（多架构）
    fetcher, err := resolver.Fetcher(ctx, name)
    if err != nil {
        return nil, err
    }

    // 3. 创建内容存储（Content Store）用于存储拉取的层
    var handler images.Handler
    handler = images.HandlerFunc(func(ctx context.Context,
        desc ocispec.Descriptor) ([]ocispec.Descriptor, error) {

        // 下载每一层内容
        return c.contentStoreHandler(ctx, desc, fetcher)
    })

    // 4. 处理多架构镜像
    if desc.MediaType == ocispec.MediaTypeImageManifest ||
       desc.MediaType == ocispec.MediaTypeImageIndex {

        handler = images.LimitManifests(handler, plat, c.config.MaxConcurrentDownloads)

        // 如果是 manifest list，选择匹配当前平台的 manifest
        if desc.MediaType == ocispec.MediaTypeImageIndex {
            handler = images.PlatformResolver(handler, plat)
        }
    }

    // 5. 遍历并下载所有层
    if err := images.Dispatch(ctx, handler, nil, desc); err != nil {
        return nil, err
    }

    // 6. 解包镜像（将层内容解压到快照存储）
    img := NewImage(c, image.Image{
        Target: desc,
    })

    if err := img.Unpack(ctx, defaultSnapshotter); err != nil {
        return nil, err
    }

    return img, nil
}
```

### 4.2 镜像层下载与内容寻址

containerd 使用 **内容寻址存储（Content-Addressable Storage, CAS）** 存储镜像层。每层的 key 是其内容的 SHA256 哈希。

```go
// github.com/containerd/containerd/content/content.go

type Provider interface {
    ReaderAt(ctx context.Context, dgst digest.Digest) (ReaderAt, error)
    Info(ctx context.Context, dgst digest.Digest) (Info, error)
}

type Ingester interface {
    Writer(ctx context.Context, opts ...WriterOpt) (Writer, error)
}

// Content Store 实现
type contentStore struct {
    root string  // 存储根目录，如 /var/lib/containerd/io.containerd.content.v1.content
}

// Writer 实现层内容的写入
func (cs *contentStore) Writer(ctx context.Context,
    opts ...WriterOpt) (Writer, error) {

    w := &contentWriter{
        cs:   cs,
        ref:  opts.Ref,
        // 写入临时文件，完成后校验哈希并重命名
        path: filepath.Join(cs.root, "ingest", opts.Ref),
    }

    return w, nil
}
```

镜像层内容存储在 `/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/<hash>` 路径下，按哈希值寻址。这保证了相同内容只存储一份（去重）。

## 5. 快照与分层文件系统

### 5.1 快照模型

```
镜像层（只读）          快照层（可写）
┌──────────┐
│ Layer 4  │ ← Commit
├──────────┤
│ Layer 3  │ ← Commit
├──────────┤
│ Layer 2  │ ← Commit
├──────────┤
│ Layer 1  │ ← Commit（基础层）
└──────────┘
     ↑ parent
┌──────────┐
│ 容器RW层 │ ← Prepare（容器运行时层）
└──────────┘
```

- **Prepare**：创建一个可写的快照层，其 parent 是镜像的最顶层
- **Commit**：将可写层提交为只读层（用于构建新镜像）
- **View**：创建一个只读的快照（用于 inspect）

### 5.2 OverlayFS 快照实现

```go
// github.com/containerd/containerd/snapshots/overlayfs/overlay.go

type snapshotter struct {
    root    string               // 快照根目录
    ms      *meta.MetaStore      // 元数据存储（boltdb）
    userxattr bool               // 是否使用 userxattr
}

func (o *snapshotter) Prepare(ctx context.Context, key, parent string,
    opts ...snapshot.Opt) ([]mount.Mount, error) {

    return o.createSnapshot(ctx, key, parent, opts, false)
}

func (o *snapshotter) createSnapshot(ctx context.Context,
    key, parent string, opts []snapshot.Opt, readonly bool) ([]mount.Mount, error) {

    // 1. 在 boltdb 中创建快照元数据
    var s storage.Snapshot
    err := o.ms.Update(func(tx *bolt.Tx) error {
        s, err = storage.CreateSnapshot(tx, key, parent, readonly)
        return err
    })

    // 2. 创建快照目录
    snapDir := o.getSnapshotDir(key)
    // 创建 diff（可写层）、work（工作目录）、fs（挂载点）子目录
    os.MkdirAll(filepath.Join(snapDir, "diff"), 0755)
    os.MkdirAll(filepath.Join(snapDir, "work"), 0755)
    os.MkdirAll(filepath.Join(snapDir, "fs"), 0755)

    // 3. 生成 OverlayFS 挂载参数
    var mounts []mount.Mount
    if readonly {
        mounts = []mount.Mount{
            {
                Type:   "overlay",
                Source: "overlay",
                Options: []string{
                    "ro",
                    "lowerdir=" + o.lowerDirs(s), // 只读层
                    "upperdir=" + filepath.Join(snapDir, "diff"),
                    "workdir=" + filepath.Join(snapDir, "work"),
                },
            },
        }
    } else {
        mounts = []mount.Mount{
            {
                Type:   "overlay",
                Source: "overlay",
                Options: []string{
                    "lowerdir=" + o.lowerDirs(s),
                    "upperdir=" + filepath.Join(snapDir, "diff"),
                    "workdir=" + filepath.Join(snapDir, "work"),
                    "userxattr",
                },
            },
        }
    }

    return mounts, nil
}
```

### 5.3 lowerDirs 构建

```go
func (o *snapshotter) lowerDirs(s storage.Snapshot) string {
    var dirs []string
    // 从 parent 开始向上遍历所有只读层
    for _, parent := range s.Parents {
        dirs = append(dirs, filepath.Join(o.getSnapshotDir(parent), "fs"))
    }
    return strings.Join(dirs, ":")
}
```

OverlayFS 的 `lowerdir` 是用 `:` 分隔的多个目录路径，排列顺序决定了层叠优先级。容器运行时，rootfs 就是 overlayfs 的挂载点，由 lowerdir（镜像层）和 upperdir（容器可写层）组合而成。

## 6. OCI Runtime 调用

### 6.1 Task 创建

```go
// github.com/containerd/containerd/task.go

func (c *Container) NewTask(ctx context.Context,
    ioCreate cio.Creator, opts ...NewTaskOpts) (Task, error) {

    // 1. 获取 OCI Spec
    spec, err := c.Spec(ctx)
    if err != nil {
        return nil, err
    }

    // 2. 获取快照挂载信息
    mounts, err := c.client.SnapshotService(c.Snapshotter).Mounts(
        ctx, c.SnapshotKey)
    if err != nil {
        return nil, err
    }

    // 3. 创建 Task 创建请求
    request := &tasks.CreateTaskRequest{
        ContainerID: c.ID,
        Rootfs:     mounts,      // 文件系统挂载信息
        Terminal:   spec.Process.Terminal,
        Stdin:      ioConfig.Stdin,
        Stdout:     ioConfig.Stdout,
        Stderr:     ioConfig.Stderr,
    }

    // 4. 应用 Task 选项（如资源限制、命名空间等）
    for _, o := range opts {
        if err := o(ctx, c, &request, ioCreate); err != nil {
            return nil, err
        }
    }

    // 5. 通过 gRPC 调用 TaskService 创建任务
    response, err := c.client.TaskService().Create(ctx, request)
    if err != nil {
        return nil, err
    }

    return &task{
        client:    c.client,
        container: c,
        io:        io,
        pid:       response.Pid,
    }, nil
}
```

### 6.2 runc shim v2 实现

containerd 通过 **shim** 进程与 OCI Runtime 交互。shim 是每个容器的父进程，负责管理容器生命周期。

```go
// github.com/containerd/containerd/runtime/v2/runc/task/service.go

type service struct {
    mu        sync.Mutex
    context   context.Context
    container *runc.Container
    platforms []/platform.Matcher
    instrumentstruments ...
}

// Create 创建容器
func (s *service) Create(ctx context.Context,
    r *taskAPI.CreateTaskRequest) (*taskAPI.CreateTaskResponse, error) {

    // 1. 保存 OCI Spec 到 bundle 目录
    spec, err := typeurl.UnmarshalAny(r.Spec)
    if err != nil {
        return nil, err
    }

    // 2. 挂载 rootfs
    for _, m := range r.Rootfs {
        if err := m.Mount(mount.WithFlags("ro")); err != nil {
            return nil, err
        }
    }

    // 3. 创建 runc.Container
    opts := []runc.CriuOpts{}
    container, err := runc.NewContainer(
        ctx,
        s.platform,
        r,          // CreateTaskRequest
        opts,
    )
    if err != nil {
        return nil, err
    }
    s.container = container

    // 4. 返回容器进程 PID
    return &taskAPI.CreateTaskResponse{
        Pid: uint32(container.Pid()),
    }, nil
}
```

### 6.3 runc 调用

```go
// github.com/containerd/containerd/runtime/v2/runc/container.go

func NewContainer(ctx context.Context, platform platform.Platform,
    r *taskAPI.CreateTaskRequest, opts *options.Options) (*Container, error) {

    // 1. 创建 runc 实例
    rc := &runc.Runc{
        Command:      r.Runtime, // runc 二进制路径
        PdeathSignal: unix.SIGKILL,
        Log:          logPath,
        LogFormat:    runc.FormatJSON,
    }

    // 2. 准备 OCI Bundle
    bundle := r.Bundle
    // rootfs 已经挂载到 bundle/rootfs

    // 3. 写入 config.json（OCI Spec）
    specBytes, _ := json.Marshal(r.Spec)
    os.WriteFile(filepath.Join(bundle, "config.json"), specBytes, 0644)

    // 4. 调用 runc create（不启动容器进程，只创建）
    if err := rc.Create(ctx, r.ID, bundle, &runc.CreateOpts{
        IO: io,
        PidFile: pidFilePath,
    }); err != nil {
        return nil, err
    }

    // 5. 读取容器进程 PID
    pid, _ := readPidFile(pidFilePath)

    return &Container{
        ID: r.ID,
        Bundle: bundle,
        runc: rc,
        pid: pid,
    }, nil
}
```

### 6.4 Start 启动容器

```go
// github.com/containerd/containerd/runtime/v2/runc/task/service.go

func (s *service) Start(ctx context.Context,
    r *taskAPI.StartRequest) (*taskAPI.StartResponse, error) {

    container, err := s.getContainer(r.ID)
    if err != nil {
        return nil, err
    }

    // 调用 runc start 启动容器进程
    if err := s.container.Start(ctx); err != nil {
        return nil, err
    }

    return &taskAPI.StartResponse{
        Pid: uint32(s.container.Pid()),
    }, nil
}

// runc.Runc.Start
func (r *Runc) Start(ctx context.Context, id string) error {
    // 实际执行: runc start <id>
    return r.execRunc(ctx, nil, "start", id)
}
```

**runc create** 和 **runc start** 是两步操作。`create` 创建容器命名空间和初始进程，但进程处于暂停状态（通过 `SIGSTOP`）；`start` 发送 `SIGCONT` 信号让进程开始执行用户定义的入口程序。这种设计允许在容器启动前进行额外的配置（如设置 cgroup、网络等）。

## 7. 容器监控与事件系统

### 7.1 容器退出监控

shim 进程是容器进程的父进程，通过 `waitpid` 监控容器退出：

```go
// github.com/containerd/containerd/runtime/v2/runc/task/service.go

func (s *service) wait(ctx context.Context,
    container *runc.Container) {

    // 等待容器进程退出
    state, err := container.Wait(ctx)
    if err != nil {
        // 处理错误
    }

    // 发布 TaskExit 事件
    s.publish(ctx, runtime.TaskExitEventTopic,
        &eventtypes.TaskExit{
            ContainerID: container.ID,
            ID:          container.ID,
            Pid:         uint32(container.Pid()),
            ExitStatus:  state.ExitCode,
            ExitedAt:    state.ExitedAt,
        })
}
```

### 7.2 事件发布

```go
// github.com/containerd/containerd/events/events.go

type EventPublisher interface {
    Publish(ctx context.Context, topic string, event Event) error
}

// 实际发布实现
func (p *publisher) Publish(ctx context.Context,
    topic string, event Event) error {

    // 序列化事件
    data, err := typeurl.MarshalAny(event)
    if err != nil {
        return err
    }

    // 通过 EventBus 发布
    envelope := &envelope.Envelope{
        Timestamp: time.Now(),
        Namespace: getNamespace(ctx),
        Topic:     topic,
        Event:     data,
    }

    return p.events.Publish(ctx, envelope)
}
```

事件类型包括：
- `TaskCreate` / `TaskStart` / `TaskExit`
- `TaskPaused` / `TaskResumed` / `TaskKilled`
- `TaskExecAdded` / `TaskExecStarted`
- `ImagePull` / `ImagePush` / `ImageDelete`
- `SnapshotPrepare` / `SnapshotCommit` / `SnapshotRemove`

## 8. CRI 插件实现

CRI（Container Runtime Interface）是 Kubernetes 定义的容器运行时接口。containerd 通过内置 CRI 插件与 Kubernetes 集成。

### 8.1 CRI 服务架构

```go
// github.com/containerd/containerd/pkg/cri/server/cri_service.go

type criService struct {
    // containerd 客户端
    client *containerd.Client

    // 镜像服务
    imageService *imageService

    // 容器服务
    containerService *containerService

    // sandbox（Pod）管理
    sandboxStore *sandboxstore.Store

    // 容器存储
    containerStore *containerstore.Store

    // 事件订阅
    eventMonitor *eventMonitor
}
```

### 8.2 Pod 创建流程

```go
// github.com/containerd/containerd/pkg/cri/server/sandbox_run.go

func (c *criService) RunPodSandbox(ctx context.Context,
    r *runtime.RunPodSandboxRequest) (*runtime.RunPodSandboxResponse, error) {

    // 1. 生成 sandbox 配置
    config := r.GetConfig()
    sandboxID := util.GenerateID()

    // 2. 拉取 Pod sandbox 镜像（pause 镜像）
    image, err := c.ensureImageExists(ctx, sandboxImage, config)
    if err != nil {
        return nil, err
    }

    // 3. 创建 sandbox 容器元数据
    metadata := sandboxstore.NewSandbox(
        sandboxstore.Metadata{
            ID:     sandboxID,
            Name:   makeSandboxName(config),
            Config: config,
        },
        sandboxstore.Status{
            State: sandboxstore.StateReady,
        },
    )

    // 4. 生成 OCI Spec
    spec, err := c.generateSandboxContainerSpec(
        ctx, sandboxID, config, &image.ImageSpec.Config)
    if err != nil {
        return nil, err
    }

    // 5. 设置网络（如果使用 CNI）
    if !hostNetwork(config) {
        // 创建网络命名空间
        netnsPath, err := buildNetNs(sandboxID)
        // 调用 CNI 插件配置网络
        err = c.setupPodNetwork(ctx, sandboxID, netnsPath, config)
    }

    // 6. 创建容器
    container, err := c.client.NewContainer(ctx,
        sandboxID,
        containerd.WithSnapshotter(c.runtimeSnapshotter),
        containerd.WithNewSnapshot(sandboxID, image),
        containerd.WithSpec(spec),
        containerd.WithRuntime(c.runtimeHandler, nil),
    )

    // 7. 创建并启动 Task
    task, err := container.NewTask(ctx, cio.NewCreator(...))
    err = task.Start(ctx)

    // 8. 保存 sandbox 状态
    c.sandboxStore.Add(metadata)

    return &runtime.RunPodSandboxResponse{
        PodSandboxId: sandboxID,
    }, nil
}
```

### 8.3 容器创建

```go
// github.com/containerd/containerd/pkg/cri/server/container_create.go

func (c *criService) CreateContainer(ctx context.Context,
    r *runtime.CreateContainerRequest) (*runtime.CreateContainerResponse, error) {

    config := r.GetConfig()
    sandboxConfig := r.GetSandboxConfig()
    sandbox, err := c.sandboxStore.Get(r.GetPodSandboxId())

    // 1. 拉取镜像
    image, err := c.ensureImageExists(ctx, config.GetImage().GetImage(), sandboxConfig)

    // 2. 生成容器 Spec
    spec, err := c.generateContainerSpec(
        ctx,
        sandbox.ID,
        sandbox.Config,
        config,
        &image.ImageSpec.Config,
    )

    // 3. 设置容器根文件系统
    containerRootDir := c.getContainerRootDir(config.GetMetadata().GetName())

    // 4. 创建容器
    container, err := c.client.NewContainer(ctx,
        containerID,
        containerd.WithSnapshotter(c.runtimeSnapshotter),
        containerd.WithNewSnapshot(containerID, image),
        containerd.WithSpec(spec),
        containerd.WithRuntime(c.runtimeHandler, nil),
        containerd.WithContainerLabels(containerLabels),
    )

    // 5. 存储容器元数据
    metadata := containerstore.NewContainer(
        containerstore.Metadata{
            ID: containerID,
            Name: config.GetMetadata().GetName(),
            SandboxID: sandbox.ID,
            Container: container,
        },
        containerstore.Status{
            CreatedAt: time.Now().UnixNano(),
        },
    )
    c.containerStore.Add(metadata)

    return &runtime.CreateContainerResponse{
        ContainerId: containerID,
    }, nil
}
```

## 9. 垃圾回收机制

containerd 需要回收不再使用的镜像层、快照和内容，以避免磁盘空间无限增长。

### 9.1 Content GC

```go
// github.com/containerd/containerd/gc/gc.go

type GarbageCollector struct {
    contentStore content.Store
    snapshotter  snapshot.Snapshotter
    metadata     *db.DB
}

func (gc *GarbageCollector) GarbageCollect(ctx context.Context) error {
    // 1. 标记阶段：遍历所有活跃的引用
    roots, err := gc.scanRoots(ctx)

    // 2. 遍历引用图，标记所有可达的内容
    marked := make(map[digest.Digest]bool)
    for _, root := range roots {
        gc.mark(root, marked)
    }

    // 3. 清除阶段：删除所有未标记的内容
    err = gc.sweep(ctx, marked)
    return err
}

// scanRoots 扫描所有活跃引用
func (gc *GarbageCollector) scanRoots(ctx context.Context) ([]Reference, error) {
    var roots []Reference

    // 镜像引用是根
    images, _ := gc.client.ListImages(ctx)
    for _, img := range images {
        roots = append(roots, Reference{
            Type: "image",
            Digest: img.Target().Digest,
        })
    }

    // 正在运行的容器引用是根
    containers, _ := gc.client.ListContainers(ctx)
    for _, c := range containers {
        img, _ := c.Image(ctx)
        roots = append(roots, Reference{
            Type: "container",
            Digest: img.Target().Digest,
        })
    }

    return roots, nil
}
```

### 9.2 Snapshot GC

快照的 GC 采用 **引用计数** 机制。只有当一个快照的所有子快照都被删除后，该快照才能被删除。

```go
// github.com/containerd/containerd/metadata/snapshot.go

func (s *snapshotter) Remove(ctx context.Context, key string) error {
    return s.ms.Update(func(tx *bolt.Tx) error {
        // 检查是否有子快照
        children, err := storage.GetSnapshots(tx, key)
        if err != nil {
            return err
        }
        if len(children) > 0 {
            return fmt.Errorf("snapshot has children: %v", children)
        }

        // 删除快照元数据
        if err := storage.RemoveSnapshot(tx, key); err != nil {
            return err
        }

        // 删除快照目录
        snapDir := s.getSnapshotDir(key)
        return os.RemoveAll(snapDir)
    })
}
```

## 10. 安全与隔离机制

### 10.1 命名空间隔离

OCI Spec 中的 `linux.namespaces` 定义了容器使用的命名空间：

```go
// 常见的命名空间配置
s.Linux.Namespaces = []Namespace{
    {Type: NamespacePID,     Path: ""},      // PID 隔离
    {Type: NamespaceMount,   Path: ""},      // 挂载点隔离
    {Type: NamespaceNetwork, Path: ""},      // 网络隔离
    {Type: NamespaceIPC,     Path: ""},      // IPC 隔离
    {Type: NamespaceUTS,     Path: ""},      // 主机名隔离
    {Type: NamespaceUser,    Path: ""},      // 用户隔离（可选）
    {Type: NamespaceCgroup,  Path: ""},      // Cgroup 隔离
}
```

### 10.2 Seccomp 过滤

```go
// OCI Spec 中的 seccomp 配置
s.Linux.Seccomp = &LinuxSeccomp{
    DefaultAction: ActErrno,  // 默认拒绝
    Architectures: []string{ArchX86_64, ArchX86},
    Syscalls: []LinuxSyscall{
        {
            Names: []string{
                "accept", "accept4", "access", "bind", "brk",
                "chmod", "chown", "clone", "close", "connect",
                // ... 允许的系统调用列表
            },
            Action: ActAllow,   // 允许
        },
    },
}
```

### 10.3 Capabilities

```go
// 设置容器 capabilities
s.Process.Capabilities = &LinuxCapabilities{
    Bounding: []string{
        "CAP_AUDIT_WRITE",
        "CAP_KILL",
        "CAP_NET_BIND_SERVICE",
        "CAP_FOWNER",
        "CAP_CHOWN",
        "CAP_DAC_OVERRIDE",
        "CAP_SETFCAP",
        "CAP_SETPCAP",
        "CAP_NET_RAW",
        "CAP_SETGID",
        "CAP_SETUID",
        "CAP_MKNOD",
        // 注意：不包含 CAP_SYS_ADMIN、CAP_SYS_PTRACE 等高危 capability
    },
    Effective:   /* 同 Bounding */,
    Permitted:   /* 同 Bounding */,
    Inheritable: []string{},  // 空
    Ambient:     []string{},  // 空
}
```

### 10.4 AppArmor / SELinux

```go
// AppArmor Profile
s.Linux.ApparmorProfile = "containerd-default-profile"

// SELinux Label
s.Linux.MountLabel = "system_u:object_r:container_file_t:s0"
s.Process.SelinuxLabel = "system_u:system_r:container_t:s0"
```

## 11. 面试题速查

**Q1: containerd 和 Docker 的关系是什么？**
A: Docker 最初是单体架构，后来拆分为 dockerd、containerd、runc 等组件。containerd 负责容器生命周期管理、镜像传输和存储、快照管理。Docker 在 containerd 之上添加了镜像构建、卷管理、网络管理等高级功能。2017 年 Docker 将 containerd 捐赠给 CNCF，现在 containerd 是一个独立项目，同时被 Docker 和 Kubernetes 使用。

**Q2: containerd 和 runc 的关系是什么？**
A: runc 是 OCI Runtime 参考实现，负责底层的命名空间创建、cgroup 设置等操作系统层面的容器隔离。containerd 是更高层的运行时，负责镜像管理、快照管理、容器生命周期管理，通过调用 runc 来实际创建和运行容器进程。containerd 通过 shim 进程管理 runc 实例。

**Q3: shim 进程的作用是什么？**
A: shim 是每个容器的父进程，作用包括：(1) 作为容器进程的父进程，监控其生命周期；(2) 在 containerd 重启后容器仍能继续运行（shim 独立于 containerd 生命周期）；(3) 处理容器的 stdio 流；(4) 转发信号给容器进程。每个容器有一个独立的 shim 进程。

**Q4: containerd 的镜像存储模型是什么？**
A: 内容寻址存储（CAS）。每个镜像层的内容用 SHA256 哈希作为 key 存储，相同内容只存储一份。镜像的 manifest 引用各层的 digest，config 包含镜像的元信息（入口命令、环境变量等）。所有内容存储在 /var/lib/containerd/io.containerd.content.v1.content/ 下。

**Q5: OverlayFS 在 containerd 中的作用是什么？**
A: OverlayFS 联合挂载多个目录，形成容器的根文件系统。镜像的每一层对应一个只读目录（lowerdir），容器的可写层是一个单独的目录（upperdir）。读取文件时从上往下查找，写入时通过 copy-up 机制将文件从只读层复制到可写层再修改。

**Q6: runc create 和 runc start 有什么区别？**
A: create 创建容器的命名空间和初始进程，但进程处于暂停状态（收到 SIGSTOP 信号）。start 发送 SIGCONT 信号让进程开始执行用户入口程序。两步设计允许在容器进程真正运行前完成额外的配置，如网络设置、cgroup 调整等。

**Q7: containerd 的 CRI 插件如何与 Kubernetes 交互？**
A: CRI 插件实现了 Kubernetes 定义的 RuntimeService 和 ImageService gRPC 接口。kubelet 通过 CRI 接口调用 containerd 创建 Pod sandbox（pause 容器）、创建业务容器、启动/停止容器、拉取镜像等。CRI 插件将这些操作转换为 containerd 的内部 API 调用。

**Q8: 容器退出后 containerd 如何感知？**
A: shim 进程是容器进程的父进程，通过 waitpid 系统调用等待容器退出。容器退出后，shim 发布 TaskExit 事件到 containerd 的事件总线。containerd 的 CRI 插件订阅这些事件，更新容器状态并通知 kubelet。

**Q9: containerd 的 GC 机制是什么？**
A: 三色标记清除。标记阶段：从镜像引用和运行中的容器出发，遍历引用图标记所有可达的内容和快照。清除阶段：删除所有未被标记的内容和快照。快照还有引用计数机制——只有当所有子快照都被删除后，父快照才能被删除。

**Q10: containerd 如何实现容器隔离？**
A: 通过 Linux 内核机制：(1) namespaces 实现 PID、网络、挂载、IPC、UTS 等隔离；(2) cgroups 实现 CPU、内存、IO 资源限制；(3) seccomp 过滤系统调用；(4) capabilities 限制特权操作；(5) AppArmor/SELinux 实现强制访问控制；(6) 只读 rootfs 防止容器内修改系统文件。这些机制由 runc 在创建容器时设置。

---

## 总结

containerd 的源码展现了一个工业级容器运行时的完整设计：内容寻址的镜像存储实现了去重和完整性校验；快照系统通过 OverlayFS 实现了高效的分层文件系统；shim 进程模型实现了容器生命周期与 containerd 的解耦；CRI 插件实现了与 Kubernetes 的无缝集成。

深入理解 containerd 源码，不仅能帮助你在面试中从容应对容器相关问题，更能让你在实际的 DevOps 工作中深入理解容器行为、排查容器故障、优化容器性能。从 OCI Spec 到 runc 调用，从镜像拉取到 rootfs 构建，每一个环节都是容器技术的核心知识点。

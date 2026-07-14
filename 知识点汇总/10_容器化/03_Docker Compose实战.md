# Docker Compose实战

> 掌握Docker Compose多服务编排核心技能，从YAML语法到多环境配置，实战一键部署Spring Boot+MySQL+Redis+Nacos+RocketMQ完整开发环境

---

## 📋 目录

- [1. Docker Compose核心概念](#1-docker-compose核心概念)
- [2. YAML语法详解](#2-yaml语法详解)
- [3. 多服务编排](#3-多服务编排)
- [4. 网络配置](#4-网络配置)
- [5. 数据卷管理](#5-数据卷管理)
- [6. 环境变量与.env文件](#6-环境变量与env文件)
- [7. 多环境配置](#7-多环境配置)
- [8. 健康检查与依赖控制](#8-健康检查与依赖控制)
- [9. 资源限制](#9-资源限制)
- [10. 常用命令](#10-常用命令)
- [11. 实战案例：一键部署微服务开发环境](#11-实战案例一键部署微服务开发环境)
- [12. 总结与最佳实践](#12-总结与最佳实践)

---

## 1. Docker Compose核心概念

### 1.1 什么是Docker Compose

Docker Compose是用于定义和运行多容器Docker应用程序的工具。通过一个YAML文件配置应用的所有服务，然后使用一条命令创建并启动所有服务。

```
核心三要素：

  Service（服务）
    ├── 一个Service = 一个容器实例
    ├── 可以从镜像创建或Dockerfile构建
    └── 定义端口、环境变量、依赖等

  Network（网络）
    ├── 服务间通信的基础设施
    ├── 支持bridge/overlay/none/hostname
    └── 同一网络内可通过服务名互相访问

  Volume（数据卷）
    ├── 持久化容器数据
    ├── 支持命名卷/匿名卷/绑定挂载
    └── 可在多个服务间共享
```

### 1.2 版本演进

```yaml
# Compose V1（docker-compose 命令，Python实现）
# Compose V2（docker compose 命令，Go实现，集成到Docker CLI）
# Compose Specification（统一规范，无版本号限制）

# 推荐使用 Compose V2
# 检查版本
docker compose version
# Docker Compose version v2.24.0
```

### 1.3 与Docker的关系

```
Dockerfile  →  定义单个容器镜像
Docker Compose  →  定义多容器编排

  ┌──────────────────────────────────────────┐
  │           docker-compose.yml             │
  │                                          │
  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐   │
  │  │Web  │→ │ DB  │  │Redis│  │ MQ  │   │
  │  │App  │  │MySQL│  │     │  │RktMQ│   │
  │  └─────┘  └─────┘  └─────┘  └─────┘   │
  │     ↕         ↕       ↕        ↕       │
  │  Volume    Volume   Volume   Volume     │
  │                                          │
  │           Docker Network                 │
  └──────────────────────────────────────────┘
```

---

## 2. YAML语法详解

### 2.1 完整结构

```yaml
# docker-compose.yml 完整结构
version: "3.9"   # Compose文件格式版本（V2可省略）

services:         # 定义所有服务（必填）
  service_name:
    image: ...
    build: ...
    # ...

networks:         # 定义网络
  network_name:
    driver: bridge

volumes:          # 定义数据卷
  volume_name:
    driver: local

configs:          # 定义配置（Swarm模式）
  config_name:
    file: ./config.txt

secrets:          # 定义密钥（Swarm模式）
  secret_name:
    file: ./secret.txt
```

### 2.2 Service配置项全解

```yaml
services:
  my_app:
    # === 镜像/构建 ===
    image: myapp:latest                    # 使用已有镜像
    build:                                 # 从Dockerfile构建
      context: ./app                      # 构建上下文路径
      dockerfile: Dockerfile              # Dockerfile文件名
      args:                               # 构建参数
        JAR_FILE: target/app.jar
      target: production                  # 多阶段构建目标
      cache_from:                         # 缓存来源
        - myapp:cache
    pull_policy: always                    # 镜像拉取策略

    # === 容器配置 ===
    container_name: my_app_prod            # 容器名（不建议在Swarm中使用）
    hostname: myapp                        # 容器主机名
    user: "1000:1000"                      # 运行用户UID:GID
    working_dir: /app                      # 工作目录
    tty: true                              # 分配伪终端
    stdin_open: true                       # 保持标准输入打开

    # === 端口映射 ===
    ports:
      - "8080:8080"                        # 主机端口:容器端口
      - "8443"                             # 仅指定容器端口（主机随机分配）
      - target: 9090                       # 详细写法
        published: "9090"
        protocol: tcp
        mode: host

    # === 环境变量 ===
    environment:
      - SPRING_PROFILES_ACTIVE=prod       # 列表写法
      - DB_HOST=mysql                     # 支持引用变量
    env_file:                              # 从文件加载
      - .env
      - .env.production

    # === 卷挂载 ===
    volumes:
      - ./data:/app/data                   # 绑定挂载（主机路径:容器路径）
      - app_logs:/var/log/app              # 命名卷
      - /etc/timezone:/etc/timezone:ro     # 只读挂载

    # === 网络 ===
    networks:
      - frontend                           # 加入网络
      - backend:
          aliases:                         # 网络别名
            - api-service
            - app

    # === 依赖 ===
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started

    # === 健康检查 ===
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

    # === 重启策略 ===
    restart: unless-stopped                # no|always|on-failure|unless-stopped

    # === 资源限制（V2语法） ===
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        max_attempts: 3
        delay: 5s

    # === 日志配置 ===
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

    # === 标签 ===
    labels:
      - "com.app.environment=production"
      - "com.app.service=api"
```

---

## 3. 多服务编排

### 3.1 Web + DB + Redis 经典组合

```yaml
version: "3.9"

services:
  # === Web应用 ===
  webapp:
    image: openjdk:17-slim
    container_name: webapp
    working_dir: /app
    volumes:
      - ./target/app.jar:/app/app.jar
      - app_logs:/app/logs
    command: java -jar -Xms512m -Xmx512m app.jar
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - DB_HOST=mysql
      - DB_PORT=3306
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app_network
    restart: unless-stopped

  # === MySQL数据库 ===
  mysql:
    image: mysql:8.0
    container_name: mysql
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: appdb
      MYSQL_USER: appuser
      MYSQL_PASSWORD: apppass
      TZ: Asia/Shanghai
    volumes:
      - mysql_data:/var/lib/mysql
      - ./sql/init:/docker-entrypoint-initdb.d  # 初始化SQL
      - ./mysql/conf:/etc/mysql/conf.d          # 自定义配置
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-proot123"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - app_network
    restart: unless-stopped

  # === Redis缓存 ===
  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - app_network
    restart: unless-stopped

networks:
  app_network:
    driver: bridge

volumes:
  mysql_data:
  redis_data:
  app_logs:
```

---

## 4. 网络配置

### 4.1 网络类型

```yaml
networks:
  # === 桥接网络（默认，单机） ===
  bridge_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

  # === Overlay网络（Swarm集群） ===
  overlay_network:
    driver: overlay
    attachable: true                    # 允许独立容器加入

  # === 外部网络（已存在） ===
  external_network:
    external: true
    name: existing_network

  # === Host网络 ===
  host_network:
    driver: host

  # === None网络 ===
  none_network:
    driver: none
```

### 4.2 多网络隔离

```yaml
services:
  nginx:
    image: nginx:alpine
    networks:
      - frontend                        # Nginx同时在前端和后端网络
      - backend
    ports:
      - "80:80"

  webapp:
    image: myapp:latest
    networks:
      - backend                         # WebApp只在内网
    depends_on:
      - mysql
      - redis

  mysql:
    image: mysql:8.0
    networks:
      - db_network                      # DB在独立的数据库网络
      - backend                         # 同时在后端网络

networks:
  frontend:                             # 前端网络（对外暴露）
    driver: bridge
  backend:                              # 后端网络（内部通信）
    driver: bridge
    internal: true                      # 内部网络，不可外部访问
  db_network:                           # 数据库网络
    driver: bridge
    internal: true
```

### 4.3 服务发现

```yaml
# 同一网络内，服务可通过服务名直接访问
# DNS解析由Docker内置DNS服务提供

services:
  app:
    image: myapp
    environment:
      # 直接使用服务名作为主机名
      - DB_HOST=mysql           # mysql是服务名
      - DB_PORT=3306
      - REDIS_HOST=redis        # redis是服务名
      - REDIS_PORT=6379
    networks:
      - mynet

  mysql:
    image: mysql:8.0
    networks:
      - mynet

  redis:
    image: redis:7
    networks:
      - mynet

networks:
  mynet:
    driver: bridge
```

---

## 5. 数据卷管理

### 5.1 卷类型

```yaml
services:
  app:
    volumes:
      # === 命名卷（由Docker管理，推荐生产使用） ===
      - app_data:/app/data

      # === 绑定挂载（挂载主机路径，开发环境常用） ===
      - ./config:/app/config
      - ./logs:/app/logs:ro          # :ro 只读

      # === 匿名卷（不推荐，难以管理） ===
      - /app/tmp

      # === tmpfs挂载（内存中，不持久化） ===
      - tmpfs_volume:/app/cache

      # === 从其他容器共享 ===
      - data_volume_from:/shared

volumes:
  app_data:
    driver: local
    driver_opts:
      type: nfs
      device: ":/path/to/nfs/share"
      o: addr=10.0.0.1,rw

  tmpfs_volume:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=100m,uid=1000
```

### 5.2 卷备份与恢复

```bash
# 备份命名卷
docker run --rm \
  -v myproject_app_data:/data:ro \
  -v $(pwd):/backup \
  alpine tar czf /backup/app_data_backup.tar.gz -C /data .

# 恢复命名卷
docker run --rm \
  -v myproject_app_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/app_data_backup.tar.gz -C /data
```

---

## 6. 环境变量与.env文件

### 6.1 .env文件

```bash
# .env 文件（与docker-compose.yml同目录）
# ================================

# MySQL配置
MYSQL_ROOT_PASSWORD=root123
MYSQL_DATABASE=appdb
MYSQL_USER=appuser
MYSQL_PASSWORD=apppass

# Redis配置
REDIS_PASSWORD=redis123

# 应用配置
APP_PORT=8080
SPRING_PROFILES_ACTIVE=dev
JAVA_OPTS=-Xms512m -Xmx512m

# 版本控制
MYSQL_VERSION=8.0
REDIS_VERSION=7-alpine
APP_VERSION=latest
```

### 6.2 引用环境变量

```yaml
# docker-compose.yml
services:
  mysql:
    image: mysql:${MYSQL_VERSION}
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    ports:
      - "3306:3306"

  app:
    image: myapp:${APP_VERSION}
    environment:
      - SPRING_PROFILES_ACTIVE=${SPRING_PROFILES_ACTIVE}
      - JAVA_OPTS=${JAVA_OPTS}
    ports:
      - "${APP_PORT}:8080"
```

### 6.3 多.env文件

```bash
# .env          — 默认环境（Git提交）
# .env.dev      — 开发环境
# .env.prod     — 生产环境
# .env.local    — 本地覆盖（Git忽略）

# 使用 --env-file 指定
docker compose --env-file .env.prod up -d
```

---

## 7. 多环境配置

### 7.1 compose.override.yml机制

```
Docker Compose 默认加载顺序：
  1. docker-compose.yml         — 基础配置
  2. docker-compose.override.yml — 覆盖配置（自动加载）

  两个文件的配置会深度合并
```

```yaml
# docker-compose.yml — 基础配置（生产环境）
services:
  app:
    image: myapp:latest
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    restart: always

  mysql:
    image: mysql:8.0
    volumes:
      - mysql_data:/var/lib/mysql
```

```yaml
# docker-compose.override.yml — 开发覆盖（不提交到生产）
services:
  app:
    build:                              # 开发环境从源码构建
      context: .
      dockerfile: Dockerfile.dev
    environment:
      - SPRING_PROFILES_ACTIVE=dev      # 覆盖为dev
      - JAVA_OPTS=-Xms256m -Xmx256m -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*5005
    volumes:
      - ./src:/app/src                  # 热加载源码
    deploy:                             # 覆盖资源限制
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

  mysql:
    ports:
      - "3306:3306"                     # 开发环境暴露端口
```

### 7.2 显式多环境

```bash
# 使用 -f 指定多个配置文件（后面的覆盖前面的）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 设置 COMPOSE_FILE 环境变量
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker compose up -d
```

---

## 8. 健康检查与依赖控制

### 8.1 Healthcheck

```yaml
services:
  mysql:
    image: mysql:8.0
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s          # 检查间隔
      timeout: 5s            # 超时时间
      retries: 5             # 重试次数
      start_period: 30s      # 启动后宽限期

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  webapp:
    image: myapp:latest
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/actuator/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### 8.2 depends_on条件

```yaml
services:
  webapp:
    depends_on:
      mysql:
        condition: service_healthy     # 等待MySQL健康检查通过
      redis:
        condition: service_started      # 等待Redis启动即可
      nacos:
        condition: service_healthy

  # 条件类型：
  # service_started      — 容器启动即满足
  # service_healthy      — 健康检查通过
  # service_completed    — 容器正常退出（适合初始化容器）
```

---

## 9. 资源限制

### 9.1 Compose V2资源限制

```yaml
services:
  app:
    deploy:
      resources:
        # 硬限制（超过会被OOM Kill）
        limits:
          cpus: '2.0'          # 最多使用2个CPU核心
          memory: 2G           # 最多使用2G内存
        # 软限制（调度参考）
        reservations:
          cpus: '0.5'          # 至少保证0.5个CPU
          memory: 512M         # 至少保证512M内存
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      update_config:
        parallelism: 2
        delay: 10s
        order: start-first
        failure_action: rollback

  # 独立容器模式（非Swarm）使用以下语法
  app_standalone:
    image: myapp
    mem_limit: 2g              # 内存限制
    cpus: 2                    # CPU限制
    mem_reservation: 512m      # 内存软限制
    memswap_limit: 4g          # 内存+Swap限制
    cpu_shares: 1024           # CPU权重
```

---

## 10. 常用命令

```bash
# === 生命周期管理 ===
docker compose up -d                    # 启动所有服务（后台）
docker compose up -d --build            # 重新构建并启动
docker compose up -d --scale worker=3   # 扩展worker服务为3个实例
docker compose down                     # 停止并删除容器/网络
docker compose down -v                  # 同时删除数据卷
docker compose down --rmi all           # 同时删除镜像
docker compose stop                     # 停止服务（不删除容器）
docker compose start                    # 启动已停止的服务
docker compose restart                  # 重启服务
docker compose pause                    # 暂停服务（不停止进程）
docker compose unpause                  # 恢复暂停的服务

# === 查看状态 ===
docker compose ps                       # 查看服务状态
docker compose ps -a                    # 包含已停止的服务
docker compose logs -f                  # 跟踪所有服务日志
docker compose logs -f app              # 跟踪指定服务日志
docker compose logs --tail=100 app      # 查看最后100行
docker compose top                      # 查看容器内进程
docker compose config                   # 查看最终合并的配置
docker compose images                   # 查看使用的镜像

# === 执行命令 ===
docker compose exec mysql mysql -uroot -p    # 进入MySQL命令行
docker compose exec app sh                    # 进入应用容器Shell
docker compose exec app java -jar /app.jar   # 在容器内执行命令
docker compose run --rm app npm test         # 一次性运行（创建新容器）

# === 构建管理 ===
docker compose build                    # 构建所有服务镜像
docker compose build --no-cache app     # 不使用缓存构建
docker compose build --parallel         # 并行构建
docker compose pull                     # 拉取所有镜像
docker compose push                     # 推送镜像到仓库

# === 服务扩展 ===
docker compose up -d --scale worker=3   # 扩展worker实例数
docker compose up -d --scale worker=3 --scale api=2
```

---

## 11. 实战案例：一键部署微服务开发环境

### 11.1 项目结构

```
microservice-dev/
├── docker-compose.yml          # 主编排文件
├── .env                        # 环境变量
├── nacos/
│   └── init/
│       └── nacos_config.sql    # Nacos初始化SQL
├── mysql/
│   ├── conf/
│   │   └── my.cnf              # MySQL配置
│   └── init/
│       └── init.sql            # 初始化SQL
├── rocketmq/
│   └── conf/
│       └── broker.conf         # Broker配置
└── app/
    ├── Dockerfile
    └── target/
        └── app.jar
```

### 11.2 完整docker-compose.yml

```yaml
version: "3.9"

services:
  # ==================== MySQL ====================
  mysql:
    image: mysql:8.0
    container_name: dev-mysql
    restart: unless-stopped
    ports:
      - "3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      TZ: Asia/Shanghai
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql/conf/my.cnf:/etc/mysql/conf.d/my.cnf
      - ./mysql/init:/docker-entrypoint-initdb.d
      - ./nacos/init/nacos_config.sql:/docker-entrypoint-initdb.d/nacos_config.sql
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --default-authentication-plugin=mysql_native_password
      --lower_case_table_names=1
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - dev_network

  # ==================== Redis ====================
  redis:
    image: redis:7-alpine
    container_name: dev-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - dev_network

  # ==================== Nacos ====================
  nacos:
    image: nacos/nacos-server:v2.3.0
    container_name: dev-nacos
    restart: unless-stopped
    ports:
      - "8848:8848"
      - "9848:9848"
      - "9849:9849"
    environment:
      MODE: standalone
      PREFER_HOST_MODE: hostname
      SPRING_DATASOURCE_PLATFORM: mysql
      MYSQL_SERVICE_HOST: mysql
      MYSQL_SERVICE_PORT: 3306
      MYSQL_SERVICE_DB_NAME: nacos_config
      MYSQL_SERVICE_USER: root
      MYSQL_SERVICE_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_SERVICE_DB_PARAM: characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useSSL=false&serverTimezone=Asia/Shanghai
      NACOS_AUTH_ENABLE: "true"
      NACOS_AUTH_TOKEN: ${NACOS_AUTH_TOKEN}
      NACOS_AUTH_IDENTITY_KEY: ${NACOS_AUTH_IDENTITY_KEY}
      NACOS_AUTH_IDENTITY_VALUE: ${NACOS_AUTH_IDENTITY_VALUE}
    volumes:
      - nacos_logs:/home/nacos/logs
    depends_on:
      mysql:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8848/nacos/v1/console/health/readiness || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 60s
    networks:
      - dev_network

  # ==================== RocketMQ NameServer ====================
  rocketmq_namesrv:
    image: apache/rocketmq:5.2.0
    container_name: dev-rocketmq-namesrv
    restart: unless-stopped
    ports:
      - "9876:9876"
    command: sh mqnamesrv
    environment:
      JAVA_OPT_EXT: "-server -Xms256m -Xmx256m -Xmn128m"
    volumes:
      - rocketmq_namesrv_logs:/home/rocketmq/logs
    networks:
      - dev_network

  # ==================== RocketMQ Broker ====================
  rocketmq_broker:
    image: apache/rocketmq:5.2.0
    container_name: dev-rocketmq-broker
    restart: unless-stopped
    ports:
      - "10909:10909"
      - "10911:10911"
      - "10912:10912"
    command: sh mqbroker -n rocketmq_namesrv:9876 --enable-proxy
    environment:
      JAVA_OPT_EXT: "-server -Xms512m -Xmx512m -Xmn256m"
      NAMESRV_ADDR: "rocketmq_namesrv:9876"
    volumes:
      - rocketmq_broker_logs:/home/rocketmq/logs
      - rocketmq_broker_store:/home/rocketmq/store
      - ./rocketmq/conf/broker.conf:/home/rocketmq/rocketmq-5.2.0/conf/broker.conf
    depends_on:
      - rocketmq_namesrv
    networks:
      - dev_network

  # ==================== RocketMQ Dashboard ====================
  rocketmq_dashboard:
    image: apacherocketmq/rocketmq-dashboard:1.0.0
    container_name: dev-rocketmq-dashboard
    restart: unless-stopped
    ports:
      - "8180:8080"
    environment:
      JAVA_OPTS: "-Drocketmq.namesrv.addr=rocketmq_namesrv:9876"
    depends_on:
      - rocketmq_broker
    networks:
      - dev_network

  # ==================== Spring Boot App ====================
  app:
    build:
      context: ./app
      dockerfile: Dockerfile
    container_name: dev-app
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "5005:5005"   # 远程调试端口
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - JAVA_OPTS=-Xms512m -Xmx512m -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*5005
      - NACOS_HOST=nacos
      - NACOS_PORT=8848
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - ROCKETMQ_NAMESRV=rocketmq_namesrv:9876
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
      nacos:
        condition: service_healthy
      rocketmq_broker:
        condition: service_started
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/actuator/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s
    volumes:
      - app_logs:/app/logs
    networks:
      - dev_network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

# ==================== 网络 ====================
networks:
  dev_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

# ==================== 数据卷 ====================
volumes:
  mysql_data:
  redis_data:
  nacos_logs:
  rocketmq_namesrv_logs:
  rocketmq_broker_logs:
  rocketmq_broker_store:
  app_logs:
```

### 11.3 .env文件

```bash
# .env — 微服务开发环境配置

# MySQL
MYSQL_ROOT_PASSWORD=root123
MYSQL_DATABASE=appdb

# Redis
REDIS_PASSWORD=redis123

# Nacos
NACOS_AUTH_TOKEN=SecretKey0123456789012345678901234567890123456789012345678901234567890
NACOS_AUTH_IDENTITY_KEY=nacos
NACOS_AUTH_IDENTITY_VALUE=nacos
```

### 11.4 启动与验证

```bash
# 一键启动全部服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看启动日志
docker compose logs -f

# 验证各服务
curl http://localhost:8080/actuator/health     # App
curl http://localhost:8848/nacos                # Nacos
curl http://localhost:8180                      # RocketMQ Dashboard
mysql -h 127.0.0.1 -uroot -proot123             # MySQL
redis-cli -a redis123                           # Redis

# 停止全部服务
docker compose down

# 停止并清除数据
docker compose down -v
```

---

## 12. 总结与最佳实践

### 12.1 最佳实践清单

```
✅ 配置管理
  ├── 使用 .env 文件管理敏感信息（加入.gitignore）
  ├── 使用多环境配置（compose.override.yml / -f 参数）
  ├── 镜像版本使用具体tag，不用latest
  └── 显式指定端口映射，避免随机端口

✅ 网络与安全
  ├── 使用自定义网络而非默认网络
  ├── 内部服务不暴露端口（仅外部入口暴露）
  ├── 使用 internal: true 隔离敏感服务
  └── 容器以非root用户运行

✅ 数据持久化
  ├── 生产环境使用命名卷而非绑定挂载
  ├── 定期备份关键数据卷
  └── 初始化脚本通过 docker-entrypoint-initdb.d 加载

✅ 健康检查
  ├── 为所有服务配置healthcheck
  ├── 使用 depends_on.condition: service_healthy
  └── 设置合理的 start_period

✅ 资源管理
  ├── 配置资源限制（limits + reservations）
  ├── 配置日志轮转（max-size + max-file）
  └── 设置合理的重启策略（unless-stopped）

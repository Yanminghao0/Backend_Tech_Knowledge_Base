# GitLab CI/CD配置

> 使用GitLab CI/CD实现代码到部署的自动化

---

## 📋 目录

1. [GitLab CI/CD概述](#gitlab-cicd概述)
2. [.gitlab-ci.yml配置](#gitlab-ci-yml配置)
3. [Runner配置](#runner配置)
4. [实战案例](#实战案例)
5. [多环境部署](#多环境部署)
6. [最佳实践](#最佳实践)

---

## GitLab CI/CD概述

### 什么是GitLab CI/CD？

**定义**：GitLab内置的持续集成/持续交付工具

**核心概念**：
- **Pipeline**：流水线，由多个Stage组成
- **Job**：任务，Pipeline中的最小执行单元
- **Stage**：阶段，同一Stage的Job并行执行
- **Runner**：执行器，运行Job的机器

**优势**：
- ✅ 与GitLab深度集成，配置即代码
- ✅ YAML配置简单（.gitlab-ci.yml）
- ✅ 支持Docker和Kubernetes
- ✅ 可视化Pipeline状态
- ✅ 内置变量管理和安全扫描

---

## .gitlab-ci.yml配置

### 1. 基础结构

```yaml
stages:
  - build
  - test
  - deploy

# 全局变量
variables:
  MAVEN_OPTS: "-Dmaven.repo.local=.m2/repository"
  DOCKER_REGISTRY: "registry.example.com"

# 默认配置
default:
  image: maven:3.9-eclipse-temurin-21
  cache:
    paths:
      - .m2/repository/

build-job:
  stage: build
  script:
    - mvn clean package -DskipTests
  artifacts:
    paths:
      - target/*.jar
    expire_in: 1 day

test-job:
  stage: test
  script:
    - mvn test
  coverage: '/Total.*?([0-9]{1,3})%/'

deploy-job:
  stage: deploy
  script:
    - echo "Deploying to production..."
  environment:
    name: production
  when: manual  # 手动触发
```

### 2. 核心配置项

**变量管理**：
```yaml
variables:
  # 普通变量
  APP_NAME: "order-service"
  # 引用CI内置变量
  IMAGE_TAG: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

# 文件变量（在GitLab UI中配置敏感信息）
# Settings → CI/CD → Variables
# - REGISTRY_PASSWORD (masked, protected)
# - DEPLOY_KEY (type: file)
# - KUBE_CONFIG (type: file)
```

**缓存策略**：
```yaml
cache:
  key:
    files:
      - pom.xml
    prefix: "$CI_JOB_NAME"
  paths:
    - .m2/repository/
    - target/
  policy: pull-push  # build阶段用pull-push，test阶段用pull

# test阶段只拉取缓存
test-job:
  cache:
    key:
      files:
        - pom.xml
    paths:
      - .m2/repository/
    policy: pull
```

**artifacts制品**：
```yaml
build:
  script: mvn package
  artifacts:
    paths:
      - target/*.jar
      - target/site/jacoco/
    reports:
      junit: target/surefire-reports/TEST-*.xml
      coverage_report:
        coverage_format: jacoco
        path: target/site/jacoco/jacoco.xml
    expire_in: 7 days
    when: always  # 即使失败也上传
```

**条件执行**：
```yaml
deploy-prod:
  stage: deploy
  script: ./deploy.sh production
  rules:
    # main分支自动部署
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: on_success
    # Tag触发部署
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
    # 其他分支不执行
    - when: never

# 仅特定文件变更时触发
api-test:
  script: mvn verify -pl api-module
  rules:
    - changes:
        - api-module/**/*
```

---

## Runner配置

### 1. Runner类型

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| **Shared Runner** | 全局共享 | 小型团队、通用任务 |
| **Group Runner** | 组内共享 | 项目组内专用 |
| **Specific Runner** | 项目专用 | 特定环境、安全要求高 |

### 2. Runner安装

```bash
# Linux安装
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
sudo apt-get install gitlab-runner

# Docker方式运行
docker run -d --name gitlab-runner \
  --restart always \
  -v /srv/gitlab-runner/config:/etc/gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gitlab/gitlab-runner:latest
```

### 3. Runner注册

```bash
# 获取注册Token: Settings → CI/CD → Runners → New project runner

# 注册Runner
sudo gitlab-runner register \
  --url https://gitlab.example.com/ \
  --token glrt-xxxxx \
  --executor docker \
  --docker-image "maven:3.9-eclipse-temurin-21" \
  --docker-privileged \
  --description "docker-runner-prod"
```

**Executor选择**：

| Executor | 性能 | 隔离性 | 适用场景 |
|----------|------|--------|---------|
| **docker** | 高 | 强 | 推荐，每次Job干净环境 |
| **kubernetes** | 高 | 强 | K8s集群，弹性伸缩 |
| **shell** | 最高 | 无 | 需要宿主机权限 |
| **docker+machine** | 高 | 强 | 自动扩缩容 |

---

## 实战案例

### 案例1：Spring Boot项目完整CI/CD

```yaml
stages:
  - validate
  - build
  - test
  - package
  - deploy

variables:
  MAVEN_OPTS: "-Dmaven.repo.local=$CI_PROJECT_DIR/.m2/repository"
  DOCKER_IMAGE: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

# 代码规范检查
validate:
  stage: validate
  image: maven:3.9-eclipse-temurin-21
  script:
    - mvn validate
    - mvn checkstyle:check
  cache: &maven_cache
    key: maven-$CI_COMMIT_REF_SLUG
    paths:
      - .m2/repository/
    policy: pull-push

# 编译构建
build:
  stage: build
  image: maven:3.9-eclipse-temurin-21
  script:
    - mvn compile -DskipTests
  cache:
    <<: *maven_cache
    policy: pull

# 单元测试
unit-test:
  stage: test
  image: maven:3.9-eclipse-temurin-21
  script:
    - mvn test
  artifacts:
    reports:
      junit: target/surefire-reports/TEST-*.xml
    when: always

# 集成测试
integration-test:
  stage: test
  image: maven:3.9-eclipse-temurin-21
  services:
    - name: mysql:8.0
      alias: mysql
    - name: redis:7-alpine
      alias: redis
  variables:
    MYSQL_ROOT_PASSWORD: test
    MYSQL_DATABASE: testdb
    SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/testdb
    SPRING_DATA_REDIS_HOST: redis
  script:
    - mvn verify -Dspring.profiles.active=test
  artifacts:
    reports:
      junit: target/failsafe-reports/TEST-*.xml

# Docker镜像构建
docker-build:
  stage: package
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin $CI_REGISTRY
  script:
    - docker build -t $DOCKER_IMAGE .
    - docker push $DOCKER_IMAGE
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_TAG'

# 部署到K8s
deploy-k8s:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config use-context production
    - kubectl set image deployment/order-service order-service=$DOCKER_IMAGE
    - kubectl rollout status deployment/order-service --timeout=300s
  environment:
    name: production
    url: https://order.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
```

### 案例2：前端项目自动化部署

```yaml
stages:
  - install
  - build
  - deploy

cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/

install:
  stage: install
  image: node:20-alpine
  script:
    - npm ci
  artifacts:
    paths:
      - node_modules/

build:
  stage: build
  image: node:20-alpine
  script:
    - npm run build
  artifacts:
    paths:
      - dist/

deploy-staging:
  stage: deploy
  image: amazon/aws-cli:latest
  script:
    - aws s3 sync dist/ s3://staging-bucket/ --delete
    - aws cloudfront create-invalidation --distribution-id EXXX --paths "/*"
  environment:
    name: staging
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

deploy-prod:
  stage: deploy
  image: amazon/aws-cli:latest
  script:
    - aws s3 sync dist/ s3://prod-bucket/ --delete
    - aws cloudfront create-invalidation --distribution-id EYYY --paths "/*"
  environment:
    name: production
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
```

---

## 多环境部署

### 1. 环境配置

```yaml
# 定义环境
.environments:
  staging: &staging
    name: staging
    url: https://staging-api.example.com
    on_stop: stop-staging

  production: &production
    name: production
    url: https://api.example.com

deploy-staging:
  stage: deploy
  script:
    - ./deploy.sh staging
  environment: *staging
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

deploy-production:
  stage: deploy
  script:
    - ./deploy.sh production
  environment: *production
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual

stop-staging:
  stage: deploy
  script:
    - ./teardown.sh staging
  environment:
    name: staging
    action: stop
  when: manual
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'
```

### 2. 手动审批

```yaml
deploy-production:
  stage: deploy
  script: ./deploy.sh production
  environment:
    name: production
  when: manual  # 需手动点击部署
  allow_failure: false  # 阻断后续Job
  only:
    - main
```

---

## 最佳实践

### 1. Pipeline优化

- **并行执行**：同Stage的Job自动并行
- **缓存Maven/npm依赖**：减少下载时间
- **使用needs关键字**：打破Stage限制，实现DAG依赖

```yaml
# DAG依赖：test不依赖build完成
unit-test:
  stage: test
  needs: [build]
  script: mvn test

integration-test:
  stage: test
  needs: [build]
  script: mvn verify
```

### 2. 缓存策略

```yaml
# 全局缓存
cache: &global_cache
  key: "$CI_COMMIT_REF_SLUG-maven"
  paths:
    - .m2/repository/
  policy: pull-push

# build阶段: 拉取+更新
build:
  cache:
    <<: *global_cache
    policy: pull-push

# test阶段: 只拉取
test:
  cache:
    <<: *global_cache
    policy: pull
```

### 3. 安全管理

- **敏感变量**：在GitLab UI设置Masked+Protected变量
- **镜像扫描**：集成Trivy扫描容器漏洞
- **密钥扫描**：使用GitLab SAST检测泄露

```yaml
container-scanning:
  stage: test
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity HIGH,CRITICAL $DOCKER_IMAGE
  allow_failure: false
```

# Jenkins流水线实战

> 掌握Jenkins Pipeline，实现自动化构建与部署

---

## 📋 目录

1. [Jenkins概述](#jenkins概述)
2. [Pipeline基础](#pipeline基础)
3. [Pipeline语法详解](#pipeline语法详解)
4. [实战案例](#实战案例)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)

---

## Jenkins概述

### 什么是Jenkins？

**定义**：开源的持续集成/持续交付工具

**核心功能**：
- 🔧 自动化构建
- 🧪 自动化测试
- 📦 制品管理
- 🚀 自动化部署

**为什么选择Jenkins？**
- ✅ 开源免费
- ✅ 插件丰富（1800+）
- ✅ 社区活跃
- ✅ 高度可定制

---

## Pipeline基础

### 1. Pipeline概念

**Pipeline = 流水线 = 一系列自动化步骤**

```
代码提交 → 代码检查 → 编译构建 → 单元测试 
→ 打包 → 部署测试环境 → 集成测试 → 部署生产环境
```

### 2. Pipeline类型

**Declarative Pipeline（声明式）**：
- 结构化语法
- 易于阅读
- 推荐使用

**Scripted Pipeline（脚本式）**：
- 灵活强大
- 学习曲线陡峭

### 3. Jenkinsfile

**定义**：Pipeline脚本文件

**位置**：项目根目录

**好处**：
- ✅ 版本控制
- ✅ 团队协作
- ✅ Pipeline即代码

---

## Pipeline语法详解

### 1. 基础结构

```groovy
pipeline {
    agent any
    
    stages {
        stage('构建') {
            steps {
                echo 'Building...'
            }
        }
        
        stage('测试') {
            steps {
                echo 'Testing...'
            }
        }
        
        stage('部署') {
            steps {
                echo 'Deploying...'
            }
        }
    }
}
```

### 2. 核心指令

**environment**：指定环境
```groovy
pipeline {
    agent any
    environment {
        APP_NAME = 'myapp'
        DOCKER_REGISTRY = 'registry.example.com'
        VERSION = "${env.BUILD_NUMBER}"
    }
}
```

**parameters**：参数化构建
```groovy
parameters {
    choice(name: 'ENV', choices: ['dev', 'test', 'staging', 'prod'], description: '部署环境')
    string(name: 'VERSION', defaultValue: 'latest', description: '版本号')
    booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: '跳过测试')
}
```

**when**：条件执行
```groovy
stage('Deploy Prod') {
    when {
        branch 'main'
        environment name: 'ENV', value: 'prod'
    }
    steps {
        sh 'kubectl apply -f k8s/prod/'
    }
}
```

**post**：构建后处理
```groovy
post {
    success {
        echo '构建成功！'
        dingtalk(robot: 'jenkins', type: 'MARKDOWN', text: ["✅ ${APP_NAME} 部署成功"])
    }
    failure {
        echo '构建失败！'
        dingtalk(robot: 'jenkins', type: 'MARKDOWN', text: ["❌ ${APP_NAME} 部署失败"])
    }
    always {
        cleanWs()  // 清理工作空间
    }
}
```

---

## 实战案例

### 案例1：Spring Boot项目自动化部署

```groovy
pipeline {
    agent any
    
    environment {
        APP_NAME = 'order-service'
        DOCKER_REGISTRY = 'registry.cn-hangzhou.aliyuncs.com'
        IMAGE_TAG = "${DOCKER_REGISTRY}/myapp/${APP_NAME}:${BUILD_NUMBER}"
    }
    
    tools {
        maven 'Maven-3.8'
        jdk 'JDK-17'
    }
    
    stages {
        stage('代码检出') {
            steps {
                git branch: 'main', url: 'https://gitlab.com/myapp/order-service.git'
            }
        }
        
        stage('编译构建') {
            steps {
                sh 'mvn clean package -DskipTests'
            }
        }
        
        stage('单元测试') {
            steps {
                sh 'mvn test'
            }
            post {
                always {
                    junit 'target/surefire-reports/**/*.xml'
                }
            }
        }
        
        stage('代码检查') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh 'mvn sonar:sonar'
                }
            }
        }
        
        stage('构建镜像') {
            steps {
                sh """
                    docker build -t ${IMAGE_TAG} .
                    docker push ${IMAGE_TAG}
                """
            }
        }
        
        stage('部署测试环境') {
            steps {
                sh """
                    kubectl set image deployment/${APP_NAME} ${APP_NAME}=${IMAGE_TAG} -n test
                    kubectl rollout status deployment/${APP_NAME} -n test --timeout=300s
                """
            }
        }
        
        stage('部署生产环境') {
            when {
                branch 'main'
            }
            input {
                message '确认部署到生产环境？'
                ok '确认部署'
            }
            steps {
                sh """
                    kubectl set image deployment/${APP_NAME} ${APP_NAME}=${IMAGE_TAG} -n prod
                    kubectl rollout status deployment/${APP_NAME} -n prod --timeout=300s
                """
            }
        }
    }
}
```

### 案例2：微服务项目多模块构建

```groovy
pipeline {
    agent any
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
            }
        }
        
        stage('并行构建') {
            parallel {
                stage('用户服务') {
                    steps {
                        dir('user-service') {
                            sh 'mvn clean package -DskipTests'
                        }
                    }
                }
                stage('订单服务') {
                    steps {
                        dir('order-service') {
                            sh 'mvn clean package -DskipTests'
                        }
                    }
                }
                stage('商品服务') {
                    steps {
                        dir('product-service') {
                            sh 'mvn clean package -DskipTests'
                        }
                    }
                }
            }
        }
        
        stage('构建Docker镜像') {
            steps {
                script {
                    def services = ['user-service', 'order-service', 'product-service']
                    services.each { svc ->
                        sh """
                            docker build -t ${svc}:${BUILD_NUMBER} ./${svc}
                            docker push registry.example.com/myapp/${svc}:${BUILD_NUMBER}
                        """
                    }
                }
            }
        }
    }
}
```

### 案例3：前后端分离项目部署

```groovy
pipeline {
    agent any
    
    stages {
        stage('构建后端') {
            steps {
                dir('backend') {
                    sh 'mvn clean package -DskipTests'
                    sh 'docker build -t backend:${BUILD_NUMBER} .'
                }
            }
        }
        
        stage('构建前端') {
            steps {
                dir('frontend') {
                    sh 'npm install'
                    sh 'npm run build'
                    sh 'docker build -t frontend:${BUILD_NUMBER} .'
                }
            }
        }
        
        stage('部署') {
            steps {
                sh 'docker-compose up -d'
            }
        }
    }
}
```

---

## 最佳实践

### 1. Pipeline设计原则

```
1. 快速反馈：单元测试阶段控制在5分钟内
2. 阶段分明：Build → Test → Deploy
3. 失败快速：任一阶段失败立即终止
4. 可重复性：相同代码多次构建结果一致
5. 幂等性：部署操作可安全重复执行
```

### 2. 性能优化

```groovy
// 1. 并行执行独立任务
stage('并行测试') {
    parallel {
        stage('单元测试') { steps { sh 'mvn test' } }
        stage('集成测试') { steps { sh 'mvn verify -P integration' } }
    }
}

// 2. Maven缓存
options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
}
// 配置Maven本地仓库缓存，避免每次下载依赖

// 3. 增量构建
// 只构建变更的模块
sh 'mvn compile -pl module-changed -am'
```

### 3. 安全管理

```groovy
// 1. 使用Credentials管理敏感信息
withCredentials([usernamePassword(credentialsId: 'docker-registry', 
    usernameVariable: 'REGISTRY_USER', 
    passwordVariable: 'REGISTRY_PASS')]) {
    sh 'docker login -u $REGISTRY_USER -p $REGISTRY_PASS registry.example.com'
}

// 2. 不在Pipeline中硬编码密码
// ❌ sh 'mysql -u root -p123456'
// ✅ 使用Credentials或环境变量

// 3. 审计日志
// 启用Pipeline日志记录，追踪谁在何时做了什么操作
```

---

## 常见问题

### Q1：Pipeline构建失败如何排查？

```
1. 查看Console Output：Jenkins页面 → Build History → Console Output
2. 检查构建日志中的ERROR信息
3. 本地复现：在本地执行Pipeline中的命令
4. 检查环境差异：Jenkins环境vs本地环境
5. 检查网络问题：能否访问外部仓库、镜像仓库
```

### Q2：如何实现并行构建？

```groovy
// 方式1：parallel阶段
stage('并行') {
    parallel {
        stage('任务A') { steps { sh './task-a.sh' } }
        stage('任务B') { steps { sh './task-b.sh' } }
    }
}

// 方式2：并行矩阵（多配置构建）
matrix {
    axes {
        axis { name 'JDK'; values '11', '17' }
        axis { name 'OS'; values 'linux', 'windows' }
    }
    stages {
        stage('Build') { steps { sh 'mvn package' } }
    }
}
```

### Q3：如何管理不同环境的配置？

```
1. 使用ConfigMap/Secret管理K8s配置
2. 使用Spring Profile区分环境
3. Jenkins参数化构建指定环境
4. 使用Git分支对应不同环境
   - develop → 开发环境
   - release → 测试环境
   - main → 生产环境
```

---

**最后更新**: 2025-12-22


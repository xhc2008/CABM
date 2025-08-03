# CABM Docker 部署文档

## 📋 概述

本文档介绍如何使用 CABM 项目提供的 Docker 脚手架工具进行开发、部署和发布。我们提供了两个核心脚本来简化 Docker 操作：

- **`deploy-docker.sh`** - 本地开发和部署管理
- **`release.sh`** - 镜像构建和发布到注册表

## 🛠️ 环境准备

### 系统要求

- Docker 20.10+ 
- Docker Buildx (多架构构建支持)
- Git (用于版本信息)
- Linux/macOS/Windows(WSL2)

### 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# macOS
brew install docker

# Windows
# 下载 Docker Desktop: https://www.docker.com/products/docker-desktop
```

### 启用 Docker Buildx

```bash
# 安装 buildx 插件
docker buildx install

# 创建多架构构建器
docker buildx create --name multiarch --driver docker-container --use
docker buildx inspect --bootstrap
```

## 🔧 配置环境变量

### 创建环境配置文件

复制示例配置文件并填入您的 API 密钥：

```bash
cp .env.example .env
```

### 编辑 .env 文件

```bash
# 必需配置 - API 密钥
CHAT_API_KEY=your_api_key_here
IMAGE_API_KEY=your_api_key_here
TTS_SERVICE_API_KEY=your_api_key_here

# 可选配置
DEBUG=false
HOST=0.0.0.0
PORT=5000
```

**⚠️ 注意事项：**
- 请将 `your_api_key_here` 替换为您的真实 API 密钥
- 不要将包含真实密钥的 `.env` 文件提交到版本控制系统
- 生产环境建议使用 Docker Secrets 或环境变量注入

## 🚀 本地开发和部署

### 使用 deploy-docker.sh

这是您的主要开发工具，提供完整的容器生命周期管理。

#### 基本命令

```bash
# 显示帮助信息
./deploy-docker.sh --help

# 一键部署（推荐新手使用）
./deploy-docker.sh deploy

# 快速构建部署
./deploy-docker.sh deploy --fast
```

#### 构建镜像

```bash
# 标准构建
./deploy-docker.sh build

# 网络优化构建（使用国内镜像源）
./deploy-docker.sh build --fast

# 无缓存构建
./deploy-docker.sh build --no-cache
```

#### 容器管理

```bash
# 运行容器
./deploy-docker.sh run

# 后台运行
./deploy-docker.sh run -d

# 指定端口
./deploy-docker.sh run --port 8080

# 启动/停止/重启
./deploy-docker.sh start
./deploy-docker.sh stop  
./deploy-docker.sh restart
```

#### 监控和调试

```bash
# 查看容器状态
./deploy-docker.sh status

# 查看实时日志
./deploy-docker.sh logs -f

# 进入容器 Shell
./deploy-docker.sh shell

# 查看最近100行日志
./deploy-docker.sh logs --tail 100
```

#### 清理

```bash
# 清理容器和镜像
./deploy-docker.sh clean
```

### 开发工作流示例

```bash
# 1. 首次设置
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥

# 2. 一键部署
./deploy-docker.sh deploy --fast

# 3. 查看应用状态
./deploy-docker.sh status
./deploy-docker.sh logs -f

# 4. 代码修改后更新
./deploy-docker.sh update --fast

# 5. 调试问题
./deploy-docker.sh shell
```

## 📦 镜像发布

### 使用 release.sh

专门用于构建多架构镜像并发布到各种注册表。

#### 基本发布

```bash
# 显示帮助
./release.sh --help

# 构建但不推送（本地测试）
./release.sh

# 构建并推送到所有注册表
./release.sh --push

# 发布特定版本
./release.sh -v 1.0.0 --push
```

#### 高级发布选项

```bash
# 发布到特定注册表
./release.sh -r docker.io --push
./release.sh -r ghcr.io --push
./release.sh -r registry.cn-hangzhou.aliyuncs.com --push

# 构建特定平台
./release.sh -p linux/amd64 --push
./release.sh -p linux/arm64 --push

# 预览发布命令
./release.sh --dry-run --push
```

### 支持的注册表

| 注册表 | 地址 | 说明 |
|--------|------|------|
| Docker Hub | docker.io | 最流行的公共注册表 |
| GitHub Container Registry | ghcr.io | GitHub 集成注册表 |
| 阿里云容器镜像服务 | registry.cn-hangzhou.aliyuncs.com | 中国大陆访问友好 |

### 注册表认证

#### Docker Hub
```bash
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password
```

#### GitHub Container Registry
```bash
export GITHUB_ACTOR=your_github_username
export GITHUB_TOKEN=your_github_token
```

#### 阿里云容器镜像服务
```bash
export ALIYUN_USERNAME=your_aliyun_username
export ALIYUN_PASSWORD=your_aliyun_password
export ALIYUN_NAMESPACE=your_namespace
```

### 发布工作流示例

```bash
# 1. 设置认证信息
export DOCKER_USERNAME=myusername
export DOCKER_PASSWORD=mypassword

# 2. 本地测试构建
./release.sh -v 1.0.0

# 3. 发布到 Docker Hub
./release.sh -v 1.0.0 -r docker.io --push

# 4. 发布到所有注册表
./release.sh -v 1.0.0 --push

# 5. 发布开发版本（不标记为latest）
./release.sh -v dev-20250103 --no-latest --push
```

## 🔄 CI/CD 集成

### GitHub Actions

我们已经为您准备了 GitHub Actions 配置文件（`.github/workflows/docker.yml`），支持：

- 自动多架构构建
- 发布到多个注册表
- 版本标签管理
- Pull Request 构建测试

### 手动触发发布

```bash
# 在项目根目录
git tag v1.0.0
git push origin v1.0.0

# 或者手动触发 workflow
# 在 GitHub 仓库页面 -> Actions -> 选择 workflow -> Run workflow
```

## 📁 目录结构

```
CABM/
├── deploy-docker.sh          # 开发部署脚本
├── release.sh               # 镜像发布脚本
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 配置
├── .env                    # 环境变量配置
├── .env.example            # 环境变量模板
├── .dockerignore           # Docker 忽略文件
└── .github/
    └── workflows/
        └── docker.yml      # GitHub Actions CI/CD
```

## 🐛 常见问题

### 1. 端口被占用

```bash
# 问题：Error: Port 5000 is already in use
# 解决：
./deploy-docker.sh run --port 8080
# 或者停止占用端口的服务
sudo lsof -ti:5000 | xargs kill -9
```

### 2. Docker 权限问题

```bash
# 问题：Permission denied while trying to connect to Docker daemon
# 解决：将用户添加到 docker 组
sudo usermod -aG docker $USER
# 重新登录生效
```

### 3. 镜像构建失败

```bash
# 清理并重试
./deploy-docker.sh clean
./deploy-docker.sh build --no-cache
```

### 4. 网络问题

```bash
# 使用国内镜像源
./deploy-docker.sh build --fast
```

### 5. 容器启动失败

```bash
# 查看详细日志
./deploy-docker.sh logs

# 进入容器调试
./deploy-docker.sh shell
```

### 6. API 密钥配置错误

```bash
# 检查环境变量
./deploy-docker.sh shell
env | grep API

# 重新配置 .env 文件
cp .env.example .env
# 编辑 .env 并重新部署
./deploy-docker.sh update
```

## 📊 性能优化

### 构建优化

```bash
# 使用 .dockerignore 减少构建上下文
echo "node_modules/" >> .dockerignore
echo "*.log" >> .dockerignore

# 使用多阶段构建（已在 Dockerfile 中配置）
# 使用国内镜像源加速
./deploy-docker.sh build --fast
```

### 运行优化

```bash
# 限制容器资源使用
docker run --memory=1g --cpus=1 cabm:latest

# 使用数据卷持久化数据
# （deploy-docker.sh 已自动配置）
```

## 🔒 安全最佳实践

1. **环境变量安全**
   - 不要在代码中硬编码密钥
   - 使用 `.env` 文件管理敏感信息
   - 生产环境使用 Docker Secrets

2. **镜像安全**
   - 定期更新基础镜像
   - 使用官方镜像
   - 扫描镜像漏洞

3. **网络安全**
   - 仅暴露必要端口
   - 使用反向代理
   - 配置防火墙规则

## 📖 进阶用法

### 自定义构建参数

编辑 `Dockerfile` 添加构建参数：

```dockerfile
ARG CUSTOM_VERSION=latest
ARG BUILD_ENV=production
```

在脚本中使用：

```bash
# 修改 deploy-docker.sh 或 release.sh
docker build --build-arg CUSTOM_VERSION=1.0.0 .
```

### 多环境部署

```bash
# 开发环境
./deploy-docker.sh run --env-file .env.dev

# 测试环境  
./deploy-docker.sh run --env-file .env.test

# 生产环境
./deploy-docker.sh run --env-file .env.prod
```

### 监控集成

```bash
# 添加健康检查
# （已在 Dockerfile 中配置）

# 集成 Prometheus 监控
# 在 docker-compose.yml 中添加监控服务
```

## 🤝 贡献指南

如果您想改进这些脚本：

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 创建 Pull Request

## 📞 技术支持

如果遇到问题：

1. 查看本文档的常见问题部分
2. 检查项目的 GitHub Issues
3. 在 GitHub 上创建新的 Issue

---

**🎉 现在您已经掌握了 CABM Docker 部署的全部技能！开始您的容器化之旅吧！**

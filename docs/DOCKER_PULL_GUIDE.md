# Docker 镜像直接拉取部署指南

本指南详细介绍如何直接拉取预构建的 Docker 镜像来部署 CABM 应用，无需本地构建。

## 📦 可用镜像源

### GitHub Container Registry (推荐)
- **镜像地址**: `ghcr.io/leletxh/cabm`
- **标签**: `latest`、分支名、commit SHA
- **架构支持**: `linux/amd64`、`linux/arm64`
- **优势**: 
  - 与源码同步构建
  - 支持多架构
  - 无需额外配置
  - 自动安全扫描

## 🚀 快速部署

### 方法一：Docker Run 命令

#### 1. 准备环境配置

创建工作目录并配置环境变量：

```bash
# 创建工作目录
mkdir cabm-app && cd cabm-app

# 创建环境配置文件
cat > .env << 'EOF'
# API 配置（必需）
CHAT_API_BASE_URL=https://api.siliconflow.cn/v1
CHAT_API_KEY=your_api_key_here
CHAT_MODEL=deepseek-ai/DeepSeek-V3

IMAGE_API_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_API_KEY=your_api_key_here
IMAGE_MODEL=Kwai-Kolors/Kolors

OPTION_API_BASE_URL=https://api.siliconflow.cn/v1
OPTION_API_KEY=your_api_key_here
OPTION_MODEL=Qwen/Qwen3-8B

MEMORY_API_BASE_URL=https://api.siliconflow.cn/v1
MEMORY_API_KEY=your_api_key_here
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3

# TTS 配置（可选）
TTS_SERVICE_URL_GPTSoVITS=http://127.0.0.1:9880
TTS_SERVICE_URL_SiliconFlow=https://api.siliconflow.cn/v1
TTS_SERVICE_API_KEY=your_api_key_here
TTS_SERVICE_METHOD=siliconflow

# 应用配置
DEBUG=False
PORT=5000
HOST=0.0.0.0
EOF

# 编辑 .env 文件，填入你的实际 API 密钥
nano .env  # 或使用其他编辑器
```

#### 2. 创建数据目录

```bash
# 创建持久化数据目录
mkdir -p data/history data/memory data/scenes
mkdir -p static/images/cache
mkdir -p static/audio
```

#### 3. 运行容器

```bash
# 拉取并运行最新版本
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/images/cache:/app/static/images/cache \
  -v $(pwd)/static/audio:/app/static/audio \
  --restart unless-stopped \
  ghcr.io/leletxh/cabm:latest
```

#### 4. 验证部署

```bash
# 检查容器状态
docker ps

# 查看启动日志
docker logs -f cabm-app

# 访问应用
echo "应用已启动，请访问: http://localhost:5000"
```

### 方法二：Docker Compose

#### 1. 创建 docker-compose.yml

```bash
# 创建工作目录
mkdir cabm-app && cd cabm-app

# 创建 docker-compose.yml 文件
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  cabm:
    image: ghcr.io/leletxh/cabm:latest
    container_name: cabm-app
    ports:
      - "5000:5000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./static/images/cache:/app/static/images/cache
      - ./static/audio:/app/static/audio
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
```

#### 2. 配置环境变量

```bash
# 创建环境配置文件（同上面的 .env 文件内容）
# 参考方法一中的环境配置步骤
```

#### 3. 启动服务

```bash
# 创建数据目录
mkdir -p data/history data/memory data/scenes
mkdir -p static/images/cache
mkdir -p static/audio

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 🔄 镜像版本管理

### 可用标签

- `latest`: 最新稳定版本（主分支最新构建）
- `main-{commit_sha}`: 主分支特定提交版本
- `{branch_name}`: 特定分支的最新版本
- `{custom_tag}`: 手动发布的版本标签

### 更新镜像

#### 使用 Docker Run

```bash
# 停止当前容器
docker stop cabm-app
docker rm cabm-app

# 拉取最新镜像
docker pull ghcr.io/leletxh/cabm:latest

# 重新运行容器（使用之前的命令）
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/images/cache:/app/static/images/cache \
  -v $(pwd)/static/audio:/app/static/audio \
  --restart unless-stopped \
  ghcr.io/leletxh/cabm:latest
```

#### 使用 Docker Compose

```bash
# 拉取最新镜像
docker-compose pull

# 重启服务
docker-compose up -d
```

## 🔧 高级配置

### 自定义端口

```bash
# 修改端口映射
docker run -d --name cabm-app \
  -p 8080:5000 \  # 映射到主机的 8080 端口
  # ... 其他参数保持不变
```

### 使用外部数据库

如果你有外部 Redis 或其他数据库服务：

```bash
# 在 .env 文件中添加数据库配置
echo "REDIS_URL=redis://your-redis-host:6379" >> .env
```

### 内存限制

```bash
# 限制容器内存使用
docker run -d --name cabm-app \
  --memory=2g \
  --memory-swap=2g \
  # ... 其他参数
```

### 网络配置

```bash
# 使用自定义网络
docker network create cabm-network

docker run -d --name cabm-app \
  --network cabm-network \
  # ... 其他参数
```

## 📋 环境变量详解

### 必需配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `CHAT_API_BASE_URL` | 聊天 API 基础 URL | `https://api.siliconflow.cn/v1` |
| `CHAT_API_KEY` | 聊天 API 密钥 | `sk-xxx` |
| `CHAT_MODEL` | 聊天模型名称 | `deepseek-ai/DeepSeek-V3` |
| `IMAGE_API_BASE_URL` | 图像 API 基础 URL | `https://api.siliconflow.cn/v1` |
| `IMAGE_API_KEY` | 图像 API 密钥 | `sk-xxx` |
| `IMAGE_MODEL` | 图像模型名称 | `Kwai-Kolors/Kolors` |

### 可选配置

| 变量名 | 说明 | 默认值 |
|--------|------|---------|
| `PORT` | 应用端口 | `5000` |
| `HOST` | 绑定地址 | `0.0.0.0` |
| `DEBUG` | 调试模式 | `False` |
| `TTS_SERVICE_METHOD` | TTS 服务方法 | `siliconflow` |

## 🔍 故障排除

### 镜像拉取失败

```bash
# 检查网络连接
docker pull hello-world

# 手动拉取镜像
docker pull ghcr.io/leletxh/cabm:latest

# 如果仍然失败，尝试使用代理
# docker pull --platform linux/amd64 ghcr.io/leletxh/cabm:latest
```

### 容器启动失败

```bash
# 查看详细错误信息
docker logs cabm-app

# 检查环境变量
docker exec cabm-app env | grep -E "(API_KEY|API_BASE_URL)"

# 进入容器调试
docker exec -it cabm-app /bin/bash
```

### 应用无法访问

1. 检查端口映射是否正确
2. 检查防火墙设置
3. 检查容器网络配置

```bash
# 检查端口占用
netstat -tlnp | grep 5000

# 检查容器网络
docker inspect cabm-app | grep -A 10 NetworkSettings
```

### 数据持久化问题

```bash
# 检查数据卷挂载
docker inspect cabm-app | grep -A 10 Mounts

# 确保目录权限正确
chmod -R 755 ./data ./static
```

## 📚 相关文档

- [DOCKER_DEPLOY_GUIDE.md](./DOCKER_DEPLOY_GUIDE.md) - 完整 Docker 部署指南
- [WINDOWS_DEPLOY_GUIDE.md](./WINDOWS_DEPLOY_GUIDE.md) - Windows 部署指南
- [TTS_GPTSoVITS.md](./TTS_GPTSoVITS.md) - TTS 服务配置指南

## ⚡ 一键部署脚本

创建一个快速部署脚本：

```bash
cat > deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 CABM Docker 快速部署脚本"
echo "=============================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 创建工作目录
echo "📁 创建工作目录..."
mkdir -p cabm-app && cd cabm-app
mkdir -p data/history data/memory data/scenes
mkdir -p static/images/cache static/audio

# 创建环境配置文件
echo "⚙️  创建配置文件..."
if [ ! -f .env ]; then
    cat > .env << 'ENVEOF'
# API 配置（请修改为你的实际密钥）
CHAT_API_BASE_URL=https://api.siliconflow.cn/v1
CHAT_API_KEY=your_api_key_here
CHAT_MODEL=deepseek-ai/DeepSeek-V3

IMAGE_API_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_API_KEY=your_api_key_here
IMAGE_MODEL=Kwai-Kolors/Kolors

OPTION_API_BASE_URL=https://api.siliconflow.cn/v1
OPTION_API_KEY=your_api_key_here
OPTION_MODEL=Qwen/Qwen3-8B

MEMORY_API_BASE_URL=https://api.siliconflow.cn/v1
MEMORY_API_KEY=your_api_key_here
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-v2-m3

# TTS 配置（可选）
TTS_SERVICE_METHOD=siliconflow
TTS_SERVICE_URL_SiliconFlow=https://api.siliconflow.cn/v1
TTS_SERVICE_API_KEY=your_api_key_here

# 应用配置
DEBUG=False
PORT=5000
HOST=0.0.0.0
ENVEOF
    echo "📝 请编辑 .env 文件，填入你的 API 密钥"
    echo "   nano .env"
    read -p "配置完成后按 Enter 继续..."
fi

# 拉取并运行容器
echo "🐳 拉取 Docker 镜像..."
docker pull ghcr.io/leletxh/cabm:latest

echo "🚀 启动容器..."
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/images/cache:/app/static/images/cache \
  -v $(pwd)/static/audio:/app/static/audio \
  --restart unless-stopped \
  ghcr.io/leletxh/cabm:latest

# 检查部署状态
echo "✅ 部署完成！"
echo "📊 容器状态："
docker ps | grep cabm-app

echo ""
echo "🌐 访问地址: http://localhost:5000"
echo "📋 管理命令:"
echo "   查看日志: docker logs -f cabm-app"
echo "   停止服务: docker stop cabm-app"
echo "   重启服务: docker restart cabm-app"
EOF

chmod +x deploy.sh
```

使用部署脚本：

```bash
# 下载并运行一键部署脚本
curl -o deploy.sh https://raw.githubusercontent.com/leletxh/CABM/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

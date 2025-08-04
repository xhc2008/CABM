# Docker 部署指南

## GitHub Actions 自动构建

### 设置 GitHub Secrets

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加以下 secrets：

1. `DOCKER_USERNAME` - 你的 Docker Hub 用户名
2. `DOCKER_PASSWORD` - 你的 Docker Hub 密码或访问令牌

**注意**: GitHub Container Registry 使用 `GITHUB_TOKEN`，无需额外配置。

### 手动触发构建

1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Docker Build and Push" workflow
3. 点击 "Run workflow"
4. 可选择设置：
   - `tag`: Docker 镜像标签（默认：latest）
   - `push_to_registry`: 是否推送到 Docker Hub（默认：true）

构建完成后，镜像将同时推送到：
- Docker Hub: `docker.io/{DOCKER_USERNAME}/cabm:{tag}`
- GitHub Container Registry: `ghcr.io/{REPOSITORY_OWNER}/cabm:{tag}`

## 本地部署

### 方法1：使用 Docker Run

**选择镜像源：**

**从 Docker Hub 拉取：**
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 2. 创建必要的目录
mkdir -p data static/images/cache

# 3. 运行容器
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/images/cache:/app/static/images/cache \
  --restart unless-stopped \
  {DOCKER_USERNAME}/cabm:latest
```

**从 GitHub Container Registry 拉取：**
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 2. 创建必要的目录
mkdir -p data static/images/cache

# 3. 运行容器
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/images/cache:/app/static/images/cache \
  --restart unless-stopped \
  ghcr.io/{REPOSITORY_OWNER}/cabm:latest
```

### 方法2：使用 Docker Compose

**选择镜像源：**

**从 GitHub Container Registry (推荐)：**
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 2. 创建必要的目录
mkdir -p data static/images/cache static/audio

# 3. 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

**从 Docker Hub：**
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 2. 创建必要的目录
mkdir -p data static/images/cache static/audio

# 3. 启动服务
docker-compose -f docker-compose.dockerhub.yml up -d
```

### 环境变量配置

编辑 `.env` 文件，配置以下必需的环境变量：

```bash
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
HOST=localhost
```

## 访问应用

启动成功后，访问 http://localhost:5000

## 管理命令

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f cabm-app

# 停止容器
docker stop cabm-app

# 重启容器
docker restart cabm-app

# 删除容器
docker rm -f cabm-app

# 更新镜像
docker pull {DOCKER_USERNAME}/cabm:latest
# 或者从 GitHub Container Registry
# docker pull ghcr.io/{REPOSITORY_OWNER}/cabm:latest

docker stop cabm-app
docker rm cabm-app
# 然后重新运行 docker run 命令
```

## 故障排除

### 容器无法启动
- 检查 `.env` 文件是否正确配置
- 检查端口 5000 是否被占用
- 查看容器日志：`docker logs cabm-app`

### API 调用失败
- 检查 API 密钥是否正确
- 检查网络连接
- 检查 API 服务是否可用

### TTS 功能异常
- 检查 TTS 配置是否正确
- 如果使用 GPT-SoVITS，确保服务正在运行
- 检查参考音频文件是否存在于 `static/audio` 目录

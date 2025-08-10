#!/bin/bash

echo "🚀 CABM Docker 快速部署脚本"
echo "=============================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "安装指南: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查 Docker 服务是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 服务未运行，请启动 Docker 服务"
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
    cat > .env << 'EOF'
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
EOF
    echo "📝 已创建 .env 配置文件"
    echo "⚠️  请编辑 .env 文件，将 'your_api_key_here' 替换为你的实际 API 密钥"
    echo "   可以使用: nano .env 或 vim .env"
    echo ""
    read -p "按 Enter 继续（请确保已配置 API 密钥）..."
fi

# 停止并删除现有容器（如果存在）
if docker ps -a | grep -q cabm-app; then
    echo "🔄 检测到现有容器，正在更新..."
    docker stop cabm-app 2>/dev/null
    docker rm cabm-app 2>/dev/null
fi

# 拉取并运行容器
echo "🐳 拉取最新 Docker 镜像..."
if ! docker pull ghcr.io/leletxh/cabm:latest; then
    echo "❌ 镜像拉取失败，请检查网络连接或尝试使用代理"
    exit 1
fi

echo "🚀 启动容器..."
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/static/images/cache:/app/static/images/cache" \
  -v "$(pwd)/static/audio:/app/static/audio" \
  --restart unless-stopped \
  ghcr.io/leletxh/cabm:latest

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 5

# 检查部署状态
if docker ps | grep -q cabm-app; then
    echo "✅ 部署成功！"
    echo ""
    echo "📊 容器状态："
    docker ps | grep cabm-app
    echo ""
    echo "🌐 访问地址: http://localhost:5000"
    echo ""
    echo "📋 常用管理命令:"
    echo "   查看日志: docker logs -f cabm-app"
    echo "   停止服务: docker stop cabm-app"
    echo "   重启服务: docker restart cabm-app"
    echo "   删除容器: docker rm -f cabm-app"
    echo "   更新镜像: docker pull ghcr.io/leletxh/cabm:latest"
    echo ""
    echo "🔧 故障排除:"
    echo "   如果无法访问，请检查:"
    echo "   1. .env 文件中的 API 密钥是否正确"
    echo "   2. 端口 5000 是否被其他程序占用: lsof -i :5000"
    echo "   3. 防火墙是否阻止了端口访问"
    echo "   4. 查看容器日志: docker logs cabm-app"
else
    echo "❌ 部署失败！"
    echo "📋 查看错误日志："
    docker logs cabm-app
    exit 1
fi

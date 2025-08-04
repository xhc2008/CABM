# CABM Docker 快速部署脚本 (Windows PowerShell)

Write-Host "🚀 CABM Docker 快速部署脚本 (Windows)" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# 检查 Docker 是否安装
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker 已安装: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未安装，请先安装 Docker Desktop for Windows" -ForegroundColor Red
    Write-Host "下载地址: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# 创建工作目录
Write-Host "📁 创建工作目录..." -ForegroundColor Cyan
$workDir = "cabm-app"
if (!(Test-Path $workDir)) {
    New-Item -ItemType Directory -Path $workDir | Out-Null
}
Set-Location $workDir

# 创建数据目录
$dataDirs = @("data\history", "data\memory", "data\scenes", "static\images\cache", "static\audio")
foreach ($dir in $dataDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# 创建环境配置文件
Write-Host "⚙️  创建配置文件..." -ForegroundColor Cyan
if (!(Test-Path ".env")) {
    $envContent = @"
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
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "📝 请编辑 .env 文件，填入你的 API 密钥" -ForegroundColor Yellow
    Write-Host "   可以使用: notepad .env" -ForegroundColor Yellow
    Read-Host "配置完成后按 Enter 继续"
}

# 停止并删除现有容器（如果存在）
$existingContainer = docker ps -a --filter "name=cabm-app" --format "{{.Names}}"
if ($existingContainer -eq "cabm-app") {
    Write-Host "🔄 检测到现有容器，正在更新..." -ForegroundColor Yellow
    docker stop cabm-app 2>$null
    docker rm cabm-app 2>$null
}

# 拉取并运行容器
Write-Host "🐳 拉取最新 Docker 镜像..." -ForegroundColor Cyan
docker pull ghcr.io/leletxh/cabm:latest

Write-Host "🚀 启动容器..." -ForegroundColor Cyan
$currentPath = (Get-Location).Path
docker run -d --name cabm-app `
  -p 5000:5000 `
  --env-file .env `
  -v "${currentPath}\data:/app/data" `
  -v "${currentPath}\static\images\cache:/app/static/images/cache" `
  -v "${currentPath}\static\audio:/app/static/audio" `
  --restart unless-stopped `
  ghcr.io/leletxh/cabm:latest

# 等待容器启动
Write-Host "⏳ 等待容器启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 检查部署状态
$runningContainer = docker ps --filter "name=cabm-app" --format "{{.Names}}"
if ($runningContainer -eq "cabm-app") {
    Write-Host "✅ 部署成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 容器状态：" -ForegroundColor Cyan
    docker ps --filter "name=cabm-app"
    Write-Host ""
    Write-Host "🌐 访问地址: http://localhost:5000" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 常用管理命令:" -ForegroundColor Cyan
    Write-Host "   查看日志: docker logs -f cabm-app"
    Write-Host "   停止服务: docker stop cabm-app"
    Write-Host "   重启服务: docker restart cabm0-app"
    Write-Host "   删除容器: docker rm -f cabm-app"
    Write-Host "   更新镜像: docker pull ghcr.io/leletxh/cabm:latest"
    Write-Host ""
    Write-Host "🔧 故障排除:" -ForegroundColor Yellow
    Write-Host "   如果无法访问，请检查:"
    Write-Host "   1. .env 文件中的 API 密钥是否正确"
    Write-Host "   2. 端口 5000 是否被其他程序占用"
    Write-Host "   3. Windows 防火墙是否阻止了端口访问"
    Write-Host "   4. Docker Desktop 是否正常运行"
} else {
    Write-Host "❌ 部署失败！" -ForegroundColor Red
    Write-Host "📋 查看错误日志：" -ForegroundColor Yellow
    docker logs cabm-app
    exit 1
}

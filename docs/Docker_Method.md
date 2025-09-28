## 🐳方法二：Docker 快速部署
### 📋 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 2GB以上的可用内存
- 1GB以上的可用存储空间
### 🚀 方法1：直接拉取镜像部署（最简单）

无需克隆代码，直接使用预构建镜像：

```bash
# Linux/macOS 一键部署
curl -o deploy.sh https://raw.githubusercontent.com/leletxh/CABM/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

```powershell
# Windows PowerShell 一键部署
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/leletxh/CABM/main/deploy.ps1" -OutFile "deploy.ps1"
PowerShell -ExecutionPolicy Bypass -File deploy.ps1
```

**[📖 Docker 镜像直接拉取部署指南](/docs/DOCKER_PULL_GUIDE.md)**

### 源码构建部署

```bash
# 克隆项目
git clone https://github.com/leletxh/CABM.git
cd CABM
```
> 编辑 .env.docker 文件，需前往[硅基流动平台](https://cloud.siliconflow.cn/i/mVqMyTZk)申请你的API Key
```bash
# 一键部署
./deploy-docker.sh deploy
```

### 方法2：手动部署

```bash
# 1. 配置环境变量
cp .env.docker .env.docker
```
> 编辑 .env.docker 文件，需前往[硅基流动平台](https://cloud.siliconflow.cn/i/mVqMyTZk)申请你的API Key
```bash
# 2. 构建镜像
./deploy-docker.sh build

# 3. 运行容器
./deploy-docker.sh run

# 4. 访问应用
# http://localhost:5000
```

**更多部署选项：**
- [📖 Docker 镜像直接拉取部署指南](/docs/DOCKER_PULL_GUIDE.md)
- [详细的部署指南](/docs/DOCKER_DEPLOYMENT.md)
- [问题解决方案](/docs/DOCKER_SOLUTION.md)

### Docker 管理命令

```bash
./docker-start.sh start      # 启动服务
./docker-start.sh stop       # 停止服务
./docker-start.sh restart    # 重启服务
./docker-start.sh logs       # 查看日志
./docker-start.sh status     # 查看状态
./docker-start.sh package    # 打包镜像
./docker-start.sh cleanup    # 清理资源
```

### 🚀 Docker 优势

- **一键部署**：无需手动安装依赖，自动配置环境
- **环境隔离**：避免与其他应用冲突
- **跨平台**：支持 Linux、Windows、macOS
- **易于管理**：统一的启动、停止、重启命令
- **生产就绪**：包含健康检查和自动重启
- **资源限制**：可控制内存和CPU使用
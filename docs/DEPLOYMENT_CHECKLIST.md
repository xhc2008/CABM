# Docker 镜像直接拉取部署 - 快速验证清单

## 📋 部署验证清单

在使用新的直接拉取部署方案之前，请确认以下项目：

### ✅ 系统要求
- [ ] Docker 已安装并运行
- [ ] 端口 5000 未被占用
- [ ] 具有互联网连接（用于拉取镜像）

### ✅ 部署步骤验证

#### 方式一：一键脚本部署
```bash
# Linux/macOS
curl -o deploy.sh https://raw.githubusercontent.com/leletxh/CABM/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

```powershell
# Windows PowerShell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/leletxh/CABM/main/deploy.ps1" -OutFile "deploy.ps1"
PowerShell -ExecutionPolicy Bypass -File deploy.ps1
```

#### 方式二：手动 Docker 命令
```bash
# 1. 创建工作目录和配置
mkdir cabm-app && cd cabm-app
mkdir -p data static/images/cache static/audio

# 2. 创建 .env 文件（参考 .env.example）
# 3. 运行容器
docker run -d --name cabm-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/static/images/cache:/app/static/images/cache \
  -v $(pwd)/static/audio:/app/static/audio \
  --restart unless-stopped \
  ghcr.io/leletxh/cabm:latest
```

#### 方式三：Docker Compose
```bash
# 使用提供的 docker-compose.yml
docker-compose up -d
```

### ✅ 部署后验证
- [ ] 容器成功启动：`docker ps | grep cabm-app`
- [ ] 应用可访问：打开 http://localhost:5000
- [ ] 日志无错误：`docker logs cabm-app`
- [ ] API 配置正确：能够正常聊天和生成图片

### ✅ 功能测试
- [ ] 基本对话功能
- [ ] 图片生成功能
- [ ] 角色切换功能
- [ ] 记忆系统功能（可选）
- [ ] TTS 语音功能（可选）

### 🔧 故障排除
如果遇到问题，请检查：
1. `.env` 文件中的 API 密钥是否正确
2. 网络连接是否正常
3. Docker 服务是否运行
4. 端口是否被占用
5. 查看详细日志：`docker logs -f cabm-app`

### 📚 相关文档
- [Docker 镜像直接拉取部署指南](DOCKER_PULL_GUIDE.md)
- [Docker 部署指南](DOCKER_DEPLOY_GUIDE.md)
- [Windows 部署指南](WINDOWS_DEPLOY_GUIDE.md)
- [故障排除指南](DOCKER_SOLUTION.md)

---

## 🚀 快速命令参考

### 容器管理
```bash
# 查看状态
docker ps

# 查看日志
docker logs -f cabm-app

# 重启容器
docker restart cabm-app

# 停止容器
docker stop cabm-app

# 删除容器
docker rm -f cabm-app

# 更新镜像
docker pull ghcr.io/leletxh/cabm:latest
```

### 数据管理
```bash
# 备份数据
tar -czf cabm-backup-$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzf cabm-backup-YYYYMMDD.tar.gz
```

### 系统监控
```bash
# 查看资源使用
docker stats cabm-app

# 查看端口占用
netstat -tlnp | grep 5000

# 检查磁盘空间
df -h
```

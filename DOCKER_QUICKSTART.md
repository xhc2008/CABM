# 🐳 CABM Docker 快速开始

## 🚀 5分钟部署指南

### 1. 准备环境

```bash
# 确保已安装 Docker
docker --version

# 克隆项目（如果还没有）
git clone <your-repo-url>
cd CABM
```

### 2. 配置API密钥

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，填入您的API密钥
nano .env
```

**必需配置的密钥：**
```bash
CHAT_API_KEY=sk-your-chat-api-key
TTS_SERVICE_API_KEY=sk-your-tts-api-key
IMAGE_API_KEY=sk-your-image-api-key
```

### 3. 一键部署

```bash
# 给脚本执行权限
chmod +x deploy-docker.sh

# 一键部署（推荐新手）
./deploy-docker.sh deploy --fast
```

### 4. 访问应用

打开浏览器访问：`http://localhost:5000`

## 🛠️ 常用命令速查

| 操作 | 命令 |
|------|------|
| 一键部署 | `./deploy-docker.sh deploy` |
| 查看状态 | `./deploy-docker.sh status` |
| 查看日志 | `./deploy-docker.sh logs -f` |
| 重启应用 | `./deploy-docker.sh restart` |
| 停止应用 | `./deploy-docker.sh stop` |
| 清理环境 | `./deploy-docker.sh clean` |

## 🔧 开发工作流

```bash
# 代码修改后快速更新
./deploy-docker.sh update --fast

# 调试问题
./deploy-docker.sh shell

# 查看详细日志
./deploy-docker.sh logs --tail 100
```

## 📦 发布镜像

```bash
# 设置注册表认证（Docker Hub示例）
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password

# 构建并发布
./release.sh -v 1.0.0 --push
```

## ❓ 遇到问题？

1. **端口被占用**：`./deploy-docker.sh run --port 8080`
2. **构建失败**：`./deploy-docker.sh clean && ./deploy-docker.sh build --no-cache`
3. **查看日志**：`./deploy-docker.sh logs -f`

## 📚 完整文档

详细使用说明请参考：[docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)

---

**🎉 就这么简单！您的 CABM 应用已经在容器中运行了！**

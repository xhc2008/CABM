# CABM Docker 部署指南

## 🚀 快速开始

### 方式一：一键部署（推荐新手）

```bash
git clone https://github.com/xhc2008/CABM.git
cd CABM
./deploy.sh
```

### 方式二：手动部署

```bash
# 1. 克隆项目
git clone https://github.com/xhc2008/CABM.git
cd CABM

# 2. 配置API密钥
cp .env.docker .env.docker
nano .env.docker  # 编辑并填入你的API密钥

# 3. 启动服务
./docker-start.sh start

# 4. 访问应用
# 浏览器打开: http://localhost:5000
```

### 方式三：使用预构建镜像

```bash
# 拉取最新镜像
docker pull ghcr.io/xhc2008/cabm:latest

# 使用docker-compose启动
docker-compose up -d
```

## 📋 系统要求

- **Docker**: 20.10 或更高版本
- **Docker Compose**: 2.0 或更高版本  
- **内存**: 至少 2GB 可用内存
- **存储**: 至少 1GB 可用空间
- **网络**: 需要访问API服务

## 🔧 管理命令

```bash
./docker-start.sh start      # 启动服务
./docker-start.sh stop       # 停止服务  
./docker-start.sh restart    # 重启服务
./docker-start.sh logs       # 查看实时日志
./docker-start.sh status     # 查看服务状态
./docker-start.sh shell      # 进入容器
./docker-start.sh cleanup    # 清理所有资源
./docker-start.sh package    # 打包镜像和部署文件
```

## 📝 配置说明

### 环境变量配置

编辑 `.env.docker` 文件：

```bash
# 对话API配置（必填）
CHAT_API_BASE_URL=https://api.siliconflow.cn/v1
CHAT_API_KEY=sk-your-api-key-here
CHAT_MODEL=deepseek-ai/DeepSeek-V3

# 图像生成API配置（必填）
IMAGE_API_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_API_KEY=sk-your-api-key-here
IMAGE_MODEL=Kwai-Kolors/Kolors

# 嵌入向量API配置（必填）
EMBEDDING_API_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=BAAI/bge-m3

# 选项生成API配置（必填）
OPTION_API_BASE_URL=https://api.siliconflow.cn/v1
OPTION_API_KEY=sk-your-api-key-here
OPTION_MODEL=Qwen/Qwen3-32B

# 应用配置（可选）
FLASK_PORT=5000
FLASK_DEBUG=false
```

### 端口配置

默认端口为 5000，如需修改：

1. 编辑 `.env.docker` 文件中的 `FLASK_PORT`
2. 编辑 `docker-compose.yml` 文件中的端口映射

## 🔍 故障排除

### 服务无法启动

```bash
# 查看详细日志
./docker-start.sh logs

# 检查容器状态
./docker-start.sh status

# 检查端口占用
netstat -tuln | grep 5000
```

### API密钥错误

确保在 `.env.docker` 文件中正确设置了所有API密钥：
- 前往 [硅基流动平台](https://cloud.siliconflow.cn/) 获取API密钥
- 确保API密钥格式正确（以 `sk-` 开头）
- 确保API余额充足

### 容器资源不足

```bash
# 查看Docker资源使用情况
docker stats

# 清理未使用的资源
docker system prune -f

# 增加Docker内存限制（在Docker Desktop设置中）
```

### 网络连接问题

```bash
# 测试网络连接
docker exec cabm-app curl -I https://api.siliconflow.cn

# 检查防火墙设置
sudo ufw status

# 检查DNS解析
docker exec cabm-app nslookup api.siliconflow.cn
```

## 📦 生产部署

### 使用外部数据库

编辑 `docker-compose.yml` 添加数据库服务：

```yaml
services:
  cabm:
    # ... 现有配置
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 反向代理配置

使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS 配置

使用 Let's Encrypt 证书：

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔒 安全建议

1. **API密钥安全**
   - 不要在代码中硬编码API密钥
   - 定期轮换API密钥
   - 使用环境变量或密钥管理服务

2. **网络安全**
   - 使用HTTPS
   - 配置防火墙规则
   - 限制访问源IP

3. **容器安全**
   - 定期更新镜像
   - 扫描镜像漏洞
   - 使用非root用户运行

## 🆙 更新升级

### 更新到最新版本

```bash
# 停止服务
./docker-start.sh stop

# 拉取最新代码
git pull origin main

# 重新构建并启动
./docker-start.sh build
./docker-start.sh start
```

### 使用预构建镜像更新

```bash
# 拉取最新镜像
docker pull ghcr.io/xhc2008/cabm:latest

# 重启服务
./docker-start.sh restart
```

## 📊 监控和日志

### 查看实时日志

```bash
# 查看所有日志
./docker-start.sh logs

# 查看最近100行日志
docker logs --tail 100 cabm-app

# 跟踪实时日志
docker logs -f cabm-app
```

### 性能监控

```bash
# 查看容器资源使用
docker stats cabm-app

# 查看容器详细信息
docker inspect cabm-app
```

## 🤝 获取帮助

如果遇到问题：

1. 查看 [故障排除](#-故障排除) 部分
2. 查看项目 [Issues](https://github.com/xhc2008/CABM/issues)
3. 提交新的 Issue 并提供：
   - 错误日志
   - 系统信息
   - 复现步骤

---

**祝您使用愉快！** 🎉

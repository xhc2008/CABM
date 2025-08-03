# CABM Docker 部署完整指南

## 📁 文件结构

```
CABM/
├── Dockerfile                 # Docker镜像构建文件
├── docker-compose.yml        # Docker Compose配置
├── .dockerignore             # Docker构建忽略文件
├── .env.docker               # Docker环境变量模板
├── docker-start.sh           # Docker管理脚本
├── deploy.sh                 # 一键部署脚本
├── test-docker.sh            # 本地测试脚本
├── release.sh                # 镜像发布脚本
├── DOCKER.md                 # Docker详细文档
└── .github/workflows/docker.yml  # GitHub Actions自动构建
```

## 🚀 快速开始

### 1. 一键部署（推荐新手）

```bash
git clone https://github.com/xhc2008/CABM.git
cd CABM
./deploy.sh
```

### 2. 手动部署

```bash
# 配置API密钥
cp .env.docker .env.docker
nano .env.docker

# 启动服务
./docker-start.sh start
```

### 3. 使用预构建镜像

```bash

docker pull leletxh/cabm:latest

```

## 🛠️ 脚本说明

### docker-start.sh - 主要管理脚本

```bash
./docker-start.sh start      # 启动服务
./docker-start.sh stop       # 停止服务
./docker-start.sh restart    # 重启服务
./docker-start.sh logs       # 查看日志
./docker-start.sh status     # 查看状态
./docker-start.sh shell      # 进入容器
./docker-start.sh cleanup    # 清理资源
./docker-start.sh package    # 打包镜像
```

### deploy.sh - 一键部署

自动完成环境检查、配置和部署的完整流程。

### test-docker.sh - 本地测试

```bash
./test-docker.sh build       # 构建测试镜像
./test-docker.sh run         # 运行测试容器
./test-docker.sh test        # 完整测试流程
./test-docker.sh health      # 健康检查
```

### release.sh - 镜像发布

```bash
./release.sh                 # 发布latest版本
./release.sh v1.0.0          # 发布指定版本
./release.sh v1.0.0 build    # 仅构建镜像
./release.sh latest push     # 仅推送镜像
```

## 📝 配置文件

### .env.docker - 环境变量配置

```bash
# 对话API配置
CHAT_API_BASE_URL=https://api.siliconflow.cn/v1
CHAT_API_KEY=sk-your-api-key
CHAT_MODEL=deepseek-ai/DeepSeek-V3

# 图像生成API配置
IMAGE_API_BASE_URL=https://api.siliconflow.cn/v1
IMAGE_API_KEY=sk-your-api-key
IMAGE_MODEL=Kwai-Kolors/Kolors

# 其他配置...
```

### docker-compose.yml - 服务编排

定义了CABM服务的完整配置，包括端口映射、环境变量、数据卷等。

## 🔄 开发流程

### 本地开发测试

```bash
# 1. 修改代码
# 2. 构建测试镜像
./test-docker.sh build

# 3. 运行测试
./test-docker.sh run

# 4. 查看日志
./test-docker.sh logs

# 5. 健康检查
./test-docker.sh health
```

### 发布新版本

```bash
# 1. 标记版本
git tag v1.0.0

# 2. 推送到仓库
git push origin v1.0.0

# 3. 发布镜像
./release.sh v1.0.0

# 4. 验证发布
./docker-start.sh status
```

## 🌐 多仓库支持

脚本支持同时推送到多个镜像仓库：

- **GitHub Container Registry**: `ghcr.io/xhc2008/cabm`
- **Docker Hub**: `docker.io/xhc2008/cabm`
- **阿里云镜像**: `registry.cn-hangzhou.aliyuncs.com/xhc2008/cabm`

## 🔧 自定义配置

### 修改端口

1. 编辑 `.env.docker` 中的 `FLASK_PORT`
2. 编辑 `docker-compose.yml` 中的端口映射

### 添加数据卷

编辑 `docker-compose.yml`：

```yaml
volumes:
  - ./custom-data:/app/custom-data
  - ./logs:/app/logs
```

### 环境变量覆盖

```bash
# 临时覆盖
FLASK_PORT=8080 ./docker-start.sh start

# 或编辑 .env.docker 文件
```

## 📊 监控和日志

### 查看实时日志

```bash
./docker-start.sh logs
```

### 监控资源使用

```bash
docker stats cabm-app
```

### 健康检查

```bash
curl http://localhost:5000/
```

## 🛡️ 安全建议

1. **API密钥管理**
   - 不要提交 `.env.docker` 到版本控制
   - 使用强密钥，定期轮换
   - 生产环境使用密钥管理服务

2. **网络安全**
   - 使用HTTPS反向代理
   - 配置防火墙规则
   - 限制访问IP范围

3. **容器安全**
   - 定期更新基础镜像
   - 扫描镜像漏洞
   - 使用非root用户

## 🚨 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tuln | grep 5000
   
   # 修改端口
   编辑 .env.docker 中的 FLASK_PORT
   ```

2. **API密钥错误**
   ```bash
   # 检查配置
   cat .env.docker
   
   # 测试API连接
   curl -H "Authorization: Bearer $CHAT_API_KEY" $CHAT_API_BASE_URL/models
   ```

3. **容器启动失败**
   ```bash
   # 查看详细日志
   ./docker-start.sh logs
   
   # 检查容器状态
   docker inspect cabm-app
   ```

### 日志收集

```bash
# 导出完整日志
docker logs cabm-app > cabm.log 2>&1

# 打包调试信息
tar -czf debug-info.tar.gz \
    cabm.log \
    .env.docker \
    docker-compose.yml \
    config.py
```

## 📚 参考资料

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- [CABM项目主页](https://github.com/xhc2008/CABM)
- [硅基流动API文档](https://cloud.siliconflow.cn/docs)

## 🤝 贡献指南

欢迎提交Docker相关的改进：

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 创建Pull Request

重点关注：
- Docker镜像优化
- 安全性改进
- 文档完善
- 脚本功能增强

---

**Docker让部署更简单！** 🐳

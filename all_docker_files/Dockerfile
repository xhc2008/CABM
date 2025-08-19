# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11-slim

# 构建参数
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=latest

# 添加标签信息
LABEL maintainer="xhc2008" \
      org.opencontainers.image.title="CABM" \
      org.opencontainers.image.description="Code Afflatus & Beyond Matter - AI对话应用" \
      org.opencontainers.image.url="https://github.com/xhc2008/CABM" \
      org.opencontainers.image.source="https://github.com/xhc2008/CABM" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.created="$BUILD_DATE" \
      org.opencontainers.image.revision="$VCS_REF" \
      org.opencontainers.image.licenses="GPL-3.0"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p static/images/cache \
    && mkdir -p data/history \
    && mkdir -p data/images \
    && mkdir -p data/scenes \
    && mkdir -p data/memory \
    && mkdir -p logs

# 设置文件权限
RUN chmod +x start.sh

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 启动命令
CMD ["python", "start.py", "--host", "0.0.0.0", "--port", "5000"]

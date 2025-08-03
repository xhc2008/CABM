#!/bin/bash

# CABM Docker 部署管理脚本
# 提供完整的Docker容器管理功能

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目配置
PROJECT_NAME="cabm"
IMAGE_NAME="cabm"
CONTAINER_NAME="cabm-app"
PORT="5000"

# 显示使用说明
show_usage() {
    echo -e "${BLUE}CABM Docker 部署管理脚本${NC}"
    echo ""
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo -e "${YELLOW}命令:${NC}"
    echo "  build           构建Docker镜像"
    echo "  run             运行容器"
    echo "  start           启动已停止的容器"
    echo "  stop            停止容器"
    echo "  restart         重启容器"
    echo "  logs            查看容器日志"
    echo "  status          查看容器状态"
    echo "  shell           进入容器Shell"
    echo "  clean           清理容器和镜像"
    echo "  deploy          一键部署（构建+运行）"
    echo "  update          更新部署（停止+构建+运行）"
    echo ""
    echo -e "${YELLOW}构建选项:${NC}"
    echo "  --fast          使用网络优化构建"
    echo "  --no-cache      不使用构建缓存"
    echo ""
    echo -e "${YELLOW}运行选项:${NC}"
    echo "  --port PORT     指定端口映射 (默认: 5000)"
    echo "  --env-file FILE 指定环境变量文件 (默认: .env)"
    echo "  --volume PATH   挂载额外目录"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 deploy                    # 一键部署"
    echo "  $0 build --fast              # 快速构建"
    echo "  $0 run --port 8080           # 在8080端口运行"
    echo "  $0 logs -f                   # 跟踪日志输出"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装Docker${NC}"
        exit 1
    fi
}

# 检查环境变量文件
check_env_file() {
    local env_file=${ENV_FILE:-".env"}
    if [[ ! -f "$env_file" ]]; then
        echo -e "${YELLOW}⚠️  环境变量文件 $env_file 不存在${NC}"
        echo -e "${YELLOW}   请复制 .env.example 为 $env_file 并配置API密钥${NC}"
        if [[ -f ".env.example" ]]; then
            echo -e "${BLUE}   运行: cp .env.example $env_file${NC}"
        fi
        return 1
    fi
    return 0
}

# 构建Docker镜像
build_image() {
    echo -e "${BLUE}🔨 构建Docker镜像...${NC}"
    
    local build_args=""
    local dockerfile="Dockerfile"
    
    # 解析构建选项
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fast)
                echo -e "${YELLOW}📡 使用网络优化构建${NC}"
                dockerfile="Dockerfile"
                # 创建优化的Dockerfile
                cat > Dockerfile.fast << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 配置pip使用清华镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p static/images/cache \
    && mkdir -p data/history \
    && mkdir -p data/memory \
    && mkdir -p data/scenes

# 设置启动脚本权限
RUN chmod +x start.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "start.py"]
EOF
                dockerfile="Dockerfile.fast"
                shift
                ;;
            --no-cache)
                build_args="$build_args --no-cache"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # 执行构建
    if docker build $build_args -f "$dockerfile" -t "$IMAGE_NAME:latest" .; then
        echo -e "${GREEN}✅ 镜像构建成功${NC}"
        # 清理临时文件
        [[ -f "Dockerfile.fast" ]] && rm -f "Dockerfile.fast"
    else
        echo -e "${RED}❌ 镜像构建失败${NC}"
        [[ -f "Dockerfile.fast" ]] && rm -f "Dockerfile.fast"
        exit 1
    fi
}

# 运行容器
run_container() {
    echo -e "${BLUE}🚀 启动容器...${NC}"
    
    local port=$PORT
    local env_file=".env"
    local volumes=""
    local run_args=""
    
    # 解析运行选项
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                port="$2"
                shift 2
                ;;
            --env-file)
                env_file="$2"
                shift 2
                ;;
            --volume)
                volumes="$volumes -v $2"
                shift 2
                ;;
            -d|--detach)
                run_args="$run_args -d"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # 检查端口是否被占用
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用${NC}"
        read -p "是否停止现有容器并继续？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_container
        else
            exit 1
        fi
    fi
    
    # 停止现有容器
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo -e "${YELLOW}🛑 停止现有容器...${NC}"
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    # 检查环境文件
    local env_arg=""
    if [[ -f "$env_file" ]]; then
        env_arg="--env-file $env_file"
    else
        echo -e "${YELLOW}⚠️  环境文件 $env_file 不存在，使用默认配置${NC}"
    fi
    
    # 启动容器
    local cmd="docker run $run_args --name $CONTAINER_NAME -p $port:5000 $env_arg $volumes"
    cmd="$cmd -v $(pwd)/data:/app/data"
    cmd="$cmd -v $(pwd)/static/images/cache:/app/static/images/cache"
    cmd="$cmd --restart unless-stopped"
    cmd="$cmd $IMAGE_NAME:latest"
    
    echo -e "${BLUE}执行命令: $cmd${NC}"
    
    if eval $cmd; then
        echo -e "${GREEN}✅ 容器启动成功${NC}"
        echo -e "${BLUE}🌐 访问地址: http://localhost:$port${NC}"
        
        # 如果是后台运行，显示日志跟踪命令
        if [[ "$run_args" == *"-d"* ]]; then
            echo -e "${YELLOW}📋 查看日志: docker logs -f $CONTAINER_NAME${NC}"
        fi
    else
        echo -e "${RED}❌ 容器启动失败${NC}"
        exit 1
    fi
}

# 停止容器
stop_container() {
    echo -e "${BLUE}🛑 停止容器...${NC}"
    if docker stop "$CONTAINER_NAME" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 容器已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  容器未运行或不存在${NC}"
    fi
}

# 启动容器
start_container() {
    echo -e "${BLUE}▶️  启动容器...${NC}"
    if docker start "$CONTAINER_NAME" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 容器已启动${NC}"
        echo -e "${BLUE}🌐 访问地址: http://localhost:$PORT${NC}"
    else
        echo -e "${RED}❌ 容器启动失败或不存在${NC}"
        echo -e "${YELLOW}💡 提示: 请先运行 'deploy' 命令创建容器${NC}"
        exit 1
    fi
}

# 重启容器
restart_container() {
    echo -e "${BLUE}🔄 重启容器...${NC}"
    if docker restart "$CONTAINER_NAME" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 容器已重启${NC}"
        echo -e "${BLUE}🌐 访问地址: http://localhost:$PORT${NC}"
    else
        echo -e "${RED}❌ 容器重启失败或不存在${NC}"
        exit 1
    fi
}

# 查看日志
show_logs() {
    echo -e "${BLUE}📋 查看容器日志...${NC}"
    if docker ps -a -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker logs "$@" "$CONTAINER_NAME"
    else
        echo -e "${RED}❌ 容器不存在${NC}"
        exit 1
    fi
}

# 查看状态
show_status() {
    echo -e "${BLUE}📊 容器状态:${NC}"
    if docker ps -a -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" | grep -q "$CONTAINER_NAME"; then
        docker ps -a -f name="$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
    else
        echo -e "${YELLOW}⚠️  容器不存在${NC}"
    fi
    
    # 显示镜像信息
    echo -e "\n${BLUE}📦 镜像信息:${NC}"
    if docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}" | tail -n +2 | grep -q .; then
        docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"
    else
        echo -e "${YELLOW}⚠️  镜像不存在${NC}"
    fi
}

# 进入容器Shell
enter_shell() {
    echo -e "${BLUE}🐚 进入容器Shell...${NC}"
    if docker exec -it "$CONTAINER_NAME" /bin/bash 2>/dev/null || docker exec -it "$CONTAINER_NAME" /bin/sh; then
        echo -e "${GREEN}✅ 已退出容器Shell${NC}"
    else
        echo -e "${RED}❌ 无法进入容器Shell，容器可能未运行${NC}"
        exit 1
    fi
}

# 清理容器和镜像
clean_all() {
    echo -e "${BLUE}🧹 清理容器和镜像...${NC}"
    
    # 停止并删除容器
    if docker ps -a -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo -e "${YELLOW}🗑️  删除容器 $CONTAINER_NAME...${NC}"
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    fi
    
    # 删除镜像
    if docker images -q "$IMAGE_NAME" | grep -q .; then
        echo -e "${YELLOW}🗑️  删除镜像 $IMAGE_NAME...${NC}"
        docker rmi "$IMAGE_NAME:latest" >/dev/null 2>&1 || true
    fi
    
    # 清理悬空镜像
    echo -e "${YELLOW}🗑️  清理悬空镜像...${NC}"
    docker image prune -f >/dev/null 2>&1 || true
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 一键部署
deploy() {
    echo -e "${BLUE}🚀 开始一键部署...${NC}"
    
    # 检查环境
    check_docker
    
    # 构建镜像
    build_image "$@"
    
    # 运行容器
    run_container -d "$@"
    
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo -e "${BLUE}🌐 访问地址: http://localhost:$PORT${NC}"
    echo -e "${YELLOW}📋 查看日志: $0 logs -f${NC}"
}

# 更新部署
update_deploy() {
    echo -e "${BLUE}🔄 开始更新部署...${NC}"
    
    # 检查环境
    check_docker
    
    # 停止现有容器
    stop_container
    
    # 构建新镜像
    build_image "$@"
    
    # 运行新容器
    run_container -d "$@"
    
    echo -e "${GREEN}🎉 更新完成！${NC}"
    echo -e "${BLUE}🌐 访问地址: http://localhost:$PORT${NC}"
}

# 主函数
main() {
    # 检查参数
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    # 解析命令
    case $1 in
        build)
            check_docker
            shift
            build_image "$@"
            ;;
        run)
            check_docker
            shift
            run_container "$@"
            ;;
        start)
            check_docker
            start_container
            ;;
        stop)
            check_docker
            stop_container
            ;;
        restart)
            check_docker
            restart_container
            ;;
        logs)
            check_docker
            shift
            show_logs "$@"
            ;;
        status)
            check_docker
            show_status
            ;;
        shell)
            check_docker
            enter_shell
            ;;
        clean)
            check_docker
            clean_all
            ;;
        deploy)
            shift
            deploy "$@"
            ;;
        update)
            shift
            update_deploy "$@"
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

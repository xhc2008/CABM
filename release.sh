#!/bin/bash

# CABM Docker 镜像发布脚本
# 支持多架构构建和多注册表发布

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目信息
PROJECT_NAME="cabm"
IMAGE_NAME="cabm"
DEFAULT_VERSION="latest"

# 支持的注册表
REGISTRIES=(
    "docker.io"           # Docker Hub
)

# 显示使用说明
show_usage() {
    echo -e "${BLUE}CABM Docker 镜像发布脚本${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo -e "${YELLOW}选项:${NC}"
    echo "  -v, --version VERSION    指定镜像版本 (默认: latest)"
    echo "  -r, --registry REGISTRY  指定注册表 (默认: docker.io)"
    echo "  -p, --platform PLATFORM  指定平台 (默认: linux/amd64,linux/arm64)"
    echo "  --push                   构建并推送到注册表"
    echo "  --no-latest              不标记为latest版本"
    echo "  --dry-run               只显示将要执行的命令"
    echo ""
    echo -e "${YELLOW}支持的注册表:${NC}"
    for registry in "${REGISTRIES[@]}"; do
        echo "  - $registry"
    done
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 --push                           # 发布到Docker Hub"
    echo "  $0 -v 1.0.0 --push                 # 发布特定版本"
    echo "  $0 -p linux/amd64 --push           # 只构建AMD64版本"
}

# 检查必要工具
check_requirements() {
    echo -e "${BLUE}🔍 检查构建环境...${NC}"
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        exit 1
    fi
    
    # 检查buildx
    if ! docker buildx version &> /dev/null; then
        echo -e "${RED}❌ Docker Buildx 未安装或启用${NC}"
        echo -e "${YELLOW}💡 运行: docker buildx install${NC}"
        exit 1
    fi
    
    # 创建或使用buildx构建器
    if ! docker buildx inspect multiarch &> /dev/null; then
        echo -e "${YELLOW}📦 创建多架构构建器...${NC}"
        docker buildx create --name multiarch --driver docker-container --use
        docker buildx inspect --bootstrap
    else
        docker buildx use multiarch
    fi
    
    echo -e "${GREEN}✅ 构建环境就绪${NC}"
}

# 登录注册表
login_registries() {
    local registries=("$@")
    
    for registry in "${registries[@]}"; do
        echo -e "${BLUE}🔐 登录到 $registry...${NC}"
        
        case $registry in
            "docker.io")
                if [[ -z "$DOCKER_USERNAME" || -z "$DOCKER_PASSWORD" ]]; then
                    echo -e "${YELLOW}⚠️  请设置 DOCKER_USERNAME 和 DOCKER_PASSWORD 环境变量${NC}"
                    read -p "Docker Hub 用户名: " DOCKER_USERNAME
                    read -s -p "Docker Hub 密码: " DOCKER_PASSWORD
                    echo
                fi
                echo "$DOCKER_PASSWORD" | docker login docker.io -u "$DOCKER_USERNAME" --password-stdin
                ;;
        esac
        
        echo -e "${GREEN}✅ 已登录到 $registry${NC}"
    done
}

# 生成镜像标签
generate_tags() {
    local version=$1
    local registries=("${@:2}")
    local tags=()
    
    for registry in "${registries[@]}"; do
        case $registry in
            "docker.io")
                tags+=("$DOCKER_USERNAME/$IMAGE_NAME:$version")
                if [[ "$ADD_LATEST" == "true" && "$version" != "latest" ]]; then
                    tags+=("$DOCKER_USERNAME/$IMAGE_NAME:latest")
                fi
                ;;
        esac
    done
    
    printf '%s\n' "${tags[@]}"
}

# 构建并推送镜像
build_and_push() {
    local version=$1
    local platforms=$2
    local push=$3
    local registries=("${@:4}")
    
    echo -e "${BLUE}🔨 构建多架构镜像...${NC}"
    echo -e "${YELLOW}版本: $version${NC}"
    echo -e "${YELLOW}平台: $platforms${NC}"
    echo -e "${YELLOW}注册表: ${registries[*]}${NC}"
    
    # 生成所有标签
    local tags=($(generate_tags "$version" "${registries[@]}"))
    
    if [[ ${#tags[@]} -eq 0 ]]; then
        echo -e "${RED}❌ 没有生成任何标签${NC}"
        exit 1
    fi
    
    # 构建标签参数
    local tag_args=""
    for tag in "${tags[@]}"; do
        tag_args="$tag_args -t $tag"
    done
    
    # 构建命令
    local build_cmd="docker buildx build"
    build_cmd="$build_cmd --platform $platforms"
    build_cmd="$build_cmd $tag_args"
    build_cmd="$build_cmd --build-arg VERSION=$version"
    build_cmd="$build_cmd --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    build_cmd="$build_cmd --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    
    if [[ "$push" == "true" ]]; then
        build_cmd="$build_cmd --push"
    else
        build_cmd="$build_cmd --load"
    fi
    
    build_cmd="$build_cmd ."
    
    # 执行构建
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}🏃 预演模式 - 将要执行的命令:${NC}"
        echo "$build_cmd"
        return 0
    fi
    
    echo -e "${BLUE}执行: $build_cmd${NC}"
    
    if eval $build_cmd; then
        echo -e "${GREEN}✅ 镜像构建成功${NC}"
        
        if [[ "$push" == "true" ]]; then
            echo -e "${GREEN}🚀 镜像已推送到注册表${NC}"
            for tag in "${tags[@]}"; do
                echo -e "${BLUE}  📦 $tag${NC}"
            done
        else
            echo -e "${YELLOW}💡 使用 --push 参数推送到注册表${NC}"
        fi
    else
        echo -e "${RED}❌ 镜像构建失败${NC}"
        exit 1
    fi
}

# 主函数
main() {
    local version="$DEFAULT_VERSION"
    local platforms="linux/amd64,linux/arm64"
    local push="false"
    local target_registries=()
    local add_latest="true"
    local dry_run="false"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--version)
                version="$2"
                shift 2
                ;;
            -r|--registry)
                target_registries+=("$2")
                shift 2
                ;;
            -p|--platform)
                platforms="$2"
                shift 2
                ;;
            --push)
                push="true"
                shift
                ;;
            --no-latest)
                add_latest="false"
                shift
                ;;
            --dry-run)
                dry_run="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知参数: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 如果没有指定注册表，使用所有注册表
    if [[ ${#target_registries[@]} -eq 0 ]]; then
        target_registries=("${REGISTRIES[@]}")
    fi
    
    # 设置全局变量
    ADD_LATEST="$add_latest"
    DRY_RUN="$dry_run"
    
    # 验证注册表
    for registry in "${target_registries[@]}"; do
        if [[ ! " ${REGISTRIES[@]} " =~ " ${registry} " ]]; then
            echo -e "${RED}❌ 不支持的注册表: $registry${NC}"
            exit 1
        fi
    done
    
    echo -e "${BLUE}🚀 CABM 镜像发布开始${NC}"
    echo -e "${YELLOW}版本: $version${NC}"
    echo -e "${YELLOW}平台: $platforms${NC}"
    echo -e "${YELLOW}推送: $push${NC}"
    
    # 检查环境
    check_requirements
    
    # 登录注册表
    if [[ "$push" == "true" && "$dry_run" == "false" ]]; then
        login_registries "${target_registries[@]}"
    fi
    
    # 构建并推送
    build_and_push "$version" "$platforms" "$push" "${target_registries[@]}"
    
    echo -e "${GREEN}🎉 发布完成！${NC}"
}

# 运行主函数
main "$@"
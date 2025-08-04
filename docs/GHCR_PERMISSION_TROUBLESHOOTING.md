# GitHub Container Registry 权限问题故障排除

## 问题描述
当使用 GitHub Actions 推送 Docker 镜像到 GitHub Container Registry (GHCR) 时，可能会遇到以下错误：

```
ERROR: failed to build: failed to solve: failed to push ghcr.io/用户名/镜像名:标签: denied: installation not allowed to Write organization package
```

## 解决方案

### 1. 检查仓库权限设置

确保 GitHub Actions 有足够的权限推送到 GHCR：

1. 进入你的 GitHub 仓库
2. 点击 **Settings** -> **Actions** -> **General**
3. 在 **Workflow permissions** 部分，确保选择了：
   - **Read and write permissions**
   - 勾选 **Allow GitHub Actions to create and approve pull requests**

### 2. 检查包权限设置

如果你的仓库属于组织：

1. 进入组织设置页面
2. 点击 **Settings** -> **Packages**
3. 确保允许从私有仓库发布包
4. 检查包的访问权限设置

### 3. 使用个人访问令牌 (PAT)

如果上述方法不工作，可以创建个人访问令牌：

1. 进入 GitHub **Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**
2. 创建新令牌，权限包括：
   - `write:packages`
   - `read:packages`
   - `delete:packages` (可选)
3. 将令牌添加到仓库的 Secrets 中，名称为 `GHCR_TOKEN`
4. 修改工作流文件，使用新的令牌：

```yaml
- name: Log in to GitHub Container Registry
  if: ${{ inputs.push_to_registry }}
  uses: docker/login-action@v3
  with:
    registry: ${{ env.GHCR_REGISTRY }}
    username: ${{ github.repository_owner }}
    password: ${{ secrets.GHCR_TOKEN }}  # 使用自定义令牌
```

### 4. 检查镜像命名

确保镜像名称格式正确：
- 格式：`ghcr.io/用户名或组织名/镜像名:标签`
- 用户名必须与实际的仓库所有者匹配

### 5. 验证权限配置

确保工作流文件包含正确的权限配置：

```yaml
jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write
```

## 测试步骤

1. 修复权限设置后，重新运行 GitHub Actions 工作流
2. 检查构建日志中的认证步骤
3. 验证镜像是否成功推送到 GHCR

## 备用方案

如果 GHCR 仍然有问题，可以考虑：

1. 使用 Docker Hub 作为替代镜像仓库
2. 使用其他容器镜像仓库服务
3. 手动构建和推送镜像

## 相关链接

- [GitHub Packages 文档](https://docs.github.com/en/packages)
- [GitHub Actions 权限配置](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Docker Login Action](https://github.com/docker/login-action)

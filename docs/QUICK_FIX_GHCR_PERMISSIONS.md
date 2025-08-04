# GitHub Actions 权限问题快速修复指南

## 🚨 "Resource not accessible by integration" 错误修复

### 步骤 1: 检查仓库设置
1. 进入仓库 -> **Settings** -> **Actions** -> **General**
2. 在 **Workflow permissions** 部分：
   - 选择 **Read and write permissions**
   - 勾选 **Allow GitHub Actions to create and approve pull requests**

### 步骤 2: 验证工作流权限
确保工作流文件包含以下权限：

```yaml
permissions:
  contents: read
  packages: write
  id-token: write
  actions: read
  security-events: write
  attestations: write
```

### 步骤 3: 创建个人访问令牌 (备用方案)

如果上述方法不工作：

1. **创建 PAT**：
   - GitHub **Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**
   - 点击 **Generate new token (classic)**
   - 选择权限：
     - ✅ `write:packages`
     - ✅ `read:packages` 
     - ✅ `delete:packages` (可选)

2. **添加到仓库 Secrets**：
   - 仓库 **Settings** -> **Secrets and variables** -> **Actions**
   - 点击 **New repository secret**
   - Name: `GHCR_TOKEN`
   - Secret: 粘贴刚创建的 PAT

3. **使用备用工作流**：
   - 文件: `.github/workflows/docker-deploy-pat.yml`
   - 这个文件使用 PAT 而不是默认的 GITHUB_TOKEN

### 步骤 4: 测试
重新运行 GitHub Actions 工作流。

## 📋 检查清单

- [ ] 仓库 Actions 权限设置为 "Read and write permissions"
- [ ] 工作流文件包含正确的 permissions 配置
- [ ] 如果需要，创建了 GHCR_TOKEN secret
- [ ] 镜像名称格式正确：`ghcr.io/用户名/仓库名:标签`

## 🔍 调试技巧

1. **查看 Actions 日志**：
   - 检查登录步骤是否成功
   - 查看具体的错误信息

2. **验证镜像名称**：
   - 确保全部小写
   - 格式：`ghcr.io/leletxh/cabm:latest`

3. **检查网络和DNS**：
   - GitHub Actions runner 能否访问 ghcr.io

## 📞 还需要帮助？

如果问题仍然存在：
1. 检查 GitHub 状态页面
2. 尝试使用不同的标签
3. 考虑使用 Docker Hub 作为替代方案

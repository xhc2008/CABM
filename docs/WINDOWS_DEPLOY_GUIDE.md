# CABM Windows 部署指南

本指南介绍如何在Windows系统上部署和管理CABM应用。

## 🚀 快速开始

### 方式一：一键启动（推荐）
双击运行 `start-windows.bat`，脚本将自动：
- 优先使用Conda部署（推荐）
- 检查并安装Python环境
- 自动配置依赖
- 启动应用
- 备用Docker部署

### 方式二：Conda专用启动
双击运行 `start-conda.bat`，专门使用Conda环境：
- 创建独立的`.conda`环境
- 安装所需依赖
- 直接启动应用

### 方式三：图形化管理界面
运行PowerShell命令：
```powershell
.\cabm-gui.ps1
```
提供直观的图形界面来管理应用，支持Conda和Docker两种方式。

### 方式四：完整安装向导
运行PowerShell命令：
```powershell
.\install-windows.ps1
```
自动检查并安装所有依赖，配置环境。

## 📋 系统要求

### 基本要求
- Windows 10/11
- 4GB+ 内存
- 5GB+ 可用磁盘空间

### 推荐环境（Conda）
- Miniconda 或 Anaconda
- Python 3.8+ （通过Conda管理）

### 备用环境（Docker）
- Docker Desktop
- 管理员权限（安装时需要）

## 🛠 管理方式

### Conda方式（推荐）

**优势：**
- 轻量级，启动快速
- 便于调试和开发
- 依赖管理简单
- 适合个人使用

**环境结构：**
```
项目目录/
├── .conda/          # 独立Python环境
├── data/            # 应用数据（持久化）
├── static/          # 静态文件
├── .env            # 配置文件
└── app.py          # 主程序
```

**常用命令：**
```bash
# 启动应用
conda run -p ".conda" python app.py

# 更新依赖
conda run -p ".conda" pip install -r requirements.txt --upgrade

# 进入环境
conda activate ".\.conda"

# 查看已安装包
conda run -p ".conda" pip list

# 删除环境
rmdir /s ".conda"
```

### Docker方式（极端情况）

**使用场景：**
- Conda安装失败
- 需要完全隔离的环境
- 生产部署

**PowerShell脚本 (deploy-docker.ps1)：**
```powershell
# 一键部署
.\deploy-docker.ps1 deploy

# 快速构建（使用国内镜像源）
.\deploy-docker.ps1 build -Fast

# 运行在不同端口
.\deploy-docker.ps1 run -Port 8080

# 查看实时日志
.\deploy-docker.ps1 logs -Follow

# 查看状态
.\deploy-docker.ps1 status
```

### 批处理脚本 (deploy-docker.bat)

**基本用法：**
```cmd
# 一键部署
deploy-docker.bat deploy

# 快速构建
deploy-docker.bat build --fast

# 查看日志
deploy-docker.bat logs --follow
```

## ⚙️ 配置说明

### 环境变量文件 (.env)

创建 `.env` 文件并配置以下参数：

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 应用配置
APP_HOST=127.0.0.1
APP_PORT=5000
DEBUG=false

# 日志配置
LOG_LEVEL=INFO
```

### 端口配置

**Conda方式：**
- 默认端口：`5000`
- 修改方式：编辑 `.env` 文件中的 `APP_PORT`

**Docker方式：**
- 默认端口：`5000`
- 修改方式：`.\deploy-docker.ps1 run -Port 8080`

### 数据持久化

**Conda方式：**
自动创建以下目录：
- `data/history/` - 对话历史
- `data/memory/` - 记忆数据
- `data/scenes/` - 场景配置
- `static/images/cache/` - 图片缓存

**Docker方式：**
以下目录会自动挂载到容器：
- `data/` - 应用数据
- `static/images/cache/` - 图片缓存

## 🔧 故障排除

### Conda相关问题

**问题1：Conda未安装**
```
解决方案：
1. 下载 Miniconda: https://docs.conda.io/en/latest/miniconda.html
2. 下载 Anaconda: https://www.anaconda.com/products/distribution
3. 安装并重启命令行
```

**问题2：环境创建失败**
```
解决方案：
1. 检查磁盘空间是否足够
2. 确保网络连接正常
3. 尝试手动创建：conda create -p ".conda" python=3.11 -y
```

**问题3：依赖安装失败**
```
解决方案：
1. 检查网络连接
2. 尝试使用国内镜像源：
   conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
   conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
3. 手动安装：conda run -p ".conda" pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

**问题4：应用启动失败**
```
解决方案：
1. 检查 .env 文件是否存在和配置正确
2. 确认API密钥是否有效
3. 查看错误日志信息
4. 尝试手动启动：conda run -p ".conda" python app.py
```

### Docker相关问题

**问题1：Docker未安装**
```
解决方案：
1. 下载 Docker Desktop: https://www.docker.com/products/docker-desktop/
2. 安装并重启计算机
3. 启动Docker Desktop
```

**问题2：Docker未启动**
```
解决方案：
1. 手动启动Docker Desktop
2. 或运行: start-windows.bat
```

**问题3：端口被占用**
```
解决方案：
1. Conda方式：修改 .env 文件中的 APP_PORT
2. Docker方式：.\deploy-docker.ps1 run -Port 8080
3. 或停止占用进程: netstat -ano | findstr :5000
```

### 权限问题

**问题：无管理员权限**
```
解决方案：
1. 右键点击PowerShell，选择"以管理员身份运行"
2. 或右键点击批处理文件，选择"以管理员身份运行"
```

### 网络问题

**问题：镜像下载缓慢**
```
解决方案：
1. 使用快速构建: .\deploy-docker.ps1 build -Fast
2. 配置Docker镜像源
```

### 应用无法访问

**检查步骤：**
1. 确认容器运行状态：`.\deploy-docker.ps1 status`
2. 查看应用日志：`.\deploy-docker.ps1 logs`
3. 检查防火墙设置
4. 尝试重启：`.\deploy-docker.ps1 restart`

## 📊 监控和日志

### 查看容器状态
```powershell
.\deploy-docker.ps1 status
```

### 查看实时日志
```powershell
.\deploy-docker.ps1 logs -Follow
```

### 进入容器调试
```powershell
.\deploy-docker.ps1 shell
```

## 🔄 更新和维护

### 更新应用
```powershell
# 停止 -> 重新构建 -> 启动
.\deploy-docker.ps1 update
```

### 备份数据
```powershell
# 备份data目录
Copy-Item -Recurse data data_backup_$(Get-Date -Format "yyyyMMdd")
```

### 清理旧数据
```powershell
# 清理容器和镜像
.\deploy-docker.ps1 clean

# 清理Docker系统
docker system prune -a
```

## 📱 快捷方式

### 创建桌面快捷方式

**启动应用：**
1. 右键桌面 -> 新建 -> 快捷方式
2. 目标：`"C:\Windows\System32\cmd.exe" /c "cd /d E:\try\CABM && start-windows.bat"`
3. 名称：`CABM启动`

**图形管理器：**
1. 右键桌面 -> 新建 -> 快捷方式  
2. 目标：`"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -File "E:\try\CABM\cabm-gui.ps1"`
3. 名称：`CABM管理器`

## 🆘 获取帮助

### 脚本帮助
```powershell
.\deploy-docker.ps1 help
.\install-windows.ps1 -?
```

### 系统信息
```powershell
# 检查Docker版本
docker --version

# 检查系统信息  
systeminfo | findstr /C:"OS Name" /C:"OS Version"

# 检查端口占用
netstat -ano | findstr :5000
```

### 常用链接
- [Docker Desktop下载](https://www.docker.com/products/docker-desktop/)
- [CABM项目地址](https://github.com/xhc2008/CABM)
- [PowerShell文档](https://docs.microsoft.com/powershell/)

## 📝 注意事项

1. **首次运行**需要管理员权限安装Docker
2. **防火墙**可能需要允许Docker和应用端口
3. **杀毒软件**可能误报，请添加信任
4. **中文路径**可能导致问题，建议使用英文路径
5. **定期更新**Docker和应用以获得最佳体验

---

如有问题，请查看日志文件或联系技术支持。

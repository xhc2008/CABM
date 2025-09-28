## Node.js 安装与启动（带UI界面）
### 1. 安装 Node.js 依赖

请确保已安装 Node.js（推荐 18.x 及以上），然后在项目根目录下运行：

```bash
npm install
```

### 2. 启动带UI的 Electron 应用

在命令行中运行：

```bash
npm run electron:start
```

或直接运行 Electron 主程序：

```bash
node electron/main.js
```

启动后会自动弹出带有UI的主界面，后端服务会自动启动并在 http://localhost:5000 提供 API。

> 如果端口 5000 已被占用，Electron 会自动连接已运行的服务。

### 3. 关闭应用

关闭所有窗口时，系统会自动通知后端退出并关闭服务。

---
```cmd
start.bat
```
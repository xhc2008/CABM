// main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn, spawnSync } = require('child_process');
const net = require('net');

let mainWindow;
let serverProcess;

// 检查端口是否可用
function isPortInUse(port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();

    socket.connect({ port: port, host: 'localhost' }, () => {
      socket.destroy();
      resolve(true);
    });

    socket.on('error', () => {
      resolve(false);
    });
  });
}

// 等待端口开放
function waitForPort(port, interval = 500) {
  return new Promise((resolve) => {
    const check = async () => {
      const inUse = await isPortInUse(port);
      if (inUse) {
        resolve();
      } else {
        setTimeout(check, interval);
      }
    };
    check();
  });
}

// 启动本地服务
function startServer() {
  // 你可以换成 'npm', ['start'] 或其他命令
  serverProcess = spawn('node', ['server.js'], {
    stdio: 'inherit', // 显示服务输出到控制台
    shell: true,
  });

  serverProcess.on('close', (code) => {
    console.log(`服务进程已退出，状态码: ${code}`);
    if (mainWindow) {
      mainWindow.webContents.send('server-stopped', code);
    }
  });

  return serverProcess;
}

// 创建 Electron 主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // 先不直接加载，等待服务就绪
  loadAppWhenReady();
}

async function loadAppWhenReady() {
  let shouldStartServer = false;

  // 检查 5000 端口是否已被占用
  const inUse = await isPortInUse(5000);
  if (!inUse) {
    console.log('端口 5000 未使用，正在启动本地服务...');
    startServer();
    shouldStartServer = true;
  } else {
    console.log('检测到服务已在运行（端口 5000）');
  }

  // 等待服务可用
  try {
    await waitForPort(5000);
    console.log('服务已就绪，加载页面...');
    mainWindow.loadURL('http://localhost:5000');
  } catch (err) {
    console.error('等待服务超时', err);
    mainWindow.webContents.send('error', '服务启动失败或超时');
  }
}

// Electron 初始化完成
app.whenReady().then(() => {
  const { Menu } = require('electron');
  Menu.setApplicationMenu(null);
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// 关闭所有窗口时退出
const http = require('http');

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // 向后端发送退出请求
    const req = http.request({
      hostname: 'localhost',
      port: 5000,
      path: '/api/exit',
      method: 'POST',
    }, (res) => {
      console.log('退出请求已发送，状态码:', res.statusCode);
      app.quit();
    });
  }
});

// 可选：处理进程退出
app.on('before-quit', () => {
  if (serverProcess && serverProcess.kill) {
    serverProcess.kill();
    console.log('已终止本地服务');
  }
});
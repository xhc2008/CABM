# -----------------------------------------------------------------------------
# Script Name: windows一键部署.ps1
# Description: 一键部署：安装 Conda（如无），创建 CABM 环境（Python 3.11），pip install requirements.txt，复制 .env 文件
# Author: leletxh (updated by assistant)
# Version: 2.0
# Date: 2025-07-31
# Usage: 双击或右键“使用 PowerShell 运行”
# Requirements: PowerShell 5.1+
# Notes: 脚本将部署到当前目录，程序也在此运行
# -----------------------------------------------------------------------------

#requires -Version 5.1

# --------------------------- 初始化设置 ----------------------------------------
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# 获取脚本所在目录（部署根目录）
$ScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
if (-not $ScriptRoot) { $ScriptRoot = (Get-Location).Path }

# 切换到脚本目录
Set-Location $ScriptRoot
Write-Host "📌 当前工作目录: $ScriptRoot" -ForegroundColor Cyan

# 日志函数
function Write-Log {
    param([string]$Message)
    $Time = Get-Date -Format "HH:mm:ss"
    Write-Host "[$Time] $Message" -ForegroundColor Yellow
}

# --------------------------- 检查 Conda 是否已安装 -----------------------------
function Test-CondaInstalled {
    return $null -ne (Get-Command conda -ErrorAction SilentlyContinue)
}

# --------------------------- 安装 Miniconda -----------------------------------
function Install-Miniconda {
    Write-Log "未检测到 conda，开始安装 Miniconda..."

    $Url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    $Installer = ".\miniconda.exe"

    try {
        Write-Log "📥 下载 Miniconda 安装包..."
        Invoke-WebRequest -Uri $Url -OutFile $Installer -UseBasicParsing

        Write-Log "🔧 静默安装中，请稍候..."
        Start-Process -FilePath $Installer -ArgumentList "/S", "/AddToPath=0", "/RegisterPython=0" -Wait

        Remove-Item $Installer -Force
        Write-Log "✅ Miniconda 安装完成。"
    }
    catch {
        Write-Error "安装失败: $_"
        exit 1
    }
}

# --------------------------- 创建 Conda 环境（Python 3.11 + pip install）--------
function Create-CondaEnvironment {
    $RequirementsFile = ".\requirements.txt"
    if (-not (Test-Path $RequirementsFile)) {
        Write-Error "❌ 错误：未找到 requirements.txt 文件，请确保它与脚本在同一目录！"
        exit 1
    }

    Write-Log "📦 开始创建 Conda 环境：CABM (Python 3.11)"
    try {
        # 构建 conda 命令调用方式
        $CondaCommand = if (Test-CondaInstalled) { "conda" } else {
            $CondaBat = "$env:LOCALAPPDATA\Miniconda3\condabin\conda.bat"
            if (Test-Path $CondaBat) {
                "cmd /c `"$CondaBat`""
            } else {
                Write-Error "❌ conda 命令不可用，且未找到安装路径。"
                exit 1
            }
        }

        # 1. 创建仅含 Python 3.11 的环境
        Write-Log "🔄 创建 Conda 环境 CABM (Python 3.11)..."
        Invoke-Expression "$CondaCommand create --name CABM python=3.11 -y"
        if ($LASTEXITCODE -ne 0) { throw "创建环境失败" }

        # 2. 激活环境并安装依赖
        Write-Log "🔄 使用 pip 安装依赖包..."
        $PipCommand = "$CondaCommand activate CABM && pip install -r `"$RequirementsFile`""
        Invoke-Expression $PipCommand
        if ($LASTEXITCODE -ne 0) { throw "pip 安装依赖失败" }

        Write-Log "✅ Conda 环境 'CABM' 创建成功，并已安装 requirements.txt 中的依赖！"
    }
    catch {
        Write-Error "❌ 创建环境或安装依赖失败: $_"
        exit 1
    }
}

# --------------------------- 复制 .env.example 为 .env -------------------------
function Copy-DotEnvFile {
    $Source = ".\.env.example"
    $Target = ".\.env"

    if (Test-Path $Source) {
        if (Test-Path $Target) {
            Write-Log "⚠️  .env 文件已存在，跳过复制"
        }
        else {
            Copy-Item -Path $Source -Destination $Target -Force
            Write-Log "✅ 已生成配置文件: .env"
        }
    }
    else {
        Write-Warning "⚠️  未找到 .env.example，跳过生成 .env"
    }
}

# --------------------------- 主流程 ------------------------------------------
try {
    Write-Host "========== 🔧 Windows 一键部署（v2.0） ==========" -ForegroundColor Green

    # 1. 检查并安装 Conda
    if (Test-CondaInstalled) {
        Write-Log "✅ Conda 已安装"
    }
    else {
        Install-Miniconda
        # 重新加载环境变量或检测新安装的 conda
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }

    # 2. 创建 Conda 环境并安装依赖
    Create-CondaEnvironment

    # 3. 复制 .env 文件
    Copy-DotEnvFile

    # ✅ 完成
    Write-Host "🎉 一键部署全部完成！" -ForegroundColor Green
    Write-Host "💡 使用方式：" -ForegroundColor White
    Write-Host "   conda activate CABM" -ForegroundColor Cyan
    Write-Host "   python your_app.py 或 .\start.bat" -ForegroundColor Cyan
}
catch {
    Write-Error "💥 部署失败: $_"
    Write-Host "请检查网络、权限、requirements.txt 是否存在，或杀毒软件是否拦截。" -ForegroundColor Red
    exit 1
}

Write-Host "🔚 脚本执行结束。" -ForegroundColor Cyan
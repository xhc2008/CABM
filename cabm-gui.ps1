#Requires -Version 5.1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# 全局变量
$script:form = $null
$script:statusLabel = $null
$script:logTextBox = $null
$script:progressBar = $null

# 创建主窗口
function New-MainForm {
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "CABM - AI对话应用管理器"
    $form.Size = New-Object System.Drawing.Size(600, 500)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedSingle"
    $form.MaximizeBox = $false
    $form.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon("$PSScriptRoot\static\images\default.svg")
    
    # 标题
    $titleLabel = New-Object System.Windows.Forms.Label
    $titleLabel.Text = "CABM - Code Afflatus & Beyond Matter"
    $titleLabel.Font = New-Object System.Drawing.Font("Microsoft YaHei", 14, [System.Drawing.FontStyle]::Bold)
    $titleLabel.ForeColor = [System.Drawing.Color]::DarkBlue
    $titleLabel.Location = New-Object System.Drawing.Point(20, 20)
    $titleLabel.Size = New-Object System.Drawing.Size(560, 30)
    $titleLabel.TextAlign = "TopCenter"
    $form.Controls.Add($titleLabel)
    
    # 状态标签
    $script:statusLabel = New-Object System.Windows.Forms.Label
    $script:statusLabel.Text = "就绪"
    $script:statusLabel.Location = New-Object System.Drawing.Point(20, 60)
    $script:statusLabel.Size = New-Object System.Drawing.Size(560, 20)
    $script:statusLabel.ForeColor = [System.Drawing.Color]::Green
    $form.Controls.Add($script:statusLabel)
    
    # 按钮面板
    $buttonPanel = New-Object System.Windows.Forms.Panel
    $buttonPanel.Location = New-Object System.Drawing.Point(20, 90)
    $buttonPanel.Size = New-Object System.Drawing.Size(560, 120)
    $form.Controls.Add($buttonPanel)
    
    # 一键启动按钮
    $startButton = New-Object System.Windows.Forms.Button
    $startButton.Text = "🚀 一键启动"
    $startButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 12, [System.Drawing.FontStyle]::Bold)
    $startButton.Location = New-Object System.Drawing.Point(10, 10)
    $startButton.Size = New-Object System.Drawing.Size(120, 40)
    $startButton.BackColor = [System.Drawing.Color]::LightGreen
    $startButton.Add_Click({ Start-Application })
    $buttonPanel.Controls.Add($startButton)
    
    # 停止按钮
    $stopButton = New-Object System.Windows.Forms.Button
    $stopButton.Text = "🛑 停止"
    $stopButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 10)
    $stopButton.Location = New-Object System.Drawing.Point(140, 10)
    $stopButton.Size = New-Object System.Drawing.Size(80, 40)
    $stopButton.BackColor = [System.Drawing.Color]::LightCoral
    $stopButton.Add_Click({ Stop-Application })
    $buttonPanel.Controls.Add($stopButton)
    
    # 重启按钮
    $restartButton = New-Object System.Windows.Forms.Button
    $restartButton.Text = "🔄 重启"
    $restartButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 10)
    $restartButton.Location = New-Object System.Drawing.Point(230, 10)
    $restartButton.Size = New-Object System.Drawing.Size(80, 40)
    $restartButton.BackColor = [System.Drawing.Color]::LightBlue
    $restartButton.Add_Click({ Restart-Application })
    $buttonPanel.Controls.Add($restartButton)
    
    # 状态查询按钮
    $statusButton = New-Object System.Windows.Forms.Button
    $statusButton.Text = "📊 状态"
    $statusButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 10)
    $statusButton.Location = New-Object System.Drawing.Point(320, 10)
    $statusButton.Size = New-Object System.Drawing.Size(80, 40)
    $statusButton.BackColor = [System.Drawing.Color]::LightYellow
    $statusButton.Add_Click({ Get-ApplicationStatus })
    $buttonPanel.Controls.Add($statusButton)
    
    # 打开应用按钮
    $openButton = New-Object System.Windows.Forms.Button
    $openButton.Text = "🌐 打开"
    $openButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 10)
    $openButton.Location = New-Object System.Drawing.Point(410, 10)
    $openButton.Size = New-Object System.Drawing.Size(80, 40)
    $openButton.BackColor = [System.Drawing.Color]::LightCyan
    $openButton.Add_Click({ Open-Application })
    $buttonPanel.Controls.Add($openButton)
    
    # 配置按钮
    $configButton = New-Object System.Windows.Forms.Button
    $configButton.Text = "⚙️ 配置"
    $configButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 9)
    $configButton.Location = New-Object System.Drawing.Point(10, 60)
    $configButton.Size = New-Object System.Drawing.Size(80, 30)
    $configButton.Add_Click({ Edit-Configuration })
    $buttonPanel.Controls.Add($configButton)
    
    # 日志按钮
    $logsButton = New-Object System.Windows.Forms.Button
    $logsButton.Text = "📋 日志"
    $logsButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 9)
    $logsButton.Location = New-Object System.Drawing.Point(100, 60)
    $logsButton.Size = New-Object System.Drawing.Size(80, 30)
    $logsButton.Add_Click({ Show-ApplicationLogs })
    $buttonPanel.Controls.Add($logsButton)
    
    # 更新按钮
    $updateButton = New-Object System.Windows.Forms.Button
    $updateButton.Text = "🔄 更新"
    $updateButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 9)
    $updateButton.Location = New-Object System.Drawing.Point(190, 60)
    $updateButton.Size = New-Object System.Drawing.Size(80, 30)
    $updateButton.Add_Click({ Update-Application })
    $buttonPanel.Controls.Add($updateButton)
    
    # 卸载按钮
    $uninstallButton = New-Object System.Windows.Forms.Button
    $uninstallButton.Text = "🗑️ 卸载"
    $uninstallButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 9)
    $uninstallButton.Location = New-Object System.Drawing.Point(280, 60)
    $uninstallButton.Size = New-Object System.Drawing.Size(80, 30)
    $uninstallButton.ForeColor = [System.Drawing.Color]::Red
    $uninstallButton.Add_Click({ Uninstall-Application })
    $buttonPanel.Controls.Add($uninstallButton)
    
    # 进度条
    $script:progressBar = New-Object System.Windows.Forms.ProgressBar
    $script:progressBar.Location = New-Object System.Drawing.Point(20, 220)
    $script:progressBar.Size = New-Object System.Drawing.Size(560, 20)
    $script:progressBar.Style = "Continuous"
    $script:progressBar.Visible = $false
    $form.Controls.Add($script:progressBar)
    
    # 日志文本框
    $script:logTextBox = New-Object System.Windows.Forms.TextBox
    $script:logTextBox.Location = New-Object System.Drawing.Point(20, 250)
    $script:logTextBox.Size = New-Object System.Drawing.Size(560, 180)
    $script:logTextBox.Multiline = $true
    $script:logTextBox.ScrollBars = "Vertical"
    $script:logTextBox.ReadOnly = $true
    $script:logTextBox.Font = New-Object System.Drawing.Font("Consolas", 9)
    $script:logTextBox.BackColor = [System.Drawing.Color]::Black
    $script:logTextBox.ForeColor = [System.Drawing.Color]::LightGreen
    $form.Controls.Add($script:logTextBox)
    
    # 底部状态栏
    $statusStrip = New-Object System.Windows.Forms.StatusStrip
    $statusLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
    $statusLabel.Text = "CABM管理器 v1.0 - 就绪"
    $statusStrip.Items.Add($statusLabel) | Out-Null
    $form.Controls.Add($statusStrip)
    
    return $form
}

# 更新状态
function Update-Status {
    param([string]$Status, [string]$Color = "Green")
    
    $script:statusLabel.Text = $Status
    $script:statusLabel.ForeColor = [System.Drawing.Color]::$Color
    $script:form.Refresh()
}

# 添加日志
function Add-Log {
    param([string]$Message)
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    
    $script:logTextBox.AppendText("$logMessage`r`n")
    $script:logTextBox.SelectionStart = $script:logTextBox.Text.Length
    $script:logTextBox.ScrollToCaret()
    $script:form.Refresh()
}

# 显示进度条
function Show-Progress {
    param([bool]$Show = $true)
    
    $script:progressBar.Visible = $Show
    if ($Show) {
        $script:progressBar.Style = "Marquee"
    } else {
        $script:progressBar.Style = "Continuous"
    }
}

# 检查Conda状态
function Test-CondaStatus {
    try {
        $result = conda --version 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# 检查CABM环境是否存在
function Test-CabmEnvironment {
    try {
        $envs = conda env list 2>$null
        return $envs -match "cabm\s"
    }
    catch {
        return $false
    }
}

# 检查应用进程状态
function Test-ApplicationProcess {
    try {
        $process = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*app.py*" -or $_.CommandLine -like "*start.py*"
        }
        return $process -ne $null
    }
    catch {
        return $false
    }
}

# 检查Docker状态（保留用于极端情况）
function Test-DockerStatus {
    try {
        $result = docker version 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# 检查容器状态（保留用于极端情况）
function Test-ContainerStatus {
    try {
        $status = docker ps -f name=cabm-app --format "{{.Status}}" 2>$null
        return $status -like "*Up*"
    }
    catch {
        return $false
    }
}

# 启动应用
function Start-Application {
    Add-Log "开始启动CABM应用..."
    Update-Status "正在启动..." "Blue"
    Show-Progress $true
    
    try {
        # 优先使用Conda部署
        if (Test-CondaStatus) {
            Add-Log "检测到Conda环境，使用Conda部署方式"
            Start-CondaApplication
        } else {
            Add-Log "未检测到Conda，尝试Docker部署方式..."
            Start-DockerApplication
        }
    }
    catch {
        Add-Log "启动失败: $($_.Exception.Message)"
        Update-Status "启动失败" "Red"
    }
    finally {
        Show-Progress $false
    }
}

# Conda方式启动应用
function Start-CondaApplication {
    Add-Log "使用Conda方式启动应用..."
    
    # 检查.conda目录
    $condaEnvPath = ".\.conda"
    if (Test-Path $condaEnvPath) {
        Add-Log "发现现有Conda环境: $condaEnvPath"
    } else {
        Add-Log "创建新的Conda环境到: $condaEnvPath"
        
        # 创建conda环境
        Add-Log "正在创建Conda环境..."
        $createCmd = "conda create -p `"$condaEnvPath`" python=3.11 -y"
        Invoke-Expression $createCmd 2>&1 | ForEach-Object { Add-Log $_ }
        
        if ($LASTEXITCODE -ne 0) {
            throw "Conda环境创建失败"
        }
        
        # 安装依赖
        Add-Log "正在安装Python依赖..."
        $installCmd = "conda run -p `"$condaEnvPath`" pip install -r requirements.txt"
        Invoke-Expression $installCmd 2>&1 | ForEach-Object { Add-Log $_ }
        
        if ($LASTEXITCODE -ne 0) {
            throw "依赖安装失败"
        }
    }
    
    # 检查是否已经在运行
    if (Test-ApplicationProcess) {
        Add-Log "检测到应用已在运行中"
        Update-Status "运行中" "Green"
        return
    }
    
    # 创建必要的目录
    $dirs = @("data\history", "data\memory", "data\scenes", "static\images\cache")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Add-Log "创建目录: $dir"
        }
    }
    
    # 检查配置文件
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Add-Log "已从模板创建配置文件 .env"
        } else {
            $defaultEnv = @"
# CABM配置文件
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
APP_HOST=127.0.0.1
APP_PORT=5000
DEBUG=false
"@
            Set-Content -Path ".env" -Value $defaultEnv -Encoding UTF8
            Add-Log "已创建默认配置文件 .env"
        }
        Add-Log "⚠️ 请编辑 .env 文件配置您的API密钥"
    }
    
    # 启动应用
    Add-Log "正在启动CABM应用..."
    $startFile = if (Test-Path "start.py") { "start.py" } else { "app.py" }
    $startCmd = "conda run -p `"$condaEnvPath`" python $startFile"
    
    # 后台启动应用
    Start-Process powershell -ArgumentList "-WindowStyle", "Minimized", "-Command", $startCmd -PassThru
    
    # 等待应用启动
    Start-Sleep -Seconds 3
    
    # 验证启动
    $maxRetries = 15
    for ($i = 0; $i -lt $maxRetries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Add-Log "应用启动成功！"
                Update-Status "运行中" "Green"
                return
            }
        }
        catch {
            # 继续等待
        }
        
        Start-Sleep -Seconds 2
        Add-Log "等待应用启动... ($($i+1)/$maxRetries)"
    }
    
    # 如果直接访问失败，检查进程
    if (Test-ApplicationProcess) {
        Add-Log "应用进程已启动，可能需要更长时间初始化"
        Update-Status "启动中" "Yellow"
    } else {
        throw "应用启动失败，请检查日志"
    }
}

# Docker方式启动应用（极端情况使用）
function Start-DockerApplication {
    Add-Log "使用Docker方式启动应用..."
    
    # 检查Docker
    if (-not (Test-DockerStatus)) {
        Add-Log "Docker未运行，正在尝试启动..."
        $dockerPaths = @(
            "C:\Program Files\Docker\Docker\Docker Desktop.exe",
            "$env:USERPROFILE\AppData\Local\Docker\Docker Desktop.exe"
        )
        
        $dockerPath = $dockerPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($dockerPath) {
            Start-Process -FilePath $dockerPath
            Add-Log "等待Docker启动..."
            
            # 等待Docker启动
            for ($i = 0; $i -lt 30; $i++) {
                Start-Sleep -Seconds 2
                if (Test-DockerStatus) {
                    Add-Log "Docker已启动"
                    break
                }
                if ($i -eq 29) {
                    throw "Docker启动超时"
                }
            }
        } else {
            throw "找不到Docker Desktop"
        }
    }
    
    # 检查容器是否存在
    $containerExists = docker ps -a -f name=cabm-app --format "{{.Names}}" 2>$null
    if ($containerExists -eq "cabm-app") {
        Add-Log "发现现有容器，正在启动..."
        docker start cabm-app 2>&1 | ForEach-Object { Add-Log $_ }
    } else {
        Add-Log "未发现容器，开始部署..."
        if (Test-Path "deploy-docker.ps1") {
            & ".\deploy-docker.ps1" "deploy" 2>&1 | ForEach-Object { Add-Log $_ }
        } elseif (Test-Path "deploy-docker.bat") {
            cmd /c "deploy-docker.bat deploy" 2>&1 | ForEach-Object { Add-Log $_ }
        } else {
            throw "找不到部署脚本"
        }
    }
    
    # 验证启动
    Start-Sleep -Seconds 5
    if (Test-ContainerStatus) {
        Add-Log "应用启动成功！"
        Update-Status "运行中" "Green"
    } else {
        throw "应用启动失败"
    }
}

# 停止应用
function Stop-Application {
    Add-Log "正在停止应用..."
    Update-Status "正在停止..." "Yellow"
    Show-Progress $true
    
    try {
        # 优先停止Conda应用
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*app.py*" -or $_.CommandLine -like "*start.py*"
        }
        
        if ($pythonProcesses) {
            Add-Log "发现运行中的Python应用进程，正在停止..."
            $pythonProcesses | ForEach-Object {
                try {
                    $_.Kill()
                    Add-Log "已停止进程 PID: $($_.Id)"
                }
                catch {
                    Add-Log "停止进程失败 PID: $($_.Id) - $($_.Exception.Message)"
                }
            }
            Add-Log "应用已停止"
            Update-Status "已停止" "Gray"
        } else {
            # 尝试停止Docker容器
            try {
                docker stop cabm-app 2>&1 | ForEach-Object { Add-Log $_ }
                Add-Log "Docker容器已停止"
                Update-Status "已停止" "Gray"
            }
            catch {
                Add-Log "未发现运行中的应用"
                Update-Status "已停止" "Gray"
            }
        }
    }
    catch {
        Add-Log "停止失败: $($_.Exception.Message)"
        Update-Status "停止失败" "Red"
    }
    finally {
        Show-Progress $false
    }
}

# 重启应用
function Restart-Application {
    Add-Log "正在重启应用..."
    Update-Status "正在重启..." "Blue"
    Show-Progress $true
    
    try {
        # 先停止应用
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*app.py*" -or $_.CommandLine -like "*start.py*"
        }
        
        if ($pythonProcesses) {
            Add-Log "停止现有Python应用..."
            $pythonProcesses | ForEach-Object { $_.Kill() }
            Start-Sleep -Seconds 2
        } else {
            # 尝试重启Docker容器
            docker restart cabm-app 2>&1 | ForEach-Object { Add-Log $_ }
            if ($LASTEXITCODE -eq 0) {
                Add-Log "Docker容器已重启"
                Update-Status "运行中" "Green"
                return
            }
        }
        
        # 重新启动Conda应用
        if (Test-CondaStatus) {
            Start-CondaApplication
        } else {
            Start-DockerApplication
        }
    }
    catch {
        Add-Log "重启失败: $($_.Exception.Message)"
        Update-Status "重启失败" "Red"
    }
    finally {
        Show-Progress $false
    }
}

# 获取应用状态
function Get-ApplicationStatus {
    Add-Log "检查应用状态..."
    
    try {
        # Conda状态
        if (Test-CondaStatus) {
            Add-Log "✅ Conda: 已安装"
            
            # 检查CABM环境
            if (Test-Path ".\.conda") {
                Add-Log "✅ CABM环境: 存在 (.\.conda)"
            } else {
                Add-Log "⚠️ CABM环境: 未创建"
            }
        } else {
            Add-Log "❌ Conda: 未安装"
        }
        
        # 应用进程状态
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*app.py*" -or $_.CommandLine -like "*start.py*"
        }
        
        if ($pythonProcesses) {
            Add-Log "✅ 应用: 运行中 (Conda方式)"
            $pythonProcesses | ForEach-Object {
                Add-Log "   进程 PID: $($_.Id)"
            }
            Update-Status "运行中" "Green"
            
            # 测试服务
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
                Add-Log "🌐 服务: 正常 (HTTP $($response.StatusCode))"
            }
            catch {
                Add-Log "🌐 服务: 无响应"
            }
        } else {
            # 检查Docker容器状态
            $containerStatus = docker ps -a -f name=cabm-app --format "{{.Names}}: {{.Status}}" 2>$null
            if ($containerStatus) {
                Add-Log "📦 Docker容器: $containerStatus"
                
                if (Test-ContainerStatus) {
                    Update-Status "运行中 (Docker)" "Green"
                    
                    # 测试服务
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 5 -UseBasicParsing
                        Add-Log "🌐 服务: 正常 (HTTP $($response.StatusCode))"
                    }
                    catch {
                        Add-Log "🌐 服务: 无响应"
                    }
                } else {
                    Update-Status "已停止" "Gray"
                }
            } else {
                Add-Log "❌ 应用: 未运行"
                Update-Status "未部署" "Red"
            }
        }
        
        # 配置文件状态
        if (Test-Path ".env") {
            Add-Log "✅ 配置文件: 存在"
        } else {
            Add-Log "⚠️ 配置文件: 缺失 (.env)"
        }
        
        # 依赖文件状态
        if (Test-Path "requirements.txt") {
            Add-Log "✅ 依赖文件: 存在"
        } else {
            Add-Log "❌ 依赖文件: 缺失 (requirements.txt)"
        }
        
        # Docker状态（仅在有Docker时显示）
        if (Test-DockerStatus) {
            Add-Log "ℹ️ Docker: 可用 (备用方案)"
            
            # 镜像信息
            $imageInfo = docker images cabm --format "{{.Repository}}:{{.Tag}} ({{.Size}})" 2>$null
            if ($imageInfo) {
                Add-Log "🖼️ Docker镜像: $imageInfo"
            }
        }
    }
    catch {
        Add-Log "状态检查失败: $($_.Exception.Message)"
    }
}

# 打开应用
function Open-Application {
    Add-Log "正在打开应用..."
    
    # 检查应用是否运行
    $isRunning = $false
    
    # 检查Python进程
    if (Test-ApplicationProcess) {
        $isRunning = $true
    }
    
    # 检查Docker容器
    if (-not $isRunning -and (Test-ContainerStatus)) {
        $isRunning = $true
    }
    
    if ($isRunning) {
        Start-Process "http://localhost:5000"
        Add-Log "已在浏览器中打开应用"
    } else {
        Add-Log "应用未运行，请先启动应用"
        [System.Windows.Forms.MessageBox]::Show("应用未运行，请先启动应用", "提示", "OK", "Warning")
    }
}

# 编辑配置
function Edit-Configuration {
    $envFile = ".env"
    if (Test-Path $envFile) {
        Start-Process notepad.exe -ArgumentList $envFile
        Add-Log "已打开配置文件编辑器"
    } else {
        $result = [System.Windows.Forms.MessageBox]::Show("配置文件不存在，是否创建？", "提示", "YesNo", "Question")
        if ($result -eq "Yes") {
            if (Test-Path ".env.example") {
                Copy-Item ".env.example" $envFile
            } else {
                Set-Content -Path $envFile -Value "# CABM配置文件`nOPENAI_API_KEY=your_api_key_here"
            }
            Start-Process notepad.exe -ArgumentList $envFile
            Add-Log "已创建并打开配置文件"
        }
    }
}

# 显示日志
function Show-ApplicationLogs {
    Add-Log "获取应用日志..."
    
    try {
        # 首先尝试显示本地日志文件
        $logFiles = @("logs\app.log", "data\history\*.log", "*.log")
        $foundLogs = $false
        
        foreach ($logPattern in $logFiles) {
            $logs = Get-ChildItem -Path $logPattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($logs) {
                Add-Log "显示日志文件: $($logs.Name)"
                $content = Get-Content $logs.FullName -Tail 20 -ErrorAction SilentlyContinue
                $content | ForEach-Object { Add-Log $_ }
                $foundLogs = $true
                break
            }
        }
        
        # 如果没有本地日志，尝试Docker日志
        if (-not $foundLogs) {
            $dockerLogs = docker logs --tail 20 cabm-app 2>&1
            if ($LASTEXITCODE -eq 0) {
                Add-Log "显示Docker容器日志:"
                $dockerLogs | ForEach-Object { Add-Log $_ }
            } else {
                Add-Log "未找到应用日志文件"
            }
        }
    }
    catch {
        Add-Log "获取日志失败: $($_.Exception.Message)"
    }
}

# 更新应用
function Update-Application {
    $result = [System.Windows.Forms.MessageBox]::Show("确定要更新应用吗？这将重新安装依赖并重启应用。", "确认更新", "YesNo", "Question")
    if ($result -eq "Yes") {
        Add-Log "开始更新应用..."
        Update-Status "正在更新..." "Blue"
        Show-Progress $true
        
        try {
            # 停止当前应用
            Stop-Application
            
            if (Test-CondaStatus -and (Test-Path ".\.conda")) {
                Add-Log "更新Conda环境依赖..."
                
                # 更新依赖
                $updateCmd = "conda run -p `".\.conda`" pip install -r requirements.txt --upgrade"
                Invoke-Expression $updateCmd 2>&1 | ForEach-Object { Add-Log $_ }
                
                if ($LASTEXITCODE -eq 0) {
                    Add-Log "依赖更新完成，重新启动应用..."
                    Start-CondaApplication
                } else {
                    throw "依赖更新失败"
                }
            } else {
                # 使用Docker更新
                if (Test-Path "deploy-docker.ps1") {
                    & ".\deploy-docker.ps1" "update" 2>&1 | ForEach-Object { Add-Log $_ }
                } elseif (Test-Path "deploy-docker.bat") {
                    cmd /c "deploy-docker.bat update" 2>&1 | ForEach-Object { Add-Log $_ }
                } else {
                    throw "找不到更新方法"
                }
            }
            
            Add-Log "更新完成"
            Update-Status "运行中" "Green"
        }
        catch {
            Add-Log "更新失败: $($_.Exception.Message)"
            Update-Status "更新失败" "Red"
        }
        finally {
            Show-Progress $false
        }
    }
}

# 卸载应用
function Uninstall-Application {
    $result = [System.Windows.Forms.MessageBox]::Show("确定要卸载应用吗？这将删除Conda环境、容器和镜像。", "确认卸载", "YesNo", "Warning")
    if ($result -eq "Yes") {
        Add-Log "开始卸载应用..."
        Update-Status "正在卸载..." "Red"
        Show-Progress $true
        
        try {
            # 停止应用
            Stop-Application
            
            # 删除Conda环境
            if (Test-Path ".\.conda") {
                Add-Log "删除Conda环境..."
                try {
                    Remove-Item ".\.conda" -Recurse -Force
                    Add-Log "Conda环境已删除"
                }
                catch {
                    Add-Log "删除Conda环境失败: $($_.Exception.Message)"
                }
            }
            
            # 删除Docker容器和镜像
            try {
                # 停止并删除容器
                docker stop cabm-app 2>&1 | ForEach-Object { Add-Log $_ }
                docker rm cabm-app 2>&1 | ForEach-Object { Add-Log $_ }
                
                # 删除镜像
                docker rmi cabm:latest 2>&1 | ForEach-Object { Add-Log $_ }
                
                # 清理悬空镜像
                docker image prune -f 2>&1 | ForEach-Object { Add-Log $_ }
            }
            catch {
                Add-Log "Docker清理过程中的警告: $($_.Exception.Message)"
            }
            
            Add-Log "卸载完成"
            Update-Status "已卸载" "Gray"
        }
        catch {
            Add-Log "卸载失败: $($_.Exception.Message)"
        }
        finally {
            Show-Progress $false
        }
    }
}

# 主程序
function Start-GUI {
    try {
        # 创建表单
        $script:form = New-MainForm
        
        # 初始状态检查
        Add-Log "CABM图形管理器已启动"
        Get-ApplicationStatus
        
        # 显示窗口
        [System.Windows.Forms.Application]::Run($script:form)
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("启动失败: $($_.Exception.Message)", "错误", "OK", "Error")
    }
}

# 启动GUI
Start-GUI

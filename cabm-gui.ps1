#Requires -Version 5.1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# 启用高DPI感知
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Drawing;
public class DPIAware {
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();
    
    [DllImport("shcore.dll")]
    public static extern int SetProcessDpiAwareness(int awareness);
    
    [DllImport("user32.dll")]
    public static extern int GetSystemMetrics(int nIndex);
    
    [DllImport("user32.dll")]
    public static extern IntPtr GetDC(IntPtr hWnd);
    
    [DllImport("gdi32.dll")]
    public static extern int GetDeviceCaps(IntPtr hdc, int nIndex);
    
    [DllImport("user32.dll")]
    public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
    
    public static void EnableDPIAwareness() {
        try {
            // 尝试使用新的 API (Windows 8.1+)
            SetProcessDpiAwareness(2); // PROCESS_PER_MONITOR_DPI_AWARE
        } catch {
            try {
                // 回退到旧的 API (Windows Vista+)
                SetProcessDPIAware();
            } catch {
                // 忽略错误，继续运行
            }
        }
    }
    
    public static float GetDPIScale() {
        try {
            IntPtr hdc = GetDC(IntPtr.Zero);
            int dpi = GetDeviceCaps(hdc, 88); // LOGPIXELSX
            ReleaseDC(IntPtr.Zero, hdc);
            
            if (dpi == 0) dpi = 96; // 默认 DPI
            return dpi / 96.0f;
        } catch {
            return 1.0f;
        }
    }
}
"@

# 启用高DPI感知
try {
    [DPIAware]::EnableDPIAwareness()
}
catch {
    # 如果设置失败，继续运行
}

# 全局变量
$script:form = $null
$script:statusLabel = $null
$script:logTextBox = $null
$script:progressBar = $null
$script:dpiScale = 1.0

# 获取DPI缩放比例
function Get-DPIScale {
    try {
        # 优先使用C#类的方法
        $scale = [DPIAware]::GetDPIScale()
        
        # 如果C#方法失败，使用备用方法
        if ($scale -eq 1.0 -or $scale -eq 0) {
            # 创建临时Graphics对象来获取DPI
            $form = New-Object System.Windows.Forms.Form
            $graphics = $form.CreateGraphics()
            $dpi = $graphics.DpiX
            $graphics.Dispose()
            $form.Dispose()
            
            if ($dpi -gt 0) {
                $scale = $dpi / 96.0
            } else {
                $scale = 1.0
            }
        }
        
        # 限制缩放范围
        if ($scale -lt 1.0) { $scale = 1.0 }
        if ($scale -gt 3.0) { $scale = 3.0 }
        
        return $scale
    }
    catch {
        return 1.0
    }
}

# DPI感知的尺寸计算
function Scale-Size {
    param(
        [int]$Width,
        [int]$Height
    )
    
    $scaledWidth = [Math]::Round($Width * $script:dpiScale)
    $scaledHeight = [Math]::Round($Height * $script:dpiScale)
    
    return New-Object System.Drawing.Size($scaledWidth, $scaledHeight)
}

# DPI感知的位置计算
function Scale-Point {
    param(
        [int]$X,
        [int]$Y
    )
    
    $scaledX = [Math]::Round($X * $script:dpiScale)
    $scaledY = [Math]::Round($Y * $script:dpiScale)
    
    return New-Object System.Drawing.Point($scaledX, $scaledY)
}

# DPI感知的字体大小计算
function Scale-FontSize {
    param([int]$Size)
    
    $scaledSize = [Math]::Round($Size * $script:dpiScale)
    if ($scaledSize -lt 8) { $scaledSize = 8 }
    if ($scaledSize -gt 48) { $scaledSize = 48 }
    
    return $scaledSize
}

# 获取支持Emoji的字体
function Get-EmojiSupportedFont {
    param([int]$Size = 10, [System.Drawing.FontStyle]$Style = [System.Drawing.FontStyle]::Regular)
    
    # DPI感知的字体大小
    $scaledSize = Scale-FontSize -Size $Size
    
    # 优先使用的字体列表（按优先级排序）
    $emojieFonts = @(
        "Segoe UI Emoji",           # Windows 10/11 默认Emoji字体
        "Segoe UI Symbol",          # Windows 7/8 符号字体
        "Symbola",                  # 开源Unicode字体
        "DejaVu Sans",              # 跨平台字体
        "Microsoft YaHei UI"        # 中文字体（有限表情支持）
    )
    
    # 获取系统中所有可用字体
    $installedFonts = [System.Drawing.FontFamily]::Families | ForEach-Object { $_.Name }
    
    # 寻找第一个可用的表情字体
    foreach ($fontName in $emojieFonts) {
        if ($installedFonts -contains $fontName) {
            try {
                $font = New-Object System.Drawing.Font($fontName, $scaledSize, $Style)
                return $font
            }
            catch {
                # 如果字体创建失败，继续下一个
                continue
            }
        }
    }
    
    # 如果都不可用，返回默认字体
    return New-Object System.Drawing.Font("Microsoft Sans Serif", $scaledSize, $Style)
}

# 获取现代化字体
function Get-ModernFont {
    param([int]$Size = 10, [System.Drawing.FontStyle]$Style = [System.Drawing.FontStyle]::Regular)
    
    # DPI感知的字体大小
    $scaledSize = Scale-FontSize -Size $Size
    
    $modernFonts = @(
        "Segoe UI",
        "Microsoft YaHei UI",
        "Consolas",
        "Calibri"
    )
    
    $installedFonts = [System.Drawing.FontFamily]::Families | ForEach-Object { $_.Name }
    
    foreach ($fontName in $modernFonts) {
        if ($installedFonts -contains $fontName) {
            try {
                return New-Object System.Drawing.Font($fontName, $scaledSize, $Style)
            }
            catch {
                continue
            }
        }
    }
    
    return New-Object System.Drawing.Font("Microsoft Sans Serif", $scaledSize, $Style)
}

# 创建现代化按钮
function New-ModernButton {
    param(
        [string]$Text,
        [System.Drawing.Point]$Location,
        [System.Drawing.Size]$Size,
        [System.Drawing.Color]$BackColor = [System.Drawing.Color]::FromArgb(70, 130, 180),
        [System.Drawing.Color]$ForeColor = [System.Drawing.Color]::White,
        [int]$FontSize = 10,
        [scriptblock]$ClickAction
    )
    
    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.Location = Scale-Point -X $Location.X -Y $Location.Y
    $button.Size = Scale-Size -Width $Size.Width -Height $Size.Height
    $button.BackColor = $BackColor
    $button.ForeColor = $ForeColor
    $button.Font = Get-EmojiSupportedFont -Size $FontSize -Style Bold
    $button.FlatStyle = "Flat"
    $button.FlatAppearance.BorderSize = 0
    
    # 安全地计算鼠标悬停颜色，确保RGB值在0-255范围内
    $hoverR = [Math]::Min(255, [Math]::Max(0, $BackColor.R + 20))
    $hoverG = [Math]::Min(255, [Math]::Max(0, $BackColor.G + 20))
    $hoverB = [Math]::Min(255, [Math]::Max(0, $BackColor.B + 20))
    $button.FlatAppearance.MouseOverBackColor = [System.Drawing.Color]::FromArgb($hoverR, $hoverG, $hoverB)
    
    # 安全地计算鼠标按下颜色，确保RGB值在0-255范围内
    $downR = [Math]::Min(255, [Math]::Max(0, $BackColor.R - 20))
    $downG = [Math]::Min(255, [Math]::Max(0, $BackColor.G - 20))
    $downB = [Math]::Min(255, [Math]::Max(0, $BackColor.B - 20))
    $button.FlatAppearance.MouseDownBackColor = [System.Drawing.Color]::FromArgb($downR, $downG, $downB)
    
    $button.Cursor = [System.Windows.Forms.Cursors]::Hand
    
    if ($ClickAction) {
        $button.Add_Click($ClickAction)
    }
    
    return $button
}

# 创建主窗口
function New-MainForm {
    # 初始化DPI缩放
    $script:dpiScale = Get-DPIScale
    
    # 输出调试信息
    Write-Host "DPI缩放比例: $($script:dpiScale)" -ForegroundColor Green
    Write-Host "基础窗口尺寸: 900x700" -ForegroundColor Yellow
    $scaledSize = Scale-Size -Width 900 -Height 700
    Write-Host "缩放后窗口尺寸: $($scaledSize.Width)x$($scaledSize.Height)" -ForegroundColor Cyan
    
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "沙雕GUI——由一位抽象且沙雕的人创作"
    $form.Size = $scaledSize
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedSingle"
    $form.MaximizeBox = $false
    $form.BackColor = [System.Drawing.Color]::FromArgb(245, 247, 250)
    
    # 设置DPI感知
    try {
        $form.AutoScaleMode = [System.Windows.Forms.AutoScaleMode]::Dpi
    }
    catch {
        # 如果设置失败，使用默认模式
        $form.AutoScaleMode = [System.Windows.Forms.AutoScaleMode]::Font
    }
    
    # 尝试加载图标
    try {
        if (Test-Path "$PSScriptRoot\static\images\default.svg") {
            # SVG图标无法直接使用，尝试其他格式
            $iconPath = "$PSScriptRoot\static\images\default.ico"
            if (Test-Path $iconPath) {
                $form.Icon = [System.Drawing.Icon]::new($iconPath)
            }
        }
    }
    catch {
        # 图标加载失败时忽略错误
    }
    
    # 顶部装饰条
    $topPanel = New-Object System.Windows.Forms.Panel
    $topPanel.Location = Scale-Point -X 0 -Y 0
    $topPanel.Size = Scale-Size -Width 900 -Height 4
    $topPanel.BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
    $form.Controls.Add($topPanel)
    
    # 主标题面板
    $titlePanel = New-Object System.Windows.Forms.Panel
    $titlePanel.Location = Scale-Point -X 0 -Y 4
    $titlePanel.Size = Scale-Size -Width 900 -Height 85
    $titlePanel.BackColor = [System.Drawing.Color]::White
    $form.Controls.Add($titlePanel)
    
    # 应用图标标签
    $iconLabel = New-Object System.Windows.Forms.Label
    $iconLabel.Text = "🚀"
    $iconLabel.Font = New-Object System.Drawing.Font("Segoe UI Emoji", (Scale-FontSize -Size 24), [System.Drawing.FontStyle]::Regular)
    $iconLabel.Location = Scale-Point -X 30 -Y 25
    $iconLabel.Size = Scale-Size -Width 50 -Height 40
    $iconLabel.TextAlign = "MiddleCenter"
    $titlePanel.Controls.Add($iconLabel)
    
    # 主标题
    $titleLabel = New-Object System.Windows.Forms.Label
    $titleLabel.Text = "CABM"
    $titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", (Scale-FontSize -Size 20), [System.Drawing.FontStyle]::Bold)
    $titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(32, 32, 32)
    $titleLabel.Location = Scale-Point -X 90 -Y 15
    $titleLabel.Size = Scale-Size -Width 200 -Height 40
    $titlePanel.Controls.Add($titleLabel)
    
    # 副标题
    $subtitleLabel = New-Object System.Windows.Forms.Label
    $subtitleLabel.Text = "Code Afflatus & Beyond Matter"
    $subtitleLabel.Font = Get-ModernFont -Size 10
    $subtitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(128, 128, 128)
    $subtitleLabel.Location = Scale-Point -X 90 -Y 50
    $subtitleLabel.Size = Scale-Size -Width 300 -Height 25
    $titlePanel.Controls.Add($subtitleLabel)
    
    # 状态指示器
    $statusIndicator = New-Object System.Windows.Forms.Panel
    $statusIndicator.Location = Scale-Point -X 800 -Y 40
    $statusIndicator.Size = Scale-Size -Width 12 -Height 12
    $statusIndicator.BackColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
    $titlePanel.Controls.Add($statusIndicator)
    
    # 状态标签
    $script:statusLabel = New-Object System.Windows.Forms.Label
    $script:statusLabel.Text = "就绪"
    $script:statusLabel.Font = Get-ModernFont -Size 9
    $script:statusLabel.Location = Scale-Point -X 820 -Y 36
    $script:statusLabel.Size = Scale-Size -Width 60 -Height 20
    $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
    $titlePanel.Controls.Add($script:statusLabel)
    
    # 主要操作按钮面板
    $mainButtonPanel = New-Object System.Windows.Forms.GroupBox
    $mainButtonPanel.Text = "主要操作"
    $mainButtonPanel.Font = Get-ModernFont -Size 10 -Style Bold
    $mainButtonPanel.Location = Scale-Point -X 30 -Y 100
    $mainButtonPanel.Size = Scale-Size -Width 840 -Height 80
    $mainButtonPanel.ForeColor = [System.Drawing.Color]::FromArgb(64, 64, 64)
    $form.Controls.Add($mainButtonPanel)
    
    # 一键启动按钮 - 主要操作，更大更醒目
    $startButton = New-ModernButton -Text "🚀 一键启动" -Location (New-Object System.Drawing.Point(20, 25)) -Size (New-Object System.Drawing.Size(140, 45)) -BackColor ([System.Drawing.Color]::FromArgb(40, 167, 69)) -FontSize 12 -ClickAction { Start-Application }
    $mainButtonPanel.Controls.Add($startButton)
    
    # 停止按钮
    $stopButton = New-ModernButton -Text "🛑 停止" -Location (New-Object System.Drawing.Point(180, 25)) -Size (New-Object System.Drawing.Size(110, 45)) -BackColor ([System.Drawing.Color]::FromArgb(220, 53, 69)) -FontSize 11 -ClickAction { Stop-Application }
    $mainButtonPanel.Controls.Add($stopButton)
    
    # 重启按钮
    $restartButton = New-ModernButton -Text "🔄 重启" -Location (New-Object System.Drawing.Point(310, 25)) -Size (New-Object System.Drawing.Size(110, 45)) -BackColor ([System.Drawing.Color]::FromArgb(255, 193, 7)) -ForeColor ([System.Drawing.Color]::FromArgb(32, 32, 32)) -FontSize 11 -ClickAction { Restart-Application }
    $mainButtonPanel.Controls.Add($restartButton)
    
    # 状态查询按钮
    $statusButton = New-ModernButton -Text "📊 状态" -Location (New-Object System.Drawing.Point(440, 25)) -Size (New-Object System.Drawing.Size(110, 45)) -BackColor ([System.Drawing.Color]::FromArgb(0, 123, 255)) -FontSize 11 -ClickAction { Get-ApplicationStatus }
    $mainButtonPanel.Controls.Add($statusButton)
    
    # 打开应用按钮
    $openButton = New-ModernButton -Text "🌐 打开" -Location (New-Object System.Drawing.Point(570, 25)) -Size (New-Object System.Drawing.Size(120, 45)) -BackColor ([System.Drawing.Color]::FromArgb(23, 162, 184)) -FontSize 11 -ClickAction { Open-Application }
    $mainButtonPanel.Controls.Add($openButton)
    
    # 管理工具面板
    $toolsPanel = New-Object System.Windows.Forms.GroupBox
    $toolsPanel.Text = "管理工具"
    $toolsPanel.Font = Get-ModernFont -Size 10 -Style Bold
    $toolsPanel.Location = Scale-Point -X 30 -Y 195
    $toolsPanel.Size = Scale-Size -Width 840 -Height 60
    $toolsPanel.ForeColor = [System.Drawing.Color]::FromArgb(64, 64, 64)
    $form.Controls.Add($toolsPanel)
    
    # 工具按钮 - 更小更紧凑
    $configButton = New-ModernButton -Text "⚙️ 配置" -Location (New-Object System.Drawing.Point(20, 20)) -Size (New-Object System.Drawing.Size(100, 30)) -BackColor ([System.Drawing.Color]::FromArgb(108, 117, 125)) -FontSize 9 -ClickAction { Edit-Configuration }
    $toolsPanel.Controls.Add($configButton)
    
    $logsButton = New-ModernButton -Text "📋 日志" -Location (New-Object System.Drawing.Point(140, 20)) -Size (New-Object System.Drawing.Size(100, 30)) -BackColor ([System.Drawing.Color]::FromArgb(108, 117, 125)) -FontSize 9 -ClickAction { Show-ApplicationLogs }
    $toolsPanel.Controls.Add($logsButton)
    
    $updateButton = New-ModernButton -Text "🔄 更新" -Location (New-Object System.Drawing.Point(260, 20)) -Size (New-Object System.Drawing.Size(100, 30)) -BackColor ([System.Drawing.Color]::FromArgb(108, 117, 125)) -FontSize 9 -ClickAction { Update-Application }
    $toolsPanel.Controls.Add($updateButton)
    
    $uninstallButton = New-ModernButton -Text "🗑️ 卸载" -Location (New-Object System.Drawing.Point(720, 20)) -Size (New-Object System.Drawing.Size(100, 30)) -BackColor ([System.Drawing.Color]::FromArgb(220, 53, 69)) -FontSize 9 -ClickAction { Uninstall-Application }
    $toolsPanel.Controls.Add($uninstallButton)
    
    # 进度条面板
    $progressPanel = New-Object System.Windows.Forms.Panel
    $progressPanel.Location = Scale-Point -X 30 -Y 270
    $progressPanel.Size = Scale-Size -Width 840 -Height 40
    $progressPanel.BackColor = [System.Drawing.Color]::White
    $form.Controls.Add($progressPanel)
    
    # 进度条标签
    $progressLabel = New-Object System.Windows.Forms.Label
    $progressLabel.Text = "操作进度"
    $progressLabel.Font = Get-ModernFont -Size 9
    $progressLabel.Location = Scale-Point -X 10 -Y 6
    $progressLabel.Size = Scale-Size -Width 100 -Height 18
    $progressLabel.ForeColor = [System.Drawing.Color]::FromArgb(108, 117, 125)
    $progressPanel.Controls.Add($progressLabel)
    
    # 进度条
    $script:progressBar = New-Object System.Windows.Forms.ProgressBar
    $script:progressBar.Location = Scale-Point -X 120 -Y 6
    $script:progressBar.Size = Scale-Size -Width 700 -Height 18
    $script:progressBar.Style = "Continuous"
    $script:progressBar.Visible = $false
    $script:progressBar.ForeColor = [System.Drawing.Color]::FromArgb(0, 123, 255)
    $progressPanel.Controls.Add($script:progressBar)
    
    # 日志面板
    $logPanel = New-Object System.Windows.Forms.GroupBox
    $logPanel.Text = "系统日志"
    $logPanel.Font = Get-ModernFont -Size 10 -Style Bold
    $logPanel.Location = Scale-Point -X 30 -Y 310
    $logPanel.Size = Scale-Size -Width 840 -Height 250
    $logPanel.ForeColor = [System.Drawing.Color]::FromArgb(64, 64, 64)
    $form.Controls.Add($logPanel)
    
    # 日志文本框
    $script:logTextBox = New-Object System.Windows.Forms.RichTextBox
    $script:logTextBox.Location = Scale-Point -X 15 -Y 25
    $script:logTextBox.Size = Scale-Size -Width 810 -Height 210
    $script:logTextBox.ReadOnly = $true
    $script:logTextBox.Font = New-Object System.Drawing.Font("Consolas", (Scale-FontSize -Size 9))
    $script:logTextBox.BackColor = [System.Drawing.Color]::FromArgb(28, 28, 28)
    $script:logTextBox.ForeColor = [System.Drawing.Color]::FromArgb(204, 204, 204)
    $script:logTextBox.BorderStyle = "None"
    $script:logTextBox.ScrollBars = "Vertical"
    $logPanel.Controls.Add($script:logTextBox)
    
    # 底部状态栏
    $statusStrip = New-Object System.Windows.Forms.StatusStrip
    $statusStrip.BackColor = [System.Drawing.Color]::FromArgb(248, 249, 250)
    $statusStrip.ForeColor = [System.Drawing.Color]::FromArgb(108, 117, 125)
    
    $statusLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
    $statusLabel.Text = "沙雕GUI v2.0 - 就绪 (DPI: $([Math]::Round($script:dpiScale * 100, 0))%)"
    $statusLabel.Font = Get-ModernFont -Size 9
    $statusStrip.Items.Add($statusLabel) | Out-Null
    
    # 版本信息
    $versionLabel = New-Object System.Windows.Forms.ToolStripStatusLabel
    $versionLabel.Text = "PowerShell GUI - 高DPI优化"
    $versionLabel.Spring = $true
    $versionLabel.TextAlign = "MiddleRight"
    $statusStrip.Items.Add($versionLabel) | Out-Null
    
    $form.Controls.Add($statusStrip)
    
    return $form
}

# 更新状态
function Update-Status {
    param([string]$Status, [string]$Color = "Green")
    
    $script:statusLabel.Text = $Status
    
    # 根据状态设置颜色和状态指示器
    switch ($Color.ToLower()) {
        "green" { 
            $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
            $statusIndicator = $script:form.Controls | Where-Object { $_.GetType().Name -eq "Panel" -and $_.Parent.GetType().Name -eq "Panel" }
            if ($statusIndicator) {
                $statusIndicator.BackColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
            }
        }
        "red" { 
            $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(220, 53, 69)
            $statusIndicator = $script:form.Controls | Where-Object { $_.GetType().Name -eq "Panel" -and $_.Parent.GetType().Name -eq "Panel" }
            if ($statusIndicator) {
                $statusIndicator.BackColor = [System.Drawing.Color]::FromArgb(220, 53, 69)
            }
        }
        "yellow" { 
            $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(255, 193, 7)
            $statusIndicator = $script:form.Controls | Where-Object { $_.GetType().Name -eq "Panel" -and $_.Parent.GetType().Name -eq "Panel" }
            if ($statusIndicator) {
                $statusIndicator.BackColor = [System.Drawing.Color]::FromArgb(255, 193, 7)
            }
        }
        "blue" { 
            $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0, 123, 255)
            $statusIndicator = $script:form.Controls | Where-Object { $_.GetType().Name -eq "Panel" -and $_.Parent.GetType().Name -eq "Panel" }
            if ($statusIndicator) {
                $statusIndicator.BackColor = [System.Drawing.Color]::FromArgb(0, 123, 255)
            }
        }
        "gray" { 
            $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(108, 117, 125)
            $statusIndicator = $script:form.Controls | Where-Object { $_.GetType().Name -eq "Panel" -and $_.Parent.GetType().Name -eq "Panel" }
            if ($statusIndicator) {
                $statusIndicator.BackColor = [System.Drawing.Color]::FromArgb(108, 117, 125)
            }
        }
        default { 
            $script:statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(40, 167, 69)
        }
    }
    
    $script:form.Refresh()
}

# 添加日志
function Add-Log {
    param([string]$Message, [string]$Type = "INFO")
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    # 根据日志类型设置颜色
    $color = switch ($Type.ToUpper()) {
        "ERROR" { [System.Drawing.Color]::FromArgb(255, 102, 102) }
        "WARNING" { [System.Drawing.Color]::FromArgb(255, 193, 7) }
        "SUCCESS" { [System.Drawing.Color]::FromArgb(40, 167, 69) }
        "INFO" { [System.Drawing.Color]::FromArgb(204, 204, 204) }
        default { [System.Drawing.Color]::FromArgb(204, 204, 204) }
    }
    
    # 添加带颜色的文本
    $logMessage = "[$timestamp] [$Type] $Message`n"
    
    $script:logTextBox.SelectionStart = $script:logTextBox.Text.Length
    $script:logTextBox.SelectionLength = 0
    $script:logTextBox.SelectionColor = $color
    $script:logTextBox.AppendText($logMessage)
    
    # 自动滚动到底部
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
        Add-Log "启动失败: $($_.Exception.Message)" "ERROR"
        Update-Status "启动失败" "Red"
    }
    finally {
        Show-Progress $false
    }
}

# Conda方式启动应用
function Start-CondaApplication {
    Add-Log "🐍 使用Conda方式启动应用..."
    
    # 检查.conda目录
    $condaEnvPath = ".\.conda"
    if (Test-Path $condaEnvPath) {
        Add-Log "✅ 发现现有Conda环境: $condaEnvPath"
    } else {
        Add-Log "📦 创建新的Conda环境到: $condaEnvPath"
        
        # 创建conda环境
        Add-Log "⏳ 正在创建Conda环境（可能需要几分钟）..."
        Update-Status "创建环境中..." "Blue"
        $createCmd = "conda create -p `"$condaEnvPath`" python=3.11 -y"
        Invoke-Expression $createCmd 2>&1 | ForEach-Object { Add-Log $_ }
        
        if ($LASTEXITCODE -ne 0) {
            throw "Conda环境创建失败"
        }
        Add-Log "✅ Conda环境创建完成"
        
        # 安装依赖
        Add-Log "📥 正在安装Python依赖（可能需要几分钟）..."
        Update-Status "安装依赖中..." "Blue"
        $installCmd = "conda run -p `"$condaEnvPath`" pip install -r requirements.txt"
        Invoke-Expression $installCmd 2>&1 | ForEach-Object { Add-Log $_ }
        
        if ($LASTEXITCODE -ne 0) {
            throw "依赖安装失败"
        }
        Add-Log "✅ 依赖安装完成"
    }
    
    # 检查是否已经在运行
    if (Test-ApplicationProcess) {
        Add-Log "⚠️ 检测到应用已在运行中"
        Update-Status "运行中" "Green"
        return
    }
    
    # 创建必要的目录
    Add-Log "📁 检查并创建必要目录..."
    $dirs = @("data\history", "data\memory", "data\scenes", "static\images\cache")
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Add-Log "   ✅ 创建目录: $dir"
        }
    }
    
    # 检查配置文件
    Add-Log "⚙️ 检查配置文件..."
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Add-Log "   ✅ 已从模板创建配置文件 .env"
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
            Add-Log "   ✅ 已创建默认配置文件 .env"
        }
        Add-Log "   ⚠️ 请编辑 .env 文件配置您的API密钥" "WARNING"
    } else {
        Add-Log "   ✅ 配置文件已存在"
    }
    
    # 启动应用
    Add-Log "🚀 正在启动CABM应用..."
    Update-Status "启动应用中..." "Blue"
    $startFile = if (Test-Path "start.py") { "start.py" } else { "app.py" }
    $startCmd = "conda run -p `"$condaEnvPath`" python $startFile"
    
    # 后台启动应用
    Start-Process powershell -ArgumentList "-WindowStyle", "Minimized", "-Command", $startCmd -PassThru
    
    # 等待应用启动
    Add-Log "⏳ 等待应用初始化..."
    Start-Sleep -Seconds 3
    
    # 验证启动
    Add-Log "🔍 验证应用启动状态..."
    Update-Status "验证启动中..." "Blue"
    $maxRetries = 15
    for ($i = 0; $i -lt $maxRetries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5000" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Add-Log "🎉 应用启动成功！服务已可用" "SUCCESS"
                Update-Status "运行中" "Green"
                return
            }
        }
        catch {
            # 继续等待
        }
        
        Start-Sleep -Seconds 2
        Add-Log "   ⏳ 等待应用响应... ($($i+1)/$maxRetries)"
    }
    
    # 如果直接访问失败，检查进程
    if (Test-ApplicationProcess) {
        Add-Log "⚠️ 应用进程已启动，但服务可能需要更长时间初始化" "WARNING"
        Add-Log "💡 建议等待1-2分钟后再尝试访问" "INFO"
        Update-Status "启动中" "Yellow"
    } else {
        throw "应用启动失败，请检查日志"
    }
}

# Docker方式启动应用（极端情况使用）
function Start-DockerApplication {
    Add-Log "🐳 使用Docker方式启动应用..."
    
    # 检查Docker
    if (-not (Test-DockerStatus)) {
        Add-Log "❌ Docker未运行，正在尝试启动..."
        Update-Status "启动Docker中..." "Blue"
        $dockerPaths = @(
            "C:\Program Files\Docker\Docker\Docker Desktop.exe",
            "$env:USERPROFILE\AppData\Local\Docker\Docker Desktop.exe"
        )
        
        $dockerPath = $dockerPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($dockerPath) {
            Add-Log "🚀 启动Docker Desktop..."
            Start-Process -FilePath $dockerPath
            Add-Log "⏳ 等待Docker启动（可能需要1-2分钟）..."
            
            # 等待Docker启动
            for ($i = 0; $i -lt 30; $i++) {
                Start-Sleep -Seconds 2
                if (Test-DockerStatus) {
                    Add-Log "✅ Docker已启动"
                    break
                }
                if ($i % 5 -eq 0) {
                    Add-Log "   ⏳ Docker启动中... ($($i*2)秒)"
                }
                if ($i -eq 29) {
                    throw "Docker启动超时，请手动启动Docker Desktop"
                }
            }
        } else {
            throw "找不到Docker Desktop，请先安装Docker"
        }
    } else {
        Add-Log "✅ Docker已运行"
    }
    
    # 检查容器是否存在
    Add-Log "🔍 检查容器状态..."
    $containerExists = docker ps -a -f name=cabm-app --format "{{.Names}}" 2>$null
    if ($containerExists -eq "cabm-app") {
        Add-Log "📦 发现现有容器，正在启动..."
        Update-Status "启动容器中..." "Blue"
        docker start cabm-app 2>&1 | ForEach-Object { Add-Log $_ }
    } else {
        Add-Log "🏗️ 未发现容器，开始构建和部署..."
        Update-Status "构建应用中..." "Blue"
        if (Test-Path "deploy-docker.ps1") {
            Add-Log "📋 使用PowerShell部署脚本..."
            & ".\deploy-docker.ps1" "deploy" 2>&1 | ForEach-Object { Add-Log $_ }
        } elseif (Test-Path "deploy-docker.bat") {
            Add-Log "📋 使用批处理部署脚本..."
            cmd /c "deploy-docker.bat deploy" 2>&1 | ForEach-Object { Add-Log $_ }
        } else {
            throw "找不到部署脚本（deploy-docker.ps1 或 deploy-docker.bat）"
        }
    }
    
    # 验证启动
    Add-Log "🔍 验证容器状态..."
    Update-Status "验证启动中..." "Blue"
    Start-Sleep -Seconds 5
    if (Test-ContainerStatus) {
        Add-Log "🎉 Docker应用启动成功！" "SUCCESS"
        Update-Status "运行中" "Green"
    } else {
        throw "Docker容器启动失败，请检查Docker日志"
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
        Add-Log "应用未运行，请先启动应用" "WARNING"
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
    $result = [System.Windows.Forms.MessageBox]::Show("⚠️ 警告：这将删除当前目录下的所有文件和文件夹！`n`n确定要继续吗？", "确认完全卸载", "YesNo", "Warning")
    if ($result -eq "Yes") {
        # 二次确认
        $confirmResult = [System.Windows.Forms.MessageBox]::Show("❗ 最后确认：这是不可逆操作！`n`n将删除：$PWD 目录下的所有内容`n`n确定继续？", "最终确认", "YesNo", "Error")
        if ($confirmResult -eq "Yes") {
            Add-Log "开始完全卸载应用..."
            Update-Status "正在卸载..." "Red"
            Show-Progress $true
            
            try {
                # 停止应用
                Add-Log "正在停止所有相关进程..."
                Stop-Application
                
                # 删除Docker容器和镜像（如果存在）
                try {
                    Add-Log "清理Docker资源..."
                    docker stop cabm-app 2>$null
                    docker rm cabm-app 2>$null
                    docker rmi cabm:latest 2>$null
                    docker image prune -f 2>$null
                    Add-Log "Docker资源清理完成"
                }
                catch {
                    Add-Log "Docker清理跳过（可能未安装）"
                }
                
                # 等待一下确保进程完全停止
                Start-Sleep -Seconds 2
                
                # 获取当前目录
                $currentDir = Get-Location
                Add-Log "当前目录: $currentDir"
                
                # 删除当前目录下的所有文件和文件夹
                Add-Log "开始删除所有文件和文件夹..."
                
                # 先删除所有文件
                Get-ChildItem -Path $currentDir -File -Force | ForEach-Object {
                    try {
                        Remove-Item $_.FullName -Force
                        Add-Log "已删除文件: $($_.Name)"
                    }
                    catch {
                        Add-Log "删除文件失败: $($_.Name) - $($_.Exception.Message)" "WARNING"
                    }
                }
                
                # 再删除所有文件夹
                Get-ChildItem -Path $currentDir -Directory -Force | ForEach-Object {
                    try {
                        Remove-Item $_.FullName -Recurse -Force
                        Add-Log "已删除文件夹: $($_.Name)"
                    }
                    catch {
                        Add-Log "删除文件夹失败: $($_.Name) - $($_.Exception.Message)" "WARNING"
                    }
                }
                
                Add-Log "卸载完成！所有文件已删除" "SUCCESS"
                Update-Status "已完全卸载" "Gray"
                
                # 显示完成消息
                [System.Windows.Forms.MessageBox]::Show("✅ 卸载完成！`n`n所有文件和文件夹已删除。`n程序将在3秒后自动关闭。", "卸载完成", "OK", "Information")
                
                # 延迟关闭窗口
                $timer = New-Object System.Windows.Forms.Timer
                $timer.Interval = 3000
                $timer.Add_Tick({
                    $script:form.Close()
                })
                $timer.Start()
                
            }
            catch {
                Add-Log "卸载失败: $($_.Exception.Message)" "ERROR"
                Update-Status "卸载失败" "Red"
                [System.Windows.Forms.MessageBox]::Show("卸载过程中出现错误：`n$($_.Exception.Message)", "错误", "OK", "Error")
            }
            finally {
                Show-Progress $false
            }
        }
        else {
            Add-Log "用户取消了卸载操作"
        }
    }
    else {
        Add-Log "用户取消了卸载操作"
    }
}

# 主程序
function Start-GUI {
    try {
        # 创建表单
        $script:form = New-MainForm
        
        # 初始状态检查和欢迎信息
        Add-Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "INFO"
        Add-Log "🚀 CABM AI对话应用管理器 v2.0 已启动" "SUCCESS"
        Add-Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "INFO"
        Add-Log "✨ 欢迎使用现代化的CABM管理界面！" "INFO"
        Add-Log "�️ 高DPI优化已启用 - 缩放比例: $([Math]::Round($script:dpiScale * 100, 0))%" "INFO"
        Add-Log "�📋 正在检查系统状态..." "INFO"
        
        Get-ApplicationStatus
        
        Add-Log "✅ 管理器初始化完成，准备就绪" "SUCCESS"
        
        # 显示窗口
        [System.Windows.Forms.Application]::Run($script:form)
    }
    catch {
        [System.Windows.Forms.MessageBox]::Show("启动失败: $($_.Exception.Message)", "错误", "OK", "Error")
    }
}

# 启动GUI
Start-GUI

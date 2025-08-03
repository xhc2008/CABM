@echo off
:: 切换到脚本所在目录
cd /d %~dp0

:: 执行 PowerShell 脚本 build.ps1
powershell -ExecutionPolicy Bypass -File "build.ps1"

:: 暂停（可选：查看输出）
pause
@echo off
chcp 65001 >nul
title CABM - GUI管理器启动

echo ========================================
echo   CABM GUI管理器启动脚本
echo ========================================
echo.
echo  启动CABM GUI管理器...

echo.

:: 启动GUI
powershell -ExecutionPolicy Bypass -File "cabm-gui.ps1"

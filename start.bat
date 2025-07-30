@echo off
chcp 65001 > nul
echo Starting CABM application...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python not found. Please install Python and ensure it's in PATH
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import flask, requests, dotenv" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing dependencies...
    pip install flask requests python-dotenv
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if PyTorch is installed
echo Checking for PyTorch...
python -c "import torch" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo PyTorch not found.
    echo(
    echo Due to the deep learning required by the ASR module, Pytorch must be downloaded
    echo If your graphics card is good enough, you can install GPU version , visit https://pytorch.org/get-started/locally/
    echo If you have a CPU only, please input 'y' to install the CPU version of PyTorch.
    echo If you want to install the GPU version, please input 'n' and install it manually.
    echo(
    set /p install_cpu="Install CPU version of PyTorch? (y/n): "
    if /i "%install_cpu%"=="y" (
        echo Installing CPU version of PyTorch...
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
        if %ERRORLEVEL% neq 0 (
            echo Error: Failed to install PyTorch. Please install it manually.
            pause
            exit /b 1
        )
        echo PyTorch installed successfully.
    ) else (
        echo Please install the GPU version of PyTorch manually.
        pause
        exit /b 1
    )
)

REM Start the application
echo Starting application...
python start.py %*
if %ERRORLEVEL% neq 0 (
    echo Application failed to start
    pause
)

exit /b 0
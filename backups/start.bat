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

REM Start the application
echo Starting application...
python start.py %*
if %ERRORLEVEL% neq 0 (
    echo Application failed to start
    pause
)

exit /b 0
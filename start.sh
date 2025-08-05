#!/bin/bash

echo "正在启动CABM应用..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python，请安装Python 3"
    exit 1
fi

# 检查依赖是否安装
echo "正在检查依赖..."
python3 -c "import flask, requests, dotenv" &> /dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖..."
    pip3 install flask requests python-dotenv
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

# 启动应用
echo "正在启动应用..."
python3 start.py "$@"
if [ $? -ne 0 ]; then
    echo "应用启动失败"
    exit 1
fi

exit 0
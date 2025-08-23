# -*- coding: utf-8 -*-
"""
CABM 应用入口
"""
import os
import sys
from pathlib import Path
from flask import Flask
import mimetypes

# 计算项目根目录
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from services.config_service import config_service
from routes import register_blueprints

# 初始化配置
need_config = not config_service.initialize()
if not need_config:
    from services.chat_service import chat_service
    app_config = config_service.get_app_config()
    static_folder = str(project_root / app_config["static_folder"])
    template_folder = str(project_root / app_config["template_folder"])
    from services.ttsapi_service import ttsService
else:
    static_folder = str(project_root / "static")
    template_folder = str(project_root / "templates")

# 创建 Flask 实例
app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
app.project_root = project_root
# 注册蓝图
register_blueprints(app)
# app.py
if not need_config:
    from services.ttsapi_service import ttsService
    app.tts = ttsService()          # 挂到 app 上
else:
    app.tts = None
# MIME 类型
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')

# 运行入口
if __name__ == '__main__':
    if not need_config:
        chat_service.set_system_prompt("character")
        app.run(
            host=app_config["host"],
            port=app_config["port"],
            debug=app_config["debug"],
            use_reloader=app_config["debug"]
        )
    else:
        # 配置模式下，仅启动 web 配置页面，不初始化业务服务
        app.run(host="localhost", port=5000, debug=True)
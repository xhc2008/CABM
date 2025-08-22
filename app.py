"""CABM应用主文件（重构版）"""
import os
import sys
import mimetypes
from pathlib import Path
from flask import Flask

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service

# 初始化配置
need_config = not config_service.initialize()
if need_config:
    print("配置初始化失败，进入配置模式。请在网页填写环境变量。")

if not need_config:
    app_config = config_service.get_app_config()
    static_folder = app_config["static_folder"]
    template_folder = app_config["template_folder"]
else:
    static_folder = str(Path(__file__).resolve().parent / "static")
    template_folder = str(Path(__file__).resolve().parent / "templates")

# 查看migration文件是否存在
migration_folder = str(Path(__file__).resolve().parent / "migrations")
if not os.path.exists(migration_folder):
    print("旧版记忆开始迁移")
    import migrate_to_faiss
    import migrate_to_peewee
    done_faiss = migrate_to_faiss.main()
    done_peewee = migrate_to_peewee.main()
    if done_faiss and done_peewee:
        print("迁移成功")
    else:
        print("请前往tools\json2index尝试备用迁移")
    with open("migrations", "w") as f:
        f.close()

# 创建Flask应用
app = Flask(
    __name__,
    static_folder=static_folder,
    template_folder=template_folder
)

# 设置JavaScript模块的MIME类型
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')

# 加载并注册插件后端路由和前端资源
from utils.plugin import load_plugins, apply_backend_hooks, apply_frontend_hooks
plugin_folder = str(Path(__file__).resolve().parent / 'utils' / 'plugin')
load_plugins(plugin_folder)
apply_backend_hooks(app)
apply_frontend_hooks(lambda route, path: None)

# 注册各功能蓝图
from routes.chat_routes import chat_bp
from routes.character_routes import character_bp
from routes.story_routes import story_bp
from routes.config_routes import config_bp
from routes.tts_routes import tts_bp

app.register_blueprint(chat_bp)
app.register_blueprint(character_bp)
app.register_blueprint(story_bp)
app.register_blueprint(config_bp)
app.register_blueprint(tts_bp)


# 设置系统提示词，使用角色提示词
if not need_config:
    from services.chat_service import chat_service
    chat_service.set_system_prompt("character")

if __name__ == '__main__':
    if not need_config:
        app.debug = app_config["debug"]
        app.run(
            host=app_config["host"],
            port=app_config["port"],
            debug=app_config["debug"],
            use_reloader=app_config["debug"]
        )
    else:
        app.run()

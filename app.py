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

# 检查是否需要执行数据迁移
if not os.path.exists("transfer"):
    if os.path.exists("data/memory"):
        print("检测到旧版数据，开始执行数据迁移...")
        try:
            import migrate_to_faiss
            success1 = migrate_to_faiss.main()
            if success1:
                print("FAISS迁移完成")
            else:
                print("FAISS迁移失败")
        except Exception as e:
            print(f"FAISS迁移出错: {e}")
        
        try:
            import migrate_to_peewee
            success2 = migrate_to_peewee.main()
            if success2:
                print("Peewee迁移完成")
            else:
                print("Peewee迁移失败")
        except Exception as e:
            print(f"Peewee迁移出错: {e}")
        
        # 创建迁移标记文件
        with open("transfer", "w") as f:
            f.write("Data migration completed")
        print("数据迁移标记已创建")
    else:
        # 如果没有旧数据，也创建迁移标记文件
        with open("transfer", "w") as f:
            f.write("No old data to migrate")
        print("无旧数据需要迁移，已创建标记文件")


if not need_config:
    app_config = config_service.get_app_config()
    static_folder = app_config["static_folder"]
    template_folder = app_config["template_folder"]
else:
    static_folder = str(Path(__file__).resolve().parent / "static")
    template_folder = str(Path(__file__).resolve().parent / "templates")

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

# 创建一个用于注册插件静态文件的函数
def register_plugin_static(route, path):
    # 为插件静态文件创建路由
    def serve_plugin_static():
        import os
        from flask import send_file
        if os.path.exists(path):
            return send_file(path)
        else:
            from flask import abort
            abort(404)
    
    app.add_url_rule(route, endpoint=route, view_func=serve_plugin_static)

apply_backend_hooks(app)
apply_frontend_hooks(register_plugin_static)

# 注册各功能蓝图
from routes.chat_routes import chat_bp
from routes.character_routes import character_bp
from routes.story_routes import story_bp
from routes.config_routes import config_bp
from routes.tts_routes import tts_bp
from routes.settings_routes import settings_bp

app.register_blueprint(chat_bp)
app.register_blueprint(character_bp)
app.register_blueprint(story_bp)
app.register_blueprint(config_bp)
app.register_blueprint(tts_bp)
app.register_blueprint(settings_bp)


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

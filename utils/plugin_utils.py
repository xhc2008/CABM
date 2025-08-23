import os

def get_plugin_inject_scripts():
    """收集所有插件的inject.js脚本"""
    plugin_inject_scripts = []
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        static_plugin_root = os.path.join(project_root, 'static', 'plugin')
        if os.path.exists(static_plugin_root):
            for plugin_name in os.listdir(static_plugin_root):
                plugin_dir = os.path.join(static_plugin_root, plugin_name)
                if os.path.isdir(plugin_dir):
                    inject_js = os.path.join(plugin_dir, 'inject.js')
                    if os.path.exists(inject_js):
                        plugin_inject_scripts.append(f'/static/plugin/{plugin_name}/inject.js')
    except Exception as e:
        print(f"收集插件注入脚本时出错: {e}")
    return plugin_inject_scripts
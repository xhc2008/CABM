from utils.plugin import BasePlugin
import os
import json
from flask import Blueprint, jsonify, render_template, request
import yaml

class PluginManagerPlugin(BasePlugin):
    name = "Plugin Manager"

    def register_frontend(self, register_func):
        """注册前端资源"""
        # 注册前端JS和CSS文件
        plugin_dir = os.path.dirname(__file__)
        static_dir = os.path.join(plugin_dir, 'static')
        
        if os.path.exists(static_dir):
            for root, dirs, files in os.walk(static_dir):
                for file in files:
                    relative_path = os.path.relpath(os.path.join(root, file), static_dir)
                    route = f'/static/plugin/plugin_manager/{relative_path}'.replace('\\', '/')
                    file_path = os.path.join(root, file)
                    register_func(route, file_path)

    def register_backend(self, app):
        """注册后端路由"""
        plugin_manager_bp = Blueprint('plugin_manager', __name__, 
                                     template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                                     static_folder=os.path.join(os.path.dirname(__file__), 'static'))
        
        @plugin_manager_bp.route('/plugins')
        def plugin_list():
            """插件列表页面"""
            return render_template('plugin_manager/index.html')
        
        @plugin_manager_bp.route('/api/plugins')
        def get_plugins():
            """获取插件列表API"""
            try:
                # 获取所有插件目录
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                plugins = []
                
                for item in os.listdir(plugin_root):
                    item_path = os.path.join(plugin_root, item)
                    if os.path.isdir(item_path) and not item.startswith('_') and item != 'plugin_manager':
                        # 判断插件是否被禁用（通过目录名是否有.nl后缀）
                        is_disabled = item.endswith('.nl')
                        # 获取干净的插件ID（移除.nl后缀）
                        clean_item = item.rstrip('.nl') if item.endswith('.nl') else item
                        
                        plugin_info = {
                            'id': item,  # 实际目录名（包括.nl后缀）
                            'name': clean_item,  # 显示名称
                            'description': '',
                            'version': '',
                            'author': '',
                            'disabled': is_disabled
                        }
                        
                        # 尝试读取插件配置文件
                        config_file = os.path.join(item_path, 'plugin.yaml')
                        if os.path.exists(config_file):
                            try:
                                with open(config_file, 'r', encoding='utf-8') as f:
                                    config = yaml.safe_load(f)
                                    plugin_info['name'] = config.get('name', clean_item)
                                    plugin_info['description'] = config.get('description', '')
                                    plugin_info['version'] = config.get('version', '')
                                    plugin_info['author'] = config.get('author', '')
                            except Exception as e:
                                print(f"读取插件 {item} 配置文件失败: {e}")
                        
                        plugins.append(plugin_info)
                
                return jsonify(plugins)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @plugin_manager_bp.route('/api/plugins/<plugin_id>/toggle', methods=['POST'])
        def toggle_plugin(plugin_id):
            """切换插件启用/禁用状态"""
            try:
                data = request.get_json()
                enabled = data.get('enabled', True)
                
                # 获取插件根目录
                plugin_root = os.path.dirname(os.path.dirname(__file__))
                
                # 查找实际的插件目录名（精确匹配）
                actual_plugin_dir = None
                for item in os.listdir(plugin_root):
                    if item == plugin_id and os.path.isdir(os.path.join(plugin_root, item)):
                        actual_plugin_dir = item
                        break
                
                if not actual_plugin_dir:
                    return jsonify({'success': False, 'message': f'未找到插件: {plugin_id}'}), 404
                
                # 构建完整路径
                old_path = os.path.join(plugin_root, actual_plugin_dir)
                
                if enabled:
                    # 启用插件：移除.nl后缀
                    if actual_plugin_dir.endswith('.nl'):
                        new_name = actual_plugin_dir.rstrip('.nl')
                        new_path = os.path.join(plugin_root, new_name)
                        os.rename(old_path, new_path)
                        return jsonify({'success': True, 'message': '插件已启用'})
                    else:
                        return jsonify({'success': True, 'message': '插件已经是启用状态'})
                else:
                    # 禁用插件：添加.nl后缀
                    if not actual_plugin_dir.endswith('.nl'):
                        new_name = actual_plugin_dir + '.nl'
                        new_path = os.path.join(plugin_root, new_name)
                        os.rename(old_path, new_path)
                        return jsonify({'success': True, 'message': '插件已禁用'})
                    else:
                        return jsonify({'success': True, 'message': '插件已经是禁用状态'})
                        
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
        
        app.register_blueprint(plugin_manager_bp, url_prefix='/plugin-manager')

# 创建插件实例
plugin = PluginManagerPlugin()
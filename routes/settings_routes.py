from flask import Blueprint, render_template, jsonify, request
from services.chat_service import chat_service
from utils.plugin_utils import get_plugin_inject_scripts
import traceback
from services.settings_service import settings_service
from services.memory_service import migrate_memory_data

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings_page():
    """设置页面"""
    plugin_inject_scripts = get_plugin_inject_scripts()
    return render_template('settings.html', plugin_inject_scripts=plugin_inject_scripts)

@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """获取当前设置"""
    try:
        settings = settings_service.get_all_settings()
        return jsonify(settings)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/settings', methods=['POST'])
def save_settings():
    """保存设置"""
    try:
        # 获取请求数据
        new_settings = request.get_json()
        
        if not new_settings:
            return jsonify({'success': False, 'error': '无效的设置数据'}), 400
        
        # 获取当前设置以检测存储类型变化
        current_settings = settings_service.get_all_settings()
        current_storage_type = current_settings.get('storage', {}).get('type', 'json')
        new_storage_type = new_settings.get('storage', {}).get('type', 'json')
        
        # 检测存储类型是否发生变化
        storage_type_changed = current_storage_type != new_storage_type
        
        # 更新设置
        if settings_service.update_settings(new_settings):
            # 如果存储类型发生变化，执行数据迁移
            if storage_type_changed:
                try:
                    print(f"检测到存储类型变化: {current_storage_type} -> {new_storage_type}")
                    print("开始执行数据迁移...")
                    
                    # 执行数据迁移
                    migrate_memory_data(current_storage_type, new_storage_type)
                    
                    print("数据迁移完成")
                    return jsonify({
                        'success': True, 
                        'message': f'设置已保存，数据已从 {current_storage_type} 迁移到 {new_storage_type}'
                    })
                except Exception as migrate_error:
                    print(f"数据迁移失败: {str(migrate_error)}")
                    traceback.print_exc()
                    return jsonify({
                        'success': False, 
                        'error': f'设置已保存，但数据迁移失败: {str(migrate_error)}'
                    }), 500
            else:
                return jsonify({'success': True, 'message': '设置已保存'})
        else:
            return jsonify({'success': False, 'error': '设置保存失败'}), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

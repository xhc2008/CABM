# -*- coding: utf-8 -*-
"""
配置页 & 退出
"""
from pathlib import Path
from flask import Blueprint, request, render_template, jsonify
import os
import sys

# 动态计算项目根目录
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

bp = Blueprint('config', __name__, url_prefix='')

def load_env_example_defaults():
    """从 .env.example 文件加载默认配置"""
    env_example_path = project_root / '.env.example'
    defaults = {}
    
    try:
        with open(env_example_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        defaults[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not load .env.example: {e}")
    
    return defaults

@bp.route('/config/simple', methods=['POST'])
def save_simple_config():
    """简易配置：使用单个API密钥配置所有服务"""
    api_key = request.form.get('simple_api_key', '').strip()
    
    if not api_key:
        return '''<div style="padding:2em;text-align:center;font-size:1.2em;color:red;">请填写 API 密钥！</div>'''
    
    # 从 .env.example 加载默认配置
    defaults = load_env_example_defaults()
    
    # 使用 .env.example 的默认值，但将所有 API 密钥替换为用户提供的密钥
    env_vars = defaults.copy()
    
    # 将用户提供的 API 密钥应用到所有需要密钥的字段
    api_key_fields = [
        'CHAT_API_KEY',
        'IMAGE_API_KEY', 
        'OPTION_API_KEY',
        'MEMORY_API_KEY',
        'TTS_SERVICE_API_KEY'
    ]
    
    for field in api_key_fields:
        env_vars[field] = api_key
    
    env_lines = [f'{k}={v}' for k, v in env_vars.items()]
    env_content = '\n'.join(env_lines)
    env_path = project_root / '.env'
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        return '''<div style="padding:2em;text-align:center;font-size:1.2em;color:green;">✅ 简易配置已保存！<br>使用默认推荐设置，API密钥已应用到所有服务。<br><br>请重新打开本程序谢谢!</div>'''
    except Exception as e:
        return f'''<div style="padding:2em;text-align:center;font-size:1.2em;color:red;">❌ 保存配置时出错：{str(e)}</div>'''

@bp.route('/config', methods=['POST'])
def save_config():
    env_vars = {
        'CHAT_API_BASE_URL': request.form.get('chat_api_base_url', ''),
        'CHAT_API_KEY': request.form.get('chat_api_key', ''),
        'CHAT_MODEL': request.form.get('chat_model', ''),
        'IMAGE_API_BASE_URL': request.form.get('image_api_base_url', ''),
        'IMAGE_API_KEY': request.form.get('image_api_key', ''),
        'IMAGE_MODEL': request.form.get('image_model', ''),
        'OPTION_API_BASE_URL': request.form.get('option_api_base_url', ''),
        'OPTION_API_KEY': request.form.get('option_api_key', ''),
        'OPTION_MODEL': request.form.get('option_model', ''),
        'MEMORY_API_BASE_URL': request.form.get('memory_api_base_url', ''),
        'MEMORY_API_KEY': request.form.get('memory_api_key', ''),
        'EMBEDDING_MODEL': request.form.get('embedding_model', ''),
        'RERANKER_MODEL': request.form.get('reranker_model', ''),
        'TTS_SERVICE_URL_GPTSoVITS': request.form.get('tts_service_url_gptsovits', ''),
        'TTS_SERVICE_URL_SiliconFlow': request.form.get('tts_service_url_siliconflow', ''),
        'TTS_SERVICE_API_KEY': request.form.get('tts_service_api_key', ''),
        'TTS_SERVICE_METHOD': request.form.get('tts_service_method', ''),
        'DEBUG': request.form.get('debug', 'False'),
        'PORT': request.form.get('port', '5000'),
        'HOST': request.form.get('host', 'localhost'),
    }
    env_lines = [f'{k}={v}' for k, v in env_vars.items()]
    env_content = '\n'.join(env_lines)
    env_path = project_root / '.env'
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    return '''<div style="padding:2em;text-align:center;font-size:1.2em;">配置已保存！<br>请重新打开本程序谢谢!</div>'''

@bp.route('/api/exit', methods=['POST'])
def exit_app():
    try:
        os._exit(0)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
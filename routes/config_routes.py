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
from flask import Blueprint, render_template, request, jsonify
from pathlib import Path
import traceback
from services.config_service import config_service
from services.chat_service import chat_service

config_bp = Blueprint('config', __name__)

@config_bp.route('/config', methods=['POST'])
def save_config():
    try:
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
        env_path = Path(__file__).resolve().parent.parent / '.env'
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        return '''<div style="padding:2em;text-align:center;font-size:1.2em;">配置已保存！<br>请重新打开本程序谢谢!</div>'''
    except Exception as e:
        traceback.print_exc()
        return '''<div style="padding:2em;text-align:center;font-size:1.2em;color:red;">配置保存失败！</div>'''

@config_bp.route('/api/clear', methods=['POST'])
def clear_history():
    try:
        chat_service.clear_history()
        prompt_type = request.json.get('prompt_type', 'character')
        chat_service.set_system_prompt(prompt_type)
        return jsonify({'success': True, 'message': '对话历史已清空'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/')
def home():
    need_config = not config_service.initialize()
    if need_config:
        return render_template('config.html')
    return render_template('index.html')

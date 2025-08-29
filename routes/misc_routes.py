# -*- coding: utf-8 -*-
"""
杂项路由
"""
import sys
from pathlib import Path
from flask import Blueprint, send_from_directory, request, jsonify, send_file, current_app, render_template
from io import BytesIO
import sys
# 动态计算项目根目录
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.config_service import config_service
need_config = not config_service.initialize()
if not need_config:
    from services.ttsapi_service import ttsService as tts


bp = Blueprint('misc', __name__, url_prefix='')
@bp.route('/data/images/<path:filename>')
def serve_character_image(filename):
    return send_from_directory(str(project_root / 'data' / 'images'), filename)

@bp.route('/data/saves/<path:filename>')
def serve_story_file(filename):
    return send_from_directory(str(project_root / 'data' / 'saves'), filename)

@bp.route('/static/images/backgrounds/<path:filename>')
def serve_background_image(filename):
    return send_from_directory(str(project_root / 'data' / 'backgrounds'), filename)

@bp.route('/api/tts', methods=['POST'])
def serve_tts():
    # 检查TTS是否启用（从前端传递的参数或默认启用）
    data = request.get_json()
    tts_enabled = data.get("enabled", True)  # 默认启用，兼容旧版本
    
    if not tts_enabled:
        return jsonify({"error": "TTS功能已关闭"}), 400
    
    tts = current_app.tts
    if tts is None or not tts.running():
        return jsonify({"error": "语音合成服务未启用/连接失败"}), 400
    
    text = data.get("text", "").strip()
    role = data.get("role", "AI助手")
    if not text:
        return jsonify({"error": "文本为空"}), 400
    try:
        audio_bytes = tts.get_tts(text, role)
        if not audio_bytes:
            return jsonify({"error": "TTS生成失败"}), 500
        audio_io = BytesIO(audio_bytes)
        audio_io.seek(0)
        return send_file(audio_io, mimetype='audio/wav', as_attachment=False, download_name=None)
    except Exception as e:
        return jsonify({"error": "语音合成失败"}), 500

@bp.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html')

@bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')



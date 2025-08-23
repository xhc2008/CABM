# -*- coding: utf-8 -*-
"""
杂项路由：/data/images、/data/saves、/api/tts 等
"""
from pathlib import Path
from flask import Blueprint, send_from_directory, request, jsonify, send_file, current_app
from io import BytesIO
import sys

project_root = Path(__file__).resolve().parent.parent  # 改为三级父目录
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

@bp.route('/api/tts', methods=['POST'])
def serve_tts():
    tts = current_app.tts
    if tts is None or not tts.running():
        return jsonify({"error": "语音合成服务未启用/连接失败"}), 400
    data = request.get_json()
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
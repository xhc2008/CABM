from flask import Blueprint, jsonify, request, send_file
from io import BytesIO
import traceback
from services.ttsapi_service import ttsService

tts_bp = Blueprint('tts', __name__)

tts = None  # 在需要时初始化

@tts_bp.route('/api/tts', methods=['POST'])
def serve_tts():
    global tts
    if tts is None:
        tts = ttsService()
    if not tts.running():
        return jsonify({"error": "语音合成服务未启用/连接失败"}), 400
    data = request.get_json()
    text = data.get("text", "").strip()
    role = data.get("role", "AI助手")
    print(f"请求TTS: 角色={role}, 文本={text}")
    if not text:
        return jsonify({"error": "文本为空"}), 400
    try:
        audio_bytes = tts.get_tts(text, role)
        if not audio_bytes:
            return jsonify({"error": "TTS生成失败"}), 500
        audio_io = BytesIO(audio_bytes)
        audio_io.seek(0)
        return send_file(
            audio_io,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=None
        )
    except Exception as e:
        print(f"TTS error: {e}")
        return jsonify({"error": "语音合成失败"}), 500

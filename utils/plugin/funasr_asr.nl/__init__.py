import os
import logging
from flask import request, jsonify
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from utils.plugin import BasePlugin

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logger = logging.getLogger(__name__)
_model_instance = None

def get_asr_model():
    global _model_instance
    if _model_instance is None:
        logger.info("正在加载 FunASR 模型 'iic/SenseVoiceSmall'...")
        try:
            _model_instance = AutoModel(
                model="iic/SenseVoiceSmall",
                vad_model="fsmn-vad",
                vad_kwargs={"max_single_segment_time": 30000},
                device="cpu",
            )
            logger.info("FunASR 模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise RuntimeError(f"无法初始化 ASR 模型: {e}")
    return _model_instance

def transcribe_audio(audio_path: str) -> str:
    model = get_asr_model()
    try:
        logger.info(f"开始识别音频: {audio_path}")
        res = model.generate(
            input=audio_path,
            cache={},
            language="auto",
            use_itn=True,
            batch_size_s=60,
            merge_vad=True,
            merge_length_s=15,
        )
        raw_text = res[0]["text"]
        final_text = rich_transcription_postprocess(raw_text)
        logger.info(f"识别完成: {final_text}")
        return final_text.strip()
    except Exception as e:
        logger.error(f"识别失败 {audio_path}: {e}")
        raise

def convert_to_16k_wav(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio_16k = audio.set_frame_rate(16000).set_channels(1)
    audio_16k.export(output_path, format="wav")
    return output_path


class FunASRPlugin(BasePlugin):
    name = "FunASR语音识别"

    def register_frontend(self, register_func):
        # 注册inject.js用于自动注入toggleRecording覆盖
        inject_path = os.path.join(os.path.dirname(__file__), 'inject.js')
        register_func('/static/plugin/funasr_asr/inject.js', inject_path)
    def register_backend(self, app):
        @app.route('/api/mic', methods=['POST'])
        def mic_transcribe():
            if 'audio' not in request.files:
                return jsonify({'error': '缺少音频文件'}), 400
            file = request.files['audio']
            if file.filename == '':
                return jsonify({'error': '未选择文件'}), 400
            filename = secure_filename(file.filename)
            temp_input = os.path.join(UPLOAD_FOLDER, filename)
            wav_path = os.path.join(UPLOAD_FOLDER, "temp_recording.wav")
            try:
                file.save(temp_input)
                convert_to_16k_wav(temp_input, wav_path)
                text = transcribe_audio(wav_path)
                return jsonify({'text': text})
            except Exception as e:
                return jsonify({'error': '语音识别失败', 'detail': str(e)}), 500
            finally:
                if os.path.exists(temp_input):
                    os.remove(temp_input)
                if os.path.exists(wav_path):
                    os.remove(wav_path)

plugin = FunASRPlugin()

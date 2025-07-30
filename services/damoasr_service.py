# services/damoasr_services/asr_engine.py

from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 全局模型实例（延迟加载）
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
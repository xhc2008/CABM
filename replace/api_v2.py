
import json
import os
import sys
import traceback
from typing import Generator
import logging
import torch
from pathlib import Path
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline

now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append("%s/GPT_SoVITS" % (now_dir))

import argparse
import subprocess
import wave
import signal
import numpy as np
import soundfile as sf
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import FastAPI, UploadFile, File
import uvicorn
from io import BytesIO
from tools.i18n.i18n import I18nAuto
from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config
from GPT_SoVITS.TTS_infer_pack.text_segmentation_method import get_method_names as get_cut_method_names
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 设置日志
logger = logging.getLogger(__name__)

# print(sys.path)
i18n = I18nAuto()
cut_method_names = get_cut_method_names()

# BERT情感分析相关配置
class EmotionAnalyzer:
    def __init__(self):
        self.bert_models: dict = {}
        self.bert_tokenizers: dict = {}
        self.sentiment_analyzers: dict = {}
        
        self.emotion_map = {
            0: "高兴", 1: "悲伤", 2: "愤怒", 3: "惊讶", 4: "恐惧", 
            5: "厌恶", 6: "中性", 7: "害羞", 8: "兴奋", 9: "舒适",
            10: "紧张", 11: "爱慕", 12: "委屈", 13: "骄傲", 14: "困惑"
        }
        
        # 不再在初始化时加载所有模型，而是按需加载
        logger.info("情感分析器初始化完成，将按需加载BERT模型")
    
    def _load_bert_model_for_role(self, role_path: Path, role_name: str) -> bool:
        """加载指定角色的BERT情感分析模型"""
        try:
            # 检查角色目录下是否有BERT模型
            bert_path = role_path / "BERT"
            if not bert_path.exists():
                logger.warning(f"角色 '{role_name}' 的BERT模型路径不存在: {bert_path}")
                return False
            
            logger.info(f"正在加载{role_name}的BERT模型: {bert_path}")
            
            # 加载tokenizer和模型
            tokenizer = BertTokenizer.from_pretrained(str(bert_path))
            model = BertForSequenceClassification.from_pretrained(str(bert_path))
            
            # 创建情感分析pipeline
            analyzer = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                framework="pt",
                device="cuda" if torch.cuda.is_available() else "cpu"
            )
            
            # 存储到对应的字典中
            self.bert_tokenizers[role_name] = tokenizer
            self.bert_models[role_name] = model
            self.sentiment_analyzers[role_name] = analyzer
            
            logger.info(f"✅ {role_name}的BERT模型加载成功，使用设备: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
            return True
            
        except Exception as e:
            logger.error(f"❌ {role_name}的BERT模型加载失败: {e}")
            return False
    
    def predict_emotion(self, text: str, role: str = "default", role_path: Path = None) -> str:
        """预测文本情感，返回情感标签"""
        # 如果角色还没有加载BERT模型，尝试加载
        if role not in self.sentiment_analyzers and role_path:
            self._load_bert_model_for_role(role_path, role)
        
        # 检查该role是否有对应的情感分析器
        if role not in self.sentiment_analyzers:
            logger.warning(f"BERT模型未加载或role '{role}' 不存在，使用默认中性情感")
            return "中性"
        
        try:
            if not text.strip():
                return "中性"
            
            analyzer = self.sentiment_analyzers[role]
            result = analyzer(text)
            
            # 确保result是列表格式
            if isinstance(result, list) and len(result) > 0:
                first_result = result[0]
                if isinstance(first_result, dict) and 'label' in first_result:
                    label = int(first_result['label'].split('_')[-1])
                    emotion = self.emotion_map.get(label, "中性")
                    score = first_result.get('score', 0.0)
                    
                    logger.info(f"情感分析 ({role}): '{text[:50]}...' -> {emotion} (置信度: {score:.4f})")
                    return emotion
            
            logger.warning(f"情感分析结果格式异常，使用默认中性情感")
            return "中性"
            
        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            return "中性"
    
    def get_ref_audio_path(self, emotion: str, role: str = "default", role_path: Path = None) -> str:
        """根据情感和角色获取参考音频路径"""
        if not role_path:
            logger.warning(f"未提供角色路径，无法查找参考音频")
            return None
        
        # 构建参考音频路径：{role_path}/refAudio/{emotion}/
        role_emotion_dir = role_path / "refAudio" / emotion
        if not role_emotion_dir.exists():
            logger.warning(f"角色情感目录不存在: {role_emotion_dir}")
            # 尝试使用中性情感作为备选
            role_neutral_dir = role_path / "refAudio" / "中性"
            if not role_neutral_dir.exists():
                logger.error(f"角色中性情感目录也不存在: {role_neutral_dir}")
                return None
            role_emotion_dir = role_neutral_dir
        
        # 查找该情感目录下的第一个wav文件
        for wav_file in role_emotion_dir.glob("*.wav"):
            return str(wav_file)
        
        logger.warning(f"在角色情感目录 {role_emotion_dir} 中未找到wav文件")
        return None
    
    def get_emotion_status(self) -> dict:
        """获取情感分析模型状态"""
        return {
            "bert_loaded": len(self.sentiment_analyzers) > 0,
            "loaded_roles": list(self.sentiment_analyzers.keys()),
            "total_loaded": len(self.sentiment_analyzers),
            "device": "CUDA" if torch.cuda.is_available() else "CPU",
            "available_emotions": list(self.emotion_map.values())
        }

# 初始化情感分析器
emotion_analyzer = EmotionAnalyzer()

parser = argparse.ArgumentParser(description="GPT-SoVITS api")
parser.add_argument("-c", "--tts_config", type=str, default="GPT_SoVITS/configs/tts_infer.yaml", help="tts_infer路径")
parser.add_argument("-a", "--bind_addr", type=str, default="127.0.0.1", help="default: 127.0.0.1")
parser.add_argument("-p", "--port", type=int, default="9880", help="default: 9880")
args = parser.parse_args()
config_path = args.tts_config
# device = args.device
port = args.port
host = args.bind_addr
argv = sys.argv

if config_path in [None, ""]:
    config_path = "GPT-SoVITS/configs/tts_infer.yaml"

tts_config = TTS_Config(config_path)
print(tts_config)
tts_pipeline = TTS(tts_config)

gpt = "default"
sovits = "default"

APP = FastAPI()
class TTS_Request(BaseModel):
    text: str = None
    text_lang: str = None
    ref_audio_path: str = None
    aux_ref_audio_paths: list = None
    prompt_lang: str = None
    prompt_text: str = ""
    top_k:int = 5
    top_p:float = 1
    temperature:float = 1
    text_split_method:str = "cut5"
    batch_size:int = 1
    batch_threshold:float = 0.75
    split_bucket:bool = True
    speed_factor:float = 1.0
    fragment_interval:float = 0.3
    seed:int = -1
    media_type:str = "wav"
    streaming_mode:bool = False
    parallel_infer:bool = True
    repetition_penalty:float = 1.35

class TTS_Request_role(BaseModel):
    text: str = None
    role: str = None
    temperature:float = 1
### modify from https://github.com/RVC-Boss/GPT-SoVITS/pull/894/files
def pack_ogg(io_buffer:BytesIO, data:np.ndarray, rate:int):
    with sf.SoundFile(io_buffer, mode='w', samplerate=rate, channels=1, format='ogg') as audio_file:
        audio_file.write(data)
    return io_buffer


def pack_raw(io_buffer:BytesIO, data:np.ndarray, rate:int):
    io_buffer.write(data.tobytes())
    return io_buffer


def pack_wav(io_buffer:BytesIO, data:np.ndarray, rate:int):
    io_buffer = BytesIO()
    sf.write(io_buffer, data, rate, format='wav')
    return io_buffer

def pack_aac(io_buffer:BytesIO, data:np.ndarray, rate:int):
    process = subprocess.Popen([
        'ffmpeg',
        '-f', 's16le',  # 输入16位有符号小端整数PCM
        '-ar', str(rate),  # 设置采样率
        '-ac', '1',  # 单声道
        '-i', 'pipe:0',  # 从管道读取输入
        '-c:a', 'aac',  # 音频编码器为AAC
        '-b:a', '192k',  # 比特率
        '-vn',  # 不包含视频
        '-f', 'adts',  # 输出AAC数据流格式
        'pipe:1'  # 将输出写入管道
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _ = process.communicate(input=data.tobytes())
    io_buffer.write(out)
    return io_buffer

def pack_audio(io_buffer:BytesIO, data:np.ndarray, rate:int, media_type:str):
    if media_type == "ogg":
        io_buffer = pack_ogg(io_buffer, data, rate)
    elif media_type == "aac":
        io_buffer = pack_aac(io_buffer, data, rate)
    elif media_type == "wav":
        io_buffer = pack_wav(io_buffer, data, rate)
    else:
        io_buffer = pack_raw(io_buffer, data, rate)
    io_buffer.seek(0)
    return io_buffer



# from https://huggingface.co/spaces/coqui/voice-chat-with-mistral/blob/main/app.py
def wave_header_chunk(frame_input=b"", channels=1, sample_width=2, sample_rate=32000):
    # This will create a wave header then append the frame input
    # It should be first on a streaming wav file
    # Other frames better should not have it (else you will hear some artifacts each chunk start)
    wav_buf = BytesIO()
    with wave.open(wav_buf, "wb") as vfout:
        vfout.setnchannels(channels)
        vfout.setsampwidth(sample_width)
        vfout.setframerate(sample_rate)
        vfout.writeframes(frame_input)

    wav_buf.seek(0)
    return wav_buf.read()


def handle_control(command:str):
    if command == "restart":
        os.execl(sys.executable, sys.executable, *argv)
    elif command == "exit":
        os.kill(os.getpid(), signal.SIGTERM)
        exit(0)


def check_params(req:dict):
    text:str = req.get("text", "")
    text_lang:str = req.get("text_lang", "")
    ref_audio_path:str = req.get("ref_audio_path", "")
    streaming_mode:bool = req.get("streaming_mode", False)
    media_type:str = req.get("media_type", "wav")
    prompt_lang:str = req.get("prompt_lang", "")
    text_split_method:str = req.get("text_split_method", "cut5")

    if ref_audio_path in [None, ""]:
        return JSONResponse(status_code=400, content={"message": "ref_audio_path is required"})
    if text in [None, ""]:
        return JSONResponse(status_code=400, content={"message": "text is required"})
    if (text_lang in [None, ""]) :
        return JSONResponse(status_code=400, content={"message": "text_lang is required"})
    elif text_lang.lower() not in tts_config.languages:
        return JSONResponse(status_code=400, content={"message": f"text_lang: {text_lang} is not supported in version {tts_config.version}"})
    if (prompt_lang in [None, ""]) :
        return JSONResponse(status_code=400, content={"message": "prompt_lang is required"})
    elif prompt_lang.lower() not in tts_config.languages:
        return JSONResponse(status_code=400, content={"message": f"prompt_lang: {prompt_lang} is not supported in version {tts_config.version}"})
    if media_type not in ["wav", "raw", "ogg", "aac"]:
        return JSONResponse(status_code=400, content={"message": f"media_type: {media_type} is not supported"})
    elif media_type == "ogg" and  not streaming_mode:
        return JSONResponse(status_code=400, content={"message": "ogg format is not supported in non-streaming mode"})
    
    if text_split_method not in cut_method_names:
        return JSONResponse(status_code=400, content={"message": f"text_split_method:{text_split_method} is not supported"})

    return None

async def tts_handle(req:dict):
    """
    Text to speech handler.
    
    Args:
        req (dict): 
            {
                "text": "",                   # str.(required) text to be synthesized
                "text_lang: "",               # str.(required) language of the text to be synthesized
                "ref_audio_path": "",         # str.(required) reference audio path
                "aux_ref_audio_paths": [],    # list.(optional) auxiliary reference audio paths for multi-speaker synthesis
                "prompt_text": "",            # str.(optional) prompt text for the reference audio
                "prompt_lang": "",            # str.(required) language of the prompt text for the reference audio
                "top_k": 5,                   # int. top k sampling
                "top_p": 1,                   # float. top p sampling
                "temperature": 1,             # float. temperature for sampling
                "text_split_method": "cut5",  # str. text split method, see text_segmentation_method.py for details.
                "batch_size": 1,              # int. batch size for inference
                "batch_threshold": 0.75,      # float. threshold for batch splitting.
                "split_bucket: True,          # bool. whether to split the batch into multiple buckets.
                "speed_factor":1.0,           # float. control the speed of the synthesized audio.
                "fragment_interval":0.3,      # float. to control the interval of the audio fragment.
                "seed": -1,                   # int. random seed for reproducibility.
                "media_type": "wav",          # str. media type of the output audio, support "wav", "raw", "ogg", "aac".
                "streaming_mode": False,      # bool. whether to return a streaming response.
                "parallel_infer": True,       # bool.(optional) whether to use parallel inference.
                "repetition_penalty": 1.35    # float.(optional) repetition penalty for T2S model.          
            }
    returns:
        StreamingResponse: audio stream response.
    """
    
    streaming_mode = req.get("streaming_mode", False)
    return_fragment = req.get("return_fragment", False)
    media_type = req.get("media_type", "wav")

    check_res = check_params(req)
    if check_res is not None:
        return check_res

    if streaming_mode or return_fragment:
        req["return_fragment"] = True
    
    try:
        tts_generator=tts_pipeline.run(req)
        
        if streaming_mode:
            def streaming_generator(tts_generator:Generator, media_type:str):
                if media_type == "wav":
                    yield wave_header_chunk()
                    media_type = "raw"
                for sr, chunk in tts_generator:
                    yield pack_audio(BytesIO(), chunk, sr, media_type).getvalue()
            # _media_type = f"audio/{media_type}" if not (streaming_mode and media_type in ["wav", "raw"]) else f"audio/x-{media_type}"
            return StreamingResponse(streaming_generator(tts_generator, media_type, ), media_type=f"audio/{media_type}")
    
        else:
            sr, audio_data = next(tts_generator)
            audio_data = pack_audio(BytesIO(), audio_data, sr, media_type).getvalue()
            return Response(audio_data, media_type=f"audio/{media_type}")
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"tts failed", "Exception": str(e)})
    





@APP.get("/control")
async def control(command: str = None):
    if command is None:
        return JSONResponse(status_code=400, content={"message": "command is required"})
    handle_control(command)
                

def set_gpt_weights(weights_path: str = None):
    try:
        if weights_path in ["", None]:
            return False
        tts_pipeline.init_t2s_weights(weights_path)
    except Exception as e:
        return False

    return True

def set_sovits_weights(weights_path: str = None):
    try:
        if weights_path in ["", None]:
            return False
        tts_pipeline.init_vits_weights(weights_path)
    except Exception as e:
        return False
    return True

@APP.post("/tts")
async def tts_post_endpoint(request: TTS_Request_role):
    global gpt, sovits
    req = request.dict()
    filepath = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # 读取角色配置文件
        with open(os.path.join(filepath, "role", req["role"], "config.json"), "rb") as f:
            config = json.load(f)
        
        # 情感分析和参考音频选择
        text = req["text"]
        role = req["role"]
        role_path = Path(filepath) / "role" / role
        
        # 进行情感分析
        emotion = emotion_analyzer.predict_emotion(text, role, role_path)
        logger.info(f"检测到情感: {emotion}")
        
        # 根据情感选择参考音频
        emotion_ref_audio_path = emotion_analyzer.get_ref_audio_path(emotion, role, role_path)
        
        # 如果找到情感对应的参考音频，使用它；否则使用默认配置
        if emotion_ref_audio_path:
            ref_audio_path = emotion_ref_audio_path
            # 从文件名提取参考文本
            ref_audio_name = Path(emotion_ref_audio_path).stem
            prompt_text = ref_audio_name
            logger.info(f"✅ 使用情感参考音频: {emotion_ref_audio_path}")
        else:
            # 使用默认配置
            ref_audio_path = os.path.join(filepath, "role", req["role"], config["ref_audio"])
            prompt_text = config["ref_text"]
            logger.info(f"⚠️ 使用默认参考音频: {ref_audio_path}")
        
        data = {
            "text": text,                   # str.(required) text to be synthesized
            "text_lang": "zh",              # str.(required) language of the text to be synthesized
            "ref_audio_path": ref_audio_path,         # str.(required) reference audio path
            "aux_ref_audio_paths": [],    # list.(optional) auxiliary reference audio paths for multi-speaker tone fusion
            "prompt_text": prompt_text,            # str.(optional) prompt text for the reference audio
            "prompt_lang": config["ref_lang"],            # str.(required) language of the prompt text for the reference audio
            "top_k": 5,                   # int. top k sampling
            "top_p": 1,                   # float. top p sampling
            "temperature": req["temperature"],             # float. temperature for sampling
            "text_split_method": "cut0",  # str. text split method, see text_segmentation_method.py for details.
            "batch_size": 1,              # int. batch size for inference
            "batch_threshold": 0.75,      # float. threshold for batch splitting.
            "split_bucket": True,         # bool. whether to split the batch into multiple buckets.
            "speed_factor":1.0,           # float. control the speed of the synthesized audio.
            "streaming_mode": False,      # bool. whether to return a streaming response.
            "seed": -1,                   # int. random seed for reproducibility.
            "parallel_infer": True,       # bool. whether to use parallel inference.
            "repetition_penalty": 1.35    # float. repetition penalty for T2S model.
        }
        
        # 检查是否需要切换模型
        if "gpt" in config and config["gpt"] != gpt:
            if not set_gpt_weights(os.path.join(filepath, "role", req["role"], config["gpt"])):
                return JSONResponse(status_code=400, content={"message": f"set gpt weights failed"})
            gpt = config["gpt"]
        
        if "sovits" in config and config["sovits"] != sovits:
            if not set_sovits_weights(os.path.join(filepath, "role", req["role"], config["sovits"])):
                return JSONResponse(status_code=400, content={"message": f"set sovits weights failed"})
            sovits = config["sovits"]
        
        return await tts_handle(data)
        
    except FileNotFoundError:
        logger.error(f"角色配置文件不存在: {os.path.join(filepath, 'role', req['role'], 'config.json')}")
        return JSONResponse(status_code=400, content={"message": f"角色配置文件不存在"})
    except Exception as e:
        logger.error(f"TTS处理失败: {e}")
        return JSONResponse(status_code=400, content={"message": f"TTS处理失败", "Exception": str(e)})

@APP.get("/set_refer_audio")
async def set_refer_audio(refer_audio_path: str = None):
    try:
        tts_pipeline.set_ref_audio(refer_audio_path)
    except Exception as e:
        return JSONResponse(status_code=400, content={"message": f"set refer audio failed", "Exception": str(e)})
    return JSONResponse(status_code=200, content={"message": "success"})


@APP.get("/running")
async def running(weights_path: str = None):
    return JSONResponse(status_code=200, content={"message": "GPT-SoVITS is running"})

@APP.get("/emotion_status")
async def get_emotion_status():
    """获取情感分析模型状态"""
    return JSONResponse(status_code=200, content=emotion_analyzer.get_emotion_status())

class TTS_Request_Enhanced(BaseModel):
    text: str = None
    role: str = None
    temperature: float = 1
    emotion: str = None  # 可选，如果提供则直接使用，否则进行情感分析

@APP.post("/tts_enhanced")
async def tts_enhanced_endpoint(request: TTS_Request_Enhanced):
    """增强版TTS端点，支持情感分析和动态参考音频选择"""
    global gpt, sovits
    req = request.dict()
    filepath = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # 读取角色配置文件
        with open(os.path.join(filepath, "role", req["role"], "config.json"), "rb") as f:
            config = json.load(f)
        
        text = req["text"]
        role = req["role"]
        role_path = Path(filepath) / "role" / role
        
        # 情感分析：如果请求中提供了emotion，直接使用；否则进行情感分析
        if req.get("emotion"):
            emotion = req["emotion"]
            logger.info(f"使用指定情感: {emotion}")
        else:
            emotion = emotion_analyzer.predict_emotion(text, role, role_path)
            logger.info(f"检测到情感: {emotion}")
        
        # 根据情感选择参考音频
        emotion_ref_audio_path = emotion_analyzer.get_ref_audio_path(emotion, role, role_path)
        
        # 如果找到情感对应的参考音频，使用它；否则使用默认配置
        if emotion_ref_audio_path:
            ref_audio_path = emotion_ref_audio_path
            # 从文件名提取参考文本
            ref_audio_name = Path(emotion_ref_audio_path).stem
            prompt_text = ref_audio_name
            logger.info(f"✅ 使用情感参考音频: {emotion_ref_audio_path}")
        else:
            # 使用默认配置
            ref_audio_path = os.path.join(filepath, "role", req["role"], config["ref_audio"])
            prompt_text = config["ref_text"]
            logger.info(f"⚠️ 使用默认参考音频: {ref_audio_path}")
        
        data = {
            "text": text,                   # str.(required) text to be synthesized
            "text_lang": "zh",              # str.(required) language of the text to be synthesized
            "ref_audio_path": ref_audio_path,         # str.(required) reference audio path
            "aux_ref_audio_paths": [],    # list.(optional) auxiliary reference audio paths for multi-speaker tone fusion
            "prompt_text": prompt_text,            # str.(optional) prompt text for the reference audio
            "prompt_lang": config["ref_lang"],            # str.(required) language of the prompt text for the reference audio
            "top_k": 5,                   # int. top k sampling
            "top_p": 1,                   # float. top p sampling
            "temperature": req["temperature"],             # float. temperature for sampling
            "text_split_method": "cut0",  # str. text split method, see text_segmentation_method.py for details.
            "batch_size": 1,              # int. batch size for inference
            "batch_threshold": 0.75,      # float. threshold for batch splitting.
            "split_bucket": True,         # bool. whether to split the batch into multiple buckets.
            "speed_factor":1.0,           # float. control the speed of the synthesized audio.
            "streaming_mode": False,      # bool. whether to return a streaming response.
            "seed": -1,                   # int. random seed for reproducibility.
            "parallel_infer": True,       # bool. whether to use parallel inference.
            "repetition_penalty": 1.35    # float. repetition penalty for T2S model.
        }
        
        # 检查是否需要切换模型
        if "gpt" in config and config["gpt"] != gpt:
            if not set_gpt_weights(os.path.join(filepath, "role", req["role"], config["gpt"])):
                return JSONResponse(status_code=400, content={"message": f"set gpt weights failed"})
            gpt = config["gpt"]
        
        if "sovits" in config and config["sovits"] != sovits:
            if not set_sovits_weights(os.path.join(filepath, "role", req["role"], config["sovits"])):
                return JSONResponse(status_code=400, content={"message": f"set sovits weights failed"})
            sovits = config["sovits"]
        
        return await tts_handle(data)
        
    except FileNotFoundError:
        logger.error(f"角色配置文件不存在: {os.path.join(filepath, 'role', req['role'], 'config.json')}")
        return JSONResponse(status_code=400, content={"message": f"角色配置文件不存在"})
    except Exception as e:
        logger.error(f"增强版TTS处理失败: {e}")
        return JSONResponse(status_code=400, content={"message": f"增强版TTS处理失败", "Exception": str(e)})

if __name__ == "__main__":
    try:
        if host == 'None':   # 在调用时使用 -a None 参数，可以让api监听双栈
            host = None
        uvicorn.run(app=APP, host=host, port=port, workers=1)
    except Exception as e:
        traceback.print_exc()
        os.kill(os.getpid(), signal.SIGTERM)
        exit(0)

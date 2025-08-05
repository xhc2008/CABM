"""
针对GPT-SoVITS的特化版本
"""

import base64
import hashlib
import logging
import requests
import os
import re
import torch
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.env_utils import get_env_var

# BERT情感分析相关导入
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline

logger = logging.getLogger(__name__)



if get_env_var("TTS_SERVICE_METHOD", "siliconflow").lower() == "siliconflow":
    class ttsService:
        def __init__(self):
            self.role_list = []
            self.role_name = {}  # name -> uri
            self.base_url = get_env_var("TTS_SERVICE_URL_SiliconFlow", "https://api.siliconflow.cn/v1").strip()
            self.api_key = get_env_var("TTS_SERVICE_API_KEY", "")
            self.method = get_env_var("TTS_SERVICE_METHOD", "siliconflow")

            if not self.api_key:
                raise ValueError("TTS_SERVICE_API_KEY 未设置，请配置环境变量。")

            self.headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            self._fetch_custom_voices()
            self._upload_local_voices()
            

        def _fetch_custom_voices(self):
            try:
                url = f"{self.base_url}/audio/voice/list"
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    result = response.json()
                    for voice in result.get("results", []):
                        name = voice.get("customName")
                        uri = voice.get("uri")
                        if name and uri:
                            self.role_list.append(name)
                            self.role_name[name] = uri
                    logger.info(f"已加载 {len(self.role_list)} 个自定义音色: {list(self.role_name.keys())}")
                else:
                    logger.error(f"请求音色列表失败: {response.status_code}, {response.text}")
            except Exception as e:
                logger.error(f"获取音色列表异常: {e}")

        def _upload_local_voices(self):
            ref_audio_dir = Path(".") / "data" / "ref_audio"
            if not ref_audio_dir.exists():
                logger.warning(f"参考音频目录不存在: {ref_audio_dir}")
                return
            for file_path in ref_audio_dir.iterdir():
                if file_path.suffix.lower() != ".wav":
                    continue
                name = file_path.stem

                if hashlib.md5(name.encode('utf-8')).hexdigest() in self.role_list:
                    logger.debug(f"音色已存在，跳过: {name}")
                    continue

                wav_path = file_path
                txt_path = ref_audio_dir / f"{name}.txt"

                # 读取参考文本
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        ref_text = f.read().strip()
                    if not ref_text:
                        ref_text = "在一无所知中, 梦里的一天结束了，一个新的轮回便会开始"
                except Exception as e:
                    logger.warning(f"读取参考文本失败 {txt_path}: {e}，使用默认文本。")
                    ref_text = "在一无所知中, 梦里的一天结束了，一个新的轮回便会开始"
                try:
                    with open(wav_path, 'rb') as f:
                        audio_data = f.read()
                    base64_str = base64.b64encode(audio_data).decode('utf-8')
                    audio_base64 = f"data:audio/wav;base64,{base64_str}"
                except Exception as e:
                    logger.error(f"读取音频文件失败 {wav_path}: {e}")
                    continue

                files = {
                    "model": (None, "FunAudioLLM/CosyVoice2-0.5B"),
                    "customName": (None, hashlib.md5(name.encode('utf-8')).hexdigest()),
                    "text": (None, ref_text),
                    "audio": (None, audio_base64)
                }

                try:
                    response = requests.post(
                        f"{self.base_url}/uploads/audio/voice",
                        files=files,
                        headers=self.headers
                    )
                    if response.status_code == 200:
                        result = response.json()
                        uri = result.get("uri")
                        if uri:
                            self.role_list.append(name)
                            self.role_name[name] = uri
                            logger.info(f"✅ 成功上传音色: {name} -> {uri}")
                        else:
                            logger.warning(f"上传成功但未返回 URI: {result}")
                    else:
                        logger.warning(f"❌ 上传音色失败 [{name}]: {response.status_code}, {response.text}")
                except Exception as e:
                    logger.error(f"上传音色异常 [{name}]: {e}")

        def get_tts(self, text, role='default', speed=1.0, gain=0.0, response_format='wav', sample_rate=44100):
            if role in self.role_name:
                voice = self.role_name[role]
            elif ':' not in role:
                voice = f"FunAudioLLM/CosyVoice2-0.5B:{role}"
            else:
                voice = role

            url = f"{self.base_url}/audio/speech"
            params = {
                "model": "FunAudioLLM/CosyVoice2-0.5B",
                "voice": voice,
                "input": text,
                "response_format": response_format,
                "speed": speed,
                "gain": gain,
            }

            if response_format in ["wav", "pcm"]:
                params["sample_rate"] = sample_rate
            elif response_format == "mp3":
                params["sample_rate"] = sample_rate if sample_rate in [32000, 44100] else 44100
            elif response_format == "opus":
                params["sample_rate"] = 48000

            try:
                response = requests.post(url, json=params, headers=self.headers)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"TTS 请求失败: {response.status_code}, {response.text}")
                    response.raise_for_status()
            except Exception as e:
                logger.error(f"获取 TTS 音频失败: {e}")
                raise

        def running(self):
            return True
else:
    class ttsService:
        def __init__(self):
            self.base_url = get_env_var("TTS_SERVICE_URL_GPTSoVITS", "http://localhost:9880")
            
            # BERT情感分析相关属性
            self.bert_models: Dict[str, Any] = {}
            self.bert_tokenizers: Dict[str, Any] = {}
            self.sentiment_analyzers: Dict[str, Any] = {}
            
            # 参考音频路径配置
            self.ref_audio_base_path = Path(__file__).parent / "res" / "refAudio"
            self.bert_model_base_path = Path(__file__).parent / "res" / "retrainedBERT"
            
            self.emotion_map = {
                0: "高兴", 1: "悲伤", 2: "愤怒", 3: "惊讶", 4: "恐惧", 
                5: "厌恶", 6: "中性", 7: "害羞", 8: "兴奋", 9: "舒适",
                10: "紧张", 11: "爱慕", 12: "委屈", 13: "骄傲", 14: "困惑"
            }

            # 初始化BERT模型
            self._init_bert_models()

        def _init_bert_models(self):
            """初始化BERT情感分析模型"""
            try:
                # 查找所有可用的BERT模型
                if not self.bert_model_base_path.exists():
                    logger.warning(f"BERT模型基础路径不存在: {self.bert_model_base_path}")
                    return
                
                for agent_dir in self.bert_model_base_path.iterdir():
                    if agent_dir.is_dir() and agent_dir.name != "__pycache__":
                        agent_name = agent_dir.name
                        self._load_bert_model_for_agent(agent_name)
                
                logger.info(f"BERT模型初始化完成，已加载 {len(self.sentiment_analyzers)} 个模型")
                
            except Exception as e:
                logger.error(f"BERT模型初始化失败: {e}")

        def _load_bert_model_for_agent(self, agent_name: str) -> bool:
            """加载指定agent的BERT情感分析模型"""
            try:
                model_path = self.bert_model_base_path / agent_name
                if not model_path.exists():
                    logger.warning(f"Agent '{agent_name}' 的BERT模型路径不存在: {model_path}")
                    return False
                
                logger.info(f"正在加载{agent_name}的BERT模型: {model_path}")
                
                # 加载tokenizer和模型
                tokenizer = BertTokenizer.from_pretrained(str(model_path))
                model = BertForSequenceClassification.from_pretrained(str(model_path))
                
                # 创建情感分析pipeline
                analyzer = pipeline(
                    "text-classification",
                    model=model,
                    tokenizer=tokenizer,
                    framework="pt",
                    device="cuda" if torch.cuda.is_available() else "cpu"
                )
                
                # 存储到对应的字典中
                self.bert_tokenizers[agent_name] = tokenizer
                self.bert_models[agent_name] = model
                self.sentiment_analyzers[agent_name] = analyzer
                
                logger.info(f"✅ {agent_name}的BERT模型加载成功，使用设备: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
                return True
                
            except Exception as e:
                logger.error(f"❌ {agent_name}的BERT模型加载失败: {e}")
                return False

        def predict_emotion(self, text: str, role: str = "default") -> str:
            """预测文本情感，返回情感标签"""
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



        def get_ref_audio_path(self, emotion: str, role: str = "default") -> Optional[str]:
            """根据情感和角色获取参考音频路径"""
            # 构建参考音频路径：/res/refAudio/{role}/{emotion}/
            role_emotion_dir = self.ref_audio_base_path / role / emotion
            if not role_emotion_dir.exists():
                logger.warning(f"角色情感目录不存在: {role_emotion_dir}")
                # 尝试使用中性情感作为备选
                role_neutral_dir = self.ref_audio_base_path / role / "中性"
                if not role_neutral_dir.exists():
                    logger.error(f"角色中性情感目录也不存在: {role_neutral_dir}")
                    return None
                role_emotion_dir = role_neutral_dir
            
            # 查找该情感目录下的第一个wav文件
            for wav_file in role_emotion_dir.glob("*.wav"):
                return str(wav_file)
            
            logger.warning(f"在角色情感目录 {role_emotion_dir} 中未找到wav文件")
            return None

        def get_tts(self, text, role='default', speed=1.0):
            """增强的TTS方法，支持情感分析和参考音频"""
            try:
                # 直接使用输入文本进行情感分析
                emotion = self.predict_emotion(text, role)
                logger.info(f"检测到情感: {emotion}")
                
                # 获取参考音频路径
                ref_audio_path = self.get_ref_audio_path(emotion, role)
                if not ref_audio_path:
                    logger.warning("未找到参考音频，使用默认TTS")
                    return self._call_default_tts(text, role, speed)
                
                # 获取参考音频的文本（从文件名提取）
                ref_audio_name = Path(ref_audio_path).stem
                
                # 调用GPT-SoVITS API
                url = f"{self.base_url}/tts"
                post_data = {
                    "prompt_text": ref_audio_name,
                    "prompt_lang": "zh",
                    "ref_audio_path": ref_audio_path,
                    "text": text,
                    "text_lang": "zh",
                }
                
                response = requests.post(url, json=post_data)
                if response.status_code == 200:
                    logger.info(f"✅ 成功生成音频 (情感: {emotion})")
                    return response.content
                else:
                    logger.error(f"❌ 音频生成失败: {response.status_code}")
                    logger.error(f"   错误信息: {response.text}")
                    # 回退到默认TTS
                    return self._call_default_tts(text, role, speed)
                    
            except Exception as e:
                logger.error(f"TTS生成异常: {e}")
                # 回退到默认TTS
                return self._call_default_tts(text, role, speed)

        def _call_default_tts(self, text, role='default', speed=1.0):
            """调用默认的TTS方法"""
            url = f"{self.base_url}/tts"
            params = {
                "text": text,
                "role": role,
                "temperature": 1,
            }
            response = requests.post(url, json=params)
            
            if response.status_code == 200:
                return response.content
            else:
                response.raise_for_status()

        def running(self):
            try:
                response = requests.get(f"{self.base_url}/running")
                return response.status_code == 200
            except requests.RequestException:
                return False

        def get_emotion_status(self) -> Dict[str, Any]:
            """获取情感分析模型状态"""
            return {
                "bert_loaded": len(self.sentiment_analyzers) > 0,
                "loaded_roles": list(self.sentiment_analyzers.keys()),
                "total_loaded": len(self.sentiment_analyzers),
                "device": "CUDA" if torch.cuda.is_available() else "CPU",
                "available_emotions": list(self.emotion_map.values())
            }

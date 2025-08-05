
"""
这里只针对硅基流动进行定制
"""

import base64
import hashlib
import logging
import requests
import json
import torch
from pathlib import Path
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline
from utils.env_utils import get_env_var

logger = logging.getLogger(__name__)

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

# 初始化情感分析器
emotion_analyzer = EmotionAnalyzer()

if get_env_var("TTS_SERVICE_METHOD", "siliconflow").lower() == "siliconflow":
    class ttsService:
        def __init__(self):
            self.role_list = []
            self.role_name = {}  # name -> uri
            self.role_emotion_voices = {}  # role -> {emotion -> uri}
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
            """上传本地角色情感音色"""
            role_dir = Path(".") / "replace" / "role"
            if not role_dir.exists():
                logger.warning(f"角色目录不存在: {role_dir}")
                return
            
            # 遍历所有角色目录
            for role_path in role_dir.iterdir():
                if not role_path.is_dir() or role_path.name.startswith('.'):
                    continue
                
                role_name = role_path.name
                logger.info(f"处理角色: {role_name}")
                
                # 检查是否有refAudio目录
                ref_audio_dir = role_path / "refAudio"
                if not ref_audio_dir.exists():
                    logger.warning(f"角色 {role_name} 的refAudio目录不存在: {ref_audio_dir}")
                    continue
                
                # 初始化角色的情感音色字典
                if role_name not in self.role_emotion_voices:
                    self.role_emotion_voices[role_name] = {}
                
                # 遍历情感目录
                for emotion_dir in ref_audio_dir.iterdir():
                    if not emotion_dir.is_dir() or emotion_dir.name.startswith('.'):
                        continue
                    
                    emotion = emotion_dir.name
                    logger.info(f"处理角色 {role_name} 的情感: {emotion}")
                    
                    # 查找该情感目录下的第一个wav文件
                    wav_files = list(emotion_dir.glob("*.wav"))
                    if not wav_files:
                        logger.warning(f"情感目录 {emotion_dir} 中没有找到wav文件")
                        continue
                    
                    wav_path = wav_files[0]
                    voice_name = f"{role_name}_{emotion}"
                    voice_hash = hashlib.md5(voice_name.encode('utf-8')).hexdigest()
                    
                    # 检查是否已经上传过
                    if voice_hash in self.role_list:
                        logger.debug(f"音色已存在，跳过: {voice_name}")
                        # 记录到角色情感音色字典中
                        self.role_emotion_voices[role_name][emotion] = self.role_name.get(voice_hash)
                        continue
                    
                    # 读取参考文本（从文件名获取）
                    ref_text = wav_path.stem
                    if not ref_text:
                        ref_text = "在一无所知中, 梦里的一天结束了，一个新的轮回便会开始"
                    
                    # 读取音频文件
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
                        "customName": (None, voice_hash),
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
                                self.role_list.append(voice_name)
                                self.role_name[voice_name] = uri
                                self.role_emotion_voices[role_name][emotion] = uri
                                logger.info(f"✅ 成功上传音色: {voice_name} -> {uri}")
                            else:
                                logger.warning(f"上传成功但未返回 URI: {result}")
                        else:
                            logger.warning(f"❌ 上传音色失败 [{voice_name}]: {response.status_code}, {response.text}")
                    except Exception as e:
                        logger.error(f"上传音色异常 [{voice_name}]: {e}")
                
                logger.info(f"角色 {role_name} 的情感音色上传完成，共 {len(self.role_emotion_voices.get(role_name, {}))} 个情感")

        def get_tts(self, text, role='default', speed=1.0, gain=0.0, response_format='wav', sample_rate=44100):
            # 检查是否有角色情感音色
            if role in self.role_emotion_voices:
                # 进行情感分析
                role_path = Path(".") / "replace" / "role" / role
                emotion = emotion_analyzer.predict_emotion(text, role, role_path)
                
                # 查找对应的情感音色
                if emotion in self.role_emotion_voices[role]:
                    voice = self.role_emotion_voices[role][emotion]
                    logger.info(f"使用角色 {role} 的 {emotion} 情感音色")
                else:
                    # 如果没有找到对应情感，使用中性情感
                    if "中性" in self.role_emotion_voices[role]:
                        voice = self.role_emotion_voices[role]["中性"]
                        logger.info(f"未找到 {emotion} 情感音色，使用中性情感音色")
                    else:
                        # 如果连中性都没有，使用默认音色
                        voice = f"FunAudioLLM/CosyVoice2-0.5B:{role}"
                        logger.warning(f"角色 {role} 没有情感音色，使用默认音色")
            elif role in self.role_name:
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

        def get_tts(self, text, role='default', speed=1.0):
            url = f"{self.base_url}/tts"
            params = {
                "text": text,                   # str.(required) text to be synthesized
                "role": role,                   # str.(required) role
                "temperature": 1,             # float. temperature for sampling
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

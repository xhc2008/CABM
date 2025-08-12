import base64
import hashlib
import logging
import re
import requests
from pathlib import Path
from utils.env_utils import get_env_var

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

        def _filter_symbols(self, text):
            """
            过滤文本中的连续符号和表情符号
            """
            if not text:
                return text
            
            # 移除连续的特殊符号 (3个或以上连续的非字母数字字符)
            text = re.sub(r'[^\w\s\u4e00-\u9fff]{3,}', '', text)
            
            # 移除常见的表情符号模式
            patterns = [
                r'o\([^)]*\)[^\w\s]*',  # o(xxx)xxx 类型
                r'\([^)]*\)[^\w\s]*',   # (xxx)xxx 类型  
                r'[^\w\s]*\([^)]*\)',   # xxx(xxx) 类型
                r'[★☆♪♫♬♭♮♯]+',        # 音符和星号
                r'[（）()【】\[\]{}｛｝]+', # 各种括号连续出现
                r'[！!？?。.，,；;：:]+', # 标点符号连续出现
                r'[~～＠@#＃$＄%％^＾&＆*＊]+', # 特殊符号连续出现
            ]
            
            for pattern in patterns:
                text = re.sub(pattern, '', text)
            
            # 清理多余的空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text

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
            
            # 导入角色模块来获取角色名称映射
            try:
                import characters
            except ImportError:
                logger.warning("无法导入characters模块，将只使用角色ID")
                characters = None
            
            # 遍历角色ID目录
            for character_dir in ref_audio_dir.iterdir():
                if not character_dir.is_dir():
                    continue
                
                character_id = character_dir.name
                wav_path = character_dir / "1.wav"
                txt_path = character_dir / "1.txt"
                logger.warning(f"导入角色ID{character_id}.............")
                # 检查必要文件是否存在
                if not wav_path.exists():
                    logger.warning(f"角色 {character_id} 的音频文件不存在: {wav_path}")
                    continue

                if hashlib.md5(character_id.encode('utf-8')).hexdigest() in self.role_list:
                    logger.debug(f"音色已存在，跳过: {character_id}")
                    continue

                # 读取参考文本
                try:
                    if txt_path.exists():
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            ref_text = f.read().strip()
                    else:
                        ref_text = ""
                    
                    if not ref_text:
                        ref_text = "在一无所知中, 梦里的一天结束了，一个新的轮回便会开始"
                except Exception as e:
                    logger.warning(f"读取参考文本失败 {txt_path}: {e}，使用默认文本。")
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
                    "customName": (None, hashlib.md5(character_id.encode('utf-8')).hexdigest()),
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
                            self.role_list.append(character_id)
                            self.role_name[character_id] = uri
                            
                            # 同时添加角色名称映射（如果能获取到的话）
                            if characters:
                                try:
                                    character_config = characters.get_character_config(character_id)
                                    if character_config and 'name' in character_config:
                                        character_name = character_config['name']
                                        self.role_name[character_name] = uri
                                        logger.info(f"✅ 成功上传音色: {character_id} ({character_name}) -> {uri}")
                                    else:
                                        logger.info(f"✅ 成功上传音色: {character_id} -> {uri}")
                                except Exception as e:
                                    logger.warning(f"获取角色名称失败 {character_id}: {e}")
                                    logger.info(f"✅ 成功上传音色: {character_id} -> {uri}")
                            else:
                                logger.info(f"✅ 成功上传音色: {character_id} -> {uri}")
                        else:
                            logger.warning(f"上传成功但未返回 URI: {result}")
                    else:
                        logger.warning(f"❌ 上传音色失败 [{character_id}]: {response.status_code}, {response.text}")
                except Exception as e:
                    logger.error(f"上传音色异常 [{character_id}]: {e}")

        def get_tts(self, text, role='default', speed=1.0, gain=0.0, response_format='wav', sample_rate=44100):
            # 过滤符号
            filtered_text = self._filter_symbols(text)
            
            # 如果过滤后文本为空，使用原文本
            if not filtered_text:
                filtered_text = text
                
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
                "input": filtered_text,
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

        def _filter_symbols(self, text):
            """
            过滤文本中的连续符号和表情符号
            """
            if not text:
                return text
            
            # 移除连续的特殊符号 (3个或以上连续的非字母数字字符)
            text = re.sub(r'[^\w\s\u4e00-\u9fff]{3,}', '', text)
            
            # 移除常见的表情符号模式
            patterns = [
                r'o\([^)]*\)[^\w\s]*',  # o(xxx)xxx 类型
                r'\([^)]*\)[^\w\s]*',   # (xxx)xxx 类型  
                r'[^\w\s]*\([^)]*\)',   # xxx(xxx) 类型
                r'[★☆♪♫♬♭♮♯]+',        # 音符和星号
                r'[（）()【】\[\]{}｛｝]+', # 各种括号连续出现
                r'[！!？?。.，,；;：:]+', # 标点符号连续出现
                r'[~～＠@#＃$＄%％^＾&＆*＊]+', # 特殊符号连续出现
            ]
            
            for pattern in patterns:
                text = re.sub(pattern, '', text)
            
            # 清理多余的空格
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text

        def get_tts(self, text, role='default', speed=1.0):
            # 过滤符号
            filtered_text = self._filter_symbols(text)
            
            # 如果过滤后文本为空，使用原文本
            if not filtered_text:
                filtered_text = text
                
            url = f"{self.base_url}/tts"
            params = {
                "text": filtered_text,          # str.(required) text to be synthesized
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

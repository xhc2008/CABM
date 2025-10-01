import base64
import hashlib
import json
import logging
import re
import requests
from pathlib import Path
from utils.env_utils import get_env_var
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from io import BytesIO
from config import get_tts_audio_config

logger = logging.getLogger(__name__)

def trim_audio_silence(audio_data, silence_threshold=None, chunk_size=None):
    """
    去除音频开头和结尾的静音部分
    
    Args:
        audio_data: 音频数据 (bytes)
        silence_threshold: 静音阈值 (dB)，默认从配置读取
        chunk_size: 检测块大小 (ms)，默认从配置读取
    
    Returns:
        处理后的音频数据 (bytes)
    """
    # 获取TTS音频配置
    tts_config = get_tts_audio_config()
    
    # 检查是否启用静音去除功能
    if not tts_config["trim_silence"]:
        return audio_data
    
    # 从配置获取参数
    if silence_threshold is None:
        silence_threshold = tts_config["silence_threshold"]
    if chunk_size is None:
        chunk_size = tts_config["silence_chunk_size"]
    
    try:
        # 将字节数据转换为AudioSegment对象
        audio_io = BytesIO(audio_data)
        audio_segment = AudioSegment.from_file(audio_io, format="wav")
        
        # 检测开头静音长度
        start_trim = detect_leading_silence(audio_segment, silence_threshold, chunk_size)
        
        # 检测结尾静音长度（通过反转音频）
        end_trim = detect_leading_silence(audio_segment.reverse(), silence_threshold, chunk_size)
        
        # 计算音频总长度
        duration = len(audio_segment)
        
        # 如果检测到的静音时间过长，保留一些静音避免过度裁剪
        max_trim = duration * tts_config["max_trim_ratio"]
        start_trim = min(start_trim, max_trim)
        end_trim = min(end_trim, max_trim)
        
        # 确保裁剪后还有音频内容
        if start_trim + end_trim >= duration:
            logger.warning("检测到的静音时间过长，跳过裁剪")
            return audio_data
        
        # 如果没有检测到明显的静音，直接返回原音频
        min_silence = tts_config["min_silence_duration"]
        if start_trim < min_silence and end_trim < min_silence:
            return audio_data
        
        # 裁剪音频
        trimmed_audio = audio_segment[start_trim:duration-end_trim]
        
        # 转换回字节数据
        output_io = BytesIO()
        trimmed_audio.export(output_io, format="wav")
        output_io.seek(0)
        
        trimmed_data = output_io.read()
        
        # 记录处理结果
        original_duration = duration / 1000.0  # 转换为秒
        trimmed_duration = len(trimmed_audio) / 1000.0
        saved_time = original_duration - trimmed_duration
        
        if saved_time > 0.01:  # 只有节省超过10ms才记录
            logger.info(f"音频静音处理: 原长度 {original_duration:.3f}s -> 处理后 {trimmed_duration:.3f}s (节省 {saved_time:.3f}s)")
        
        return trimmed_data
        
    except Exception as e:
        logger.warning(f"音频静音处理失败，返回原音频: {e}")
        return audio_data
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

        def _get_file_hash(self, file_path):
            """计算文件的MD5哈希值"""
            hash_md5 = hashlib.md5()
            try:
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                return hash_md5.hexdigest()
            except Exception as e:
                logger.error(f"计算文件哈希失败 {file_path}: {e}")
                return None

        def _load_voice_cache(self):
            """加载本地音色缓存"""
            cache_file = Path(".") / "data" / "voice_cache.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"加载音色缓存失败: {e}")
            return {}

        def _save_voice_cache(self, cache):
            """保存本地音色缓存"""
            cache_file = Path(".") / "data" / "voice_cache.json"
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存音色缓存失败: {e}")

        def _upload_local_voices(self):
            ref_audio_dir = Path(".") / "data" / "ref_audio"
            if not ref_audio_dir.exists():
                logger.warning(f"参考音频目录不存在: {ref_audio_dir}")
                return
            
            # 加载本地缓存
            voice_cache = self._load_voice_cache()
            cache_updated = False
            
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
                
                # 检查必要文件是否存在
                if not wav_path.exists():
                    logger.warning(f"角色 {character_id} 的音频文件不存在: {wav_path}")
                    continue

                # 计算音频文件哈希值
                audio_hash = self._get_file_hash(wav_path)
                if not audio_hash:
                    continue

                # 检查缓存中是否已存在相同哈希的音色
                cached_info = voice_cache.get(character_id)
                if cached_info and cached_info.get('audio_hash') == audio_hash:
                    # 使用缓存的URI
                    uri = cached_info.get('uri')
                    if uri:
                        self.role_list.append(character_id)
                        self.role_name[character_id] = uri
                        
                        # 添加角色名称映射
                        # if characters:
                        #     try:
                        #         character_config = characters.get_character_config(character_id)
                        #         if character_config and 'name' in character_config:
                        #             character_name = character_config['name']
                        #             self.role_name[character_name] = uri
                        #     except Exception:
                        #         pass
                        
                        logger.info(f"🔄 使用缓存音色: {character_id} -> {uri}")
                        continue

                # 检查服务器上是否已存在（通过customName）
                custom_name = hashlib.md5(character_id.encode('utf-8')).hexdigest()
                if custom_name in [name for name in self.role_name.keys() if isinstance(name, str) and len(name) == 32]:
                    logger.debug(f"音色已存在于服务器，跳过: {character_id}")
                    continue

                logger.info(f"📤 上传角色 {character_id} 的参考音频...")

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
                    ref_text = ""
                
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
                    "customName": (None, custom_name),
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
                            
                            # 更新缓存
                            voice_cache[character_id] = {
                                'audio_hash': audio_hash,
                                'uri': uri,
                                'custom_name': custom_name,
                                'upload_time': str(Path(wav_path).stat().st_mtime)
                            }
                            cache_updated = True
                            
                            # 同时添加角色名称映射（如果能获取到的话）
                            if characters:
                                try:
                                    character_config = characters.get_character_config(character_id)
                                    if character_config and 'name' in character_config:
                                        character_name = character_config['name']
                                        self.role_name[character_id] = uri
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
            
            # 保存更新的缓存
            if cache_updated:
                self._save_voice_cache(voice_cache)

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
        
            #特化（虽然很抽象，但很有效）
            filtered_text = filtered_text.replace("希儿", "希而")
            filtered_text = filtered_text.replace("布洛妮娅", "Bronya")
            filtered_text = filtered_text.replace("安柏", "安博")

            full_input=filtered_text
            #为什么加了prompt就很诡异……？
            # if "希儿" in filtered_text:
            #     full_input+="“希儿”的“儿”不要读轻声。"
            # if "布洛妮娅" in filtered_text:
            #     full_input+="“布洛妮娅”读作“Bronya”。"
            #full_input+="<|endofprompt|>"+filtered_text
            logger.info("TTS角色："+role)
            url = f"{self.base_url}/audio/speech"
            params = {
                "model": "FunAudioLLM/CosyVoice2-0.5B",
                "voice": voice,
                "input": full_input,
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
                    # 对音频进行静音处理
                    raw_audio = response.content
                    processed_audio = trim_audio_silence(raw_audio)
                    return processed_audio
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
                # 对音频进行静音处理
                raw_audio = response.content
                processed_audio = trim_audio_silence(raw_audio)
                return processed_audio
            else:
                response.raise_for_status()
        def running(self):
            try:
                response = requests.get(f"{self.base_url}/running")
                return response.status_code == 200
            except requests.RequestException:
                return False

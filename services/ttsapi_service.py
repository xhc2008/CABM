import base64
import hashlib
import logging
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

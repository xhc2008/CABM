import requests
import os
from utils.env_utils import get_env_var

class ttsService:
    def __init__(self):
        self.base_url = get_env_var("TTS_SERVICE_URL", "http://localhost:9880")

    def get_tts(self, text, role='default', speed=1.0):
        """
        获取TTS音频
        :param text: 要转换的文本
        :param role: 角色
        :param speed: 语速
        :return: 音频数据
        """
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
        """
        检查TTS服务是否运行
        :return: bool
        """
        try:
            response = requests.get(f"{self.base_url}/running")
            return response.status_code == 200
        except requests.RequestException:
            return False
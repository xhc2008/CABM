"""
TTS语音合成服务
基于stream_processor.js的分割逻辑，实现后端TTS处理
"""
import os
import re
import time
import hashlib
from pathlib import Path
from openai import OpenAI
from utils.env_utils import get_env_var
from utils.api_utils import APIError

class TTSService:
    def __init__(self, config_service):
        self.config_service = config_service
        self.tts_config = config_service.get_tts_config()
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=get_env_var("TTS_API_KEY"),
            base_url=get_env_var("TTS_API_BASE_URL", "https://api.siliconflow.cn/v1")
        )
        
        # 确保音频目录存在
        self.audio_dir = Path(self.tts_config["audio_dir"])
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 分句标点符号（与stream_processor.js保持一致）
        self.pause_markers = ['。', '？', '！', '…', '~']
    
    def is_enabled(self):
        """检查TTS是否启用"""
        return self.tts_config.get("enable_tts", False)
    
    def split_sentences(self, text):
        """
        分割文本为句子
        参考stream_processor.js的分割逻辑
        """
        if not text:
            return []
        
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            # 如果遇到分句标点符号，结束当前句子
            if char in self.pause_markers:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # 添加剩余的内容
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def generate_audio_filename(self, text):
        """
        根据文本内容生成音频文件名
        使用MD5哈希避免重复生成相同内容的音频
        """
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"tts_{text_hash}.{self.tts_config['response_format']}"
    
    def generate_tts_audio(self, text):
        """
        生成单句话的TTS音频
        """
        if not text or not text.strip():
            return None
        
        try:
            # 生成文件名
            filename = self.generate_audio_filename(text)
            file_path = self.audio_dir / filename
            
            # 如果文件已存在，直接返回
            if file_path.exists():
                return str(file_path)
            
            # 调用TTS API
            with self.client.audio.speech.with_streaming_response.create(
                model=self.tts_config["model"],
                voice=self.tts_config["voice"],
                input=text,
                response_format=self.tts_config["response_format"]
            ) as response:
                response.stream_to_file(file_path)
            
            return str(file_path)
            
        except Exception as e:
            print(f"TTS生成失败: {str(e)}")
            raise APIError(f"TTS生成失败: {str(e)}")
    
    def process_content_stream(self, content_stream):
        """
        处理流式内容，为每个句子生成TTS音频
        这是一个生成器，会逐句返回音频文件路径
        """
        if not self.is_enabled():
            return
        
        buffer = ""
        
        for chunk in content_stream:
            if chunk is None:
                continue
                
            buffer += chunk
            
            # 检查是否有完整的句子
            sentences = self.split_sentences(buffer)
            
            # 如果有多个句子，说明前面的句子已经完整
            if len(sentences) > 1:
                # 处理除最后一个句子外的所有句子
                for sentence in sentences[:-1]:
                    if sentence.strip():
                        try:
                            audio_path = self.generate_tts_audio(sentence)
                            if audio_path:
                                yield {
                                    'text': sentence,
                                    'audio_path': audio_path,
                                    'audio_url': f"/api/audio/{os.path.basename(audio_path)}"
                                }
                        except Exception as e:
                            print(f"处理句子TTS失败: {sentence}, 错误: {e}")
                
                # 保留最后一个句子作为新的buffer
                buffer = sentences[-1] if sentences else ""
        
        # 处理剩余的内容
        if buffer.strip():
            try:
                audio_path = self.generate_tts_audio(buffer)
                if audio_path:
                    yield {
                        'text': buffer,
                        'audio_path': audio_path,
                        'audio_url': f"/api/audio/{os.path.basename(audio_path)}"
                    }
            except Exception as e:
                print(f"处理最后句子TTS失败: {buffer}, 错误: {e}")
    
    def process_complete_text(self, text):
        """
        处理完整文本，返回所有句子的TTS音频
        """
        if not self.is_enabled() or not text:
            return []
        
        sentences = self.split_sentences(text)
        results = []
        
        for sentence in sentences:
            if sentence.strip():
                try:
                    audio_path = self.generate_tts_audio(sentence)
                    if audio_path:
                        results.append({
                            'text': sentence,
                            'audio_path': audio_path,
                            'audio_url': f"/api/audio/{os.path.basename(audio_path)}"
                        })
                except Exception as e:
                    print(f"处理句子TTS失败: {sentence}, 错误: {e}")
        
        return results
    
    def get_audio_file_path(self, filename):
        """
        获取音频文件的完整路径
        """
        return self.audio_dir / filename
    
    def cleanup_old_audio_files(self, max_age_hours=24):
        """
        清理旧的音频文件
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for audio_file in self.audio_dir.glob("tts_*.mp3"):
                if current_time - audio_file.stat().st_mtime > max_age_seconds:
                    audio_file.unlink()
                    print(f"删除旧音频文件: {audio_file}")
        except Exception as e:
            print(f"清理音频文件失败: {e}")

# 全局TTS服务实例
tts_service = None

def get_tts_service():
    """获取TTS服务实例"""
    global tts_service
    if tts_service is None:
        from services.config_service import config_service
        tts_service = TTSService(config_service)
    return tts_service
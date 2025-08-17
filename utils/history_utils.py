"""
历史记录工具模块
负责处理聊天历史的持久化存储和加载
"""
import os
import json
import time
import collections
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Deque
from pathlib import Path
from config import get_app_config

class HistoryManager:
    """历史记录管理器"""
    
    def __init__(self, history_dir: str):
        """
        初始化历史记录管理器
        
        Args:
            history_dir: 历史记录存储目录
        """
        self.history_dir = history_dir
        self._ensure_history_dir()
        # 缓存各角色的历史记录
        self.history_cache: Dict[str, Deque[Dict[str, Any]]] = {}
    
    def _ensure_history_dir(self):
        """确保历史记录目录存在"""
        os.makedirs(self.history_dir, exist_ok=True)
    
    def _get_character_history_file(self, character_id: str) -> str:
        """
        获取角色历史记录文件路径
        
        Args:
            character_id: 角色ID
            
        Returns:
            历史记录文件路径
        """
        return os.path.join(self.history_dir, f"{character_id}_history.log")
    
    def _initialize_cache(self, character_id: str, max_size: int) -> None:
        """
        初始化角色历史记录缓存
        
        Args:
            character_id: 角色ID
            max_size: 缓存的最大消息数量
        """
        if character_id in self.history_cache:
            return
            
        # 获取历史记录文件路径
        history_file = self._get_character_history_file(character_id)
        
        # 如果文件不存在，创建空缓存
        if not os.path.exists(history_file):
            self.history_cache[character_id] = collections.deque(maxlen=max_size)
            return
        
        # 读取历史记录
        messages = []
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            # 保留完整消息记录
                            messages.append(message)
                        except json.JSONDecodeError:
                            # 忽略无效的JSON行
                            continue
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            messages = []
        
        # 创建缓存，只保留最近的max_size条消息
        self.history_cache[character_id] = collections.deque(
            messages[-max_size:] if max_size > 0 and len(messages) > max_size else messages,
            maxlen=max_size
        )
        print(f"已加载 {len(self.history_cache[character_id])} 条 {character_id} 的历史记录到内存")
    
    def _clean_assistant_content(self, content: str) -> str:
        """
        清理assistant消息内容，去除【】及其内部的内容
        注意：此方法在新的JSON格式下已弃用，保留仅为兼容性
        
        Args:
            content: 原始消息内容
            
        Returns:
            清理后的消息内容
        """
        # 使用正则表达式去除【】及其内部的内容
        cleaned_content = re.sub(r'【[^】]*】', '', content)
        return cleaned_content
    
    def save_message(self, character_id: str, role: str, content: str) -> None:
        """
        保存消息到历史记录
        
        Args:
            character_id: 角色ID
            role: 消息角色
            content: 消息内容
        """
        # 注意：在新的JSON格式下，我们直接存储原始响应内容，不再清理【】标记
        # 因为JSON格式的响应已经将mood和content分离，历史记录中存储的是完整的原始响应
        # clean_assistant_history配置已弃用
        
        # 获取当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建消息记录
        message_record = {
            "timestamp": timestamp,
            "role": role,
            "content": content
        }
        
        # 获取历史记录文件路径
        history_file = self._get_character_history_file(character_id)
        
        # 写入历史记录文件
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(message_record, ensure_ascii=False) + "\n")
        
        # 更新内存缓存
        if character_id in self.history_cache:
            self.history_cache[character_id].append(message_record)
    
    def save_message_to_file(self, file_path: str, role: str, content: str) -> None:
        """
        保存消息到指定文件
        
        Args:
            file_path: 历史记录文件路径
            role: 消息角色
            content: 消息内容
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 获取当前时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建消息记录
        message_record = {
            "timestamp": timestamp,
            "role": role,
            "content": content
        }
        
        # 写入历史记录文件
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(message_record, ensure_ascii=False) + "\n")
    
    def load_history_from_file(self, file_path: str, count: int = 10, max_cache_size: int = 100) -> List[Dict[str, Any]]:
        """
        从指定文件加载历史记录
        
        Args:
            file_path: 历史记录文件路径
            count: 加载的消息数量
            max_cache_size: 缓存的最大消息数量
            
        Returns:
            历史记录列表，按时间从旧到新排序
        """
        # 如果文件不存在，返回空列表
        if not os.path.exists(file_path):
            return []
        
        # 读取历史记录
        messages = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            messages.append(message)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return []
        
        # 返回最近的count条消息
        return messages[-count:] if count > 0 and len(messages) > count else messages
    
    def load_history(self, character_id: str, count: int = 10, max_cache_size: int = 100) -> List[Dict[str, Any]]:
        """
        加载历史记录
        
        Args:
            character_id: 角色ID
            count: 加载的消息数量
            max_cache_size: 缓存的最大消息数量
            
        Returns:
            历史记录列表，按时间从旧到新排序
        """
        # 确保缓存已初始化
        if character_id not in self.history_cache:
            self._initialize_cache(character_id, max_cache_size)
        
        # 从缓存中获取历史记录
        messages = list(self.history_cache[character_id])
        
        # 转换为API需要的格式
        api_messages = []
        for message in messages[-count:] if count > 0 else messages:
            api_messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return api_messages
    
    def clear_history(self, character_id: str) -> bool:
        """
        清空历史记录
        
        Args:
            character_id: 角色ID
            
        Returns:
            是否成功清空
        """
        # 获取历史记录文件路径
        history_file = self._get_character_history_file(character_id)
        
        # 如果文件不存在，返回True
        if not os.path.exists(history_file):
            return True
        
        # 清空文件
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                pass
            
            # 清空缓存
            if character_id in self.history_cache:
                self.history_cache[character_id].clear()
                
            return True
        except Exception as e:
            print(f"清空历史记录失败: {e}")
            return False
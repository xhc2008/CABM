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
    
    def load_history_paginated(self, character_id: str, page: int = 1, page_size: int = 20, max_cache_size: int = 200) -> Dict[str, Any]:
        """
        分页加载历史记录
        
        Args:
            character_id: 角色ID
            page: 页码（从1开始）
            page_size: 每页消息数量
            max_cache_size: 缓存的最大消息数量
            
        Returns:
            包含历史记录和分页信息的字典
        """
        # 确保缓存已初始化
        if character_id not in self.history_cache:
            self._initialize_cache(character_id, max_cache_size)
        
        # 从缓存中获取所有历史记录
        all_messages = list(self.history_cache[character_id])
        total_messages = len(all_messages)
        
        # 如果缓存中的消息不够，从文件中加载更多
        if total_messages < page * page_size:
            # 从文件中加载更多历史记录
            history_file = self._get_character_history_file(character_id)
            if os.path.exists(history_file):
                try:
                    with open(history_file, "r", encoding="utf-8") as f:
                        file_messages = []
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    message = json.loads(line)
                                    file_messages.append(message)
                                except json.JSONDecodeError:
                                    continue
                    
                    # 更新缓存（保留最新的max_cache_size条消息）
                    if len(file_messages) > max_cache_size:
                        file_messages = file_messages[-max_cache_size:]
                    
                    self.history_cache[character_id] = collections.deque(file_messages, maxlen=max_cache_size)
                    all_messages = list(self.history_cache[character_id])
                    total_messages = len(all_messages)
                    
                except Exception as e:
                    print(f"从文件加载历史记录失败: {e}")
        
        # 计算分页
        total_pages = (total_messages + page_size - 1) // page_size if total_messages > 0 else 1
        start_index = max(0, total_messages - page * page_size)
        end_index = max(0, total_messages - (page - 1) * page_size)
        
        # 获取当前页的消息（从后往前取）
        page_messages = all_messages[start_index:end_index]
        
        # 转换为API需要的格式
        api_messages = []
        for message in page_messages:
            api_messages.append({
                "role": message["role"],
                "content": message["content"],
                "timestamp": message.get("timestamp", "")
            })
        
        return {
            "messages": api_messages,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_messages": total_messages,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
        }
    
    def load_history_from_file_paginated(self, file_path: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        从指定文件分页加载历史记录
        
        Args:
            file_path: 历史记录文件路径
            page: 页码（从1开始）
            page_size: 每页消息数量
            
        Returns:
            包含历史记录和分页信息的字典
        """
        # 如果文件不存在，返回空结果
        if not os.path.exists(file_path):
            return {
                "messages": [],
                "pagination": {
                    "current_page": 1,
                    "page_size": page_size,
                    "total_messages": 0,
                    "total_pages": 0,
                    "has_more": False
                }
            }
        
        # 读取所有历史记录
        all_messages = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            all_messages.append(message)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            return {
                "messages": [],
                "pagination": {
                    "current_page": 1,
                    "page_size": page_size,
                    "total_messages": 0,
                    "total_pages": 0,
                    "has_more": False
                }
            }
        
        total_messages = len(all_messages)
        total_pages = (total_messages + page_size - 1) // page_size if total_messages > 0 else 1
        
        # 计算当前页的消息范围（从后往前取）
        start_index = max(0, total_messages - page * page_size)
        end_index = max(0, total_messages - (page - 1) * page_size)
        
        # 获取当前页的消息
        page_messages = all_messages[start_index:end_index]
        
        # 转换为API需要的格式
        api_messages = []
        for message in page_messages:
            api_messages.append({
                "role": message["role"],
                "content": message["content"],
                "timestamp": message.get("timestamp", "")
            })
        
        return {
            "messages": api_messages,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_messages": total_messages,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
        }
    
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
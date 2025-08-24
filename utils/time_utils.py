"""
时间工具模块
用于计算上次对话时间间隔
"""
import os
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

class TimeTracker:
    """时间跟踪器"""
    
    def __init__(self, history_dir: str):
        """
        初始化时间跟踪器
        
        Args:
            history_dir: 历史记录存储目录
        """
        self.history_dir = history_dir
    
    def _get_character_history_file(self, character_id: str) -> str:
        """
        获取角色历史记录文件路径
        
        Args:
            character_id: 角色ID
            
        Returns:
            历史记录文件路径
        """
        return os.path.join(self.history_dir, f"{character_id}_history.log")
    
    def get_last_message_time(self, character_id: str) -> Optional[datetime]:
        """
        获取角色最后一条消息的时间
        
        Args:
            character_id: 角色ID
            
        Returns:
            最后一条消息的时间，如果没有历史记录则返回None
        """
        history_file = self._get_character_history_file(character_id)
        
        if not os.path.exists(history_file):
            return None
        
        try:
            # 读取文件最后一行
            with open(history_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines:
                    return None
                
                # 从最后一行开始查找
                for line in reversed(lines):
                    line = line.strip()
                    if line:
                        try:
                            message = json.loads(line)
                            # 检查role是否为assistant
                            if message.get("role") == "assistant":
                                timestamp_str = message.get("timestamp")
                                if timestamp_str:
                                    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        except (json.JSONDecodeError, ValueError):
                            continue
                
                return None 
            
        except Exception as e:
            print(f"读取最后消息时间失败: {e}")
            return None
    
    def format_time_elapsed(self, last_time: Optional[datetime], current_time: datetime) -> str:
        """
        格式化时间间隔
        
        Args:
            last_time: 上次时间
            current_time: 当前时间
            
        Returns:
            格式化的时间间隔字符串
        """
        if last_time is None:
            return ""
        
        delta = current_time - last_time
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 60:
            return "<1分钟"
        elif total_seconds < 3600:  # 小于1小时
            minutes = total_seconds // 60
            return f"{minutes}分钟"
        elif total_seconds < 259200:  # 小于72小时
            hours = total_seconds // 3600
            return f"{hours}小时"
        else:
            days = total_seconds // 86400
            return f"{days}天"
    
    def get_time_elapsed_prefix(self, character_id: str) -> str:
        """
        获取时间间隔前缀
        
        Args:
            character_id: 角色ID
            
        Returns:
            时间间隔前缀，如"距上次对话xx"
        """
        last_time = self.get_last_message_time(character_id)
        current_time = datetime.now()
        
        time_elapsed = self.format_time_elapsed(last_time, current_time)
        
        if time_elapsed:
            return f"距上次对话：{time_elapsed}"
        else:
            return ""

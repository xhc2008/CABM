"""
提示词日志工具
记录发送给聊天模型的完整提示词
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

class PromptLogger:
    """提示词日志记录器"""
    
    def __init__(self, log_file: str = "log.txt"):
        """
        初始化日志记录器
        
        参数:
            log_file: 日志文件路径
        """
        self.log_file = log_file
        self.logger = logging.getLogger("PromptLogger")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else "."
        os.makedirs(log_dir, exist_ok=True)
    
    def log_prompt(self, messages: List[Dict[str, str]], character_name: str = None, user_query: str = None):
        """
        记录完整的提示词到日志文件
        
        参数:
            messages: 发送给模型的消息列表
            character_name: 角色名称
            user_query: 用户查询
        """
        try:
            # 构建日志条目
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "character_name": character_name,
                "user_query": user_query,
                "messages": messages,
                "total_messages": len(messages)
            }
            
            # 计算总字符数
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            log_entry["total_characters"] = total_chars
            
            # 写入日志文件
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            
            self.logger.info(f"记录提示词日志: {len(messages)} 条消息, {total_chars} 字符")
            
        except Exception as e:
            self.logger.error(f"记录提示词日志失败: {e}")
    
    def log_formatted_prompt(self, system_prompt: str, user_prompt: str, memory_context: str = "", 
                           character_name: str = None, user_query: str = None):
        """
        记录格式化的提示词（分别记录system和user部分）
        
        参数:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            memory_context: 记忆上下文
            character_name: 角色名称
            user_query: 原始用户查询
        """
        try:
            # 构建完整的消息列表
            messages = []
            
            # 添加系统消息
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加用户消息（包含记忆上下文）
            user_content = ""
            if memory_context:
                user_content += memory_context + "\n\n"
            user_content += user_prompt
            
            messages.append({
                "role": "user", 
                "content": user_content
            })
            
            # 记录到日志
            self.log_prompt(messages, character_name, user_query)
            
        except Exception as e:
            self.logger.error(f"记录格式化提示词失败: {e}")
    
    def get_recent_logs(self, count: int = 10) -> List[Dict]:
        """
        获取最近的日志条目
        
        参数:
            count: 返回的条目数量
            
        返回:
            最近的日志条目列表
        """
        try:
            if not os.path.exists(self.log_file):
                return []
            
            logs = []
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            
            # 返回最近的条目
            return logs[-count:] if len(logs) > count else logs
            
        except Exception as e:
            self.logger.error(f"读取日志失败: {e}")
            return []
    
    def clear_logs(self):
        """清空日志文件"""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            self.logger.info("日志文件已清空")
        except Exception as e:
            self.logger.error(f"清空日志失败: {e}")

# 创建全局提示词日志记录器
prompt_logger = PromptLogger()

if __name__ == "__main__":
    # 测试提示词日志记录器
    
    # 测试记录消息列表
    messages = [
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "你好，请介绍一下自己。"}
    ]
    
    prompt_logger.log_prompt(messages, "test_character", "你好")
    
    # 测试记录格式化提示词
    prompt_logger.log_formatted_prompt(
        system_prompt="你是一个有用的AI助手。",
        user_prompt="请介绍一下自己。",
        memory_context="用户之前说过他叫小明。",
        character_name="test_character",
        user_query="介绍自己"
    )
    
    # 获取最近的日志
    recent_logs = prompt_logger.get_recent_logs(5)
    print(f"最近的 {len(recent_logs)} 条日志:")
    for i, log in enumerate(recent_logs, 1):
        print(f"{i}. {log['timestamp']} - {log.get('character_name', 'unknown')} - {log.get('total_messages', 0)} 条消息")
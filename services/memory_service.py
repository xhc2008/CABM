"""
记忆服务模块
管理角色的记忆数据库
"""
import os
import sys
import logging
from typing import Dict, Optional
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.memory_utils import ChatHistoryVectorDB
from services.config_service import config_service

class MemoryService:
    """记忆服务类"""
    
    def __init__(self):
        """初始化记忆服务"""
        self.memory_databases: Dict[str, ChatHistoryVectorDB] = {}
        self.current_character = None
        self.logger = logging.getLogger("MemoryService")
        
        # 设置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def initialize_character_memory(self, character_name: str) -> bool:
        """
        初始化指定角色的记忆数据库
        
        参数:
            character_name: 角色名称
            
        返回:
            是否初始化成功
        """
        try:
            if character_name not in self.memory_databases:
                # 创建新的记忆数据库
                memory_db = ChatHistoryVectorDB(character_name=character_name)
                memory_db.initialize_database()
                self.memory_databases[character_name] = memory_db
                self.logger.info(f"初始化角色记忆数据库: {character_name}")
            
            self.current_character = character_name
            return True
            
        except Exception as e:
            self.logger.error(f"初始化角色记忆数据库失败 {character_name}: {e}")
            return False
    
    def get_current_memory_db(self) -> Optional[ChatHistoryVectorDB]:
        """
        获取当前角色的记忆数据库
        
        返回:
            当前角色的记忆数据库，如果没有则返回None
        """
        if self.current_character and self.current_character in self.memory_databases:
            return self.memory_databases[self.current_character]
        return None
    
    def search_memory(self, query: str, character_name: str = None, top_k: int = 3, timeout: int = 10) -> str:
        """
        搜索记忆并返回格式化的提示词
        
        参数:
            query: 查询文本
            character_name: 角色名称，如果为None则使用当前角色
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            格式化的记忆提示词
        """
        if character_name is None:
            character_name = self.current_character
        
        if not character_name:
            self.logger.warning("没有指定角色，无法搜索记忆")
            return ""
        
        self.logger.info(f"开始记忆搜索: 角色={character_name}, 查询='{query}', top_k={top_k}, 超时={timeout}秒")
        
        # 确保角色记忆数据库已初始化
        if not self.initialize_character_memory(character_name):
            self.logger.error(f"角色记忆数据库初始化失败: {character_name}")
            return ""
        
        memory_db = self.memory_databases[character_name]
        result = memory_db.get_relevant_memory(query, top_k, timeout)
        
        if result:
            self.logger.info(f"记忆搜索完成: 生成了 {len(result)} 字符的记忆上下文")
        else:
            self.logger.info("记忆搜索完成: 未找到相关记忆")
        
        return result
    
    def add_conversation(self, user_message: str, assistant_message: str, character_name: str = None):
        """
        添加对话到记忆数据库
        
        参数:
            user_message: 用户消息
            assistant_message: 助手回复
            character_name: 角色名称，如果为None则使用当前角色
        """
        if character_name is None:
            character_name = self.current_character
        
        if not character_name:
            self.logger.warning("没有指定角色，无法添加对话记录")
            return
        
        # 确保角色记忆数据库已初始化
        if not self.initialize_character_memory(character_name):
            return
        
        memory_db = self.memory_databases[character_name]
        memory_db.add_chat_turn(user_message, assistant_message)
        
        # 保存到文件
        try:
            memory_db.save_to_file()
        except Exception as e:
            self.logger.error(f"保存记忆数据库失败: {e}")
    
    def set_current_character(self, character_name: str) -> bool:
        """
        设置当前角色
        
        参数:
            character_name: 角色名称
            
        返回:
            是否设置成功
        """
        return self.initialize_character_memory(character_name)
    
    def get_memory_stats(self, character_name: str = None) -> Dict:
        """
        获取记忆数据库统计信息
        
        参数:
            character_name: 角色名称，如果为None则使用当前角色
            
        返回:
            统计信息字典
        """
        if character_name is None:
            character_name = self.current_character
        
        if not character_name or character_name not in self.memory_databases:
            return {"error": "角色记忆数据库未初始化"}
        
        memory_db = self.memory_databases[character_name]
        return {
            "character_name": character_name,
            "total_records": len(memory_db.vectors),
            "model": memory_db.model,
            "database_file": memory_db.db_file_path
        }

# 创建全局记忆服务实例
memory_service = MemoryService()

if __name__ == "__main__":
    # 测试记忆服务
    import time
    
    # 初始化角色记忆
    if memory_service.initialize_character_memory("test_character"):
        print("记忆数据库初始化成功")
        
        # 添加对话
        memory_service.add_conversation(
            "你好，我叫小明",
            "你好小明！很高兴认识你。"
        )
        
        # 搜索记忆
        memory_prompt = memory_service.search_memory("我的名字")
        print("搜索结果:")
        print(memory_prompt)
        
        # 获取统计信息
        stats = memory_service.get_memory_stats()
        print("统计信息:")
        print(stats)
    else:
        print("记忆数据库初始化失败")
"""
记忆服务模块
管理角色的记忆数据库
"""
import os
import sys
import logging
import asyncio
from typing import Dict, Optional, Tuple
from pathlib import Path
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.memory_utils import ChatHistoryVectorDB
from services.config_service import config_service
from services.character_details_service import character_details_service
from config import get_memory_config,  get_RAG_config

class MemoryService:
    """记忆服务类"""
    
    def __init__(self):
        """初始化记忆服务"""
        self.memory_databases: Dict[str, ChatHistoryVectorDB] = {}
        self.story_databases: Dict[str, ChatHistoryVectorDB] = {}
        self.current_character = None
        self.current_story = None
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
                memory_db = ChatHistoryVectorDB(RAG_config=get_RAG_config() , character_name=character_name)
                memory_db.initialize_database()
                self.memory_databases[character_name] = memory_db
                self.logger.info(f"初始化角色记忆数据库: {character_name}")
            
            self.current_character = character_name
            return True
            
        except Exception as e:
            traceback.print_exc()
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
    
    def search_memory(self, query: str, character_name: str = None, top_k: int = None, timeout: int = None) -> str:
        """
        搜索记忆并返回格式化的提示词
        
        参数:
            query: 查询文本
            character_name: 角色名称，如果为None则使用当前角色
            top_k: 返回的最相似结果数量，如果为None则使用配置中的值
            timeout: 超时时间（秒），如果为None则使用配置中的值
            
        返回:
            格式化的记忆提示词
        """
        if character_name is None:
            character_name = self.current_character
        
        if not character_name:
            self.logger.warning("没有指定角色，无法搜索记忆")
            return ""
        
        # 从配置中获取默认值
        memory_config = get_memory_config()
        if top_k is None:
            top_k = memory_config['top_k']
        if timeout is None:
            timeout = memory_config['timeout']
        
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
    
    async def search_memory_and_details_async(self, query: str, character_name: str = None, 
                                            memory_top_k: int = None, details_top_k: int = 3, 
                                            timeout: int = None) -> Tuple[str, str]:
        """
        异步同时搜索记忆和角色详细信息
        
        参数:
            query: 查询文本
            character_name: 角色名称，如果为None则使用当前角色
            memory_top_k: 记忆检索返回的最相似结果数量
            details_top_k: 详细信息检索返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            (记忆提示词, 角色详细信息提示词) 的元组
        """
        if character_name is None:
            character_name = self.current_character
        
        if not character_name:
            self.logger.warning("没有指定角色，无法搜索记忆和详细信息")
            return "", ""
        
        # 从配置中获取默认值
        memory_config = get_memory_config()
        if memory_top_k is None:
            memory_top_k = memory_config['top_k']
        if timeout is None:
            timeout = memory_config['timeout']
        
        self.logger.info(f"开始异步记忆和详细信息检索: 角色={character_name}, 查询='{query}'")
        
        # 创建异步任务
        loop = asyncio.get_event_loop()
        
        # 记忆检索任务
        memory_task = loop.run_in_executor(
            None, 
            self.search_memory, 
            query, character_name, memory_top_k, timeout
        )
        
        # 角色详细信息检索任务
        details_task = character_details_service.search_character_details_async(
            character_name, query, details_top_k, timeout
        )
        
        try:
            # 等待两个任务完成
            memory_result, details_result = await asyncio.gather(
                memory_task, 
                details_task, 
                return_exceptions=True
            )
            
            # 处理异常结果
            if isinstance(memory_result, Exception):
                self.logger.error(f"记忆检索异常: {memory_result}")
                memory_result = ""
            
            if isinstance(details_result, Exception):
                self.logger.error(f"详细信息检索异常: {details_result}")
                details_result = ""
            
            self.logger.info(f"异步检索完成: 记忆={len(memory_result)}字符, 详细信息={len(details_result)}字符")
            return memory_result, details_result
            
        except Exception as e:
            self.logger.error(f"异步检索失败: {e}")
            traceback.print_exc()
            return "", ""
    
    def search_memory_and_details(self, query: str, character_name: str = None, 
                                memory_top_k: int = None, details_top_k: int = 3, 
                                timeout: int = None) -> Tuple[str, str]:
        """
        同步搜索记忆和角色详细信息（使用异步实现）
        
        参数:
            query: 查询文本
            character_name: 角色名称，如果为None则使用当前角色
            memory_top_k: 记忆检索返回的最相似结果数量
            details_top_k: 详细信息检索返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            (记忆提示词, 角色详细信息提示词) 的元组
        """
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # 运行异步函数
            return loop.run_until_complete(
                self.search_memory_and_details_async(
                    query, character_name, memory_top_k, details_top_k, timeout
                )
            )
        except Exception as e:
            self.logger.error(f"同步检索失败: {e}")
            traceback.print_exc()
            return "", ""
    
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
            traceback.print_exc()
    
    def initialize_story_memory(self, story_id: str) -> bool:
        """
        初始化指定故事的记忆数据库
        
        参数:
            story_id: 故事ID
            
        返回:
            是否初始化成功
        """
        try:
            if story_id not in self.story_databases:
                # 创建新的故事记忆数据库
                memory_db = ChatHistoryVectorDB(RAG_config=get_RAG_config(), character_name=story_id, is_story=True)
                memory_db.initialize_database()
                self.story_databases[story_id] = memory_db
                self.logger.info(f"初始化故事记忆数据库: {story_id}")
            
            self.current_story = story_id
            return True
            
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"初始化故事记忆数据库失败 {story_id}: {e}")
            return False
    
    def search_story_memory(self, query: str, story_id: str = None, top_k: int = None, timeout: int = None) -> str:
        """
        搜索故事记忆并返回格式化的提示词
        
        参数:
            query: 查询文本
            story_id: 故事ID，如果为None则使用当前故事
            top_k: 返回的最相似结果数量，如果为None则使用配置中的值
            timeout: 超时时间（秒），如果为None则使用配置中的值
            
        返回:
            格式化的记忆提示词
        """
        if story_id is None:
            story_id = self.current_story
        
        if not story_id:
            self.logger.warning("没有指定故事，无法搜索记忆")
            return ""
        
        # 从配置中获取默认值
        memory_config = get_memory_config()
        if top_k is None:
            top_k = memory_config['top_k']
        if timeout is None:
            timeout = memory_config['timeout']
        
        self.logger.info(f"开始故事记忆搜索: 故事={story_id}, 查询='{query}', top_k={top_k}, 超时={timeout}秒")
        
        # 确保故事记忆数据库已初始化
        if not self.initialize_story_memory(story_id):
            self.logger.error(f"故事记忆数据库初始化失败: {story_id}")
            return ""
        
        memory_db = self.story_databases[story_id]
        result = memory_db.get_relevant_memory(query, top_k, timeout)
        
        if result:
            self.logger.info(f"故事记忆搜索完成: 生成了 {len(result)} 字符的记忆上下文")
        else:
            self.logger.info("故事记忆搜索完成: 未找到相关记忆")
        
        return result
    
    def add_story_conversation(self, user_message: str, assistant_message: str, story_id: str = None):
        """
        添加对话到故事记忆数据库
        
        参数:
            user_message: 用户消息
            assistant_message: 助手回复
            story_id: 故事ID，如果为None则使用当前故事
        """
        if story_id is None:
            story_id = self.current_story
        
        if not story_id:
            self.logger.warning("没有指定故事，无法添加对话记录")
            return
        
        # 确保故事记忆数据库已初始化
        if not self.initialize_story_memory(story_id):
            return
        
        memory_db = self.story_databases[story_id]
        memory_db.add_chat_turn(user_message, assistant_message)
        
        # 保存到文件
        try:
            memory_db.save_to_file()
        except Exception as e:
            self.logger.error(f"保存故事记忆数据库失败: {e}")
            traceback.print_exc()
    
    def add_story_message(self, speaker_name: str, message: str, story_id: str = None):
        """
        添加单条消息到故事记忆数据库（用于多角色对话）
        
        参数:
            speaker_name: 说话者名称
            message: 消息内容
            story_id: 故事ID，如果为None则使用当前故事
        """
        if story_id is None:
            story_id = self.current_story
        
        if not story_id:
            self.logger.warning("没有指定故事，无法添加消息记录")
            return
        
        # 确保故事记忆数据库已初始化
        if not self.initialize_story_memory(story_id):
            return
        
        memory_db = self.story_databases[story_id]
        memory_db.add_single_message(speaker_name, message)
        
        # 保存到文件
        try:
            memory_db.save_to_file()
        except Exception as e:
            self.logger.error(f"保存故事记忆数据库失败: {e}")
            traceback.print_exc()
    
    def set_current_character(self, character_name: str) -> bool:
        """
        设置当前角色
        
        参数:
            character_name: 角色名称
            
        返回:
            是否设置成功
        """
        return self.initialize_character_memory(character_name)
    
    def set_current_story(self, story_id: str) -> bool:
        """
        设置当前故事
        
        参数:
            story_id: 故事ID
            
        返回:
            是否设置成功
        """
        return self.initialize_story_memory(story_id)
    
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
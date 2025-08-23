"""
记忆服务模块
管理角色的记忆数据库
"""
import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.config_service import config_service
from services.character_details_service import character_details_service
from services.settings_service import settings_service
from config import get_memory_config,  get_RAG_config

def create_memory_database(character_name: str, is_story: bool = False):
    """
    根据设置创建相应的内存数据库实例
    
    参数:
        character_name: 角色名称或故事ID
        is_story: 是否为故事模式
        
    返回:
        内存数据库实例
    """
    storage_type = settings_service.get_setting("storage", "type", "json")
    
    if storage_type == "json":
        # 使用JSON存储（兼容老版本）
        # 注意：JSON存储类不支持is_story参数，只使用character_name
        from utils.ori_memory_utils import ChatHistoryVectorDB
        return ChatHistoryVectorDB(character_name=character_name)
    elif storage_type == "faiss_peewee":
        # 使用FAISS+Peewee数据库（更快更好）
        from utils.peewee_memory_utils import PeeweeChatHistoryVectorDB as ChatHistoryVectorDB
        return ChatHistoryVectorDB(RAG_config=get_RAG_config(), character_name=character_name, is_story=is_story)
    else:
        # 默认使用FAISS+Peewee
        from utils.peewee_memory_utils import PeeweeChatHistoryVectorDB as ChatHistoryVectorDB
        return ChatHistoryVectorDB(RAG_config=get_RAG_config(), character_name=character_name, is_story=is_story)

def migrate_memory_data(from_type: str, to_type: str):
    """
    迁移所有记忆数据和聊天历史从一种存储类型到另一种
    
    参数:
        from_type: 源存储类型 ("json" 或 "faiss_peewee")
        to_type: 目标存储类型 ("json" 或 "faiss_peewee")
        
    返回:
        是否迁移成功
    """
    if from_type == to_type:
        return True
        
    logger = logging.getLogger("MemoryService")
    logger.info(f"开始迁移所有记忆数据从 {from_type} 到 {to_type}")
    
    try:
        # 导入HistoryManager
        from utils.history_utils import HistoryManager
        
        # 获取所有角色列表
        characters_dir = Path("characters")
        if not characters_dir.exists():
            logger.warning("角色目录不存在，无需迁移")
            return True
            
        character_files = list(characters_dir.glob("*.toml"))
        if not character_files:
            logger.warning("未找到角色文件，无需迁移")
            return True
            
        # 提取角色名称
        character_names = [f.stem for f in character_files]
        logger.info(f"找到 {len(character_names)} 个角色需要迁移: {character_names}")
        
        success_count = 0
        total_count = len(character_names)
        
        # 迁移每个角色的数据
        for character_name in character_names:
            try:
                logger.info(f"正在迁移角色: {character_name}")
                
                # 创建源数据库实例
                if from_type == "json":
                    from utils.ori_memory_utils import ChatHistoryVectorDB
                    source_db = ChatHistoryVectorDB(character_name=character_name)
                else:
                    from utils.peewee_memory_utils import PeeweeChatHistoryVectorDB
                    source_db = PeeweeChatHistoryVectorDB(RAG_config=get_RAG_config(), character_name=character_name, is_story=False)
                
                # 创建目标数据库实例
                if to_type == "json":
                    from utils.ori_memory_utils import ChatHistoryVectorDB
                    target_db = ChatHistoryVectorDB(character_name=character_name)
                else:
                    from utils.peewee_memory_utils import PeeweeChatHistoryVectorDB
                    target_db = PeeweeChatHistoryVectorDB(RAG_config=get_RAG_config(), character_name=character_name, is_story=False)
                
                # 初始化数据库
                source_db.initialize_database()
                target_db.initialize_database()
                
                # 获取源数据库的所有对话记录
                migrated_records = 0
                
                if from_type == "json":
                    # 从JSON迁移到数据库
                    if hasattr(source_db, 'metadata') and source_db.metadata:
                        logger.info(f"角色 {character_name} 找到 {len(source_db.metadata)} 条JSON记录需要迁移")
                        
                        # 迁移每条记录
                        for meta in source_db.metadata:
                            if meta.get('type') == 'conversation':
                                user_msg = meta.get('user_message', '')
                                assistant_msg = meta.get('assistant_message', '')
                                timestamp = meta.get('timestamp', '')
                                
                                if user_msg and assistant_msg:
                                    target_db.add_chat_turn(user_msg, assistant_msg, timestamp)
                                    migrated_records += 1
                        
                        # 保存目标数据库
                        if migrated_records > 0:
                            target_db.save_to_file()
                            logger.info(f"角色 {character_name} 迁移完成: {migrated_records} 条记录")
                        else:
                            logger.info(f"角色 {character_name} 无有效记录需要迁移")
                    else:
                        logger.info(f"角色 {character_name} JSON源数据库为空，无需迁移")
                        
                else:
                    # 从数据库迁移到JSON
                    try:
                        # 获取数据库中的所有对话记录
                        if hasattr(source_db, 'get_recent_conversations'):
                            # 获取所有对话记录（设置一个很大的limit）
                            conversations = source_db.get_recent_conversations(limit=10000)
                            logger.info(f"角色 {character_name} 找到 {len(conversations)} 条数据库记录需要迁移")
                            
                            # 迁移每条记录
                            for conv in conversations:
                                user_msg = conv.get('user_message', '')
                                assistant_msg = conv.get('assistant_message', '')
                                timestamp = conv.get('timestamp', '')
                                
                                if user_msg and assistant_msg:
                                    # 转换timestamp格式
                                    if hasattr(timestamp, 'isoformat'):
                                        timestamp = timestamp.isoformat()
                                    elif isinstance(timestamp, str):
                                        timestamp = timestamp
                                    else:
                                        timestamp = datetime.now().isoformat()
                                    
                                    target_db.add_chat_turn(user_msg, assistant_msg, timestamp)
                                    migrated_records += 1
                            
                            # 保存目标数据库
                            if migrated_records > 0:
                                target_db.save_to_file()
                                logger.info(f"角色 {character_name} 迁移完成: {migrated_records} 条记录")
                            else:
                                logger.info(f"角色 {character_name} 无有效记录需要迁移")
                        else:
                            logger.warning(f"角色 {character_name} 源数据库不支持获取对话记录")
                            
                    except Exception as db_error:
                        logger.error(f"角色 {character_name} 数据库记录读取失败: {db_error}")
                        traceback.print_exc()
                
                # 迁移聊天历史记录
                try:
                    history_manager = HistoryManager(config_service.get_app_config()["history_dir"])
                    old_history_file = os.path.join(history_manager.history_dir, f"{character_name}_history.log")
                    
                    if os.path.exists(old_history_file):
                        # 读取旧的历史记录
                        old_history = []
                        with open(old_history_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        old_history.append(json.loads(line))
                                    except json.JSONDecodeError:
                                        continue
                        
                        if old_history:
                            logger.info(f"角色 {character_name} 找到 {len(old_history)} 条历史记录需要迁移")
                            
                            # 迁移每条历史记录
                            for record in old_history:
                                role = record.get('role')
                                content = record.get('content')
                                timestamp = record.get('timestamp')
                                
                                if role and content:
                                    # 保存到新的历史记录管理器
                                    history_manager.save_message(character_name, role, content)
                            
                            logger.info(f"角色 {character_name} 历史记录迁移完成: {len(old_history)} 条记录")
                        else:
                            logger.info(f"角色 {character_name} 无历史记录需要迁移")
                    else:
                        logger.info(f"角色 {character_name} 无历史记录文件需要迁移")
                except Exception as history_error:
                    logger.error(f"角色 {character_name} 历史记录迁移失败: {history_error}")
                    traceback.print_exc()
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"角色 {character_name} 迁移失败: {e}")
                traceback.print_exc()
                # 继续迁移其他角色
                continue
        
        logger.info(f"记忆数据迁移完成: {success_count}/{total_count} 个角色迁移成功")
        
        # 如果至少有一个角色迁移成功，就认为整体迁移成功
        return success_count > 0 or total_count == 0
            
    except Exception as e:
        logger.error(f"记忆数据迁移失败: {e}")
        traceback.print_exc()
        return False

class MemoryService:
    """记忆服务类"""
    
    def __init__(self):
        """初始化记忆服务"""
        self.memory_databases: Dict[str, Any] = {}
        self.story_databases: Dict[str, Any] = {}
        self.current_character = None
        self.current_story = None
        self.logger = logging.getLogger("MemoryService")
        
        # 只在根日志记录器没有配置时才添加处理器
        # 如果根日志记录器已经有处理器，就不要重复添加
        root_logger = logging.getLogger()
        if not root_logger.handlers:
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
                # 使用工厂函数创建新的记忆数据库
                memory_db = create_memory_database(character_name, is_story=False)
                memory_db.initialize_database()
                self.memory_databases[character_name] = memory_db
                storage_type = settings_service.get_setting("storage", "type", "json")
                self.logger.info(f"初始化角色记忆数据库: {character_name} (存储类型: {storage_type})")
            
            self.current_character = character_name
            return True
            
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"初始化角色记忆数据库失败 {character_name}: {e}")
            return False
    
    def get_current_memory_db(self) -> Optional[Any]:
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
                # 使用工厂函数创建新的故事记忆数据库
                memory_db = create_memory_database(story_id, is_story=True)
                memory_db.initialize_database()
                self.story_databases[story_id] = memory_db
                storage_type = settings_service.get_setting("storage", "type", "json")
                self.logger.info(f"初始化故事记忆数据库: {story_id} (存储类型: {storage_type})")
            
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
        return memory_db.get_stats()

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

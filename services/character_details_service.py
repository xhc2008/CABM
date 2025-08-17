"""
角色详细信息服务模块
管理角色的详细信息向量数据库
"""
import os
import sys
import logging
import json
import asyncio
from typing import Dict, Optional, List
from pathlib import Path
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.memory_utils import ChatHistoryVectorDB
from services.config_service import config_service
from config import get_RAG_config

class CharacterDetailsService:
    """角色详细信息服务类"""
    
    def __init__(self):
        """初始化角色详细信息服务"""
        self.details_databases: Dict[str, ChatHistoryVectorDB] = {}
        self.logger = logging.getLogger("CharacterDetailsService")
        
        # 设置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def initialize_character_details(self, character_id: str) -> bool:
        """
        初始化指定角色的详细信息数据库
        
        参数:
            character_id: 角色ID
            
        返回:
            是否初始化成功
        """
        try:
            if character_id not in self.details_databases:
                # 创建新的详细信息数据库
                details_db = CharacterDetailsVectorDB(
                    RAG_config=get_RAG_config(), 
                    character_id=character_id
                )
                details_db.initialize_database()
                self.details_databases[character_id] = details_db
                self.logger.info(f"初始化角色详细信息数据库: {character_id}")
            
            return True
            
        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"初始化角色详细信息数据库失败 {character_id}: {e}")
            return False
    
    def build_character_details(self, character_id: str, text_files: List[str]) -> bool:
        """
        构建角色详细信息向量数据库
        
        参数:
            character_id: 角色ID
            text_files: 文本文件路径列表
            
        返回:
            是否构建成功
        """
        try:
            # 确保数据库已初始化
            if not self.initialize_character_details(character_id):
                return False
            
            details_db = self.details_databases[character_id]
            
            # 处理每个文本文件
            for file_path in text_files:
                if not os.path.exists(file_path):
                    self.logger.warning(f"文件不存在: {file_path}")
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    
                    if not content:
                        self.logger.warning(f"文件为空: {file_path}")
                        continue
                    
                    # 按空行分段（\n\n）
                    segments = [seg.strip() for seg in content.split('\n\n') if seg.strip()]
                    
                    if not segments:
                        self.logger.warning(f"文件没有有效内容: {file_path}")
                        continue
                    
                    # 添加到向量数据库
                    for segment in segments:
                        details_db.add_text(segment)
                    
                    self.logger.info(f"处理文件 {file_path}: 添加了 {len(segments)} 个段落")
                    
                except Exception as e:
                    self.logger.error(f"处理文件失败 {file_path}: {e}")
                    continue
            
            # 保存数据库
            details_db.save_to_file()
            self.logger.info(f"角色详细信息数据库构建完成: {character_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"构建角色详细信息数据库失败 {character_id}: {e}")
            traceback.print_exc()
            return False
    
    async def search_character_details_async(self, character_id: str, query: str, top_k: int = 3, timeout: int = 10) -> str:
        """
        异步搜索角色详细信息
        
        参数:
            character_id: 角色ID
            query: 查询文本
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            格式化的角色详细信息提示词
        """
        loop = asyncio.get_event_loop()
        
        # 在线程池中执行同步搜索
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.search_character_details, character_id, query, top_k, timeout)
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: future.result()), 
                    timeout=timeout
                )
                return result
            except asyncio.TimeoutError:
                self.logger.warning(f"角色详细信息检索超时 ({timeout}秒): {character_id}")
                return ""
            except Exception as e:
                self.logger.error(f"异步角色详细信息检索失败: {e}")
                return ""
    
    def search_character_details(self, character_id: str, query: str, top_k: int = 3, timeout: int = 10) -> str:
        """
        搜索角色详细信息并返回格式化的提示词
        
        参数:
            character_id: 角色ID
            query: 查询文本
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            格式化的角色详细信息提示词
        """
        try:
            # 确保数据库已初始化
            if not self.initialize_character_details(character_id):
                return ""
            
            details_db = self.details_databases[character_id]
            
            # 检查数据库是否有内容
            if not hasattr(details_db, 'rag') or not details_db.rag:
                self.logger.info(f"角色 {character_id} 没有详细信息数据")
                return ""
            
            self.logger.info(f"开始角色详细信息检索: 角色={character_id}, 查询='{query}', top_k={top_k}")
            
            # 搜索相关内容
            results = details_db.search(query, top_k, timeout)
            
            if not results:
                self.logger.info(f"角色详细信息检索完成: 未找到相关内容")
                return ""
            
            # 格式化为提示词
            details_texts = [result['text'] for result in results]
            details_prompt = "你的相关人物细节：" + "；".join(details_texts)
            
            self.logger.info(f"角色详细信息检索完成: 生成了 {len(details_prompt)} 字符的详细信息上下文")
            return details_prompt
            
        except Exception as e:
            self.logger.error(f"搜索角色详细信息失败 {character_id}: {e}")
            traceback.print_exc()
            return ""
    
    def get_character_details_stats(self, character_id: str) -> Dict:
        """
        获取角色详细信息数据库统计信息
        
        参数:
            character_id: 角色ID
            
        返回:
            统计信息字典
        """
        if character_id not in self.details_databases:
            return {"error": "角色详细信息数据库未初始化"}
        
        details_db = self.details_databases[character_id]
        return {
            "character_id": character_id,
            "database_file": details_db.db_file_path if hasattr(details_db, 'db_file_path') else "未知"
        }


class CharacterDetailsVectorDB(ChatHistoryVectorDB):
    """角色详细信息向量数据库类，继承自ChatHistoryVectorDB"""
    
    def __init__(self, RAG_config: dict, character_id: str):
        """
        初始化角色详细信息向量数据库
        
        参数:
            RAG_config: RAG配置字典
            character_id: 角色ID
        """
        # 调用父类构造函数，使用特殊的命名约定
        super().__init__(
            RAG_config=RAG_config,
            character_name=character_id,
            is_story=False
        )
        
        # 重新设置数据目录为角色详细信息专用目录
        self.data_details = os.path.join('data', 'details')
        os.makedirs(self.data_details, exist_ok=True)
        
        # 设置详细信息数据库文件路径
        self.db_file_path = os.path.join(self.data_details, f'{character_id}.json')
        
        # 更新日志器名称
        self.logger = logging.getLogger(f"CharacterDetailsDB_{character_id}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def save_to_file(self, file_path: str = None):
        """
        将向量数据库保存到<角色ID>.json文件
        
        参数:
            file_path: 保存路径，如果为None则使用默认路径
        """
        if file_path is None:
            file_path = self.db_file_path
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存RAG数据到同一目录
            rag_save = self.rag.save_to_file(os.path.dirname(file_path))
            data = {
                'character_id': self.character_name,
                'rag': rag_save,
                'last_updated': self.get_current_timestamp()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            self.logger.info(f"角色详细信息数据库已保存到 {file_path}")
        except Exception as e:
            self.logger.error(f"保存角色详细信息数据库失败: {e}")
            raise
    
    def load_from_file(self, file_path: str = None):
        """
        从<角色ID>.json文件加载向量数据库
        
        参数:
            file_path: 加载路径，如果为None则使用默认路径
        """
        if file_path is None:
            file_path = self.db_file_path
        
        if not os.path.exists(file_path):
            self.logger.info(f"详细信息数据库文件不存在，将创建新的数据库: {file_path}")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.character_name = data.get('character_id', self.character_name)
            self.logger.info(f"加载角色详细信息RAG缓存")
            self.rag.load_from_file(data.get('rag', None))
            self.logger.info(f"角色详细信息数据库加载完成，角色: {self.character_name}")
        except Exception as e:
            self.logger.error(f"加载详细信息数据库失败: {e}")
    
    def get_current_timestamp(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# 创建全局角色详细信息服务实例
character_details_service = CharacterDetailsService()

if __name__ == "__main__":
    # 测试角色详细信息服务
    import tempfile
    
    # 创建测试文件
    test_content = """这是第一段内容。
这里有一些角色的背景信息。

这是第二段内容。
这里描述了角色的性格特点。

这是第三段内容。
这里是角色的经历和故事。"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # 测试构建详细信息数据库
        if character_details_service.build_character_details("test_character", [test_file_path]):
            print("详细信息数据库构建成功")
            
            # 测试搜索
            result = character_details_service.search_character_details("test_character", "角色的性格")
            print("搜索结果:")
            print(result)
            
            # 获取统计信息
            stats = character_details_service.get_character_details_stats("test_character")
            print("统计信息:")
            print(stats)
        else:
            print("详细信息数据库构建失败")
    finally:
        # 清理测试文件
        os.unlink(test_file_path)
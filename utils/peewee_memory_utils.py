"""
基于Peewee ORM的记忆存储工具
使用SQLite数据库进行结构化存储
"""
import os
import signal
import logging
import pickle
from datetime import datetime
import traceback
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import faiss
except ImportError:
    print("警告: faiss-cpu 未安装，请运行: pip install faiss-cpu")
    faiss = None

try:
    from peewee import *
except ImportError:
    print("警告: peewee 未安装，请运行: pip install peewee")
    raise ImportError("peewee 未安装")

from .RAG import RAG
import sys
sys.path.append(r'utils\RAG')

class TimeoutError(Exception):
    """超时异常"""
    pass

def timeout_handler(signum, frame):
    """超时处理函数"""
    raise TimeoutError("操作超时")

# 数据库模型定义
class BaseModel(Model):
    class Meta:
        database = None  # 将在运行时设置

class MemoryRecord(BaseModel):
    """记忆记录模型"""
    id = AutoField(primary_key=True)
    character_name = CharField(max_length=100, index=True)
    text = TextField()
    user_message = TextField(null=True)
    assistant_message = TextField(null=True)
    timestamp = DateTimeField(default=datetime.now, index=True)
    record_type = CharField(max_length=50, default='conversation')  # conversation, story, etc.
    vector_index = IntegerField(null=True)  # FAISS索引中的位置
    similarity_score = FloatField(null=True)  # 最后一次搜索的相似度分数
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        indexes = (
            (('character_name', 'timestamp'), False),
            (('character_name', 'record_type'), False),
        )

class PeeweeChatHistoryVectorDB:
    def __init__(self, RAG_config: dict, model: str = None, character_name: str = "default", is_story: bool = False):
        """
        初始化基于Peewee+FAISS的向量数据库
        
        参数:
            RAG_config: RAG配置字典
            model: 使用的嵌入模型，如果为None则从环境变量读取
            character_name: 角色名称或故事ID，用于确定数据库文件名
            is_story: 是否为故事模式
        """
        if faiss is None:
            raise ImportError("faiss-cpu 未安装，请运行: pip install faiss-cpu")
            
        self.config = RAG_config
        self.character_name = character_name
        self.model = model
        self.is_story = is_story
        
        # 设置日志
        self.logger = logging.getLogger(f"PeeweeMemoryDB_{character_name}")
        
        # 只在根日志记录器没有配置时才添加处理器
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        # 根据模式设置数据目录
        if is_story:
            # 故事模式：保存到 data/saves/{story_id}/
            self.data_memory = os.path.join('data', 'saves', character_name)
        else:
            # 角色模式：保存到 data/memory/{character_name}/
            self.data_memory = os.path.join('data', 'memory', character_name)
        
        os.makedirs(self.data_memory, exist_ok=True)
        
        # 初始化数据库
        self.db_path = os.path.join(self.data_memory, f"{character_name}_memory.db")
        self.database = SqliteDatabase(self.db_path)
        
        # 设置模型的数据库
        BaseModel._meta.database = self.database
        MemoryRecord._meta.database = self.database
        
        # 创建表
        self.database.create_tables([MemoryRecord], safe=True)
        
        # 初始化RAG系统
        self.rag = RAG(RAG_config)
        
        # FAISS相关属性
        self.index = None
        self.vector_dim = RAG_config['Multi_Recall']['Cosine_Similarity']['vector_dim']
        
        # 文件路径
        self.faiss_index_path = os.path.join(self.data_memory, f"{character_name}_faiss.index")
        
        # 初始化FAISS索引
        self._init_faiss_index()
    
    def _init_faiss_index(self):
        """初始化FAISS索引"""
        # 使用L2距离的平面索引，适合中小规模数据
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.logger.info(f"初始化FAISS索引，维度: {self.vector_dim}")
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        获取文本的嵌入向量
        
        参数:
            texts: 文本列表
            
        返回:
            嵌入向量数组
        """
        embeddings = []
        
        # 获取嵌入模型配置
        cosine_config = self.config['Multi_Recall']['Cosine_Similarity']
        
        try:
            if cosine_config['embed_func'] == 'API':
                # 使用API获取嵌入
                from utils.RAG.Multi_Recall.Cosine_Similarity import Embedding_API
                embed_model = Embedding_API(**cosine_config['embed_kwds'])
                
                # 批量获取嵌入
                batch_embeddings = embed_model.embed(texts)
                if batch_embeddings:
                    embeddings = batch_embeddings
                else:
                    # 如果获取失败，使用零向量
                    embeddings = [np.zeros(self.vector_dim).tolist() for _ in texts]
                    
            elif cosine_config['embed_func'] == 'Model':
                # 使用本地模型获取嵌入
                from utils.RAG.Multi_Recall.Cosine_Similarity import Embedding_Model
                embed_model = Embedding_Model(**cosine_config['embed_kwds'])
                
                # 批量获取嵌入
                batch_embeddings = embed_model.embed(texts)
                if batch_embeddings:
                    embeddings = batch_embeddings
                else:
                    # 如果获取失败，使用零向量
                    embeddings = [np.zeros(self.vector_dim).tolist() for _ in texts]
            else:
                # 未知的嵌入方法
                self.logger.warning(f"未知的嵌入方法: {cosine_config['embed_func']}")
                embeddings = [np.zeros(self.vector_dim).tolist() for _ in texts]
                
        except Exception as e:
            self.logger.error(f"获取嵌入失败: {e}")
            traceback.print_exc()
            embeddings = [np.zeros(self.vector_dim).tolist() for _ in texts]
        
        # 转换为numpy数组并归一化
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # 归一化向量（避免除零错误）
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)  # 避免除零
        embeddings_array = embeddings_array / norms
        
        return embeddings_array
    
    def add_text(self, text: str, user_message: str = None, assistant_message: str = None, record_type: str = "conversation"):
        """
        添加单个文本到向量数据库和SQL数据库
        
        参数:
            text: 要添加的文本
            user_message: 用户消息（可选）
            assistant_message: 助手回复（可选）
            record_type: 记录类型
        """
        if not text.strip():
            return
            
        try:
            # 获取嵌入向量
            embeddings = self._get_embeddings([text])
            
            if len(embeddings) > 0:
                # 添加到FAISS索引
                vector_index = self.index.ntotal
                self.index.add(embeddings)
                
                # 保存到数据库
                with self.database.atomic():
                    record = MemoryRecord.create(
                        character_name=self.character_name,
                        text=text,
                        user_message=user_message,
                        assistant_message=assistant_message,
                        record_type=record_type,
                        vector_index=vector_index,
                        timestamp=datetime.now()
                    )
                
                self.logger.info(f"添加记录到数据库: ID={record.id}, 文本='{text[:50]}...'")
                return record.id
                
        except Exception as e:
            self.logger.error(f"添加文本失败: {e}")
            traceback.print_exc()
            return None
    
    def search(self, query: str, top_k: int = 5, timeout: int = 10) -> List[Dict]:
        """
        搜索与查询文本最相似的文本（带超时）
        
        参数:
            query: 查询文本
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            包含相似结果和数据库记录的字典列表
            
        异常:
            TimeoutError: 当操作超时时
        """
        if self.index.ntotal == 0:
            self.logger.info("FAISS索引为空，返回空结果")
            return []
        
        # 设置超时处理（仅在非Windows系统上）
        if os.name != 'nt':  # 非Windows系统
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        try:
            # 获取查询向量
            query_embeddings = self._get_embeddings([query])
            
            if len(query_embeddings) == 0:
                return []
            
            # 在FAISS中搜索
            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_embeddings, k)
            
            results = []
            
            # 从数据库获取对应的记录
            with self.database.atomic():
                for i, (distance, vector_idx) in enumerate(zip(distances[0], indices[0])):
                    try:
                        # 根据vector_index查找数据库记录
                        record = MemoryRecord.get(
                            (MemoryRecord.character_name == self.character_name) &
                            (MemoryRecord.vector_index == int(vector_idx))
                        )
                        
                        similarity = 1.0 / (1.0 + distance)  # 转换为相似度
                        
                        # 更新相似度分数
                        record.similarity_score = similarity
                        record.updated_at = datetime.now()
                        record.save()
                        
                        result = {
                            'id': record.id,
                            'text': record.text,
                            'user_message': record.user_message,
                            'assistant_message': record.assistant_message,
                            'distance': float(distance),
                            'similarity': similarity,
                            'timestamp': record.timestamp,
                            'record_type': record.record_type,
                            'vector_index': record.vector_index
                        }
                        results.append(result)
                        
                    except MemoryRecord.DoesNotExist:
                        self.logger.warning(f"未找到vector_index={vector_idx}的数据库记录")
                        continue
            
            # 记录检索结果到日志
            if results:
                self.logger.info(f"数据库检索查询: '{query}' -> 找到 {len(results)} 条相关记录")
                for i, result in enumerate(results, 1):
                    text_preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
                    self.logger.info(f"  记录 {i}: ID={result['id']}, '{text_preview}' (相似度: {result['similarity']:.3f})")
            else:
                self.logger.info(f"数据库检索查询: '{query}' -> 未找到相关记录")
                
            return results
            
        except TimeoutError:
            self.logger.warning(f"数据库检索超时 ({timeout}秒)")
            return []
        except Exception as e:
            self.logger.error(f"数据库检索失败: {e}")
            traceback.print_exc()
            return []
        finally:
            # 取消超时设置（仅在非Windows系统上）
            if os.name != 'nt':
                signal.alarm(0)
    
    def save_to_file(self, file_path: str = None):
        """
        保存FAISS索引到文件（数据库自动持久化）
        
        参数:
            file_path: 保存路径，如果为None则使用默认路径
        """
        try:
            # 保存FAISS索引
            if self.index.ntotal > 0:
                faiss.write_index(self.index, self.faiss_index_path)
                self.logger.info(f"FAISS索引已保存到 {self.faiss_index_path}")
            
            # 数据库自动持久化，无需手动保存
            self.logger.info(f"数据库记录自动保存到 {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"保存索引失败: {e}")
            traceback.print_exc()

    def load_from_file(self, file_path: str = None):
        """
        从文件加载FAISS索引（数据库自动加载）
        
        参数:
            file_path: 加载路径，如果为None则使用默认路径
        """
        self.logger.info("加载FAISS索引和数据库...")
        
        try:
            # 加载FAISS索引
            if os.path.exists(self.faiss_index_path):
                self.index = faiss.read_index(self.faiss_index_path)
                self.logger.info(f"FAISS索引加载完成，包含 {self.index.ntotal} 个向量")
            else:
                self.logger.info("FAISS索引文件不存在，使用空索引")
                self._init_faiss_index()
            
            # 检查数据库记录数量
            with self.database.atomic():
                record_count = MemoryRecord.select().where(
                    MemoryRecord.character_name == self.character_name
                ).count()
                self.logger.info(f"数据库包含 {record_count} 条记录")
            
            # 验证数据一致性
            if self.index.ntotal != record_count:
                self.logger.warning(f"数据不一致: FAISS向量数量({self.index.ntotal}) != 数据库记录数量({record_count})")
                
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            traceback.print_exc()
            # 重新初始化
            self._init_faiss_index()
    
    def add_chat_turn(self, user_message: str, assistant_message: str, timestamp: str = None):
        """
        添加一轮对话到向量数据库
        
        参数:
            user_message: 用户消息
            assistant_message: 助手回复
            timestamp: 时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                timestamp = datetime.now()
        
        # 将用户消息和助手回复组合成一个对话单元（用于向量化）
        conversation_text = f"用户: {user_message}\n助手: {assistant_message}"
        
        record_id = self.add_text(
            text=conversation_text,
            user_message=user_message,
            assistant_message=assistant_message,
            record_type="conversation"
        )
        
        if record_id:
            self.logger.info(f"添加对话记录到数据库: ID={record_id}, 用户='{user_message[:50]}...'")
        else:
            self.logger.error("添加对话记录失败")
    
    def initialize_database(self):
        """
        初始化数据库（加载现有数据）
        """
        self.load_from_file()
        self.logger.info(f"Peewee记忆数据库初始化完成，角色: {self.character_name}")
    
    def get_relevant_memory(self, query: str, top_k: int = 5, timeout: int = 10, min_similarity: float = 0.3) -> str:
        """
        获取相关记忆并格式化为提示词
        
        参数:
            query: 查询文本
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            min_similarity: 最小相似度阈值
            
        返回:
            格式化的记忆提示词
        """
        try:
            results = self.search(query, top_k, timeout)
            
            if not results:
                return ""
            
            # 过滤低相似度结果
            filtered_results = [r for r in results if r.get('similarity', 0) >= min_similarity]
            
            if not filtered_results:
                return ""
                    
            # 格式化为提示词
            memory_prompt = "这是相关的记忆，可以作为参考：\n```\n" + \
                '\n'.join([r['text'] for r in filtered_results])
            
            memory_prompt += "```\n请参考以上历史记录，保持对话的连贯性和一致性。"
            
            self.logger.info(f"生成记忆提示词: {len(memory_prompt)} 字符")
            self.logger.debug(f"生成的记忆提示词内容: {memory_prompt}")
            return memory_prompt
            
        except Exception as e:
            self.logger.error(f"获取相关记忆失败: {e}")
            traceback.print_exc()
            return ""
    
    def get_stats(self) -> Dict:
        """
        获取数据库统计信息
        
        返回:
            统计信息字典
        """
        try:
            with self.database.atomic():
                total_records = MemoryRecord.select().where(
                    MemoryRecord.character_name == self.character_name
                ).count()
                
                conversation_records = MemoryRecord.select().where(
                    (MemoryRecord.character_name == self.character_name) &
                    (MemoryRecord.record_type == 'conversation')
                ).count()
                
                latest_record = MemoryRecord.select().where(
                    MemoryRecord.character_name == self.character_name
                ).order_by(MemoryRecord.timestamp.desc()).first()
                
                return {
                    "character_name": self.character_name,
                    "model": self.model,
                    "vector_dim": self.vector_dim,
                    "total_vectors": self.index.ntotal if self.index else 0,
                    "total_records": total_records,
                    "conversation_records": conversation_records,
                    "latest_record_time": latest_record.timestamp if latest_record else None,
                    "database_path": self.db_path,
                    "faiss_index_path": self.faiss_index_path
                }
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {
                "character_name": self.character_name,
                "error": str(e)
            }
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """
        获取最近的对话记录
        
        参数:
            limit: 返回记录数量限制
            
        返回:
            对话记录列表
        """
        try:
            with self.database.atomic():
                records = MemoryRecord.select().where(
                    (MemoryRecord.character_name == self.character_name) &
                    (MemoryRecord.record_type == 'conversation')
                ).order_by(MemoryRecord.timestamp.desc()).limit(limit)
                
                conversations = []
                for record in records:
                    conversations.append({
                        'id': record.id,
                        'user_message': record.user_message,
                        'assistant_message': record.assistant_message,
                        'timestamp': record.timestamp,
                        'similarity_score': record.similarity_score
                    })
                
                return conversations
        except Exception as e:
            self.logger.error(f"获取最近对话失败: {e}")
            return []
    
    def delete_old_records(self, days: int = 30) -> int:
        """
        删除指定天数之前的记录
        
        参数:
            days: 保留天数
            
        返回:
            删除的记录数量
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.database.atomic():
                # 获取要删除的记录的vector_index
                old_records = MemoryRecord.select().where(
                    (MemoryRecord.character_name == self.character_name) &
                    (MemoryRecord.timestamp < cutoff_date)
                )
                
                deleted_count = 0
                for record in old_records:
                    # 注意：这里需要重建FAISS索引来删除向量
                    # 简单起见，我们只删除数据库记录
                    record.delete_instance()
                    deleted_count += 1
                
                self.logger.info(f"删除了 {deleted_count} 条旧记录")
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"删除旧记录失败: {e}")
            return 0

# 使用示例
if __name__ == "__main__":
    # 初始化向量数据库（从环境变量自动读取配置）
    import sys
    sys.path.append(r'D:\Mypower\Git\MyPython\MyProject\CABM')
    sys.path.append(r'utils\RAG')
    from config import RAG_CONFIG
    
    vector_db = PeeweeChatHistoryVectorDB(RAG_CONFIG, character_name="test_character")
    
    print("初始化完成")

    # 添加对话
    vector_db.add_chat_turn('你好，我叫小明', '你好小明！很高兴认识你。')
    print("添加对话完成")
    
    # 搜索相似文本
    results = vector_db.search("我的名字", top_k=5)
    print("搜索结果:")
    for res in results:
        print(f"ID: {res['id']}, 文本: {res['text']}, 相似度: {res['similarity']:.3f}")
    
    # 获取统计信息
    stats = vector_db.get_stats()
    print("统计信息:", stats)

import json
import os
import signal
import logging
from datetime import datetime
from typing import List, Dict, Optional, Union
import numpy as np
from collections import defaultdict
from utils.env_utils import get_env_var

class TimeoutError(Exception):
    """超时异常"""
    pass

def timeout_handler(signum, frame):
    """超时处理函数"""
    raise TimeoutError("操作超时")

class ChatHistoryVectorDB:
    def __init__(self, api_key: str = None, model: str = None, character_name: str = "default"):
        """
        初始化向量数据库
        
        参数:
            api_key: Silicon Flow API的密钥，如果为None则从环境变量读取
            model: 使用的嵌入模型，如果为None则从环境变量读取
            character_name: 角色名称，用于确定数据库文件名
        """
        self.api_key = api_key or get_env_var('EMBEDDING_API_KEY')
        self.model = model or get_env_var('EMBEDDING_MODEL', 'BAAI/bge-m3')
        self.base_url = get_env_var('EMBEDDING_API_BASE_URL', 'https://api.siliconflow.cn/v1')
        self.character_name = character_name
        self.vectors = []  # 存储所有向量
        self.metadata = []  # 存储对应的元数据
        self.text_to_index = defaultdict(list)  # 文本到索引的映射
        self.loaded_texts = set()  # 记录已加载的文本，避免重复处理
        
        # 初始化 OpenAI 客户端
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError:
            print("未找到openai模块，请安装openai模块")
            self.client = None
        
        # 设置日志
        self.logger = logging.getLogger(f"MemoryDB_{character_name}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 确保数据目录存在
        self.memory_dir = "data/memory"
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 数据库文件路径
        self.db_file_path = os.path.join(self.memory_dir, f"{character_name}_memory.json")
        
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        调用API获取文本的嵌入向量（带缓存检查）
        """
        # 如果已有该文本的向量，直接返回
        if text in self.text_to_index:
            return self.vectors[self.text_to_index[text][0]]
            
        # 检查客户端是否可用
        if not self.client:
            print("OpenAI客户端未初始化")
            return None
            
        try:
            # 使用 OpenAI 库调用嵌入API
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"获取嵌入时发生异常: {e}")
            return None

    def add_text(self, text: str, metadata: Optional[Dict] = None):
        """
        添加单个文本到向量数据库
        
        参数:
            text: 要添加的文本
            metadata: 可选的元数据字典
        """
        if not text or len(text.strip()) < 1:
            return
            
        vector = self._get_embedding(text)
        if vector is None:
            return
            
        self.vectors.append(vector)
        if metadata is None:
            metadata = {'text': text}
        else:
            metadata['text'] = text
        self.metadata.append(metadata)
        self.text_to_index[text].append(len(self.vectors) - 1)
    
    def search(self, query: str, top_k: int = 5, timeout: int = 10) -> List[Dict]:
        """
        搜索与查询文本最相似的文本（带超时）
        
        参数:
            query: 查询文本
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            包含相似结果和元数据的字典列表
            
        异常:
            TimeoutError: 当操作超时时
        """
        if not self.vectors:
            return []
        
        # 设置超时处理（仅在非Windows系统上）
        if os.name != 'nt':  # 非Windows系统
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        try:
            query_vector = self._get_embedding(query)
            if query_vector is None:
                return []
                
            # 计算余弦相似度
            query_vector = np.array(query_vector)
            vectors = np.array(self.vectors)
            similarities = np.dot(vectors, query_vector) / (
                np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector)
            )
            
            # 获取最相似的top_k个结果
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                result = {
                    'text': self.metadata[idx]['text'],
                    'similarity': float(similarities[idx]),
                    'metadata': {k: v for k, v in self.metadata[idx].items() if k != 'text'}
                }
                results.append(result)
            
            # 记录检索结果到日志
            if results:
                self.logger.info(f"记忆检索查询: '{query}' -> 找到 {len(results)} 条相关记录")
                for i, result in enumerate(results, 1):
                    similarity = result['similarity']
                    text_preview = result['text'][:100] + "..." if len(result['text']) > 100 else result['text']
                    self.logger.info(f"  记录 {i}: 相似度={similarity:.3f}, 内容='{text_preview}'")
            else:
                self.logger.info(f"记忆检索查询: '{query}' -> 未找到相关记录")
                
            return results
            
        except TimeoutError:
            self.logger.warning(f"记忆检索超时 ({timeout}秒)")
            return []
        finally:
            # 取消超时设置（仅在非Windows系统上）
            if os.name != 'nt':
                signal.alarm(0)
    
    def save_to_file(self, file_path: str = None):
        """
        将向量数据库保存到文件
        
        参数:
            file_path: 保存路径，如果为None则使用默认路径
        """
        if file_path is None:
            file_path = self.db_file_path
            
        data = {
            'character_name': self.character_name,
            'model': self.model,
            'vectors': self.vectors,
            'metadata': self.metadata,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"向量数据库已保存到 {file_path}")

    def load_from_file(self, file_path: str = None):
        """
        从文件加载向量数据库
        
        参数:
            file_path: 加载路径，如果为None则使用默认路径
        """
        if file_path is None:
            file_path = self.db_file_path
            
        if not os.path.exists(file_path):
            self.logger.info(f"数据库文件不存在，将创建新的数据库: {file_path}")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.character_name = data.get('character_name', self.character_name)
            self.model = data.get('model', self.model)
            self.vectors = data.get('vectors', [])
            self.metadata = data.get('metadata', [])
            
            # 重建文本到索引的映射
            self.text_to_index = defaultdict(list)
            self.loaded_texts = set()
            for idx, meta in enumerate(self.metadata):
                text = meta.get('text', '')
                if text:
                    self.text_to_index[text].append(idx)
                    self.loaded_texts.add(text)
                    
            self.logger.info(f"成功加载向量数据库，共 {len(self.vectors)} 条记录")
            
        except Exception as e:
            self.logger.error(f"加载数据库失败: {e}")
            # 初始化为空数据库
            self.vectors = []
            self.metadata = []
            self.text_to_index = defaultdict(list)
            self.loaded_texts = set()

    def load_from_log(self, file_path: str, incremental: bool = True):
        """
        从日志文件加载数据并生成向量（构建知识库，支持增量加载）
        
        参数:
            file_path: 日志文件路径
            incremental: 是否增量加载（只处理新内容）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    content = entry.get('content', '')
                    if not content or len(content.strip()) < 1:
                        continue
                        
                    # 增量加载模式下，跳过已处理的文本
                    if incremental and content in self.loaded_texts:
                        continue
                        
                    # 获取嵌入向量（使用缓存机制）
                    vector = self._get_embedding(content)
                    if vector is None:
                        continue
                        
                    # 存储数据和元数据
                    self.vectors.append(vector)
                    metadata = {
                        'text': content,
                        'timestamp': entry.get('timestamp', ''),
                        'role': entry.get('role', '')
                    }
                    self.metadata.append(metadata)
                    self.text_to_index[content].append(len(self.vectors) - 1)
                    self.loaded_texts.add(content)
                    
                except json.JSONDecodeError:
                    print(f"跳过无法解析的行: {line}")
                    continue
    
    def add_chat_turn(self, user_message: str, assistant_message: str, timestamp: str = None):
        """
        添加一轮对话到向量数据库
        
        参数:
            user_message: 用户消息
            assistant_message: 助手回复
            timestamp: 时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # 将用户消息和助手回复组合成一个对话单元（用于向量化）
        conversation_text = f"用户: {user_message}\n助手: {assistant_message}"
        
        # 添加到向量数据库（不在metadata中重复存储text）
        metadata = {
            'user_message': user_message,
            'assistant_message': assistant_message,
            'timestamp': timestamp,
            'type': 'conversation'
        }
        
        self.add_text(conversation_text, metadata)
        self.logger.info(f"添加对话记录到向量数据库: {user_message[:50]}...")
    
    def initialize_database(self):
        """
        初始化数据库（加载现有数据）
        """
        self.load_from_file()
        self.logger.info(f"记忆数据库初始化完成，角色: {self.character_name}")
    
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
            
            # 过滤低相似度的结果
            filtered_results = [r for r in results if r['similarity'] >= min_similarity]
            
            if not filtered_results:
                self.logger.info(f"记忆过滤后无结果: 最小相似度阈值={min_similarity}, 原始结果数={len(results)}")
                return ""
            
            self.logger.info(f"记忆过滤结果: {len(filtered_results)}/{len(results)} 条记录通过相似度阈值 {min_similarity}")
            
            # 格式化为提示词
            memory_prompt = "这是相关的记忆，可以作为参考：\n```\n"
            
            for i, result in enumerate(filtered_results, 1):
                metadata = result['metadata']
                if metadata.get('type') == 'conversation':
                    user_msg = metadata.get('user_message', '')
                    assistant_msg = metadata.get('assistant_message', '')
                    timestamp = metadata.get('timestamp', '')
                    
                    memory_prompt += f"记录 {i}:\n"
                    memory_prompt += f"用户: {user_msg}\n"
                    memory_prompt += f"你: {assistant_msg}\n"
                    memory_prompt += f"时间: {timestamp}\n\n"
                    
                    # 记录详细的记忆内容到日志
                    self.logger.info(f"  -> 记录 {i}: 用户='{user_msg[:50]}...', 你='{assistant_msg[:50]}...', 相似度={result['similarity']:.3f}")
                else:
                    memory_prompt += f"记录 {i}: {result['text']}\n\n"
                    self.logger.info(f"  -> 记录 {i}: '{result['text'][:50]}...', 相似度={result['similarity']:.3f}")
            
            memory_prompt += "```\n请参考以上历史记录，保持对话的连贯性和一致性。"
            
            self.logger.info(f"生成记忆提示词: {len(memory_prompt)} 字符")
            
            return memory_prompt
            
        except Exception as e:
            self.logger.error(f"获取相关记忆失败: {e}")
            return ""


# 使用示例
if __name__ == "__main__":
    # 初始化向量数据库（从环境变量自动读取配置）
    vector_db = ChatHistoryVectorDB()
    print("初始化完成")

    vector_db.load_from_file("vector_db.json")
    print("加载完成")
    # 添加单个文本
    #vector_db.add_text("测试文本", {"role": "test", "timestamp": "2023-01-01"})
    
    # 搜索相似文本
    results = vector_db.search("", top_k=5)  # 使用默认值
    print("搜索结果:")
    for res in results:
        print(f"文本: {res['text']}, 相似度: {res['similarity']:.4f}")
        print(f"元数据: {res['metadata']}\n")
    
    # 保存向量数据库
    # vector_db.save_to_file("vector_db.json")
    
    # # 加载向量数据库
    # new_vector_db = ChatHistoryVectorDB()
    # new_vector_db.load_from_file("vector_db.json")
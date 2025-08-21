"""
基于FAISS的记忆存储工具
支持faiss-cpu和faiss-gpu，自动检测GPU并智能回退
"""
import json
import os
import signal
import logging
import pickle
from datetime import datetime
import traceback
from typing import List, Dict, Optional, Tuple
import numpy as np

# 尝试导入faiss-gpu，如果失败则回退到faiss-cpu
try:
    import faiss
    # 检测是否有GPU支持
    try:
        # 尝试创建GPU资源来测试GPU可用性
        if faiss.get_num_gpus() > 0:
            # 测试GPU是否真正可用
            test_res = faiss.StandardGpuResources()
            FAISS_GPU_AVAILABLE = True
            print(f"✓ 检测到 {faiss.get_num_gpus()} 个GPU，FAISS-GPU支持已启用")
        else:
            FAISS_GPU_AVAILABLE = False
            print("ℹ 未检测到可用GPU，使用CPU模式")
    except Exception as e:
        FAISS_GPU_AVAILABLE = False
        print(f"ℹ GPU初始化失败，回退到CPU模式: {e}")
except ImportError:
    print("警告: faiss 未安装，请运行: pip install faiss-cpu 或 pip install faiss-gpu")
    faiss = None
    FAISS_GPU_AVAILABLE = False

from .RAG import RAG
import sys
sys.path.append(r'utils\RAG')

class TimeoutError(Exception):
    """超时异常"""
    pass

def timeout_handler(signum, frame):
    """超时处理函数"""
    raise TimeoutError("操作超时")

class FaissChatHistoryVectorDB:
    def __init__(self, RAG_config: dict, model: str = None, character_name: str = "default", is_story: bool = False):
        """
        初始化基于FAISS的向量数据库
        
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
        self.logger = logging.getLogger(f"FaissMemoryDB_{character_name}")
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
        
        # 初始化RAG系统
        self.rag = RAG(RAG_config)
        
        # FAISS相关属性
        self.index = None
        self.gpu_index = None  # GPU索引
        self.gpu_resources = None  # GPU资源
        self.texts = []  # 存储原始文本
        self.metadata = []  # 存储元数据
        self.vector_dim = RAG_config['Multi_Recall']['Cosine_Similarity']['vector_dim']
        self.use_gpu = FAISS_GPU_AVAILABLE  # 是否使用GPU
        
        # 文件路径
        self.faiss_index_path = os.path.join(self.data_memory, f"{character_name}_faiss.index")
        self.texts_path = os.path.join(self.data_memory, f"{character_name}_texts.pkl")
        self.metadata_path = os.path.join(self.data_memory, f"{character_name}_metadata.json")
        
        # 初始化FAISS索引
        self._init_faiss_index()
    
    def _init_faiss_index(self):
        """初始化FAISS索引，支持GPU加速"""
        try:
            if self.use_gpu and FAISS_GPU_AVAILABLE:
                # 初始化GPU资源
                self.gpu_resources = faiss.StandardGpuResources()
                
                # 创建CPU索引
                cpu_index = faiss.IndexFlatL2(self.vector_dim)
                
                # 将索引移动到GPU
                self.index = faiss.index_cpu_to_gpu(self.gpu_resources, 0, cpu_index)
                self.logger.info(f"✓ 初始化FAISS-GPU索引，维度: {self.vector_dim}")
            else:
                # 使用CPU索引
                self.index = faiss.IndexFlatL2(self.vector_dim)
                self.logger.info(f"初始化FAISS-CPU索引，维度: {self.vector_dim}")
                
        except Exception as e:
            # GPU初始化失败，回退到CPU
            self.logger.warning(f"GPU索引初始化失败，回退到CPU模式: {e}")
            self.use_gpu = False
            self.index = faiss.IndexFlatL2(self.vector_dim)
            self.logger.info(f"初始化FAISS-CPU索引（回退），维度: {self.vector_dim}")
    
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
    
    def add_text(self, text: str, metadata: Dict = None):
        """
        添加单个文本到向量数据库
        
        参数:
            text: 要添加的文本
            metadata: 可选的元数据字典
        """
        if not text.strip():
            return
            
        # 获取嵌入向量
        embeddings = self._get_embeddings([text])
        
        if len(embeddings) > 0:
            # 添加到FAISS索引
            self.index.add(embeddings)
            
            # 存储文本和元数据
            self.texts.append(text)
            if metadata is None:
                metadata = {"timestamp": datetime.now().isoformat()}
            self.metadata.append(metadata)
            
            self.logger.info(f"添加文本到FAISS索引: {text[:50]}...")
    
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
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.texts):
                    result = {
                        'text': self.texts[idx],
                        'distance': float(distance),
                        'similarity': 1.0 / (1.0 + distance),  # 转换为相似度
                        'metadata': self.metadata[idx] if idx < len(self.metadata) else {}
                    }
                    results.append(result)
            
            # 记录检索结果到日志
            if results:
                self.logger.info(f"FAISS检索查询: '{query}' -> 找到 {len(results)} 条相关记录")
                for i, result in enumerate(results, 1):
                    text_preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
                    self.logger.info(f"  记录 {i}: '{text_preview}' (相似度: {result['similarity']:.3f})")
            else:
                self.logger.info(f"FAISS检索查询: '{query}' -> 未找到相关记录")
                
            return results
            
        except TimeoutError:
            self.logger.warning(f"FAISS检索超时 ({timeout}秒)")
            return []
        except Exception as e:
            self.logger.error(f"FAISS检索失败: {e}")
            traceback.print_exc()
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
        try:
            if file_path is None:
                file_path = self.data_memory
            
            # 保存FAISS索引
            if self.index.ntotal > 0:
                # 如果是GPU索引，需要先转换为CPU索引再保存
                if self.use_gpu and hasattr(self.index, 'index'):
                    # GPU索引，转换为CPU索引保存
                    cpu_index = faiss.index_gpu_to_cpu(self.index)
                    faiss.write_index(cpu_index, self.faiss_index_path)
                    self.logger.info(f"FAISS-GPU索引已转换为CPU格式并保存到 {self.faiss_index_path}")
                else:
                    # CPU索引，直接保存
                    faiss.write_index(self.index, self.faiss_index_path)
                    self.logger.info(f"FAISS索引已保存到 {self.faiss_index_path}")
            
            # 保存文本数据
            with open(self.texts_path, 'wb') as f:
                pickle.dump(self.texts, f)
            
            # 保存元数据
            metadata_info = {
                'character_name': self.character_name,
                'model': self.model,
                'vector_dim': self.vector_dim,
                'total_texts': len(self.texts),
                'metadata': self.metadata,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_info, f, ensure_ascii=False, indent=4)
            
            self.logger.info(f"向量数据库已保存到 {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存数据库失败: {e}")
            traceback.print_exc()

    def load_from_file(self, file_path: str = None):
        """
        从文件加载向量数据库
        
        参数:
            file_path: 加载路径，如果为None则使用默认路径
        """
        self.logger.info("加载FAISS向量数据库...")
        
        try:
            # 加载FAISS索引
            if os.path.exists(self.faiss_index_path):
                # 先加载到CPU
                cpu_index = faiss.read_index(self.faiss_index_path)
                
                # 如果启用GPU且可用，将索引移动到GPU
                if self.use_gpu and FAISS_GPU_AVAILABLE:
                    try:
                        if self.gpu_resources is None:
                            self.gpu_resources = faiss.StandardGpuResources()
                        self.index = faiss.index_cpu_to_gpu(self.gpu_resources, 0, cpu_index)
                        self.logger.info(f"✓ FAISS-GPU索引加载完成，包含 {self.index.ntotal} 个向量")
                    except Exception as e:
                        self.logger.warning(f"GPU索引加载失败，使用CPU模式: {e}")
                        self.use_gpu = False
                        self.index = cpu_index
                        self.logger.info(f"FAISS-CPU索引加载完成（回退），包含 {self.index.ntotal} 个向量")
                else:
                    self.index = cpu_index
                    self.logger.info(f"FAISS-CPU索引加载完成，包含 {self.index.ntotal} 个向量")
            else:
                self.logger.info("FAISS索引文件不存在，使用空索引")
                self._init_faiss_index()
            
            # 加载文本数据
            if os.path.exists(self.texts_path):
                with open(self.texts_path, 'rb') as f:
                    self.texts = pickle.load(f)
                self.logger.info(f"加载了 {len(self.texts)} 条文本记录")
            else:
                self.texts = []
                self.logger.info("文本文件不存在，使用空列表")
            
            # 加载元数据
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    metadata_info = json.load(f)
                    
                self.character_name = metadata_info.get('character_name', self.character_name)
                self.model = metadata_info.get('model', self.model)
                self.metadata = metadata_info.get('metadata', [])
                
                self.logger.info(f"元数据加载完成，角色: {self.character_name}")
            else:
                self.metadata = []
                self.logger.info("元数据文件不存在，使用空列表")
            
            # 验证数据一致性
            if len(self.texts) != len(self.metadata):
                self.logger.warning(f"数据不一致: 文本数量({len(self.texts)}) != 元数据数量({len(self.metadata)})")
                # 调整元数据长度
                while len(self.metadata) < len(self.texts):
                    self.metadata.append({"timestamp": datetime.now().isoformat()})
                self.metadata = self.metadata[:len(self.texts)]
            
            if self.index.ntotal != len(self.texts):
                self.logger.warning(f"数据不一致: FAISS向量数量({self.index.ntotal}) != 文本数量({len(self.texts)})")
                
        except Exception as e:
            self.logger.error(f"加载数据库失败: {e}")
            traceback.print_exc()
            # 重新初始化
            self._init_faiss_index()
            self.texts = []
            self.metadata = []
    
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
        
        metadata = {
            "timestamp": timestamp,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "type": "conversation"
        }
        
        self.add_text(conversation_text, metadata)
        self.logger.info(f"添加对话记录到FAISS数据库: {user_message[:50]}...")
    
    def initialize_database(self):
        """
        初始化数据库（加载现有数据）
        """
        self.load_from_file()
        self.logger.info(f"FAISS记忆数据库初始化完成，角色: {self.character_name}")
    
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
    
    def get_gpu_info(self) -> Dict:
        """
        获取GPU信息
        
        返回:
            GPU信息字典
        """
        gpu_info = {
            "gpu_available": FAISS_GPU_AVAILABLE,
            "using_gpu": self.use_gpu,
            "num_gpus": 0,
            "gpu_memory_info": []
        }
        
        if FAISS_GPU_AVAILABLE:
            try:
                gpu_info["num_gpus"] = faiss.get_num_gpus()
                
                # 获取GPU内存信息
                for i in range(gpu_info["num_gpus"]):
                    try:
                        # 创建临时GPU资源来获取内存信息
                        temp_res = faiss.StandardGpuResources()
                        gpu_info["gpu_memory_info"].append({
                            "gpu_id": i,
                            "status": "可用"
                        })
                    except Exception as e:
                        gpu_info["gpu_memory_info"].append({
                            "gpu_id": i,
                            "status": f"不可用: {e}"
                        })
                        
            except Exception as e:
                gpu_info["error"] = str(e)
        
        return gpu_info
    
    def get_stats(self) -> Dict:
        """
        获取数据库统计信息
        
        返回:
            统计信息字典
        """
        stats = {
            "character_name": self.character_name,
            "model": self.model,
            "vector_dim": self.vector_dim,
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_texts": len(self.texts),
            "total_metadata": len(self.metadata),
            "faiss_index_path": self.faiss_index_path,
            "texts_path": self.texts_path,
            "metadata_path": self.metadata_path,
            "gpu_info": self.get_gpu_info()
        }
        
        return stats

# 使用示例
if __name__ == "__main__":
    # 初始化向量数据库（从环境变量自动读取配置）
    import sys
    sys.path.append(r'D:\Mypower\Git\MyPython\MyProject\CABM')
    sys.path.append(r'utils\RAG')
    from config import RAG_CONFIG
    
    vector_db = FaissChatHistoryVectorDB(RAG_CONFIG)
    
    print("初始化完成")

    vector_db.add_text('测试文本1')
    print("加载完成")
    
    # 搜索相似文本
    results = vector_db.search("测试", top_k=5)
    print("搜索结果:")
    for res in results:
        print(f"文本: {res['text']}, 相似度: {res['similarity']:.3f}")

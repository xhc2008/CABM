import json
import os
import signal
import logging
from datetime import datetime
import traceback
from .RAG import RAG
import sys
sys.path.append(r'utils\RAG')
class TimeoutError(Exception):
    """超时异常"""
    pass

def timeout_handler(signum, frame):
    """超时处理函数"""
    raise TimeoutError("操作超时")

class ChatHistoryVectorDB:
    def __init__(self, RAG_config: dict, model: str = None, character_name: str = "default", is_story: bool = False):
        """
        初始化向量数据库
        
        参数:
            RAG_config: RAG配置字典
            model: 使用的嵌入模型，如果为None则从环境变量读取
            character_name: 角色名称或故事ID，用于确定数据库文件名
            is_story: 是否为故事模式
        """
        self.config = RAG_config
        self.character_name = character_name
        self.model = model
        self.is_story = is_story
        
        # 设置日志
        self.logger = logging.getLogger(f"MemoryDB_{character_name}")
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
        
        # 确保目录存在
        os.makedirs(self.data_memory, exist_ok=True)    
        
        self.rag = RAG(RAG_config)
        
    def add_text(self, text: str):
        """
        添加单个文本到向量数据库
        
        参数:
            text: 要添加的文本
            metadata: 可选的元数据字典
        """
        self.rag.add(text)
    
    def search(self, query: str, top_k: int = 5, timeout: int = 10):
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
        
        # 设置超时处理（仅在非Windows系统上）
        if os.name != 'nt':  # 非Windows系统
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        
        try:
            # 获取最相似的top_k个结果
            top_indices = self.rag.req(query=query, top_k=top_k)
            
            results = []
            for text in top_indices:
                result = {  #TODO 去除了<相似度>键, 多路召回后不是都有相似度
                    'text': text
                }
                results.append(result)
            
            # 记录检索结果到日志
            if results:
                self.logger.info(f"记忆检索查询: '{query}' -> 找到 {len(results)} 条相关记录")
                for i, result in enumerate(results, 1):
                    text_preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
                    self.logger.info(f"  记录 {i}: '{text_preview}'")
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
            file_path = self.data_memory
        rag_save = self.rag.save_to_file(file_path)
        data = {
            'character_name': self.character_name,
            'model': self.model,
            'rag': rag_save,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(os.path.join(file_path, f"{self.character_name}_memory.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        self.logger.info(f"向量数据库已保存到 {file_path}")

    def load_from_file(self, file_path: str = None):
        """
        从文件加载向量数据库
        
        参数:
            file_path: 加载路径，如果为None则使用默认路径
        """
        self.logger.info("加载向量数据库...")
        if file_path is None:
            file_path = os.path.join(self.data_memory, f"{self.character_name}_memory.json")
        
        if not os.path.exists(file_path):
            self.logger.info(f"数据库文件不存在，将创建新的数据库: {file_path}")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.character_name = data.get('character_name', self.character_name)
            self.model = data.get('model', self.model)
            self.logger.info(f"加载RAG缓存")
            self.rag.load_from_file(data.get('rag', None))
            self.logger.info(f"向量数据库加载完成，角色: {self.character_name}")
        except Exception as e:
            self.logger.error(f"加载数据库失败: {e}")

    #TODO 未使用的函数
    # def load_from_log(self, file_path: str, incremental: bool = True):
    #     """
    #     从日志文件加载数据并生成向量（构建知识库，支持增量加载）
        
    #     参数:
    #         file_path: 日志文件路径
    #         incremental: 是否增量加载（只处理新内容）
    #     """
    #     if not os.path.exists(file_path):
    #         raise FileNotFoundError(f"文件 {file_path} 不存在")
            
    #     with open(file_path, 'r', encoding='utf-8') as f:
    #         for line in f:
    #             try:
    #                 entry = json.loads(line.strip())
    #                 content = entry.get('content', '')
    #                 if not content or len(content.strip()) < 1:
    #                     continue
                        
    #                 # 增量加载模式下，跳过已处理的文本
    #                 if incremental and content in self.loaded_texts:
    #                     continue
                        
    #                 # 获取嵌入向量（使用缓存机制）
    #                 vector = self._get_embedding(content)
    #                 if vector is None:
    #                     continue
                        
    #                 # 存储数据和元数据
    #                 self.vectors.append(vector)
    #                 metadata = {
    #                     'text': content,
    #                     'timestamp': entry.get('timestamp', ''),
    #                     'role': entry.get('role', '')
    #                 }
    #                 self.metadata.append(metadata)
    #                 self.text_to_index[content].append(len(self.vectors) - 1)
    #                 self.loaded_texts.add(content)
                    
    #             except json.JSONDecodeError:
    #                 print(f"跳过无法解析的行: {line}")
    #                 continue
    
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
    
        self.add_text(conversation_text)
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
                    
            # 格式化为提示词
            memory_prompt = "这是相关的记忆，可以作为参考：\n```\n" + \
                '\n'.join([r['text'] for r in results])
            
            memory_prompt += "```\n请参考以上历史记录，保持对话的连贯性和一致性。"
            
            self.logger.info(f"生成记忆提示词: {len(memory_prompt)} 字符")
            self.logger.debug(f"生成的记忆提示词内容: {memory_prompt}")
            return memory_prompt
            
        except Exception as e:
            self.logger.error(f"获取相关记忆失败: {e}")
            traceback.print_exc()
            return ""


# 使用示例
if __name__ == "__main__":
    # 初始化向量数据库（从环境变量自动读取配置）
    import sys
    sys.path.append(r'D:\Mypower\Git\MyPython\MyProject\CABM')
    sys.path.append(r'utils\RAG')
    from config import RAG_CONFIG
    vector_db = ChatHistoryVectorDB(RAG_CONFIG)
    
    print("初始化完成")

    vector_db.add_text('测试文本1')
    print("加载完成")
    
    # 搜索相似文本
    results = vector_db.search("静流的外号", top_k=5)  # 使用默认值
    print("搜索结果:")
    for res in results:
        print(f"文本: {res['text']}")
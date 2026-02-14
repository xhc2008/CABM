import json
import os
import logging
from datetime import datetime
import traceback
import threading
import concurrent.futures
from .RAG import RAG
import sys
sys.path.append(r'utils\RAG')

class TimeoutError(Exception):
    """超时异常"""
    pass

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
    
    def _perform_search(self, query: str, top_k: int = 5):
        """执行实际的搜索操作"""
        # 获取最相似的top_k个结果
        top_indices = self.rag.req(query=query, top_k=top_k)
        
        results = []
        for text in top_indices:
            result = {
                'text': text
            }
            results.append(result)
        
        return results
    
    def search(self, query: str, top_k: int = 5, timeout: int = 10):
        """
        搜索与查询文本最相似的文本（带超时，线程安全）
        
        参数:
            query: 查询文本
            top_k: 返回的最相似结果数量
            timeout: 超时时间（秒）
            
        返回:
            包含相似结果和元数据的字典列表
            
        异常:
            TimeoutError: 当操作超时时
        """
        results = []
        
        try:
            # 使用 ThreadPoolExecutor 实现超时控制（线程安全）
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                # 提交搜索任务
                future = executor.submit(self._perform_search, query, top_k)
                
                try:
                    # 等待结果，带超时
                    results = future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    # 超时处理
                    self.logger.warning(f"记忆检索超时 ({timeout}秒)")
                    future.cancel()  # 取消任务
                    return []
                except Exception as e:
                    # 其他异常
                    self.logger.error(f"记忆检索出错: {e}")
                    return []
            
            # 记录检索结果到日志
            if results:
                self.logger.info(f"记忆检索查询: '{query}' -> 找到 {len(results)} 条相关记录")
                for i, result in enumerate(results, 1):
                    text_preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
                    self.logger.info(f"  记录 {i}: '{text_preview}'")
            else:
                self.logger.info(f"记忆检索查询: '{query}' -> 未找到相关记录")
                
            return results
            
        except Exception as e:
            self.logger.error(f"搜索过程发生错误: {e}")
            traceback.print_exc()
            return []
    
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
            traceback.print_exc()
    
    def add_chat_turn(self, user_message: str, assistant_message: str, timestamp: str = None):
        """
        添加一轮对话到向量数据库（新格式：每条记录一个角色的话）
        
        参数:
            user_message: 用户消息
            assistant_message: 助手回复
            timestamp: 时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # 新格式：分别添加用户和角色的消息
        user_text = f"玩家：{user_message}"
        
        # 处理助手消息：如果是JSON格式，只取content部分
        try:
            import json
            assistant_data = json.loads(assistant_message)
            assistant_content = assistant_data.get('content', assistant_message)
        except (json.JSONDecodeError, TypeError):
            assistant_content = assistant_message
        
        # 获取角色名
        if self.is_story:
            # 故事模式：使用故事中的主要角色名
            try:
                from services.config_service import config_service
                from services.story_service import story_service
                story_data = story_service.get_current_story_data()
                if story_data:
                    characters = story_data.get('characters', {}).get('list', [])
                    if isinstance(characters, str):
                        characters = [characters]
                    if characters:
                        char_config = config_service.get_character_config(characters[0])
                        character_name = char_config.get('name', characters[0]) if char_config else characters[0]
                    else:
                        character_name = self.character_name
                else:
                    character_name = self.character_name
            except:
                character_name = self.character_name
        else:
            # 普通模式：使用角色配置中的名称
            try:
                from services.config_service import config_service
                char_config = config_service.get_character_config(self.character_name)
                character_name = char_config.get('name', self.character_name) if char_config else self.character_name
            except:
                character_name = self.character_name
        
        assistant_text = f"{character_name}：{assistant_content}"
        
        # 分别添加两条记录
        self.add_text(user_text)
        self.add_text(assistant_text)
        
        self.logger.info(f"添加对话记录到向量数据库: 玩家={user_message[:30]}..., {character_name}={assistant_content[:30]}...")
    
    def add_single_message(self, speaker_name: str, message: str, timestamp: str = None):
        """
        添加单条消息到向量数据库（用于多角色对话）
        
        参数:
            speaker_name: 说话者名称
            message: 消息内容
            timestamp: 时间戳，如果为None则使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # 处理消息内容：如果是JSON格式，只取content部分
        try:
            import json
            message_data = json.loads(message)
            content = message_data.get('content', message)
        except (json.JSONDecodeError, TypeError):
            content = message
        
        # 格式化为记忆文本
        memory_text = f"{speaker_name}：{content}"
        
        # 添加到向量数据库
        self.add_text(memory_text)
        
        self.logger.info(f"添加单条消息到向量数据库: {speaker_name}={content[:30]}...")
    
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
            memory_prompt = "这是唤醒的记忆，可以作为参考：\n```\n" + \
                '\n'.join([r['text'] for r in results])
            
            memory_prompt += "\n```\n以上是记忆而不是最近的对话，可以不使用。"
            
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
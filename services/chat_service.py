"""
对话服务模块
封装对话API调用和处理
"""
import sys
import json
import time
import re
import os
from typing import List, Dict, Any, Optional, Iterator, Union, Tuple
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.api_utils import make_api_request, APIError, handle_api_error, parse_stream_data
from utils.history_utils import HistoryManager
from utils.prompt_logger import prompt_logger
from services.config_service import config_service
from config import get_memory_config
from utils.time_utils import TimeTracker
# 注意：为了避免循环导入，scene_service和memory_service将在ChatService类中导入

class Message:
    """消息类"""
    def __init__(self, role: str, content: str):
        """
        初始化消息
        
        Args:
            role: 消息角色（"system", "user", "assistant"）
            content: 消息内容
        """
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {
            "role": self.role,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Message':
        """从字典创建消息"""
        return cls(data["role"], data["content"])




import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class ChatService:
    """对话服务类"""
    
    def __init__(self):
        """初始化对话服务"""
        self.history: List[Message] = []
        self.config_service = config_service
        self.logger = logging.getLogger(__name__)
        
        # 剧情模式相关
        self.story_mode = False
        self.current_story_id = None
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 创建历史记录管理器
        app_config = self.config_service.get_app_config()
        history_dir = app_config["history_dir"]
        self.history_manager = HistoryManager(history_dir)
        
        # 初始化时间跟踪器
        self.time_tracker = TimeTracker(history_dir)
        
        # 导入记忆服务（避免循环导入）
        from services.memory_service import memory_service
        self.memory_service = memory_service
        
        # 初始化时加载历史记录
        self._load_history_on_startup()
        
        # 初始化当前角色的记忆数据库
        self._initialize_character_memory()
        
        # 初始化OpenAI客户端
        self.openai_answer = True
        try:
            # 获取环境变量
            api_key = os.getenv("CHAT_API_KEY")
            base_url = os.getenv("CHAT_API_BASE_URL")
            model = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
            
            # 验证必要的环境变量
            if not api_key:
                self.logger.error("缺少CHAT_API_KEY环境变量")
                raise ValueError("Missing CHAT_API_KEY environment variable")
                
            if not base_url:
                self.logger.warning("未设置CHAT_API_BASE_URL，将使用默认API地址")
                base_url = "https://api.openai.com/v1"
            
            # 初始化客户端（带重试和超时配置）
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=60.0,  # 60秒超时
                max_retries=3  # 最多重试3次
            )
            self.chat_model = model
            
        except ImportError:
            self.openai_answer = False
            self.logger.error("未找到openai模块，请安装openai模块")
        except Exception as e:
            self.openai_answer = False
            self.logger.error(f"OpenAI客户端初始化失败: {e}")
    
    def add_message(self, role: str, content: str) -> Message:
        """
        添加消息到历史记录
        
        Args:
            role: 消息角色
            content: 消息内容
            
        Returns:
            添加的消息对象
        """
        message = Message(role, content)
        self.history.append(message)
        
        # 限制历史记录长度
        max_history = self.config_service.get_app_config()["max_history_length"]
        if len(self.history) > max_history:
            # 保留system消息
            system_messages = [msg for msg in self.history if msg.role == "system"]
            other_messages = [msg for msg in self.history if msg.role != "system"]
            
            # 保留最新的消息
            other_messages = other_messages[-(max_history - len(system_messages)):]
            
            # 重建历史记录
            self.history = system_messages + other_messages
        
        # 如果不是系统消息，保存到持久化历史记录
        if role != "system":
            if self.story_mode and self.current_story_id:
                # 剧情模式：保存到故事目录
                from services.story_service import story_service
                history_path = story_service.get_story_history_path()
                self.history_manager.save_message_to_file(history_path, role, content)
            else:
                # 普通模式：保存到角色目录
                character_id = self.config_service.current_character_id or "default"
                self.history_manager.save_message(character_id, role, content)
        
        return message
    
    def clear_history(self, keep_system: bool = True, clear_persistent: bool = False, confirm: bool = False) -> None:
        """
        清空对话历史
        
        Args:
            keep_system: 是否保留system消息
            clear_persistent: 是否清空持久化历史记录
            confirm: 是否已确认清空操作（对于危险操作的安全确认）
        
        Raises:
            ValueError: 当尝试清空持久化历史但未确认时
        """
        if clear_persistent and not confirm:
            raise ValueError("清空持久化历史记录需要确认操作")
        
        character_id = self.config_service.current_character_id or "default"
        self.logger.info(f"正在清空历史记录 - 角色: {character_id}, 保留系统消息: {keep_system}, 清空持久化: {clear_persistent}")
        
        if keep_system:
            self.history = [msg for msg in self.history if msg.role == "system"]
        else:
            self.history = []
            
        # 如果需要清空持久化历史记录
        if clear_persistent:
            self.logger.warning(f"正在清空持久化历史记录 - 角色: {character_id}")
            self.history_manager.clear_history(character_id)
            self.logger.info("持久化历史记录已清空")
    
    def get_history(self) -> List[Message]:
        """获取对话历史"""
        return self.history.copy()
    
    def format_messages(self) -> List[Dict[str, str]]:
        """格式化消息以适应API要求"""
        return [msg.to_dict() for msg in self.history]
    
    def set_system_prompt(self, prompt_type: str = "default") -> None:
        """
        设置系统提示词（统一由config_service处理拼接）
        
        Args:
            prompt_type: 提示词类型，如果为"character"则使用当前角色的提示词
        """
        # 移除现有的system消息
        self.history = [msg for msg in self.history if msg.role != "system"]
        
        # 统一由config_service拼接系统提示词
        system_prompt = self.config_service.get_system_prompt(prompt_type)
        self.add_message("system", system_prompt)
        self.logger.info(f"系统提示词已设置: {system_prompt[:50]}...")
    
    def _build_system_prompt_with_context(self, user_query: str = None) -> str:
        """
        构建包含时间前缀、相关记忆和角色详情的系统提示词
        
        Args:
            user_query: 用户查询，用于检索相关记忆和角色详情
            
        Returns:
            完整的系统提示词
        """
        # 获取基础系统提示词
        if self.story_mode and self.current_story_id:
            base_prompt = self.config_service.get_system_prompt("character")
            
            # 剧情模式：添加剧情引导内容
            try:
                from services.story_service import story_service
                
                # 获取故事进度信息
                offset = story_service.get_offset()
                current_idx, current_chapter, next_chapter = story_service.get_current_chapter_info()
                
                # 根据偏移值添加引导内容
                guidance = f"当前章节：`{current_chapter}`"
                if next_chapter:  # 只有在还有下一章节时才添加引导
                    if offset<10:
                        guidance += f"。下一章节：`{next_chapter}`。请保持在当前章节，不要进入下一章节"
                    if 10 <= offset < 30:
                        guidance += f"。请暗示性地引导用户向`{next_chapter}`方向推进故事"
                    elif offset >= 30:
                        guidance += f"。请制造突发事件以引导用户向`{next_chapter}`方向推进故事"
                
                # 构建剧情模式提示词
                story_prompt = f"你是一个视听小说中的角色，你需要为用户制造沉浸式的剧情体验。{guidance}{base_prompt}"
                base_prompt = story_prompt
                
                self.logger.info(f"剧情模式提示词已构建，偏移值: {offset}, 当前章节: {current_chapter}")
                
            except Exception as e:
                self.logger.error(f"构建剧情模式提示词失败: {e}")
                # 出错时回退到基础提示词
                
        else:
            # 普通模式
            base_prompt = "你是一个视听小说中的角色，你正在和用户闲聊。"+self.config_service.get_system_prompt("character")
        
        # 初始化上下文部分
        context_parts = []
        
        # 添加时间前缀（仅在非故事模式下）
        if not self.story_mode:
            character_id = self.config_service.current_character_id or "default"
            time_prefix = self.time_tracker.get_time_elapsed_prefix(character_id)
            if time_prefix:
                context_parts.append(time_prefix)
        
        # 添加记忆和角色详情上下文
        memory_context = ""
        details_context = ""
        
        if user_query:
            try:
                if self.story_mode and self.current_story_id:
                    # 剧情模式：使用故事ID进行记忆检索
                    memory_context = self.memory_service.search_story_memory(
                        query=user_query,
                        story_id=self.current_story_id
                    )
                    # 剧情模式：尝试获取角色详细信息
                    character_id = self.config_service.current_character_id
                    if character_id:
                        from services.character_details_service import character_details_service
                        details_context = character_details_service.search_character_details(
                            character_id=character_id,
                            query=user_query,
                            top_k=3
                        )
                else:
                    # 普通模式：同时进行记忆和角色详细信息检索
                    character_id = self.config_service.current_character_id or "default"
                    memory_context, details_context = self.memory_service.search_memory_and_details(
                        query=user_query,
                        character_name=character_id
                    )
                
                # 构建完整的上下文
                if memory_context:
                    context_parts.append(memory_context)
                if details_context:
                    context_parts.append(details_context)
                    
            except Exception as e:
                self.logger.error(f"记忆和详细信息检索失败: {e}")
        
        # 如果有上下文信息，添加到系统提示词
        if context_parts:
            context_str = "\n\n".join(context_parts)
            full_prompt = f"{base_prompt}\n\n{context_str}"
        else:
            full_prompt = base_prompt
            
        return full_prompt
    
    def _load_history_on_startup(self):
        """在启动时加载历史记录到内存"""
        if self.story_mode and self.current_story_id:
            # 剧情模式：从故事目录加载
            from services.story_service import story_service
            history_path = story_service.get_story_history_path()
            
            app_config = self.config_service.get_app_config()
            max_history = app_config["max_history_length"]
            
            history_messages = self.history_manager.load_history_from_file(history_path, max_history, max_history * 2)
        else:
            # 普通模式：从角色目录加载
            character_id = self.config_service.current_character_id or "default"
            
            app_config = self.config_service.get_app_config()
            max_history = app_config["max_history_length"]
            
            history_messages = self.history_manager.load_history(character_id, max_history, max_history * 2)
        
        # 转换为Message对象并添加到内存中
        for msg in history_messages:
            if msg["role"] != "system":  # 系统消息会通过set_system_prompt单独设置
                self.history.append(Message.from_dict(msg))
    
    def _initialize_character_memory(self):
        """初始化当前角色的记忆数据库"""
        if self.story_mode and self.current_story_id:
            # 剧情模式：使用故事ID作为记忆标识
            self.memory_service.initialize_story_memory(self.current_story_id)
        else:
            # 普通模式：使用角色ID
            character_id = self.config_service.current_character_id or "default"
            self.memory_service.initialize_character_memory(character_id)
    
    def set_character(self, character_id: str) -> bool:
        """
        设置角色
        
        Args:
            character_id: 角色ID
            
        Returns:
            是否设置成功
        """
        # 设置角色
        if self.config_service.set_character(character_id):
            # 清空当前会话历史
            self.history = []
            
            # 设置系统提示词
            self.set_system_prompt("character")
            
            # 初始化该角色的记忆数据库
            self.memory_service.set_current_character(character_id)
            
            # 加载该角色的历史记录
            app_config = self.config_service.get_app_config()
            max_history = app_config["max_history_length"]
            history_messages = self.history_manager.load_history(character_id, max_history, max_history * 2)
            
            # 转换为Message对象并添加到内存中
            for msg in history_messages:
                if msg["role"] != "system":  # 系统消息已通过set_system_prompt设置
                    self.history.append(Message.from_dict(msg))
                    
            return True
        
        return False
    
    def set_story_mode(self, story_id: str) -> bool:
        """
        设置剧情模式
        
        Args:
            story_id: 故事ID
            
        Returns:
            是否设置成功
        """
        try:
            from services.story_service import story_service
            
            # 加载故事
            if not story_service.load_story(story_id):
                return False
            
            # 获取故事数据
            story_data = story_service.get_current_story_data()
            if not story_data:
                return False
            
            # 获取故事中的角色
            characters = story_data.get('characters', {}).get('list', [])
            if not characters:
                return False
            
            # 设置第一个角色为当前角色
            character_id = characters[0]
            if not self.config_service.set_character(character_id):
                return False
            
            # 启用剧情模式
            self.story_mode = True
            self.current_story_id = story_id
            
            # 清空当前会话历史
            self.history = []
            
            # 设置剧情模式的系统提示词
            self.set_story_system_prompt()
            
            # 初始化故事记忆数据库
            self.memory_service.initialize_story_memory(story_id)
            
            # 加载故事的历史记录
            history_path = story_service.get_story_history_path()
            app_config = self.config_service.get_app_config()
            max_history = app_config["max_history_length"]
            
            history_messages = self.history_manager.load_history_from_file(history_path, max_history, max_history * 2)
            
            # 转换为Message对象并添加到内存中
            for msg in history_messages:
                if msg["role"] != "system":
                    self.history.append(Message.from_dict(msg))
            
            self.logger.info(f"成功设置剧情模式: {story_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置剧情模式失败: {e}")
            return False
    
    def set_story_system_prompt(self):
        """设置剧情模式的系统提示词（现在只是触发更新）"""
        # 移除现有的system消息
        self.history = [msg for msg in self.history if msg.role != "system"]
        
        # 添加空的系统消息占位符，实际内容会在_build_system_prompt_with_context中构建
        self.add_message("system", "")
        self.logger.info("剧情模式系统提示词已触发更新")
    
    def exit_story_mode(self):
        """退出剧情模式"""
        self.story_mode = False
        self.current_story_id = None
        
        # 清除当前故事记忆上下文指针（不在此处加载/切换历史，由进入 /chat 时统一处理）
        try:
            self.memory_service.current_story = None
            self.logger.info("已退出剧情模式，已清除故事记忆上下文指针")
        except Exception as e:
            self.logger.error(f"清除故事记忆上下文指针失败: {e}")
        
        self.logger.info("已退出剧情模式")
    
    def get_character_config(self):
        """
        获取当前角色配置
        
        Returns:
            角色配置字典
        """
        return self.config_service.get_character_config()
        
    def load_persistent_history(self, count: Optional[int] = None) -> List[Message]:
        """
        加载持久化历史记录
        
        Args:
            count: 加载的消息数量，如果为None则使用配置中的值
        Returns:
            历史记录列表（Message对象）
        """
        character_id = self.config_service.current_character_id or "default"
        if count is None:
            count = self.config_service.get_app_config()["max_history_length"]
        raw_msgs = self.history_manager.load_history(character_id, count)
        return [Message.from_dict(msg) for msg in raw_msgs]
    
    def chat_completion(
        self, 
        messages: Optional[List[Dict[str, str]]] = None, 
        stream: bool = True,
        user_query: str = None,
        on_token=None
    ) -> Iterator[str]:
        """
        调用对话API（集成记忆检索，仅流式返回）
        
        Args:
            messages: 消息列表，如果为None则使用历史记录
            stream: 是否使用流式输出
            user_query: 用户查询，用于记忆检索和日志记录
            on_token: 可选，流式生成时每个token的回调
        Returns:
            迭代器，每次yield一个字符串token
        Raises:
            APIError: 当API调用失败时
        """
        # 获取API配置
        url = self.config_service.get_chat_api_url()
        api_key = self.config_service.get_chat_api_key()
        chat_config = self.config_service.get_chat_config()
        stream_config = self.config_service.get_stream_config()
        
        # 检查是否启用流式输出
        if stream and not stream_config.get("enable_streaming", True):
            stream = False
        
        # 准备请求数据
        if messages is None:
            # 使用内存中的历史记录（已经包含了从持久化存储加载的记录）
            messages = self.format_messages()
        
        # 如果有用户查询，构建包含上下文的系统提示词
        if user_query:
            # 构建包含记忆、角色详情、时间前缀和剧情引导的系统提示词
            full_system_prompt = self._build_system_prompt_with_context(user_query)
            
            # 移除现有的system消息
            messages = [msg for msg in messages if msg.get("role") != "system"]
            
            # 添加新的系统提示词到消息列表开头
            messages.insert(0, {"role": "system", "content": full_system_prompt})
        else:
            # 如果没有用户查询，检查是否需要添加基础系统提示词
            has_system_message = any(msg.get("role") == "system" for msg in messages)
            if not has_system_message:
                # 使用_build_system_prompt_with_context来构建基础提示词
                system_prompt = self._build_system_prompt_with_context()
                messages.insert(0, {"role": "system", "content": system_prompt})
        
        # 记录完整提示词到日志
        try:
            character_id = self.config_service.current_character_id or "default"
            prompt_logger.log_prompt(
                messages=messages,
                character_name=character_id,
                user_query=user_query
            )
        except Exception as e:
            self.logger.error(f"记录提示词日志失败: {e}")
        
        try:
            # 发送API请求
            # response, data = make_api_request(
            #     url=url,
            #     method="POST",
            #     headers=headers,
            #     json_data=request_data,
            #     stream=stream
            # )
            print(f"~ 发送对话请求:")
            for message in messages:
                print(f"{message['role']}: {message['content'][:50]}...")
            print('~')
            # 处理流式响应
            if stream:
                del_list = ['model', 'stream', 'top_k']
                for key in del_list:
                    if key in chat_config:
                        del chat_config[key]
                
                def stream_generator():
                    stream_ans = self.client.chat.completions.create(
                        model=os.getenv("CHAT_MODEL"),
                        messages=messages,
                        stream=True,
                        response_format={"type": "json_object"},
                        **chat_config
                    )
                    ifreasoning = False
                    for chunk in stream_ans:
                        data = chunk.choices[0].delta
                        x = data.content
                        if data.content is None:
                            if ifreasoning is False:
                                print('思考中...')
                                ifreasoning = True
                                # yield '思考中...\n'
                            x = data.reasoning_content
                            print(x, end="", flush=True)
                            continue
                        else:
                            if ifreasoning is True:
                                print('\n回答中...')
                                ifreasoning = False
                        print(x, end="", flush=True)
                        yield x
                # def stream_generator__():
                #     response.encoding = "utf-8"
                    
                #     for line in response.iter_lines(decode_unicode=True):
                #         if line:
                #             parsed_data = parse_stream_data(line)
                #             if parsed_data:                             
                #                 yield parsed_data
                    
                #     # 注意：记忆添加逻辑已移至app.py中处理，避免重复添加
                return stream_generator()
            
            ### 以下代码应该弃用! 在app.py中, 只接收流式返回!
            # else:
            #     # 处理非流式响应
            #     if "choices" in data and len(data["choices"]) > 0:
            #         message = data["choices"][0].get("message", {})
            #         if message and "content" in message:
            #             assistant_message = message["content"]
            #             # 将助手回复添加到历史记录
            #             self.add_message("assistant", assistant_message)
                        
            #             # 添加到记忆数据库
            #             if user_query:
            #                 try:
            #                     character_id = self.config_service.current_character_id or "default"
            #                     self.memory_service.add_conversation(
            #                         user_message=user_query,
            #                         assistant_message=assistant_message,
            #                         character_name=character_id
            #                     )
            #                 except Exception as e:
            #                     print(f"添加对话到记忆数据库失败: {e}")
                
            #     return data
            
        except APIError as e:
            # 处理API错误
            error_info = handle_api_error(e)
            raise APIError(error_info["error"], e.status_code, error_info)

    async def chat_completion_async(self, messages: Optional[List[Dict[str, str]]] = None, 
                                user_query: str = None) -> Iterator[str]:
        """
        异步对话API调用（预留接口）
        
        Args:
            messages: 消息列表
            user_query: 用户查询
            
        Returns:
            Iterator[str]: 流式响应
            
        Note:
            此为预留接口，将在未来实现异步支持
        """
        raise NotImplementedError("异步支持将在未来版本实现")

# 创建全局对话服务实例
chat_service = ChatService()

if __name__ == "__main__":
    # 测试对话服务
    try:
        # 初始化配置
        if not config_service.initialize():
            logging.error("配置初始化失败")
            sys.exit(1)
        
        # 设置系统提示词
        chat_service.set_system_prompt()
        
        # 添加用户消息
        chat_service.add_message("user", "你好，请介绍一下自己")
        
        # 调用API（流式）
        logging.info("发送API请求...")
        for token in chat_service.chat_completion(stream=True):
            print(token, end="", flush=True)
        
        # 打印对话历史
        logging.info("\n对话历史:")
        for msg in chat_service.get_history():
            logging.info(f"{msg.role}: {msg.content[:50]}...")
        
    except APIError as e:
        logging.error(f"API错误: {e.message}")
        if hasattr(e, "response") and e.response:
            logging.error(f"详细信息: {e.response}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"发生错误: {str(e)}")
        sys.exit(1)

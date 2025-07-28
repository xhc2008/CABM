"""
对话服务模块
封装对话API调用和处理
"""
import sys
import json
import time
import re
from typing import List, Dict, Any, Optional, Generator, Union, Tuple
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.api_utils import make_api_request, APIError, handle_api_error, parse_stream_data
from utils.history_utils import HistoryManager
from utils.prompt_logger import prompt_logger
from services.config_service import config_service
from config import get_memory_config
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




class ChatService:
    """对话服务类"""
    
    def __init__(self):
        """初始化对话服务"""
        self.history: List[Message] = []
        self.config_service = config_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 创建历史记录管理器
        app_config = self.config_service.get_app_config()
        history_dir = app_config["history_dir"]
        self.history_manager = HistoryManager(history_dir)
        
        # 导入记忆服务（避免循环导入）
        from services.memory_service import memory_service
        self.memory_service = memory_service
        
        # 初始化时加载历史记录
        self._load_history_on_startup()
        
        # 初始化当前角色的记忆数据库
        self._initialize_character_memory()
    
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
            character_id = self.config_service.current_character_id or "default"
            self.history_manager.save_message(character_id, role, content)
        
        return message
    
    def clear_history(self, keep_system: bool = True, clear_persistent: bool = False) -> None:
        """
        清空对话历史
        
        Args:
            keep_system: 是否保留system消息
            clear_persistent: 是否清空持久化历史记录
        """
        if keep_system:
            self.history = [msg for msg in self.history if msg.role == "system"]
        else:
            self.history = []
            
        # 如果需要清空持久化历史记录
        if clear_persistent:
            character_id = self.config_service.current_character_id or "default"
            self.history_manager.clear_history(character_id)
    
    def get_history(self) -> List[Message]:
        """获取对话历史"""
        return self.history.copy()
    
    def format_messages(self) -> List[Dict[str, str]]:
        """格式化消息以适应API要求"""
        return [msg.to_dict() for msg in self.history]
    
    def set_system_prompt(self, prompt_type: str = "default") -> None:
        """
        设置系统提示词
        
        Args:
            prompt_type: 提示词类型，如果为"character"则使用当前角色的提示词
        """
        # 移除现有的system消息
        self.history = [msg for msg in self.history if msg.role != "system"]
        
        # 添加新的system消息
        system_prompt = self.config_service.get_system_prompt(prompt_type)
        self.add_message("system", system_prompt)
    
    def _load_history_on_startup(self):
        """在启动时加载历史记录到内存"""
        # 获取当前角色ID
        character_id = self.config_service.current_character_id or "default"
        
        # 获取配置
        app_config = self.config_service.get_app_config()
        max_history = app_config["max_history_length"]
        
        # 加载历史记录
        history_messages = self.history_manager.load_history(character_id, max_history, max_history * 2)
        
        # 转换为Message对象并添加到内存中
        for msg in history_messages:
            if msg["role"] != "system":  # 系统消息会通过set_system_prompt单独设置
                self.history.append(Message.from_dict(msg))
    
    def _initialize_character_memory(self):
        """初始化当前角色的记忆数据库"""
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
    
    def get_character_config(self):
        """
        获取当前角色配置
        
        Returns:
            角色配置字典
        """
        return self.config_service.get_character_config()
        
    def load_persistent_history(self, count: Optional[int] = None) -> List[Dict[str, str]]:
        """
        加载持久化历史记录
        
        Args:
            count: 加载的消息数量，如果为None则使用配置中的值
            
        Returns:
            历史记录列表
        """
        character_id = self.config_service.current_character_id or "default"
        if count is None:
            count = self.config_service.get_app_config()["max_history_length"]
        
        return self.history_manager.load_history(character_id, count)
    
    def chat_completion(
        self, 
        messages: Optional[List[Dict[str, str]]] = None, 
        stream: bool = True,
        user_query: str = None
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        调用对话API（集成记忆检索）
        
        Args:
            messages: 消息列表，如果为None则使用历史记录
            stream: 是否使用流式输出
            user_query: 用户查询，用于记忆检索和日志记录
            
        Returns:
            如果stream为False，返回完整响应
            如果stream为True，返回生成器，逐步产生响应
            
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
            
            # 确保系统提示词中包含角色设定
            has_system_message = any(msg.get("role") == "system" for msg in messages)
            if not has_system_message:
                # 如果没有系统消息，添加一个
                character_config = self.config_service.get_character_config()
                general_prompt = self.config_service.get_system_prompt("default")
                system_prompt = f"{general_prompt}\n\n{character_config['prompt']}"
                messages.insert(0, {"role": "system", "content": system_prompt})
        
        # 如果有用户查询，进行记忆检索
        memory_context = ""
        if user_query:
            try:
                character_id = self.config_service.current_character_id or "default"
                memory_context = self.memory_service.search_memory(
                    query=user_query,
                    character_name=character_id
                )
                
                # 如果有相关记忆，添加到最后一条用户消息中
                if memory_context and messages:
                    # 找到最后一条用户消息
                    for i in range(len(messages) - 1, -1, -1):
                        if messages[i]["role"] == "user":
                            original_content = messages[i]["content"]
                            messages[i]["content"] = memory_context + "\n\n" + original_content
                            break
                            
            except Exception as e:
                print(f"记忆检索失败: {e}")
                memory_context = ""
        
        # 记录完整提示词到日志
        try:
            character_id = self.config_service.current_character_id or "default"
            prompt_logger.log_prompt(
                messages=messages,
                character_name=character_id,
                user_query=user_query
            )
        except Exception as e:
            print(f"记录提示词日志失败: {e}")
        
        request_data = {
            **chat_config,
            "messages": messages,
            "stream": stream,
            "enable_thinking": False
        }
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 发送API请求
            response, data = make_api_request(
                url=url,
                method="POST",
                headers=headers,
                json_data=request_data,
                stream=stream
            )
            
            # 处理流式响应
            if stream:
                def stream_generator():
                    response.encoding = "utf-8"
                    full_content = ""
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            parsed_data = parse_stream_data(line)
                            if parsed_data:
                                # 收集完整内容用于后续添加到记忆
                                if "choices" in parsed_data and len(parsed_data["choices"]) > 0:
                                    delta = parsed_data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        full_content += delta["content"]
                                
                                yield parsed_data
                    
                    # 注意：记忆添加逻辑已移至app.py中处理，避免重复添加
                
                return stream_generator()
            
            # 处理非流式响应
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                if message and "content" in message:
                    assistant_message = message["content"]
                    # 将助手回复添加到历史记录
                    self.add_message("assistant", assistant_message)
                    
                    # 添加到记忆数据库
                    if user_query:
                        try:
                            character_id = self.config_service.current_character_id or "default"
                            self.memory_service.add_conversation(
                                user_message=user_query,
                                assistant_message=assistant_message,
                                character_name=character_id
                            )
                        except Exception as e:
                            print(f"添加对话到记忆数据库失败: {e}")
            
            return data
            
        except APIError as e:
            # 处理API错误
            error_info = handle_api_error(e)
            raise APIError(error_info["error"], e.status_code, error_info)

# 创建全局对话服务实例
chat_service = ChatService()

if __name__ == "__main__":
    # 测试对话服务
    try:
        # 初始化配置
        if not config_service.initialize():
            print("配置初始化失败")
            sys.exit(1)
        
        # 设置系统提示词
        chat_service.set_system_prompt()
        
        # 添加用户消息
        chat_service.add_message("user", "你好，请介绍一下自己")
        
        # 调用API（非流式）
        print("发送API请求...")
        response = chat_service.chat_completion(stream=False)
        
        # 打印响应
        print("\nAPI响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        
        # 打印对话历史
        print("\n对话历史:")
        for msg in chat_service.get_history():
            print(f"{msg.role}: {msg.content[:50]}...")
        
    except APIError as e:
        print(f"API错误: {e.message}")
        if hasattr(e, "response") and e.response:
            print(f"详细信息: {e.response}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)
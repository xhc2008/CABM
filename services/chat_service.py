"""
对话服务模块
封装对话API调用和处理
"""
import sys
import json
from typing import List, Dict, Any, Optional, Generator, Union
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.api_utils import make_api_request, APIError, handle_api_error, parse_stream_data
from services.config_service import config_service

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
        
        return message
    
    def clear_history(self, keep_system: bool = True) -> None:
        """
        清空对话历史
        
        Args:
            keep_system: 是否保留system消息
        """
        if keep_system:
            self.history = [msg for msg in self.history if msg.role == "system"]
        else:
            self.history = []
    
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
            # 设置系统提示词
            self.set_system_prompt("character")
            return True
        
        return False
    
    def get_character_config(self):
        """
        获取当前角色配置
        
        Returns:
            角色配置字典
        """
        return self.config_service.get_character_config()
    
    def chat_completion(
        self, 
        messages: Optional[List[Dict[str, str]]] = None, 
        stream: bool = True
    ) -> Union[Dict[str, Any], Generator[Dict[str, Any], None, None]]:
        """
        调用对话API
        
        Args:
            messages: 消息列表，如果为None则使用历史记录
            stream: 是否使用流式输出
            
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
        
        # 准备请求数据
        messages = messages or self.format_messages()
        
        request_data = {
            **chat_config,
            "messages": messages,
            "stream": stream
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
                                # 如果是结束标记
                                if parsed_data.get("done"):
                                    # 将完整消息添加到历史记录
                                    if full_content:
                                        self.add_message("assistant", full_content)
                                    yield {"done": True}
                                    break
                                
                                # 处理增量内容
                                if "choices" in parsed_data and len(parsed_data["choices"]) > 0:
                                    delta = parsed_data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        full_content += delta["content"]
                                
                                yield parsed_data
                
                return stream_generator()
            
            # 处理非流式响应
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                if message and "content" in message:
                    # 将助手回复添加到历史记录
                    self.add_message("assistant", message["content"])
            
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
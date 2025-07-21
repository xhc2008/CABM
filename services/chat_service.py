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

class StreamController:
    """流式输出控制器"""
    
    def __init__(self, config_service):
        """初始化流式输出控制器"""
        self.config_service = config_service
        self.buffer = ""
        self.current_paragraph = ""
        self.paragraphs = []
        self.is_paused = False
        self.is_complete = False
        self.last_output_time = 0
        self.stream_config = self.config_service.get_stream_config()
    
    def process_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理流式数据块
        
        Args:
            chunk: 流式数据块
            
        Returns:
            处理后的数据块，添加了控制信息
        """
        # 更新配置
        self.stream_config = self.config_service.get_stream_config()
        
        # 如果是结束标记
        if chunk.get("done"):
            self.is_complete = True
            # 如果还有未处理的段落，添加到结果中
            if self.current_paragraph:
                self.paragraphs.append(self.current_paragraph)
                self.current_paragraph = ""
            
            # 添加控制信息
            chunk["stream_control"] = {
                "is_complete": True,
                "paragraphs": self.paragraphs
            }
            return chunk
        
        # 处理增量内容
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                content = delta["content"]
                self.buffer += content
                
                # 检查是否有完整段落
                paragraph_delimiters = self.stream_config["paragraph_delimiters"]
                for delimiter in paragraph_delimiters:
                    if delimiter in self.buffer:
                        # 分割段落
                        parts = re.split(f"({delimiter})", self.buffer, 1)
                        if len(parts) >= 3:
                            # 添加完整段落到结果
                            complete_paragraph = self.current_paragraph + parts[0] + parts[1]
                            self.paragraphs.append(complete_paragraph)
                            
                            # 更新当前段落和缓冲区
                            self.current_paragraph = ""
                            self.buffer = parts[2]
                            
                            # 添加控制信息
                            chunk["stream_control"] = {
                                "is_complete": False,
                                "paragraph_complete": True,
                                "paragraph": complete_paragraph,
                                "pause": self.stream_config["pause_on_paragraph"]
                            }
                            return chunk
                
                # 如果没有完整段落，添加到当前段落
                self.current_paragraph += self.buffer
                self.buffer = ""
        
        # 添加控制信息
        chunk["stream_control"] = {
            "is_complete": False,
            "paragraph_complete": False,
            "content": delta.get("content", "")
        }
        
        return chunk
    
    def control_output_speed(self) -> float:
        """
        控制输出速度
        
        Returns:
            需要等待的秒数
        """
        current_time = time.time()
        output_speed = self.stream_config["output_speed"]
        
        # 如果输出速度为0，不限制速度
        if output_speed <= 0:
            return 0
        
        # 计算需要等待的时间
        time_per_char = 1.0 / output_speed
        elapsed = current_time - self.last_output_time
        
        # 如果已经过了足够的时间，不需要等待
        if elapsed >= time_per_char:
            self.last_output_time = current_time
            return 0
        
        # 计算需要等待的时间
        wait_time = time_per_char - elapsed
        self.last_output_time = current_time + wait_time
        return wait_time
    
    def reset(self):
        """重置控制器状态"""
        self.buffer = ""
        self.current_paragraph = ""
        self.paragraphs = []
        self.is_paused = False
        self.is_complete = False
        self.last_output_time = 0


class ChatService:
    """对话服务类"""
    
    def __init__(self):
        """初始化对话服务"""
        self.history: List[Message] = []
        self.config_service = config_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 创建流式输出控制器
        self.stream_controller = StreamController(self.config_service)
        
        # 创建历史记录管理器
        app_config = self.config_service.get_app_config()
        history_dir = app_config["history_dir"]
        self.history_manager = HistoryManager(history_dir)
        
        # 初始化时加载历史记录
        self._load_history_on_startup()
    
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
        if messages is None:
            # 使用内存中的历史记录（已经包含了从持久化存储加载的记录）
            messages = self.format_messages()
        
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
                # 重置流式控制器状态
                self.stream_controller.reset()
                
                def stream_generator():
                    response.encoding = "utf-8"
                    full_content = ""
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            parsed_data = parse_stream_data(line)
                            if parsed_data:
                                # 处理流式数据
                                processed_chunk = self.stream_controller.process_chunk(parsed_data)
                                
                                # 如果是结束标记
                                if processed_chunk.get("done"):
                                    # 将完整消息添加到历史记录
                                    if full_content:
                                        self.add_message("assistant", full_content)
                                    yield processed_chunk
                                    break
                                
                                # 处理增量内容
                                if "choices" in processed_chunk and len(processed_chunk["choices"]) > 0:
                                    delta = processed_chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        full_content += delta["content"]
                                
                                # 控制输出速度
                                wait_time = self.stream_controller.control_output_speed()
                                if wait_time > 0:
                                    time.sleep(wait_time)
                                
                                yield processed_chunk
                
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
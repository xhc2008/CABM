"""
API工具模块
用于处理API请求和错误
"""
import json
import time
import requests
from typing import Dict, Any, Optional, Tuple, List

class APIError(Exception):
    """API错误类"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

def make_api_request(
    url: str, 
    method: str = "POST", 
    headers: Optional[Dict[str, str]] = None, 
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    stream: bool = False,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: int = 1
) -> Tuple[requests.Response, Any]:
    """
    发送API请求并处理错误
    
    Args:
        url: API端点URL
        method: HTTP方法，默认为POST
        headers: 请求头
        data: 表单数据
        json_data: JSON数据
        stream: 是否使用流式响应
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        
    Returns:
        元组 (response, data)，其中response是请求响应对象，data是响应数据
        
    Raises:
        APIError: 当API请求失败时
    """
    method = method.upper()
    headers = headers or {}
    
    # 添加默认的Content-Type
    if json_data is not None and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    
    retries = 0
    last_error = None
    
    while retries < max_retries:
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                stream=stream,
                timeout=timeout
            )
            
            # 检查HTTP状态码
            if response.status_code >= 400:
                error_msg = f"API请求失败: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and "error" in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    pass
                
                raise APIError(error_msg, response.status_code, response)
            
            # 如果是流式响应，直接返回响应对象
            if stream:
                return response, None
            
            # 解析JSON响应
            try:
                response_data = response.json()
                return response, response_data
            except json.JSONDecodeError:
                # 如果不是JSON响应，返回文本内容
                return response, response.text
                
        except (requests.RequestException, APIError) as e:
            last_error = e
            retries += 1
            
            # 如果是最后一次重试，或者是认证错误（不需要重试），则抛出异常
            if retries >= max_retries or (
                isinstance(e, APIError) and e.status_code in (401, 403)
            ):
                if isinstance(e, requests.RequestException):
                    raise APIError(f"API请求失败: {str(e)}")
                raise e
            
            # 等待一段时间后重试
            time.sleep(retry_delay)
    
    # 如果所有重试都失败，抛出最后一个错误
    if isinstance(last_error, APIError):
        raise last_error
    raise APIError(f"API请求失败，已重试{max_retries}次: {str(last_error)}")

def handle_api_error(error: APIError) -> Dict[str, Any]:
    """
    处理API错误并返回友好的错误信息
    
    Args:
        error: API错误对象
        
    Returns:
        包含错误信息的字典
    """
    error_info = {
        "success": False,
        "error": error.message,
        "status_code": error.status_code
    }
    
    # 根据状态码提供更具体的错误信息
    if error.status_code == 401:
        error_info["error"] = "认证失败，请检查API密钥"
        error_info["solution"] = "请确保在.env文件中设置了正确的API密钥"
    elif error.status_code == 403:
        error_info["error"] = "没有权限访问该API"
        error_info["solution"] = "请确保API密钥有权限访问该资源"
    elif error.status_code == 404:
        error_info["error"] = "API端点不存在"
        error_info["solution"] = "请检查API URL是否正确"
    elif error.status_code == 429:
        error_info["error"] = "API请求过于频繁，已被限流"
        error_info["solution"] = "请稍后再试或减少请求频率"
    elif error.status_code and 500 <= error.status_code < 600:
        error_info["error"] = "API服务器错误"
        error_info["solution"] = "请稍后再试，服务器可能暂时不可用"
    elif "connection" in error.message.lower():
        error_info["error"] = "网络连接错误"
        error_info["solution"] = "请检查网络连接并重试"
    elif "timeout" in error.message.lower():
        error_info["error"] = "API请求超时"
        error_info["solution"] = "请稍后再试或增加超时时间"
    
    return error_info

def parse_stream_data(line: str) -> Optional[Dict[str, Any]]:
    """
    解析流式响应数据行
    
    Args:
        line: 响应数据行
        
    Returns:
        解析后的数据字典，如果不是有效数据则返回None
    """
    if not line or line.strip() == "":
        return None
    
    # 移除"data: "前缀（如果有）
    if line.startswith("data: "):
        line = line[6:]
    
    # 忽略心跳消息
    if line.strip() == "[DONE]":
        return {"done": True}
    
    try:
        data = json.loads(line)
        
        # 适配讯飞星火API的流式输出格式
        if "payload" in data:
            try:
                # 尝试获取内容
                content = None
                
                # 检查不同可能的路径
                if "choices" in data["payload"]:
                    choices = data["payload"]["choices"]
                    if isinstance(choices, dict) and "text" in choices and len(choices["text"]) > 0:
                        content = choices["text"][0].get("content", "")
                    elif isinstance(choices, list) and len(choices) > 0:
                        content = choices[0].get("content", "")
                
                if content is not None:
                    # 转换为标准格式
                    return {
                        "choices": [
                            {
                                "delta": {
                                    "content": content
                                }
                            }
                        ]
                    }
            except (KeyError, IndexError, TypeError):
                # 如果解析失败，继续处理
                pass
        
        return data
    except (json.JSONDecodeError, KeyError, IndexError):
        # 如果解析失败，返回None
        return None
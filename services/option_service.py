"""
选项生成服务模块
负责生成用户对话选项
"""
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.api_utils import make_api_request, APIError, handle_api_error
from services.config_service import config_service

class OptionService:
    """选项生成服务类"""
    
    def __init__(self):
        """初始化选项生成服务"""
        self.config_service = config_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
    
    def generate_options(
        self, 
        conversation_history: List[Dict[str, str]], 
        character_config: Dict[str, Any],
        user_query: str
    ) -> List[str]:
        """
        生成对话选项
        
        Args:
            conversation_history: 对话历史记录
            character_config: 角色配置
            user_query: 用户最后的查询
            
        Returns:
            生成的选项列表（最多3个）
            
        Raises:
            APIError: 当API调用失败时
        """
        # 检查是否启用选项生成
        option_config = self.config_service.get_option_config()
        if not option_config.get("enable_option_generation", True):
            return []
        
        # 获取API配置
        url = self.config_service.get_option_api_url()
        api_key = self.config_service.get_option_api_key()
        system_prompt = self.config_service.get_option_system_prompt()
        
        # 构建用户提示词
        user_prompt = self._build_user_prompt(conversation_history, character_config, user_query)
        
        # 准备请求数据
        request_data = {
            "model": option_config["model"],
            "max_tokens": option_config["max_tokens"],
            "temperature": option_config["temperature"],
            "stream": option_config["stream"],
            "enable_thinking": False,  # 关闭思考
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
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
                stream=False
            )
            
            # 处理响应
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                if message and "content" in message:
                    content = message["content"].strip()
                    
                    # 按换行符分割选项
                    options = [opt.strip() for opt in content.split('\n') if opt.strip()]
                    
                    # 限制最多3个选项
                    return options[:3]
            
            return []
            
        except APIError as e:
            # 处理API错误
            error_info = handle_api_error(e)
            print(f"选项生成API错误: {error_info['error']}")
            return []
        except Exception as e:
            print(f"选项生成失败: {str(e)}")
            return []
    
    def _build_user_prompt(
        self, 
        conversation_history: List[Dict[str, str]], 
        character_config: Dict[str, Any],
        user_query: str
    ) -> str:
        """
        构建用户提示词
        
        Args:
            conversation_history: 对话历史记录
            character_config: 角色配置
            user_query: 用户最后的查询
            
        Returns:
            构建的用户提示词
        """
        # 构建对话历史部分
        history_text = ""
        for msg in conversation_history[-6:]:  # 只取最近6条消息
            role = msg["role"]
            content = msg["content"]
            
            if role == "user":
                history_text += f"用户: {content}\n"
            elif role == "assistant":
                history_text += f"{character_config['name']}: {content}\n"
        
        # 构建角色设定部分
        character_setting = f"角色名称: {character_config['name']}\n"
        character_setting += f"角色描述: {character_config['description']}\n"
        character_setting += f"角色设定: {character_config['prompt']}\n"
        
        # 构建完整的用户提示词
        user_prompt = f"""对话历史:
{history_text}

{character_setting}

用户最后的问题: {user_query}

请基于以上对话历史、角色设定和用户最后的问题，生成3个用户可能想要继续询问的问题选项。"""
        
        return user_prompt

# 创建全局选项生成服务实例
option_service = OptionService()

if __name__ == "__main__":
    # 测试选项生成服务
    try:
        # 初始化配置
        if not config_service.initialize():
            print("配置初始化失败")
            sys.exit(1)
        
        # 模拟对话历史
        test_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！我是凌音，很高兴见到你。"},
            {"role": "user", "content": "你喜欢什么音乐？"}
        ]
        
        # 获取角色配置
        character_config = config_service.get_character_config()
        
        # 生成选项
        print("生成选项...")
        options = option_service.generate_options(
            conversation_history=test_history,
            character_config=character_config,
            user_query="你喜欢什么音乐？"
        )
        
        # 打印结果
        print("\n生成的选项:")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)
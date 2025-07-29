"""
选项生成服务模块
负责生成用户对话选项
"""
import sys
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.config_service import config_service

class OptionService:
    """选项生成服务类"""
    
    def __init__(self):
        """初始化选项生成服务"""
        self.config_service = config_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 初始化 OpenAI 客户端
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("OPTION_API_KEY"),
                base_url=os.getenv("OPTION_API_BASE_URL")
            )
        except ImportError:
            print("未找到openai模块，请安装openai模块")
            self.client = None
    
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
        
        # 检查客户端是否可用
        if not self.client:
            print("OpenAI客户端未初始化，跳过选项生成")
            return []
        
        # 获取系统提示词
        system_prompt = self.config_service.get_option_system_prompt()
        
        # 构建用户提示词
        user_prompt = self._build_user_prompt(conversation_history, character_config, user_query)
        
        try:
            # 构建请求参数
            request_params = {
                "model": os.getenv("OPTION_MODEL"),
                "max_tokens": option_config["max_tokens"],
                "temperature": option_config["temperature"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }
            
            # 根据OpenAI库规范，添加禁用思考的参数
            # 对于支持reasoning的模型（如o1系列），可以通过reasoning参数控制
            # model_name = os.getenv("OPTION_MODEL", "").lower()
            # if "o1" in model_name or "reasoning" in model_name:
            #     request_params["reasoning"] = False
            
            # 使用 OpenAI 库调用选项生成API
            response = self.client.chat.completions.create(**request_params)
            
            # 处理响应
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content.strip()
                
                # 按换行符分割选项
                options = [opt.strip() for opt in content.split('\n') if opt.strip()]
                
                # 限制最多3个选项
                return options[:3]
            
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
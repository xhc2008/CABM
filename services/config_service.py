"""
配置服务
负责加载和管理应用配置
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.env_utils import load_env_vars, get_env_var
import config
import characters

class ConfigService:
    """配置服务类"""
    
    def __init__(self):
        """初始化配置服务"""
        self.initialized = False
        self.config_loaded = False
        self.current_character_id = None
    
    def initialize(self):
        """初始化配置"""
        if self.initialized:
            return True
        
        # 加载环境变量
        if not load_env_vars():
            print("环境变量加载失败")
            return False
        
        # 验证配置
        try:
            config.validate_config()
            self.config_loaded = True
        except ValueError as e:
            print(f"配置验证失败: {e}")
            return False
        
        # 创建必要的目录
        self._create_required_directories()
        
        # 加载默认角色
        self.current_character_id = None
        self.get_character_config()
        
        self.initialized = True
        return True
    
    def _create_required_directories(self):
        """创建必要的目录"""
        # 创建图像缓存目录
        cache_dir = config.APP_CONFIG["image_cache_dir"]
        os.makedirs(cache_dir, exist_ok=True)
        
        # 创建静态资源目录
        static_dir = config.APP_CONFIG["static_folder"]
        os.makedirs(static_dir, exist_ok=True)
        
        # 创建模板目录
        template_dir = config.APP_CONFIG["template_folder"]
        os.makedirs(template_dir, exist_ok=True)
        
        # 创建历史记录目录
        history_dir = config.APP_CONFIG["history_dir"]
        os.makedirs(history_dir, exist_ok=True)
    
    def _get_character_moods(self, character_id: str) -> list:
        """
        获取角色的心情列表
        
        Args:
            character_id: 角色ID
            
        Returns:
            心情列表
        """
        # 首先尝试从角色配置中获取心情列表（TOML格式）
        character_config = characters.get_character_config(character_id)
        if character_config and 'moods' in character_config:
            return character_config['moods']
        
        # 如果没有找到，尝试从角色模块获取（Python格式，向后兼容）
        character_module = characters.get_character_module(character_id)
        if character_module and hasattr(character_module, 'MOODS') and character_module.MOODS:
            return character_module.MOODS
        
        # 如果都没有找到，返回空列表
        return []
    
    def get_chat_config(self):
        """获取对话模型配置"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_chat_config()
    
    def get_image_config(self):
        """获取图像生成模型配置"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_image_config()
    
    def get_system_prompt(self, prompt_type="default"):
        """
        获取系统提示词
        
        Args:
            prompt_type: 提示词类型，如果为"character"则使用当前角色的提示词和通用提示词
            
        Returns:
            系统提示词
        """
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        
        if prompt_type == "character":
            character_config = self.get_character_config()
            general_prompt = config.get_system_prompt("default")
            
            # 获取角色的心情列表并动态拼接
            moods = self._get_character_moods(character_config['id'])
            if moods:
                # 构建心情字符串，格式：1.心情1 2.心情2 3.心情3 4.心情4
                mood_str = " ".join([f"{i+1}.{mood}" for i, mood in enumerate(moods)])
                # 替换通用提示词中的心情部分
                general_prompt = general_prompt.replace("<[MOODS]>", mood_str)
            
            return f"{general_prompt}\n\n{character_config['prompt']}"
        
        # 对于非角色类型的提示词，也需要处理心情拼接
        prompt = config.get_system_prompt(prompt_type)
        if self.current_character_id:
            moods = self._get_character_moods(self.current_character_id)
            if moods:
                mood_str = " ".join([f"{i+1}.{mood}" for i, mood in enumerate(moods)])
                prompt = prompt.replace("<[MOODS]>", mood_str)
        
        return prompt
    
    def get_random_image_prompt(self):
        """获取随机图像提示词"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_random_image_prompt()
    
    def get_app_config(self):
        """获取应用配置"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_app_config()
    
    def get_stream_config(self):
        """获取流式输出配置"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_stream_config()
    
    def get_chat_api_base_url(self):
        """获取对话API Base URL"""
        return get_env_var("CHAT_API_BASE_URL")
    
    def get_chat_api_key(self):
        """获取对话API密钥"""
        return get_env_var("CHAT_API_KEY")
    
    def get_image_api_base_url(self):
        """获取图像API Base URL"""
        return get_env_var("IMAGE_API_BASE_URL")
    
    def get_image_api_key(self):
        """获取图像API密钥"""
        return get_env_var("IMAGE_API_KEY")
    
    def get_option_api_base_url(self):
        """获取选项生成API Base URL"""
        return get_env_var("OPTION_API_BASE_URL")
    
    def get_option_api_key(self):
        """获取选项生成API密钥"""
        return get_env_var("OPTION_API_KEY")
    
    # 保持向后兼容性的方法
    def get_chat_api_url(self):
        """获取对话API URL（向后兼容）"""
        return self.get_chat_api_base_url()
    
    def get_image_api_url(self):
        """获取图像API URL（向后兼容）"""
        return self.get_image_api_base_url()
    
    def get_option_api_url(self):
        """获取选项生成API URL（向后兼容）"""
        return self.get_option_api_base_url()
    
    def get_option_config(self):
        """获取选项生成配置"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_option_config()
    
    def get_option_system_prompt(self):
        """获取选项生成系统提示词"""
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        return config.get_option_system_prompt()
    
    def get_character_config(self, character_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取角色配置
        
        Args:
            character_id: 角色ID，如果为None则使用当前角色或默认角色
            
        Returns:
            角色配置字典
        """
        # 如果未指定角色ID，使用当前角色
        if character_id is None:
            character_id = self.current_character_id
        
        # 加载角色配置
        character_config = characters.get_character_config(character_id)
        
        # 更新当前角色ID
        self.current_character_id = character_config["id"]
        
        return character_config
    
    def set_character(self, character_id: str) -> bool:
        """
        设置当前角色
        
        Args:
            character_id: 角色ID
            
        Returns:
            是否设置成功
        """
        # 加载角色配置
        character_config = characters.get_character_config(character_id)
        
        # 如果成功加载，更新当前角色ID
        if character_config["id"] == character_id:
            self.current_character_id = character_id
            return True
        
        return False
    
    def list_available_characters(self):
        """
        列出所有可用的角色
        
        Returns:
            角色配置列表
        """
        return characters.list_available_characters()

# 创建全局配置服务实例
config_service = ConfigService()

if __name__ == "__main__":
    # 测试配置服务
    if config_service.initialize():
        print("配置服务初始化成功")
        print(f"对话API Base URL: {config_service.get_chat_api_base_url()}")
        print(f"图像API Base URL: {config_service.get_image_api_base_url()}")
        print(f"对话模型: {config_service.get_chat_config()['model']}")
        print(f"图像模型: {config_service.get_image_config()['model']}")
        print(f"流式输出启用: {config_service.get_stream_config()['enable_streaming']}")
        
        # 测试角色配置
        character = config_service.get_character_config()
        print(f"\n当前角色: {character['name']} ({character['id']})")
        print(f"角色描述: {character['description'][:50]}...")
        
        # 列出所有可用角色
        print("\n可用角色:")
        for char in config_service.list_available_characters():
            print(f"- {char['name']} ({char['id']})")
    else:
        print("配置服务初始化失败")
        sys.exit(1)
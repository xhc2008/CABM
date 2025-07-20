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
            prompt_type: 提示词类型，如果为"character"则使用当前角色的提示词
            
        Returns:
            系统提示词
        """
        if not self.config_loaded:
            raise RuntimeError("配置未加载")
        
        if prompt_type == "character":
            character_config = self.get_character_config()
            return character_config["prompt"]
        
        return config.get_system_prompt(prompt_type)
    
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
    
    def get_chat_api_url(self):
        """获取对话API URL"""
        return get_env_var("CHAT_API_URL")
    
    def get_chat_api_key(self):
        """获取对话API密钥"""
        return get_env_var("CHAT_API_KEY")
    
    def get_image_api_url(self):
        """获取图像API URL"""
        return get_env_var("IMAGE_API_URL")
    
    def get_image_api_key(self):
        """获取图像API密钥"""
        return get_env_var("IMAGE_API_KEY")
    
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
        print(f"对话API URL: {config_service.get_chat_api_url()}")
        print(f"图像API URL: {config_service.get_image_api_url()}")
        print(f"对话模型: {config_service.get_chat_config()['model']}")
        print(f"图像模型: {config_service.get_image_config()['model']}")
        
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
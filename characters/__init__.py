"""
角色配置管理模块
"""
import os
import sys
import importlib
from pathlib import Path
from typing import Dict, List, Any, Optional

# 角色配置缓存
_character_configs = {}
_default_character_id = "Silver_Wolf"

def load_character_config(character_id: str) -> Optional[Dict[str, Any]]:
    """
    加载角色配置
    
    Args:
        character_id: 角色ID
        
    Returns:
        角色配置字典，如果未找到则返回None
    """
    # 如果已经加载过，直接返回缓存
    if character_id in _character_configs:
        return _character_configs[character_id]
    
    try:
        # 尝试导入角色模块
        module_name = f"characters.{character_id}"
        module = importlib.import_module(module_name)
        
        # 获取角色配置
        if hasattr(module, "get_character_config"):
            config = module.get_character_config()
            _character_configs[character_id] = config
            return config
        
        return None
    except (ImportError, AttributeError):
        return None

def get_character_config(character_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取角色配置
    
    Args:
        character_id: 角色ID，如果为None则使用默认角色
        
    Returns:
        角色配置字典
    """
    # 如果未指定角色ID，使用默认角色
    if character_id is None:
        character_id = _default_character_id
    
    # 加载角色配置
    config = load_character_config(character_id)
    
    # 如果未找到配置，使用默认角色
    if config is None and character_id != _default_character_id:
        config = load_character_config(_default_character_id)
    
    # 如果仍未找到配置，返回空配置
    if config is None:
        return {
            "id": "default",
            "name": "AI助手",
            "name_en": "AI Assistant",
            "image": "static/images/default/1.png",
            "calib": 0,
            "color": "#ffffff",
            "description": "默认AI助手",
            "prompt": "你是一个有用的AI助手。",
            "welcome": "你好，我是AI助手。有什么我可以帮助你的吗？",
            "examples": []
        }
    
    # 确保图像路径正确处理
    if "image" in config and config["image"].startswith("data/"):
        # 将data路径转换为URL路径
        config["image"] = "/" + config["image"]
    
    return config

def list_available_characters() -> List[Dict[str, Any]]:
    """
    列出所有可用的角色
    
    Returns:
        角色配置列表
    """
    characters = []
    
    # 获取角色目录
    characters_dir = Path(__file__).parent
    
    # 遍历角色目录
    for file_path in characters_dir.glob("*.py"):
        # 跳过__init__.py
        if file_path.name == "__init__.py":
            continue
        
        # 获取角色ID
        character_id = file_path.stem
        
        # 加载角色配置
        config = load_character_config(character_id)
        if config:
            characters.append(config)
    
    return characters

def get_character_module(character_id: str):
    """
    获取角色模块
    
    Args:
        character_id: 角色ID
        
    Returns:
        角色模块对象，如果未找到则返回None
    """
    try:
        # 尝试导入角色模块
        module_name = f"characters.{character_id}"
        module = importlib.import_module(module_name)
        return module
    except ImportError:
        return None

def set_default_character(character_id: str) -> bool:
    """
    设置默认角色
    
    Args:
        character_id: 角色ID
        
    Returns:
        是否设置成功
    """
    global _default_character_id
    
    # 检查角色是否存在
    if load_character_config(character_id) is not None:
        _default_character_id = character_id
        return True
    
    return False
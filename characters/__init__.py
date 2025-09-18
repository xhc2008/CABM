"""
角色配置管理模块
支持 TOML 和 Python 双格式的角色配置
"""
import os
import sys
import importlib
import rtoml
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.env_utils import get_env_var

# 角色配置缓存
_character_configs = {}
_default_character_id = "Silver_Wolf"

def load_character_config_from_toml(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    从 TOML 文件加载角色配置
    
    Args:
        file_path: TOML 文件路径
        
    Returns:
        角色配置字典，如果未找到则返回None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = rtoml.load(f)
            
        # 构建标准格式的配置字典
        config = {
            "id": data.get("id", file_path.stem),
            "name": data.get("name", "未命名角色"),
            "name_en": data.get("name_en", ""),
            "image": data.get("image", "static/images/default/1.png"),
            "calib": data.get("calib", 0),
            "scale_rate": data.get("scale_rate", 100),
            "color": data.get("color", "#ffffff"),
            "description": data.get("description", ""),
            "prompt": data.get("prompt", ""),
            "welcome": data.get("welcome", "你好，我是AI助手。有什么我可以帮助你的吗？"),
            #"examples": data.get("examples", []),
            "moods": [m.get("name", "") for m in data.get("moods", [])]
        }
        return config
    except Exception as e:
        print(f"加载TOML配置文件失败 {file_path}: {str(e)}")
        return None

def load_character_config_from_py(module_name: str) -> Optional[Dict[str, Any]]:
    """
    从 Python 模块加载角色配置
    
    Args:
        module_name: 模块名称
        
    Returns:
        角色配置字典，如果未找到则返回None
    """
    try:
        # 尝试导入角色模块
        module = importlib.import_module(module_name)
        
        # 获取角色配置
        if hasattr(module, "get_character_config"):
            return module.get_character_config()
        
        return None
    except (ImportError, AttributeError):
        return None

def load_character_config(character_id: str) -> Optional[Dict[str, Any]]:
    """
    加载角色配置，优先加载 TOML 格式，除非 OPEN_SAOVC=true
    
    Args:
        character_id: 角色ID
        
    Returns:
        角色配置字典，如果未找到则返回None
    """
    # 如果已经加载过，直接返回缓存
    if character_id in _character_configs:
        return _character_configs[character_id]
    
    # 获取环境变量
    open_saovc = get_env_var("OPEN_SAOVC", "false").lower() == "true"
    
    # 构建文件路径
    characters_dir = Path(__file__).parent
    toml_path = characters_dir / f"{character_id}.toml"
    
    config = None
    
    # 如果不是强制使用旧版格式且存在TOML文件，优先使用TOML
    if not open_saovc and toml_path.exists():
        config = load_character_config_from_toml(toml_path)
    
    # 如果没有找到TOML配置或强制使用旧版格式，尝试加载Python模块
    if config is None:
        module_name = f"characters.{character_id}"
        config = load_character_config_from_py(module_name)
    
    # 如果成功加载，缓存配置
    if config is not None:
        _character_configs[character_id] = config
    
    return config

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
            "scale_rate": 100,
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
    
    # 确保所有必要字段都有默认值
    if "scale_rate" not in config:
        config["scale_rate"] = 100
    
    return config

def list_available_characters() -> List[Dict[str, Any]]:
    """
    列出所有可用的角色
    
    Returns:
        角色配置列表
    """
    characters = []
    characters_dir = Path(__file__).parent
    open_saovc = get_env_var("OPEN_SAOVC", "false").lower() == "true"
    
    # 遍历TOML文件
    if not open_saovc:
        for file_path in characters_dir.glob("*.toml"):
            config = load_character_config(file_path.stem)
            if config:
                characters.append(config)
    
    # 如果是强制使用旧版格式或者没有找到TOML文件，遍历Python文件
    if open_saovc or not characters:
        for file_path in characters_dir.glob("*.py"):
            if file_path.name == "__init__.py":
                continue
            config = load_character_config(file_path.stem)
            if config:
                characters.append(config)
    
    return characters

def get_character_module(character_id: str):
    """
    获取角色模块（仅用于兼容旧版本）
    
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
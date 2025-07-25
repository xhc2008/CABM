"""
环境变量加载工具
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 自动加载环境变量
_env_loaded = False

def _auto_load_env():
    """自动加载环境变量（仅加载一次）"""
    global _env_loaded
    if not _env_loaded:
        base_dir = Path(__file__).resolve().parent.parent
        env_path = base_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            _env_loaded = True

# 在模块导入时自动加载环境变量
_auto_load_env()

def load_env_vars(env_file=".env"):
    """
    加载环境变量文件
    
    Args:
        env_file (str): 环境变量文件路径，默认为.env
        
    Returns:
        bool: 是否成功加载环境变量
    """
    # 获取项目根目录
    base_dir = Path(__file__).resolve().parent.parent
    env_path = base_dir / env_file
    
    # 检查环境变量文件是否存在
    if not env_path.exists():
        print(f"错误: 找不到环境变量文件 {env_file}")
        print(f"请复制 {env_file}.example 到 {env_file} 并填写正确的配置")
        return False
    
    # 加载环境变量
    load_dotenv(env_path)
    
    # 验证必要的环境变量
    required_vars = [
        "CHAT_API_URL", 
        "CHAT_API_KEY",
        "CHAT_MODEL",
        "IMAGE_API_URL",
        "IMAGE_API_KEY",
        "IMAGE_MODEL",
        "EMBEDDING_API_URL",
        "EMBEDDING_API_KEY",
        "EMBEDDING_MODEL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"错误: 缺少必要的环境变量: {', '.join(missing_vars)}")
        print(f"请在 {env_file} 文件中设置这些变量")
        return False
    
    return True

def get_env_var(name, default=None):
    """
    获取环境变量值
    
    Args:
        name (str): 环境变量名称
        default: 默认值，如果环境变量不存在则返回此值
        
    Returns:
        环境变量值或默认值
    """
    return os.getenv(name, default)

if __name__ == "__main__":
    # 测试环境变量加载
    if load_env_vars():
        print("环境变量加载成功")
        print(f"CHAT_API_URL: {get_env_var('CHAT_API_URL')}")
        print(f"IMAGE_API_URL: {get_env_var('IMAGE_API_URL')}")
        print(f"EMBEDDING_API_URL: {get_env_var('EMBEDDING_API_URL')}")
        print(f"EMBEDDING_MODEL: {get_env_var('EMBEDDING_MODEL')}")
    else:
        sys.exit(1)
"""
应用配置文件
包含模型配置、提示词和其他应用设置
"""
from utils.env_utils import get_env_var

# 对话模型配置
CHAT_CONFIG = {
    "model": get_env_var("CHAT_MODEL","deepseek-ai/DeepSeek-V3"),  # 默认模型
    "max_tokens": 4096,   # 最大生成令牌数
    "top_k": 5,           # Top-K采样
    "temperature": 1.0,   # 温度参数，控制创造性
    "stream": True,       # 默认使用流式输出
}



# 流式输出配置
STREAM_CONFIG = {
    "enable_streaming": True,     # 启用流式输出
}

# 图像生成模型配置
IMAGE_CONFIG = {
    "model": get_env_var("IMAGE_MODEL","Kwai-Kolors/Kolors"),  # 默认模型
    "image_size": "1024x1024",      # 默认图像尺寸
    "batch_size": 1,                # 默认生成数量
    "num_inference_steps": 20,      # 推理步数
    "guidance_scale": 7.5,          # 引导比例
}

# 通用提示词配置
SYSTEM_PROMPTS = {
    "default": "禁止使用markdown",
}

# 图像提示词配置
IMAGE_PROMPTS = [
    "繁星点缀的夜空下，一片宁静的湖泊倒映着群山和森林，远处有篝火和小屋",
    "阳光透过云层，照耀在广阔的草原上，野花盛开，远处有山脉和小溪",
    "雪花飘落的冬日森林，松树覆盖着白雪，小路蜿蜒，远处有小木屋和炊烟",
    "雨后的城市街道，霓虹灯反射在湿润的路面上，行人撑着伞，远处是城市天际线",
    "一间温馨的二次元风格卧室，阳光透过薄纱窗帘洒在木地板上,床上散落着卡通抱枕，墙边有摆满书籍和手办的原木色书架.书桌上亮着一盏小台灯，电脑屏幕泛着微光，窗外隐约可见樱花树。画面线条柔和，色彩清新，带有动画般的细腻阴影和高光。",
]

# 负面提示词
NEGATIVE_PROMPTS = "模糊, 扭曲, 变形, 低质量, 像素化, 低分辨率, 不完整"

# 应用配置
APP_CONFIG = {
    "debug": get_env_var("DEBUG", "False").lower() == "true",
    "port": int(get_env_var("PORT", "5000")),
    "host": get_env_var("HOST", "0.0.0.0"),
    "static_folder": "static",
    "template_folder": "templates",
    "image_cache_dir": "static/images/cache",
    "max_history_length": 4,  # 最大对话历史长度（发送给AI的上下文长度）
    "history_dir": "data/history",  # 历史记录存储目录
    "show_scene_name": True,  # 是否在前端显示场景名称
}

def get_chat_config():
    """获取对话模型配置"""
    return CHAT_CONFIG.copy()

def get_image_config():
    """获取图像生成模型配置"""
    return IMAGE_CONFIG.copy()

def get_system_prompt(prompt_type="default"):
    """获取通用提示词"""
    return SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["default"])

def get_random_image_prompt():
    """获取随机图像提示词"""
    import random
    return random.choice(IMAGE_PROMPTS)

def get_app_config():
    """获取应用配置"""
    return APP_CONFIG.copy()

def get_stream_config():
    """获取流式输出配置"""
    return STREAM_CONFIG.copy()

def validate_config():
    """验证配置完整性"""
    # 验证对话模型配置
    required_chat_keys = ["model", "max_tokens", "temperature"]
    missing_chat_keys = [key for key in required_chat_keys if key not in CHAT_CONFIG]
    
    # 验证图像模型配置
    required_image_keys = ["model", "image_size", "guidance_scale"]
    missing_image_keys = [key for key in required_image_keys if key not in IMAGE_CONFIG]
    
    # 验证系统提示词配置
    if "default" not in SYSTEM_PROMPTS:
        missing_chat_keys.append("default_system_prompt")
    
    # 验证流式输出配置
    required_stream_keys = ["enable_streaming"]
    missing_stream_keys = [key for key in required_stream_keys if key not in STREAM_CONFIG]
    
    # 验证应用配置
    required_app_keys = ["debug", "port", "host", "image_cache_dir", "history_dir", "max_history_length", "show_scene_name"]
    missing_app_keys = [key for key in required_app_keys if key not in APP_CONFIG]
    
    # 合并所有缺失的配置项
    all_missing = missing_chat_keys + missing_image_keys + missing_stream_keys + missing_app_keys
    
    if all_missing:
        raise ValueError(f"配置不完整，缺少以下配置项: {', '.join(all_missing)}")
    
    return True

if __name__ == "__main__":
    # 测试配置验证
    try:
        if validate_config():
            print("配置验证成功")
            print(f"对话模型: {get_chat_config()['model']}")
            print(f"图像模型: {get_image_config()['model']}")
            print(f"默认系统提示词: {get_system_prompt()}")
            print(f"随机图像提示词: {get_random_image_prompt()}")
            print(f"流式输出启用: {get_stream_config()['enable_streaming']}")
    except ValueError as e:
        print(f"配置验证失败: {e}")
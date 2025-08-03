"""
应用配置文件
包含模型配置、提示词和其他应用设置
⚠警告：除非你知道自己在做什么，否则请不要修改这里的配置
"""
from utils.env_utils import get_env_var
from dotenv import load_dotenv
load_dotenv()
import os

# 对话模型配置
CHAT_CONFIG = {
    "model": get_env_var("CHAT_MODEL","deepseek-ai/DeepSeek-V3"),  # 默认模型
    "max_tokens": 512,   # 最大生成token数
    "top_k": 5,           # Top-K采样
    "temperature": 0.9,   # 温度参数，控制创造性
    "stream": True,       # 是否使用流式响应
}



# 流式输出配置
STREAM_CONFIG = {
    "enable_streaming": True,     # 启用流式输出
}

# 选项生成配置
OPTION_CONFIG = {
    "enable_option_generation": True,  # 启用选项生成
    "model": get_env_var("OPTION_MODEL", "deepseek-ai/DeepSeek-V3"),  # 选项生成模型
    "max_tokens": 100,            # 最大生成token数
    "temperature": 0.7,           # 温度参数
    "stream": False,              # 选项生成不使用流式
    'enable_thinking': False,     # 是否启用思考
}

# 记忆模块配置
MEMORY_CONFIG = {
    "top_k": 5,                   # 记忆检索返回的最相似结果数量
    "timeout": 10,                # 记忆检索超时时间（秒）
    "min_similarity": 0.3,        # 最小相似度阈值
}

RAG_CONFIG = {
    ## 多路召回选择
    # 如果你都选择了API，出现“无法使用BM25”的报错可以忽略，不影响使用
    "Multi_Recall":{
        'BM25': {
            'lan': 'zh'  # ['zh', 'en']  语言选择
        },
        "Cosine_Similarity":{
            ## 嵌入选择('Model', 'API')选择其中一个!
            
            # 'embed_func': 'Model',
            # 'embed_kwds': {
            #     'emb_model_name_or_path': 'BAAI/bge-large-zh',  # 模型名称或路径
            #     'max_len': 512,  # 每段文本最大长度
            #     'bath_size': 64,  # 批量推理大小
            #     'device': 'cuda',  # ['cuda', 'cpu']  # 使用cuda或cpu进行推理
            # },
            
            'embed_func': 'API',
            'embed_kwds': {
                'base_url': 'https://api.siliconflow.cn/v1',  # 嵌入模型的url地址
                'api_key': os.getenv("MEMORY_API_KEY"),
                'model': 'BAAI/bge-m3'
            },
            
            'vector_dim': 1024,  # 嵌入维度(必须和嵌入模型的输出维度一样! 默认bge是1024, 不用调!)
        }
    },
    'Reranker': {
        # 'reranker_func': 'Model',  # Choice ['Model', 'API']
        # 'reranker_kwds': {
        #     'rerank_model_name_or_path': 'BAAI/bge-reranker-large',
        #     'device': 'cuda'
        # }
        
        'reranker_func': 'API',
        'reranker_kwds': {
            'base_url': 'https://api.siliconflow.cn/v1',
            'api_key': os.getenv("MEMORY_API_KEY"),
            'model': 'netease-youdao/bce-reranker-base_v1'
        }
    }
    
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
    "default": """你必须以严格的JSON格式，按顺序输出以下字段：
    "mood": <int> 当前的表情，且必须是其中之一，**只写序号**：<[MOODS]>
    "content": <string> 用1到6句话回复用户，禁止换行，禁止使用markdown。
    你的身份：""",
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

OPTION_SYSTEM_PROMPTS="""
你是一个选项生成器，你需要根据对话内容，为**用户**提供3个选项。
每个选项不能多余15个字。选项之间用换行隔开。不要回复多余的提示词、解释或符号，只回复选项内容。
回复格式示例：
我觉得可以
我觉得不行
我不知道
"""
# 应用配置
APP_CONFIG = {
    "debug": get_env_var("DEBUG", "False").lower() == "true",
    "port": int(get_env_var("PORT", "5000")),
    "host": get_env_var("HOST", "0.0.0.0"),  # 服务器监听地址，0.0.0.0表示监听所有接口
    "static_folder": "static",
    "template_folder": "templates",
    "image_cache_dir": "static/images/cache",
    "max_history_length": 8,  # 最大对话历史长度（发送给AI的上下文长度）
    "history_dir": "data/history",  # 历史记录存储目录
    "show_scene_name": True,  # 是否在前端显示场景名称
    "auto_open_browser": get_env_var("AUTO_OPEN_BROWSER", "True").lower() == "true",  # 是否自动打开浏览器（会自动使用本地IP地址）
    "clean_assistant_history": get_env_var("CLEAN_ASSISTANT_HISTORY", "True").lower() == "true",  # 已弃用：JSON格式下不再需要清理【】标记
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

def get_memory_config():
    """获取记忆模块配置"""
    return MEMORY_CONFIG.copy()

def get_RAG_config():
    """获取RAG模块配置"""
    return RAG_CONFIG.copy()

def get_option_config():
    """获取选项生成配置"""
    return OPTION_CONFIG.copy()

def get_option_system_prompt():
    """获取选项生成系统提示词"""
    return OPTION_SYSTEM_PROMPTS

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
    
    # 验证记忆模块配置
    required_memory_keys = ["top_k", "timeout", "min_similarity"]
    missing_memory_keys = [key for key in required_memory_keys if key not in MEMORY_CONFIG]
    
    # 验证选项生成配置
    required_option_keys = ["enable_option_generation", "model", "max_tokens", "temperature"]
    missing_option_keys = [key for key in required_option_keys if key not in OPTION_CONFIG]
    
    # 验证应用配置
    required_app_keys = ["debug", "port", "host", "image_cache_dir", "history_dir", "max_history_length", "show_scene_name", "clean_assistant_history"]
    missing_app_keys = [key for key in required_app_keys if key not in APP_CONFIG]
    
    # 合并所有缺失的配置项
    all_missing = missing_chat_keys + missing_image_keys + missing_stream_keys + missing_memory_keys + missing_option_keys + missing_app_keys
    
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
            print(f"记忆检索top_k: {get_memory_config()['top_k']}")
            print(f"选项生成启用: {get_option_config()['enable_option_generation']}")
            print(f"选项生成模型: {get_option_config()['model']}")
    except ValueError as e:
        print(f"配置验证失败: {e}")
"""
配置测试脚本
用于测试环境变量和配置文件的加载
"""
import sys
from services.config_service import config_service

def test_config():
    """测试配置加载"""
    print("正在测试配置加载...")
    
    # 初始化配置服务
    if not config_service.initialize():
        print("配置服务初始化失败")
        return False
    
    # 测试获取配置
    try:
        # 测试对话配置
        chat_config = config_service.get_chat_config()
        print(f"对话模型: {chat_config['model']}")
        print(f"最大令牌数: {chat_config['max_tokens']}")
        
        # 测试图像配置
        image_config = config_service.get_image_config()
        print(f"图像模型: {image_config['model']}")
        print(f"图像尺寸: {image_config['image_size']}")
        
        # 测试系统提示词
        default_prompt = config_service.get_system_prompt()
        creative_prompt = config_service.get_system_prompt("creative")
        print(f"默认提示词: {default_prompt[:30]}...")
        print(f"创意提示词: {creative_prompt[:30]}...")
        
        # 测试随机图像提示词
        image_prompt = config_service.get_random_image_prompt()
        print(f"随机图像提示词: {image_prompt[:30]}...")
        
        # 测试应用配置
        app_config = config_service.get_app_config()
        print(f"调试模式: {app_config['debug']}")
        print(f"端口: {app_config['port']}")
        
        # 测试API配置
        chat_api_url = config_service.get_chat_api_url()
        image_api_url = config_service.get_image_api_url()
        print(f"对话API URL: {chat_api_url}")
        print(f"图像API URL: {image_api_url}")
        
        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    if test_config():
        print("\n配置测试成功!")
        sys.exit(0)
    else:
        print("\n配置测试失败!")
        sys.exit(1)
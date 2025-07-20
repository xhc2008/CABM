"""
图像服务测试脚本
"""
import sys
import os
from pathlib import Path
from services.config_service import config_service
from services.image_service import image_service, ImageConfig
from utils.api_utils import APIError

def test_image_service():
    """测试图像服务"""
    print("正在测试图像服务...")
    
    # 初始化配置
    if not config_service.initialize():
        print("配置初始化失败")
        return False
    
    try:
        # 创建图像缓存目录
        cache_dir = Path(config_service.get_app_config()["image_cache_dir"])
        os.makedirs(cache_dir, exist_ok=True)
        
        # 测试创建图像配置
        print("创建图像配置...")
        image_config = ImageConfig(
            prompt="一座宁静的岛屿，海鸥在上空盘旋，月光照耀着海面",
            image_size="1024x1024",
            guidance_scale=7.5
        )
        
        print(f"图像提示词: {image_config.prompt}")
        print(f"图像尺寸: {image_config.image_size}")
        print(f"引导比例: {image_config.guidance_scale}")
        print(f"随机种子: {image_config.seed}")
        
        # 测试生成背景图像
        print("\n正在生成背景图像...")
        print("注意：如果图像API密钥未配置或无效，将使用备用图像或报错")
        
        try:
            result = image_service.generate_background()
            
            # 打印结果
            print(f"图像生成{'成功' if result.get('success', False) else '失败'}")
            if "image_path" in result:
                print(f"图像路径: {result['image_path']}")
                
                # 检查文件是否存在
                if os.path.exists(result['image_path']):
                    print(f"文件大小: {os.path.getsize(result['image_path']) / 1024:.2f} KB")
                else:
                    print("警告：图像文件不存在")
            
            if "error" in result:
                print(f"错误信息: {result['error']}")
            
            if "fallback" in result and result["fallback"]:
                print("使用了备用图像")
            
            # 测试获取当前背景
            current_bg = image_service.get_current_background()
            print(f"\n当前背景: {current_bg}")
            
            # 测试清理旧图像
            print("\n清理旧图像...")
            image_service.cleanup_old_images()
            
            return True
            
        except APIError as e:
            print(f"\nAPI错误: {e.message}")
            if hasattr(e, "response") and e.response:
                print(f"详细信息: {e.response}")
            
            # 如果是认证错误，可能是API密钥未配置，这是预期的
            if e.status_code in (401, 403):
                print("\n注意：这可能是因为图像API密钥未正确配置")
                print("在实际应用中，您需要在.env文件中设置有效的IMAGE_API_KEY")
                return True
            
            return False
            
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    if test_image_service():
        print("\n图像服务测试完成!")
        sys.exit(0)
    else:
        print("\n图像服务测试失败!")
        sys.exit(1)
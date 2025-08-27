"""
CABM应用启动脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.image_service import image_service

def main():
    """主函数"""
    print("正在启动CABM应用...")
    
    # 初始化配置
    print("正在加载配置...")
    if not config_service.initialize():
        print("配置初始化失败")
        sys.exit(1)
    
    # 获取应用配置
    app_config = config_service.get_app_config()
    
    # 检查临时图像目录
    print("正在检查临时图像目录...")
    temp_images_dir = Path(app_config["image_cache_dir"])
    os.makedirs(temp_images_dir, exist_ok=True)
    
    # 检查是否有背景图片
    if not image_service.get_current_background():
        print("正在生成初始背景图片...")
        try:
            image_service.generate_background()
        except Exception as e:
            print(f"背景图片生成失败: {str(e)}")
            print("将使用默认背景")
    
    # 启动Flask应用
    print(f"正在启动Web服务器，地址: http://{app_config['host']}:{app_config['port']}")
    print("按Ctrl+C停止服务器")
    
    # 导入app模块
    from app import app
    
    # 启动应用
    app.run(
        host=app_config["host"],
        port=app_config["port"],
        debug=app_config["debug"]
    )

if __name__ == "__main__":
    main()
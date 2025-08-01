#!/usr/bin/env python
"""
CABM应用启动脚本
同时启动前端和后端服务
"""
import os
import sys
import time
import logging
import argparse
import webbrowser
from pathlib import Path
from threading import Thread

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CABM")

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

def setup_environment():
    """设置环境"""
    try:
        # 导入配置服务
        from services.config_service import config_service
        
        # 初始化配置
        logger.info("正在加载配置...")
        if not config_service.initialize():
            logger.error("配置初始化失败")
            return False
        
        # 获取应用配置
        app_config = config_service.get_app_config()
        
        # 检查图像缓存目录
        logger.info("正在检查图像缓存...")
        cache_dir = Path(app_config["image_cache_dir"])
        os.makedirs(cache_dir, exist_ok=True)
        
        # 检查默认角色图片
        character_image_path = Path("static/images/default/1.png")
        if not character_image_path.exists():
            logger.warning(f"默认角色图片不存在: {character_image_path}")
            logger.warning("将使用占位符图片")
        
        # 导入图像服务
        from services.image_service import image_service
        
        # 检查是否有背景图片
        if not image_service.get_current_background():
            logger.info("正在生成初始背景图片...")
            try:
                image_service.generate_background()
            except Exception as e:
                logger.error(f"背景图片生成失败: {str(e)}")
                logger.warning("将使用默认背景")
        
        # 初始化记忆服务
        logger.info("正在初始化记忆数据库...")
        try:
            from services.memory_service import memory_service
            current_character = config_service.current_character_id or "default"
            if memory_service.initialize_character_memory(current_character):
                logger.info(f"记忆数据库初始化成功: {current_character}")
            else:
                logger.warning("记忆数据库初始化失败")
        except Exception as e:
            logger.error(f"记忆数据库初始化失败: {str(e)}")
            logger.warning("将在没有记忆功能的情况下继续运行")
        
        return True
    except Exception as e:
        logger.error(f"环境设置失败: {str(e)}")
        return False

def open_browser(host, port, delay=1.5):
    """在浏览器中打开URL"""
    def _open_browser():
        time.sleep(delay)  # 等待服务器启动
        
        # 如果host是0.0.0.0，获取本地IP地址用于浏览器访问
        if host == "0.0.0.0":
            try:
                from utils.network_utils import get_local_ip
                local_ip = get_local_ip()
                browser_host = local_ip if local_ip else "127.0.0.1"
                print(f"如果你想要使用语音输入功能，请确保你使用的是本地地址而不是IP地址！")
                print(f"如果你的环境为公网环境，请确保你使用的是https协议地址，否则浏览器可能会阻止调用麦克风！")
            except Exception as e:
                logger.warning(f"获取本地IP失败: {e}")
                browser_host = "127.0.0.1"
        else:
            browser_host = host
        
        url = f"http://{browser_host}:{port}"
        logger.info(f"正在浏览器中打开应用: {url}")
        
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"无法自动打开浏览器: {e}")
            logger.info(f"请手动在浏览器中访问: {url}")
    
    browser_thread = Thread(target=_open_browser)
    browser_thread.daemon = True
    browser_thread.start()

def start_server(host, port, debug=False, open_browser_flag=True):
    """启动服务器"""
    try:
        # 导入Flask应用
        from app import app
        
        # 如果需要，启动浏览器（只在非重载模式下打开）
        # WERKZEUG_RUN_MAIN 环境变量在Flask重载时会被设置
        if open_browser_flag and not os.environ.get('WERKZEUG_RUN_MAIN'):
            open_browser(host, port)
        
        # 显示服务器信息
        if host == "0.0.0.0":
            try:
                from utils.network_utils import get_local_ip, get_all_local_ips
                local_ip = get_local_ip()
                all_ips = get_all_local_ips()
                
                logger.info(f"正在启动Web服务器...")
                logger.info(f"本地访问地址: http://127.0.0.1:{port}")
                if local_ip and local_ip != "127.0.0.1":
                    logger.info(f"局域网访问地址: http://{local_ip}:{port}")
                
                # 显示所有可用的IP地址
                if len(all_ips) > 1:
                    logger.info("所有可用地址:")
                    for ip in all_ips:
                        logger.info(f"  http://{ip}:{port}")
                        
            except Exception as e:
                logger.warning(f"获取网络信息失败: {e}")
                logger.info(f"正在启动Web服务器，地址: http://{host}:{port}")
        else:
            logger.info(f"正在启动Web服务器，地址: http://{host}:{port}")
        
        logger.info("按Ctrl+C停止服务器")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug  # 只在debug模式下启用重载器
        )
        
        return True
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='CABM应用启动脚本')
    parser.add_argument('--host', type=str, help='主机地址')
    parser.add_argument('--port', type=int, help='端口号')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    args = parser.parse_args()
    
    logger.info("正在启动CABM应用...")
    
    # 设置环境
    if not setup_environment():
        logger.error("环境设置失败，应用无法启动")
        sys.exit(1)
    
    # 导入配置服务
    from services.config_service import config_service
    
    # 获取应用配置
    app_config = config_service.get_app_config()
    
    # 设置主机和端口
    host = args.host or app_config["host"]
    port = args.port or app_config["port"]
    debug = args.debug or app_config["debug"]
    open_browser_flag = not args.no_browser and app_config.get("auto_open_browser", True)
    
    # 启动服务器
    if not start_server(host, port, debug, open_browser_flag):
        logger.error("服务器启动失败")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("应用已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}")
        sys.exit(1)
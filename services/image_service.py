"""
图像服务模块
封装图像生成API调用和处理
"""
import os
import sys
import time
import random
import base64
import shutil
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from openai import APIError
import traceback

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.config_service import config_service

class ImageConfig:
    """图像配置类"""
    
    def __init__(
        self,
        prompt: str = None,
        image_size: str = None,
        batch_size: int = None,
        num_inference_steps: int = None,
        guidance_scale: float = None,
        negative_prompt: str = None,
        seed: int = None
    ):
        """
        初始化图像配置
        
        Args:
            prompt: 图像提示词
            image_size: 图像尺寸
            batch_size: 生成数量
            num_inference_steps: 推理步数
            guidance_scale: 引导比例
            negative_prompt: 负面提示词
            seed: 随机种子
        """
        # 获取默认配置
        default_config = config_service.get_image_config()
        
        # 设置配置项，如果未提供则使用默认值
        self.model = default_config["model"]
        self.prompt = prompt or config_service.get_random_image_prompt()
        self.image_size = image_size or default_config["image_size"]
        self.batch_size = batch_size or default_config["batch_size"]
        self.num_inference_steps = num_inference_steps or default_config["num_inference_steps"]
        self.guidance_scale = guidance_scale or default_config["guidance_scale"]
        self.negative_prompt = negative_prompt or config_service.get_image_config().get("negative_prompt", "")
        self.seed = seed or random.randint(0, 9999999999)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "model": self.model,
            "prompt": self.prompt,
            "image_size": self.image_size,
            "batch_size": self.batch_size,
            "num_inference_steps": self.num_inference_steps,
            "guidance_scale": self.guidance_scale,
            "negative_prompt": self.negative_prompt,
            "seed": self.seed
        }

class ImageService:
    """图像服务类"""
    
    def __init__(self):
        """初始化图像服务"""
        self.config_service = config_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 创建图像缓存目录
        self.cache_dir = Path(self.config_service.get_app_config()["image_cache_dir"])
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 背景管理相关目录和文件
        self.project_root = Path(__file__).resolve().parent.parent
        self.backgrounds_dir = self.project_root / 'data' / 'backgrounds'
        self.background_config_file = self.project_root / 'data' / 'background.json'
        
        # 确保背景目录存在
        self.backgrounds_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前背景图片路径
        self.current_background = None
        
        # 加载背景配置
        self.backgrounds = self._load_backgrounds()
        
        # 初始化 OpenAI 客户端
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("IMAGE_API_KEY"),
                base_url=os.getenv("IMAGE_API_BASE_URL")
            )
        except ImportError:
            print("未找到openai模块，请安装openai模块")
            self.client = None
    
    def generate_image(self, image_config: Optional[ImageConfig] = None) -> Dict[str, Any]:
        """
        生成图像
        
        Args:
            image_config: 图像配置，如果为None则使用默认配置
            
        Returns:
            包含图像URL和信息的字典
        """
        # 检查客户端是否可用
        if not self.client:
            # 使用备用图像
            fallback_image = self.get_fallback_image()
            if fallback_image:
                self.current_background = fallback_image
                return {
                    "success": False,
                    "error": "OpenAI客户端未初始化",
                    "image_path": str(fallback_image),
                    "fallback": True
                }
            raise Exception("OpenAI客户端未初始化且无备用图像")
        
        # 准备图像配置
        if image_config is None:
            image_config = ImageConfig()
        
        try:
            # 使用 OpenAI 库调用图像生成API
            response = self.client.images.generate(
                model=image_config.model,
                prompt=image_config.prompt,
                size=image_config.image_size,
                n=image_config.batch_size
            )
            
            # 处理响应
            if response.data and len(response.data) > 0:
                # 下载图像
                image_url = response.data[0].url
                image_path = self.download_image(image_url)
                
                # 更新当前背景
                self.current_background = image_path
                
                return {
                    "success": True,
                    "image_path": str(image_path),
                    "image_url": image_url,
                    "config": image_config.to_dict(),
                    "seed": image_config.seed
                }
            
            raise Exception("图像生成失败：响应中没有图像数据")
            
        except Exception as e:
            print(f"图像生成失败: {e}")
            
            # 使用备用图像
            fallback_image = self.get_fallback_image()
            if fallback_image:
                self.current_background = fallback_image
                return {
                    "success": False,
                    "error": str(e),
                    "image_path": str(fallback_image),
                    "fallback": True
                }
            
            raise e
    
    def download_image(self, url: str) -> Path:
        """
        下载图像
        
        Args:
            url: 图像URL
            
        Returns:
            图像保存路径
            
        Raises:
            APIError: 当下载失败时
        """
        try:
            # 创建唯一文件名
            timestamp = int(time.time())
            filename = f"image_{timestamp}.jpg"
            image_path = self.cache_dir / filename
            
            # 下载图像
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                return image_path
            
            raise APIError(f"图像下载失败: HTTP {response.status_code}")
            
        except Exception as e:
            raise APIError(f"图像下载失败: {str(e)}")
    
    def get_fallback_image(self) -> Optional[Path]:
        """
        获取备用图像
        
        Returns:
            备用图像路径，如果没有则返回None
        """
        # 检查缓存目录中是否有图像
        image_files = list(self.cache_dir.glob("*.jpg")) + list(self.cache_dir.glob("*.png"))
        
        if image_files:
            # 返回最新的图像
            return sorted(image_files, key=os.path.getmtime, reverse=True)[0]
        
        return None
    
    def generate_background(self, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成背景图像
        
        Args:
            prompt: 图像提示词，如果为None则使用随机提示词
            
        Returns:
            包含图像路径和信息的字典
        """
        try:
            # 创建图像配置
            image_config = ImageConfig(prompt=prompt)
            
            # 生成图像
            result = self.generate_image(image_config)
            
            # 清理旧图像
            self.cleanup_old_images()
            
            return result
            
        except APIError as e:
            # 处理API错误
            error_info = e.response if hasattr(e, "response") else {"error": str(e)}
            traceback.print_exc()
            # 如果有备用图像，使用备用图像
            if "image_path" in error_info:
                return {
                    "success": False,
                    "error": error_info["error"],
                    "image_path": error_info["image_path"],
                    "fallback": True
                }
            
            # 否则抛出异常
            raise e
    
    def get_current_background(self) -> Optional[str]:
        """
        获取当前背景图片路径
        
        Returns:
            当前背景图片路径，如果没有则返回None
        """
        if self.current_background and os.path.exists(self.current_background):
            return str(self.current_background)
        
        # 如果当前背景不存在，尝试获取备用图像
        fallback = self.get_fallback_image()
        if fallback:
            self.current_background = fallback
            return str(fallback)
        
        return None
    
    def cleanup_old_images(self, max_age_hours: int = 24, max_files: int = 20) -> None:
        """
        清理旧图像
        
        Args:
            max_age_hours: 最大保留时间（小时）
            max_files: 最大保留文件数
        """
        try:
            # 获取所有图像文件
            image_files = list(self.cache_dir.glob("*.jpg")) + list(self.cache_dir.glob("*.png"))
            
            # 如果文件数量超过最大值，按修改时间排序并删除最旧的文件
            if len(image_files) > max_files:
                sorted_files = sorted(image_files, key=os.path.getmtime)
                files_to_delete = sorted_files[:len(image_files) - max_files]
                
                for file_path in files_to_delete:
                    try:
                        os.remove(file_path)
                    except:
                        pass
            
            # 删除超过最大保留时间的文件
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for file_path in image_files:
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime < cutoff_time:
                        os.remove(file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"清理旧图像时出错: {str(e)}")
    
    # 背景管理功能
    def _load_backgrounds(self) -> Dict[str, Any]:
        """加载背景配置文件"""
        try:
            if self.background_config_file.exists():
                import json
                with open(self.background_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"加载背景配置失败: {e}")
            return {}
    
    def _save_backgrounds(self) -> bool:
        """保存背景配置文件"""
        try:
            import json
            with open(self.background_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.backgrounds, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存背景配置失败: {e}")
            return False
    
    def get_all_backgrounds(self) -> Dict[str, Any]:
        """获取所有背景信息"""
        # 重新加载配置以确保数据最新
        self.backgrounds = self._load_backgrounds()
        
        # 检查文件是否存在，移除不存在的背景
        valid_backgrounds = {}
        for filename, info in self.backgrounds.items():
            if (self.backgrounds_dir / filename).exists():
                valid_backgrounds[filename] = info
        
        # 如果有变化，更新配置
        if len(valid_backgrounds) != len(self.backgrounds):
            self.backgrounds = valid_backgrounds
            self._save_backgrounds()
        
        return self.backgrounds
    
    def add_background(self, name: str, desc: str = "", prompt: str = "", 
                      image_data: bytes = None, filename: str = None) -> Dict[str, Any]:
        """添加新背景"""
        try:
            import uuid
            from PIL import Image
            from io import BytesIO
            
            # 生成文件名
            if not filename:
                file_ext = '.png'  # 默认PNG格式
                filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # 如果提供了图片数据，保存图片
            if image_data:
                image_path = self.backgrounds_dir / filename
                with open(image_path, 'wb') as f:
                    f.write(image_data)
            else:
                # 如果没有提供图片且没有提示词，生成占位图片
                if not prompt.strip():
                    self._create_placeholder_image(filename, name)
                else:
                    # 如果有提示词，使用AI生成图片
                    try:
                        result = self.generate_background(prompt)
                        if result.get('success') and result.get('image_path'):
                            # 将生成的图片复制到背景目录
                            import shutil
                            generated_path = Path(result['image_path'])
                            target_path = self.backgrounds_dir / filename
                            shutil.copy2(generated_path, target_path)
                        else:
                            # 生成失败，创建占位图片
                            self._create_placeholder_image(filename, name)
                    except Exception as gen_error:
                        print(f"AI生成背景失败: {gen_error}")
                        # 生成失败，创建占位图片
                        self._create_placeholder_image(filename, name)
            
            # 添加到配置
            self.backgrounds[filename] = {
                'name': name,
                'desc': desc,
                'prompt': prompt
            }
            
            # 保存配置
            if self._save_backgrounds():
                return {
                    'success': True,
                    'filename': filename,
                    'message': '背景添加成功'
                }
            else:
                return {
                    'success': False,
                    'error': '保存配置失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'添加背景失败: {str(e)}'
            }
    
    def _create_placeholder_image(self, filename: str, name: str):
        """创建占位图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            # 创建一个渐变背景的占位图片
            img = Image.new('RGB', (1920, 1080), color=(50, 50, 70))
            draw = ImageDraw.Draw(img)
            
            # 创建简单的渐变效果
            for y in range(1080):
                color_value = int(50 + (y / 1080) * 50)  # 从50到100的渐变
                draw.line([(0, y), (1920, y)], fill=(color_value, color_value, color_value + 20))
            
            # 尝试添加文字
            try:
                # 尝试使用系统字体
                font_size = 72
                try:
                    # Windows系统字体
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        # 备用字体
                        font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", font_size)
                    except:
                        # 使用默认字体
                        font = ImageFont.load_default()
                
                # 计算文字位置（居中）
                text = name
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (1920 - text_width) // 2
                y = (1080 - text_height) // 2
                
                # 绘制文字阴影
                draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
                # 绘制文字
                draw.text((x, y), text, font=font, fill=(200, 200, 255))
                
            except Exception as font_error:
                print(f"添加文字失败: {font_error}")
            
            # 保存图片
            image_path = self.backgrounds_dir / filename
            img.save(image_path, 'PNG')
            
        except Exception as e:
            print(f"创建占位图片失败: {e}")
            # 如果失败，创建一个最简单的图片
            try:
                from PIL import Image
                img = Image.new('RGB', (1920, 1080), color=(50, 50, 70))
                image_path = self.backgrounds_dir / filename
                img.save(image_path, 'PNG')
            except:
                pass
    
    def delete_background(self, filename: str) -> Dict[str, Any]:
        """删除背景"""
        try:
            # 重新加载配置以确保数据最新
            self.backgrounds = self._load_backgrounds()
            
            if filename not in self.backgrounds:
                return {
                    'success': False,
                    'error': '背景不存在'
                }
            
            # 删除文件
            image_path = self.backgrounds_dir / filename
            if image_path.exists():
                image_path.unlink()
            
            # 从配置中移除
            del self.backgrounds[filename]
            
            # 保存配置
            if self._save_backgrounds():
                return {
                    'success': True,
                    'message': '背景删除成功'
                }
            else:
                return {
                    'success': False,
                    'error': '保存配置失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'删除背景失败: {str(e)}'
            }
    
    def get_background_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """获取单个背景信息"""
        return self.backgrounds.get(filename)
    
    def update_background_info(self, filename: str, name: str = None, 
                             desc: str = None, prompt: str = None) -> Dict[str, Any]:
        """更新背景信息"""
        try:
            # 重新加载配置以确保数据最新
            self.backgrounds = self._load_backgrounds()
            
            if filename not in self.backgrounds:
                return {
                    'success': False,
                    'error': '背景不存在'
                }
            
            # 更新信息
            if name is not None:
                self.backgrounds[filename]['name'] = name
            if desc is not None:
                self.backgrounds[filename]['desc'] = desc
            if prompt is not None:
                self.backgrounds[filename]['prompt'] = prompt
            
            # 保存配置
            if self._save_backgrounds():
                return {
                    'success': True,
                    'message': '背景信息更新成功'
                }
            else:
                return {
                    'success': False,
                    'error': '保存配置失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'更新背景信息失败: {str(e)}'
            }
    
    def get_random_background(self) -> Optional[str]:
        """获取随机背景"""
        if not self.backgrounds:
            return None
        
        return random.choice(list(self.backgrounds.keys()))
    
    def get_background_url(self, filename: str) -> str:
        """获取背景图片URL"""
        return f"/static/images/backgrounds/{filename}"
    
    def upload_background_image(self, file_data: bytes, original_filename: str,
                               name: str, desc: str = "", prompt: str = "") -> Dict[str, Any]:
        """上传背景图片"""
        try:
            import uuid
            # 获取文件扩展名
            file_ext = Path(original_filename).suffix.lower()
            if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                return {
                    'success': False,
                    'error': '不支持的图片格式'
                }
            
            # 生成新文件名
            new_filename = f"{uuid.uuid4().hex}{file_ext}"
            
            # 处理图片（可选：调整大小、压缩等）
            processed_data = self._process_image(file_data)
            
            # 添加背景
            return self.add_background(
                name=name,
                desc=desc,
                prompt=prompt,
                image_data=processed_data,
                filename=new_filename
            )
            
        except Exception as e:
            return {
                'success': False,
                'error': f'上传图片失败: {str(e)}'
            }
    
    def _process_image(self, image_data: bytes) -> bytes:
        """处理图片（调整大小、压缩等）"""
        try:
            from PIL import Image
            from io import BytesIO
            
            # 打开图片
            img = Image.open(BytesIO(image_data))
            
            # 转换为RGB（如果是RGBA或其他格式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 调整大小（可选）
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存为字节流
            output = BytesIO()
            img.save(output, format='PNG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"处理图片失败: {e}")
            return image_data  # 返回原始数据
    
    def get_background_stats(self) -> Dict[str, Any]:
        """获取背景统计信息"""
        total_count = len(self.backgrounds)
        total_size = 0
        
        try:
            for filename in self.backgrounds.keys():
                image_path = self.backgrounds_dir / filename
                if image_path.exists():
                    total_size += image_path.stat().st_size
        except Exception as e:
            print(f"计算背景统计信息失败: {e}")
        
        return {
            'total_count': total_count,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }

# 创建全局图像服务实例
image_service = ImageService()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # 测试图像服务
    try:
        # 初始化配置
        if not config_service.initialize():
            print("配置初始化失败")
            sys.exit(1)
        
        # 生成背景图像
        print("正在生成背景图像...")
        result = image_service.generate_background()
        
        # 打印结果
        print(f"图像生成{'成功' if result.get('success', False) else '失败'}")
        if "image_path" in result:
            print(f"图像路径: {result['image_path']}")
        if "error" in result:
            print(f"错误信息: {result['error']}")
        if "fallback" in result and result["fallback"]:
            print("使用了备用图像")
        
    except APIError as e:
        print(f"API错误: {e.message}")
        if hasattr(e, "response") and e.response:
            print(f"详细信息: {e.response}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)
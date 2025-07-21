"""
场景服务模块
负责场景的生成、切换和管理
"""
import os
import sys
import json
import time
import random
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.api_utils import make_api_request, APIError, handle_api_error
from services.config_service import config_service
from services.image_service import image_service

class Scene:
    """场景类"""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        image_path: Optional[str] = None,
        created_at: Optional[int] = None
    ):
        """
        初始化场景
        
        Args:
            id: 场景ID
            name: 场景名称
            description: 场景描述
            image_path: 场景图片路径
            created_at: 场景创建时间戳
        """
        self.id = id
        self.name = name
        self.description = description
        self.image_path = image_path
        self.created_at = created_at or int(time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_path": self.image_path,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """从字典创建场景"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            image_path=data.get("image_path"),
            created_at=data.get("created_at")
        )


class SceneService:
    """场景服务类"""
    
    def __init__(self):
        """初始化场景服务"""
        self.config_service = config_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 场景缓存目录
        self.scenes_dir = Path("data/scenes")
        os.makedirs(self.scenes_dir, exist_ok=True)
        
        # 当前场景
        self.current_scene = None
        
        # 加载默认场景
        self._load_default_scene()
    
    def _load_default_scene(self):
        """加载默认场景"""
        # 检查是否有保存的场景
        scenes = self.list_scenes()
        
        if scenes:
            # 加载最新的场景
            latest_scene = max(scenes, key=lambda s: s.created_at)
            self.current_scene = latest_scene
        else:
            # 创建默认场景
            default_scene = Scene(
                id="default",
                name="默认场景",
                description="一个温馨的二次元风格卧室，阳光透过薄纱窗帘洒在木地板上，床上散落着卡通抱枕，墙边有摆满书籍和手办的原木色书架。",
                image_path=None
            )
            
            # 保存默认场景
            self.save_scene(default_scene)
            
            # 设置为当前场景
            self.current_scene = default_scene
    
    def save_scene(self, scene: Scene) -> bool:
        """
        保存场景
        
        Args:
            scene: 场景对象
            
        Returns:
            是否保存成功
        """
        try:
            # 保存场景数据
            scene_path = self.scenes_dir / f"{scene.id}.json"
            
            with open(scene_path, "w", encoding="utf-8") as f:
                json.dump(scene.to_dict(), f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存场景失败: {str(e)}")
            return False
    
    def load_scene(self, scene_id: str) -> Optional[Scene]:
        """
        加载场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            场景对象，如果不存在则返回None
        """
        try:
            # 加载场景数据
            scene_path = self.scenes_dir / f"{scene_id}.json"
            
            if not scene_path.exists():
                return None
            
            with open(scene_path, "r", encoding="utf-8") as f:
                scene_data = json.load(f)
            
            return Scene.from_dict(scene_data)
        except Exception as e:
            print(f"加载场景失败: {str(e)}")
            return None
    
    def list_scenes(self) -> List[Scene]:
        """
        列出所有场景
        
        Returns:
            场景列表
        """
        scenes = []
        
        try:
            # 获取所有场景文件
            scene_files = list(self.scenes_dir.glob("*.json"))
            
            for scene_file in scene_files:
                try:
                    with open(scene_file, "r", encoding="utf-8") as f:
                        scene_data = json.load(f)
                    
                    scenes.append(Scene.from_dict(scene_data))
                except Exception as e:
                    print(f"加载场景文件失败: {scene_file}, 错误: {str(e)}")
        except Exception as e:
            print(f"列出场景失败: {str(e)}")
        
        return scenes
    
    def get_current_scene(self) -> Optional[Scene]:
        """
        获取当前场景
        
        Returns:
            当前场景对象，如果没有则返回None
        """
        return self.current_scene
    
    def set_current_scene(self, scene_id: str) -> bool:
        """
        设置当前场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            是否设置成功
        """
        # 加载场景
        scene = self.load_scene(scene_id)
        
        if scene:
            self.current_scene = scene
            return True
        
        return False
    
    def create_scene(self, name: str, description: str) -> Scene:
        """
        创建新场景
        
        Args:
            name: 场景名称
            description: 场景描述
            
        Returns:
            创建的场景对象
        """
        # 生成场景ID
        scene_id = f"scene_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # 创建场景对象
        scene = Scene(
            id=scene_id,
            name=name,
            description=description
        )
        
        # 生成场景图片
        try:
            result = image_service.generate_background(description)
            if "image_path" in result:
                scene.image_path = result["image_path"]
        except Exception as e:
            print(f"生成场景图片失败: {str(e)}")
        
        # 保存场景
        self.save_scene(scene)
        
        return scene
    
    def check_scene_switch(self, chat_history: List[Dict[str, str]]) -> bool:
        """
        检查是否需要切换场景
        
        Args:
            chat_history: 聊天历史记录
            
        Returns:
            是否需要切换场景
        """
        try:
            # 获取决策模型配置
            decision_model_config = self.config_service.get_decision_model_config()
            
            # 准备提示词
            current_scene_desc = "无" if not self.current_scene else f"{self.current_scene.name}: {self.current_scene.description}"
            prompt = f"你是一个决策模型，根据对话判断是否需要切换场景:\n"
            
            # 添加聊天历史
            for msg in chat_history:
                role = "用户" if msg["role"] == "user" else ("系统" if msg["role"] == "system" else "AI")
                prompt += f"{role}: {msg['content']}\n"
            
            prompt += f"当前场景：{current_scene_desc}\n\n"
            prompt += "如果没有，回复0\n如果有，回复1\n不要输出多余的符号/解释"
            
            # 调用决策模型
            response = self._call_decision_model(prompt, decision_model_config)
            
            # 解析响应
            if response and response.strip() == "1":
                return True
            
            return False
            
        except Exception as e:
            print(f"检查场景切换失败: {str(e)}")
            return False
    
    def select_scene(self, chat_history: List[Dict[str, str]]) -> Optional[Scene]:
        """
        选择场景
        
        Args:
            chat_history: 聊天历史记录
            
        Returns:
            选择的场景对象，如果需要创建新场景则返回None
        """
        try:
            # 获取决策模型配置
            decision_model_config = self.config_service.get_decision_model_config()
            
            # 获取所有场景
            scenes = self.list_scenes()
            
            # 如果没有场景，直接创建新场景
            if not scenes:
                return None
            
            # 准备提示词
            current_scene_desc = "无" if not self.current_scene else f"{self.current_scene.name}: {self.current_scene.description}"
            prompt = ""
            
            # 添加聊天历史
            for msg in chat_history:
                role = "用户" if msg["role"] == "user" else ("系统" if msg["role"] == "system" else "AI")
                prompt += f"{role}: {msg['content']}\n"
            
            prompt += f"当前场景：{current_scene_desc}\n\n"
            prompt += "你是一个场景选择器，根据用户输入选择场景：\n"
            
            # 添加场景列表
            for i, scene in enumerate(scenes):
                prompt += f"{i+1}. {scene.name}-{scene.description}\n"
            
            prompt += "都不合适-回复0\n"
            
            # 调用决策模型
            response = self._call_decision_model(prompt, decision_model_config)
            
            # 解析响应
            if response:
                try:
                    scene_index = int(response.strip())
                    if 1 <= scene_index <= len(scenes):
                        return scenes[scene_index - 1]
                except ValueError:
                    pass
            
            # 如果没有合适的场景，返回None表示需要创建新场景
            return None
            
        except Exception as e:
            print(f"选择场景失败: {str(e)}")
            return None
    
    def generate_new_scene(self, chat_history: List[Dict[str, str]]) -> Optional[Scene]:
        """
        生成新场景
        
        Args:
            chat_history: 聊天历史记录
            
        Returns:
            生成的场景对象，如果生成失败则返回None
        """
        try:
            # 获取决策模型配置
            decision_model_config = self.config_service.get_decision_model_config()
            
            # 准备提示词
            prompt = ""
            
            # 添加聊天历史
            for msg in chat_history:
                role = "用户" if msg["role"] == "user" else ("系统" if msg["role"] == "system" else "AI")
                prompt += f"{role}: {msg['content']}\n"
            
            prompt += "\n你是一个场景生成器，根据对话给新场景起个名字，简短但有独特性，然后写一段话详细地描述这个场景\n"
            prompt += "格式：\n场景名称：xxx\n场景描述：xxx\n"
            
            # 调用决策模型
            response = self._call_decision_model(prompt, decision_model_config)
            
            # 解析响应
            if response:
                # 提取场景名称和描述
                name_match = re.search(r"场景名称：(.+?)(?:\n|$)", response)
                desc_match = re.search(r"场景描述：(.+?)(?:\n|$)", response)
                
                if name_match and desc_match:
                    name = name_match.group(1).strip()
                    description = desc_match.group(1).strip()
                    
                    # 创建新场景
                    return self.create_scene(name, description)
            
            return None
            
        except Exception as e:
            print(f"生成新场景失败: {str(e)}")
            return None
    
    def _call_decision_model(self, prompt: str, model_config: Dict[str, Any]) -> Optional[str]:
        """
        调用决策模型
        
        Args:
            prompt: 提示词
            model_config: 模型配置
            
        Returns:
            模型响应，如果调用失败则返回None
        """
        try:
            # 获取API配置
            url = self.config_service.get_decision_api_url()
            api_key = self.config_service.get_decision_api_key()
            
            # 准备请求数据
            request_data = {
                **model_config,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }
            
            # 准备请求头
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 发送API请求
            response, data = make_api_request(
                url=url,
                method="POST",
                headers=headers,
                json_data=request_data,
                stream=False
            )
            
            # 处理响应
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                if message and "content" in message:
                    return message["content"]
            
            return None
            
        except Exception as e:
            print(f"调用决策模型失败: {str(e)}")
            return None
    
    def process_scene_switch(self, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        处理场景切换
        
        Args:
            chat_history: 聊天历史记录
            
        Returns:
            处理结果，包含是否切换场景、场景信息等
        """
        result = {
            "scene_switched": False,
            "scene": None,
            "is_new_scene": False,
            "decision_calls": 0
        }
        
        # 检查是否需要切换场景
        need_switch = self.check_scene_switch(chat_history)
        result["decision_calls"] += 1
        
        if not need_switch:
            return result
        
        # 选择场景
        selected_scene = self.select_scene(chat_history)
        result["decision_calls"] += 1
        
        # 如果没有选择现有场景，生成新场景
        if not selected_scene:
            new_scene = self.generate_new_scene(chat_history)
            result["decision_calls"] += 1
            
            if new_scene:
                selected_scene = new_scene
                result["is_new_scene"] = True
        
        # 如果有选择的场景，切换到该场景
        if selected_scene:
            self.current_scene = selected_scene
            result["scene_switched"] = True
            result["scene"] = selected_scene.to_dict()
        
        return result

# 创建全局场景服务实例
scene_service = SceneService()

if __name__ == "__main__":
    # 测试场景服务
    try:
        # 初始化配置
        if not config_service.initialize():
            print("配置初始化失败")
            sys.exit(1)
        
        # 获取当前场景
        current_scene = scene_service.get_current_scene()
        if current_scene:
            print(f"当前场景: {current_scene.name}")
            print(f"场景描述: {current_scene.description}")
        else:
            print("当前没有场景")
        
        # 列出所有场景
        scenes = scene_service.list_scenes()
        print(f"\n共有 {len(scenes)} 个场景:")
        for scene in scenes:
            print(f"- {scene.name}: {scene.description[:50]}...")
        
    except Exception as e:
        print(f"测试场景服务失败: {str(e)}")
        sys.exit(1)
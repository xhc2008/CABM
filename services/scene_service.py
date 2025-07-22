"""
场景服务模块
负责管理和切换场景
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.config_service import config_service

class Scene:
    """场景类"""
    
    def __init__(self, scene_id: str, name: str, description: str, background: Optional[str] = None):
        """
        初始化场景
        
        Args:
            scene_id: 场景ID
            name: 场景名称
            description: 场景描述
            background: 场景背景图片路径（可选）
        """
        self.id = scene_id
        self.name = name
        self.description = description
        self.background = background
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "background": self.background
        }

class SceneService:
    """场景服务类"""
    
    def __init__(self):
        """初始化场景服务"""
        self.scenes: Dict[str, Scene] = {}
        self.current_scene_id: Optional[str] = None
        
        # 加载默认场景
        self._load_default_scenes()
    
    def _load_default_scenes(self):
        """加载默认场景"""
        # 添加默认场景
        self.add_scene(
            scene_id="default",
            name="默认场景",
            description="一个普通的聊天场景",
            background=None
        )
        
        # 设置当前场景为默认场景
        self.current_scene_id = "default"
    
    def add_scene(self, scene_id: str, name: str, description: str, background: Optional[str] = None) -> Scene:
        """
        添加场景
        
        Args:
            scene_id: 场景ID
            name: 场景名称
            description: 场景描述
            background: 场景背景图片路径（可选）
            
        Returns:
            添加的场景对象
        """
        scene = Scene(scene_id, name, description, background)
        self.scenes[scene_id] = scene
        return scene
    
    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """
        获取场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            场景对象，如果不存在则返回None
        """
        return self.scenes.get(scene_id)
    
    def get_current_scene(self) -> Optional[Scene]:
        """
        获取当前场景
        
        Returns:
            当前场景对象，如果不存在则返回None
        """
        if self.current_scene_id:
            return self.get_scene(self.current_scene_id)
        return None
    
    def switch_scene(self, scene_id: str) -> bool:
        """
        切换场景
        
        Args:
            scene_id: 场景ID
            
        Returns:
            是否切换成功
        """
        if scene_id in self.scenes:
            self.current_scene_id = scene_id
            return True
        return False
    
    def list_scenes(self) -> List[Dict[str, Any]]:
        """
        列出所有场景
        
        Returns:
            场景列表
        """
        return [scene.to_dict() for scene in self.scenes.values()]

# 创建全局场景服务实例
scene_service = SceneService()

if __name__ == "__main__":
    # 测试场景服务
    print("当前场景:", scene_service.get_current_scene().to_dict())
    
    # 添加新场景
    scene_service.add_scene(
        scene_id="cafe",
        name="咖啡厅",
        description="一个安静的咖啡厅，窗外阳光明媚",
        background="images/cafe.jpg"
    )
    
    # 切换场景
    scene_service.switch_scene("cafe")
    print("切换后场景:", scene_service.get_current_scene().to_dict())
    
    # 列出所有场景
    print("所有场景:", scene_service.list_scenes())
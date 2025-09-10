"""
场景服务模块
负责管理角色和故事的场景背景
"""
import json
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

class SceneService:
    """场景服务类"""
    
    def __init__(self):
        """初始化场景服务"""
        self.project_root = Path(__file__).resolve().parent.parent
        self.scenes_dir = self.project_root / 'data' / 'scenes'
        self.backgrounds_dir = self.project_root / 'data' / 'backgrounds'
        self.background_json_path = self.project_root / 'data' / 'background.json'
        
        # 确保目录存在
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
    
    def get_scene_file_path(self, character_id: str = None, story_id: str = None) -> Path:
        """
        获取场景文件路径
        
        Args:
            character_id: 角色ID（普通聊天模式）
            story_id: 故事ID（故事模式）
            
        Returns:
            场景文件路径
        """
        if story_id:
            # 故事模式：data/saves/<故事ID>/scenes.json
            story_dir = self.project_root / 'data' / 'saves' / story_id
            story_dir.mkdir(parents=True, exist_ok=True)
            return story_dir / 'scenes.json'
        elif character_id:
            # 普通聊天模式：data/scenes/<角色ID>.json
            return self.scenes_dir / f'{character_id}.json'
        else:
            raise ValueError("必须提供character_id或story_id")
    
    def load_scenes(self, character_id: str = None, story_id: str = None) -> Dict[str, Any]:
        """
        加载场景数据
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            
        Returns:
            场景数据字典
        """
        scene_file = self.get_scene_file_path(character_id, story_id)
        
        if scene_file.exists():
            try:
                with open(scene_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"加载场景文件失败: {e}")
                return self._create_default_scenes()
        else:
            # 文件不存在，创建默认场景
            scenes_data = self._create_default_scenes()
            self.save_scenes(scenes_data, character_id, story_id)
            return scenes_data
    
    def save_scenes(self, scenes_data: Dict[str, Any], character_id: str = None, story_id: str = None):
        """
        保存场景数据
        
        Args:
            scenes_data: 场景数据
            character_id: 角色ID
            story_id: 故事ID
        """
        scene_file = self.get_scene_file_path(character_id, story_id)
        
        try:
            with open(scene_file, 'w', encoding='utf-8') as f:
                json.dump(scenes_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存场景文件失败: {e}")
    
    def _create_default_scenes(self) -> Dict[str, Any]:
        """
        创建默认场景数据
        
        Returns:
            默认场景数据
        """
        # 从background.json中随机选择一个背景作为默认背景
        available_backgrounds = self._get_available_backgrounds()
        
        if available_backgrounds:
            # 随机选择一个背景
            default_bg = random.choice(list(available_backgrounds.keys()))
        else:
            default_bg = None
        
        return {
            "last_background": default_bg,
            "backgrounds": []
        }
    
    def _get_available_backgrounds(self) -> Dict[str, Any]:
        """
        获取可用的背景列表
        
        Returns:
            背景数据字典
        """
        if self.background_json_path.exists():
            try:
                with open(self.background_json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def get_last_background(self, character_id: str = None, story_id: str = None) -> Optional[str]:
        """
        获取最后使用的背景
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            
        Returns:
            背景文件名，如果没有则返回None
        """
        scenes_data = self.load_scenes(character_id, story_id)
        return scenes_data.get("last_background")
    
    def update_background_usage(self, background_filename: str, character_id: str = None, story_id: str = None):
        """
        更新背景使用记录
        
        Args:
            background_filename: 背景文件名
            character_id: 角色ID
            story_id: 故事ID
        """
        scenes_data = self.load_scenes(character_id, story_id)
        
        # 更新last_background
        scenes_data["last_background"] = background_filename
        
        # 查找是否已存在该背景的记录
        background_record = None
        for bg in scenes_data["backgrounds"]:
            if bg["id"] == background_filename:
                background_record = bg
                break
        
        if background_record:
            # 更新使用次数
            background_record["usage_count"] += 1
        else:
            # 创建新的背景记录
            new_record = {
                "id": background_filename,
                "usage_count": 1,
                "impression": "None"
            }
            scenes_data["backgrounds"].append(new_record)
        
        # 保存更新后的数据
        self.save_scenes(scenes_data, character_id, story_id)
    
    def get_background_usage_stats(self, character_id: str = None, story_id: str = None) -> List[Dict[str, Any]]:
        """
        获取背景使用统计
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            
        Returns:
            背景使用统计数据列表
        """
        scenes_data = self.load_scenes(character_id, story_id)
        return scenes_data.get("backgrounds", [])
    
    def copy_scenes_for_story(self, character_id: str, story_id: str):
        """
        为故事复制角色的场景数据
        
        Args:
            character_id: 源角色ID
            story_id: 目标故事ID
        """
        try:
            # 加载角色的场景数据
            character_scenes = self.load_scenes(character_id=character_id)
            
            # 保存到故事目录
            self.save_scenes(character_scenes, story_id=story_id)
            
            print(f"已为故事 {story_id} 复制角色 {character_id} 的场景数据")
        except Exception as e:
            print(f"复制场景数据失败: {e}")
            # 如果复制失败，创建默认场景
            default_scenes = self._create_default_scenes()
            self.save_scenes(default_scenes, story_id=story_id)
    
    def create_empty_scenes_for_story(self, story_id: str):
        """
        为多角色故事创建空的场景数据
        
        Args:
            story_id: 故事ID
        """
        try:
            # 创建默认场景数据
            default_scenes = self._create_default_scenes()
            
            # 保存到故事目录
            self.save_scenes(default_scenes, story_id=story_id)
            
            print(f"已为多角色故事 {story_id} 创建空的场景数据")
        except Exception as e:
            print(f"创建空场景数据失败: {e}")
    
    def select_random_background(self, character_id: str = None, story_id: str = None) -> Optional[str]:
        """
        随机选择一个背景
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            
        Returns:
            随机选择的背景文件名
        """
        available_backgrounds = self._get_available_backgrounds()
        
        if available_backgrounds:
            selected_bg = random.choice(list(available_backgrounds.keys()))
            # 更新使用记录
            self.update_background_usage(selected_bg, character_id, story_id)
            return selected_bg
        
        return None
    
    def get_background_url(self, background_filename: str) -> str:
        """
        获取背景图片的URL
        
        Args:
            background_filename: 背景文件名
            
        Returns:
            背景图片URL
        """
        return f"/static/images/backgrounds/{background_filename}"
    
    def get_background_info(self, background_filename: str, character_id: str = None, story_id: str = None) -> Dict[str, Any]:
        """
        获取背景的完整信息（结合background.json和scenes数据）
        
        Args:
            background_filename: 背景文件名
            character_id: 角色ID
            story_id: 故事ID
            
        Returns:
            背景完整信息
        """
        # 从background.json获取基本信息
        available_backgrounds = self._get_available_backgrounds()
        bg_info = available_backgrounds.get(background_filename, {})
        
        # 从scenes数据获取使用统计
        scenes_data = self.load_scenes(character_id, story_id)
        usage_info = None
        for bg in scenes_data.get("backgrounds", []):
            if bg["id"] == background_filename:
                usage_info = bg
                break
        
        # 合并信息
        result = {
            "id": background_filename,
            "name": bg_info.get("name", "未知背景"),
            "desc": bg_info.get("desc", ""),
            "prompt": bg_info.get("prompt", ""),
            "url": self.get_background_url(background_filename),
            "usage_count": usage_info["usage_count"] if usage_info else 0,
            "impression": usage_info["impression"] if usage_info else "None"
        }
        
        return result
    
    def update_background_impression(self, background_filename: str, impression: str, character_id: str = None, story_id: str = None):
        """
        更新背景印象
        
        Args:
            background_filename: 背景文件名
            impression: 印象描述
            character_id: 角色ID
            story_id: 故事ID
        """
        scenes_data = self.load_scenes(character_id, story_id)
        
        # 查找背景记录
        for bg in scenes_data["backgrounds"]:
            if bg["id"] == background_filename:
                bg["impression"] = impression
                break
        else:
            # 如果不存在，创建新记录
            scenes_data["backgrounds"].append({
                "id": background_filename,
                "usage_count": 0,
                "impression": impression
            })
        
        # 保存更新后的数据
        self.save_scenes(scenes_data, character_id, story_id)

# 创建全局场景服务实例
scene_service = SceneService()
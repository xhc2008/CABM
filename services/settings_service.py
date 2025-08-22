"""
设置服务模块
管理应用的用户设置配置
"""
import os
import sys
from pathlib import Path
import toml
from typing import Dict, Any

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

class SettingsService:
    """设置服务类"""
    
    def __init__(self, config_path: str = "config/app_settings.toml"):
        """初始化设置服务"""
        self.config_path = Path(config_path)
        self.settings = {}
        self.load_settings()
    
    def load_settings(self) -> bool:
        """
        加载设置配置
        
        返回:
            是否加载成功
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.settings = toml.load(f)
                return True
            else:
                # 如果配置文件不存在，创建默认配置
                self.settings = self._get_default_settings()
                self.save_settings()
                return True
        except Exception as e:
            print(f"加载设置配置失败: {e}")
            # 使用默认配置
            self.settings = self._get_default_settings()
            return False
    
    def save_settings(self) -> bool:
        """
        保存设置配置
        
        返回:
            是否保存成功
        """
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                toml.dump(self.settings, f)
            return True
        except Exception as e:
            print(f"保存设置配置失败: {e}")
            return False
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """获取默认设置配置"""
        return {
            "storage": {
                "type": "json",  # 可选: "json", "faiss_peewee"
                "vector_db_path": "data/memory",
                "chat_history_path": "data/history"
            },
            "audio": {
                "bgm_volume": 0.5,
                "bgm_enabled": True,
                "bgm_folder": "static/bgm"
            },
            "ui": {
                "show_logo": True,
                "theme": "default"
            }
        }
    
    def get_setting(self, section: str, key: str, default=None):
        """
        获取设置值
        
        参数:
            section: 配置节
            key: 配置键
            default: 默认值
            
        返回:
            配置值
        """
        return self.settings.get(section, {}).get(key, default)
    
    def set_setting(self, section: str, key: str, value):
        """
        设置配置值
        
        参数:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        获取所有设置
        
        返回:
            所有设置的副本
        """
        return self.settings.copy()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        更新设置
        
        参数:
            new_settings: 新的设置配置
            
        返回:
            是否更新成功
        """
        try:
            # 更新设置
            for section, section_settings in new_settings.items():
                if section not in self.settings:
                    self.settings[section] = {}
                self.settings[section].update(section_settings)
            
            # 保存到文件
            return self.save_settings()
        except Exception as e:
            print(f"更新设置失败: {e}")
            return False

# 创建全局设置服务实例
settings_service = SettingsService()

if __name__ == "__main__":
    # 测试设置服务
    if settings_service.load_settings():
        print("设置服务初始化成功")
        print("当前设置:")
        print(settings_service.get_all_settings())
        
        # 测试修改设置
        settings_service.set_setting("audio", "bgm_volume", 0.8)
        settings_service.set_setting("storage", "type", "faiss")
        
        # 保存设置
        if settings_service.save_settings():
            print("设置保存成功")
        else:
            print("设置保存失败")
    else:
        print("设置服务初始化失败")

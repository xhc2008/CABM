"""
剧情服务模块
处理剧情模式的故事管理、进度跟踪和导演判断
"""
import os
import sys
import json
import time
import re
import rtoml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.config_service import config_service
from utils.api_utils import make_api_request, APIError
from config import get_director_prompts, DIRECTOR_SYSTEM_PROMPTS, get_story_prompts, get_option_config

class StoryService:
    """剧情服务类"""
    
    def __init__(self):
        """初始化剧情服务"""
        self.logger = logging.getLogger(__name__)
        self.config_service = config_service
        self.current_story = None
        self.story_data = None
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
    
    def list_stories(self) -> List[Dict[str, Any]]:
        """
        获取所有可用的故事存档
        
        Returns:
            故事列表，每个故事包含基本信息
        """
        stories = []
        saves_dir = Path("data/saves")
        
        if not saves_dir.exists():
            saves_dir.mkdir(parents=True, exist_ok=True)
            return stories
        
        for story_dir in saves_dir.iterdir():
            if story_dir.is_dir():
                story_file = story_dir / "story.toml"
                if story_file.exists():
                    try:
                        story_info = self._load_story_info(story_dir.name)
                        if story_info:
                            stories.append(story_info)
                    except Exception as e:
                        self.logger.error(f"加载故事 {story_dir.name} 失败: {e}")
        
        # 按最后游玩时间排序
        stories.sort(key=lambda x: x.get('last_played', ''), reverse=True)
        return stories
    
    def _load_story_info(self, story_id: str) -> Optional[Dict[str, Any]]:
        """
        加载故事基本信息
        
        Args:
            story_id: 故事ID
            
        Returns:
            故事信息字典
        """
        story_path = Path("data/saves") / story_id / "story.toml"
        
        if not story_path.exists():
            return None
        
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                data = rtoml.load(f)
            
            # 获取角色信息（支持多角色）
            characters = []
            character_list = data.get('characters', {}).get('list', [])
            # 兼容旧格式：如果是字符串，转换为列表
            if isinstance(character_list, str):
                character_list = [character_list]
            
            for char_id in character_list:
                char_config = self.config_service.get_character_config(char_id)
                if char_config:
                    characters.append({
                        'id': char_id,
                        'name': char_config.get('name', char_id),
                        'color': char_config.get('color', '#ffffff')
                    })
            
            # 获取进度信息
            current_chapter = data.get('progress', {}).get('current', 0)
            outline = data.get('structure', {}).get('outline', [])
            current_progress = "未开始"
            if current_chapter < len(outline):
                current_progress = outline[current_chapter]
            
            # 获取封面图片
            cover_url = None
            cover_path = Path("data/saves") / story_id / "cover.png"
            if cover_path.exists():
                cover_url = f"/data/saves/{story_id}/cover.png"
            
            # 获取最后游玩时间
            history_path = Path("data/saves") / story_id / "history.log"
            last_played = None
            if history_path.exists():
                try:
                    stat = history_path.stat()
                    last_played = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            return {
                'id': story_id,
                'title': data.get('metadata', {}).get('title', story_id),
                'summary': data.get('summary', {}).get('text', ''),
                'characters': characters,
                'current_progress': current_progress,
                'cover_url': cover_url,
                'last_played': last_played,
                'creator': data.get('metadata', {}).get('creator', '未知'),
                'create_date': data.get('metadata', {}).get('create_date', '')
            }
            
        except Exception as e:
            self.logger.error(f"解析故事文件 {story_path} 失败: {e}")
            return None
    
    def load_story(self, story_id: str) -> bool:
        """
        加载指定的故事
        
        Args:
            story_id: 故事ID
            
        Returns:
            是否加载成功
        """
        story_path = Path("data/saves") / story_id / "story.toml"
        
        if not story_path.exists():
            self.logger.error(f"故事文件不存在: {story_path}")
            return False
        
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                self.story_data = rtoml.load(f)
            
            self.current_story = story_id
            self.logger.info(f"成功加载故事: {story_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载故事失败: {e}")
            return False
    
    def get_current_story_data(self) -> Optional[Dict[str, Any]]:
        """获取当前故事数据"""
        return self.story_data
    
    def get_current_story_id(self) -> Optional[str]:
        """获取当前故事ID"""
        return self.current_story
    
    def get_story_memory_path(self) -> str:
        """获取当前故事的记忆文件路径"""
        if not self.current_story:
            raise ValueError("未加载任何故事")
        return f"data/saves/{self.current_story}/memory.json"
    
    def get_story_history_path(self) -> str:
        """获取当前故事的历史记录文件路径"""
        if not self.current_story:
            raise ValueError("未加载任何故事")
        return f"data/saves/{self.current_story}/history.log"
    
    def get_current_chapter_info(self) -> Tuple[int, str, Optional[str]]:
        """
        获取当前章节信息
        
        Returns:
            (当前章节索引, 当前章节内容, 下一章节内容)
        """
        if not self.story_data:
            raise ValueError("未加载任何故事")
        
        current = self.story_data.get('progress', {}).get('current', 0)
        outline = self.story_data.get('structure', {}).get('outline', [])
        
        current_chapter = outline[current] if current < len(outline) else "故事结束"
        next_chapter = outline[current + 1] if current + 1 < len(outline) else None
        
        return current, current_chapter, next_chapter
    
    def get_offset(self) -> int:
        """获取当前偏移值"""
        if not self.story_data:
            raise ValueError("未加载任何故事")
        return self.story_data.get('progress', {}).get('offset', 0)
    
    def update_progress(self, advance_chapter: bool = False, offset_increment: int = 0):
        """
        更新故事进度
        
        Args:
            advance_chapter: 是否推进到下一章节
            offset_increment: 偏移值增量
        """
        if not self.story_data or not self.current_story:
            raise ValueError("未加载任何故事")
        
        if advance_chapter:
            self.story_data['progress']['current'] += 1
            self.story_data['progress']['offset'] = 0
        else:
            self.story_data['progress']['offset'] += offset_increment
        
        # 保存到文件
        self._save_story_data()
        self.logger.info(f"更新故事进度: 章节={self.story_data['progress']['current']}, 偏移={self.story_data['progress']['offset']}")
        
        # 通知聊天服务更新系统提示词（如果在剧情模式下）
        try:
            from services.chat_service import chat_service
            if chat_service.story_mode and chat_service.current_story_id == self.current_story:
                chat_service.set_story_system_prompt()
                self.logger.info("已更新剧情模式系统提示词")
        except Exception as e:
            self.logger.error(f"更新系统提示词失败: {e}")
    
    def _save_story_data(self):
        """保存故事数据到文件"""
        if not self.story_data or not self.current_story:
            return
        
        story_path = Path("data/saves") / self.current_story / "story.toml"
        
        try:
            with open(story_path, 'w', encoding='utf-8') as f:
                f.write(rtoml.dumps(self.story_data))
        except Exception as e:
            self.logger.error(f"保存故事数据失败: {e}")
    
    def is_story_finished(self) -> bool:
        """检查故事是否已结束"""
        if not self.story_data:
            return False
        
        current = self.story_data.get('progress', {}).get('current', 0)
        outline = self.story_data.get('structure', {}).get('outline', [])
        
        return current >= len(outline) - 1
    
    def get_story_characters(self) -> List[Dict[str, Any]]:
        """
        获取故事中的角色信息
        
        Returns:
            角色信息列表，包含玩家和所有角色
        """
        if not self.story_data:
            return []
        
        characters = []
        
        # 添加玩家（序号0）
        characters.append({
            'id': 'player',
            'name': '玩家',
            'is_player': True
        })
        
        # 添加故事角色
        character_list = self.story_data.get('characters', {}).get('list', [])
        # 兼容旧格式：如果是字符串，转换为列表
        if isinstance(character_list, str):
            character_list = [character_list]
        
        for char_id in character_list:
            char_config = self.config_service.get_character_config(char_id)
            if char_config:
                characters.append({
                    'id': char_id,
                    'name': char_config.get('name', char_id),
                    'is_player': False
                })
        
        return characters
    
    def call_director_model(self, chat_history: str) -> Tuple[int, int]:
        """
        调用导演模型判断剧情进度和下次说话角色
        
        Args:
            chat_history: 聊天历史记录
            
        Returns:
            (偏移值, 下次说话角色序号) 的元组
        """
        if not self.story_data:
            raise ValueError("未加载任何故事")
        
        # 获取章节信息
        _, current_chapter, next_chapter = self.get_current_chapter_info()
        
        if next_chapter is None:
            # 已经是最后一章，返回0表示故事结束，随机选择角色
            import random
            characters = self.get_story_characters()
            next_speaker = random.randint(0, len(characters) - 1)
            return 0, next_speaker
        
        # 获取故事角色信息
        characters = self.get_story_characters()
        
        # 构建提示词
        user_prompt = get_director_prompts(chat_history, current_chapter, next_chapter, characters)
        
        # 获取API配置
        option_config = get_option_config()
        url = self.config_service.get_option_api_url()
        api_key = self.config_service.get_option_api_key()
        
        # 准备请求数据
        messages = [
            {"role": "system", "content": DIRECTOR_SYSTEM_PROMPTS},
            {"role": "user", "content": user_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": os.getenv("OPTION_MODEL"),
            "messages": messages,
            "extra_body":{
                "max_tokens": 50,  # 增加token数以支持JSON输出
                "temperature": 0.1,  # 低温度确保稳定输出
                "enable_reasoning": False  
            },
            "stream": False,
            "response_format": {"type": "json_object"}
        }
        
        try:
            self.logger.info(f"调用导演模型判断剧情进度...")
            response, data = make_api_request(
                url=url+"/chat/completions",
                method="POST",
                headers=headers,
                json_data=request_data,
                stream=False
            )
            # 提取回复内容
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                if message and "content" in message:
                    content = message["content"].strip()
                    
                    try:
                        # 解析JSON
                        result_json = json.loads(content)
                        offset = result_json.get("offset", 1)
                        next_speaker = result_json.get("next", 0)
                        
                        # 验证范围
                        if 0 <= offset <= 9 and 0 <= next_speaker < len(characters):
                            self.logger.info(f"导演模型判断结果: offset={offset}, next={next_speaker}")
                            return offset, next_speaker
                        else:
                            self.logger.warning(f"导演模型返回超出范围的结果: offset={offset}, next={next_speaker}")
                    except json.JSONDecodeError:
                        self.logger.warning(f"导演模型返回非JSON格式: {content}")
                    
                    # 解析失败，随机选择
                    import random
                    next_speaker = random.randint(0, len(characters) - 1)
                    self.logger.info(f"解析失败，随机选择角色: {next_speaker}")
                    return 1, next_speaker
            
            self.logger.error("导演模型返回格式错误")
            import random
            characters = self.get_story_characters()
            return 1, random.randint(0, len(characters) - 1)
            
        except Exception as e:
            self.logger.error(f"调用导演模型失败: {e}")
            import random
            characters = self.get_story_characters()
            return 1, random.randint(0, len(characters) - 1)  # 出错时返回默认值
    
    def create_story(self, story_id: str, title: str, character_ids: List[str], 
                    story_direction: str, background_images: List[str] = None) -> bool:
        """
        创建新故事
        
        Args:
            story_id: 故事ID
            title: 故事标题
            character_ids: 角色ID列表（支持单个或多个角色）
            story_direction: 故事导向
            background_images: 背景图片路径列表
            
        Returns:
            是否创建成功
        """
        story_dir = Path("data/saves") / story_id
        
        # 检查故事是否已存在
        if story_dir.exists():
            self.logger.error(f"故事ID已存在: {story_id}")
            return False
        
        try:
            # 创建故事目录
            story_dir.mkdir(parents=True, exist_ok=True)
            
            # 验证所有角色配置
            character_configs = {}
            for char_id in character_ids:
                char_config = self.config_service.get_character_config(char_id)
                if not char_config:
                    raise ValueError(f"未找到角色: {char_id}")
                character_configs[char_id] = char_config
            
            # 生成故事大纲
            story_content = self._generate_story_content(character_configs, story_direction)
            
            # 创建故事配置文件
            story_data = {
                'metadata': {
                    'story_id': story_id,
                    'title': title,
                    'creator': '用户',
                    'create_date': datetime.now().strftime('%Y-%m-%d'),
                    'seed': story_direction
                },
                'progress': {
                    'current': 0,
                    'offset': 0
                },
                'summary': {
                    'text': story_content['summary']
                },
                'structure': {
                    'outline': story_content['outline']
                },
                'characters': {
                    'list': character_ids
                }
            }
            
            # 保存故事文件
            story_file = story_dir / "story.toml"
            with open(story_file, 'w', encoding='utf-8') as f:
                f.write(rtoml.dumps(story_data))
            
            # 处理背景图片
            if background_images:
                self._save_background_images(story_dir, background_images)
            
            # 创建空的记忆和历史文件
            (story_dir / "memory.json").touch()
            (story_dir / "history.log").touch()
            
            self.logger.info(f"成功创建故事: {story_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建故事失败: {e}")
            # 清理已创建的文件
            if story_dir.exists():
                import shutil
                shutil.rmtree(story_dir, ignore_errors=True)
            return False
    
    def _generate_story_content(self, character_configs: Dict[str, Dict[str, Any]], story_direction: str) -> Dict[str, Any]:
        """
        使用AI生成故事内容
        
        Args:
            character_configs: 角色配置字典
            story_direction: 故事导向
            
        Returns:
            包含summary和outline的字典
        """
        # 根据角色数量选择不同的提示词格式
        if len(character_configs) == 1:
            # 单角色
            char_id = list(character_configs.keys())[0]
            character_config = character_configs[char_id]
            character_name = character_config.get('name', '角色')
            character_prompt = character_config.get('prompt', character_config.get('description', ''))
            
            # 构建生成提示词
            from config import get_story_prompts
            user_prompt = get_story_prompts(character_name, character_prompt, "", story_direction)
        else:
            # 多角色
            character_names = [config.get('name', char_id) for char_id, config in character_configs.items()]
            character_prompts = []
            for char_id, config in character_configs.items():
                char_name = config.get('name', char_id)
                char_prompt = config.get('prompt', config.get('description', ''))
                character_prompts.append(f"{char_name}: {char_prompt}")
            
            combined_character_prompt = "\n".join(character_prompts)
            
            # 构建生成提示词
            from config import get_multi_character_story_prompts
            user_prompt = get_multi_character_story_prompts(character_names, combined_character_prompt, story_direction)
        
        # 获取API配置
        option_config = get_option_config()
        url = self.config_service.get_option_api_url()
        api_key = self.config_service.get_option_api_key()
        
        # 准备请求数据
        messages = [
            {"role": "user", "content": user_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        request_data = {
            "model": option_config["model"],
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.8,
            "stream": False,
            "response_format": {"type": "json_object"}
        }
        
        try:
            self.logger.info("生成故事内容...")
            response, data = make_api_request(
                url=url,
                method="POST",
                headers=headers,
                json_data=request_data,
                stream=False
            )
            
            # 提取回复内容
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                if message and "content" in message:
                    content = message["content"].strip()
                    
                    try:
                        story_data = json.loads(content)
                        
                        # 验证必要字段
                        if 'summary' in story_data and 'outline' in story_data:
                            if isinstance(story_data['outline'], list) and len(story_data['outline']) >= 10:
                                return story_data
                    except json.JSONDecodeError:
                        pass
            
            # 如果AI生成失败，使用默认模板
            self.logger.warning("AI生成故事内容失败，使用默认模板")
            if len(character_configs) == 1:
                char_name = list(character_configs.values())[0].get('name', '角色')
            else:
                char_names = [config.get('name', char_id) for char_id, config in character_configs.items()]
                char_name = "、".join(char_names)
            return self._get_default_story_template(char_name)
            
        except Exception as e:
            self.logger.error(f"生成故事内容失败: {e}")
            if len(character_configs) == 1:
                char_name = list(character_configs.values())[0].get('name', '角色')
            else:
                char_names = [config.get('name', char_id) for char_id, config in character_configs.items()]
                char_name = "、".join(char_names)
            return self._get_default_story_template(char_name)
    
    def _get_default_story_template(self, character_name: str) -> Dict[str, Any]:
        """获取默认故事模板"""
        return {
            'summary': f'这是一个关于{character_name}的冒险故事。在这个充满未知的世界里，你们将一起经历各种挑战和成长。',
            'outline': [
                '故事开始',
                '初次相遇',
                '建立信任',
                '面临挑战',
                '共同努力',
                '克服困难',
                '深化关系',
                '新的冒险',
                '成长蜕变',
                '故事结束'
            ]
        }
    
    def _save_background_images(self, story_dir: Path, image_paths: List[str]):
        """保存背景图片到故事目录"""
        try:
            import shutil
            
            for i, image_path in enumerate(image_paths):
                if Path(image_path).exists():
                    if i == 0:
                        # 第一张作为封面
                        dest_path = story_dir / "cover.png"
                    else:
                        dest_path = story_dir / f"background_{i}.png"
                    
                    shutil.copy2(image_path, dest_path)
                    
        except Exception as e:
            self.logger.error(f"保存背景图片失败: {e}")

# 创建全局故事服务实例
story_service = StoryService()
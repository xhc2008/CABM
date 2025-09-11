"""
多角色对话服务模块
专门处理多角色故事的对话逻辑，与单角色逻辑完全分离
"""
import sys
import json
import time
import re
import os
from typing import List, Dict, Any, Optional, Iterator, Union, Tuple
from pathlib import Path
import logging
from config import get_director_prompts_mult, DIRECTOR_SYSTEM_PROMPTS_MULT, get_story_prompts, get_option_config

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.config_service import config_service
from services.story_service import story_service
from services.memory_service import memory_service
from utils.history_utils import HistoryManager
from utils.api_utils import make_api_request, APIError
from openai import OpenAI

class MultiCharacterService:
    """多角色对话服务类"""
    
    def __init__(self):
        """初始化多角色服务"""
        self.logger = logging.getLogger(__name__)
        self.config_service = config_service
        self.story_service = story_service
        self.memory_service = memory_service
        
        # 确保配置服务已初始化
        if not self.config_service.initialized:
            self.config_service.initialize()
        
        # 创建历史记录管理器
        app_config = self.config_service.get_app_config()
        history_dir = app_config["history_dir"]
        self.history_manager = HistoryManager(history_dir)
        
        # 初始化OpenAI客户端
        self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """初始化OpenAI客户端"""
        try:
            api_key = os.getenv("CHAT_API_KEY")
            base_url = os.getenv("CHAT_API_BASE_URL")
            model = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
            
            if not api_key:
                self.logger.error("缺少CHAT_API_KEY环境变量")
                raise ValueError("Missing CHAT_API_KEY environment variable")
                
            if not base_url:
                self.logger.warning("未设置CHAT_API_BASE_URL，将使用默认API地址")
                base_url = "https://api.openai.com/v1"
            
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=60.0,
                max_retries=3
            )
            self.chat_model = model
            
        except Exception as e:
            self.logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
    
    def is_multi_character_story(self, story_id: str) -> bool:
        """
        检查是否为多角色故事
        
        Args:
            story_id: 故事ID
            
        Returns:
            是否为多角色故事
        """
        try:
            if not self.story_service.load_story(story_id):
                return False
            
            story_data = self.story_service.get_current_story_data()
            if not story_data:
                return False
            
            # 正确处理字符列表格式
            characters = story_data.get('characters', [])
            if isinstance(characters, dict):
                # 如果characters是字典，尝试获取list字段
                characters = characters.get('list', [])
            elif isinstance(characters, str):
                # 如果characters是字符串，尝试解析
                try:
                    characters = json.loads(characters)
                    if isinstance(characters, dict):
                        characters = characters.get('list', [])
                except json.JSONDecodeError:
                    characters = [characters]
            
            return len(characters) > 1
            
        except Exception as e:
            self.logger.error(f"检查多角色故事失败: {e}")
            return False

    def get_story_characters(self, story_id: str) -> List[Dict[str, Any]]:
        """
        获取故事中的角色信息
        
        Args:
            story_id: 故事ID
            
        Returns:
            角色信息列表，包含玩家和所有角色
        """
        if not self.story_service.load_story(story_id):
            return []
        
        return self.story_service.get_story_characters()

    def format_messages_for_character(self, messages: List[Dict[str, str]], target_character_id: str, story_id: str) -> List[Dict[str, str]]:
        """
        为特定角色格式化消息，确保每个角色只看到自己说的话作为assistant消息
        
        Args:
            messages: 原始消息列表
            target_character_id: 目标角色ID
            story_id: 故事ID
            
        Returns:
            格式化后的消息列表
        """
        try:
            # 获取故事角色信息
            story_data = self.story_service.get_current_story_data()
            
            # 正确处理字符列表格式
            characters = story_data.get('characters', [])
            if isinstance(characters, dict):
                characters = characters.get('list', [])
            elif isinstance(characters, str):
                try:
                    characters = json.loads(characters)
                    if isinstance(characters, dict):
                        characters = characters.get('list', [])
                except json.JSONDecodeError:
                    characters = [characters]
            
            # 确保characters是列表
            if not isinstance(characters, list):
                characters = []
            
            # 构建角色专用的消息格式
            formatted_messages = []
            current_user_content = ""
            
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")
                
                if role == "system":
                    # 系统消息保持不变
                    formatted_messages.append(msg)
                elif role == "user":
                    # 用户消息：累积到当前用户内容中
                    if current_user_content:
                        current_user_content += f"\n玩家：{content}"
                    else:
                        current_user_content = f"玩家：{content}"
                elif role == target_character_id:
                    # 目标角色的消息：作为assistant消息（包含完整JSON）
                    if current_user_content:
                        formatted_messages.append({"role": "user", "content": current_user_content})
                        current_user_content = ""
                    formatted_messages.append({"role": "assistant", "content": content})
                elif role in characters:
                    # 其他角色的消息：提取content并添加到用户内容中
                    try:
                        # 解析JSON获取content
                        msg_data = json.loads(content)
                        character_content = msg_data.get('content', content)
                        
                        # 获取角色名
                        char_config = self.config_service.get_character_config(role)
                        char_name = char_config.get('name', role) if char_config else role
                        
                        if current_user_content:
                            current_user_content += f"\n{char_name}：{character_content}"
                        else:
                            current_user_content = f"{char_name}：{character_content}"
                    except (json.JSONDecodeError, KeyError):
                        # 解析失败，使用原始内容
                        char_config = self.config_service.get_character_config(role)
                        char_name = char_config.get('name', role) if char_config else role
                        
                        if current_user_content:
                            current_user_content += f"\n{char_name}：{content}"
                        else:
                            current_user_content = f"{char_name}：{content}"
                else:
                    # 处理其他可能的消息类型，确保它们使用标准角色
                    if role not in ["system", "user", "assistant", "tool"]:
                        # 非标准角色，转换为用户消息
                        if current_user_content:
                            formatted_messages.append({"role": "user", "content": current_user_content})
                            current_user_content = ""
                        # 将非标准角色的消息内容添加到用户消息中
                        char_config = self.config_service.get_character_config(role)
                        char_name = char_config.get('name', role) if char_config else role
                        current_user_content = f"{char_name}：{content}"
                    else:
                        # 标准角色，直接添加
                        if current_user_content:
                            formatted_messages.append({"role": "user", "content": current_user_content})
                            current_user_content = ""
                        formatted_messages.append(msg)
            
            # 如果还有未处理的用户内容，添加到最后
            if current_user_content:
                formatted_messages.append({"role": "user", "content": current_user_content})
            
            # 确保消息列表不以assistant结尾（避免prefix与json_object冲突）
            if formatted_messages and formatted_messages[-1].get("role") == "assistant":
                # 如果最后一个消息是assistant，添加一个空的user消息
                formatted_messages.append({"role": "user", "content": "请继续对话。"})
            
            return formatted_messages
            
        except Exception as e:
            self.logger.error(f"格式化角色消息失败: {e}")
            # 出错时回退到原始格式，但确保所有角色都是标准值
            safe_messages = []
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content", "")
                if role not in ["system", "user", "assistant", "tool"]:
                    # 将非标准角色转换为用户消息
                    char_config = self.config_service.get_character_config(role)
                    char_name = char_config.get('name', role) if char_config else role
                    safe_messages.append({
                        "role": "user",
                        "content": f"{char_name}：{content}"
                    })
                else:
                    safe_messages.append(msg)
            return safe_messages
    
    def build_character_system_prompt(self, character_id: str, story_id: str, user_query: str = None) -> str:
        """
        构建角色专用的系统提示词
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            user_query: 用户查询，用于记忆检索
            
        Returns:
            完整的系统提示词
        """
        try:
            # 获取基础角色提示词
            char_config = self.config_service.get_character_config(character_id)
            if not char_config:
                return "你是一个AI助手。"
            
            base_prompt = char_config.get('prompt', '')
            
            # 获取故事信息
            story_data = self.story_service.get_current_story_data()
            characters = story_data.get('characters', {}).get('list', [])
            if isinstance(characters, str):
                characters = [characters]
            
            # 获取其他角色名称
            other_character_names = []
            for char_id in characters:
                if char_id != character_id:
                    other_char_config = self.config_service.get_character_config(char_id)
                    if other_char_config:
                        other_character_names.append(other_char_config.get('name', char_id))
            
            # 获取剧情引导信息
            offset = self.story_service.get_offset()
            _, current_chapter, next_chapter = self.story_service.get_current_chapter_info()
            
            # 构建剧情引导
            guidance = f"当前章节：`{current_chapter}`"
            if next_chapter:
                if offset < 10:
                    guidance += f"。下一章节：`{next_chapter}`。请保持在当前章节，不要进入下一章节"
                elif 10 <= offset < 30:
                    guidance += f"。请暗示性地引导用户向`{next_chapter}`方向推进故事"
                elif offset >= 30:
                    guidance += f"。请制造突发事件以引导用户向`{next_chapter}`方向推进故事"
            
            # 构建多角色提示词
            char_name = char_config.get('name', character_id)
            if other_character_names:
                story_prompt = f"你是一个视听小说中的多角色故事的主要角色{char_name}，故事中还有其他角色：{', '.join(other_character_names)}。你需要为用户制造沉浸式的剧情体验，适时让其他角色参与对话和互动。{guidance}\n\n{base_prompt}"
            else:
                story_prompt = f"你是一个视听小说中的角色{char_name}，你需要为用户制造沉浸式的剧情体验。{guidance}\n\n{base_prompt}"
            
            # 添加记忆上下文
            if user_query:
                try:
                    memory_context = self.memory_service.search_story_memory(
                        query=user_query,
                        story_id=story_id
                    )
                    
                    if memory_context:
                        story_prompt = f"{story_prompt}\n\n{memory_context}"
                        
                except Exception as e:
                    self.logger.error(f"记忆检索失败: {e}")
            
            return story_prompt
            
        except Exception as e:
            self.logger.error(f"构建角色系统提示词失败: {e}")
            return "你是一个AI助手。"
    
    def chat_completion_for_character(
        self, 
        character_id: str,
        story_id: str,
        messages: List[Dict[str, str]],
        user_query: str = None
    ) -> Iterator[str]:
        """
        为特定角色调用对话API
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            messages: 消息列表
            user_query: 用户查询
            
        Returns:
            流式响应迭代器
        """
        try:
            # 构建角色专用系统提示词
            system_prompt = self.build_character_system_prompt(character_id, story_id, user_query)
            
            # 格式化消息
            formatted_messages = self.format_messages_for_character(messages, character_id, story_id)
            
            # 移除现有system消息并添加角色专用系统提示词
            formatted_messages = [msg for msg in formatted_messages if msg.get("role") != "system"]
            formatted_messages.insert(0, {"role": "system", "content": system_prompt})
            
            # 获取聊天配置
            chat_config = self.config_service.get_chat_config()
            
            # 清理不兼容的配置项
            del_list = ['model', 'stream', 'top_k']
            for key in del_list:
                if key in chat_config:
                    del chat_config[key]
            
            self.logger.info(f"为角色 {character_id} 发送对话请求")
            
            # 调用API
            stream_ans = self.client.chat.completions.create(
                model=os.getenv("CHAT_MODEL"),
                messages=formatted_messages,
                stream=True,
                response_format={"type": "json_object"},
                **chat_config
            )
            
            # 处理流式响应
            is_reasoning = False
            for chunk in stream_ans:
                data = chunk.choices[0].delta
                content = data.content
                
                if content is None:
                    if not is_reasoning:
                        self.logger.info(f"角色 {character_id} 思考中...")
                        is_reasoning = True
                    reasoning_content = data.reasoning_content
                    if reasoning_content:
                        print(reasoning_content, end="", flush=True)
                    continue
                else:
                    if is_reasoning:
                        self.logger.info(f"角色 {character_id} 回答中...")
                        is_reasoning = False
                
                print(content, end="", flush=True)
                yield content
                
        except Exception as e:
            self.logger.error(f"角色 {character_id} 对话失败: {e}")
            yield f'{{"content": "抱歉，我现在无法回应。", "mood": 1}}'
    
    def save_character_message(self, character_id: str, story_id: str, message: str):
        """
        保存角色消息到历史记录和记忆
        
        Args:
            character_id: 角色ID
            story_id: 故事ID
            message: 消息内容
        """
        try:
            # 保存到历史记录
            history_path = self.story_service.get_story_history_path()
            self.history_manager.save_message_to_file(
                history_path, 
                "assistant", 
                message,
                is_multi_character=True,
                speaker_character_id=character_id
            )
            
            # 保存到记忆数据库
            char_config = self.config_service.get_character_config(character_id)
            character_name = char_config.get('name', character_id) if char_config else character_id
            
            self.memory_service.add_story_message(
                speaker_name=character_name,
                message=message,
                story_id=story_id
            )
            
            self.logger.info(f"已保存角色 {character_id} 的消息")
            
        except Exception as e:
            self.logger.error(f"保存角色消息失败: {e}")
    

    def call_director_model(self, chat_history: str, isPlayer: bool = False) -> Tuple[int, int]:
        """
        调用导演模型判断剧情进度和下次说话角色
        
        Args:
            chat_history: 聊天历史记录
            isPlayer: 是否为玩家回合，如果是则在角色列表中排除玩家
            
        Returns:
            (偏移值, 下次说话角色序号) 的元组
        """
        # if not self.story_data:
        #     raise ValueError("未加载任何故事")
        
        # 获取章节信息
        _, current_chapter, next_chapter = self.story_service.get_current_chapter_info()
        
        if next_chapter is None:
            # 已经是最后一章，返回0表示故事结束，随机选择角色
            import random
            characters = self.story_service.get_story_characters()
            next_speaker = random.randint(0, len(characters) - 1)
            return 0, next_speaker
        
        # 获取故事角色信息
        characters = self.story_service.get_story_characters()
        
        # 如果是玩家回合，过滤掉玩家角色
        if isPlayer:
            characters = [char for char in characters if not char.get('is_player', False)]

        self.logger.info("变量值: " + str(characters))
        # 构建提示词
        user_prompt = get_director_prompts_mult(chat_history, current_chapter, next_chapter, characters,isPlayer)
        
        # 获取API配置
        option_config = get_option_config()
        url = self.config_service.get_option_api_url()
        api_key = self.config_service.get_option_api_key()
        
        # 准备请求数据
        messages = [
            {"role": "system", "content": DIRECTOR_SYSTEM_PROMPTS_MULT},
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
            self.logger.info(f"导演正在决策...")
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
                        # 处理可能的```json```包裹
                        json_content = content.strip()
                        if json_content.startswith('```json'):
                            json_content = json_content[7:]
                        elif json_content.startswith('```'):
                            json_content = json_content[3:]
                        if json_content.endswith('```'):
                            json_content = json_content[:-3]
                        json_content = json_content.strip()
                        
                        # 解析JSON
                        result_json = json.loads(json_content)
                        offset = result_json.get("offset", 1)
                        next_speaker = result_json.get("next", 1)
                        
                        # 验证范围
                        if 0 <= offset <= 9 and isPlayer <= next_speaker <= len(characters):
                            self.logger.info(f"导演模型判断结果: offset={offset}, next={next_speaker}")
                            return offset, next_speaker
                        else:
                            self.logger.warning(f"导演模型返回超出范围的结果: offset={offset}, next={next_speaker}")
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"导演模型返回非JSON格式: {content}, 错误: {e}")
                    
                    # 解析失败，随机选择
                    import random
                    next_speaker = random.randint(isPlayer, len(characters) )
                    self.logger.info(f"解析失败，随机选择角色: {next_speaker}")
                    return 1, next_speaker
            
            self.logger.error("导演模型返回格式错误")
            import random
            characters = self.story_service.get_story_characters()
            return 1, random.randint(isPlayer, len(characters) )
            
        except Exception as e:
            self.logger.error(f"调用导演模型失败: {e}")
            import random
            characters = self.story_service.get_story_characters()
            return 1, random.randint(isPlayer, len(characters) )  # 出错时返回默认值

# 创建全局多角色服务实例
multi_character_service = MultiCharacterService()
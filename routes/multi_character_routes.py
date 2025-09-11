# -*- coding: utf-8 -*-
"""
多角色对话路由
专门处理多角色故事的对话逻辑，与单角色逻辑完全分离
"""
import os
import json
import re
import traceback
from pathlib import Path
from flask import Blueprint, request, jsonify, Response
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.config_service import config_service
need_config = not config_service.initialize()
if not need_config:
    from services.multi_character_service import multi_character_service
    from services.story_service import story_service
    from utils.history_utils import HistoryManager

bp = Blueprint('multi_character', __name__, url_prefix='/api/multi-character')

def handle_next_speaker_recursively(story_id, max_history, characters, max_depth=5, current_depth=0):
    """
    递归处理下一个说话者，避免无限循环
    
    Args:
        story_id: 故事ID
        max_history: 最大历史记录数
        characters: 角色列表
        max_depth: 最大递归深度
        current_depth: 当前递归深度
    """
    if current_depth >= max_depth:
        print(f"达到最大递归深度 {max_depth}，停止角色自动回复")
        yield f"data: {json.dumps({'nextSpeaker': 'player', 'message': '对话轮次过多，请继续'})}\n\n"
        return
    
    try:
        # 获取聊天历史用于导演判断
        history_path = story_service.get_story_history_path()
        app_config = config_service.get_app_config()
        history_dir = app_config["history_dir"]
        history_manager = HistoryManager(history_dir)
        
        history_messages = history_manager.load_history_from_file(history_path, max_history, max_history * 2)
        
        # 构建聊天历史文本
        chat_history_text = ""
        for msg in history_messages[-max_history:]:
            if msg["role"] == "user":
                chat_history_text += f"玩家：{msg['content']}\n"
            elif msg["role"] == "assistant" or msg["role"] in [char['id'] for char in characters]:
                # 解析JSON格式的回复，只取content部分
                try:
                    msg_data = json.loads(msg['content'])
                    content = msg_data.get('content', msg['content'])
                except:
                    content = msg['content']
                
                # 获取角色名
                speaker_id = msg.get('speaker_character_id') or msg["role"]
                character_config = config_service.get_character_config(speaker_id)
                character_name = character_config.get('name', speaker_id) if character_config else speaker_id
                chat_history_text += f"{character_name}：{content}\n"
        
        # 调用导演模型
        director_offset, next_speaker = multi_character_service.call_director_model(chat_history_text)
        
        # 处理导演结果
        if director_offset == 0:
            # 推进到下一章节
            story_service.update_progress(advance_chapter=True)
            
            # 检查是否故事结束
            if story_service.is_story_finished():
                print("故事已结束")
                yield f"data: {json.dumps({'storyFinished': True})}\n\n"
                return
        else:
            # 增加偏移值
            story_service.update_progress(offset_increment=director_offset)
        
        # 发送故事进度更新
        current_idx, current_chapter, next_chapter = story_service.get_current_chapter_info()
        current_offset = story_service.get_offset()
        
        progress_update = {
            'storyProgress': {
                'current': current_idx,
                'currentChapter': current_chapter,
                'nextChapter': next_chapter,
                'offset': current_offset
            }
        }
        
        if story_service.is_story_finished():
            progress_update['storyFinished'] = True
        
        yield f"data: {json.dumps(progress_update)}\n\n"
        
        # 处理下次说话角色
        if 0 <= next_speaker < len(characters):
            next_character = characters[next_speaker]
            if next_character['is_player']:
                # 下次是玩家说话，结束递归
                print(f"下次说话：{next_character['name']}")
                yield f"data: {json.dumps({'nextSpeaker': 'player'})}\n\n"
            else:
                # 下次是角色说话，继续角色自动回复
                print(f"下次说话：{next_character['name']} (角色自动回复，深度: {current_depth + 1})")
                yield f"data: {json.dumps({'nextSpeaker': next_character['id'], 'nextSpeakerName': next_character['name']})}\n\n"
                
                # 执行角色自动回复
                try:
                    # 获取历史消息用于角色回复
                    history_messages_dict = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in history_messages
                    ]
                    
                    # 构建该角色专用的查询
                    last_message = ""
                    if history_messages:
                        last_msg = history_messages[-1]
                        if last_msg["role"] == "user":
                            last_message = last_msg["content"]
                        elif last_msg["role"] == "assistant" or last_msg["role"] in [char['id'] for char in characters]:
                            try:
                                msg_data = json.loads(last_msg["content"])
                                last_message = msg_data.get('content', last_msg["content"])
                            except:
                                last_message = last_msg["content"]
                    
                    # 调用角色回复API
                    character_stream = multi_character_service.chat_completion_for_character(
                        character_id=next_character['id'],
                        story_id=story_id,
                        messages=history_messages_dict,
                        user_query=f"作为{next_character['name']}继续对话"
                    )
                    
                    # 发送角色回复
                    character_response = ""
                    yield f"data: {json.dumps({'characterResponse': True, 'characterName': next_character['name']})}\n\n"
                    
                    for chunk in character_stream:
                        if chunk:
                            character_response += chunk
                            # 实时解析并发送角色回复
                            try:
                                content_match = re.search(r'"content":\s*"([^"]*)', character_response)
                                if content_match:
                                    current_content = content_match.group(1)
                                    current_content = current_content.replace('\\"', '"').replace('\\\\', '\\')
                                    yield f"data: {json.dumps({'characterContent': current_content})}\n\n"
                            except:
                                yield f"data: {json.dumps({'characterContent': chunk})}\n\n"
                    
                    # 保存角色回复到历史记录和记忆
                    if character_response:
                        multi_character_service.save_character_message(
                            character_id=next_character['id'],
                            story_id=story_id,
                            message=character_response
                        )
                    
                    yield f"data: {json.dumps({'characterResponseComplete': True})}\n\n"
                    
                    # 递归处理下一个说话者
                    yield from handle_next_speaker_recursively(story_id, max_history, characters, max_depth, current_depth + 1)
                    
                except Exception as e:
                    print(f"角色自动回复失败: {e}")
                    traceback.print_exc()
                    yield f"data: {json.dumps({'error': f'角色自动回复失败: {str(e)}'})}\n\n"
        else:
            print(f"无效的角色序号: {next_speaker}")
            yield f"data: {json.dumps({'nextSpeaker': 'player', 'message': '角色选择错误，请继续'})}\n\n"
            
    except Exception as e:
        print(f"处理下一个说话者失败: {e}")
        traceback.print_exc()
        yield f"data: {json.dumps({'error': f'处理下一个说话者失败: {str(e)}'})}\n\n"

@bp.route('/chat/stream', methods=['POST'])
def multi_character_chat_stream():
    """多角色故事流式对话"""
    try:
        data = request.json
        message = data.get('message', '')
        story_id = data.get('story_id', '')
        
        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400
        if not story_id:
            return jsonify({'success': False, 'error': '故事ID不能为空'}), 400
        
        # 检查是否为多角色故事
        if not multi_character_service.is_multi_character_story(story_id):
            return jsonify({'success': False, 'error': '不是多角色故事'}), 400
        
        # 加载故事
        if not story_service.load_story(story_id):
            return jsonify({'success': False, 'error': f'故事 {story_id} 不存在'}), 404
        
        def generate():
            try:
                # 保存用户消息到历史记录
                history_path = story_service.get_story_history_path()
                app_config = config_service.get_app_config()
                history_dir = app_config["history_dir"]
                history_manager = HistoryManager(history_dir)
                
                history_manager.save_message_to_file(
                    history_path, 
                    "user", 
                    message,
                    is_multi_character=True
                )
                
                # 保存用户消息到记忆
                from services.memory_service import memory_service
                memory_service.add_story_message(
                    speaker_name="玩家",
                    message=message,
                    story_id=story_id
                )
                
                # 获取故事角色信息
                characters = multi_character_service.get_story_characters(story_id)
                
                # 获取配置
                max_history = config_service.get_app_config()["max_history_length"]
                
                # 处理下一个说话者（可能触发角色自动回复）
                yield from handle_next_speaker_recursively(story_id, max_history, characters)
                
            except Exception as e:
                print(f"多角色对话流处理失败: {e}")
                traceback.print_exc()
                yield f"data: {json.dumps({'error': f'对话处理失败: {str(e)}'})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/characters/<story_id>', methods=['GET'])
def get_story_characters(story_id):
    """获取故事中的角色信息"""
    try:
        if not multi_character_service.is_multi_character_story(story_id):
            return jsonify({'success': False, 'error': '不是多角色故事'}), 400
        
        characters = multi_character_service.get_story_characters(story_id)
        return jsonify({'success': True, 'characters': characters})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/check/<story_id>', methods=['GET'])
def check_multi_character_story(story_id):
    """检查是否为多角色故事"""
    try:
        is_multi = multi_character_service.is_multi_character_story(story_id)
        return jsonify({'success': True, 'is_multi_character': is_multi})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
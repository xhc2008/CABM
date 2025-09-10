# -*- coding: utf-8 -*-
"""
剧情模式相关路由
"""
import os
import json
import re
import datetime
import shutil
import traceback
import uuid
from pathlib import Path
from flask import Blueprint, request, render_template, jsonify, Response, send_file
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.config_service import config_service
need_config = not config_service.initialize()
if not need_config:
    from services.chat_service import chat_service
    from services.image_service import image_service
    from services.story_service import story_service
    from services.option_service import option_service

bp = Blueprint('story', __name__, url_prefix='')

# ------------------------------------------------------------------
# 辅助函数
# ------------------------------------------------------------------
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
        history_messages = chat_service.get_history()[-max_history:]
        chat_history_text = ""
        for msg in history_messages:
            if msg.role == "user":
                chat_history_text += f"玩家：{msg.content}\n"
            elif msg.role == "assistant":
                # 解析JSON格式的回复，只取content部分
                try:
                    msg_data = json.loads(msg.content)
                    content = msg_data.get('content', msg.content)
                except:
                    content = msg.content
                
                # 获取角色名（从历史记录的speaker_character_id或当前角色）
                character_config = chat_service.get_character_config()
                character_name = character_config.get('name', 'AI助手')
                chat_history_text += f"{character_name}：{content}\n"
        
        # 调用导演模型
        director_offset, next_speaker = story_service.call_director_model(chat_history_text)
        
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
                    # 保存当前角色ID
                    original_character = chat_service.config_service.current_character_id
                    
                    # 切换到指定角色
                    chat_service.config_service.set_character(next_character['id'])
                    
                    # 重新设置剧情模式系统提示词（触发该角色的记忆和设定加载）
                    chat_service.set_story_system_prompt()
                    
                    # 构建该角色专用的系统提示词（包含记忆检索）
                    # 使用最后一条消息作为查询来检索相关记忆
                    last_message = ""
                    if history_messages:
                        last_msg = history_messages[-1]
                        if last_msg.role == "user":
                            last_message = last_msg.content
                        elif last_msg.role == "assistant":
                            try:
                                msg_data = json.loads(last_msg.content)
                                last_message = msg_data.get('content', last_msg.content)
                            except:
                                last_message = last_msg.content
                    
                    character_system_prompt = chat_service._build_system_prompt_with_context(last_message)
                    
                    # 构建该角色的对话历史格式
                    character_messages = chat_service.format_messages_for_character(next_character['id'])
                    
                    # 移除现有system消息并添加角色专用系统提示词
                    character_messages = [msg for msg in character_messages if msg.get("role") != "system"]
                    character_messages.insert(0, {"role": "system", "content": character_system_prompt})
                    
                    # 调用角色回复API
                    character_stream = chat_service.chat_completion(
                        messages=character_messages,
                        stream=True,
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
                    
                    # 保存角色回复到历史记录
                    if character_response:
                        chat_service.add_message("assistant", character_response, speaker_character_id=next_character['id'])
                        
                        # 添加到记忆数据库
                        char_config = config_service.get_character_config(next_character['id'])
                        character_name = char_config.get('name', next_character['id']) if char_config else next_character['id']
                        
                        chat_service.memory_service.add_story_message(
                            speaker_name=character_name,
                            message=character_response,
                            story_id=story_id
                        )
                    
                    # 恢复原角色
                    if original_character:
                        chat_service.config_service.set_character(original_character)
                    
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

# ------------------------------------------------------------------
# 页面路由
# ------------------------------------------------------------------
@bp.route('/story')
def story_page():
    return render_template('story.html')

@bp.route('/story/<story_id>')
def story_chat_page(story_id):
    if not story_service.load_story(story_id):
        return f"故事 {story_id} 不存在", 404
    if not chat_service.set_story_mode(story_id):
        return f"无法设置剧情模式: {story_id}", 500

    # 使用新的场景服务获取背景
    background_url = None
    try:
        from services.scene_service import scene_service
        
        # 获取故事的背景
        last_background = scene_service.get_last_background(story_id=story_id)
        if last_background:
            background_url = scene_service.get_background_url(last_background)
    except Exception as e:
        print(f"获取故事背景失败: {e}")
    story_data = story_service.get_current_story_data()
    current_character = chat_service.get_character_config()
    app_config = config_service.get_app_config()
    show_scene_name = app_config.get("show_scene_name", True)

    return render_template(
        'story_chat.html',
        background_url=background_url,
        story_data=story_data,
        story_id=story_id,
        current_character=current_character,
        show_scene_name=show_scene_name
    )

# ------------------------------------------------------------------
# API 路由
# ------------------------------------------------------------------
@bp.route('/api/stories', methods=['GET'])
def list_stories():
    try:
        import rtoml
        saves_dir = project_root / 'data' / 'saves'
        stories = []
        if not saves_dir.exists():
            return jsonify({'success': True, 'stories': []})
        for story_dir in saves_dir.iterdir():
            if not story_dir.is_dir():
                continue
            story_toml_path = story_dir / 'story.toml'
            if not story_toml_path.exists():
                continue
            try:
                with open(story_toml_path, 'r', encoding='utf-8') as f:
                    story_data = rtoml.load(f)
                metadata = story_data.get('metadata', {})
                progress = story_data.get('progress', {})
                summary = story_data.get('summary', {})
                structure = story_data.get('structure', {})
                characters_data = story_data.get('characters', {})
                story_id = metadata.get('story_id', story_dir.name)
                title = metadata.get('title', '未命名故事')
                current_index = progress.get('current', 0)
                outline = structure.get('outline', [])
                character_ids = characters_data.get('list', [])
                current_progress = "未开始"
                if outline and 0 <= current_index < len(outline):
                    current_progress = outline[current_index]
                characters = []
                for char_id in character_ids:
                    char_config = config_service.get_character_config(char_id)
                    if char_config:
                        characters.append({
                            'id': char_id,
                            'name': char_config.get('name', char_id),
                            'color': char_config.get('color', '#ffffff')
                        })
                    else:
                        characters.append({'id': char_id, 'name': char_id, 'color': '#ffffff'})
                cover_path = story_dir / 'cover.png'
                cover_url = None
                if cover_path.exists():
                    cover_url = f"/api/stories/{story_id}/cover"
                else:
                    cover_jpg_path = story_dir / 'cover.jpg'
                    if cover_jpg_path.exists():
                        cover_url = f"/api/stories/{story_id}/cover"
                last_played = None
                try:
                    latest_time = 0
                    for file_path in story_dir.rglob('*'):
                        if file_path.is_file():
                            mtime = file_path.stat().st_mtime
                            if mtime > latest_time:
                                latest_time = mtime
                    if latest_time > 0:
                        last_played = datetime.datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
                stories.append({
                    'id': story_id,
                    'title': title,
                    'summary': summary.get('text', '暂无简介'),
                    'characters': characters,
                    'current_progress': current_progress,
                    'cover_url': cover_url,
                    'create_date': metadata.get('create_date', ''),
                    'creator': metadata.get('creator', ''),
                    'version': metadata.get('version', '1.0.0'),
                    'last_played': last_played
                })
            except Exception as e:
                print(f"读取存档 {story_dir.name} 失败: {e}")
                continue
        stories.sort(key=lambda x: (x.get('last_played', ''), x.get('create_date', '')), reverse=True)
        return jsonify({'success': True, 'stories': stories})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/stories/<story_id>/cover')
def get_story_cover(story_id):
    try:
        from PIL import Image
        story_dir = project_root / 'data' / 'saves' / story_id
        cover_path = story_dir / 'cover.png'
        if cover_path.exists():
            return send_file(str(cover_path), mimetype='image/png')
        cover_jpg_path = story_dir / 'cover.jpg'
        if cover_jpg_path.exists():
            return send_file(str(cover_jpg_path), mimetype='image/jpeg')
        default_cover = project_root / 'static' / 'images' / 'default.svg'
        if default_cover.exists():
            return send_file(str(default_cover), mimetype='image/svg+xml')
        return jsonify({'success': False, 'error': '封面图片不存在'}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/stories/create', methods=['POST'])
def create_story():
    try:
        import rtoml
        from PIL import Image
        from utils.env_utils import get_env_var
        from config import get_story_prompts, get_multi_character_story_prompts
        from utils.api_utils import make_api_request

        story_id = request.form.get('storyId')
        story_title = request.form.get('storyTitle')
        character_ids_raw = request.form.get('selectedCharacterId')
        story_direction = request.form.get('storyDirection')
        reference_info_count_raw = request.form.get('referenceInfoCount', '0')
        try:
            reference_info_count = max(0, min(100, int(reference_info_count_raw)))
        except Exception:
            reference_info_count = 0
        background_images = request.files.getlist('backgroundImages')

        if not all([story_id, story_title, character_ids_raw, story_direction]):
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400
        if not re.fullmatch(r'^[a-zA-Z0-9_]+$', story_id):
            return jsonify({'success': False, 'error': '故事ID格式不正确'}), 400

        # 解析角色ID（支持单个或多个）
        try:
            if character_ids_raw.startswith('[') and character_ids_raw.endswith(']'):
                # 多角色JSON格式
                character_ids = json.loads(character_ids_raw)
                if not isinstance(character_ids, list) or len(character_ids) == 0:
                    return jsonify({'success': False, 'error': '角色列表格式错误'}), 400
            else:
                # 单角色字符串格式
                character_ids = [character_ids_raw]
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '角色数据格式错误'}), 400

        story_dir = project_root / 'data' / 'saves' / story_id
        if story_dir.exists():
            return jsonify({'success': False, 'error': f'故事ID "{story_id}" 已存在'}), 400

        # 验证所有角色是否存在
        character_configs = {}
        for char_id in character_ids:
            char_config = config_service.get_character_config(char_id)
            if not char_config:
                return jsonify({'success': False, 'error': f'角色 "{char_id}" 不存在'}), 400
            character_configs[char_id] = char_config

        # 多角色时强制参考信息数量为0
        if len(character_ids) > 1:
            reference_info_count = 0

        story_dir.mkdir(parents=True, exist_ok=True)
        backgrounds_dir = story_dir / 'backgrounds'
        backgrounds_dir.mkdir(exist_ok=True)

        cover_created = False
        for i, bg_image in enumerate(background_images, 1):
            if bg_image and bg_image.filename:
                bg_path = backgrounds_dir / f"{i}.jpg"
                img = Image.open(bg_image)
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(str(bg_path), 'JPEG', quality=85)
                if i == 1 and not cover_created:
                    cover_path = story_dir / 'cover.png'
                    w, h = img.size
                    size = min(w, h)
                    left = (w - size) // 2
                    top = (h - size) // 2
                    cover = img.crop((left, top, left + size, top + size)).resize((512, 512), Image.Resampling.LANCZOS)
                    cover.save(str(cover_path), 'PNG')
                    cover_created = True

        (story_dir / 'history.log').touch()

        # 处理记忆和场景数据
        if len(character_ids) == 1:
            # 单角色：复制记忆和场景数据
            character_id = character_ids[0]
            memory_source = project_root / 'data' / 'memory' / character_id / f'{character_id}_memory.json'
            memory_target = story_dir / f'{story_id}_memory.json'
            if memory_source.exists():
                shutil.copy2(str(memory_source), str(memory_target))
            else:
                memory_target.write_text('[]', encoding='utf-8')

            # 复制场景数据
            from services.scene_service import scene_service
            scene_service.copy_scenes_for_story(character_id, story_id)
        else:
            # 多角色：创建空的记忆和场景文件
            memory_target = story_dir / f'{story_id}_memory.json'
            memory_target.write_text('[]', encoding='utf-8')
            
            # 为多角色创建空的场景文件
            from services.scene_service import scene_service
            scene_service.create_empty_scenes_for_story(story_id)

        # 构建角色提示词和详细信息
        character_prompts = []
        character_details_text = ""
        
        for char_id in character_ids:
            char_config = character_configs[char_id]
            char_name = char_config.get('name', char_id)
            char_prompt = char_config.get('prompt', '')
            character_prompts.append(f"{char_name}: {char_prompt}")
            
            # 单角色时才获取详细信息
            if len(character_ids) == 1 and reference_info_count > 0:
                details_file = project_root / 'data' / 'details' / f"{char_id}.json"
                if details_file.exists():
                    with open(details_file, 'r', encoding='utf-8') as f:
                        details_data = json.load(f)
                    id_to_doc = details_data.get('rag', {}).get('retriever', {}).get('id_to_doc', {})
                    docs = [str(v) for v in id_to_doc.values() if isinstance(v, str) and v.strip()]
                    if docs:
                        k = min(reference_info_count, len(docs))
                        import random
                        sampled = random.sample(docs, k)
                        character_details_text = "\n\n".join(sampled)

        api_base_url = get_env_var("CHAT_API_BASE_URL")
        api_key = get_env_var("CHAT_API_KEY")
        model = get_env_var("CHAT_MODEL")
        
        # 根据角色数量选择不同的提示词格式
        if len(character_ids) == 1:
            # 单角色
            character_config = character_configs[character_ids[0]]
            story_prompt = get_story_prompts(
                character_config.get('name', character_ids[0]),
                character_config.get('prompt', ''),
                character_details_text,
                story_direction
            )
        else:
            # 多角色
            character_names = [character_configs[char_id].get('name', char_id) for char_id in character_ids]
            combined_character_prompt = "\n".join(character_prompts)
            story_prompt = get_multi_character_story_prompts(
                character_names,
                combined_character_prompt,
                story_direction
            )
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": story_prompt}],
            "max_tokens": 2000,
            "temperature": 0.8,
            "stream": False
        }
        response, data = make_api_request(
            url=f"{api_base_url}/chat/completions",
            method="POST",
            headers=headers,
            json_data=request_data,
            timeout=60
        )
        if not (data and "choices" in data and len(data["choices"]) > 0):
            shutil.rmtree(story_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': '故事生成失败（无有效响应），请稍后重试'}), 500

        content = data["choices"][0]["message"]["content"]
        try:
            json_content = content.strip()
            if json_content.startswith('```json'):
                json_content = json_content[7:]
            elif json_content.startswith('```'):
                json_content = json_content[3:]
            if json_content.endswith('```'):
                json_content = json_content[:-3]
            json_content = json_content.strip()
            story_data = json.loads(json_content)
            summary = story_data.get('summary', '')
            outline = story_data.get('outline', [])
            if not isinstance(outline, list) or len(outline) == 0:
                raise ValueError('无效的大纲')
            outline[-1] = "故事结束"
        except Exception:
            shutil.rmtree(story_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': '故事生成失败（解析错误），请稍后重试'}), 500

        story_toml_data = {
            'metadata': {
                'story_id': story_id,
                'title': story_title,
                'creator': '用户',
                'create_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'seed': story_direction,
                'reference_info_count': reference_info_count
            },
            'progress': {'current': 0, 'offset': 0},
            'summary': {'text': summary},
            'structure': {'outline': outline},
            'characters': {'list': character_ids}
        }
        with open(story_dir / 'story.toml', 'w', encoding='utf-8') as f:
            rtoml.dump(story_toml_data, f)
        return jsonify({'success': True, 'message': '故事创建成功', 'story_id': story_id})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/story/chat', methods=['POST'])
def story_chat():
    try:
        data = request.json
        message = data.get('message', '')
        story_id = data.get('story_id', '')
        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400
        if not story_id:
            return jsonify({'success': False, 'error': '故事ID不能为空'}), 400
        if not story_service.load_story(story_id):
            return jsonify({'success': False, 'error': f'故事 {story_id} 不存在'}), 404
        chat_service.set_story_mode(story_id)
        chat_service.add_message("user", message)
        response = chat_service.chat_completion(stream=False, user_query=message)
        assistant_message = None
        if "choices" in response and len(response["choices"]) > 0:
            message_data = response["choices"][0].get("message", {})
            if message_data and "content" in message_data:
                assistant_message = message_data["content"]
        return jsonify({
            'success': True,
            'message': assistant_message,
            'history': [msg.to_dict() for msg in chat_service.get_history()]
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/story/chat/stream', methods=['POST'])
def story_chat_stream():
    try:
        data = request.json
        message = data.get('message', '')
        story_id = data.get('story_id', '')
        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400
        if not story_id:
            return jsonify({'success': False, 'error': '故事ID不能为空'}), 400
        if not story_service.load_story(story_id):
            return jsonify({'success': False, 'error': f'故事 {story_id} 不存在'}), 404
        
        # 检查是否为多角色故事，如果是则重定向到多角色服务
        story_data = story_service.get_current_story_data()
        characters = story_data.get('characters', {}).get('list', [])
        if isinstance(characters, str):
            characters = [characters]
        
        if len(characters) > 1:
            # 多角色故事，重定向到多角色路由
            from routes.multi_character_routes import multi_character_chat_stream
            return multi_character_chat_stream()
        
        # 单角色故事，继续使用原有逻辑
        chat_service.set_story_mode(story_id)
        chat_service.add_message("user", message)

        def generate():
            try:
                stream_gen = chat_service.chat_completion(stream=True, user_query=message)
                full_response = ""
                parsed_mood = None
                parsed_content = ""
                
                for chunk in stream_gen:
                    if chunk is not None:
                        full_response += chunk
                        
                        # 实时解析JSON内容，即使不完整
                        try:
                            # 尝试提取content字段，即使JSON不完整
                            content_match = re.search(r'"content":\s*"([^"]*)', full_response)
                            if content_match:
                                current_content = content_match.group(1)
                                
                                # 处理转义字符
                                current_content = current_content.replace('\\"', '"')
                                current_content = current_content.replace('\\\\', '\\')
                                
                                if current_content != parsed_content:
                                    # 检查是否是新的响应（内容变短）
                                    if len(current_content) < len(parsed_content):
                                        # 新的响应开始，发送完整内容
                                        yield f"data: {json.dumps({'content': current_content})}\n\n"
                                        parsed_content = current_content
                                    else:
                                        # 同一响应的增量内容
                                        content_diff = current_content[len(parsed_content):]
                                        if content_diff:
                                            yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                        parsed_content = current_content
                            
                            # 同时尝试提取mood字段（支持int和string类型）
                            mood_match = re.search(r'"mood":\s*("[^"]*"|\d+)', full_response)
                            if mood_match:
                                mood_str = mood_match.group(1)
                                try:
                                    # 如果是引号包围的字符串
                                    if mood_str.startswith('"') and mood_str.endswith('"'):
                                        current_mood = mood_str[1:-1]
                                    else:
                                        # 如果是数字
                                        current_mood = int(mood_str)

                                    if current_mood != parsed_mood:
                                        yield f"data: {json.dumps({'mood': current_mood})}\n\n"
                                        parsed_mood = current_mood
                                except (ValueError, TypeError):
                                    pass
                                    
                        except Exception as e:
                            # JSON解析失败，尝试作为普通文本发送
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # 将完整消息添加到历史记录（存储原始响应内容）
                if full_response:
                    chat_service.add_message("assistant", full_response)
                    # 添加到记忆数据库（存储原始响应内容）
                    try:
                        # 检查是否为多角色故事
                        story_data = story_service.get_current_story_data()
                        characters = story_data.get('characters', {}).get('list', []) if story_data else []
                        if isinstance(characters, str):
                            characters = [characters]
                        is_multi_character = len(characters) > 1
                        
                        if is_multi_character:
                            # 多角色模式：分别添加用户和角色消息
                            chat_service.memory_service.add_story_message(
                                speaker_name="玩家",
                                message=message,
                                story_id=story_id
                            )
                            
                            # 获取当前角色名
                            if characters:
                                char_config = config_service.get_character_config(characters[0])
                                character_name = char_config.get('name', characters[0]) if char_config else characters[0]
                            else:
                                character_name = "角色"
                            
                            chat_service.memory_service.add_story_message(
                                speaker_name=character_name,
                                message=full_response,
                                story_id=story_id
                            )
                        else:
                            # 单角色模式：使用原有方法
                            chat_service.memory_service.add_story_conversation(
                                user_message=message,
                                assistant_message=full_response,
                                story_id=story_id
                            )
                    except Exception as e:
                        print(f"添加对话到记忆数据库失败: {e}")
                        traceback.print_exc()
                    
                    # 调用导演模型和生成选项（同步执行以便发送更新给前端）
                    try:
                        # 获取聊天历史用于导演判断
                        app_config = config_service.get_app_config()
                        max_history = app_config["max_history_length"]
                        
                        # 格式化聊天历史
                        history_messages = chat_service.get_history()[-max_history:]
                        chat_history_text = ""
                        for msg in history_messages:
                            if msg.role == "user":
                                chat_history_text += f"玩家：{msg.content}\n"
                            elif msg.role == "assistant":
                                # 解析JSON格式的回复，只取content部分
                                try:
                                    msg_data = json.loads(msg.content)
                                    content = msg_data.get('content', msg.content)
                                except:
                                    content = msg.content
                                
                                # 获取角色名
                                character_config = chat_service.get_character_config()
                                character_name = character_config.get('name', 'AI助手')
                                chat_history_text += f"{character_name}：{content}\n"
                        
                        # 调用导演模型
                        director_offset, next_speaker = story_service.call_director_model(chat_history_text)
                        
                        # 处理导演结果
                        story_finished = False
                        if director_offset == 0:
                            # 推进到下一章节
                            story_service.update_progress(advance_chapter=True)
                            
                            # 检查是否故事结束
                            if story_service.is_story_finished():
                                print("故事已结束")
                                story_finished = True
                        else:
                            # 增加偏移值
                            story_service.update_progress(offset_increment=director_offset)
                        
                        # 使用递归函数处理下次说话角色
                        characters = story_service.get_story_characters()
                        
                        # 处理第一次导演判断的结果
                        if 0 <= next_speaker < len(characters):
                            next_character = characters[next_speaker]
                            if next_character['is_player']:
                                # 下次是玩家说话，正常等待用户输入
                                print(f"下次说话：{next_character['name']}")
                                yield f"data: {json.dumps({'nextSpeaker': 'player'})}\n\n"
                            else:
                                # 下次是角色说话，使用递归函数处理
                                print(f"开始角色自动回复流程，首个角色：{next_character['name']}")
                                
                                # 先发送第一个角色的信息
                                yield f"data: {json.dumps({'nextSpeaker': next_character['id'], 'nextSpeakerName': next_character['name']})}\n\n"
                                
                                # 执行第一个角色的回复
                                try:
                                    # 保存当前角色ID
                                    original_character = chat_service.config_service.current_character_id
                                    
                                    # 切换到指定角色
                                    chat_service.config_service.set_character(next_character['id'])
                                    
                                    # 重新设置剧情模式系统提示词（触发该角色的记忆和设定加载）
                                    chat_service.set_story_system_prompt()
                                    
                                    # 构建该角色专用的系统提示词（包含记忆检索）
                                    character_system_prompt = chat_service._build_system_prompt_with_context(message)
                                    
                                    # 构建该角色的对话历史格式
                                    character_messages = chat_service.format_messages_for_character(next_character['id'])
                                    
                                    # 移除现有system消息并添加角色专用系统提示词
                                    character_messages = [msg for msg in character_messages if msg.get("role") != "system"]
                                    character_messages.insert(0, {"role": "system", "content": character_system_prompt})
                                    
                                    # 调用角色回复API
                                    character_stream = chat_service.chat_completion(
                                        messages=character_messages,
                                        stream=True,
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
                                    
                                    # 保存角色回复到历史记录
                                    if character_response:
                                        chat_service.add_message("assistant", character_response, speaker_character_id=next_character['id'])
                                        
                                        # 添加到记忆数据库
                                        char_config = config_service.get_character_config(next_character['id'])
                                        character_name = char_config.get('name', next_character['id']) if char_config else next_character['id']
                                        
                                        chat_service.memory_service.add_story_message(
                                            speaker_name=character_name,
                                            message=character_response,
                                            story_id=story_id
                                        )
                                    
                                    # 恢复原角色
                                    if original_character:
                                        chat_service.config_service.set_character(original_character)
                                    
                                    yield f"data: {json.dumps({'characterResponseComplete': True})}\n\n"
                                    
                                    # 递归处理后续的说话者
                                    yield from handle_next_speaker_recursively(story_id, max_history, characters)
                                        
                                except Exception as e:
                                    print(f"角色自动回复失败: {e}")
                                    traceback.print_exc()
                                    yield f"data: {json.dumps({'error': f'角色自动回复失败: {str(e)}'})}\n\n"
                        else:
                            print(f"无效的角色序号: {next_speaker}")
                            yield f"data: {json.dumps({'nextSpeaker': 'player', 'message': '角色选择错误，请继续'})}\n\n"

                        
                    except Exception as e:
                        print(f"导演模型处理失败: {e}")
                        traceback.print_exc()
                    
                    # 生成选项
                    try:
                        conversation_history = chat_service.format_messages()
                        character_config = chat_service.get_character_config()
                        options = option_service.generate_options(
                            conversation_history=conversation_history,
                            character_config=character_config,
                            user_query=message
                        )
                        
                        if options:
                            yield f"data: {json.dumps({'options': options})}\n\n"
                    except Exception as e:
                        print(f"选项生成失败: {e}")
                        
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                error_msg = str(e)
                print(f"流式响应错误: {error_msg}")
                traceback.print_exc()
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                yield "data: [DONE]\n\n"
        
        headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
        return Response(generate(), mimetype='text/event-stream', headers=headers)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
@bp.route('/api/story/exit', methods=['POST'])
def exit_story_mode():
    try:
        chat_service.exit_story_mode()
        return jsonify({'success': True, 'message': '已退出剧情模式'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/story/history', methods=['GET'])
def get_story_history_paginated():
    """分页获取故事历史记录"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 获取当前故事的历史记录文件路径
        history_path = story_service.get_story_history_path()
        if not history_path:
            return jsonify({
                'success': False,
                'error': '未找到故事历史记录'
            }), 400
        
        # 分页加载历史记录
        result = chat_service.history_manager.load_history_from_file_paginated(
            file_path=history_path,
            page=page,
            page_size=page_size
        )
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'参数错误: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
# -*- coding: utf-8 -*-
"""
普通聊天、背景图生成、清空历史
"""
import os
import json
import re
import traceback
from pathlib import Path
from flask import Blueprint, request, render_template, jsonify, Response, send_file
from io import BytesIO
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 只有在非配置模式下才导入服务
from services.config_service import config_service
need_config = not config_service.initialize()
if not need_config:
    from services.chat_service import chat_service
    from services.image_service import image_service
    from services.scene_service import scene_service
    from services.option_service import option_service
    from utils.api_utils import APIError

bp = Blueprint('chat', __name__, url_prefix='')

# ------------------------------------------------------------------
# 导入文本处理工具
from utils.text_utils import get_last_assistant_sentence_for_character

# ------------------------------------------------------------------
# 页面路由
# ------------------------------------------------------------------
@bp.route('/')
def home():
    if need_config:
        return render_template('config.html')
    return render_template('index.html')

@bp.route('/chat')
def chat_page():
    try:
        if getattr(chat_service, "story_mode", False):
            chat_service.exit_story_mode()
        current_character = chat_service.get_character_config()
        if current_character and "id" in current_character:
            chat_service.set_character(current_character["id"])
    except Exception as e:
        print(f"进入聊天页切换角色失败: {e}")
        traceback.print_exc()

    # 使用新的场景服务获取背景
    background_url = None
    try:
        from services.scene_service import scene_service
        
        # 获取当前角色ID
        current_character = chat_service.get_character_config()
        character_id = current_character.get("id") if current_character else None
        
        # 获取最后使用的背景
        last_background = scene_service.get_last_background(character_id=character_id)
        if last_background:
            background_url = scene_service.get_background_url(last_background)
    except Exception as e:
        print(f"获取背景失败: {e}")

    character_image_path = os.path.join(bp.static_folder or str(project_root / 'static'), 'images', 'default', '1.png')
    if not os.path.exists(character_image_path):
        print(f"警告: 默认角色图片不存在: {character_image_path}")

    app_config = config_service.get_app_config()
    show_scene_name = app_config.get("show_scene_name", True)

    last_sentence = ""
    try:
        current_character = chat_service.get_character_config()
        if current_character and "id" in current_character:
            last_sentence = get_last_assistant_sentence_for_character(current_character["id"]) or ""
    except Exception:
        pass

    from utils.plugin import FRONTEND_HOOKS
    plugin_inject_scripts = []
    def collect_inject(route, path):
        if route.endswith('/inject.js'):
            plugin_inject_scripts.append(route)
    for hook in FRONTEND_HOOKS:
        hook(collect_inject)

    return render_template(
        'chat.html',
        background_url=background_url,
        show_scene_name=show_scene_name,
        last_sentence=last_sentence,
        plugin_inject_scripts=plugin_inject_scripts
    )

# ------------------------------------------------------------------
# API 路由
# ------------------------------------------------------------------
@bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message', '')
        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400
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
    except APIError as e:
        return jsonify({'success': False, 'error': e.message}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    try:
        message = request.json.get('message', '')
        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'}), 400
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
                
                # 处理完整响应（保持原有逻辑）
                if full_response:
                    chat_service.add_message("assistant", full_response)
                    try:
                        if chat_service.story_mode and chat_service.current_story_id:
                            chat_service.memory_service.add_story_conversation(
                                user_message=message,
                                assistant_message=full_response,
                                story_id=chat_service.current_story_id
                            )
                        else:
                            character_id = chat_service.config_service.current_character_id or "default"
                            chat_service.memory_service.add_conversation(
                                user_message=message,
                                assistant_message=full_response,
                                character_name=character_id
                            )
                    except Exception as e:
                        print(f"添加对话到记忆数据库失败: {e}")
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
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"

        headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
        return Response(generate(), mimetype='text/event-stream', headers=headers)
        
    except APIError as e:
        return jsonify({'success': False, 'error': e.message}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/background', methods=['POST'])
def generate_background():
    try:
        prompt = request.json.get('prompt')
        result = image_service.generate_background(prompt)
        if "image_path" in result:
            rel_path = os.path.relpath(result["image_path"], start=(bp.static_folder or str(project_root / 'static')))
            background_url = f"/static/{rel_path.replace(os.sep, '/')}"
            return jsonify({
                'success': True,
                'background_url': background_url,
                'prompt': result.get('config', {}).get('prompt')
            })
        return jsonify({'success': False, 'error': '背景图片生成失败'}), 500
    except APIError as e:
        return jsonify({'success': False, 'error': e.message}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/backgrounds', methods=['GET'])
def get_backgrounds():
    """获取所有背景列表"""
    try:
        import json
        from pathlib import Path
        
        # 读取背景配置文件
        background_json_path = project_root / 'data' / 'background.json'
        if background_json_path.exists():
            with open(background_json_path, 'r', encoding='utf-8') as f:
                backgrounds = json.load(f)
        else:
            backgrounds = {}
        
        return jsonify({
            'success': True,
            'backgrounds': backgrounds
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/background/select', methods=['POST'])
def select_background():
    """选择指定的背景"""
    try:
        from services.scene_service import scene_service
        
        filename = request.json.get('filename')
        character_id = request.json.get('character_id')
        story_id = request.json.get('story_id')
        
        if not filename:
            return jsonify({'success': False, 'error': '未指定背景文件'}), 400
        
        # 更新场景使用记录
        scene_service.update_background_usage(filename, character_id, story_id)
        
        # 构建背景URL
        background_url = scene_service.get_background_url(filename)
        
        # 读取背景信息
        import json
        from pathlib import Path
        
        background_json_path = project_root / 'data' / 'background.json'
        prompt = None
        if background_json_path.exists():
            with open(background_json_path, 'r', encoding='utf-8') as f:
                backgrounds = json.load(f)
                if filename in backgrounds:
                    prompt = backgrounds[filename].get('prompt')
        
        return jsonify({
            'success': True,
            'background_url': background_url,
            'prompt': prompt
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/background/initial', methods=['POST'])
def get_initial_background():
    """获取初始背景"""
    try:
        from services.scene_service import scene_service
        
        character_id = request.json.get('character_id')
        story_id = request.json.get('story_id')
        
        # 获取最后使用的背景
        last_background = scene_service.get_last_background(character_id, story_id)
        
        if last_background:
            background_url = scene_service.get_background_url(last_background)
            
            # 读取背景信息
            import json
            background_json_path = project_root / 'data' / 'background.json'
            prompt = None
            if background_json_path.exists():
                with open(background_json_path, 'r', encoding='utf-8') as f:
                    backgrounds = json.load(f)
                    if last_background in backgrounds:
                        prompt = backgrounds[last_background].get('prompt')
            
            return jsonify({
                'success': True,
                'background_url': background_url,
                'filename': last_background,
                'prompt': prompt
            })
        else:
            # 没有历史背景，随机选择一个
            selected_bg = scene_service.select_random_background(character_id, story_id)
            if selected_bg:
                background_url = scene_service.get_background_url(selected_bg)
                return jsonify({
                    'success': True,
                    'background_url': background_url,
                    'filename': selected_bg,
                    'prompt': None
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '没有可用的背景'
                })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/background/stats', methods=['POST'])
def get_background_stats():
    """获取背景使用统计"""
    try:
        from services.scene_service import scene_service
        
        character_id = request.json.get('character_id')
        story_id = request.json.get('story_id')
        
        # 获取使用统计
        stats = scene_service.get_background_usage_stats(character_id, story_id)
        
        # 获取每个背景的完整信息
        background_info = []
        for bg_record in stats:
            bg_info = scene_service.get_background_info(bg_record["id"], character_id, story_id)
            background_info.append(bg_info)
        
        return jsonify({
            'success': True,
            'stats': background_info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/background/add', methods=['POST'])
def add_background():
    """添加新背景"""
    try:
        import json
        import uuid
        from pathlib import Path
        
        name = request.json.get('name', '').strip()
        desc = request.json.get('desc', '').strip()
        prompt = request.json.get('prompt', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': '背景名称不能为空'}), 400
        
        # 生成背景图片
        result = image_service.generate_background(prompt if prompt else None)
        if "image_path" not in result:
            return jsonify({'success': False, 'error': '背景图片生成失败'}), 500
        
        # 生成新的文件名
        file_extension = Path(result["image_path"]).suffix
        new_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # 移动文件到backgrounds目录
        backgrounds_dir = project_root / 'data' / 'backgrounds'
        backgrounds_dir.mkdir(exist_ok=True)
        
        new_path = backgrounds_dir / new_filename
        import shutil
        shutil.move(result["image_path"], new_path)
        
        # 更新背景配置文件
        background_json_path = project_root / 'data' / 'background.json'
        if background_json_path.exists():
            with open(background_json_path, 'r', encoding='utf-8') as f:
                backgrounds = json.load(f)
        else:
            backgrounds = {}
        
        backgrounds[new_filename] = {
            'name': name,
            'desc': desc,
            'prompt': prompt if prompt else result.get('config', {}).get('prompt', '')
        }
        
        with open(background_json_path, 'w', encoding='utf-8') as f:
            json.dump(backgrounds, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'filename': new_filename,
            'message': '背景添加成功'
        })
        
    except APIError as e:
        return jsonify({'success': False, 'error': e.message}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/clear', methods=['POST'])
def clear_history():
    try:
        chat_service.clear_history()
        prompt_type = request.json.get('prompt_type', 'character')
        chat_service.set_system_prompt(prompt_type)
        return jsonify({'success': True, 'message': '对话历史已清空'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/history', methods=['GET'])
def get_history_paginated():
    """分页获取历史记录"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 获取当前角色
        current_character = chat_service.get_character_config()
        if not current_character or "id" not in current_character:
            return jsonify({
                'success': False,
                'error': '未选择角色'
            }), 400
        
        character_id = current_character["id"]
        
        # 分页加载历史记录
        result = chat_service.history_manager.load_history_paginated(
            character_id=character_id,
            page=page,
            page_size=page_size,
            max_cache_size=200
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
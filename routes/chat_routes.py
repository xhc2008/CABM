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
# 工具函数（与 app.py 保持一致）
# ------------------------------------------------------------------
def _parse_assistant_text(raw: str) -> str:
    if not raw:
        return ""
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            text = obj.get('content')
            if isinstance(text, str):
                return text
        if isinstance(obj, str):
            return obj
    except Exception:
        pass
    return str(raw)

def _extract_last_sentence(text: str) -> str:
    import re as _re
    if not text:
        return ""
    text = _re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    sentence_endings = ['。', '！', '？', '!', '?', '.', '…', '♪', '...']
    escaped = ''.join(_re.escape(ch) for ch in sentence_endings)
    pattern = rf"([^ {escaped}]+(?:[{escaped}]+)?)$"
    m = _re.search(pattern, text)
    return m.group(1).strip() if m else text

def _get_last_assistant_sentence_for_character(character_id: str) -> str:
    try:
        history_messages = chat_service.history_manager.load_history(character_id, count=200, max_cache_size=500)
        for msg in reversed(history_messages):
            if msg.get('role') == 'assistant':
                raw = msg.get('content', '')
                text = _parse_assistant_text(raw)
                return _extract_last_sentence(text)
    except Exception as e:
        print(f"提取最后一句失败: {e}")
    return ""

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

    background = image_service.get_current_background()
    if not background:
        try:
            result = image_service.generate_background()
            if "image_path" in result:
                background = result["image_path"]
        except Exception as e:
            print(f"背景图片生成失败: {e}")

    background_url = None
    if background:
        background_url = f"/static/images/cache/{os.path.basename(background)}"

    character_image_path = os.path.join(bp.static_folder or str(project_root / 'static'), 'images', 'default', '1.png')
    if not os.path.exists(character_image_path):
        print(f"警告: 默认角色图片不存在: {character_image_path}")

    current_scene = scene_service.get_current_scene()
    scene_data = current_scene.to_dict() if current_scene else None
    app_config = config_service.get_app_config()
    show_scene_name = app_config.get("show_scene_name", True)

    last_sentence = ""
    try:
        current_character = chat_service.get_character_config()
        if current_character and "id" in current_character:
            last_sentence = _get_last_assistant_sentence_for_character(current_character["id"]) or ""
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
        current_scene=scene_data,
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
                        # --- JSON 解析逻辑（同原 app.py）---
                        try:
                            json_start = full_response.rfind('{')
                            if json_start != -1:
                                potential_json = full_response[json_start:]
                                brace_count = 0
                                json_end = -1
                                for i, char in enumerate(potential_json):
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_end = i + 1
                                            break
                                if json_end != -1:
                                    json_str = potential_json[:json_end]
                                    try:
                                        json_data = json.loads(json_str)
                                        if 'mood' in json_data:
                                            new_mood = json_data['mood']
                                            if new_mood != parsed_mood:
                                                parsed_mood = new_mood
                                                yield f"data: {json.dumps({'mood': parsed_mood})}\n\n"
                                        if 'content' in json_data:
                                            new_content = json_data['content']
                                            if new_content != parsed_content:
                                                if len(new_content) < len(parsed_content):
                                                    yield f"data: {json.dumps({'content': new_content})}\n\n"
                                                    parsed_content = new_content
                                                else:
                                                    content_diff = new_content[len(parsed_content):]
                                                    if content_diff:
                                                        yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                                    parsed_content = new_content
                                    except json.JSONDecodeError:
                                        pass
                        except Exception as e:
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
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

@bp.route('/api/clear', methods=['POST'])
def clear_history():
    try:
        chat_service.clear_history()
        prompt_type = request.json.get('prompt_type', 'character')
        chat_service.set_system_prompt(prompt_type)
        return jsonify({'success': True, 'message': '对话历史已清空'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
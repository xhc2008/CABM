from flask import Blueprint, render_template, request, jsonify, Response, current_app
import traceback
import json
import re
import os
from services.chat_service import chat_service
from services.image_service import image_service
from services.scene_service import scene_service
from services.option_service import option_service
from utils.api_utils import APIError

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat_page():
    # 聊天页面逻辑（从app.py迁移）
    try:
        if getattr(chat_service, "story_mode", False):
            chat_service.exit_story_mode()
        current_character = chat_service.get_character_config()
        if current_character and "id" in current_character:
            chat_service.set_character(current_character["id"])
    except Exception as e:
        print(f"进入聊天页切换角色失败: {str(e)}")
        traceback.print_exc()
    background = image_service.get_current_background()
    if not background:
        try:
            result = image_service.generate_background()
            if "image_path" in result:
                background = result["image_path"]
        except Exception as e:
            print(f"背景图片生成失败: {str(e)}")
            traceback.print_exc()
    background_url = None
    if background:
        background_url = f"/static/images/cache/{os.path.basename(background)}"
    character_image_path = os.path.join(current_app.static_folder, 'images', 'default', '1.png')
    if not os.path.exists(character_image_path):
        print(f"警告: 默认角色图片不存在: {character_image_path}")
        print("请将角色图片放置在 static/images/default/1.png")
    current_scene = scene_service.get_current_scene()
    scene_data = current_scene.to_dict() if current_scene else None
    show_scene_name = True
    last_sentence = ""
    try:
        current_character = chat_service.get_character_config()
        if current_character and "id" in current_character:
            last_sentence = ""  # 可调用工具函数
    except Exception:
        pass
    plugin_inject_scripts = []
    return render_template(
        'chat.html',
        background_url=background_url,
        current_scene=scene_data,
        show_scene_name=show_scene_name,
        last_sentence=last_sentence,
        plugin_inject_scripts=plugin_inject_scripts
    )

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
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

@chat_bp.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    try:
        data = request.json
        message = data.get('message', '')
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
                                else:
                                    try:
                                        content_match = re.search(r'"content":\s*"([^"]*)', potential_json)
                                        if content_match:
                                            current_content = content_match.group(1)
                                            if current_content != parsed_content:
                                                if len(current_content) < len(parsed_content):
                                                    yield f"data: {json.dumps({'content': current_content})}\n\n"
                                                    parsed_content = current_content
                                                else:
                                                    content_diff = current_content[len(parsed_content):]
                                                    if content_diff:
                                                        yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                                    parsed_content = current_content
                                    except Exception:
                                        pass
                        except Exception as e:
                            print(f"解析JSON响应失败: {e}")
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
                        traceback.print_exc()
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
                        traceback.print_exc()
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
    except APIError as e:
        return jsonify({'success': False, 'error': e.message}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

from flask import Blueprint, render_template, jsonify, request, Response, send_file
import traceback
import json
import os
from services.story_service import story_service
from services.chat_service import chat_service
from services.image_service import image_service
from services.config_service import config_service
from services.option_service import option_service
from pathlib import Path
from utils.plugin_utils import get_plugin_inject_scripts

story_bp = Blueprint('story', __name__)

@story_bp.route('/story')
def story_page():
    plugin_inject_scripts = get_plugin_inject_scripts()
    return render_template('story.html', plugin_inject_scripts=plugin_inject_scripts)

@story_bp.route('/story/<story_id>')
def story_chat_page(story_id):
    if not story_service.load_story(story_id):
        return f"故事 {story_id} 不存在", 404
    if not chat_service.set_story_mode(story_id):
        return f"无法设置剧情模式: {story_id}", 500
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

@story_bp.route('/api/stories', methods=['GET'])
def list_stories():
    try:
        stories = story_service.list_stories()
        return jsonify({'success': True, 'stories': stories})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@story_bp.route('/api/stories/create', methods=['POST'])
def create_story():
    try:
        data = request.get_json(silent=True)
        if not data:
            data = request.form
        # 兼容前端所有字段
        story_id = data.get('storyId', '').strip()
        title = data.get('storyTitle', data.get('title', '')).strip()
        summary = data.get('storyDirection', data.get('summary', '')).strip()
        selected_character_id = data.get('selectedCharacterId', '').strip()
        reference_info_count = data.get('referenceInfoCount', '')
        outline = data.get('outline', [])
        # 兼容 outline 字符串
        if isinstance(outline, str):
            import json
            try:
                outline = json.loads(outline)
            except Exception:
                outline = []
        # backgroundImages 可为文件或路径，暂略
        if not story_id or not title or not summary or not selected_character_id:
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400
        # 假设 story_service.create_story 支持这些参数
        # 获取角色配置
        character_config = config_service.get_character_config(selected_character_id)
        if not character_config:
            return jsonify({'success': False, 'error': f'未找到角色配置: {selected_character_id}'}), 404

        # 获取角色详细信息
        from services.character_details_service import character_details_service
        character_details = ""
        try:
            details_result = character_details_service.search_character_details(selected_character_id, "who are you", top_k=3)
            if details_result:
                character_details = details_result
        except Exception as e:
            print(f"获取角色详细信息失败，将使用空字符串: {e}")
            character_details = character_config.get('description', '')  # 回退到基础描述
        
        # 创建故事
        success = story_service.create_story(
            story_id=story_id,
            title=title,
            character_id=selected_character_id,
            story_direction=summary,
            background_images=None  # 可后续扩展
        )
        if success:
            return jsonify({'success': True, 'story_id': story_id})
        else:
            return jsonify({'success': False, 'error': '创建失败'}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@story_bp.route('/api/stories/<story_id>/cover')
def get_story_cover(story_id):
    try:
        story_dir = Path('data/saves') / story_id
        cover_path = story_dir / 'cover.png'
        if cover_path.exists():
            return send_file(str(cover_path), mimetype='image/png')
        cover_jpg_path = story_dir / 'cover.jpg'
        if cover_jpg_path.exists():
            return send_file(str(cover_jpg_path), mimetype='image/jpeg')
        default_cover = Path('static/images/default.svg')
        if default_cover.exists():
            return send_file(str(default_cover), mimetype='image/svg+xml')
        return jsonify({'success': False, 'error': '封面图片不存在'}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@story_bp.route('/api/story/chat', methods=['POST'])
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

@story_bp.route('/api/story/chat/stream', methods=['POST'])
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
                                        import re
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
                        chat_service.memory_service.add_story_conversation(
                            user_message=message,
                            assistant_message=full_response,
                            story_id=story_id
                        )
                    except Exception as e:
                        print(f"添加对话到故事记忆数据库失败: {e}")
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
        # 保证异常时返回JSON而不是HTML
        return jsonify({'success': False, 'error': str(e)}), 500

@story_bp.route('/api/story/exit', methods=['POST'])
def exit_story_mode():
    try:
        chat_service.exit_story_mode()
        return jsonify({'success': True, 'message': '已退出剧情模式'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

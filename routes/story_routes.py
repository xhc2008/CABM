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
        from config import get_story_prompts
        from utils.api_utils import make_api_request

        story_id = request.form.get('storyId')
        story_title = request.form.get('storyTitle')
        character_id = request.form.get('selectedCharacterId')
        story_direction = request.form.get('storyDirection')
        reference_info_count_raw = request.form.get('referenceInfoCount', '0')
        try:
            reference_info_count = max(0, min(100, int(reference_info_count_raw)))
        except Exception:
            reference_info_count = 0
        background_images = request.files.getlist('backgroundImages')

        if not all([story_id, story_title, character_id, story_direction]):
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400
        if not re.fullmatch(r'^[a-zA-Z0-9_]+$', story_id):
            return jsonify({'success': False, 'error': '故事ID格式不正确'}), 400

        story_dir = project_root / 'data' / 'saves' / story_id
        if story_dir.exists():
            return jsonify({'success': False, 'error': f'故事ID "{story_id}" 已存在'}), 400

        character_config = config_service.get_character_config(character_id)
        if not character_config:
            return jsonify({'success': False, 'error': f'角色 "{character_id}" 不存在'}), 400

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

        memory_source = project_root / 'data' / 'memory' / character_id / f'{character_id}_memory.json'
        memory_target = story_dir / f'{story_id}_memory.json'
        if memory_source.exists():
            shutil.copy2(str(memory_source), str(memory_target))
        else:
            memory_target.write_text('[]', encoding='utf-8')

        character_prompt = character_config.get('prompt', '')
        character_details_text = ""
        if reference_info_count > 0:
            details_file = project_root / 'data' / 'details' / f"{character_id}.json"
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
        story_prompt = get_story_prompts(
            character_config.get('name', character_id),
            character_prompt,
            character_details_text,
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
            'characters': {'list': [character_id]}
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
        chat_service.set_story_mode(story_id)
        chat_service.add_message("user", message)

        def generate():
            try:
                stream_gen = chat_service.chat_completion(stream=True, user_query=message)
                full_response = ""
                for chunk in stream_gen:
                    if chunk is not None:
                        full_response += chunk
                        # 与 chat_routes.py 中同样的 JSON 解析逻辑，略
                        # 这里简化，仅发送文本块
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                if full_response:
                    chat_service.add_message("assistant", full_response)
                    chat_service.memory_service.add_story_conversation(
                        user_message=message,
                        assistant_message=full_response,
                        story_id=story_id
                    )
                    # 可在此处调用导演模型与选项生成，与原 app.py 一致
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
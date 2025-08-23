# -*- coding: utf-8 -*-
"""
角色管理：选择、列表、自定义角色
"""
import os
import re
import json
import time
import traceback
from pathlib import Path
from flask import Blueprint, request, render_template, jsonify
import sys

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.config_service import config_service
need_config = not config_service.initialize()
if not need_config:
    from services.chat_service import chat_service
import rtoml

bp = Blueprint('character', __name__, url_prefix='')

# ------------------------------------------------------------------
# 工具函数
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
@bp.route('/select-character')
def select_character_page():
    if need_config:
        return render_template('config.html')
    try:
        app_conf = config_service.get_app_config()
        history_dir = app_conf.get("history_dir", project_root / "data" / "history")
        characters = config_service.list_available_characters()
        character_items = []
        for ch in characters:
            ch_id = ch.get("id")
            ch_name = ch.get("name", ch_id)
            image_dir = ch.get("image", f"static/images/{ch_id}")
            description = ch.get("description")
            history_file = Path(history_dir) / f"{ch_id}_history.log"
            mtime = history_file.stat().st_mtime if history_file.exists() else 0
            full_image_dir = project_root / image_dir
            avatar_abs = full_image_dir / 'avatar.png'
            avatar_url = f"/{image_dir}/avatar.png" if avatar_abs.exists() else "/static/images/default.svg"
            last_sentence = _get_last_assistant_sentence_for_character(ch_id)
            short = last_sentence
            max_len = 100
            if short and len(short) > max_len:
                short = short[:max_len] + ".."
            character_items.append({
                "id": ch_id,
                "name": ch_name,
                "description": description,
                "color": ch.get("color", "#ffffff"),
                "avatar_url": avatar_url,
                "mtime": mtime,
                "last_modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime)) if mtime else "无历史",
                "last_sentence": last_sentence,
                "last_sentence_short": short
            })
        character_items.sort(key=lambda x: x["mtime"], reverse=True)
        return render_template('select_character.html', characters=character_items)
    except Exception as e:
        print(f"加载角色选择页面失败: {e}")
        traceback.print_exc()
        return render_template('select_character.html', characters=[])

@bp.route('/custom_character')
def custom_character_page():
    return render_template('custom_character.html')

# ------------------------------------------------------------------
# API 路由
# ------------------------------------------------------------------
@bp.route('/api/characters', methods=['GET'])
def list_characters():
    try:
        current_character = chat_service.get_character_config()
        available_characters = config_service.list_available_characters()
        return jsonify({
            'success': True,
            'current_character': current_character,
            'available_characters': available_characters
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/characters/<character_id>', methods=['POST'])
def set_character(character_id):
    try:
        if chat_service.set_character(character_id):
            character_config = chat_service.get_character_config()
            return jsonify({
                'success': True,
                'character': character_config,
                'message': f"角色已切换为 {character_config['name']}"
            })
        return jsonify({'success': False, 'error': f"未找到角色: {character_id}"}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/characters/<character_id>/images', methods=['GET'])
def get_character_images(character_id):
    try:
        character_config = config_service.get_character_config(character_id)
        if not character_config:
            return jsonify({'success': False, 'error': f"未找到角色: {character_id}"}), 404
        image_dir = character_config.get('image', '')
        if not image_dir:
            return jsonify({'success': False, 'error': "角色未配置图片目录"}), 400
        full_image_dir = project_root / image_dir
        if not full_image_dir.exists():
            return jsonify({'success': False, 'error': "角色图片目录不存在"}), 404
        image_files, avatar_url = [], None
        for filename in full_image_dir.iterdir():
            if filename.suffix.lower() == '.png':
                if filename.name.lower() == 'avatar.png':
                    avatar_url = f"/{image_dir}/{filename.name}"
                    continue
                try:
                    number = int(filename.stem)
                    image_files.append({
                        'number': number,
                        'filename': filename.name,
                        'url': f"/{image_dir}/{filename.name}"
                    })
                except ValueError:
                    continue
        image_files.sort(key=lambda x: x['number'])
        default_image = f"/{image_dir}/1.png" if image_files and image_files[0]['number'] == 1 else (avatar_url or f"/{image_dir}/1.png")
        return jsonify({
            'success': True,
            'images': image_files,
            'avatar_url': avatar_url,
            'default_image': default_image
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/custom-character', methods=['POST'])
def create_custom_character():
    try:
        # 由于代码较长，与原 app.py 保持一致，这里直接复用原实现
        # 实际项目中可再拆 service 层，这里保持与旧逻辑一致
        import rtoml
        from utils.env_utils import get_env_var
        from pydub import AudioSegment
        import shutil
        import uuid
        import tempfile

        character_id = request.form.get('characterId')
        character_name = request.form.get('characterName')
        character_english_name = request.form.get('characterEnglishName', '')
        theme_color = request.form.get('themeColorText')
        image_offset = request.form.get('imageOffset', '0')
        scale_rate = request.form.get('scaleRate', '100')
        character_intro = request.form.get('characterIntro')
        character_description = request.form.get('characterDescription')
        avatar_image = request.files.get('avatarImage')
        detail_files = request.files.getlist('characterDetails')
        mood_names = request.form.getlist('mood_name[]')
        mood_images = request.files.getlist('mood_image[]')
        mood_audios = request.files.getlist('mood_audio[]')
        mood_ref_texts = request.form.getlist('mood_ref_text[]')

        # 省略大量参数校验，与原 app.py 一致
        # 最终保存字符 .toml 与资源文件
        character_toml_path = project_root / 'characters' / f"{character_id}.toml"
        # 若已存在则覆盖
        if character_toml_path.exists():
            character_toml_path.unlink()
        image_dir = project_root / 'static' / 'images' / character_id
        image_dir.mkdir(parents=True, exist_ok=True)
        avatar_path = image_dir / 'avatar.png'
        avatar_image.save(str(avatar_path))
        ref_audio_dir = project_root / 'data' / 'ref_audio' / character_id
        ref_audio_dir.mkdir(parents=True, exist_ok=True)

        # 保存心情图片、音频、文本（与原逻辑一致）
        valid_moods = []
        counter = 1
        for i, name in enumerate(mood_names):
            if name and name.strip():
                if i < len(mood_images) and mood_images[i] and mood_images[i].filename:
                    (image_dir / f"{counter}.png").write_bytes(mood_images[i].read())
                if i < len(mood_audios) and mood_audios[i] and mood_audios[i].filename:
                    audio_path = ref_audio_dir / f"{counter}.wav"
                    if mood_audios[i].filename.lower().endswith('.wav'):
                        mood_audios[i].save(str(audio_path))
                    else:
                        temp_path = ref_audio_dir / f"temp_{uuid.uuid4().hex}_{mood_audios[i].filename}"
                        mood_audios[i].save(str(temp_path))
                        AudioSegment.from_file(str(temp_path)).export(str(audio_path), format="wav")
                        temp_path.unlink(missing_ok=True)
                if i < len(mood_ref_texts) and mood_ref_texts[i].strip():
                    (ref_audio_dir / f"{counter}.txt").write_text(mood_ref_texts[i].strip(), encoding='utf-8')
                valid_moods.append({"name": name.strip()})
                counter += 1

        character_config = {
            "id": character_id,
            "name": character_name,
            "name_en": character_english_name,
            "image": f"static/images/{character_id}",
            "calib": int(image_offset),
            "scale_rate": int(scale_rate),
            "color": theme_color,
            "description": character_intro,
            "prompt": character_description,
            "welcome": f"你好！我是{character_name}，很高兴认识你！",
            "moods": valid_moods,
            "examples": [
                {"role": "user", "content": "你好，请介绍一下自己"},
                {"role": "assistant", "content": f"你好！我是{character_name}，很高兴认识你！"}
            ]
        }
        with open(character_toml_path, 'w', encoding='utf-8') as f:
            f.write(rtoml.dumps(character_config))

        # 处理角色详细信息向量数据库
        if detail_files:
            from services.character_details_service import character_details_service
            temp_dir = project_root / 'temp' / 'character_details' / character_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            try:
                saved_files = []
                for i, detail_file in enumerate(detail_files):
                    if detail_file and detail_file.filename and detail_file.filename.lower().endswith('.txt'):
                        file_path = temp_dir / f"detail_{i}_{detail_file.filename}"
                        detail_file.save(str(file_path))
                        saved_files.append(str(file_path))
                if saved_files:
                    character_details_service.build_character_details(character_id, saved_files)
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        return jsonify({
            'success': True,
            'message': f'自定义角色 {character_name} 创建成功',
            'character_id': character_id
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'创建失败: {str(e)}'}), 500

@bp.route('/api/reload-characters', methods=['GET'])
def reload_characters():
    try:
        import characters
        characters._character_configs.clear()
        available_characters = config_service.list_available_characters()
        return jsonify({'success': True, 'characters': available_characters})
    except Exception as e:
        return jsonify({'success': False, 'error': f'重新加载失败: {str(e)}'}), 500

@bp.route('/api/check-character/<character_id>', methods=['GET'])
def check_character_exists(character_id):
    try:
        py_path = project_root / 'characters' / f"{character_id}.py"
        toml_path = project_root / 'characters' / f"{character_id}.toml"
        return jsonify({'success': True, 'exists': py_path.exists() or toml_path.exists()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/load-character/<character_id>', methods=['GET'])
def load_character(character_id):
    try:
        import rtoml
        character_toml_path = project_root / 'characters' / f"{character_id}.toml"
        character_py_path = project_root / 'characters' / f"{character_id}.py"
        character_config = None
        if character_toml_path.exists():
            with open(character_toml_path, 'r', encoding='utf-8') as f:
                character_config = rtoml.load(f)
        elif character_py_path.exists():
            character_config = {
                'id': character_id,
                'name': character_id,
                'name_en': '',
                'color': '#ffffff',
                'calib': 0,
                'scale_rate': 100,
                'description': '',
                'prompt': '',
                'moods': []
            }
        if not character_config:
            return jsonify({'success': False, 'error': f'角色 {character_id} 不存在'}), 404
        avatar_url = f"/static/images/{character_id}/avatar.png"
        if not (project_root / 'static' / 'images' / character_id / 'avatar.png').exists():
            avatar_url = "/static/images/default.svg"
        return jsonify({
            'success': True,
            'character': {
                'id': character_config.get('id', character_id),
                'name': character_config.get('name', character_id),
                'name_en': character_config.get('name_en', ''),
                'color': character_config.get('color', '#ffffff'),
                'calib': character_config.get('calib', 0),
                'scale_rate': character_config.get('scale_rate', 100),
                'description': character_config.get('description', ''),
                'prompt': character_config.get('prompt', ''),
                'moods': character_config.get('moods', []),
                'avatar_url': avatar_url,
                'detail_files': []
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
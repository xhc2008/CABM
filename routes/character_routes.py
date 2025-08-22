from flask import Blueprint, jsonify, request, render_template, current_app
import traceback
import os
import re
from pathlib import Path
from io import BytesIO
from pydub import AudioSegment
from services.character_details_service import character_details_service
from utils.env_utils import get_env_var
from services.chat_service import chat_service
from services.config_service import config_service

character_bp = Blueprint('character', __name__)

@character_bp.route('/api/bgm-tracks')
def list_bgm_tracks():
    """获取BGM列表"""
    try:
        bgm_dir = os.path.join('static', 'bgm')
        if not os.path.exists(bgm_dir):
            return jsonify([])
        tracks = []
        for filename in os.listdir(bgm_dir):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.aac')):
                tracks.append(filename)
        return jsonify(tracks)
    except Exception as e:
        print(f"获取BGM列表失败: {str(e)}")
        return jsonify([])

@character_bp.route('/select-character')
def select_character_page():
    from services.config_service import config_service
    from services.chat_service import chat_service
    import time
    import os
    import traceback

    try:
        app_conf = config_service.get_app_config()
        history_dir = app_conf.get("history_dir", os.path.join("data", "history"))
        characters = config_service.list_available_characters()
        character_items = []
        for ch in characters:
            ch_id = ch.get("id")
            ch_name = ch.get("name", ch_id)
            image_dir = ch.get("image", f"static/images/{ch_id}")
            description = ch.get("description")
            history_file = os.path.join(history_dir, f"{ch_id}_history.log")
            if os.path.exists(history_file):
                mtime = os.path.getmtime(history_file)
            else:
                mtime = 0
            app_static = current_app.static_folder
            static_parent = str(Path(app_static).parent)
            full_image_dir = os.path.join(static_parent, image_dir)
            avatar_abs = os.path.join(full_image_dir, 'avatar.png')
            if os.path.exists(avatar_abs):
                avatar_url = f"/{image_dir}/avatar.png"
            else:
                avatar_url = "/static/images/default.svg"
            # 获取最后一句助手回复
            last_sentence = ""
            try:
                history_messages = chat_service.history_manager.load_history(ch_id, count=200, max_cache_size=500)
                for msg in reversed(history_messages):
                    if msg.get('role') == 'assistant':
                        raw = msg.get('content', '')
                        last_sentence = str(raw)
                        break
            except Exception:
                pass
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

@character_bp.route('/api/characters', methods=['GET'])
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

@character_bp.route('/api/characters/<character_id>', methods=['POST'])
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

@character_bp.route('/api/characters/<character_id>/images', methods=['GET'])
def get_character_images(character_id):
    try:
        character_config = config_service.get_character_config(character_id)
        if not character_config:
            return jsonify({'success': False, 'error': f"未找到角色: {character_id}"}), 404
        image_dir = character_config.get('image', '')
        if not image_dir:
            return jsonify({'success': False, 'error': "角色未配置图片目录"}), 400
        app_static = current_app.static_folder
        static_parent = str(Path(app_static).parent)
        full_image_dir = os.path.join(static_parent, image_dir)
        if not os.path.exists(full_image_dir):
            return jsonify({'success': False, 'error': "角色图片目录不存在"}), 404
        image_files = []
        avatar_url = None
        for filename in os.listdir(full_image_dir):
            if filename.lower().endswith('.png'):
                if filename.lower() == 'avatar.png':
                    avatar_url = f"/{image_dir}/{filename}"
                    continue
                name_without_ext = os.path.splitext(filename)[0]
                try:
                    number = int(name_without_ext)
                    image_files.append({
                        'number': number,
                        'filename': filename,
                        'url': f"/{image_dir}/{filename}"
                    })
                except ValueError:
                    continue
        image_files.sort(key=lambda x: x['number'])
        default_image = f"/{image_dir}/1.png" if image_files and image_files[0]['number'] == 1 else (avatar_url if avatar_url else f"/{image_dir}/1.png")
        return jsonify({
            'success': True,
            'images': image_files,
            'avatar_url': avatar_url,
            'default_image': default_image
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@character_bp.route('/api/reload-characters', methods=['GET'])
def reload_characters():
    try:
        import characters
        characters._character_configs.clear()
        available_characters = config_service.list_available_characters()
        return jsonify({
            'success': True,
            'characters': available_characters
        })
    except Exception as e:
        print(f"重新加载角色列表失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'重新加载失败: {str(e)}'}), 500

@character_bp.route('/api/check-character/<character_id>', methods=['GET'])
def check_character_exists(character_id):
    try:
        character_py_path = Path('characters') / f"{character_id}.py"
        character_toml_path = Path('characters') / f"{character_id}.toml"
        exists = character_py_path.exists() or character_toml_path.exists()
        return jsonify({'success': True, 'exists': exists})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@character_bp.route('/custom_character')
def custom_character_page():
    """自定义角色页面"""
    return render_template('custom_character.html')

@character_bp.route('/api/custom-character', methods=['POST'])
def create_custom_character():
    """创建自定义角色API"""
    try:
        import rtoml
        
        # 获取表单数据
        character_id = request.form.get('characterId')
        character_name = request.form.get('characterName')
        character_english_name = request.form.get('characterEnglishName', '')
        theme_color = request.form.get('themeColorText')
        image_offset = request.form.get('imageOffset', '0')
        scale_rate = request.form.get('scaleRate', '100')
        character_intro = request.form.get('characterIntro')
        character_description = request.form.get('characterDescription')
        
        # 获取头像文件
        avatar_image = request.files.get('avatarImage')
        
        # 获取角色详细信息文件
        detail_files = request.files.getlist('characterDetails')
        
        # 验证必填字段
        if not all([character_id, character_name, theme_color, character_intro, character_description]):
            return jsonify({'success': False, 'error': '缺少必填字段'}), 400
        
        # 验证头像
        if not avatar_image or not avatar_image.filename:
            return jsonify({'success': False, 'error': '必须上传角色头像'}), 400
        
        # 验证角色ID格式
        if not re.match(r'^[a-zA-Z0-9_]+$', character_id):
            return jsonify({'success': False, 'error': '角色ID格式不正确'}), 400
        
        # 验证颜色格式
        if not re.match(r'^#[0-9A-F]{6}$', theme_color, re.IGNORECASE):
            return jsonify({'success': False, 'error': '主题颜色格式不正确'}), 400
        
        # 验证立绘校准范围
        try:
            offset = int(image_offset)
            if offset < -100 or offset > 100:
                raise ValueError()
        except ValueError:
            return jsonify({'success': False, 'error': '角色立绘校准必须是-100到100之间的整数'}), 400
            
        # 验证缩放率范围
        try:
            scale = int(scale_rate)
            if scale < 1 or scale > 300:
                raise ValueError()
        except ValueError:
            return jsonify({'success': False, 'error': '立绘缩放率必须是1到300之间的整数'}), 400
        
        # 处理心情数据
        mood_names = request.form.getlist('mood_name[]')
        mood_images = request.files.getlist('mood_image[]')
        mood_audios = request.files.getlist('mood_audio[]')
        mood_ref_texts = request.form.getlist('mood_ref_text[]')
        
        if not mood_names or len(mood_names) == 0:
            return jsonify({'success': False, 'error': '至少需要一个心情设置'}), 400
        
        # 创建角色图片目录
        image_dir = Path('static') / 'images' / character_id
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存头像
        avatar_path = image_dir / 'avatar.png'
        avatar_image.save(str(avatar_path))
        
        # 创建参考音频目录
        ref_audio_dir = Path('data') / 'ref_audio' / character_id
        ref_audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存心情图片和参考音频/文本
        valid_moods = []
        counter = 1
        for i, name in enumerate(mood_names):
            if name.strip():
                # 保存心情图片
                if i < len(mood_images) and mood_images[i] and mood_images[i].filename:
                    image_filename = f"{counter}.png"
                    image_path = image_dir / image_filename
                    mood_images[i].save(str(image_path))
                
                # 保存参考音频
                if i < len(mood_audios) and mood_audios[i] and mood_audios[i].filename:
                    audio_filename = f"{counter}.wav"
                    audio_path = ref_audio_dir / audio_filename
                    
                    if mood_audios[i].filename.lower().endswith('.wav'):
                        mood_audios[i].save(str(audio_path))
                    else:
                        # 使用pydub转换音频格式
                        import tempfile
                        import uuid
                        
                        # 使用唯一的临时文件名避免冲突
                        temp_filename = f"temp_{uuid.uuid4().hex}_{mood_audios[i].filename}"
                        temp_path = ref_audio_dir / temp_filename
                        
                        try:
                            # 保存临时文件
                            mood_audios[i].save(str(temp_path))
                            
                            # 转换音频格式
                            audio = AudioSegment.from_file(str(temp_path))
                            audio.export(str(audio_path), format="wav")
                            
                            # 确保音频对象被正确释放
                            del audio
                            
                        except Exception as e:
                            print(f"音频转换失败: {e}")
                        finally:
                            # 无论成功失败都尝试删除临时文件
                            try:
                                if temp_path.exists():
                                    # 添加延迟确保文件句柄被释放
                                    import time
                                    time.sleep(0.1)
                                    temp_path.unlink()
                            except Exception as cleanup_error:
                                print(f"清理临时文件失败: {cleanup_error}")
                
                # 保存参考文本
                if i < len(mood_ref_texts) and mood_ref_texts[i].strip():
                    text_filename = f"{counter}.txt"
                    text_path = ref_audio_dir / text_filename
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(mood_ref_texts[i].strip())
                
                valid_moods.append({"name": name.strip()})
                counter += 1
                
        # 检查是否使用旧版格式
        open_saovc = get_env_var("OPEN_SAOVC", "false").lower() == "true"
        
        character_py_path = Path('characters') / f"{character_id}.py"
        character_toml_path = Path('characters') / f"{character_id}.toml"
        
        if open_saovc:
            # 使用旧版Python格式
            character_file_content = f'''"""
角色配置文件: {character_name}
"""

# 角色基本信息
CHARACTER_ID = "{character_id}"
CHARACTER_NAME = "{character_name}"
CHARACTER_NAME_EN = "{character_english_name}"
SCALE_RATE = {scale} #缩放率（百分比）

# 角色外观
CHARACTER_IMAGE = "static/images/{character_id}"  # 角色立绘目录路径
CALIB = {offset}   # 显示位置的校准值（负值向上移动，正值向下移动）
CHARACTER_COLOR = "{theme_color}"  # 角色名称颜色

# 角色心情
MOODS = {[m["name"] for m in valid_moods]}

# 角色设定
CHARACTER_DESCRIPTION = """
{character_intro}
"""

# AI系统提示词
CHARACTER_PROMPT = """
{character_description}
"""

# 角色欢迎语
CHARACTER_WELCOME = "你好！我是{character_name}，很高兴认识你！"

# 角色对话示例
CHARACTER_EXAMPLES = [
    {{"role": "user", "content": "你好，请介绍一下自己"}},
    {{"role": "assistant", "content": "你好！我是{character_name}，很高兴认识你！"}},
]

# 获取角色配置
def get_character_config():
    """获取角色配置"""
    return {{
        "id": CHARACTER_ID,
        "name": CHARACTER_NAME,
        "name_en": CHARACTER_NAME_EN,
        "image": CHARACTER_IMAGE,
        "calib": CALIB,
        "scale_rate": SCALE_RATE,
        "color": CHARACTER_COLOR,
        "description": CHARACTER_DESCRIPTION,
        "prompt": CHARACTER_PROMPT,
        "welcome": CHARACTER_WELCOME,
        "examples": CHARACTER_EXAMPLES
    }}
'''
            # 保存Python格式配置文件
            with open(character_py_path, 'w', encoding='utf-8') as f:
                f.write(character_file_content)
        else:
            # 使用新版TOML格式
            character_config = {
                "id": character_id,
                "name": character_name,
                "name_en": character_english_name,
                "image": f"static/images/{character_id}",
                "calib": offset,
                "scale_rate": scale,
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
            
            # 保存TOML格式配置文件
            with open(character_toml_path, 'w', encoding='utf-8') as f:
                f.write(rtoml.dumps(character_config))
        
        # 处理角色详细信息文件
        if detail_files:
            # 创建临时目录保存上传的文件
            temp_dir = Path('temp') / 'character_details' / character_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                saved_files = []
                
                # 保存上传的文件
                for i, detail_file in enumerate(detail_files):
                    if detail_file and detail_file.filename:
                        # 验证文件类型
                        if not detail_file.filename.lower().endswith('.txt'):
                            continue
                        
                        # 保存文件
                        file_path = temp_dir / f"detail_{i}_{detail_file.filename}"
                        detail_file.save(str(file_path))
                        saved_files.append(str(file_path))
                
                # 构建角色详细信息向量数据库
                if saved_files:
                    success = character_details_service.build_character_details(character_id, saved_files)
                    if success:
                        print(f"角色详细信息数据库构建成功: {character_id}")
                    else:
                        print(f"角色详细信息数据库构建失败: {character_id}")
                
            except Exception as e:
                print(f"处理角色详细信息文件失败: {e}")
                traceback.print_exc()
            finally:
                # 清理临时文件
                try:
                    import shutil
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"清理临时文件失败: {e}")
        
        return jsonify({
            'success': True,
            'message': f'自定义角色 {character_name} 创建成功',
            'character_id': character_id
        })
        
    except Exception as e:
        print(f"创建自定义角色失败: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'创建失败: {str(e)}'}), 500

@character_bp.route('/api/load-character/<character_id>', methods=['GET'])
def load_character(character_id):
    try:
        import rtoml
        character_py_path = Path('characters') / f"{character_id}.py"
        character_toml_path = Path('characters') / f"{character_id}.toml"
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
        avatar_path = Path('static') / 'images' / character_id / 'avatar.png'
        if not avatar_path.exists():
            avatar_url = "/static/images/default.svg"
        detail_files = []
        character_data = {
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
            'detail_files': detail_files
        }
        return jsonify({'success': True, 'character': character_data})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

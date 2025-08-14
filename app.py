
"""
CABM应用主文件
"""
import os
import sys
import json
import time
import re
from io import BytesIO
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, Response, send_file
from pydub import AudioSegment
import traceback
# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))


from services.config_service import config_service

need_config = not config_service.initialize()
if not need_config:
    from services.chat_service import chat_service
    from services.image_service import image_service
    from services.scene_service import scene_service
    from services.option_service import option_service
    from services.ttsapi_service import ttsService
    from utils.api_utils import APIError

# 初始化配置
need_config = not config_service.initialize()
if need_config:
    print("配置初始化失败，进入配置模式。请在网页填写环境变量。")

if not need_config:
    app_config = config_service.get_app_config()
    static_folder = app_config["static_folder"]
    template_folder = app_config["template_folder"]
else:
    static_folder = str(Path(__file__).resolve().parent / "static")
    template_folder = str(Path(__file__).resolve().parent / "templates")

# 设置语音服务
if not need_config:
    tts = ttsService()
# 创建Flask应用
app = Flask(
    __name__,
    static_folder=static_folder,
    template_folder=template_folder
)

# 配置页面提交路由
@app.route('/config', methods=['POST'])
def save_config():
    # 获取表单数据
    env_vars = {
        'CHAT_API_BASE_URL': request.form.get('chat_api_base_url', ''),
        'CHAT_API_KEY': request.form.get('chat_api_key', ''),
        'CHAT_MODEL': request.form.get('chat_model', ''),
        'IMAGE_API_BASE_URL': request.form.get('image_api_base_url', ''),
        'IMAGE_API_KEY': request.form.get('image_api_key', ''),
        'IMAGE_MODEL': request.form.get('image_model', ''),
        'OPTION_API_BASE_URL': request.form.get('option_api_base_url', ''),
        'OPTION_API_KEY': request.form.get('option_api_key', ''),
        'OPTION_MODEL': request.form.get('option_model', ''),
        'MEMORY_API_BASE_URL': request.form.get('memory_api_base_url', ''),
        'MEMORY_API_KEY': request.form.get('memory_api_key', ''),
        'EMBEDDING_MODEL': request.form.get('embedding_model', ''),
        'RERANKER_MODEL': request.form.get('reranker_model', ''),
        'TTS_SERVICE_URL_GPTSoVITS': request.form.get('tts_service_url_gptsovits', ''),
        'TTS_SERVICE_URL_SiliconFlow': request.form.get('tts_service_url_siliconflow', ''),
        'TTS_SERVICE_API_KEY': request.form.get('tts_service_api_key', ''),
        'TTS_SERVICE_METHOD': request.form.get('tts_service_method', ''),
        'DEBUG': request.form.get('debug', 'False'),
        'PORT': request.form.get('port', '5000'),
        'HOST': request.form.get('host', 'localhost'),
    }
    # 保存到 .env 文件
    env_lines = [f'{k}={v}' for k, v in env_vars.items()]
    env_content = '\n'.join(env_lines)
    env_path = Path(__file__).resolve().parent / '.env'
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    return '''<div style="padding:2em;text-align:center;font-size:1.2em;">配置已保存！<br>请重新打开本程序谢谢!</div>'''

if not need_config:
    app.debug = app_config["debug"]

# 设置JavaScript模块的MIME类型
import mimetypes
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')

def convert_to_16k_wav(input_path, output_path):
    """转换音频为 16kHz 单声道 WAV"""
    audio = AudioSegment.from_file(input_path)
    audio_16k = audio.set_frame_rate(16000).set_channels(1)
    audio_16k.export(output_path, format="wav")
    return output_path

@app.route('/')
def home():
    """
    访问主页
    """
    # 如果需要配置，重定向到配置页
    if need_config:
        return render_template('config.html')
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    """聊天页面"""
    # 获取当前背景图片
    background = image_service.get_current_background()
    # 如果没有背景图片，生成一个
    if not background:
        try:
            result = image_service.generate_background()
            if "image_path" in result:
                background = result["image_path"]
        except Exception as e:
            print(f"背景图片生成失败: {str(e)}")
            traceback.print_exc()
    # 将背景路径转换为URL
    background_url = None
    if background:
        rel_path = os.path.relpath(background, start=app.static_folder)
        background_url = f"/static/{rel_path.replace(os.sep, '/')}"
    # 检查默认角色图片是否存在，如果不存在则创建一个提示
    character_image_path = os.path.join(app.static_folder, 'images', 'default', '1.png')
    if not os.path.exists(character_image_path):
        print(f"警告: 默认角色图片不存在: {character_image_path}")
        print("请将角色图片放置在 static/images/default/1.png")
    # 获取当前场景
    current_scene = scene_service.get_current_scene()
    scene_data = current_scene.to_dict() if current_scene else None
    # 获取应用配置
    app_config = config_service.get_app_config()
    show_scene_name = app_config.get("show_scene_name", True)
    return render_template(
        'chat.html',
        background_url=background_url,
        current_scene=scene_data,
        show_scene_name=show_scene_name
    )

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天API"""
    try:
        # 获取请求数据
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        # 添加用户消息
        chat_service.add_message("user", message)
        
        # 调用对话API（传递用户查询用于记忆检索）
        response = chat_service.chat_completion(stream=False, user_query=message)
        
        # 获取助手回复
        assistant_message = None
        if "choices" in response and len(response["choices"]) > 0:
            message_data = response["choices"][0].get("message", {})
            if message_data and "content" in message_data:
                assistant_message = message_data["content"]
        
        # 返回响应
        return jsonify({
            'success': True,
            'message': assistant_message,
            'history': [msg.to_dict() for msg in chat_service.get_history()]
        })
        
    except APIError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天API - 处理JSON格式响应"""
    try:
        # 获取请求数据
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        # 添加用户消息
        chat_service.add_message("user", message)
        
        # 创建流式响应生成器
        def generate():
            try:
                # 调用对话API（流式，传递用户查询用于记忆检索）
                stream_gen = chat_service.chat_completion(stream=True, user_query=message)
                full_response = ""
                parsed_mood = None
                parsed_content = ""
                
                # 逐步返回响应
                for chunk in stream_gen:
                    if chunk is not None:
                        full_response += chunk
                        
                        # 实时解析JSON格式的响应
                        try:
                            # 尝试解析当前累积的响应
                            # 查找最后一个可能的JSON对象
                            json_start = full_response.rfind('{')
                            if json_start != -1:
                                # 尝试解析从最后一个{开始的JSON
                                potential_json = full_response[json_start:]
                                
                                # 检查是否有完整的JSON结构
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
                                
                                # 如果找到完整的JSON，尝试解析
                                if json_end != -1:
                                    json_str = potential_json[:json_end]
                                    try:
                                        json_data = json.loads(json_str)
                                        
                                        # 处理mood字段
                                        if 'mood' in json_data:
                                            new_mood = json_data['mood']
                                            if new_mood != parsed_mood:
                                                parsed_mood = new_mood
                                                # 立即发送mood给前端处理表情变化
                                                yield f"data: {json.dumps({'mood': parsed_mood})}\n\n"
                                        
                                        # 处理content字段 - 实时发送增量内容
                                        if 'content' in json_data:
                                            new_content = json_data['content']
                                            if new_content != parsed_content:
                                                # 检查是否是新的JSON对象（content长度变短了）
                                                if len(new_content) < len(parsed_content):
                                                    # 新的JSON对象，直接发送全部内容
                                                    yield f"data: {json.dumps({'content': new_content})}\n\n"
                                                    parsed_content = new_content
                                                else:
                                                    # 同一个JSON对象的增量更新
                                                    content_diff = new_content[len(parsed_content):]
                                                    if content_diff:
                                                        yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                                    parsed_content = new_content
                                                
                                    except json.JSONDecodeError:
                                        # JSON不完整，继续等待更多数据
                                        pass
                                else:
                                    # 尝试解析不完整的JSON来提取content字段
                                    # 这是为了处理流式JSON的情况
                                    try:
                                        # 查找content字段的值（支持不完整的字符串）
                                        # 匹配 "content": "任何内容（可能没有结束引号）
                                        content_match = re.search(r'"content":\s*"([^"]*)', potential_json)
                                        if content_match:
                                            current_content = content_match.group(1)
                                            if current_content != parsed_content:
                                                # 检查是否是新的JSON对象（content长度变短了）
                                                if len(current_content) < len(parsed_content):
                                                    # 新的JSON对象，直接发送全部内容
                                                    yield f"data: {json.dumps({'content': current_content})}\n\n"
                                                    parsed_content = current_content
                                                else:
                                                    # 同一个JSON对象的增量更新
                                                    content_diff = current_content[len(parsed_content):]
                                                    if content_diff:
                                                        yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                                    parsed_content = current_content
                                    except Exception:
                                        pass
                                        
                        except Exception as e:
                            print(f"解析JSON响应失败: {e}")
                            # 如果JSON解析失败，尝试作为普通文本处理
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                            
                # 将完整消息添加到历史记录（存储原始响应内容）
                if full_response:
                    chat_service.add_message("assistant", full_response)
                    # 添加到记忆数据库（存储原始响应内容）
                    try:
                        character_id = chat_service.config_service.current_character_id or "default"
                        chat_service.memory_service.add_conversation(
                            user_message=message,
                            assistant_message=full_response,
                            character_name=character_id
                        )
                    except Exception as e:
                        print(f"添加对话到记忆数据库失败: {e}")
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
                            # 发送选项数据
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
        
        # 设置响应头
        headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
        }
        
        # 返回流式响应
        return Response(generate(), mimetype='text/event-stream', headers=headers)
        
    except APIError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/background', methods=['POST'])
def generate_background():
    """生成背景图片API"""
    try:
        # 获取请求数据
        data = request.json
        prompt = data.get('prompt')
        
        # 生成背景图片
        result = image_service.generate_background(prompt)
        
        # 如果生成成功
        if "image_path" in result:
            # 从绝对路径转换为相对URL
            rel_path = os.path.relpath(result["image_path"], start=app.static_folder)
            background_url = f"/static/{rel_path.replace(os.sep, '/')}"
            
            return jsonify({
                'success': True,
                'background_url': background_url,
                'prompt': result.get('config', {}).get('prompt')
            })
        
        return jsonify({
            'success': False,
            'error': '背景图片生成失败'
        }), 500
        
    except APIError as e:
        return jsonify({
            'success': False,
            'error': e.message
        }), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """清空对话历史API"""
    try:
        # 清空对话历史
        chat_service.clear_history()
        
        # 设置系统提示词
        prompt_type = request.json.get('prompt_type', 'character')
        chat_service.set_system_prompt(prompt_type)
        
        return jsonify({
            'success': True,
            'message': '对话历史已清空'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/characters', methods=['GET'])
def list_characters():
    """列出可用角色API"""
    try:
        # 获取当前角色
        current_character = chat_service.get_character_config()
        
        # 获取所有可用角色
        available_characters = config_service.list_available_characters()
        
        return jsonify({
            'success': True,
            'current_character': current_character,
            'available_characters': available_characters
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/characters/<character_id>', methods=['POST'])
def set_character(character_id):
    """设置角色API"""
    try:
        # 设置角色
        if chat_service.set_character(character_id):
            # 获取角色配置
            character_config = chat_service.get_character_config()
            
            return jsonify({
                'success': True,
                'character': character_config,
                'message': f"角色已切换为 {character_config['name']}"
            })
        
        return jsonify({
            'success': False,
            'error': f"未找到角色: {character_id}"
        }), 404
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/exit', methods=['POST'])
def exit_app():
    """退出应用API"""
    try:
        os._exit(0)
        return jsonify({
            'success': True,
            'message': '应用已退出'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@app.route('/api/characters/<character_id>/images', methods=['GET'])
def get_character_images(character_id):
    """获取角色的所有图片API"""
    try:
        # 获取角色配置
        character_config = config_service.get_character_config(character_id)
        if not character_config:
            return jsonify({
                'success': False,
                'error': f"未找到角色: {character_id}"
            }), 404
        
        # 获取角色图片目录
        image_dir = character_config.get('image', '')
        if not image_dir:
            return jsonify({
                'success': False,
                'error': "角色未配置图片目录"
            }), 400
        
        # 构建完整路径
        full_image_dir = os.path.join(app.static_folder.replace('static', ''), image_dir)
        
        # 检查目录是否存在
        if not os.path.exists(full_image_dir):
            return jsonify({
                'success': False,
                'error': "角色图片目录不存在"
            }), 404
        
        # 获取目录下的所有png文件
        image_files = []
        avatar_url = None
        
        for filename in os.listdir(full_image_dir):
            if filename.lower().endswith('.png'):
                # 检查是否是头像文件
                if filename.lower() == 'avatar.png':
                    avatar_url = f"/{image_dir}/{filename}"
                    continue
                
                # 提取数字编号
                name_without_ext = os.path.splitext(filename)[0]
                try:
                    number = int(name_without_ext)
                    image_files.append({
                        'number': number,
                        'filename': filename,
                        'url': f"/{image_dir}/{filename}"
                    })
                except ValueError:
                    # 如果文件名不是数字，跳过
                    continue
        
        # 按数字排序
        image_files.sort(key=lambda x: x['number'])
        
        # 确定默认图片：优先使用1.png，否则使用avatar.png
        default_image = f"/{image_dir}/1.png" if image_files and image_files[0]['number'] == 1 else (avatar_url if avatar_url else f"/{image_dir}/1.png")
        
        return jsonify({
            'success': True,
            'images': image_files,
            'avatar_url': avatar_url,
            'default_image': default_image
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/data/images/<path:filename>')
def serve_character_image(filename):
    """提供角色图片"""
    return send_from_directory('data/images', filename)

@app.route('/custom_character')
def custom_character_page():
    """自定义角色页面"""
    return render_template('custom_character.html')

@app.route('/api/custom-character', methods=['POST'])
def create_custom_character():
    """创建自定义角色API"""
    try:
        # 获取表单数据
        character_id = request.form.get('characterId')
        character_name = request.form.get('characterName')
        character_english_name = request.form.get('characterEnglishName', '')
        theme_color = request.form.get('themeColorText')
        image_offset = request.form.get('imageOffset', '0')
        character_intro = request.form.get('characterIntro')
        character_description = request.form.get('characterDescription')
        
        # 获取头像文件
        avatar_image = request.files.get('avatarImage')
        
        # 验证必填字段
        if not all([character_id, character_name, theme_color, character_intro, character_description]):
            return jsonify({
                'success': False,
                'error': '缺少必填字段'
            }), 400
        
        # 验证头像
        if not avatar_image or not avatar_image.filename:
            return jsonify({
                'success': False,
                'error': '必须上传角色头像'
            }), 400
        
        # 验证角色ID格式
        if not re.match(r'^[a-zA-Z0-9_]+$', character_id):
            return jsonify({
                'success': False,
                'error': '角色ID格式不正确'
            }), 400
        
        # 验证颜色格式
        if not re.match(r'^#[0-9A-F]{6}$', theme_color, re.IGNORECASE):
            return jsonify({
                'success': False,
                'error': '主题颜色格式不正确'
            }), 400
        
        # 验证立绘校准范围
        try:
            offset = int(image_offset)
            if offset < -100 or offset > 100:
                raise ValueError()
        except ValueError:
            return jsonify({
                'success': False,
                'error': '角色立绘校准必须是-100到100之间的整数'
            }), 400
        
        # 处理心情数据
        mood_names = request.form.getlist('mood_name[]')
        mood_images = request.files.getlist('mood_image[]')
        mood_audios = request.files.getlist('mood_audio[]')
        mood_ref_texts = request.form.getlist('mood_ref_text[]')
        
        if not mood_names or len(mood_names) == 0:
            return jsonify({
                'success': False,
                'error': '至少需要一个心情设置'
            }), 400
        
        # 检查角色是否已存在
        character_file_path = Path('characters') / f"{character_id}.py"
        if character_file_path.exists():
            return jsonify({
                'success': False,
                'error': f'角色ID "{character_id}" 已存在'
            }), 400
        
        # 创建角色图片目录
        image_dir = Path('static') / 'images' / character_id
        image_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存头像
        avatar_path = image_dir / 'avatar.png'
        avatar_image.save(str(avatar_path))
        
        # 创建参考音频目录
        ref_audio_dir = Path('data') / 'ref_audio' / character_id
        ref_audio_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存心情图片和参考音频/文本，按顺序命名为1.png, 2.png...和1.wav, 2.wav...
        valid_moods = []
        counter = 1
        for i, name in enumerate(mood_names):
            if name.strip():
                # 保存心情图片
                if i < len(mood_images) and mood_images[i] and mood_images[i].filename:
                    # 强制使用.png格式
                    image_filename = f"{counter}.png"
                    image_path = image_dir / image_filename
                    mood_images[i].save(str(image_path))
                
                # 保存参考音频（如果有）
                if i < len(mood_audios) and mood_audios[i] and mood_audios[i].filename:
                    audio_filename = f"{counter}.wav"
                    audio_path = ref_audio_dir / audio_filename
                    
                    # 如果不是wav格式，转换为wav
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
                                # 如果删除失败，记录但不阻止程序继续
                
                # 保存参考文本（如果有）
                if i < len(mood_ref_texts) and mood_ref_texts[i].strip():
                    text_filename = f"{counter}.txt"
                    text_path = ref_audio_dir / text_filename
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(mood_ref_texts[i].strip())
                
                valid_moods.append(name.strip())
                counter += 1
        
        # 创建角色配置文件，完全按照lingyin.py的格式
        character_file_content = f'''"""
角色配置文件: {character_name}
"""

# 角色基本信息
CHARACTER_ID = "{character_id}"
CHARACTER_NAME = "{character_name}"
CHARACTER_NAME_EN = "{character_english_name}"

# 角色外观
CHARACTER_IMAGE = "static/images/{character_id}"  # 角色立绘目录路径
CALIB = {offset}   # 显示位置的校准值（负值向上移动，正值向下移动）
CHARACTER_COLOR = "{theme_color}"  # 角色名称颜色

# 角色心情
MOODS = {valid_moods}

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
        "color": CHARACTER_COLOR,
        "description": CHARACTER_DESCRIPTION,
        "prompt": CHARACTER_PROMPT,
        "welcome": CHARACTER_WELCOME,
        "examples": CHARACTER_EXAMPLES
    }}
'''
        
        # 保存角色配置文件到characters目录
        with open(character_file_path, 'w', encoding='utf-8') as f:
            f.write(character_file_content)
        
        return jsonify({
            'success': True,
            'message': f'自定义角色 {character_name} 创建成功',
            'character_id': character_id
        })
        
    except Exception as e:
        print(f"创建自定义角色失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'创建失败: {str(e)}'
        }), 500

@app.route('/api/reload-characters', methods=['GET'])
def reload_characters():
    """重新加载角色列表API"""
    try:
        # 清除角色配置缓存
        import characters
        characters._character_configs.clear()
        
        # 重新获取所有可用角色
        available_characters = config_service.list_available_characters()
        
        return jsonify({
            'success': True,
            'characters': available_characters
        })
        
    except Exception as e:
        print(f"重新加载角色列表失败: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'重新加载失败: {str(e)}'
        }), 500

@app.route('/api/tts', methods=['POST'])
def serve_tts():
    global tts
    if not tts.running():
        return jsonify({"error": "语音合成服务未启用/连接失败"}), 400
    data = request.get_json()
    text = data.get("text", "").strip()
    role = data.get("role", "AI助手")
    print(f"请求TTS: 角色={role}, 文本={text}")
    if not text:
        return jsonify({"error": "文本为空"}), 400

    try:
        audio_bytes = tts.get_tts(text, role)  # 应返回 bytes
        if not audio_bytes:
            return jsonify({"error": "TTS生成失败"}), 500

        audio_io = BytesIO(audio_bytes)
        audio_io.seek(0)

        return send_file(
            audio_io,
            mimetype='audio/wav',
            as_attachment=False,
            download_name=None
        )
    except Exception as e:
        print(f"TTS error: {e}")
        return jsonify({"error": "语音合成失败"}), 500

if __name__ == '__main__':
    # 设置系统提示词，使用角色提示词
    chat_service.set_system_prompt("character")
    
    # 启动应用
    app.run(
        host=app_config["host"],
        port=app_config["port"],
        debug=app_config["debug"],
        use_reloader=app_config["debug"]  # 只在debug模式下启用重载器
    )
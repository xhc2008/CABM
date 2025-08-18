
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
    from services.story_service import story_service
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
    # 确保每次进入聊天页面时切换到当前角色（重置上下文/历史/记忆）
    try:
        # 若处于剧情模式，先退出
        if getattr(chat_service, "story_mode", False):
            chat_service.exit_story_mode()
        # 获取并切换到当前角色（会清空内存历史、设置system、初始化记忆并加载该角色历史）
        current_character = chat_service.get_character_config()
        if current_character and "id" in current_character:
            chat_service.set_character(current_character["id"])
            print(f"已切换到角色: {current_character['name']} ({current_character['id']})")
    except Exception as e:
        print(f"进入聊天页切换角色失败: {str(e)}")
        traceback.print_exc()
    
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
        background_url = f"/static/images/cache/{os.path.basename(background)}"
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
                        if chat_service.story_mode and chat_service.current_story_id:
                            # 剧情模式：添加到故事记忆
                            chat_service.memory_service.add_story_conversation(
                                user_message=message,
                                assistant_message=full_response,
                                story_id=chat_service.current_story_id
                            )
                        else:
                            # 普通模式：添加到角色记忆
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

@app.route('/data/saves/<path:filename>')
def serve_story_file(filename):
    """提供故事文件"""
    return send_from_directory('data/saves', filename)

@app.route('/custom_character')
def custom_character_page():
    """自定义角色页面"""
    return render_template('custom_character.html')

@app.route('/story')
def story_page():
    """剧情模式页面"""
    return render_template('story.html')

@app.route('/story/<story_id>')
def story_chat_page(story_id):
    """剧情聊天页面"""
    # 加载故事
    if not story_service.load_story(story_id):
        return f"故事 {story_id} 不存在", 404
    
    # 设置聊天服务为剧情模式
    if not chat_service.set_story_mode(story_id):
        return f"无法设置剧情模式: {story_id}", 500
    
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
        background_url = f"/static/images/cache/{os.path.basename(background)}"
    
    # 获取故事数据
    story_data = story_service.get_current_story_data()
    
    # 获取当前角色配置（应该已经通过set_story_mode设置好了）
    current_character = chat_service.get_character_config()
    
    # 获取应用配置
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

@app.route('/api/stories', methods=['GET'])
def list_stories():
    """获取故事列表API"""
    try:
        stories = story_service.list_stories()
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''
@app.route('/api/stories/create', methods=['POST'])
def create_story():
    """创建新故事API"""
    try:
        # 获取表单数据
        story_id = request.form.get('storyId')
        story_title = request.form.get('storyTitle')
        character_id = request.form.get('selectedCharacterId')
        story_direction = request.form.get('storyDirection')
        
        # 验证必填字段
        if not all([story_id, story_title, character_id, story_direction]):
            return jsonify({
                'success': False,
                'error': '缺少必填字段'
            }), 400
        
        # 验证故事ID格式
        if not re.match(r'^[a-zA-Z0-9_]+$', story_id):
            return jsonify({
                'success': False,
                'error': '故事ID格式不正确'
            }), 400
        
        # 处理背景图片
        background_images = []
        uploaded_files = request.files.getlist('backgroundImages')
        
        if uploaded_files:
            # 创建临时目录保存上传的图片
            import tempfile
            temp_dir = Path(tempfile.mkdtemp())
            
            for i, file in enumerate(uploaded_files):
                if file and file.filename:
                    # 保存到临时文件
                    temp_path = temp_dir / f"bg_{i}.png"
                    file.save(str(temp_path))
                    background_images.append(str(temp_path))
        
        # 创建故事
        success = story_service.create_story(
            story_id=story_id,
            title=story_title,
            character_id=character_id,
            story_direction=story_direction,
            background_images=background_images
        )
        
        # 清理临时文件
        if background_images:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        if success:
            return jsonify({
                'success': True,
                'message': '故事创建成功',
                'story_id': story_id
            })
        else:
            return jsonify({
                'success': False,
                'error': '故事创建失败'
            }), 500
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
'''
@app.route('/api/story/chat', methods=['POST'])
def story_chat():
    """剧情模式聊天API（非流式）"""
    try:
        # 获取请求数据
        data = request.json
        message = data.get('message', '')
        story_id = data.get('story_id', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        if not story_id:
            return jsonify({
                'success': False,
                'error': '故事ID不能为空'
            }), 400
        
        # 加载故事
        if not story_service.load_story(story_id):
            return jsonify({
                'success': False,
                'error': f'故事 {story_id} 不存在'
            }), 404
        
        # 设置剧情模式的聊天服务
        chat_service.set_story_mode(story_id)
        
        # 添加用户消息
        chat_service.add_message("user", message)
        
        # 调用对话API
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
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/story/chat/stream', methods=['POST'])
def story_chat_stream():
    """剧情模式流式聊天API"""
    try:
        # 获取请求数据
        data = request.json
        message = data.get('message', '')
        story_id = data.get('story_id', '')
        
        if not message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        if not story_id:
            return jsonify({
                'success': False,
                'error': '故事ID不能为空'
            }), 400
        
        # 加载故事
        if not story_service.load_story(story_id):
            return jsonify({
                'success': False,
                'error': f'故事 {story_id} 不存在'
            }), 404
        
        # 设置剧情模式的聊天服务
        chat_service.set_story_mode(story_id)
        
        # 添加用户消息
        chat_service.add_message("user", message)
        
        # 创建流式响应生成器
        def generate():
            try:
                # 调用对话API（流式）
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
                            json_start = full_response.rfind('{')
                            if json_start != -1:
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
                                                yield f"data: {json.dumps({'mood': parsed_mood})}\n\n"
                                        
                                        # 处理content字段
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
                                    # 尝试解析不完整的JSON
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
                
                # 将完整消息添加到历史记录
                if full_response:
                    chat_service.add_message("assistant", full_response)
                    
                    # 添加到记忆数据库
                    try:
                        chat_service.memory_service.add_story_conversation(
                            user_message=message,
                            assistant_message=full_response,
                            story_id=story_id
                        )
                    except Exception as e:
                        print(f"添加对话到故事记忆数据库失败: {e}")
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
                        director_result = story_service.call_director_model(chat_history_text)
                        
                        # 处理导演结果
                        story_finished = False
                        if director_result == 0:
                            # 推进到下一章节
                            story_service.update_progress(advance_chapter=True)
                            
                            # 检查是否故事结束
                            if story_service.is_story_finished():
                                print("故事已结束")
                                story_finished = True
                        else:
                            # 增加偏移值
                            story_service.update_progress(offset_increment=director_result)
                        
                        # 获取更新后的故事进度
                        current_idx, current_chapter, next_chapter = story_service.get_current_chapter_info()
                        current_offset = story_service.get_offset()
                        
                        # 发送故事进度更新给前端
                        progress_update = {
                            'storyProgress': {
                                'current': current_idx,
                                'currentChapter': current_chapter,
                                'nextChapter': next_chapter,
                                'offset': current_offset
                            }
                        }
                        
                        if story_finished:
                            progress_update['storyFinished'] = True
                        
                        yield f"data: {json.dumps(progress_update)}\n\n"
                        
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
        
        # 设置响应头
        headers = {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
        
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

@app.route('/api/custom-character', methods=['POST'])
def create_custom_character():
    """创建自定义角色API"""
    try:
        import rtoml
        from utils.env_utils import get_env_var

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

        # 验证缩放率范围
        try:
            scale = int(scale_rate)
            if scale < 1 or scale > 300:
                raise ValueError()
        except ValueError:
            return jsonify({
                'success': False,
                'error': '立绘缩放率必须是1到300之间的整数'
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
        
        # 检查角色是否已存在（同时检查.py和.toml）
        character_py_path = Path('characters') / f"{character_id}.py"
        character_toml_path = Path('characters') / f"{character_id}.toml"
        if character_py_path.exists() or character_toml_path.exists():
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
                
                # 保存参考文本（如果有）
                if i < len(mood_ref_texts) and mood_ref_texts[i].strip():
                    text_filename = f"{counter}.txt"
                    text_path = ref_audio_dir / text_filename
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(mood_ref_texts[i].strip())
                
                valid_moods.append({"name": name.strip()})
                counter += 1

        # 检查是否使用旧版格式
        open_saovc = get_env_var("OPEN_SAOVC", "false").lower() == "true"
        
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
            from services.character_details_service import character_details_service
            
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

@app.route('/api/stories', methods=['GET'])
def get_stories():
    """获取所有存档列表API"""
    try:
        import rtoml
        from pathlib import Path
        
        stories = []
        saves_dir = Path('data/saves')
        
        # 检查存档目录是否存在
        if not saves_dir.exists():
            return jsonify({
                'success': True,
                'stories': []
            })
        
        # 遍历所有存档目录
        for story_dir in saves_dir.iterdir():
            if not story_dir.is_dir():
                continue
                
            story_toml_path = story_dir / 'story.toml'
            if not story_toml_path.exists():
                continue
                
            try:
                # 读取story.toml文件
                with open(story_toml_path, 'r', encoding='utf-8') as f:
                    story_data = rtoml.load(f)
                
                # 获取基本信息
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
                
                # 获取当前进度描述
                current_progress = "未开始"
                if outline and 0 <= current_index < len(outline):
                    current_progress = outline[current_index]
                
                # 获取角色信息（转换ID为名称和颜色）
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
                        characters.append({
                            'id': char_id,
                            'name': char_id,
                            'color': '#ffffff'
                        })
                
                # 获取封面图片URL
                cover_path = story_dir / 'cover.png'
                cover_url = None
                if cover_path.exists():
                    cover_url = f"/api/stories/{story_id}/cover"
                else:
                    # 检查是否有cover.jpg
                    cover_jpg_path = story_dir / 'cover.jpg'
                    if cover_jpg_path.exists():
                        cover_url = f"/api/stories/{story_id}/cover"
                
                # 获取文件夹最近更新时间
                import os
                import datetime
                last_played = None
                try:
                    # 获取目录下所有文件的最新修改时间
                    latest_time = 0
                    for file_path in story_dir.rglob('*'):
                        if file_path.is_file():
                            mtime = file_path.stat().st_mtime
                            if mtime > latest_time:
                                latest_time = mtime
                    
                    if latest_time > 0:
                        last_played = datetime.datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"获取最后游玩时间失败: {e}")
                
                story_info = {
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
                }
                
                stories.append(story_info)
                
            except Exception as e:
                print(f"读取存档 {story_dir.name} 失败: {e}")
                continue
        
        # 按最后游玩时间排序（最近的在前），如果没有则按创建日期排序
        stories.sort(key=lambda x: (x.get('last_played', ''), x.get('create_date', '')), reverse=True)
        
        return jsonify({
            'success': True,
            'stories': stories
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stories/<story_id>/cover')
def get_story_cover(story_id):
    """获取存档封面图片"""
    try:
        from pathlib import Path
        
        story_dir = Path('data/saves') / story_id
        
        # 优先查找cover.png
        cover_path = story_dir / 'cover.png'
        if cover_path.exists():
            return send_file(str(cover_path), mimetype='image/png')
        
        # 其次查找cover.jpg
        cover_jpg_path = story_dir / 'cover.jpg'
        if cover_jpg_path.exists():
            return send_file(str(cover_jpg_path), mimetype='image/jpeg')
        
        # 如果都没有，返回默认图片
        default_cover = Path('static/images/default.svg')
        if default_cover.exists():
            return send_file(str(default_cover), mimetype='image/svg+xml')
        
        return jsonify({
            'success': False,
            'error': '封面图片不存在'
        }), 404
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stories/create', methods=['POST'])
def create_story():
    """创建新故事API"""
    try:
        import rtoml
        from pathlib import Path
        import datetime
        import shutil
        from PIL import Image
        from utils.api_utils import make_api_request
        from config import get_story_prompts
        from utils.env_utils import get_env_var
        
        # 获取表单数据
        story_id = request.form.get('storyId')
        story_title = request.form.get('storyTitle')
        character_id = request.form.get('selectedCharacterId')
        story_direction = request.form.get('storyDirection')
        background_images = request.files.getlist('backgroundImages')
        
        # 验证必填字段
        if not all([story_id, story_title, character_id, story_direction]):
            return jsonify({
                'success': False,
                'error': '缺少必填字段'
            }), 400
        
        # 验证故事ID格式
        if not re.match(r'^[a-zA-Z0-9_]+$', story_id):
            return jsonify({
                'success': False,
                'error': '故事ID格式不正确，只能包含英文字母、数字和下划线'
            }), 400
        
        # 检查故事ID是否已存在
        story_dir = Path('data/saves') / story_id
        if story_dir.exists():
            return jsonify({
                'success': False,
                'error': f'故事ID "{story_id}" 已存在'
            }), 400
        
        # 验证角色是否存在
        character_config = config_service.get_character_config(character_id)
        if not character_config:
            return jsonify({
                'success': False,
                'error': f'角色 "{character_id}" 不存在'
            }), 400
        
        # 创建故事目录
        story_dir.mkdir(parents=True, exist_ok=True)
        backgrounds_dir = story_dir / 'backgrounds'
        backgrounds_dir.mkdir(exist_ok=True)
        
        # 保存背景图片
        cover_created = False
        for i, bg_image in enumerate(background_images, 1):
            if bg_image and bg_image.filename:
                # 保存背景图片
                bg_filename = f"{i}.jpg"
                bg_path = backgrounds_dir / bg_filename
                
                # 转换为JPEG格式
                try:
                    image = Image.open(bg_image)
                    # 如果是RGBA模式，转换为RGB
                    if image.mode == 'RGBA':
                        # 创建白色背景
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
                        image = background
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    image.save(str(bg_path), 'JPEG', quality=85)
                    
                    # 第一张图片作为封面
                    if i == 1 and not cover_created:
                        cover_path = story_dir / 'cover.png'
                        # 创建封面（裁剪为正方形）
                        width, height = image.size
                        size = min(width, height)
                        left = (width - size) // 2
                        top = (height - size) // 2
                        right = left + size
                        bottom = top + size
                        
                        cover_image = image.crop((left, top, right, bottom))
                        cover_image = cover_image.resize((512, 512), Image.Resampling.LANCZOS)
                        cover_image.save(str(cover_path), 'PNG')
                        cover_created = True
                        
                except Exception as e:
                    print(f"处理背景图片失败: {e}")
                    continue
        
        # 创建空白的history.log
        history_path = story_dir / 'history.log'
        history_path.touch()
        
        # 复制角色记忆文件
        memory_source = Path('data/memory') / character_id / f'{character_id}_memory.json'
        memory_target = story_dir / f'{story_id}_memory.json'
        if memory_source.exists():
            shutil.copy2(str(memory_source), str(memory_target))
        else:
            # 如果没有记忆文件，创建空的
            with open(memory_target, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        
        # 获取角色系统提示词
        character_prompt = character_config.get('prompt', '')
        
        # 调用LLM生成故事内容
        try:
            # 构建请求
            api_base_url = get_env_var("CHAT_API_BASE_URL")
            api_key = get_env_var("CHAT_API_KEY")
            model = get_env_var("CHAT_MODEL")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 获取故事生成提示词
            story_prompt = get_story_prompts(character_config.get('name', character_id), character_prompt, story_direction)
            
            request_data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": story_prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.8,
                "stream": False
            }
            
            # 保存调试信息到temp.txt
            debug_info = {
                'timestamp': datetime.datetime.now().isoformat(),
                'story_id': story_id,
                'character_id': character_id,
                'story_direction': story_direction,
                'request': {
                    'url': f"{api_base_url}/chat/completions",
                    'headers': {k: v for k, v in headers.items() if k != 'Authorization'},  # 不保存API密钥
                    'data': request_data
                }
            }
            
            # 发送请求
            response, data = make_api_request(
                url=f"{api_base_url}/chat/completions",
                method="POST",
                headers=headers,
                json_data=request_data,
                timeout=60
            )
            
            # 添加响应到调试信息
            debug_info['response'] = {
                'status_code': response.status_code if response else None,
                'data': data
            }
            
            # 保存调试信息到temp.txt
            try:
                with open('temp.txt', 'w', encoding='utf-8') as f:
                    f.write("=== AI故事生成调试信息 ===\n")
                    f.write(f"时间: {debug_info['timestamp']}\n")
                    f.write(f"故事ID: {debug_info['story_id']}\n")
                    f.write(f"角色ID: {debug_info['character_id']}\n")
                    f.write(f"故事导向: {debug_info['story_direction']}\n\n")
                    
                    f.write("=== 原始请求 ===\n")
                    f.write(json.dumps(debug_info['request'], ensure_ascii=False, indent=2))
                    f.write("\n\n")
                    
                    f.write("=== 原始响应 ===\n")
                    f.write(json.dumps(debug_info['response'], ensure_ascii=False, indent=2))
                    f.write("\n\n")
                    
                    if data and "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        f.write("=== AI生成的内容 ===\n")
                        f.write(content)
                        f.write("\n\n")
            except Exception as debug_e:
                print(f"保存调试信息失败: {debug_e}")
            
            # 解析响应
            if data and "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                
                # 解析JSON响应
                try:
                    # 处理被```包裹的JSON
                    json_content = content.strip()
                    
                    # 移除markdown代码块标记
                    if json_content.startswith('```json'):
                        json_content = json_content[7:]  # 移除```json
                    elif json_content.startswith('```'):
                        json_content = json_content[3:]   # 移除```
                    
                    if json_content.endswith('```'):
                        json_content = json_content[:-3]  # 移除结尾的```
                    
                    json_content = json_content.strip()
                    
                    # 尝试解析JSON
                    story_data = json.loads(json_content)
                    summary = story_data.get('summary', '暂无简介')
                    outline = story_data.get('outline', ['开始'])
                    #outline[0] = "故事开始"
                    outline[-1] = "故事结束"
                    
                    # 在调试文件中添加解析结果
                    try:
                        with open('temp.txt', 'a', encoding='utf-8') as f:
                            f.write("=== JSON解析结果 ===\n")
                            f.write(f"提取的JSON内容: {json_content}\n")
                            f.write(f"解析成功: True\n")
                            f.write(f"故事梗概: {summary}\n")
                            f.write(f"大纲条目数: {len(outline)}\n")
                            f.write(f"大纲前5条: {outline[:5]}\n\n")
                    except Exception:
                        pass
                        
                except json.JSONDecodeError as je:
                    # JSON解析失败，记录错误并使用默认值
                    try:
                        with open('temp.txt', 'a', encoding='utf-8') as f:
                            f.write("=== JSON解析失败 ===\n")
                            f.write(f"错误信息: {str(je)}\n")
                            f.write(f"尝试解析的内容: {json_content if 'json_content' in locals() else content}\n\n")
                    except Exception:
                        pass
                    
                    summary = story_direction
                    outline = ['开始', '发展', '转折', '高潮', '结局']
            else:
                # 如果API调用失败，使用默认值
                summary = story_direction
                outline = ['开始', '发展', '转折', '高潮', '结局']
                
        except Exception as e:
            print(f"LLM生成故事内容失败: {e}")
            # 使用默认值
            summary = story_direction
            outline = ['开始', '发展', '转折', '高潮', '结局']
        
        # 创建story.toml文件
        story_toml_data = {
            'metadata': {
                'story_id': story_id,
                'title': story_title,
                'creator': '用户',
                'create_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'seed': story_direction
            },
            'progress': {
                'current': 0,
                'offset': 0
            },
            'summary': {
                'text': summary
            },
            'structure': {
                'outline': outline
            },
            'characters': {
                'list': [character_id]
            }
        }
        
        # 保存story.toml
        story_toml_path = story_dir / 'story.toml'
        with open(story_toml_path, 'w', encoding='utf-8') as f:
            rtoml.dump(story_toml_data, f)
        
        return jsonify({
            'success': True,
            'message': '故事创建成功',
            'story_id': story_id
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/story/exit', methods=['POST'])
def exit_story_mode():
    """退出剧情模式API"""
    try:
        # 退出剧情模式
        chat_service.exit_story_mode()
        
        return jsonify({
            'success': True,
            'message': '已退出剧情模式'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
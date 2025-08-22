"""CABM应用主文件（重构版）"""
import os
import sys
import mimetypes
from pathlib import Path
from flask import Flask

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.chat_service import chat_service
from services.image_service import image_service
from services.scene_service import scene_service
from services.option_service import option_service
from services.tts_service import get_tts_service
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

# 查看migration文件是否存在
migration_folder = str(Path(__file__).resolve().parent / "migrations")
if not os.path.exists(migration_folder):
    print("旧版记忆开始迁移")
    import migrate_to_faiss
    import migrate_to_peewee
    done_faiss = migrate_to_faiss.main()
    done_peewee = migrate_to_peewee.main()
    if done_faiss and done_peewee:
        print("迁移成功")
    else:
        print("请前往tools\json2index尝试备用迁移")
    with open("migrations", "w") as f:
        f.close()

# 创建Flask应用
app = Flask(
    __name__,
    static_folder=static_folder,
    template_folder=template_folder
)

# 设置JavaScript模块的MIME类型
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')

# 加载并注册插件后端路由和前端资源
from utils.plugin import load_plugins, apply_backend_hooks, apply_frontend_hooks
plugin_folder = str(Path(__file__).resolve().parent / 'utils' / 'plugin')
load_plugins(plugin_folder)
apply_backend_hooks(app)
apply_frontend_hooks(lambda route, path: None)

# 注册各功能蓝图
from routes.chat_routes import chat_bp
from routes.character_routes import character_bp
from routes.story_routes import story_bp
from routes.config_routes import config_bp
from routes.tts_routes import tts_bp

<<<<<<< HEAD
app.register_blueprint(chat_bp)
app.register_blueprint(character_bp)
app.register_blueprint(story_bp)
app.register_blueprint(config_bp)
app.register_blueprint(tts_bp)
=======
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式聊天API - 处理JSON格式响应并支持TTS"""
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
        
        # 获取TTS服务
        tts_service = get_tts_service()
        
        # 创建流式响应生成器
        def generate():
            try:
                # 调用对话API（流式，传递用户查询用于记忆检索）
                stream_gen = chat_service.chat_completion(stream=True, user_query=message)
                full_response = ""
                parsed_mood = None
                parsed_content = ""
                content_buffer = ""  # 用于TTS处理的内容缓冲区
                
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
                                                    content_buffer = new_content
                                                else:
                                                    # 同一个JSON对象的增量更新
                                                    content_diff = new_content[len(parsed_content):]
                                                    if content_diff:
                                                        yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                                        content_buffer += content_diff
                                                    parsed_content = new_content
                                                
                                                # 处理TTS - 检查是否有完整的句子
                                                if tts_service.is_enabled():
                                                    sentences = tts_service.split_sentences(content_buffer)
                                                    if len(sentences) > 1:
                                                        # 处理除最后一个句子外的所有句子
                                                        for sentence in sentences[:-1]:
                                                            if sentence.strip():
                                                                try:
                                                                    audio_path = tts_service.generate_tts_audio(sentence)
                                                                    if audio_path:
                                                                        yield f"data: {json.dumps({'tts': {'text': sentence, 'audio_url': f'/api/audio/{os.path.basename(audio_path)}'}})}\n\n"
                                                                except Exception as e:
                                                                    print(f"TTS生成失败: {e}")
                                                        
                                                        # 保留最后一个句子作为新的buffer
                                                        content_buffer = sentences[-1] if sentences else ""
                                                
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
                                                    content_buffer = current_content
                                                else:
                                                    # 同一个JSON对象的增量更新
                                                    content_diff = current_content[len(parsed_content):]
                                                    if content_diff:
                                                        yield f"data: {json.dumps({'content': content_diff})}\n\n"
                                                        content_buffer += content_diff
                                                    parsed_content = current_content
                                                
                                                # 处理TTS - 检查是否有完整的句子
                                                if tts_service.is_enabled():
                                                    sentences = tts_service.split_sentences(content_buffer)
                                                    if len(sentences) > 1:
                                                        # 处理除最后一个句子外的所有句子
                                                        for sentence in sentences[:-1]:
                                                            if sentence.strip():
                                                                try:
                                                                    audio_path = tts_service.generate_tts_audio(sentence)
                                                                    if audio_path:
                                                                        yield f"data: {json.dumps({'tts': {'text': sentence, 'audio_url': f'/api/audio/{os.path.basename(audio_path)}'}})}\n\n"
                                                                except Exception as e:
                                                                    print(f"TTS生成失败: {e}")
                                                        
                                                        # 保留最后一个句子作为新的buffer
                                                        content_buffer = sentences[-1] if sentences else ""
                                    except Exception:
                                        pass
                                        
                        except Exception as e:
                            print(f"解析JSON响应失败: {e}")
                            # 如果JSON解析失败，尝试作为普通文本处理
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # 处理剩余的TTS内容
                if tts_service.is_enabled() and content_buffer.strip():
                    try:
                        audio_path = tts_service.generate_tts_audio(content_buffer)
                        if audio_path:
                            yield f"data: {json.dumps({'tts': {'text': content_buffer, 'audio_url': f'/api/audio/{os.path.basename(audio_path)}'}})}\n\n"
                    except Exception as e:
                        print(f"最后句子TTS生成失败: {e}")
                            
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
>>>>>>> c77e41f6cfba1a2b802d1d76145879ea594ea91a


# 设置系统提示词，使用角色提示词
if not need_config:
    from services.chat_service import chat_service
    chat_service.set_system_prompt("character")

@app.route('/api/audio/<filename>')
def serve_audio_file(filename):
    """提供TTS音频文件"""
    try:
        tts_service = get_tts_service()
        audio_path = tts_service.get_audio_file_path(filename)
        
        if not audio_path.exists():
            return jsonify({
                'success': False,
                'error': '音频文件不存在'
            }), 404
        
        return send_from_directory(str(audio_path.parent), filename, mimetype='audio/mpeg')
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    if not need_config:
        app.debug = app_config["debug"]
        app.run(
            host=app_config["host"],
            port=app_config["port"],
            debug=app_config["debug"],
            use_reloader=app_config["debug"]
        )
    else:
        app.run()

"""
CABM应用主文件
"""
import os
import sys
import json
import time
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, Response

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.chat_service import chat_service
from services.image_service import image_service
from services.scene_service import scene_service
from services.option_service import option_service
from utils.api_utils import APIError

# 初始化配置
if not config_service.initialize():
    print("配置初始化失败")
    sys.exit(1)

# 获取应用配置
app_config = config_service.get_app_config()

# 创建Flask应用
app = Flask(
    __name__,
    static_folder=app_config["static_folder"],
    template_folder=app_config["template_folder"]
)

# 设置调试模式
app.debug = app_config["debug"]

@app.route('/')
def index():
    """首页"""
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
    
    # 将背景路径转换为URL
    background_url = None
    if background:
        # 从绝对路径转换为相对URL
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
    
    # 渲染模板
    return render_template(
        'index.html',
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
                        
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                error_msg = str(e)
                print(f"流式响应错误: {error_msg}")
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/exit', methods=['POST'])
def exit_app():
    """退出应用API"""
    try:
        # 在实际应用中，这里可能需要清理资源或保存状态
        # 这里简化处理，直接返回成功
        return jsonify({
            'success': True,
            'message': '应用已退出'
        })
        
    except Exception as e:
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
        for filename in os.listdir(full_image_dir):
            if filename.lower().endswith('.png'):
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
        
        return jsonify({
            'success': True,
            'images': image_files,
            'default_image': f"/{image_dir}/1.png"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/data/images/<path:filename>')
def serve_character_image(filename):
    """提供角色图片"""
    return send_from_directory('data/images', filename)

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
"""
CABM应用主文件
"""
import os
import sys
import json
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, Response

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.chat_service import chat_service
from services.image_service import image_service
from services.scene_service import scene_service
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
    character_image_path = os.path.join(app.static_folder, 'images', 'default.png')
    if not os.path.exists(character_image_path):
        print(f"警告: 默认角色图片不存在: {character_image_path}")
        print("请将角色图片放置在 static/images/default.png")
    
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
        
        # 调用对话API
        response = chat_service.chat_completion(stream=False)
        
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
    """流式聊天API - 只负责转发AI响应"""
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
                # 调用对话API（流式）
                stream_gen = chat_service.chat_completion(stream=True)
                full_content = ""
                
                # 逐步返回响应
                for chunk in stream_gen:
                    # 如果是结束标记
                    if chunk.get("done"):
                        # 将完整消息添加到历史记录
                        if full_content:
                            chat_service.add_message("assistant", full_content)
                        yield "data: [DONE]\n\n"
                        break
                    
                    # 处理增量内容
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            full_content += content
                            
                            # 直接转发原始数据，让前端处理
                            yield f"data: {json.dumps({'content': content})}\n\n"
                
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
        port=app_config["port"]
    )
"""
CABM应用主文件
"""
import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, Response

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.chat_service import chat_service
from services.image_service import image_service
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
    
    # 渲染模板
    return render_template(
        'index.html',
        background_url=background_url
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
    """流式聊天API"""
    try:
        # 获取请求数据
        data = request.json
        message = data.get('message', '')
        control_action = data.get('control_action', None)
        
        if not message and not control_action:
            return jsonify({
                'success': False,
                'error': '消息不能为空且未指定控制动作'
            }), 400
        
        # 如果是控制命令
        if control_action:
            # 处理控制命令
            if control_action == "continue":
                # 继续输出
                chat_service.stream_controller.is_paused = False
                
                # 简单返回继续信号，让前端知道可以继续
                return jsonify({
                    'success': True,
                    'action': 'continue'
                })
            elif control_action == "pause":
                # 暂停输出
                chat_service.stream_controller.is_paused = True
                return jsonify({
                    'success': True,
                    'action': 'pause'
                })
            elif control_action == "skip":
                # 跳过当前段落
                return jsonify({
                    'success': True,
                    'action': 'skip'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'未知的控制命令: {control_action}'
                }), 400
        
        # 添加用户消息
        chat_service.add_message("user", message)
        
        # 创建流式响应生成器
        def generate():
            try:
                # 调用对话API（流式）
                stream_gen = chat_service.chat_completion(stream=True)
                
                # 保存流生成器以便继续使用
                chat_service._current_stream_gen = stream_gen
                
                # 逐步返回响应
                for chunk in stream_gen:
                    # 如果是结束标记
                    if chunk.get("done"):
                        # 添加完成标记
                        yield f"data: {json.dumps({'stream_control': {'is_complete': True}})}\n\n"
                        yield "data: [DONE]\n\n"
                        # 清除保存的流生成器
                        chat_service._current_stream_gen = None
                        break
                    
                    # 检查是否有控制信息
                    if "stream_control" in chunk:
                        # 如果段落完成且需要暂停
                        if chunk["stream_control"].get("paragraph_complete") and chunk["stream_control"].get("pause"):
                            # 添加暂停标记
                            chunk["stream_control"]["status"] = "paused"
                    
                    # 转发流式数据
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # 如果需要暂停，停止当前流式响应
                    if "stream_control" in chunk and chunk["stream_control"].get("status") == "paused":
                        break
                
            except Exception as e:
                error_msg = str(e)
                print(f"流式响应错误: {error_msg}")
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                yield "data: [DONE]\n\n"
                # 清除保存的流生成器
                chat_service._current_stream_gen = None
        
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

if __name__ == '__main__':
    # 设置系统提示词
    chat_service.set_system_prompt()
    
    # 启动应用
    app.run(
        host=app_config["host"],
        port=app_config["port"]
    )
# -*- coding: utf-8 -*-
"""
背景管理路由
"""
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# 动态计算项目根目录
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.image_service import image_service

bp = Blueprint('background', __name__, url_prefix='/api/background')

@bp.route('/list', methods=['GET'])
def get_backgrounds():
    """获取所有背景列表"""
    try:
        backgrounds = image_service.get_all_backgrounds()
        return jsonify({
            'success': True,
            'backgrounds': backgrounds
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/add', methods=['POST'])
def add_background():
    """添加新背景（不上传文件，使用AI生成或创建占位图）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        name = data.get('name', '').strip()
        desc = data.get('desc', '').strip()
        prompt = data.get('prompt', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': '背景名称不能为空'
            }), 400
        
        # 这里不会重复调用AI生成，逻辑已在image_service中处理
        result = image_service.add_background(
            name=name,
            desc=desc,
            prompt=prompt
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/upload', methods=['POST'])
def upload_background():
    """上传背景图片"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 获取表单数据
        name = request.form.get('name', '').strip()
        desc = request.form.get('desc', '').strip()
        prompt = request.form.get('prompt', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': '背景名称不能为空'
            }), 400
        
        # 读取文件数据
        file_data = file.read()
        original_filename = secure_filename(file.filename)
        
        result = image_service.upload_background_image(
            file_data=file_data,
            original_filename=original_filename,
            name=name,
            desc=desc,
            prompt=prompt
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/delete/<filename>', methods=['DELETE'])
def delete_background(filename):
    """删除背景"""
    try:
        result = image_service.delete_background(filename)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/info/<filename>', methods=['GET'])
def get_background_info(filename):
    """获取背景详细信息"""
    try:
        info = image_service.get_background_info(filename)
        
        if info:
            return jsonify({
                'success': True,
                'info': info,
                'filename': filename,
                'url': image_service.get_background_url(filename)
            })
        else:
            return jsonify({
                'success': False,
                'error': '背景不存在'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/update/<filename>', methods=['PUT'])
def update_background(filename):
    """更新背景信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        name = data.get('name')
        desc = data.get('desc')
        prompt = data.get('prompt')
        
        result = image_service.update_background_info(
            filename=filename,
            name=name,
            desc=desc,
            prompt=prompt
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/select', methods=['POST'])
def select_background():
    """选择背景"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        filename = data.get('filename')
        if not filename:
            return jsonify({
                'success': False,
                'error': '背景文件名不能为空'
            }), 400
        
        # 检查背景是否存在
        info = image_service.get_background_info(filename)
        if not info:
            return jsonify({
                'success': False,
                'error': '背景不存在'
            }), 404
        
        # 返回背景URL和提示词
        background_url = image_service.get_background_url(filename)
        
        return jsonify({
            'success': True,
            'background_url': background_url,
            'prompt': info.get('prompt', ''),
            'name': info.get('name', ''),
            'message': f'已切换到背景: {info.get("name", filename)}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/initial', methods=['POST'])
def get_initial_background():
    """获取初始背景"""
    try:
        # 可以根据角色ID或故事ID选择合适的背景
        # 这里先返回随机背景
        filename = image_service.get_random_background()
        
        if filename:
            info = image_service.get_background_info(filename)
            background_url = image_service.get_background_url(filename)
            
            return jsonify({
                'success': True,
                'background_url': background_url,
                'prompt': info.get('prompt', '') if info else '',
                'name': info.get('name', '') if info else '',
                'filename': filename
            })
        else:
            return jsonify({
                'success': False,
                'error': '没有可用的背景'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/stats', methods=['GET'])
def get_background_stats():
    """获取背景统计信息"""
    try:
        stats = image_service.get_background_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 兼容旧的API路径
@bp.route('s', methods=['GET'])
def get_backgrounds_legacy():
    """兼容旧的API路径 /api/backgrounds"""
    return get_backgrounds()
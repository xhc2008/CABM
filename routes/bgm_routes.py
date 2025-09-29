# -*- coding: utf-8 -*-
"""
BGM 相关路由
"""
import os
from pathlib import Path
from flask import Blueprint, send_from_directory, jsonify, current_app, request
from werkzeug.utils import secure_filename
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint('bgm', __name__, url_prefix='')

def get_bgm_routes(bp):
    """获取BGM路由函数"""
    
    @bp.route('/api/bgm-tracks', methods=['GET'])
    def get_bgm_tracks():
        """获取可用的BGM音轨列表"""
        try:
            # 获取BGM文件夹路径
            bgm_folder = Path(current_app.root_path) / 'static' / 'bgm'
            
            # 确保文件夹存在
            if not bgm_folder.exists():
                logger.warning(f"BGM文件夹不存在: {bgm_folder}")
                return jsonify([])
            
            # 获取所有音频文件
            audio_extensions = {'.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac'}
            audio_files = []
            
            for file in bgm_folder.iterdir():
                if file.is_file() and file.suffix.lower() in audio_extensions:
                    audio_files.append(file.name)
            
            logger.info(f"找到 {len(audio_files)} 个BGM文件: {audio_files}")
            return jsonify(audio_files)
            
        except Exception as e:
            logger.error(f"获取BGM列表时出错: {str(e)}")
            return jsonify(["bgm01.aac"])  # 默认回退
    
    @bp.route('/static/bgm/<path:filename>')
    def serve_bgm_file(filename):
        """提供BGM音频文件"""
        try:
            # 安全检查：防止路径遍历攻击
            if '..' in filename or filename.startswith('/'):
                return "无效的文件名", 400
                
            bgm_folder = Path(current_app.root_path) / 'static' / 'bgm'
            return send_from_directory(str(bgm_folder), filename)
            
        except Exception as e:
            logger.error(f"提供BGM文件时出错: {filename}, 错误: {str(e)}")
            return "文件未找到", 404
    
    @bp.route('/api/bgm-tracks/<filename>', methods=['DELETE'])
    def delete_bgm_track(filename):
        """删除BGM音轨文件"""
        try:
            # 安全检查：防止路径遍历攻击
            if '..' in filename or filename.startswith('/') or '/' in filename:
                return jsonify({"success": False, "message": "无效的文件名"}), 400
            
            bgm_folder = Path(current_app.root_path) / 'static' / 'bgm'
            file_path = bgm_folder / filename
            
            # 检查文件是否存在
            if not file_path.exists():
                return jsonify({"success": False, "message": "文件不存在"}), 404
            
            # 删除文件
            file_path.unlink()
            logger.info(f"成功删除BGM文件: {filename}")
            
            return jsonify({"success": True, "message": "文件删除成功"})
            
        except Exception as e:
            logger.error(f"删除BGM文件时出错: {filename}, 错误: {str(e)}")
            return jsonify({"success": False, "message": f"删除失败: {str(e)}"}), 500
    
    @bp.route('/api/bgm-tracks/upload', methods=['POST'])
    def upload_bgm_track():
        """上传BGM音轨文件"""
        try:
            # 检查是否有文件
            if 'file' not in request.files:
                return jsonify({"success": False, "message": "没有选择文件"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"success": False, "message": "没有选择文件"}), 400
            
            # 检查文件扩展名
            allowed_extensions = {'.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac'}
            filename = secure_filename(file.filename)
            file_ext = Path(filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                return jsonify({
                    "success": False, 
                    "message": f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
                }), 400
            
            # 确保BGM文件夹存在
            bgm_folder = Path(current_app.root_path) / 'static' / 'bgm'
            bgm_folder.mkdir(parents=True, exist_ok=True)
            
            # 检查文件是否已存在
            file_path = bgm_folder / filename
            if file_path.exists():
                return jsonify({"success": False, "message": "文件已存在"}), 409
            
            # 保存文件
            file.save(str(file_path))
            logger.info(f"成功上传BGM文件: {filename}")
            
            return jsonify({"success": True, "message": "文件上传成功", "filename": filename})
            
        except Exception as e:
            logger.error(f"上传BGM文件时出错: {str(e)}")
            return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500

    return bp

# 创建并配置蓝图
bp = get_bgm_routes(bp)
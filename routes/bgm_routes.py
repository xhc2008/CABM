# -*- coding: utf-8 -*-
"""
BGM 相关路由
"""
import os
from pathlib import Path
from flask import Blueprint, send_from_directory, jsonify, current_app
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

    return bp

# 创建并配置蓝图
bgm_bp = get_bgm_routes(bp)
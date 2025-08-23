# -*- coding: utf-8 -*-
"""
杂项路由
"""
import sys
from pathlib import Path
from flask import Blueprint, render_template

# 动态计算项目根目录
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

bp = Blueprint('misc', __name__, url_prefix='')

@bp.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html')

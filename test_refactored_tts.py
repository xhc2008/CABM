#!/usr/bin/env python3
"""
测试重构后的流式TTS服务
"""
import sys
import json
import base64
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.
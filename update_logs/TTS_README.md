# TTS语音合成功能说明

## 功能概述

本项目已成功集成TTS（Text-to-Speech）语音合成功能，支持将AI助手的回复转换为语音并在前端播放。

## 功能特点

### 后端功能
- **智能分句**: 参考`stream_processor.js`的分割逻辑，按照标点符号（。？！…~）自动分割句子
- **流式处理**: 每接收到一个完整句子就立即生成TTS音频
- **音频缓存**: 使用MD5哈希避免重复生成相同内容的音频
- **文件管理**: 所有音频文件存储在`data/audio/`目录下

### 前端功能
- **音频队列**: 音频按顺序排队播放
- **并行处理**: 音频播放与文本输出并行进行
- **智能中断**: 用户点击屏幕时中断当前音频，播放下一段
- **跳过功能**: 支持跳过所有音频播放

## 配置说明

### 环境变量配置（.env文件）
```env
# TTS语音合成API配置
TTS_API_BASE_URL=https://api.siliconflow.cn/v1
TTS_API_KEY=your_api_key_here
TTS_MODEL=FunAudioLLM/CosyVoice2-0.5B
TTS_VOICE=中文女
ENABLE_TTS=True
```

### 应用配置（config.py）
```python
# TTS语音合成配置
TTS_CONFIG = {
    "model": get_env_var("TTS_MODEL", "FunAudioLLM/CosyVoice2-0.5B"),  # TTS模型
    "voice": get_env_var("TTS_VOICE", "中文女"),  # 音色
    "response_format": "mp3",       # 音频格式
    "audio_dir": "data/audio",      # 音频存储目录
    "enable_tts": get_env_var("ENABLE_TTS", "True").lower() == "true",  # 是否启用TTS
}
```

## 使用方法

1. **启用TTS**: 确保`.env`文件中`ENABLE_TTS=True`
2. **配置API**: 设置正确的API密钥和音色
3. **启动应用**: 运行`python app.py`
4. **开始对话**: 在前端发送消息，AI回复会自动生成语音

## 交互说明

- **自动播放**: AI回复时会自动按句子顺序播放语音
- **点击继续**: 点击屏幕任意位置可跳到下一句语音
- **跳过音频**: 点击"跳过"按钮停止所有音频播放
- **并行输出**: 语音播放不会阻塞文本显示

## 技术实现

### 后端处理流程
1. 接收流式文本内容
2. 按标点符号分割句子
3. 为每个完整句子生成TTS音频
4. 将音频URL发送给前端

### 前端处理流程
1. 接收TTS音频数据
2. 添加到音频播放队列
3. 按顺序播放音频
4. 支持用户交互中断

## 文件结构

```
├── services/
│   └── tts_service.py          # TTS服务实现
├── data/
│   └── audio/                  # 音频文件存储目录
├── static/js/
│   └── main.js                 # 前端音频播放逻辑
├── config.py                   # TTS配置
├── .env                        # 环境变量
└── test_tts.py                 # TTS功能测试脚本
```

## 测试

运行测试脚本验证TTS功能：
```bash
python test_tts.py
```

## 注意事项

1. **API配额**: TTS API调用会消耗配额，请合理使用
2. **音频格式**: 目前支持MP3格式
3. **浏览器兼容**: 需要支持HTML5 Audio API的现代浏览器
4. **网络要求**: 需要稳定的网络连接来访问TTS API

## 故障排除

1. **403错误**: 检查API密钥和音色配置是否正确
2. **音频不播放**: 检查浏览器是否支持音频自动播放
3. **文件不存在**: 确保`data/audio/`目录存在且有写入权限
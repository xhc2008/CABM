# 增强版TTS功能 - 支持情感分析和动态参考音频

## 概述

本次更新为CABM项目添加了增强的TTS（文本转语音）功能，支持基于BERT的情感分析和动态参考音频选择。该功能能够根据文本内容自动分析情感，并选择相应的参考音频来生成更自然的语音。

## 主要特性

### 1. 情感分析
- 基于BERT模型的情感分析
- 支持15种情感类型：高兴、悲伤、愤怒、惊讶、恐惧、厌恶、中性、害羞、兴奋、舒适、紧张、爱慕、委屈、骄傲、困惑
- 按需加载角色特定的BERT模型

### 2. 动态参考音频选择
- 根据检测到的情感自动选择相应的参考音频
- 支持多情感参考音频目录结构
- 自动回退到默认参考音频

### 3. 角色配置增强
- 支持角色特定的BERT模型
- 支持角色特定的多情感参考音频
- 灵活的配置文件结构

## 目录结构

```
GPT-SoVITS/
├── role/
│   ├── 角色名1/
│   │   ├── config.json          # 角色配置文件
│   │   ├── reference.wav        # 默认参考音频
│   │   ├── BERT/                # 可选：自定义文本情感分析模型
│   │   ├── refAudio/            # 可选：自定义多情感参考音频
│   │   │   ├── 高兴/
│   │   │   ├── 悲伤/
│   │   │   ├── 愤怒/
│   │   │   └── ...
│   │   ├── character-gpt.ckpt   # 可选：自定义GPT模型
│   │   └── character-sovits.pth # 可选：自定义SoVITS模型
│   └── ...
├── api_v2.py                    # 增强版API
└── ...
```

## 配置文件格式

### config.json 示例
```json
{
    "ref_audio": "reference.wav",
    "ref_text": "骇入空间站的时候，我随手改了下螺丝咕姆的画像，不过…最后还是改回去了。",
    "ref_lang": "zh",
    "BERTmodel": "BERT/",
    "multiREF": "refAudio/"
}
```

### 配置参数说明
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| ref_audio | string | ✓ | 默认参考音频文件名 |
| ref_text | string | ✓ | 默认参考音频对应的文本内容 |
| ref_lang | string | ✓ | 参考文本语言（zh/en/ja等） |
| BERTmodel | string | ✗ | BERT模型目录路径 |
| multiREF | string | ✗ | 多情感参考音频目录路径 |

## API端点

### 1. 标准TTS端点
- **URL**: `POST /tts`
- **功能**: 自动情感分析 + 动态参考音频选择
- **请求格式**:
```json
{
    "text": "要合成的文本",
    "role": "角色名",
    "temperature": 1.0
}
```

### 2. 增强版TTS端点
- **URL**: `POST /tts_enhanced`
- **功能**: 支持手动指定情感
- **请求格式**:
```json
{
    "text": "要合成的文本",
    "role": "角色名",
    "temperature": 1.0,
    "emotion": "高兴"  // 可选，手动指定情感
}
```

### 3. 情感分析状态端点
- **URL**: `GET /emotion_status`
- **功能**: 获取已加载的BERT模型状态
- **返回格式**:
```json
{
    "bert_loaded": true,
    "loaded_roles": ["银狼"],
    "total_loaded": 1,
    "device": "CUDA",
    "available_emotions": ["高兴", "悲伤", "愤怒", ...]
}
```

## 使用方法

### 1. 启动服务
```bash
cd GPT-SoVITS
python api_v2.py -a 127.0.0.1 -p 9880
```

### 2. 测试API
```bash
# 使用测试脚本
python test_tts_endpoint.py
```

### 3. 客户端调用示例
```python
import requests

# 标准TTS调用
response = requests.post("http://127.0.0.1:9880/tts", json={
    "text": "你好，我是银狼！",
    "role": "银狼",
    "temperature": 1.0
})

# 增强版TTS调用（指定情感）
response = requests.post("http://127.0.0.1:9880/tts_enhanced", json={
    "text": "我很高兴见到你！",
    "role": "银狼",
    "emotion": "高兴",
    "temperature": 1.0
})
```

## 技术实现

### 1. 情感分析器 (EmotionAnalyzer)
- 按需加载角色特定的BERT模型
- 支持15种情感分类
- 自动设备检测（CUDA/CPU）

### 2. 参考音频管理器
- 动态路径构建
- 情感目录自动发现
- 回退机制（中性情感作为备选）

### 3. API增强
- 保持向后兼容性
- 新增增强版端点
- 完善的错误处理

## 依赖要求

- Python 3.9+
- transformers >= 4.30.0
- torch >= 2.0.0
- fastapi
- uvicorn
- requests

## 注意事项

1. **BERT模型**: 每个角色的BERT模型需要单独训练和配置
2. **参考音频**: 建议每个情感至少准备一个高质量的参考音频
3. **性能**: 首次加载BERT模型可能需要一些时间
4. **内存**: 多个BERT模型会占用较多内存

## 更新日志

- **v1.0.0**: 初始版本，支持基础情感分析和动态参考音频选择
- 添加了BERT情感分析功能
- 添加了多情感参考音频支持
- 添加了增强版API端点
- 完善了错误处理和日志记录

## 贡献者

- 实现了基于BERT的情感分析
- 添加了动态参考音频选择功能
- 增强了API的灵活性和易用性 
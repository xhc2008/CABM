#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from replace.ttsapi_service import ttsService, emotion_analyzer

def test_emotion_analysis():
    """测试情感分析功能"""
    print("=== 测试情感分析功能 ===")
    
    # 测试文本
    test_texts = [
        "我很高兴见到你！",
        "这真是太糟糕了，我很伤心。",
        "你怎么能这样对我！我很生气！",
        "哇，这真是太令人惊讶了！",
        "我害怕黑暗。",
        "我讨厌这个味道。",
        "今天天气不错。",
        "我有点害羞。",
        "太棒了！我太兴奋了！",
        "这里很舒服。",
        "我有点紧张。",
        "我爱你。",
        "我觉得很委屈。",
        "我为自己感到骄傲。",
        "我不太明白。"
    ]
    
    role = "银狼"
    role_path = Path("replace/role/银狼")
    
    for text in test_texts:
        emotion = emotion_analyzer.predict_emotion(text, role, role_path)
        print(f"文本: '{text}' -> 情感: {emotion}")

def test_tts_service():
    """测试TTS服务"""
    print("\n=== 测试TTS服务 ===")
    
    try:
        # 初始化TTS服务
        tts = ttsService()
        print("✅ TTS服务初始化成功")
        
        # 打印已加载的角色情感音色
        if hasattr(tts, 'role_emotion_voices'):
            print(f"已加载的角色情感音色:")
            for role, emotions in tts.role_emotion_voices.items():
                print(f"  角色: {role}")
                for emotion, uri in emotions.items():
                    print(f"    {emotion}: {uri}")
        
        # 测试不同情感的文本
        test_cases = [
            ("银狼", "我很高兴见到你！"),
            ("银狼", "这真是太糟糕了，我很伤心。"),
            ("银狼", "你怎么能这样对我！我很生气！"),
            ("银狼", "今天天气不错。"),
        ]
        
        for role, text in test_cases:
            print(f"\n测试角色: {role}, 文本: '{text}'")
            try:
                # 这里只是测试逻辑，不实际调用API
                if role in getattr(tts, 'role_emotion_voices', {}):
                    role_path = Path("replace/role") / role
                    emotion = emotion_analyzer.predict_emotion(text, role, role_path)
                    print(f"  检测到情感: {emotion}")
                    
                    if emotion in tts.role_emotion_voices[role]:
                        print(f"  ✅ 找到对应的情感音色")
                    else:
                        print(f"  ⚠️ 未找到对应的情感音色，将使用中性音色")
                else:
                    print(f"  ⚠️ 角色 {role} 没有情感音色配置")
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                
    except Exception as e:
        print(f"❌ TTS服务初始化失败: {e}")

def test_role_structure():
    """测试角色目录结构"""
    print("\n=== 测试角色目录结构 ===")
    
    role_dir = Path("replace/role")
    if not role_dir.exists():
        print(f"❌ 角色目录不存在: {role_dir}")
        return
    
    for role_path in role_dir.iterdir():
        if not role_path.is_dir() or role_path.name.startswith('.'):
            continue
        
        role_name = role_path.name
        print(f"\n角色: {role_name}")
        
        # 检查BERT模型
        bert_path = role_path / "BERT"
        if bert_path.exists():
            print(f"  ✅ BERT模型存在: {bert_path}")
        else:
            print(f"  ⚠️ BERT模型不存在: {bert_path}")
        
        # 检查refAudio目录
        ref_audio_path = role_path / "refAudio"
        if ref_audio_path.exists():
            print(f"  ✅ refAudio目录存在: {ref_audio_path}")
            
            # 检查情感目录
            emotion_count = 0
            for emotion_dir in ref_audio_path.iterdir():
                if emotion_dir.is_dir() and not emotion_dir.name.startswith('.'):
                    wav_files = list(emotion_dir.glob("*.wav"))
                    print(f"    情感: {emotion_dir.name} ({len(wav_files)} 个音频文件)")
                    emotion_count += 1
            
            print(f"  总共 {emotion_count} 个情感目录")
        else:
            print(f"  ⚠️ refAudio目录不存在: {ref_audio_path}")

if __name__ == "__main__":
    print("开始测试情感TTS功能...\n")
    
    # 测试角色目录结构
    test_role_structure()
    
    # 测试情感分析
    test_emotion_analysis()
    
    # 测试TTS服务
    test_tts_service()
    
    print("\n测试完成！") 
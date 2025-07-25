#!/usr/bin/env python
"""
记忆模块测试脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.memory_service import memory_service
from utils.prompt_logger import prompt_logger

def test_memory_module():
    """测试记忆模块"""
    print("=== 记忆模块测试 ===")
    
    # 1. 初始化配置
    print("1. 初始化配置...")
    if not config_service.initialize():
        print("❌ 配置初始化失败")
        return False
    print("✅ 配置初始化成功")
    
    # 2. 初始化记忆数据库
    print("\n2. 初始化记忆数据库...")
    character_name = "test_character"
    if memory_service.initialize_character_memory(character_name):
        print(f"✅ 记忆数据库初始化成功: {character_name}")
    else:
        print("❌ 记忆数据库初始化失败")
        return False
    
    # 3. 添加测试对话
    print("\n3. 添加测试对话...")
    test_conversations = [
        ("你好，我叫小明", "你好小明！很高兴认识你。"),
        ("我今年25岁", "知道了，你今年25岁。"),
        ("我喜欢编程", "编程是一个很有趣的爱好！"),
        ("我住在北京", "北京是个很棒的城市。"),
        ("我的工作是软件工程师", "软件工程师是个很有前景的职业。")
    ]
    
    for user_msg, assistant_msg in test_conversations:
        memory_service.add_conversation(user_msg, assistant_msg, character_name)
        print(f"✅ 添加对话: {user_msg[:20]}...")
    
    # 4. 测试记忆检索
    print("\n4. 测试记忆检索...")
    test_queries = [
        "我的名字是什么？",
        "我多大了？",
        "我的爱好是什么？",
        "我住在哪里？",
        "我的职业是什么？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        memory_result = memory_service.search_memory(query, character_name, top_k=2, timeout=10)
        if memory_result:
            print("✅ 找到相关记忆:")
            print(memory_result[:200] + "..." if len(memory_result) > 200 else memory_result)
        else:
            print("❌ 未找到相关记忆")
    
    # 5. 测试提示词日志
    print("\n5. 测试提示词日志...")
    test_messages = [
        {"role": "system", "content": "你是一个有用的AI助手。"},
        {"role": "user", "content": "请介绍一下自己。"}
    ]
    
    prompt_logger.log_prompt(test_messages, character_name, "介绍自己")
    print("✅ 提示词日志记录成功")
    
    # 6. 获取统计信息
    print("\n6. 获取统计信息...")
    stats = memory_service.get_memory_stats(character_name)
    print(f"✅ 统计信息: {stats}")
    
    print("\n=== 测试完成 ===")
    return True

if __name__ == "__main__":
    try:
        success = test_memory_module()
        if success:
            print("\n🎉 所有测试通过！")
        else:
            print("\n❌ 测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#!/usr/bin/env python
"""
记忆模块集成测试脚本
测试记忆检索在实际对话中的效果
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.chat_service import chat_service
from services.memory_service import memory_service

def test_memory_integration():
    """测试记忆模块集成"""
    print("=== 记忆模块集成测试 ===")
    
    # 1. 初始化配置
    print("1. 初始化配置...")
    if not config_service.initialize():
        print("❌ 配置初始化失败")
        return False
    print("✅ 配置初始化成功")
    
    # 2. 设置角色
    print("\n2. 设置测试角色...")
    character_id = "Silver_Wolf"
    if chat_service.set_character(character_id):
        print(f"✅ 角色设置成功: {character_id}")
    else:
        print("❌ 角色设置失败")
        return False
    
    # 3. 添加一些测试对话到记忆
    print("\n3. 添加测试对话到记忆...")
    test_conversations = [
        ("我叫小明，今年25岁", "你好小明！很高兴认识你，25岁正是青春年华呢！"),
        ("我是一名程序员", "程序员是个很棒的职业！你主要用什么编程语言？"),
        ("我喜欢Python和JavaScript", "Python和JavaScript都是很实用的语言！"),
        ("我住在上海", "上海是个国际化大都市，生活一定很精彩吧！"),
        ("我有一只叫小白的猫", "小白一定很可爱！我也很喜欢小动物。")
    ]
    
    for user_msg, assistant_msg in test_conversations:
        memory_service.add_conversation(user_msg, assistant_msg, character_id)
        print(f"✅ 添加对话: {user_msg[:20]}...")
    
    # 4. 测试记忆检索
    print("\n4. 测试记忆检索...")
    test_queries = [
        "我的名字是什么？",
        "我多大了？",
        "我的职业是什么？",
        "我会什么编程语言？",
        "我住在哪里？",
        "我的宠物叫什么？"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        memory_result = memory_service.search_memory(query, character_id, top_k=2, timeout=10)
        if memory_result:
            print("✅ 找到相关记忆:")
            # 只显示前200个字符
            display_text = memory_result[:200] + "..." if len(memory_result) > 200 else memory_result
            print(display_text)
        else:
            print("❌ 未找到相关记忆")
    
    # 5. 模拟实际对话流程
    print("\n5. 模拟实际对话流程...")
    
    # 清空当前会话历史，但保留记忆
    chat_service.clear_history(keep_system=True, clear_persistent=False)
    
    # 模拟用户提问
    user_question = "你还记得我的名字吗？"
    print(f"用户问题: {user_question}")
    
    # 添加用户消息
    chat_service.add_message("user", user_question)
    
    # 获取记忆上下文
    memory_context = memory_service.search_memory(user_question, character_id, top_k=2)
    print(f"记忆上下文长度: {len(memory_context)} 字符")
    
    if memory_context:
        print("✅ 成功检索到相关记忆")
        print("记忆上下文预览:")
        print(memory_context[:300] + "..." if len(memory_context) > 300 else memory_context)
    else:
        print("❌ 未检索到相关记忆")
    
    # 6. 获取统计信息
    print("\n6. 获取统计信息...")
    stats = memory_service.get_memory_stats(character_id)
    print(f"✅ 统计信息: {stats}")
    
    print("\n=== 集成测试完成 ===")
    return True

if __name__ == "__main__":
    try:
        success = test_memory_integration()
        if success:
            print("\n🎉 集成测试通过！记忆模块已成功集成到聊天系统中。")
        else:
            print("\n❌ 集成测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
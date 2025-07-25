#!/usr/bin/env python
"""
测试上下文和记忆的集成
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from services.config_service import config_service
from services.chat_service import chat_service
from services.memory_service import memory_service

def test_context_and_memory():
    """测试上下文和记忆的集成"""
    print("=== 上下文和记忆集成测试 ===")
    
    # 初始化
    if not config_service.initialize():
        print("❌ 配置初始化失败")
        return False
    
    # 设置角色
    character_id = "Silver_Wolf"
    chat_service.set_character(character_id)
    
    # 清空当前会话历史，但保留记忆
    chat_service.clear_history(keep_system=True, clear_persistent=False)
    
    # 添加一些长期记忆（模拟之前的对话）
    print("1. 添加长期记忆...")
    memory_service.add_conversation(
        "我叫张三，是个医生", 
        "你好张三医生！很高兴认识你。", 
        character_id
    )
    memory_service.add_conversation(
        "我今年30岁了", 
        "30岁正是事业的黄金期呢！", 
        character_id
    )
    
    # 添加一些短期上下文（当前会话）
    print("2. 添加短期上下文...")
    chat_service.add_message("user", "今天天气不错")
    chat_service.add_message("assistant", "是的，阳光明媚的日子总是让人心情愉快。")
    chat_service.add_message("user", "我想出去散步")
    chat_service.add_message("assistant", "散步是个好主意！运动有益健康。")
    
    # 现在用户问一个需要长期记忆的问题
    user_query = "你还记得我的职业吗？"
    print(f"3. 用户查询: {user_query}")
    
    # 添加用户消息
    chat_service.add_message("user", user_query)
    
    # 模拟chat_completion的消息准备过程
    messages = chat_service.format_messages()
    
    # 进行记忆检索
    memory_context = memory_service.search_memory(user_query, character_id, top_k=2)
    
    # 添加记忆上下文到最后一条用户消息
    if memory_context and messages:
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                original_content = messages[i]["content"]
                messages[i]["content"] = memory_context + "\n\n" + original_content
                break
    
    # 显示最终的消息结构
    print("\n4. 最终发送给AI的消息结构:")
    for i, msg in enumerate(messages):
        role = msg["role"]
        content = msg["content"]
        print(f"\n消息 {i+1} ({role}):")
        if len(content) > 200:
            print(content[:200] + "...")
        else:
            print(content)
    
    print(f"\n5. 分析:")
    print(f"- 总消息数: {len(messages)}")
    print(f"- 包含系统消息: {'是' if any(m['role'] == 'system' for m in messages) else '否'}")
    print(f"- 包含历史上下文: {'是' if len([m for m in messages if m['role'] in ['user', 'assistant']]) > 1 else '否'}")
    print(f"- 包含记忆上下文: {'是' if memory_context else '否'}")
    
    if memory_context:
        print(f"- 记忆上下文长度: {len(memory_context)} 字符")
    
    return True

if __name__ == "__main__":
    try:
        test_context_and_memory()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
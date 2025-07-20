"""
对话服务测试脚本
"""
import sys
import json
from services.config_service import config_service
from services.chat_service import chat_service
from utils.api_utils import APIError

def test_chat_service():
    """测试对话服务"""
    print("正在测试对话服务...")
    
    # 初始化配置
    if not config_service.initialize():
        print("配置初始化失败")
        return False
    
    try:
        # 设置系统提示词
        chat_service.set_system_prompt("friendly")
        print("已设置系统提示词: friendly")
        
        # 添加用户消息
        user_message = "你好，请用一句话介绍一下自己"
        chat_service.add_message("user", user_message)
        print(f"已添加用户消息: {user_message}")
        
        # 调用API（非流式）
        print("\n发送API请求...")
        response = chat_service.chat_completion(stream=False)
        
        # 打印响应
        print("\nAPI响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        
        # 打印对话历史
        print("\n对话历史:")
        for msg in chat_service.get_history():
            print(f"{msg.role}: {msg.content[:100]}...")
        
        # 测试清空历史
        chat_service.clear_history(keep_system=True)
        print("\n已清空对话历史（保留系统提示词）")
        print(f"当前历史记录长度: {len(chat_service.get_history())}")
        
        # 测试流式响应
        print("\n测试流式响应...")
        chat_service.add_message("user", "请用三个词形容你自己")
        
        print("接收流式响应:")
        stream_gen = chat_service.chat_completion(stream=True)
        
        for chunk in stream_gen:
            if chunk.get("done"):
                print("[流式响应结束]")
                break
                
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    print(delta["content"], end="", flush=True)
        
        print("\n\n测试完成!")
        return True
        
    except APIError as e:
        print(f"\nAPI错误: {e.message}")
        if hasattr(e, "response") and e.response:
            print(f"详细信息: {e.response}")
        return False
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    if test_chat_service():
        print("\n对话服务测试成功!")
        sys.exit(0)
    else:
        print("\n对话服务测试失败!")
        sys.exit(1)
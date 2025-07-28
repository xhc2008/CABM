#!/usr/bin/env python3
"""
测试选项生成功能
"""
import requests
import json
import time

def test_option_generation():
    """测试选项生成功能"""
    base_url = "http://127.0.0.1:5000"
    
    print("测试选项生成功能...")
    
    # 发送一条消息并获取流式响应
    message = "你好，请介绍一下自己"
    
    print(f"发送消息: {message}")
    
    response = requests.post(
        f"{base_url}/api/chat/stream",
        json={"message": message},
        stream=True
    )
    
    if response.status_code != 200:
        print(f"请求失败: {response.status_code}")
        print(response.text)
        return
    
    print("接收流式响应:")
    full_content = ""
    options = []
    
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith('data: '):
            data_str = line[6:]  # 去掉 'data: ' 前缀
            
            if data_str == '[DONE]':
                print("\n流式响应结束")
                break
            
            try:
                data = json.loads(data_str)
                
                if 'content' in data:
                    content = data['content']
                    full_content += content
                    print(content, end='', flush=True)
                
                if 'options' in data:
                    options = data['options']
                    print(f"\n\n收到选项: {options}")
                
            except json.JSONDecodeError as e:
                print(f"\n解析JSON失败: {e}, 数据: {data_str}")
    
    print(f"\n\n完整响应: {full_content}")
    print(f"生成的选项: {options}")
    
    if options:
        print("✅ 选项生成功能正常工作！")
    else:
        print("❌ 未收到选项数据")

if __name__ == "__main__":
    test_option_generation()
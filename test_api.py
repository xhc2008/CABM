#!/usr/bin/env python3
"""
测试新的流式API
"""
import requests
import json
import time

def test_stream_api():
    """测试流式API"""
    url = "http://localhost:5000/api/chat/stream"
    data = {"message": "你好，请简单介绍一下自己"}
    
    print("发送请求...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print("-" * 50)
    
    try:
        response = requests.post(
            url,
            json=data,
            stream=True,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code != 200:
            print(f"错误: HTTP {response.status_code}")
            print(response.text)
            return
        
        print("接收流式响应:")
        full_content = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(f"原始行: {line}")
                
                if line.startswith('data: '):
                    json_str = line[6:]  # 移除 'data: ' 前缀
                    
                    if json_str == '[DONE]':
                        print("流式响应结束")
                        break
                    
                    try:
                        data = json.loads(json_str)
                        print(f"解析数据: {data}")
                        
                        if 'content' in data:
                            content = data['content']
                            full_content += content
                            print(f"增量内容: '{content}'")
                            print(f"累积内容: '{full_content}'")
                        
                        if 'error' in data:
                            print(f"错误: {data['error']}")
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        print(f"原始数据: {json_str}")
        
        print("-" * 50)
        print(f"最终内容: {full_content}")
        
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

def test_regular_api():
    """测试普通API"""
    url = "http://localhost:5000/api/chat"
    data = {"message": "你好"}
    
    print("测试普通API...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    print("=== 测试新的流式API ===")
    test_stream_api()
    
    print("\n=== 测试普通API ===")
    test_regular_api()
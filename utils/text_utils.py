"""
文本处理工具模块
包含文本解析、句子分割等功能
"""
import re
import json
from typing import List, Optional


def parse_assistant_text(raw: str) -> str:
    """
    解析助手回复文本，提取纯文本内容
    
    Args:
        raw: 原始回复文本
        
    Returns:
        解析后的纯文本内容
    """
    try:
        # 尝试解析JSON格式
        obj = json.loads(raw)
        if isinstance(obj, dict):
            # 优先返回content字段
            if 'content' in obj:
                return obj['content']
            # 如果没有content，返回text字段
            if 'text' in obj:
                return obj['text']
        if isinstance(obj, str):
            return obj
    except Exception:
        pass
    return str(raw)


def extract_last_sentence(text: str) -> str:
    """
    提取文本的最后一句话
    
    Args:
        text: 输入文本
        
    Returns:
        最后一句话
    """
    if not text:
        return ""
    
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    
    sentence_endings = ['。', '！', '？', '!', '?', '.', '…', '♪', '...']
    escaped = ''.join(re.escape(ch) for ch in sentence_endings)
    pattern = rf"([^ {escaped}]+(?:[{escaped}]+)?)$"
    m = re.search(pattern, text)
    return m.group(1).strip() if m else text


def split_into_sentences(text: str) -> List[str]:
    """
    将文本按照标点符号分割成句子
    
    Args:
        text: 输入文本
        
    Returns:
        句子列表
    """
    if not text:
        return []
    
    # 先解析助手回复文本
    text = parse_assistant_text(text)
    
    # 清理文本
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    
    # 定义句子结束标点
    sentence_endings = ['。', '！', '？', '!', '?', '.', '…', '♪', '...']
    
    # 构建分割正则表达式
    escaped_endings = ''.join(re.escape(ch) for ch in sentence_endings)
    # 匹配句子：非结束标点的字符 + 结束标点（可选）
    pattern = rf"([^{escaped_endings}]*[{escaped_endings}]+|[^{escaped_endings}]+(?=[{escaped_endings}]|$))"
    
    sentences = re.findall(pattern, text)
    
    # 清理和过滤句子
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:  # 只保留非空句子
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences


def get_last_assistant_sentence_for_character(character_id: str) -> str:
    """
    获取指定角色的最后一句助手回复
    
    Args:
        character_id: 角色ID
        
    Returns:
        最后一句助手回复
    """
    try:
        from services.chat_service import chat_service
        
        history_messages = chat_service.history_manager.load_history(character_id, count=200, max_cache_size=500)
        for msg in reversed(history_messages):
            if msg.get('role') == 'assistant':
                raw = msg.get('content', '')
                text = parse_assistant_text(raw)
                return extract_last_sentence(text)
    except Exception as e:
        print(f"提取最后一句失败: {e}")
    return ""


def format_message_content_for_display(content: str, role: str) -> List[str]:
    """
    格式化消息内容用于显示，将长文本分割成句子
    
    Args:
        content: 消息内容
        role: 消息角色
        
    Returns:
        句子列表
    """
    if role == 'assistant':
        # 助手消息需要分割成句子
        return split_into_sentences(content)
    else:
        # 用户和系统消息直接返回
        return [content] if content.strip() else []


def clean_assistant_content(content: str) -> str:
    """
    清理助手消息内容，去除【】及其内部的内容（兼容旧格式）
    
    Args:
        content: 原始消息内容
        
    Returns:
        清理后的消息内容
    """
    # 先尝试解析JSON格式
    parsed_content = parse_assistant_text(content)
    
    # 如果解析后的内容与原内容相同，说明不是JSON格式，需要清理【】标记
    if parsed_content == content:
        # 使用正则表达式去除【】及其内部的内容
        cleaned_content = re.sub(r'【[^】]*】', '', content)
        return cleaned_content.strip()
    
    return parsed_content


if __name__ == "__main__":
    # 测试函数
    test_text = "你好！这是第一句话。这是第二句话？最后一句话..."
    print("原文本:", test_text)
    print("分割结果:", split_into_sentences(test_text))
    print("最后一句:", extract_last_sentence(test_text))
    
    # 测试JSON格式
    json_text = '{"content": "你好！这是JSON格式的回复。", "mood": "happy"}'
    print("JSON文本:", json_text)
    print("解析结果:", parse_assistant_text(json_text))
    print("分割结果:", split_into_sentences(json_text))
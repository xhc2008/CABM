import json
import os
import requests
from typing import List, Dict, Optional, Union
import numpy as np
from collections import defaultdict

class ChatHistoryVectorDB:
    def __init__(self, api_key: str, model: str = "BAAI/bge-large-zh-v1.5"):
        """
        初始化向量数据库
        
        参数:
            api_key: Silicon Flow API的密钥
            model: 使用的嵌入模型，默认为"BAAI/bge-large-zh-v1.5"
        """
        self.api_key = api_key
        self.model = model
        self.url = "https://api.siliconflow.cn/v1/embeddings"
        self.vectors = []  # 存储所有向量
        self.metadata = []  # 存储对应的元数据
        self.text_to_index = defaultdict(list)  # 文本到索引的映射
        
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        调用API获取文本的嵌入向量
        
        参数:
            text: 要嵌入的文本
            
        返回:
            嵌入向量列表或None(如果失败)
        """
        payload = {
            "model": self.model,
            "input": text
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data['data'][0]['embedding']
            else:
                print(f"获取嵌入失败，状态码: {response.status_code}, 响应: {response.text}")
                return None
        except Exception as e:
            print(f"获取嵌入时发生异常: {e}")
            return None
    
    def load_from_log(self, file_path: str):
        """
        从日志文件加载数据并生成向量
        
        参数:
            file_path: 日志文件路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    content = entry.get('content', '')
                    if not content or len(content.strip()) < 1:
                        continue
                        
                    # 获取嵌入向量
                    vector = self._get_embedding(content)
                    if vector is None:
                        continue
                        
                    # 存储数据和元数据
                    self.vectors.append(vector)
                    metadata = {
                        'text': content,
                        'timestamp': entry.get('timestamp', ''),
                        'role': entry.get('role', '')
                    }
                    self.metadata.append(metadata)
                    self.text_to_index[content].append(len(self.vectors) - 1)
                    
                except json.JSONDecodeError:
                    print(f"跳过无法解析的行: {line}")
                    continue
    
    def add_text(self, text: str, metadata: Optional[Dict] = None):
        """
        添加单个文本到向量数据库
        
        参数:
            text: 要添加的文本
            metadata: 可选的元数据字典
        """
        if not text or len(text.strip()) < 1:
            return
            
        vector = self._get_embedding(text)
        if vector is None:
            return
            
        self.vectors.append(vector)
        if metadata is None:
            metadata = {'text': text}
        else:
            metadata['text'] = text
        self.metadata.append(metadata)
        self.text_to_index[text].append(len(self.vectors) - 1)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索与查询文本最相似的文本
        
        参数:
            query: 查询文本
            top_k: 返回的最相似结果数量
            
        返回:
            包含相似结果和元数据的字典列表
        """
        if not self.vectors:
            return []
            
        query_vector = self._get_embedding(query)
        if query_vector is None:
            return []
            
        # 计算余弦相似度
        query_vector = np.array(query_vector)
        vectors = np.array(self.vectors)
        similarities = np.dot(vectors, query_vector) / (
            np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector)
        )
        
        # 获取最相似的top_k个结果
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            result = {
                'text': self.metadata[idx]['text'],
                'similarity': float(similarities[idx]),
                'metadata': {k: v for k, v in self.metadata[idx].items() if k != 'text'}
            }
            results.append(result)
            
        return results
    
    def save_to_file(self, file_path: str):
        """
        将向量数据库保存到文件
        
        参数:
            file_path: 保存路径
        """
        data = {
            'model': self.model,
            'vectors': self.vectors,
            'metadata': self.metadata
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, file_path: str):
        """
        从文件加载向量数据库
        
        参数:
            file_path: 加载路径
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.model = data.get('model', self.model)
        self.vectors = data.get('vectors', [])
        self.metadata = data.get('metadata', [])
        
        # 重建文本到索引的映射
        self.text_to_index = defaultdict(list)
        for idx, meta in enumerate(self.metadata):
            text = meta.get('text', '')
            if text:
                self.text_to_index[text].append(idx)


# 使用示例
if __name__ == "__main__":
    # 初始化向量数据库
    api_key = "your_api_key_here"  # 替换为你的API密钥
    vector_db = ChatHistoryVectorDB(api_key)
    
    # 从日志文件加载数据
    vector_db.load_from_log("Silver_Wolf_history.log")
    
    # 添加单个文本
    vector_db.add_text("测试文本", {"role": "test", "timestamp": "2023-01-01"})
    
    # 搜索相似文本
    results = vector_db.search("你好", top_k=3)
    print("搜索结果:")
    for res in results:
        print(f"文本: {res['text']}, 相似度: {res['similarity']:.4f}")
        print(f"元数据: {res['metadata']}\n")
    
    # 保存向量数据库
    vector_db.save_to_file("vector_db.json")
    
    # 加载向量数据库
    new_vector_db = ChatHistoryVectorDB(api_key)
    new_vector_db.load_from_file("vector_db.json")
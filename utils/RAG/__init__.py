import os
from typing import List
from .Retriever_all import Retriever
from importlib import import_module
class RAG:
    def __init__(self, config: dict):
        # 初始化函数
        self.retriever = Retriever(config)
        self.Reranker_config = config['Reranker']
        self.reranker_func = self.Reranker_config['reranker_func']
        module = import_module(
            f'utils.RAG.Reranker.Reranker_{self.reranker_func}')
        self.reranker = getattr(module, f'Reranker_{self.reranker_func}')(**self.Reranker_config['reranker_kwds'])
    
    def save_to_file(self, file_path: str):
        return {
            'retriever': self.retriever.save_to_file(file_path)
        }
    def load_from_file(self, data_dict: dict):
        if data_dict is not None:
            self.retriever.load_from_file(data_dict['retriever'])
        return self
    
    
    def add(self, corpus: List[str] | str):
        # 私有添加函数
        self.retriever.add(corpus)
        return self
        
    def req(self, query, top_k=5) -> List[str]:
        # 查询函数
        retrieval_res = self.retriever.retrieval(query)  # 获得初步查询
        if retrieval_res is None or len(retrieval_res) == 0:
            return []
        rerank_res = self.reranker.rerank(retrieval_res, query, k=top_k)  # 后处理, 精排
        return rerank_res

if __name__ == '__main__':
    # 创建一个知识库对象
    import sys
    sys.path.append(r'D:\Mypower\Git\MyPython\MyProject\CABM')
    from config import RAG_CONFIG
    kb = RAG(RAG_CONFIG)
    
    # 添加内容
    kb.add(['test', 'hello', '静流', '我爱你'])
    
    print(kb.req('静流的外号', 5))
    
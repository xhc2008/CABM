from typing import List
import logging
from importlib import import_module
from traceback import print_exc
import traceback
# from langchain.vectorstores import FAISS

class Retriever:
    def __init__(self, config: dict):
        self.logger = logging.getLogger(f"Retriever")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
        self.config = config

        self.initialize()
        
    def save_to_file(self, file_path: str):
        dic = {}
        for recall_func in self.recall_dict:
            dic[recall_func] = self.recall_dict[recall_func].save_to_file(file_path)
        dic['id_to_doc'] = self.id_to_doc
        return dic
    
    def load_from_file(self, data_dict: dict):
        self.id_to_doc = data_dict['id_to_doc'].copy()
        for recall_func in self.recall_dict:
            self.recall_dict[recall_func].load_from_file(data_dict)
        return self
            
    def initialize(self):
        self.recall_config = self.config['Multi_Recall']
        self.id_to_doc = {}  # 用于存储文档的映射
        self.recall_dict = {}
        for recall_func in self.recall_config:
            self.logger.info(f"Loading {recall_func}...")
            func_kwds = self.recall_config[recall_func]
            try:
                module = import_module(f"utils.RAG.Multi_Recall.{recall_func}")  # 动态导入包
            except Exception as e:
                self.logger.error(f"Error loading {recall_func}: {e}")
                print_exc()
                continue
            try:
                self.recall_dict[recall_func] = getattr(module, recall_func)(**func_kwds)  # 创建召回对象
            except Exception as e:
                self.logger.error(f"Error creating {recall_func}: {e}")
                print_exc()
                continue
        return self
    
    def process_corpus(self, corpus: List[str] | str) -> List[str]:  # 进行如分段, 去除标点等前处理操作
        return corpus
    
    def add(self, corpus: List[str] | str) -> None:
        if isinstance(corpus, str):
            corpus = [corpus]
        corpus = self.process_corpus(corpus)  # 前处理
        self.logger.info(f"Process {len(corpus)} documents")
        
        for recall_func, recall_module in self.recall_dict.items():  # 循环添加
            self.logger.info(f"Adding {recall_func}...")
            recall_module.add(corpus, self.id_to_doc)
        
        starId = len(self.id_to_doc)  # 更新id_to_doc
        for doc in corpus:
            self.id_to_doc[starId] = doc
            starId += 1
        return self
    def retrieval(self, query, 
                  methods = None,
                  top_k = 10
                  ) -> List[str]:
        search_res = list()
        if methods is None:
            methods = list(self.recall_dict.keys())
        for method in methods:
            if method in self.recall_dict:
                res = self.recall_dict[method].retrieval(query, self.id_to_doc, top_k)
                search_res.extend(res)
        search_res = list(set(search_res))  # 结果去重
        return search_res

if __name__ == "__main__":
    import sys
    sys.path.append(r'D:\Mypower\Git\MyPython\MyProject\CABM')
    
    from langchain.text_splitter import CharacterTextSplitter
    text_splitter = CharacterTextSplitter(
        separator='',
        chunk_size=256,      # 每个分片最大字符数
        chunk_overlap=64     # 分片之间的重叠字符数
    )
    data = open('test/镜流.txt', 'r', encoding='utf-8').read()
    chunks = text_splitter.split_text(data)
    
    from config import RAG_CONFIG
    vector_db = Retriever(config=RAG_CONFIG)
    vector_db.add(chunks)
    
    print(vector_db.retrieval('镜流的属性', top_k=1, methods=['Cosine_Similarity']))
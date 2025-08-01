from .Retriever import *
from typing import List, Literal, Dict
try:
    from rank_bm25 import BM25Okapi
    import jieba
except ImportError:
    raise ImportError("rank_bm25 or jieba 未安装. 无法使用BM25")


class BM25(Retriever):
    def __init__(self, lan: Literal['zh', 'en'] = 'zh'):
        self.bm25 = None
        self.lan = lan
    
    @property
    def method(self):
        if self.lan == 'zh':
            method = lambda x: jieba.lcut(x)
        else:
            method = lambda x: x.split()
        return method
    def add(self,
            corpus: List[str] | str,  # 新增文档
            id_to_doc: Dict[int, str]  # 已有的文档id_to_doc
            ):
        '''
        由于BM25需要对所有的文档进行处理, 所以使用id_to_doc
        '''
        if isinstance(corpus, str):
            corpus = [corpus]
        corpus = list(id_to_doc.values()) + corpus
            
        tokenized_documents = []
        for p in tqdm(corpus, desc='BM25 Embedding', unit='step'):
            tokenized_documents.append(self.method(p))
        self.bm25 = BM25Okapi(corpus)
    
    def retrieval(self, 
                  query: str, 
                  id_to_doc: Dict[int, str], 
                  top_k: int = 10):  # 原文档corpus可为外部传入, 减少重复储存带来的内存消耗
        query = self.method(query)
        res = self.bm25.get_top_n(query, list(id_to_doc.values()), n=top_k)
        return res

    def save_to_file(self, file_path: str):
        logger.info('保存BM25索引')
        return ''
        
    
    def load_from_file(self, data_dict: dict):
        logger.info('加载BM25索引')
        self.add([], data_dict['id_to_doc'])
        return self

if __name__ == '__main__':
    bm = BM25()
    li = ['终于见到你了', '不想看见你', '你怎么还在', '不在']
    id_to_doc = {}
    bm.add(li, id_to_doc)
    starId = len(id_to_doc)
    for doc in li:
        id_to_doc[starId] = doc
        starId += 1
    print(bm.retrieval('不在', id_to_doc, top_k=4))
from abc import ABC, abstractmethod
from typing import List, Dict
import logging
__all__ = ['Retriever', 'tqdm', 'logger']

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, *args, **kwargs):
        return iterable
    
class Retriever(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def add(self,
            corpus: List[str] | str,  # 新增文档
            id_to_doc: Dict[int, str]  # 已有的文档id_to_doc
            ):
        pass

    @abstractmethod
    def retrieval(self, 
                  query: str,  # 查询字符串
                  id_to_doc: Dict[int, str],  # 文档id_to_doc  
                  top_k: int = 10  # 召回文档数目
                  ):
        pass
    
    @abstractmethod
    def save_to_file(self, file_path: str):
        pass
    
    @abstractmethod
    def load_from_file(self, data_dict: dict):
        pass

logger = logging.getLogger(f"Recall Loading")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
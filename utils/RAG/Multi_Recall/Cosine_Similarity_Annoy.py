from .Retriever import *
from typing import List, Literal, Dict, Union
import traceback
import os
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    class Embedding_Model:
        def __init__(self, 
                     emb_model_name_or_path, 
                     max_len: int = 512, 
                     bath_size: int = 64, 
                     device: Literal['cuda', 'cpu'] = None):
            if 'bge' in emb_model_name_or_path:
                self.DEFAULT_QUERY_BGE_INSTRUCTION_ZH = "为这个句子生成表示以用于检索相关文章："
            else:
                self.DEFAULT_QUERY_BGE_INSTRUCTION_ZH = ""
            self.emb_model_name_or_path = emb_model_name_or_path
            if device is None:
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            else: 
                device = torch.device(device)
            self.device = device
            self.batch_size = bath_size
            self.max_len = max_len
            
            self.model = AutoModel.from_pretrained(emb_model_name_or_path, trust_remote_code=True).half().to(device)
            self.tokenizer = AutoTokenizer.from_pretrained(emb_model_name_or_path, trust_remote_code=True)

        def embed(self, texts: Union[List[str], str]) -> List[List[float]]:
            if isinstance(texts, str):
                texts = [texts]
                
            num_texts = len(texts)
            texts = [t.replace("\n", " ") for t in texts]
            sentence_embeddings = []

            for start in tqdm(range(0, num_texts, self.batch_size), desc='Model批量嵌入文本'):
                end = min(start + self.batch_size, num_texts)
                batch_texts = texts[start:end]
                batch_texts = [self.DEFAULT_QUERY_BGE_INSTRUCTION_ZH+x for x in batch_texts]
                encoded_input = self.tokenizer(batch_texts, max_length=self.max_len, padding=True, truncation=True,
                                            return_tensors='pt').to(self.device)

                with torch.no_grad():
                    model_output = self.model(**encoded_input)
                    # Perform pooling. In this case, cls pooling.
                    if 'gte' in self.emb_model_name_or_path:
                        batch_embeddings = model_output.last_hidden_state[:, 0]
                    else:
                        batch_embeddings = model_output[0][:, 0]
                    batch_embeddings = torch.nn.functional.normalize(batch_embeddings, p=2, dim=1)
                    sentence_embeddings.extend(batch_embeddings.tolist())

            return sentence_embeddings
        
        def __call__(self, *args, **kwds):
            return self.embed(*args, **kwds)
except ImportError:
    logger.info('torch或transformers未安装. 无法使用Embedding_Model')
    Embedding_Model = None
    
try:
    from openai import OpenAI
    class Embedding_API:
        def __init__(self, base_url, api_key: str, model: str):
            self.base_url = base_url
            self.api_key = api_key
            self.model = model
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        
        def embed(self, texts: Union[List[str], str]) -> List[List[float]]:
            """
            调用API获取文本的嵌入向量（带缓存检查）
            """
            if isinstance(texts, str):
                texts = [texts]
                
            if not self.client:  # 检查客户端是否可用
                print("OpenAI客户端未初始化")
                return None
            
            try:
                ans = []
                for text in tqdm(texts, desc='API嵌入文本'):
                    # 使用 OpenAI 库调用嵌入API
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=text
                    )
                    res = response.data[0].embedding
                    ans.append(res)
                return ans
            except Exception as e:
                print(f"获取嵌入时发生异常: {e}")
                traceback.print_exc()
        
        def __call__(self, *args, **kwds):
            return self.embed(*args, **kwds)
except ImportError:
    logger.info("未找到openai模块. 无法使用Embedding_API")
    Embedding_API = None

try:
    from annoy import AnnoyIndex
    import numpy as np
except ImportError:
    raise ImportError("annoy 未安装. 无法使用索引向量数据库")

embed_dict = {
    'Model': Embedding_Model,
    'API': Embedding_API
}

class Cosine_Similarity(Retriever):
    def __init__(self, 
                 embed_func: Literal['Model', 'API'], 
                 embed_kwds: dict, 
                 vector_dim: int = 1024,
                 threshold: float = 0.5
                 ):
        self.vector_dim = vector_dim  # 向量维度
        self.annoy_index = AnnoyIndex(self.vector_dim, 'angular')  # 向量数据库
        self.threshold = threshold
        self.embedClass = embed_dict[embed_func]
        if self.embedClass is None:
            raise ValueError("当前选择的嵌入方法不可用!")
        self.embed = self.embedClass(**embed_kwds)

    def save_to_file(self, file_path: str):
        logger.info('保存向量数据库')
        return ''
    
    def load_from_file(self, data_dict: dict):
        try:
            logger.info('加载向量数据库, 并重新编制索引')
            id_to_doc = data_dict['id_to_doc']
            self.add(list(id_to_doc.values()), {})
        except Exception as e:
            logger.info('Cosine_Similarity Load 失败!: ', e)
            traceback.print_exc()
    
    def add(self,
            corpus: List[str] | str,  # 新增文档
            id_to_doc: Dict[int, str]  # 已有的文档id_to_doc
            ):
        embde_corpus = self.embed(corpus)
        starId = len(id_to_doc)
        for dx, embed_doc in enumerate(embde_corpus):
            self.annoy_index.add_item(starId+dx, embed_doc)  # 添加向量

        self.build()
        
    def retrieval(self, 
                  query: str, 
                  id_to_doc: Dict[int, str], 
                  top_k: int = 10
                  ):
        query_embed = self.embed(query)[0]
        nearest_ids, distances = self.annoy_index.get_nns_by_vector(query_embed, top_k//3+1, include_distances=True)
        res = []
        for idx, dist in zip(nearest_ids, distances):  # 遍历最接近的向量
            if dist < self.threshold:
                break
            res.append(id_to_doc[max(idx-1, 0)])  #TODO 保留上下文信息
            res.append(id_to_doc[idx])
            res.append(id_to_doc[min(len(id_to_doc)-1, idx+1)])
            
        res = list(set(res))  # 去重
        return res
    
    def build(self, n_trees: int = 10):
        self.annoy_index.build(n_trees)
    

if __name__ == "__main__":
    import time
    
    # 测试embedding模型
    # embedding = Embedding_Model(emb_model_name_or_path="BAAI/bge-large-zh", device='cuda')
    # star = time.time()
    # print(len(embedding(["你好", '介绍你自己', '你叫什么'])))
    # print(time.time() - star)
    
    # 测试embeddingAPI
    # from dotenv import load_dotenv
    # import os
    # load_dotenv()
    # embedding = Embedding_API(api_key=os.getenv("EMBEDDING_API_KEY"), base_url=os.getenv("EMBEDDING_API_BASE_URL"), model=os.getenv("EMBEDDING_MODEL"))
    # star = time.time()
    # print(embedding(["你好"]))
    # print(time.time() - star)
    
    from langchain.text_splitter import CharacterTextSplitter
    text_splitter = CharacterTextSplitter(
        chunk_size=128,      # 每个分片最大字符数
        chunk_overlap=32     # 分片之间的重叠字符数
    )
    data = open('test/镜流.txt', 'r', encoding='utf-8').read()
    chunks = text_splitter.split_text(data)
    vector_db = Cosine_Similarity(embed_func='Model', 
                                  embed_kwds={'emb_model_name_or_path': 'BAAI/bge-large-zh'})
    id_to_doc = {}

    vector_db.add(chunks, id_to_doc=id_to_doc)
    
    starId = len(id_to_doc)  # 更新id_to_doc
    for doc in chunks:
        id_to_doc[starId] = doc
        starId += 1
    print(vector_db.retrieval('镜流的属性', id_to_doc=id_to_doc, top_k=1))
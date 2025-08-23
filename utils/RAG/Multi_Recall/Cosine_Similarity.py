from .Retriever import *
from typing import List, Literal, Dict, Union
import traceback
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    class Embedding_Model:
        def __init__(self, 
                     emb_model_name_or_path, 
                     max_len: int = 512, 
                     bath_size: int = 64, 
                     device: Literal['cuda', 'cpu'] = None):
            logger.info('初始化Embedding_Model: %s', emb_model_name_or_path)
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
            logger.info('初始化Embedding_API: %s', model)
            self.base_url = base_url
            self.api_key = api_key
            self.model = model
            if not self.api_key:
                raise ValueError("API key is missing. Please set the EMBEDDING_API_KEY environment variable.")
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
    import numpy as np
except ImportError:
    raise ImportError("numpy 未安装. 无法使用索引向量数据库")

embed_dict = {
    'Model': Embedding_Model,
    'API': Embedding_API
}
'''
TODO
由Annoy重构为使用list的存储模式.
'''
class Cosine_Similarity(Retriever):
    def __init__(self, 
                 embed_func: Literal['Model', 'API'], 
                 embed_kwds: dict, 
                 vector_dim: int = 1024,
                 threshold: float = 0.5
                 ):
        self.vector_dim = vector_dim  # 向量维度
        self.vectors = []  # 存储所有向量，类型为List[np.ndarray]
        self.threshold = threshold
        self.embedClass = embed_dict[embed_func]
        if self.embedClass is None:
            raise ValueError("当前选择的嵌入方法不可用!")
        self.embed = self.embedClass(**embed_kwds)

    def save_to_file(self, file_path: str):
        logger.info('保存向量数据库')
        return self.vectors

    def load_from_file(self, data_dict: dict):
        try:
            logger.info('加载向量数据库, 并重新编制索引')
            self.vectors = data_dict['Cosine_Similarity'].copy()
            
        except Exception as e:
            logger.info('Cosine_Similarity Load 失败!: ', e)
            traceback.print_exc()

    def add(self,
            corpus: List[str] | str,  # 新增文档
            id_to_doc: Dict[int, str]  # 已有的文档id_to_doc
            ):
        # 1. 计算新增文本的向量
        embed_corpus = self.embed(corpus)
        # 2. 转成np.ndarray，归一化
        embed_corpus = np.array(embed_corpus)
        embed_corpus = embed_corpus/ np.linalg.norm(embed_corpus, axis=1, keepdims=True)  # 归一化
        embed_corpus = embed_corpus.tolist()  # 转成list
        
        self.vectors.extend(embed_corpus)
        
        return self

    def retrieval(self, 
                  query: str, 
                  id_to_doc: Dict[int, str], 
                  top_k: int = 10
                  ):
        # 1. 计算query向量，归一化
        query_embed = self.embed(query)[0]
        query_embed = np.array(query_embed)
        query_embed = query_embed / np.linalg.norm(query_embed)

        # 2. 计算余弦相似度（向量点积，因为归一化了，所以点积=余弦相似度）
        sims = []
        for vec in self.vectors:
            sims.append(np.dot(query_embed, vec))

        sims = np.array(sims)
        # 3. 找到相似度最高的top_k个索引
        topk_idx = sims.argsort()[::-1][:top_k//3+1]

        res = []
        for idx in topk_idx:  # 遍历最接近的向量
            idx = int(idx)
            dist = sims[idx]
            if dist < self.threshold:
                break
            res.append(id_to_doc[max(idx-1, 0)])  #TODO 保留上下文信息
            res.append(id_to_doc[idx])
            res.append(id_to_doc[min(len(id_to_doc)-1, idx+1)])
        res = list(set(res))
        return res
    

if __name__ == "__main__":
    import time
    
    # 测试embedding模型
    # embedding = Embedding_Model(emb_model_name_or_path="BAAI/bge-large-zh", device='cuda')
    # star = time.time()
    # print(len(embedding(["你好", '介绍你自己', '你叫什么'])))
    # print(time.time() - star)
    
    # 测试embeddingAPI
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
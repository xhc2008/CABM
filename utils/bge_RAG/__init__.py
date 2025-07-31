import os
import dotenv
dotenv.load_dotenv()
from retriever import Retriever
from reranker import Reranker

class RAG():
    def __init__(self, max_len=256, overlap_len=50):
        # 初始化函数
        self.retriever = Retriever(emb_model_name_or_path='BAAI/bge-large-zh')
        self.reranker = Reranker(rerank_model_name_or_path='BAAI/bge-reranker-large')
        self.max_len = int(max_len)
        self.overlap_len = int(overlap_len)
    def _add(self, corpus):
        # 私有添加函数
        self.retriever.add(corpus)
        
    def req(self, query, top_k=5):
        # 查询函数
        retrieval_res = self.retriever.retrieval(query)  # 获得初步查询
        rerank_res = self.reranker.rerank(retrieval_res, query, k=top_k)  # 后处理, 精排
        return '\n<document-spilt>\n'.join(rerank_res)
    
    def spilt(self, page_content):
        # 分隔函数
        cleaned_chunks = []
        i = 0
        # 暴力将整个pdf当做一个字符串，然后按照固定大小的滑动窗口切割
        all_str = ''.join(page_content)
        # all_str = all_str.replace('\n', '')
        while i < len(all_str):
            cur_s = all_str[i:i+self.max_len]
            if len(cur_s) > 10:
                cleaned_chunks.append(cur_s)
            i += (self.max_len - self.overlap_len)
        return cleaned_chunks
    def add(self, upload_file_path:str =None):
        spiltNum = self.max_len
        chunk_overlap = self.overlap_len
        # 开发的添加函数
        if upload_file_path is None:
            upload_file_path = os.environ['UPLOAD_DIR']
        print('~ 正在读取文本')
        corpus = []
        for file in os.listdir(upload_file_path):  # 循环添加
            print(file, end='\t')
            if file.endswith('.txt'):
                with open(os.path.join(upload_file_path, file), 'r', encoding='utf-8') as f:
                    text = f.read()
                from langchain.text_splitter import CharacterTextSplitter
                text_splitter = CharacterTextSplitter(
                    separator="",      # 按换行分割（可自定义）
                    chunk_size=spiltNum,      # 每个分片最大字符数
                    chunk_overlap=chunk_overlap     # 分片之间的重叠字符数
                )
                corpus = corpus + text_splitter.split_text(text)
        print('~ 添加了: ', len(os.listdir(upload_file_path)), ' 条数据')
        print('~ 正在添加进知识库')
        if  len(corpus) > 0:
            self._add(corpus)
        print('~ 添加成功')
    
    def delete(self, *args, **kwargs):
        # 从知识库中删除
        self.add(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        # 保存
        # TODO
        pass
    
    def load(self, *args, **kwargs):
        # 加载知识库内容
        self.add()

if __name__ == '__main__':
    # 创建一个知识库对象
    kb = RAG()
    
    # 添加内容
    kb.add('test')
    
    print(kb.req('静流的外号', 5))
    
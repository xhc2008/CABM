import gradio as gr
import numpy as np
import faiss
import json
import os

def json_to_index(json_file):
    # gradio File 输入为文件路径字符串
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 假定结构为 [{"text": "...", ...}]
    texts = [item["text"] for item in data if "text" in item]
    # 简单 embedding：每条文本转为长度 128 的随机向量（实际可替换为真实 embedding）
    dim = 128
    embeddings = np.random.rand(len(texts), dim).astype("float32")
    # 构建 faiss index
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    # 保存 index 文件
    out_path = "output.index"
    faiss.write_index(index, out_path)
    return out_path

iface = gr.Interface(
    fn=json_to_index,
    inputs=gr.File(label="上传 JSON 文件"),
    outputs=gr.File(label="下载 Index 文件"),
    title="JSON 转 Index 工具",
    description="上传包含 memory 的 JSON 文件，自动生成 FAISS index 向量文件。"
)

if __name__ == "__main__":
    iface.launch()

import gradio as gr

def parse_files(faiss_file, peewee_db):
    import os
    import pickle
    import json

    chats = []

    # 解析FAISS index文件
    if faiss_file is not None:
        faiss_path = faiss_file.name
        base_dir = os.path.dirname(faiss_path)
        texts_path = None
        metadata_path = None

        for fname in os.listdir(base_dir):
            if fname.endswith("_texts.pkl"):
                texts_path = os.path.join(base_dir, fname)
            if fname.endswith("_metadata.json"):
                metadata_path = os.path.join(base_dir, fname)

        if texts_path and metadata_path:
            try:
                with open(texts_path, "rb") as f:
                    texts = pickle.load(f)
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                # 只还原文本内容，meta可选
                for i, text in enumerate(texts):
                    chats.append([text, "", ""])  # 只填user列，其他留空
            except Exception as e:
                chats.append([f"FAISS文件解析失败: {e}", "", ""])
        # 如果没有相关文件则跳过，不输出提示
    # 解析peewee数据库
    if peewee_db is not None:
        import sqlite3
        try:
            conn = sqlite3.connect(peewee_db.name)
            cursor = conn.cursor()
            cursor.execute("SELECT user_message, assistant_message, timestamp FROM memoryrecord WHERE record_type='conversation'")
            rows = cursor.fetchall()
            for row in rows:
                user_msg, assistant_msg, ts = row
                chats.append([user_msg or "", assistant_msg or "", ts or ""])
            conn.close()
        except Exception as e:
            chats.append([f"peewee数据库解析失败: {e}", "", ""])
    return chats

def save_files(edited_chats):
    import tempfile
    import os
    import sqlite3
    import faiss
    import numpy as np
    import time

    # DataFrame对象转list
    if hasattr(edited_chats, "to_list"):
        edited_chats = edited_chats.to_list()
    elif hasattr(edited_chats, "values"):
        edited_chats = edited_chats.values.tolist()

    # 唯一文件名
    ts = int(time.time() * 1000)
    tmp_dir = tempfile.gettempdir()
    db_path = os.path.join(tmp_dir, f"edited_memory_{ts}.db")
    index_path = os.path.join(tmp_dir, f"edited_memory_{ts}.index")

    # 写入peewee数据库（sqlite）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memoryrecord (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            assistant_message TEXT,
            timestamp TEXT,
            record_type TEXT
        )
    """)
    for row in edited_chats:
        user, assistant, t = row
        cursor.execute(
            "INSERT INTO memoryrecord (user_message, assistant_message, timestamp, record_type) VALUES (?, ?, ?, ?)",
            (user, assistant, t, "conversation")
        )
    conn.commit()
    conn.close()

    # 写入FAISS向量文件（仅保存空索引，实际业务应补充向量写入）
    dim = 384
    index = faiss.IndexFlatL2(dim)
    faiss.write_index(index, index_path)

    return db_path, index_path

def ui_upload(faiss_file, peewee_db):
    chats = parse_files(faiss_file, peewee_db)
    return chats

def ui_save(chats):
    # DataFrame转list
    try:
        import pandas as pd
        if isinstance(chats, pd.DataFrame):
            chats = chats.values.tolist()
    except Exception:
        pass
    json_path, index_path = save_files(chats)
    return json_path, index_path

with gr.Blocks() as demo:
    gr.Markdown("# 向量/数据库转聊天记录编辑工具")
    with gr.Row():
        faiss_file = gr.File(label="上传FAISS index文件")
        peewee_db = gr.File(label="上传peewee数据库文件")
    load_btn = gr.Button("加载聊天记录")
    chatbox = gr.Dataframe(headers=["user", "assistant", "timestamp"], datatype=["str", "str", "str"], label="聊天记录", interactive=True)
    save_btn = gr.Button("保存编辑结果")
    download_json = gr.File(label="下载编辑后的记忆peewee")
    download_index = gr.File(label="下载编辑后的index文件")

    load_btn.click(fn=ui_upload, inputs=[faiss_file, peewee_db], outputs=chatbox)
    save_btn.click(fn=ui_save, inputs=chatbox, outputs=[download_json, download_index])

if __name__ == "__main__":
    demo.launch()

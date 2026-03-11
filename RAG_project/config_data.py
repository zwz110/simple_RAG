from pathlib import Path

# 基于本文件所在目录构建路径，避免不同工作目录导致的重复嵌套
BASE_DIR = Path(__file__).resolve().parent

md5_path = str(BASE_DIR / "md5.txt")
3
# chroma
collection_name = 'rag_test1'
persist_directory = str(BASE_DIR / "chroma_db")


chunk_size = 500
chunk_overlap = 50
separators = ["\n", "\n\n", '.', ',', "。", "，", "!", "！"]
max_split_char_number = 500  # 超过该值才进行文本分割


#
similarity_threshold=2  #检索返回匹配的文档数量


embedding_model="text-embedding-v4"
chat_model="qwen3-max"

session_config = {"configurable": {"session_id": "user_001"}}




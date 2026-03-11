import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime
from langchain_community.document_loaders import CSVLoader,PyPDFLoader,TextLoader,Docx2txtLoader,UnstructuredExcelLoader
import tempfile



def check_md5(md5_str:str):

    # False：md5未处理过,True：md5已处理过
    if not os.path.exists(config.md5_path):
        open(config.md5_path,"w",encoding="utf-8").close()
        return False
    else:
        with open(config.md5_path,"r",encoding="utf-8") as f:
            for line in f:
                line=line.strip()
                if line==md5_str:
                    return True
        return False

def save_md5(md5_str:str):
    with open(config.md5_path,"a",encoding="utf-8") as f:
        f.write(md5_str+"\n")


#将传入的字符串转换为16进制的md5字符串
def get_string_md5(input_str:str,encoding="utf-8"):

    #将字符串转换为字节数组（MD5算法只处理字节，不处理字符串）
    str_bytes=input_str.encode(encoding=encoding)

    #创建md5对象
    md5_obj=hashlib.md5()   #得到md5对象
    md5_obj.update(str_bytes)   #更新内容(传入即将转换的字节数组)
    md5_hex=md5_obj.hexdigest() #得到md5的16进制字符串
    return md5_hex


"""针对文件字节流生成MD5（适配二进制文件如PDF/Excel）"""
def get_file_md5(file_bytes:bytes):
    md5_obj=hashlib.md5()
    md5_obj.update(file_bytes)
    return md5_obj.hexdigest()

#从MD5记录文件中删除指定MD5（核心：删除后更新文件）
def remove_md5(md5_str:str):
    if not os.path.exists(config.md5_path):
        return
    with open(config.md5_path,"r",encoding="utf-8")as f:
        lines=[line.strip()for line in f if line.strip()!=md5_str]
    with open(config.md5_path,"w",encoding="utf-8")as f:
        f.write("\n".join(lines)+"\n")

class KnowledgeBaseService(object):
    def __init__(self):
        #文件夹不存在就创建，存在则跳过
        os.makedirs(config.persist_directory,exist_ok=True)
        self.chroma=Chroma(
            collection_name=config.collection_name,
            embedding_function=DashScopeEmbeddings(model="text-embedding-v4"),
            persist_directory=config.persist_directory
        )
        
        self.spliter=RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,#分割后文本的最大长度
            chunk_overlap=config.chunk_overlap,#连续文本段之间的字符重叠数量
            separators=config.separators,#自然段落划分符号
            length_function=len,  #用len函数作为长度统计的依据
            )
        
    def upload_by_str(self,data,filename):
        #将传入的字符串，进行向量化，存入向量数据库中
        md5_hex=get_string_md5(data)
        if check_md5(md5_hex):
            return "[跳过]内容已存在知识库中"
        
        if len(data)>config.max_split_char_number:
            knowledge_chunks:list[str]=self.spliter.split_text(data)
        else:
            knowledge_chunks=[data]
        
        metdata={
            "source":filename,
            "create_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator":"用户上传",
            "md5":md5_hex
        }
        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=[metdata for _ in knowledge_chunks]
            )
        save_md5(md5_hex)

        return  "[成功]内容已经成功存入"
    
    def load_document(self,file_bytes:bytes,filename:str):
        #新增：加载多类型文档，返回LangChain Document列表
        file_ext=os.path.splitext(filename)[-1].lower()
        try:
            # 创建临时文件（加载器需要文件路径）
            #delete=False 确保文件不会随文件对象关闭而消失，直到手动删除；
            #suffix=file_ext 保证临时文件的扩展名和原文件一致（比如 PDF 解析库依赖 .pdf 扩展名识别文件类型）
            with tempfile.NamedTemporaryFile(delete=False,suffix=file_ext) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path=temp_file.name
                # 按类型加载文档
            if file_ext == ".txt":
                loader = TextLoader(temp_file_path, encoding="utf-8")
            elif file_ext == ".csv":
                loader = CSVLoader(temp_file_path, encoding="utf-8")
            elif file_ext == ".pdf":
                loader = PyPDFLoader(temp_file_path)
            elif file_ext == ".docx":
                loader = Docx2txtLoader(temp_file_path)
            elif file_ext in [".xlsx", ".xls"]:
                loader = UnstructuredExcelLoader(temp_file_path)
            else:
                raise ValueError(f"不支持的文件类型：{file_ext}")
            documents=[]
            for document in loader.lazy_load():
                documents.append(document)

            # 删除临时文件
            os.unlink(temp_file_path)
             # 为每个文档片段添加基础元数据
            for doc in documents:
                doc.metadata.update({
                    "file_name": filename,
                    "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "operator": "用户上传"
                })
            return documents
        except Exception as e:
            # 异常时清理临时文件
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise Exception(f'加载文档失败:{str(e)}')


    def upload_by_file(self,file_bytes:bytes,filename:str):
        #新增：处理上传的文件（多类型），保留MD5防重复
        try:
            file_md5=get_file_md5(file_bytes)
            if check_md5(file_md5):
                return f"[跳过]文件 {filename} 已完整上传过，无需重复处理"
            documents=self.load_document(file_bytes,filename)
            if not documents:
                return f"[失败]文件 {filename} 加载后无内容，请检查文件有效性"
            
            #分割文档（统一用配置的分割器）
            split_docs=self.spliter.split_documents(documents)
            if not split_docs:
                return f"[失败]文件 {filename} 分割后无内容"
            
            #为每个分割片段生成唯一MD5（避免片段重复）
            chunk_text=[]
            chunk_metadatas=[]
            for idx,doc in enumerate(split_docs):
                chunk_md5=get_string_md5(doc.page_content)
                if check_md5(chunk_md5):
                    continue
                chunk_text.append(doc.page_content)
                # 构造片段元数据（继承原文档元数据 + 新增片段信息）
                chunk_metadata=doc.metadata.copy()
                chunk_metadata.update({
                    "source": filename,
                    "chunk_idx": idx,
                    "chunk_md5": chunk_md5,
                    "file_md5": file_md5
                })
                chunk_metadatas.append(chunk_metadata)
                save_md5(chunk_md5)
            if not chunk_text:
                return f"[跳过]文件 {filename} 的所有内容已存在知识库中"
            
            #存入向量数据库
            self.chroma.add_texts(chunk_text,metadatas=chunk_metadatas)
            save_md5(file_md5)
            return f"[成功]文件 {filename} 上传完成."
        except Exception as e:
            return f"[失败]文件 {filename} 上传失败：{str(e)}"

    #获取知识库中所有已上传的文件列表（去重）
    def get_uploaded_file(self):
        try:
            # 从向量数据库中查询所有元数据，提取source字段（文件名）
            all_docs=self.chroma.get()  # 获取所有文档的元数据和ID
            if not all_docs["metadatas"]:
                return []
            # 去重，返回唯一的文件名列表
            file_name=[]
            for meta in all_docs["metadatas"]:
                if meta is None:
                    continue
                source = meta.get("source")
                if source:
                    file_name.append(source)
            # 去重
            file_name = list(set(file_name))
            return sorted(file_name)
        except Exception as e:
            raise Exception(f"获取文件列表失败：{str(e)}")
        
    #按文件名删除知识库中对应的所有片段
    def delete_file_by_name(self,filename:str):
        try:
            #查询该文件对应的所有文档ID和MD5
            all_docs=self.chroma.get()
            delete_ids=[]
            delete_md5=set() # 要删除的MD5集合（文件MD5+片段MD5）
            for idx,meta in enumerate(all_docs["metadatas"]):
                if meta is None:
                    continue
                if meta.get("source")==filename:
                    delete_ids.append(all_docs["ids"][idx])
                 # 收集要删除的MD5（包括文件MD5+片段MD5）
                    if "file_md5" in meta:
                        delete_md5.add(meta["file_md5"])
                    if "chunk_md5" in meta:
                        delete_md5.add(meta["chunk_md5"])
                    if "md5" in meta:
                        delete_md5.add(meta["md5"]) 
            if not delete_ids:
                return f"[提示]未找到文件 {filename} 对应的任何数据" 
            
            #从向量数据库删除对应ID的片段
            self.chroma.delete(ids=delete_ids)

            #从MD5记录文件中删除对应的MD5
            for md5_str in delete_md5:
                remove_md5(md5_str)
            return f"[成功]已删除文件 {filename}相关内容"
        except Exception as e:
            return f"[失败]删除文件 {filename} 失败：{str(e)}"
        

    #清空整个知识库（谨慎使用）
    def delete_all_files(self):
        try:
            self.chroma.delete_collection()
            self.chroma=Chroma(
                collection_name=config.collection_name,
                embedding_function=DashScopeEmbeddings(model=config.embedding_model),
                persist_directory=config.persist_directory
            )
            open(config.md5_path,"w","utf-8").close()
            return "[成功]已清空整个知识库和MD5记录"
        except Exception as e:
            return f"[失败]清空知识库失败：{str(e)}"

    
if __name__=='__main__':
    service=KnowledgeBaseService()
    print(service.upload_by_str(data="周杰伦",filename="test"))
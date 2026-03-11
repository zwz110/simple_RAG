# LangChain RAG 项目

一个基于 LangChain 和阿里云百炼的检索增强生成（RAG）系统，提供知识库管理和智能问答功能。

## ✨ 主要功能

- **多格式文件上传**：支持 TXT、CSV、PDF、DOCX、Excel 等格式文件上传到知识库
- **智能检索问答**：基于上传的文档内容进行精准问答
- **知识库管理**：查看、删除已上传文件，清空整个知识库
- **对话历史**：支持多轮对话，保持上下文连贯性
- **流式响应**：问答结果实时流式输出，提升用户体验

## 🛠️ 技术栈

- **后端框架**：
  - LangChain - 大语言模型应用开发框架
  - ChromaDB - 向量数据库
  - DashScope Embeddings - 阿里云百炼嵌入模型
  - ChatTongyi - 通义千问大语言模型

- **前端界面**：
  - Streamlit - 快速构建数据应用的Python框架

- **核心功能**：
  - 文本分割与向量化
  - 相似度检索
  - 提示工程优化
  - MD5 去重机制

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 阿里云百炼 API Key（用于嵌入模型和聊天模型）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd RAG_project
   ```

2. **创建虚拟环境**（推荐）
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
   
   *如果没有 requirements.txt，手动安装以下包：*
   ```bash
   pip install streamlit langchain langchain-chroma dashscope langchain-community langchain-text-splitters python-docx openpyxl
   ```

4. **配置 API Key**
   在侧边栏中输入阿里云百炼 API Key，或设置环境变量：
   ```bash
   export DASHSCOPE_API_KEY="your-api-key-here"
   # Windows
   set DASHSCOPE_API_KEY=your-api-key-here
   ```

### 运行应用

项目包含两个独立的 Streamlit 应用：

1. **知识库管理应用**（文件上传/删除）
   ```bash
   streamlit run app_file_upload.py
   ```
   

2. **智能问答应用**
   ```bash
   streamlit run app_qa.py
   ```
   

   *注意：两个应用使用相同的知识库（chroma_db 目录）*

## 📖 使用方法

### 1. 知识库管理

1. 运行 `app_file_upload.py`
2. 在侧边栏输入阿里云百炼 API Key，
3. 在左侧上传区域选择文件（支持多种格式）
4. 文件会自动分割、向量化并存入 ChromaDB
5. 在右侧查看已上传文件，可选择删除特定文件
6. 可在侧边栏清空整个知识库（危险操作）

### 2. 智能问答

1. 运行 `app_qa.py`
2. 在聊天界面直接提问
3. 系统会自动从知识库检索相关信息
4. 基于检索结果生成回答，支持流式输出
5. 对话历史会自动保存，支持多轮对话

## 🏗️ 项目结构

```
RAG_project/
├── app_file_upload.py          # 知识库管理Web应用
├── app_qa.py                   # 智能问答Web应用
├── rag.py                      # RAG服务核心逻辑
├── knowledge_base.py           # 知识库服务（上传、处理、管理）
├── vector_stores.py            # 向量存储服务
├── config_data.py              # 配置文件
├── file_history_store.py       # 对话历史存储
├── test1.py                    # 测试文件
├── md5.txt                     # MD5去重记录文件
├── chroma_db/                  # ChromaDB向量数据库目录
├── chat_history/               # 对话历史存储目录
├── data/                       # 示例数据目录
└── simple_RAG/                 # 简单RAG示例
```

### 核心模块说明

- **`config_data.py`**：项目配置，包括ChromaDB路径、模型参数、分割设置等
- **`knowledge_base.py`**：知识库服务类，处理文件上传、文本分割、MD5去重、向量存储
- **`vector_stores.py`**：向量存储服务，封装ChromaDB操作
- **`rag.py`**：RAG服务类，整合检索、提示模板、大模型调用
- **`file_history_store.py`**：对话历史存储管理

## ⚙️ 配置说明

在 `config_data.py` 中可以调整以下参数：

```python
# 向量数据库配置
collection_name = 'rag_test1'          # ChromaDB集合名称
persist_directory = "chroma_db"       # 向量数据库存储目录

# 文本分割配置
chunk_size = 500                      # 文本块大小
chunk_overlap = 50                    # 文本块重叠大小
max_split_char_number = 500           # 最小分割字符数

# 检索配置
similarity_threshold = 2              # 检索返回的文档数量

# 模型配置
embedding_model = "text-embedding-v4" # 嵌入模型
chat_model = "qwen3-max"              # 聊天模型
```

## 🔧 核心特性

### MD5 去重机制
- 文件级别去重：避免重复上传相同文件
- 片段级别去重：避免重复存储相同文本内容
- 自动记录：所有处理过的内容MD5保存在 `md5.txt`

### 多格式支持
- 文本文件：TXT、CSV
- 文档文件：PDF、DOCX
- 表格文件：XLSX、XLS

### 智能文本分割
- 根据标点符号和自然段落智能分割
- 可配置的分块大小和重叠区域
- 小文本自动跳过分割

## 📝 示例

### 知识库上传示例
```python
from knowledge_base import KnowledgeBaseService

service = KnowledgeBaseService()
# 上传文本
result = service.upload_by_str("这是示例文本", "example.txt")
print(result)

# 上传文件
with open("document.pdf", "rb") as f:
    result = service.upload_by_file(f.read(), "document.pdf")
print(result)
```

### RAG问答示例
```python
from rag import RagService
import config_data as config

rag_service = RagService()
session_config = {"configurable": {"session_id": "user_001"}}

# 提问
result = rag_service.chain.invoke(
    {"input": "什么是人工智能？"},
    config=session_config
)
print(result)
```

## 🐛 常见问题

### Q: 上传文件后问答应用找不到内容？
A: 确保两个应用使用相同的知识库路径，默认都指向 `chroma_db` 目录。

### Q: API Key 无效？
A: 请确认阿里云百炼账户有足够的额度，且API Key正确。

### Q: 文件上传失败？
A: 检查文件格式是否支持，文件大小是否超过限制（默认100MB）。

### Q: 问答响应慢？
A: 可能是网络问题或模型调用延迟，可尝试调整检索数量或检查API连接。

## 📄 许可证

本项目基于 MIT 许可证开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 📧 联系

如有问题或建议，请通过项目仓库提交 Issue。

---

**温馨提示**：使用前请确保已获取阿里云百炼 API Key，并了解相关计费规则。
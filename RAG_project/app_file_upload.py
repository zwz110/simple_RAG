#基于Streamlit完成WEB网页上传服务
import streamlit as st
from knowledge_base import KnowledgeBaseService
import time
import os

#添加网页标题
st.title("😘知识库更新服务😘")

# 侧边栏：API Key配置 + 清空功能
with st.sidebar:
    st.header("⚙️ 配置")
    # 阿里云百炼API Key
    dashscope_key = st.text_input("阿里云百炼API Key", type="password")
    if dashscope_key:
        os.environ["DASHSCOPE_API_KEY"] = dashscope_key

    # 清空知识库（危险操作，需二次确认）
    st.divider()
    st.header("🗑️ 危险操作")
    if st.button("清空整个知识库", type="primary", use_container_width=True):
        if st.checkbox("⚠️ 确认清空？此操作不可恢复！"):
            with st.spinner("正在清空..."):
                result = st.session_state["service"].delete_all_files()
                if "[成功]" in result:
                    st.success(result)
                else:
                    st.error(result)

# 初始化知识库服务
if "service" not in st.session_state:
    with st.spinner("初始化知识库服务..."):
        if "DASHSCOPE_API_KEY" not in os.environ and not dashscope_key:
            st.error("❌ 请先在侧边栏输入阿里云百炼API Key！")
        else:
            st.session_state["service"] = KnowledgeBaseService()
            st.success("✅ 知识库服务初始化完成！")

# 分栏：上传区 + 删除区
col1, col2 = st.columns(2)

# 左栏：文件上传
with col1:
    st.subheader("📤 文件上传")
    uploader_file = st.file_uploader(
        label="支持 TXT/CSV/PDF/DOCX/XLSX/XLS",
        type=["txt", "csv", "pdf", "docx", "xlsx", "xls"],
        accept_multiple_files=False,
        help="单个文件建议≤100MB"
    )

    if uploader_file is not None and "service" in st.session_state:
        file_name = uploader_file.name
        file_ext = os.path.splitext(file_name)[-1].lower()
        file_size = uploader_file.size / 1024  # KB

        with st.info("📄 文件信息"):
            st.write(f"文件名：{file_name}")
            st.write(f"格式：{file_ext} | 大小：{file_size:.2f} KB")

        if file_size > 100 * 1024:
            st.error("❌ 文件超过100MB，请拆分后上传！")
        else:
            with st.spinner("🚀 正在导入知识库..."):
                result = st.session_state["service"].upload_by_file(
                    file_bytes=uploader_file.getvalue(),
                    filename=file_name
                )
                if "[成功]" in result:
                    st.success(result)
                elif "[跳过]" in result:
                    st.warning(result)
                else:
                    st.error(result)

# 右栏：文件删除
with col2:
    st.subheader("🗑️ 文件删除")
    if "service" in st.session_state:
        # 获取已上传的文件列表
        try:
            with st.spinner("加载已上传文件列表..."):
                file_list = st.session_state["service"].get_uploaded_file()

            if file_list:
                st.info("📋 已上传文件列表")
                # 下拉选择要删除的文件
                selected_file = st.selectbox("请选择要删除的文件", file_list)

                # 删除按钮
                if st.button("删除选中文件", type="primary", use_container_width=True):
                    with st.spinner("正在删除..."):
                        result = st.session_state["service"].delete_file_by_name(selected_file)
                        if "[成功]" in result:
                            st.success(result)
                            # 刷新页面（重新加载文件列表）
                            st.rerun()
                        else:
                            st.warning(result)
            else:
                st.info("📭 知识库中暂无上传的文件")
        except Exception as e:
            st.error(f"❌ 加载文件列表失败：{str(e)}")

# 底部：知识库统计
st.divider()
st.subheader("📊 知识库统计")
if "service" in st.session_state:
    try:
        # 获取总片段数
        all_docs = st.session_state["service"].chroma.get()
        total_chunks = len(all_docs["ids"])
        total_files = len(st.session_state["service"].get_uploaded_file())
        with st.success("统计信息"):
            st.write(f"总文件数：{total_files} | 总文本片段数：{total_chunks}")
    except Exception as e:
        st.warning(f"无法获取统计信息：{str(e)}")
import streamlit as st
from rag import RagService
import config_data as config

#标题
st.title("智能客服")
st.divider()    #分隔符

if "message"not in st.session_state:
    st.session_state["message"]=[{"role":"assistant","content":"你好，有什么可以帮助你的?"}]

if "rag" not in st.session_state:
    st.session_state["rag"]=RagService()

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

#在页面最下方提供用户输入栏
prompt=st.chat_input()
if prompt:
    #在页面输出用户的提问
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user","content":prompt})

    with st.spinner("思考中"):
        # 1. 调用stream方法获取流式迭代器
        stream_iter=st.session_state["rag"].chain.stream({"input":prompt},config=config.session_config)
        full_re=""
        for chunk in stream_iter:
            full_re+=chunk
        st.chat_message("assistant").write_stream(stream_iter)
        st.session_state["message"].append({"role":"assistant","content":full_re})
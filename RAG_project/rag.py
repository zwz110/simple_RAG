import config_data as config
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatTongyi
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from file_history_store import get_history


def print_prompt(prompt):
    print("="*40)
    print("参考资料和问题如下:\n")
    print(prompt)
    print("="*40)
    return prompt

class RagService(object):
    def __init__(self):
        self.vector_service=VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model)
        )
        self.prompt_template=ChatPromptTemplate.from_messages(
            [
                ("system","请严格根据以下参考信息回答用户问题:1.仅基于参考信息进行回答,若参考信息不足以解答问题,直接注明‘暂无相关信息’,禁止编造任何额外内容;2.回答逻辑简洁清晰,语言通俗易懂,紧密贴合用户需求;3.整合所有相关参考信息的关键细节,避免冗余和遗漏。参考资料:{context}。"),
                ("system","并且我提供的用户历史会话信息如下："),
                  MessagesPlaceholder("history"),
                ("user","请回答用户提问：{input}")
            ]
        )
        self.chat_model=ChatTongyi(model=config.chat_model)
        self.chain=self.__get_chain()

    def format_func(self,docs:list):
        if not docs:
            return "无参考资料"
        s1="["
        for doc in docs:
            s1+=doc.page_content
        s1+="]"
        return s1

    def temp1(self,value:dict)->str:
        return value["input"]

    def get_history_message(self,input_dict:dict,config:dict):
        session_id=config.get("configurable",{}).get("session_id")
        if not session_id:
            return []
        history_store=get_history(session_id)
        return history_store.messages

    def __get_chain(self):
        chain=(
            RunnablePassthrough.assign(
               context=RunnableLambda(self.temp1) | self.vector_service.get_retriever() | self.format_func,
               history=lambda x,config: self.get_history_message(x,config)
            ) | self.prompt_template | print_prompt |self.chat_model | StrOutputParser()
        )
        
        conversion_chain=RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",   # 声明用户输入消息在模板中的占位符
            history_messages_key="history" ,    # 声明历史消息在模板中的占位符
            output_messages_key="output"      # 标记模型输出，用于记录历史
        )
        return conversion_chain
    
if __name__ == '__main__':
    # 会话配置（固定格式）
    session_config = {"configurable": {"session_id": "user_001"}}
    
    # 初始化RAG服务并调用
    rag_service = RagService()
    
    # 第一次提问（无历史）
    result1 = rag_service.chain.invoke(
        {"input": "小希的数表"},
        config=session_config  # 注意：第二个参数是config，不是直接传session_config
    )
    print("第一次回答：", result1)
    print("-"*50)
    
    # 第二次提问（带历史）
    result2 = rag_service.chain.invoke(
        {"input":"我应该如何学习这门语言？"},
        config=session_config
    )
    print("第二次回答：", result2)

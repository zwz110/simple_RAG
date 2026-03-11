import json,os
from typing import Sequence
from langchain_core.messages import messages_from_dict,message_to_dict,BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableWithMessageHistory 
import config_data as config


class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self,session_id,storage_path):
        self.session_id=session_id
        self.storage_path=storage_path

        self.file_path=os.path.join(self.storage_path,self.session_id)
        os.makedirs(os.path.dirname(self.file_path),exist_ok=True)

    def add_messages(self,messages:Sequence[BaseMessage])->None:
        all_messages=list(self.messages)
        all_messages.extend(messages)

        new_message=[]
        for message in all_messages:
            d=message_to_dict(message)
            new_message.append(d)
        with open(self.file_path,"w",encoding="utf-8") as f:
            json.dump(new_message,f,ensure_ascii=False)
    @property
    def messages(self) ->list[BaseMessage]:
        try:
            with open(self.file_path,"r",encoding="utf-8")as f:
                content=f.read().strip()
                if not content:
                    return []
                message_data=json.loads(content)
                return messages_from_dict(message_data)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
        
    def clear(self)->None:
        with open(self.file_path,"w",encoding="utf-8") as f:
            json.dump([],f,ensure_ascii=False)

def get_history(session_id):
    return FileChatMessageHistory(session_id,str(config.BASE_DIR / "chat_history"))
# 通过RunnableWithMessageHistory获取一个新的带有历史记录功能的chain


if __name__=='__main__':
     # 如下固定格式，配置当前会话的ID
    session_config = {"configurable": {"session_id": "user_001"}}

    
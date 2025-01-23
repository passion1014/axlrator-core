from typing import Optional
from pydantic import BaseModel


class CodeAssistInfo(BaseModel):
    indexname: str
    question: str
    current_code: str
    sql_request: str

class ChatInfo(BaseModel):
    seq: int
    messenger_type: str # 01:user, 02:agent, 
    message_body: str
    send_time:str

class CodeChatInfo(BaseModel):
    thread_id: str
    question: str
    chat_history: Optional[list[ChatInfo]] = None  # 선택적 필드로 설정, 기본값 None
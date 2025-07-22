from typing import List, Optional
from pydantic import BaseModel
from langchain_core.messages import BaseMessage

class DocumentManualInfo(BaseModel):
    indexname: str = ""
    question: str = ""
    messages: Optional[List[BaseMessage]] = None
    current_code: str = ""
    request_type: str = "" # 01=클래스 주석, 02=메서드 주석, 99=기타
    sql_request: Optional[str] = ""
    metadata: Optional[dict] = None


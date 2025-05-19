from typing import Optional
from pydantic import BaseModel


class DocumentManualInfo(BaseModel):
    indexname: str = ""
    question: str = ""
    current_code: str = ""
    request_type: str = "" # 01=클래스 주석, 02=메서드 주석, 99=기타
    sql_request: Optional[str] = ""


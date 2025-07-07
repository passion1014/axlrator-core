from typing import Optional
from pydantic import BaseModel
from enum import Enum

class RequestType(str, Enum):
    WEBSQUARE = "01" # 웹스퀘어
    XPLATFORM = "02" # 엑스플랫폼
    OTHER = "99"

class UiConvertInfo(BaseModel):
    from_type: RequestType = RequestType.OTHER
    to_type: RequestType = RequestType.OTHER
    
    from_code: str = "" # 변환 대상이 되는 코드
    to_code: str = "" # 변환후 결과 코드
    

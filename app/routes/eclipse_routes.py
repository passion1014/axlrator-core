from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.chain import create_rag_chain, create_term_conversion_chain, create_text_to_sql_chain
from app.config import setup_logging

logger = setup_logging()
router = APIRouter()

# 질문을 위한 요청 모델 정의
class SQLRequest(BaseModel):
    question: str

class CodeRequest(BaseModel):
    question: str

    
# SQL 요청 엔드포인트
@router.post("/api/sql")
async def sql_endpoint(request: SQLRequest):
    chain = create_text_to_sql_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}


# code assist 요청 엔드포인트
@router.post("/api/code")
async def code_endpoint(request: CodeRequest):
    chain = create_rag_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}


# code assist 요청 엔드포인트
@router.post("/api/term")
async def term_conversion_endpoint(request: CodeRequest):
    chain = create_term_conversion_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}

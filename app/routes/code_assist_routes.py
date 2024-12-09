from fastapi import APIRouter
from openai import BaseModel
from app.chain_graph.code_assist_chain import code_assist_chain 
from app.config import setup_logging

logger = setup_logging()
router = APIRouter()

class CodeAssistRequest(BaseModel):
    indexname: str
    question: str
    current_code: str
    sql_request: str


# code assist 요청 엔드포인트
@router.post("/api/code")
async def sample_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    
    chain = code_assist_chain()
    
    state = {"indexname": request.indexname, "question": request.question, "current_code": request.current_code}
    response = chain.invoke(state)
    return {"response": response}

# code assist 요청 엔드포인트
@router.post("/api/autocode")
async def autocode_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    
    state = {"question": request.question}
    response = code_assist_chain(type="01").invoke(state)
    return {"response": response}

# 주석 생성 요청 엔드포인트
@router.post("/api/makecomment")
async def makecomment_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    
    state = {"question": request.question}
    response = code_assist_chain(type="03").invoke(state)
    return {"response": response}

# MapDataUtil 생성 요청 엔드포인트
@router.post("/api/makemapdatautil")
async def make_mapdatautil_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    
    state = {"question": request.question}
    response = code_assist_chain(type="04").invoke(state)
    return {"response": response}

# SQL 생성 요청 엔드포인트
@router.post("/api/makesql")
async def make_sql_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    
    state = {"question": request.question, "sql_request": request.sql_request}
    
    response = code_assist_chain(type="05").invoke(state)
    return {"response": response}



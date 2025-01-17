from typing import List
from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.chain_graph.code_assist_chain import CodeAssistChain, code_assist_chain 
from app.config import setup_logging
from app.db_model.database import SessionLocal
from app.db_model.data_repository import ChatHistoryRepository
from fastapi.responses import JSONResponse, StreamingResponse

logger = setup_logging()
router = APIRouter()
code_assist = CodeAssistChain(index_name="cg_code_assist")

class ChatInfo(BaseModel):
    seq: int
    user_message: str
    ai_message: str
    user_time:str
    ai_time:str

class CodeAssistInfo(BaseModel):
    indexname: str
    question: str
    current_code: str
    sql_request: str
    chat_history: List[ChatInfo]

@router.post("/api/predicate")
async def predicate(request: CodeAssistInfo):
    chain = code_assist.get_chain(task_type="01")
    
    state = {"indexname": request.indexname, "question": request.question, "current_code": request.current_code}
    response = chain.invoke(state)
    return {"response": response}

@router.post("/api/code")
# async def sample_endpoint(request: CodeAssistInfo):
async def sample_endpoint(request: Request):
    try:
        body = await request.json()
        message = CodeAssistInfo.model_validate(body)

        # chain 생성
        chain = code_assist.get_chain(task_type="01")

        # chain 실행
        response = chain.invoke(message)

        # 결과 반환
        return {"response": response}
    
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=500
        )

@router.post("/api/autocode")
async def autocode_endpoint(request: Request):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)

    async def stream_response():
        # `ainvoke` 호출
        result = code_assist_chain(type="01").astream(message, stream_mode="values")
        async for chunk in result:
            print (111111111)
            print (chunk)

        # 결과가 비동기 반복 가능한 객체인지 확인
        # if isinstance(result, dict) or not hasattr(result, "__aiter__"):
        #     # 단일 값 반환
        #     yield str(result)
        # else:
        #     # 비동기 반복 가능한 객체 처리
        #     for chunk in result:
        #         yield chunk

    return StreamingResponse(stream_response(), media_type="text/event-stream")


# 주석 생성 요청 엔드포인트
@router.post("/api/makecomment")
async def makecomment_endpoint(request: Request):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    response = code_assist_chain(type="03").invoke(message)
    return {"response": response}

# MapDataUtil 생성 요청 엔드포인트
@router.post("/api/makemapdatautil")
async def make_mapdatautil_endpoint(request: Request):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    response = code_assist_chain(type="04").invoke(message)
    return {"response": response}

# SQL 생성 요청 엔드포인트
@router.post("/api/makesql")
async def make_sql_endpoint(request: Request):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)

    #TODO: 이력등록
    
    response = code_assist_chain(type="05").invoke(message)
    return {"response": response}

# SQL 생성 요청 엔드포인트
@router.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)

    # chain 호출
    response = code_assist_chain(type="05").invoke(message)
    
    #TODO: 이력등록
    
    return {"response": response}

class ChatHistoryService:
    def __init__(self):
        self.session = SessionLocal()
        self.chat_history_repository = ChatHistoryRepository(self.session)

class CodeAssistService:
    def __init__(self):
        self.session = SessionLocal()
        self.chat_history_repository = ChatHistoryRepository(self.session)
    
    # 인텐트 분류
    def get_question_category():
        
        pass

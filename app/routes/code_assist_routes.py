from typing import List, Optional
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
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
    messenger_type: str # 01:user, 02:agent, 
    message_body: str
    send_time:str

class CodeAssistInfo(BaseModel):
    indexname: str
    question: str
    current_code: str
    sql_request: str
    chat_history: Optional[list[ChatInfo]] = None  # 선택적 필드로 설정, 기본값 None

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

    async def stream_response() :
        async for chunk in code_assist_chain(type="01").astream(message, stream_mode="custom"):
            print("## chucnk=", chunk.content)
            yield chunk.content

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

    #TODO: insert history

    async def stream_response() :
        async for chunk in code_assist_chain(type="05").astream(message, stream_mode="custom"):
            print("## chucnk=", chunk.content)
            yield chunk.content
    return StreamingResponse(stream_response(), media_type="text/event-stream")


# SQL 생성 요청 엔드포인트
@router.post("/api/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        message = CodeAssistInfo.model_validate(body)

        # chain 생성
        chain = code_assist.get_chain(task_type="05")

        # chain 실행
        response = chain.invoke(message)

        # 결과 반환
        return {"response": response}
    
    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=500
        )


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

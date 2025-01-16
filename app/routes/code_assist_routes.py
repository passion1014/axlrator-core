from fastapi import APIRouter
from openai import BaseModel
from app.chain_graph.code_assist_chain import CodeAssistChain, code_assist_chain 
from app.config import setup_logging
from app.db_model.database import SessionLocal
from app.db_model.database_models import ChatHistory, UserInfo
from app.db_model.data_repository import ChatHistoryRepository, UserInfoRepository
from typing import Optional
from typing import List
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

logger = setup_logging()
router = APIRouter()
code_assist = CodeAssistChain(index_name="cg_code_assist")

class CodeAssistRequest(BaseModel):
    indexname: str
    question: str
    current_code: str
    sql_request: str


# code assist 요청 엔드포인트
@router.post("/api/predicate")
async def predicate(request: CodeAssistRequest):
    chain = code_assist.get_chain(task_type="01")
    
    state = {"indexname": request.indexname, "question": request.question, "current_code": request.current_code}
    response = chain.invoke(state)
    return {"response": response}



# code assist 요청 엔드포인트
@router.post("/api/code")
async def sample_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    
    chain = code_assist.get_chain(task_type="01")
    
    state = {"indexname": request.indexname, "question": request.question, "current_code": request.current_code}
    response = chain.invoke(state)
    return {"response": response}



@router.post("/api/autocode")
def autocode_endpoint(request: CodeAssistRequest):
    state = {"question": request.question}
    

    async def stream_response():
        # `ainvoke` 호출
        result = code_assist_chain(type="01").astream(state, stream_mode="values")
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


# @router.post("/api/autocode")
# async def autocode_endpoint(request: CodeAssistRequest):
#     state = {"question": request.question}

#     async def stream_response() -> AsyncGenerator[str, None]:
#         async for chunk in code_assist_chain(type="01").astream(state, stream_mode="chunks"):
#             # Convert the chunk to a JSON string if it's a dictionary or an object
#             if isinstance(chunk, (dict, list)):
#                 print(1)
#                 yield json.dumps(chunk) + "\n"
#             else:
#                 # Convert non-dict types to strings
#                 print(2)
#                 yield str(chunk) + "\n"

#     return StreamingResponse(stream_response(), media_type="text/event-stream")

# async def autocode_endpoint(request: CodeAssistRequest):
#     state = {"question": request.question}

#     async def stream_response() -> AsyncGenerator[str, None]:
#         # astream은 비동기 제너레이터이므로 async for로 처리
#         async for chunk in code_assist_chain(type="01").astream(state, stream_mode="values"):
#             # print(f"### chunk = {chunk}")  # 디버깅 출력
#             yield chunk  # 클라이언트로 스트리밍

#     return StreamingResponse(stream_response(), media_type="text/event-stream")

# @router.post("/api/autocode")
# def autocode_endpoint(request: CodeAssistRequest):
#     state = {"question": request.question}

#     def stream_response():
#         # `ainvoke` 호출
#         result = code_assist_chain(type="01").ainvoke(state, stream_mode="chunks")
#         for chunk in result:
#             yield chunk

#         # 결과가 비동기 반복 가능한 객체인지 확인
#         # if isinstance(result, dict) or not hasattr(result, "__aiter__"):
#         #     # 단일 값 반환
#         #     yield str(result)
#         # else:
#         #     # 비동기 반복 가능한 객체 처리
#         #     for chunk in result:
#         #         yield chunk

#     return StreamingResponse(stream_response(), media_type="text/event-stream")




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

    #이력등록
    
    
    state = {"question": request.question, "sql_request": request.sql_request}    
    response = code_assist_chain(type="05").invoke(state)
    return {"response": response}



class ChatHistoryService:
    def __init__(self):
        self.session = SessionLocal()
        self.chat_history_repository = ChatHistoryRepository(self.session)
   
 
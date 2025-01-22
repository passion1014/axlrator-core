import os
from typing import List, Optional
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.chain_graph.code_assist_chain import CodeAssistChain, code_assist_chain 
from app.config import setup_logging
from app.db_model.database import SessionLocal
from app.db_model.data_repository import ChatHistoryRepository
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from app.chain_graph.code_chat_agent import CodeChatAgent
from psycopg_pool import AsyncConnectionPool
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver

logger = setup_logging()
router = APIRouter()
code_assist = CodeAssistChain(index_name="cg_code_assist")

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

    DB_URI = os.getenv("DATABASE_URL")
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }



    body = await request.json()
    message = CodeChatInfo.model_validate(body)
    
    thread_id = message.thread_id
    
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    question = message.question

    # 채팅을 위한 에이전트
    agent = CodeChatAgent(index_name="cg_code_assist")
    
    
    pool = AsyncConnectionPool(
        conninfo=DB_URI,
        max_size=20,
        kwargs=connection_kwargs,
    )

    async def stream_response():
        async with pool:
            checkpointer = AsyncPostgresSaver(pool)
            graph, _ = agent.get_chain(thread_id=thread_id, checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            input_message = HumanMessage(content=question)

            async for event in graph.astream(
                {"messages": [input_message]}, config, stream_mode="custom"
            ):
                print(f"### {event['messages'][-1].content}")
                yield event["messages"][-1].content

    return StreamingResponse(stream_response(), media_type="text/event-stream")    
    
    
    # checkpointer = AsyncPostgresSaver(pool)
    
    # graph, _ = agent.get_chain(thread_id=thread_id, checkpointer=checkpointer)
    # config = {"configurable": {"thread_id": thread_id}}
    # input_message = HumanMessage(content=question)

    # async def stream_response() :
    #     async for event in graph.astream({"messages": [input_message]}, config, stream_mode="custom"):
    #         print(f"### {event["messages"][-1].content}")
    #         yield event["messages"][-1].content

    # return StreamingResponse(stream_response(), media_type="text/event-stream")





    # async with AsyncConnectionPool(
    #     conninfo=DB_URI,
    #     max_size=20,
    #     kwargs=connection_kwargs,
    # ) as pool:
    #     checkpointer = AsyncPostgresSaver(pool)

    #     graph, _ = agent.get_chain(thread_id=thread_id, checkpointer=checkpointer)
    #     config = {"configurable": {"thread_id": thread_id}}
    #     input_message = HumanMessage(content=question)

    #     async def stream_response() :
    #         async for event in graph.astream({"messages": [input_message]}, config, stream_mode="values"):
    #             yield event["messages"][-1]

    #     return StreamingResponse(stream_response(), media_type="text/event-stream")
    

    # try:
    #     body = await request.json()
    #     message = CodeAssistInfo.model_validate(body)

    #     async def stream_response() :
    #         async for chunk in code_assist.get_chain(task_type="chat").astream(message, stream_mode="custom"):
    #             print("## chucnk=", chunk.content)
    #             yield chunk.content

    #     return StreamingResponse(stream_response(), media_type="text/event-stream")
    
    # except Exception as e:
    #     return JSONResponse(
    #         content={"error": f"An error occurred: {str(e)}"},
    #         status_code=500
    #     )



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

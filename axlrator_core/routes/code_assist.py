import os
import uuid

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession

from axlrator_core.chain_graph.code_assist_chain import CodeAssistChain, code_assist_chain
from axlrator_core.chain_graph.code_chat_agent import CodeChatAgent
from axlrator_core.common.chat_history_manager import checkpoint_to_code_chat_info
from axlrator_core.config import setup_logging
from axlrator_core.dataclasses.code_assist_data import CodeAssistInfo, CodeChatInfo
from axlrator_core.db_model.database import get_async_session
from axlrator_core.db_model.data_repository import RSrcTableRepository

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langfuse.callback import CallbackHandler
from psycopg_pool import AsyncConnectionPool

logger = setup_logging()
router = APIRouter()



@router.post("/api/autocompletion")
async def call_api_autocompletion(
    request: Request, 
    session: AsyncSession = Depends(get_async_session)
) -> Response:
    '''
    자동완성(ghost text) / AI.AUTOCODE_URL
    '''
    
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    # CodeAssistChain class 선언
    code_assist = CodeAssistChain(index_name="code_assist", session=session)

    # 스트리밍이 아닐 경우 일반 응답 반환
    result = code_assist.chain_autocompletion().invoke(message)
    return JSONResponse(content={"result": result})



@router.post("/api/code-contextual")
@router.post("/api/code")
async def call_api_code(
    request: Request, 
    session = Depends(get_async_session)
):
    '''
    명령형 코드생성 / AI.CODE_URL
    '''
    
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    callback_handler = CallbackHandler()
    
    # CodeAssistChain class 선언
    code_assist = CodeAssistChain(index_name="code_assist", session=session)

    # 스트리밍 여부를 결정하는 플래그 (body에 "stream": true/false 추가)
    stream_mode = body.get("stream", False)
    if stream_mode:
        async def stream_response() :
            async for chunk in code_assist.chain_codeassist().astream(message, stream_mode="custom", config={"callbacks": [callback_handler]}):
                yield chunk.content
        return StreamingResponse(stream_response(), media_type="text/event-stream")

    else:
        # 스트리밍이 아닐 경우 일반 응답 반환
        result_generator = code_assist.chain_codeassist().astream(message, stream_mode="custom", config={"callbacks": [callback_handler]})
        result_text = "".join([chunk.content async for chunk in result_generator])
        return JSONResponse(content={"result": result_text})


@router.post("/api/autocode")
async def autocode_endpoint(
    request: Request, 
    # file: UploadFile = File,
    session: AsyncSession = Depends(get_async_session)
):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    # _file = file

    form_data = await request.form()

    # 파일 데이터 가져오기
    uploaded_file = form_data.get("file")
    if uploaded_file:
        # 파일 이름 가져오기
        file_name = uploaded_file.filename
        
        # 파일 내용 읽기
        file_content = await uploaded_file.read()
        
        # 파일 내용 처리
        # ...

    # 다른 폼 데이터 가져오기
    question = form_data.get("question")
    context = form_data.get("context")
    # ...

    message = CodeAssistInfo(
        question=question,
        context=context,
        # ...
    )

    
    
    call_type = "01" # 코드 생성
    
    # 단순히 테이블명 하나만 들어올 경우 MapDataUtil을 만든다.
    rsrc_table_repository = RSrcTableRepository(session=session)
    table_data = await rsrc_table_repository.get_data_by_table_name(table_name=message.question)
    
    if table_data:
        call_type="04" # MapDataUtil 생성
        message.sql_request = message.question

    chain = await code_assist_chain(type=call_type, session=session)

    async def stream_response() :
        async for chunk in chain.astream(message, stream_mode="custom"):
            yield chunk.content

    return StreamingResponse(stream_response(), media_type="text/event-stream")



# 주석 생성 요청 엔드포인트
@router.post("/api/makecomment")
async def makecomment_endpoint(
    request: Request,
    session = Depends(get_async_session)
):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    chain = await code_assist_chain(type="03", session=session)

    async def stream_response() :
        async for chunk in chain.astream(message, stream_mode="custom"):
            yield chunk.content
    return StreamingResponse(stream_response(), media_type="text/event-stream")


# MapDataUtil 생성 요청 엔드포인트
@router.post("/api/makemapdatautil")
async def make_mapdatautil_endpoint(
    request: Request,
    session = Depends(get_async_session)
):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    chain = await code_assist_chain(type="04", session=session)

    async def stream_response() :
        async for chunk in chain.astream(message, stream_mode="custom"):
            yield chunk.content
    return StreamingResponse(stream_response(), media_type="text/event-stream")


# SQL 생성 요청 엔드포인트
@router.post("/api/makesql")
async def make_sql_endpoint(
    request: Request,
    session = Depends(get_async_session)
):
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    chain = await code_assist_chain(type="05", session=session)

    async def stream_response() :
        async for chunk in chain.astream(message, stream_mode="custom"):
            yield chunk.content
    return StreamingResponse(stream_response(), media_type="text/event-stream")

# SQL 생성 요청 엔드포인트
@router.post("/api/get-threadid")
async def get_thread_id(request: Request):
    return str(uuid.uuid4())


@router.post("/api/chat")
async def chat(
    request: Request,
    session = Depends(get_async_session)
):
    # request 값 확인
    body = await request.json()
    message = CodeChatInfo.model_validate(body)
    
    # 항상 한글로 답변하도록    
    question = message.question + "\n** Think in English but write the response in 한국어(korean). **"
    
    # thread_id 셋팅
    thread_id = message.thread_id or str(uuid.uuid4())
    # config셋팅
    config = {"configurable": {"thread_id": thread_id}}


    database_url = os.getenv("DATABASE_URL")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    pool = AsyncConnectionPool(
        conninfo=database_url,
        max_size=50,
        timeout=60,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
        },
    )
    checkpointer = AsyncPostgresSaver(pool)
    checkpoint = await checkpointer.aget(config)

    code_chat_info = checkpoint_to_code_chat_info(thead_id=thread_id, checkpoint=checkpoint)

    # 채팅을 위한 에이전트
    agent = await CodeChatAgent.create(index_name="cg_code_assist", session=session)
        
    graph, _ = agent.get_chain(thread_id=thread_id, checkpointer=checkpointer)
    input_message = HumanMessage(content=question)

    async def stream_response() :
        async for event in graph.astream({"messages": [input_message]}, config, stream_mode="custom"): #stream_mode = values
            if event.content and len(event.content) > 0:
                content = event.content[-1]['text'] if isinstance(event.content[-1], dict) else event.content
                yield content

    return StreamingResponse(stream_response(), media_type="text/event-stream")




# class ChatHistoryService:
#     def __init__(self):
#         self.session = get_async_session_generator()
#         self.chat_history_repository = ChatHistoryRepository(self.session)

# class CodeAssistService:
#     def __init__(self):
#         self.session = get_async_session_generator()
#         self.chat_history_repository = ChatHistoryRepository(self.session)

#     # 인텐트 분류
#     def get_question_category():
#         pass

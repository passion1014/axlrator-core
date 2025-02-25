
import json
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.chain_graph.code_assist_chain import code_assist_chain
from app.chain_graph.code_chat_agent import CodeChatAgent
from app.common.chat_history_manager import checkpoint_to_code_chat_info
from app.dataclasses.code_assist_data import CodeAssistInfo
from app.db_model.database import get_async_session
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage


router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True


@router.post("/v1/chat/completions", response_class=JSONResponse)
async def get_completions(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    '''
    연결 > Edit Connection >
        url = http://localhost:8001/aifred-oi/v1
    '''
    body = await request.json()
    
    try:
        message = ChatCompletionRequest.model_validate(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {e}")

    model = message.model
    messages = message.messages
    stream_mode = message.stream

    if not messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    question = messages[-1].content + "\n** Think in English but write the response in 한국어(korean). **"

    thread_id = str(uuid.uuid4())
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
    agent = await CodeChatAgent.create(index_name="cg_code_assist", session=session) 
    graph, _ = agent.get_chain(thread_id=thread_id, checkpointer=checkpointer)
    input_message = HumanMessage(content=question)

    if stream_mode:
        async def stream_response():
            async for event in graph.astream({"messages": [input_message]}, config, stream_mode="custom"):
                if event.content and len(event.content) > 0:
                    content = event.content[-1]['text'] if isinstance(event.content[-1], dict) else event.content
                    chunk = json.dumps({
                        "id": thread_id,
                        "object": "chat.completion.chunk",
                        "created": int(uuid.uuid4().time_low),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": None
                        }]
                    })
                    yield f"data: {chunk}\n\n"

            yield f"data: {json.dumps({'id': thread_id, 'object': 'chat.completion.chunk', 'created': int(uuid.uuid4().time_low), 'model': model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]})}\n\n"
        return StreamingResponse(stream_response(), media_type="text/event-stream")

    else:
        response = {
            "id": thread_id,
            "object": "chat.completion",
            "created": int(uuid.uuid4().time_low),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "이것은 일반 응답입니다."},
                    "finish_reason": "stop"
                }
            ]
        }
        return JSONResponse(content=response)



@router.get("/v1/models", response_class=JSONResponse)
async def get_models(request: Request):
    """
    /models 엔드포인트를 통해 사용 가능한 모델 목록을 반환합니다.
    """
    # 예시 모델 목록
    models = {
        "object": "list",
        "data": [
            {
                "id": "code_assist", # The model identifier, which can be referenced in the API endpoints.
                "object": "model", # The Unix timestamp (in seconds) when the model was created.
                "created": 1686935002, # The object type, which is always "model".
                "owned_by": "organization-owner1" # The organization that owns the model.
            },
            {
                "id": "chat",
                "object": "model",
                "created": 1686935002,
                "owned_by": "organization-owner2"
            },
            {
                "id": "기타",
                "object": "model",
                "created": 1686935002,
                "owned_by": "openai3"
            }
        ]
    }
    
    return JSONResponse(content=models)

# @router.post("/v1/chat/completions", response_class=JSONResponse)
# async def get_completions(
#     request: Request,
#     session = Depends(get_async_session)
# ):
#     '''
#     참고 : https://platform.openai.com/docs/api-reference/making-requests
#     {
#         "model": "code_assist",
#         "messages": [{"role": "user", "content": "Say this is a test!"}],
#         "temperature": 0.7
#     }
#     '''

#     # request 값 확인
#     body = await request.json()
#     message = ChatCompletionRequest.model_validate(body)
    
    
#     model = body.get("model", "")
#     question = body.get("messages", [{}])[0].get("content", "") + "\n** Think in English but write the response in 한국어(korean). **" # 항상 한글로 답변하도록
    
#     # thread_id 생성 및 config 셋팅
#     thread_id = str(uuid.uuid4()) # message.thread_id or str(uuid.uuid4())
#     config = {"configurable": {"thread_id": thread_id}}

#     database_url = os.getenv("DATABASE_URL")
#     if database_url.startswith("postgresql+asyncpg://"):
#         database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

#     pool = AsyncConnectionPool(
#         conninfo=database_url,
#         max_size=50,
#         timeout=60,
#         kwargs={
#             "autocommit": True,
#             "prepare_threshold": 0,
#         },
#     )
#     checkpointer = AsyncPostgresSaver(pool)
#     # checkpoint = await checkpointer.aget(config)
#     # code_chat_info = checkpoint_to_code_chat_info(thead_id=thread_id, checkpoint=checkpoint)

#     # 채팅을 위한 에이전트
#     agent = await CodeChatAgent.create(index_name="cg_code_assist", session=session) 
#     graph, _ = agent.get_chain(thread_id=thread_id, checkpointer=checkpointer)
#     input_message = HumanMessage(content=question)

#     # 스트리밍 여부를 결정하는 플래그 (body에 "stream": true/false 추가)
#     stream_mode = body.get("stream", True)

#     async def stream_response() :
#         async for event in graph.astream({"messages": [input_message]}, config, stream_mode="custom"): #stream_mode = values
#             if event.content and len(event.content) > 0:
#                 content = event.content[-1]['text'] if isinstance(event.content[-1], dict) else event.content
#                 yield content
#     return StreamingResponse(stream_response(), media_type="text/event-stream")






#     if stream_mode:
#         async def stream_response() :
#             async for event in graph.astream({"messages": [input_message]}, config, stream_mode="custom"): #stream_mode = values
#                 if event.content and len(event.content) > 0:
#                     content = event.content[-1]['text'] if isinstance(event.content[-1], dict) else event.content
#                     yield content
#         return StreamingResponse(stream_response(), media_type="text/event-stream")

#     else:
#         # 스트리밍이 아닐 경우, 비동기 제너레이터의 결과를 리스트로 변환 후 반환
#         result_generator = await graph.ainvoke({"messages": [input_message]}, config, stream_mode="custom")
#         # 비동기 제너레이터에서 결과를 가져오기 위해 리스트 컴프리헨션 사용
#         result_text = "".join([chunk.content for chunk in result_generator])

#         response = ChatCompletionResponse(
#             id="chatcmpl-12345",
#             object="chat.completion",
#             created=1700000000,  # 예제 timestamp
#             model=message.model,
#             choices=[
#                 ChatCompletionResponseChoice(
#                     index=0,
#                     message=ChatMessage(role="assistant", content=result_text),
#                     finish_reason="stop"
#                 )
#             ]
#         )
        
#         return response
        
        
        
        
        # return {
        #     "id": "chatcmpl-abc123",
        #     "object": "chat.completion",
        #     "created": 1677858242,
        #     "model": model,
        #     "usage": {
        #         "prompt_tokens": 13,
        #         "completion_tokens": 7,
        #         "total_tokens": 20,
        #         "completion_tokens_details": {
        #             "reasoning_tokens": 0,
        #             "accepted_prediction_tokens": 0,
        #             "rejected_prediction_tokens": 0
        #         }
        #     },
        #     "choices": [
        #         {
        #             "message": {
        #                 "role": "assistant",
        #                 "content": result_text
        #             },
        #             "logprobs": "",
        #             "finish_reason": "stop",
        #             "index": 0
        #         }
        #     ]
        # }



@router.post("/api/query")
async def call_rag_api(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> JSONResponse:
    body = await request.json()
    message = CodeAssistInfo.model_validate(body)
    
    chain = await code_assist_chain(type="02", session=session)
    
    # 스트리밍이 아닐 경우, 비동기 제너레이터의 결과를 리스트로 변환 후 반환
    result_generator = chain.astream(message, stream_mode="custom")
    result_text = "".join([chunk.content async for chunk in result_generator])
    return JSONResponse(content={"result": result_text})


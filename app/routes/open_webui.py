
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
from app.dataclasses.code_assist_data import CodeAssistInfo
from app.db_model.database import get_async_session
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True

# http://localhost:8080/api/v1/tasks/auto/completions
@router.post("/v1/task/auto/completions", response_class=JSONResponse)
async def task_auto_completions(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    print(f"### /task/auto/completions Request = {request}")


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
    stream_mode = message.stream
    # messages = message.messages
    messages = [convert_chat_message(m) for m in message.messages]

    if not messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    agent = await CodeChatAgent.create(index_name="cg_code_assist", session=session) 
    graph, _ = agent.get_chain(thread_id=thread_id)

    if stream_mode:
        async def stream_response():
            async for event in graph.astream({"messages": messages}, config, stream_mode="custom"):
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
        result = await graph.ainvoke({"messages": messages}, config)

        if result["messages"]:
            content = "".join(
                m.content for m in result["messages"] if isinstance(m, AIMessage) and m.content
            )
        else:
            content = ""
        
        response = {
            "id": thread_id,
            "object": "chat.completion",
            "created": int(uuid.uuid4().time_low),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop"
                }
            ]
        }
        return JSONResponse(content=response)


        # response = {
        #     "id": thread_id,
        #     "object": "chat.completion",
        #     "created": int(uuid.uuid4().time_low),
        #     "model": model,
        #     "choices": [
        #         {
        #             "index": 0,
        #             "message": {"role": "assistant", "content": "이것은 일반 응답입니다."},
        #             "finish_reason": "stop"
        #         }
        #     ]
        # }
        # return JSONResponse(content=response)

def convert_chat_message(chat_message):
    """ChatMessage를 LangChain의 Message 객체로 변환"""
    if chat_message.role == "user":
        return HumanMessage(content=chat_message.content)
    elif chat_message.role == "assistant":
        return AIMessage(content=chat_message.content)
    elif chat_message.role == "system":
        return SystemMessage(content=chat_message.content)
    return chat_message  # 이미 올바른 형식이면 그대로 반환


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
                "id": "AXLR-Code",
                "object": "model",
                "created": 1686935002,
                "owned_by": "aifred"
            },
            {
                "id": "chat",
                "object": "model",
                "created": 1686935002,
                "owned_by": "aifred"
            }
        ]
    }
    
    return JSONResponse(content=models)


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


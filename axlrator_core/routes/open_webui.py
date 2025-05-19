
import json
import os
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Union

from axlrator_core.chain_graph.agent_state import CodeAssistAutoCompletion
from axlrator_core.chain_graph.code_assist_chain import CodeAssistChain, code_assist_chain
from axlrator_core.chain_graph.code_chat_agent import CodeChatAgent
from axlrator_core.chain_graph.document_manual_chain import DocumentManualChain
from axlrator_core.dataclasses.code_assist_data import CodeAssistInfo
from axlrator_core.dataclasses.document_manual_data import DocumentManualInfo
from axlrator_core.db_model.database import get_async_session
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langfuse.callback import CallbackHandler

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True
    
class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]  # 하나 또는 여러 개의 prompt 가능
    suffix: Optional[str] = None
    max_tokens: Optional[int] = 16
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    best_of: Optional[int] = 1
    logit_bias: Optional[dict] = None
    user: Optional[str] = None


class Choice(BaseModel):
    text: str
    index: int
    logprobs: Optional[dict] = None
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: Optional[str] = None
    choices: List[Choice]
    usage: Usage


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
    print(f"### /v1/chat/completions - body = {body}")
    
    try:
        message = ChatCompletionRequest.model_validate(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {e}")
    
    callback_handler = CallbackHandler()

    model = message.model
    stream_mode = message.stream
    # messages = message.messages
    messages = [convert_chat_message(m) for m in message.messages]

    if not messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    if model == "chat":
        print("### DocumentManualChain 체인을 생성합니다.")

        document_manual_info = DocumentManualInfo(
            indexname="manual_document",
            question=body['messages'][0]['content']
        )
        
        document_manual_chain = DocumentManualChain(index_name="manual_document", session=session)
        result = document_manual_chain.chain_manual_query().invoke(document_manual_info, config={"callbacks": [callback_handler]})
        # return JSONResponse(content={"result": result})
        
        response = {
            "id": thread_id,
            "object": "chat.completion",
            "created": int(uuid.uuid4().time_low),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": result['response']},
                    "finish_reason": "stop"
                }
            ]
        }
        return JSONResponse(content=response)        
        
    else:
        print("### CodeChatAgent 체인을 생성합니다.")
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


@router.post("/v1/completions")
async def call_api_autocompletion(
    request: Request, 
    session: AsyncSession = Depends(get_async_session)
):
    body = await request.json()
    
    try:
        message = CompletionRequest.model_validate(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {e}")
    
    # prompt가 list면 첫 번째만 사용
    prompt_text = message.prompt[0] if isinstance(message.prompt, list) else message.prompt

    # CodeAssistAutoCompletion에 필요한 필드 생성
    state: CodeAssistAutoCompletion = {
        "prompt": "",
        "current_code": prompt_text,
        "response": "" 
    }
    
    # CodeAssistChain 실행
    code_assist = CodeAssistChain(index_name="cg_code_assist", session=session)
    result_state = code_assist.chain_autocompletion().invoke(state)
    completion_text = result_state["response"][0] if result_state["response"] else ""

    # OpenAI 호환 응답 생성
    response = CompletionResponse(
        id=f"cmpl-{uuid.uuid4().hex[:24]}",
        object="text_completion",
        created=int(time.time()),
        model=message.model,
        system_fingerprint="fp_mocked123456",
        choices=[
            Choice(
                text=completion_text,
                index=0,
                logprobs=None,
                finish_reason="stop"
            )
        ],
        usage=Usage(
            prompt_tokens=10, # → 추정 또는 tokenizer 사용해서 계산
            completion_tokens=len(completion_text.split()),  # 간단한 추정
            total_tokens=10 + len(completion_text.split())
        )
    )
    return JSONResponse(content=response.model_dump())



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


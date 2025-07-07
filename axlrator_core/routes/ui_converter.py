import os
import uuid

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession

from axlrator_core.chain_graph.code_assist_chain import CodeAssistChain, code_assist_chain
from axlrator_core.chain_graph.code_chat_agent import CodeChatAgent
from axlrator_core.chain_graph.ui_convert_chain import UiConvertChain, UiConvertState
from axlrator_core.common.chat_history_manager import checkpoint_to_code_chat_info
from axlrator_core.config import setup_logging
from axlrator_core.dataclasses.code_assist_data import CodeAssistInfo, CodeChatInfo
from axlrator_core.dataclasses.ui_convert_data import UiConvertInfo
from axlrator_core.db_model.database import get_async_session
from axlrator_core.db_model.data_repository import RSrcTableRepository

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langfuse.callback import CallbackHandler
from psycopg_pool import AsyncConnectionPool

from axlrator_core.process.contextual_process import generate_code_context

logger = setup_logging()
router = APIRouter()

'''
@router.post("/api/convert-ui")
'''

@router.post("/api/convert-ui")
async def call_api_conver_ui(
    request: Request, 
    session: AsyncSession = Depends(get_async_session)
) -> Response:
    '''화면 전환 요청 시 호출되는 엔드포인트

    Args:
        request (Request): 요청 객체
        session (AsyncSession): 데이터베이스 세션

    Returns:
        Response: 응답 객체
    '''
    
    body = await request.json()
    message = UiConvertInfo.model_validate(body)
    callback_handler = CallbackHandler()
    
    ui_convert_input: UiConvertState = {
        "prompt": "",
        "from_code": message.from_code,
        "to_code": "",
        "from_type": message.from_type.value,  # assuming RequestType is an Enum
        "to_type": message.to_type.value
    }
    
    
    ui_convert_chain = UiConvertChain(index_name="code_assist", session=session)

    # 스트리밍이 아닐 경우 일반 응답 반환
    result = ui_convert_chain.chain_convert().invoke(ui_convert_input, config={"callbacks": [callback_handler]})
    return JSONResponse(content={"result": result})

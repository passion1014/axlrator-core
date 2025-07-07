import os
import uuid

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from sqlalchemy.ext.asyncio import AsyncSession

from axlrator_core.chain_graph.document_manual_chain import DocumentManualChain, combine_documents_with_next_content
from axlrator_core.common.chat_history_manager import checkpoint_to_code_chat_info
from axlrator_core.config import setup_logging
from axlrator_core.dataclasses.document_manual_data import DocumentManualInfo
from axlrator_core.db_model.database import get_async_session
from axlrator_core.db_model.data_repository import RSrcTableRepository

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langfuse.callback import CallbackHandler
from psycopg_pool import AsyncConnectionPool

from axlrator_core.process.contextual_process import generate_code_context

logger = setup_logging()
router = APIRouter()



@router.post("/api/contextual-query")
async def call_api_contextual_query(
    request: Request, 
    session: AsyncSession = Depends(get_async_session)
) -> Response:
    body = await request.json()
    message = DocumentManualInfo.model_validate(body)
    callback_handler = CallbackHandler()
    
    # DocumentManualChain class 선언
    document_manual_chain = DocumentManualChain(index_name="manual_document", session=session)

    # result_generator = document_manual_chain.chain_manual_query().astream(message, stream_mode="custom", config={"callbacks": [callback_handler]})
    # result_text = "".join([chunk.content async for chunk in result_generator])
    # return JSONResponse(content={"result": result_generator['response']})

    result = document_manual_chain.chain_manual_query().invoke(message, config={"callbacks": [callback_handler]})
    return JSONResponse(content={"result": result})


@router.post("/api/combine-contextual-test")
async def call_api_combine_contextual_query(
    request: Request, 
    session: AsyncSession = Depends(get_async_session)
) -> Response:
    body = await request.json()
    
    
    result = combine_documents_with_next_content(body)
    
    return JSONResponse(content={"result": result})


from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import Session
from sqlalchemy import select
from app.common.exception_handler import handle_exceptions
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model import database_models
from app.db_model.data_repository import FaissInfoRepository
from app.db_model.database import get_async_session
from app.vectordb.faiss_vectordb import FaissVectorDB, get_vector_db
from sqlalchemy.ext.asyncio import AsyncSession


logger = setup_logging()
router = APIRouter()


@router.get("/v1/get-vectors")
@handle_exceptions
async def get_vector_index_list(
    request: Request, 
    session = Depends(get_async_session)
):
    try:
        data = await request.json()
        index_id = data.get('index_id')
        index_name = data.get('index_name')
        
        faissinfo_repository = FaissInfoRepository(session=session)
        faiss_infos = await faissinfo_repository.get_faiss_infos(index_id=index_id, index_name=index_name)
        
        if not faiss_infos:
            return {
                "success": False,
                "message": "FAISS 정보를 찾을 수 없습니다."
            }
        
        search_results = [
            faiss_info.__dict__ for faiss_info in faiss_infos
        ]

        # 결과 반환
        return {
            "success": True,
            "message": "검색이 성공적으로 완료되었습니다.",
            "data": search_results
        }

    except Exception as e:
        logger.error(f"FAISS 목록 조회 중 오류 발생: {str(e)}")
        return {
            "success": False, 
            "message": f"FAISS 목록 조회 중 오류 발생: {str(e)}"
        }


@router.get("/v1/search-vector-datas")
@handle_exceptions
async def get_vector_index_list(
    request: Request, 
    session = Depends(get_async_session)
):
    try:
        # 요청 데이터 파싱
        data = await request.json()
        
        index_name = data.get('index_name')
        search_text = data.get('search_text')
        top_k = data.get('top_k', 5) # 기본값 5
        
        # 필수 파라미터 체크
        if not index_name or not search_text:
            return {
                "success": False,
                "message": "index_name과 search_text는 필수 파라미터입니다."
            }

        ### 아래 내용은 조회할때 마다 초기화해서는 안되는 부분이다. 서버 로딩시 초기화할지 확인 필요 ###
        
        # FAISS 벡터 DB 초기화
        faiss_vector_db = await get_vector_db(session=session, index_name=index_name)
        # faiss_info = faiss_vector_db.psql_docstore.get_faiss_info()
        
        # 유사도 검색 실행
        search_results = await faiss_vector_db.search_similar_documents(query=search_text, k=top_k)
        
        # 결과 반환
        return {
            "success": True,
            "message": "검색이 성공적으로 완료되었습니다.",
            "data": search_results
        }

    except Exception as e:
        logger.error(f"FAISS 검색 중 오류 발생: {str(e)}")
        
        return {
            "success": False, 
            "message": f"검색 중 오류가 발생했습니다: {str(e)}"
        }



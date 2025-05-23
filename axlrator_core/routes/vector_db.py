from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import Session
from sqlalchemy import select
from axlrator_core.config import TEMPLATE_DIR, setup_logging
from axlrator_core.db_model import database_models
from axlrator_core.db_model.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

from axlrator_core.vectordb.vector_store import create_collection, get_vector_store


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/list", response_class=HTMLResponse)
async def ui_faiss_list(request: Request):
    return templates.TemplateResponse("/faissManage/faissList.html", {"request": request, "message": "건설공제 FAISS관리"})


# FAISS Info 데이터를 가져오는 엔드포인트
@router.get("/api/faiss_info")
async def get_faiss_info(session: AsyncSession = Depends(get_async_session)):
    async with session.begin():
        faiss_info_list = await session.scalars(select(database_models.FaissInfo))
        return [{"id": info.id,
                "index_name": info.index_name,
                "index_desc": info.index_desc,
                "index_file_path": info.index_file_path,
                "modified_at": info.modified_at,
                "created_at": info.created_at,
                "modified_by": info.modified_by,
                "created_by": info.created_by} for info in faiss_info_list]


# FAISS 벡터 조회를 위한 엔드포인트
@router.post("/api/search")
async def search_faiss_vector(request: Request, session: AsyncSession = Depends(get_async_session)):
    # try:
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

        vector_store = get_vector_store(collection_name=index_name)
        search_results = vector_store.similarity_search_with_score(query=search_text, k=2) 

        # 결과 반환
        return {
            "success": True,
            "message": "검색이 성공적으로 완료되었습니다.",
            "data": search_results
        }

    # except Exception as e:
    #     logger.error(f"FAISS 검색 중 오류 발생: {str(e)}")
    #     return {
    #         "success": False, 
    #         "message": f"검색 중 오류가 발생했습니다: {str(e)}"
    #     }



# FAISS 저장을 위한 엔드포인트
@router.post("/api/create")
async def create_faiss_info(request: Request, session: AsyncSession = Depends(get_async_session)):
    # try:
        # 요청 데이터 파싱
        data = await request.json()
        
        index_name = data.get('index_name')
        index_desc = data.get('index_desc')
        
        # index_desc가 비어있으면 기본값 설정
        if not index_desc:
            index_desc = f"{index_name}를 위한 FAISS정보"

        # 받은 파라미터로 초기화
        # faiss_vector_db = await get_vector_db(session=session, collection_name=index_name)
        
        vector_store = create_collection(collection_name=index_name)
        fields = vector_store.vector_fields
        

        # # 기존재하는지 체크
        # faiss_info = await faiss_vector_db.psql_docstore.get_faiss_info()
        # if faiss_info is not None:
        #     return {
        #         "success": True,
        #         "message": "이미 FAISS 정보가 존재합니다.",
        #         "data": {
        #             "id": faiss_info.id,
        #             "index_name": faiss_info.index_name,
        #             "index_desc": faiss_info.index_desc,
        #             "index_file_path": faiss_info.index_file_path
        #         }
        #     }
            
        # # FAISS 데이터 insert
        # faiss_info = faiss_vector_db.psql_docstore.insert_faiss_info(index_desc=index_desc)


        return {
            "success": True,
            "message": "FAISS 정보가 성공적으로 저장되었습니다.",
            "data": {
                # "id": faiss_info.id,
                "index_name": index_name,
                "index_desc": index_desc,
                # "index_file_path": faiss_info.index_file_path
            }
        }
        
    # except Exception as e:
    #     session.rollback()
    #     return {
    #         "success": False,
    #         "message": f"FAISS 정보 저장 중 오류가 발생했습니다: {str(e)}"
    #     }

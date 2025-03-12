from datetime import datetime
from fastapi import APIRouter, Depends, Request
from app.common.exception_handler import handle_exceptions
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model.data_repository import FaissInfoRepository
from app.db_model.database import get_async_session

from app.vectordb.vector_store import get_vector_store

logger = setup_logging()
router = APIRouter()

@router.get("/v1/get-vectors")
@handle_exceptions
async def search_vector_datas(
    request: Request, 
    session = Depends(get_async_session)
):
    try:
        data = await request.json()
        index_id = data.get('index_id')
        index_name = data.get('index_name')
        
        faissinfo_repository = FaissInfoRepository(session=session)
        faiss_infos = await faissinfo_repository.get_faisses(index_id=index_id, index_name=index_name)
        
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
async def search_vector_datas(
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
        if not index_name and not search_text:
            return {
                "success": False,
                "message": "index_name과 search_text 중 값이 있어야 합니다"
            }

        ### 아래 내용은 조회할때 마다 초기화해서는 안되는 부분이다. 서버 로딩시 초기화할지 확인 필요 ###
        
        # FAISS 벡터 DB 초기화
        vector_store = get_vector_store(collection_name=index_name)
        search_results = vector_store.similarity_search_with_score(query=search_text, k=top_k) 
        
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

@router.get("/v1/get-vector-chunkdatas")
@handle_exceptions
async def get_vector_chunkdatas(
    request: Request, 
    session = Depends(get_async_session)
):
    data = await request.json()
    index_name = data.get('index_name')
    from_date = data.get('from_date')
    to_date = data.get('to_date')
    data_name = data.get('data_name')
    data_type = data.get('data_type')
    
    # from_date와 to_date 필수 체크
    if not from_date or not to_date:
        return {
            "success": False,
            "message": "from_date와 to_date는 필수 파라미터입니다."
        }
    
    faissinfo_repository = FaissInfoRepository(session=session)
    faiss_datas = await faissinfo_repository.get_faiss_datas(
        index_name=index_name,
        from_date=datetime.fromisoformat(from_date) if from_date else None,
        to_date=datetime.fromisoformat(to_date) if to_date else None,
        data_name=data_name,
        data_type=data_type
    )

    if not faiss_datas:
        return {
            "success": False,
            "message": "벡터 데이터 정보를 찾을 수 없습니다."
        }
    
    search_results = [
        {  # 딕셔너리 리터럴 추가
            "index_name": data['faiss_info']['index_name'],
            "index_desc": data['faiss_info']['index_desc'],
            "index_file_path": data['faiss_info']['index_file_path'],
            "data_name": data['chunked_data']['data_name'],
            "data_type": data['chunked_data']['data_type'],
            "content": data['chunked_data']['content'],
            "context_chunk": data['chunked_data']['context_chunk'],
            "document_metadata": data['chunked_data']['document_metadata'],
            "modified_at": data['chunked_data']['modified_at'],
            "created_at": data['chunked_data']['created_at'],
            "modified_by": data['chunked_data']['modified_by'],
            "created_by": data['chunked_data']['created_by']
        }
        for data in faiss_datas
    ]
    
    # 결과 반환
    return {
        "success": True,
        "message": "검색이 성공적으로 완료되었습니다.",
        "data": search_results
    }


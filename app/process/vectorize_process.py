
from uuid import uuid4
from app.db_model.data_repository import ChunkedDataRepository, OrgRSrcRepository
from app.db_model.database import get_async_session
# from app.vectordb.faiss_vectordb import get_vector_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.vectordb.vector_store import get_vector_store
from langchain_core.documents import Document

async def process_vectorize(collection_name: str, session: AsyncSession, org_resrc):
    """
    데이터를 벡터화하여 처리합니다.

    Returns:
        벡터화된 인덱스 번호
    """
    
    # index_name 필수값 체크
    if not collection_name:
        raise ValueError("collection_name 필수 파라미터입니다.")
    
    # org_resrc 필수값 체크
    if org_resrc is None:
        raise ValueError("org_resrc는 필수 파라미터입니다.")
    
        
    vector_store = get_vector_store(collection_name=collection_name)
    orgrsrc_repository = OrgRSrcRepository(session=session)
    chunked_data_Repository = ChunkedDataRepository(session=session)
    
    # org_resrc.id로 ChunkedData 를 조회
    chunked_data_list = await chunked_data_Repository.get_chunked_data_by_org_resrc_id(org_resrc_id=org_resrc.id)

    uuids = [str(uuid4()) for _ in range(len(chunked_data_list))]
    
    # 각각의 ChunkedData에 대해 처리
    documents = [
        Document(
            page_content=data.content,
            metadata={"id": uuid, **(data.document_metadata if isinstance(data.document_metadata, dict) else {})}
        )
        for data, uuid in zip(chunked_data_list, uuids)
    ]
    

    # vector_store에 저장
    vector_ids = vector_store.add_documents(documents=documents, ids=uuids)

    # chunked_data 업데이트
    for data, document, uuid, vector_id in zip(chunked_data_list, documents, uuids, vector_ids):
        await chunked_data_Repository.update_chunked_data(
            chunked_data=data,
            faiss_info_id=data.id, # TODO 수정 필요
            vector_index=data.id, # TODO 수정 필요
            document_metadata=document.metadata,
            modified_by="vector_workflow"
        )
    
    # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
    await orgrsrc_repository.update_org_resrc(org_resrc=org_resrc, is_vector=True)
    

async def process_vectorize_faiss(index_name: str, session: AsyncSession, org_resrc, faiss_info=None):
    """
    데이터를 벡터화하여 처리합니다.
    
    Args:
        data: 벡터화할 데이터 객체
        faiss_info: FAISS 정보 객체 
        session: DB 세션
        
    Returns:
        벡터화된 인덱스 번호
    """
    
    # index_name 필수값 체크
    if not index_name:
        raise ValueError("index_name은 필수 파라미터입니다.")
    
    # org_resrc 필수값 체크
    if org_resrc is None:
        raise ValueError("org_resrc는 필수 파라미터입니다.")
    
    # session이 없을 경우 생성
    if session is None:
        from app.db_model.database import SessionLocal
        session = get_async_session()

    # faiss_vector_db = await get_vector_db(collection_name=index_name, session=session)
    vector_store = get_vector_store(index_name)
    orgrsrc_repository = OrgRSrcRepository(session=session)
    chunked_data_Repository = ChunkedDataRepository(session=session)
    
    # 기존에 저장된 벡터DB 불러오기
    # faiss_vector_db.read_index()
    
    # 조회후 다시 체크
    if faiss_info is None:
        raise ValueError(f"# 기저장된 {index_name}의 FAISS 정보가 없습니다.")

    # org_resrc.id로 ChunkedData 를 조회
    chunked_data_list = chunked_data_Repository.get_chunked_data_by_org_resrc_id(org_resrc_id=org_resrc.id)

    # documents 리스트 생성
    documents = [
        Document(
            page_content=data.content,
            metadata=data.document_metadata if isinstance(data.document_metadata, dict) else {}
        )
        for data in chunked_data_list
    ]

    # UUID 리스트 생성 (각 문서에 대한 고유 ID 할당)
    uuids = [str(uuid4()) for _ in range(len(documents))]

    # 각각의 ChunkedData에 대해 처리
    for data in chunked_data_list:
        # metadata dict 인지 확인
        metadata = data.document_metadata if isinstance(data.document_metadata, dict) else {}
        try:
            # faiss_index = faiss_vector_db.add_embedded_content_to_index(data.id, data.content, metadata)
            chunked_data_Repository.update_chunked_data(chunked_data=data, 
                                                    faiss_info_id=index_name, 
                                                    vector_index=index_name, 
                                                    document_metadata=metadata,
                                                    modified_by='vector_workflow')
        except Exception as e:
            print(f"# 벡터인덱스 생성 + 저장시 오류 발생: {e}")
            session.rollback()
    
    # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
    orgrsrc_repository.update_org_resrc(org_resrc=org_resrc, is_vector=True)

    # vector_store에 저장
    vector_store.add_documents(documents=documents, ids=uuids)

    # 세션 커밋
    session.commit()
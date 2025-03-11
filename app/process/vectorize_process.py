
from app.db_model.data_repository import ChunkedDataRepository, OrgRSrcRepository
from app.db_model.database import get_async_session
from app.vectordb.milvus_vectordb import MilvusVectorDB
from app.vectordb.faiss_vectordb import get_vector_db
from sqlalchemy.ext.asyncio import AsyncSession


async def process_vectorize(collection_name: str, session: AsyncSession, org_resrc, faiss_info=None):
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
    
    # session이 없을 경우 생성
    if session is None:
        from app.db_model.database import SessionLocal
        session = get_async_session()
        
    milvus_vectordb = MilvusVectorDB()

    orgrsrc_repository = OrgRSrcRepository(session=session)
    chunked_data_Repository = ChunkedDataRepository(session=session)
    
    # org_resrc.id로 ChunkedData 를 조회
    chunked_data_list = chunked_data_Repository.get_chunked_data_by_org_resrc_id(org_resrc_id=org_resrc.id)

    # 각각의 ChunkedData에 대해 처리
    for data in chunked_data_list:
        # metadata dict 인지 확인
        metadata = data.document_metadata if isinstance(data.document_metadata, dict) else {}
        try:
            # Milvus에 벡터 데이터 삽입
            milvus_id = milvus_vectordb.insert_vectors(
                collection_name="document_vectors",
                vectors=[data.content],  # 벡터 데이터
                ids=[data.id],          # primary key
                metadata=[metadata]      # 메타데이터 
            )
            
            # chunked data 업데이트
            chunked_data_Repository.update_chunked_data(
                chunked_data=data,
                milvus_collection="document_vectors", 
                vector_id=milvus_id,
                document_metadata=metadata,
                modified_by='vector_workflow'
            )
        except Exception as e:
            print(f"# Milvus 벡터 저장 중 오류 발생: {e}")
            session.rollback()
    
    # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
    orgrsrc_repository.update_org_resrc(org_resrc=org_resrc, is_vector=True)
    
    # 세션 커밋
    session.commit()


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

    faiss_vector_db = await get_vector_db(collection_name=index_name, session=session)
    orgrsrc_repository = OrgRSrcRepository(session=session)
    chunked_data_Repository = ChunkedDataRepository(session=session)
    
    # 기존에 저장된 벡터DB 불러오기
    # faiss_vector_db.read_index()
    

    # FAISS_INFO 파라미터가 없으면 조회
    if faiss_info is None:
        faiss_info = faiss_vector_db.psql_docstore.get_faiss_info()

    # 조회후 다시 체크
    if faiss_info is None:
        raise ValueError(f"# 기저장된 {index_name}의 FAISS 정보가 없습니다.")

    # org_resrc.id로 ChunkedData 를 조회
    chunked_data_list = chunked_data_Repository.get_chunked_data_by_org_resrc_id(org_resrc_id=org_resrc.id)

    # 각각의 ChunkedData에 대해 처리
    for data in chunked_data_list:
        # metadata dict 인지 확인
        metadata = data.document_metadata if isinstance(data.document_metadata, dict) else {}
        try:
            # 벡터 인덱스 생성 및 업데이트
            faiss_index = faiss_vector_db.add_embedded_content_to_index(data.id, data.content, metadata)
            chunked_data_Repository.update_chunked_data(chunked_data=data, 
                                                    faiss_info_id=faiss_info.id, 
                                                    vector_index=faiss_index, 
                                                    document_metadata=metadata,
                                                    modified_by='vector_workflow')
        except Exception as e:
            print(f"# 벡터인덱스 생성 + 저장시 오류 발생: {e}")
            session.rollback()
    
    # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
    orgrsrc_repository.update_org_resrc(org_resrc=org_resrc, is_vector=True)

    # FAISS_INFO에 저장 및 .index 파일 생성
    faiss_vector_db.write_index()
    
    # 세션 커밋
    session.commit()
import asyncio
import os
from typing import Dict, Optional, Union
import faiss
# import json      # 메타데이터를 JSON으로 처리하기 위한 라이브러리
from fastapi import Depends
from langchain_community.vectorstores import FAISS
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from langchain_core.documents import Document

from app.db_model.data_repository import ChunkedDataRepository
from app.db_model.database import get_async_session
from app.db_model.database_models import FaissInfo, ChunkedData
from app.utils import get_embedding_model
from sqlalchemy.ext.asyncio import AsyncSession

class PostgresDocstore:
    def __init__(self, index_name: str, session):
        """SQLAlchemy 세션을 주입받음"""
        self.session = session
        self.index_name = index_name
        self.index_file_path = f'data/vector/{self.index_name}.index' # ex) cg_text_to_sql, cg_code_assist
        
    async def get_faiss_info(self) -> FaissInfo:
        """인덱스 이름으로 FAISS 정보를 조회합니다."""
        stmt = select(FaissInfo).where(FaissInfo.index_name == self.index_name)
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if result:
            return result
        return None
        
    def insert_faiss_info(self, index_desc: str = '') -> FaissInfo:
        """FAISS 인덱스 정보 저장"""
        faiss_info = FaissInfo(
            index_name=self.index_name,
            index_desc=index_desc,
            index_file_path=self.index_file_path,
        )
        self.session.add(faiss_info)
        self.session.commit()
        
        return faiss_info
        

    def insert_document(self, document_id, index, content, metadata=None) -> None:
        """OrgRSrcData 테이블에 문서 추가"""

        new_document = ChunkedData(
            org_resrc_id=document_id,
            content=content, 
            vector_index=index,
            document_metadata=metadata
        )
        self.session.add(new_document)
        self.session.commit()
                

    async def get_document(self, document_id) -> Optional[Dict[str, any]]:
        """OrgRSrcData 테이블에서 문서 조회"""
        stmt = select(ChunkedData).where(ChunkedData.id == document_id)
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if result:
            return result
        return None
        # if result:
        #     return {"content": result.content, "metadata": result.document_metadata}
        # return None
    
    async def get_chunked_data_by_faiss_info_id(self, faiss_info_id: int) -> list[ChunkedData]:
        """vector_index 조회"""
        stmt = select(ChunkedData).where(ChunkedData.faiss_info_id == faiss_info_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_document_by_index(self, vector_index) -> Optional[Dict[str, any]]:
        """vector_index 조회"""
        # Numpy int64 값을 Python의 int로 변환
        vector_index = int(vector_index) 

        stmt = (
            select(ChunkedData)
            .join(FaissInfo, ChunkedData.faiss_info_id == FaissInfo.id)
            .where((ChunkedData.vector_index == vector_index) & (FaissInfo.index_name == self.index_name))
        )
        chunked_data = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if chunked_data:
            result = chunked_data.__dict__
            result['vector_index'] = vector_index
            return result
        return None

    def delete_document(self, document_id) -> None:
        """OrgRSrcData 테이블에서 문서 삭제"""
        stmt = delete(ChunkedData).where(ChunkedData.id == document_id)
        self.session.execute(stmt)
        self.session.commit()

    def search(self, search: str) -> Union[str, Document]:
        '''
        langchain_community.docstore.base의 추상함수
        -> 클래스가 faiss의 docstore에 parameter로 사용될 경우 반드시 구현해야 함
        '''
        doc = self.get_document(document_id=search)
        document = Document(
            page_content=doc.get("content"),
            metadata=doc.get("metadata"),
        )
        
        return document


class FaissVectorDB:
    _loaded_indices = {}

    def __init__(self, index_name: str, session: AsyncSession):
        # 기본 속성 초기화 (비동기 작업이 필요없는 것들)
        self.index_name = index_name
        self.index_file_path = f'data/vector/{self.index_name}.index'
        self.session = session
        self.embeddings = get_embedding_model()
        self.embedding_dimension = self.embeddings.embed_query("임베딩 벡터 차원")
        self.psql_docstore = PostgresDocstore(index_name=self.index_name, session=self.session)
        self.vector_store = None
        self.index = None

    @classmethod
    async def create(cls, index_name: str, session: AsyncSession) -> 'FaissVectorDB':
        # __init__ 호출
        instance = cls(index_name, session)
        
        # 이미 로드된 인덱스가 있다면 메모리에서 가져옴
        if index_name in cls._loaded_indices:
            instance.vector_store = cls._loaded_indices[index_name]
            print(f"### {instance.index_name} 인덱스를 메모리에서 로드했습니다.")
            return instance

        # 새로운 FAISS 인덱스 생성
        instance.index = faiss.IndexFlatL2(len(instance.embedding_dimension))
        instance.vector_store = FAISS(
            embedding_function=instance.embeddings,
            index=instance.index,
            docstore=instance.psql_docstore,
            index_to_docstore_id={},
        )

        # 없으면 인덱스 생성
        if not os.path.exists(instance.index_file_path):
            faiss.write_index(instance.vector_store.index, instance.index_file_path)
            print(f"### {instance.index_name} 인덱스를 신규로 생성합니다.")

        # 인덱스 파일에서 로드 (비동기 작업)
        await instance.read_index()

        # 캐시에 저장
        cls._loaded_indices[index_name] = instance.vector_store
        print(f"### {instance.index_name} 인덱스를 디스크에서 로드하고 캐시에 저장했습니다.")

        return instance

    def as_retriever(self, search_kwargs):
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)


    def add_embedded_content_to_index(self, document_id, content, metadata) -> ChunkedData:
        """
        문서 내용을 임베딩하고 FAISS 인덱스에 추가합니다.

        Args:
            document_id (str): 문서의 고유 식별자
            content (str): 문서의 내용
            metadata (dict): 문서와 관련된 메타데이터

        Returns:
            int: FAISS 인덱스에 추가된 벡터의 인덱스

        동작 과정:
        1. 주어진 내용과 메타데이터로 Document 객체를 생성합니다.
        2. 문서 내용을 임베딩 벡터로 변환합니다.
        3. 임베딩 벡터를 FAISS 인덱스에 추가합니다.
        4. 추가된 벡터의 인덱스를 계산합니다.
        5. FAISS 인덱스와 문서 ID 간의 매핑을 설정합니다.
        6. 추가된 벡터의 인덱스를 반환합니다.
        """
        # Document 객체 생성
        document = Document(page_content=content, metadata=metadata)
        
        # 임베딩 벡터 생성
        embedding_content = self.embeddings.embed_query(document.page_content)
        
        # 벡터를 배열로 변환 및 float32 타입으로 변환
        embedding_content = np.array([embedding_content], dtype=np.float32)
        
        # FAISS 인덱스에 벡터 추가
        self.vector_store.index.add(embedding_content)
        
        # FAISS 인덱스에 벡터가 추가된 후 매핑 정보 업데이트
        # 주의: 인덱스의 벡터 개수는 추가된 후에 반영되므로, ntotal을 사용해서 현재 벡터 인덱스를 가져옴
        faiss_index = self.vector_store.index.ntotal - 1  # 현재 추가된 벡터의 인덱스
        
        # FAISS 인덱스와 문서 ID 간의 매핑 설정
        self.vector_store.index_to_docstore_id[faiss_index] = document_id
        print(f"Document ID {document_id} mapped to FAISS vector index {faiss_index}")
        
        return faiss_index

    def get_all_documents(self):
        """
        벡터 스토어에 저장된 모든 문서들의 목록을 반환합니다.

        Returns:
            list: 저장된 모든 문서 목록. 각 문서는 딕셔너리 형태로 반환됩니다.
        """
        try:
            # 전체 벡터 개수 확인
            total_vectors = self.vector_store.index.ntotal
            # print(f"### 전체 벡터 개수: {total_vectors}")
            # print(f"### self.vector_store.index_to_docstore_id: {self.vector_store.index_to_docstore_id}")
            
            # 모든 문서 정보를 저장할 리스트
            all_documents = []
            
            # 각 인덱스에 대해 문서 정보 조회
            for idx in range(total_vectors):
                # docstore_id 가져오기 
                docstore_id = self.vector_store.index_to_docstore_id.get(idx)
                
                if docstore_id:
                    # PostgreSQL에서 문서 정보 조회
                    document = self.psql_docstore.get_document_by_index(idx)
                    if document:
                        all_documents.append(document)
            
            return all_documents
            
        except Exception as e:
            print(f"### 문서 목록 조회 중 오류 발생: {str(e)}")
            return []


    async def search_similar_documents(self, query, k=10):
        # 쿼리를 임베딩으로 변환
        query_embedding = self.embeddings.embed_query(query)
        
        # 임베딩 벡터를 numpy 배열로 변환
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # 벡터를 2차원 배열로 변환 (1x3072)
        query_embedding = query_embedding.reshape(1, -1)
        # print(f"### query_embedding.shape = {query_embedding.shape}")

        # FAISS에서 유사한 벡터 검색 (k는 찾을 유사 벡터의 수)
        distances, indices = self.vector_store.index.search(query_embedding, k)

        # # 검색된 인덱스와 거리 출력
        # print(f"### Distances: {distances}, Indices: {indices}")
        # # 매핑된 문서 ID 정보 출력
        # print(f"### index_to_docstore_id mapping: {self.vector_store.index_to_docstore_id}")
        
        # PostgreSQL에서 문서 가져오기
        results = await asyncio.gather(
            *[
                self.psql_docstore.get_document_by_index(idx)
                for idx in indices[0]
                if idx != -1
            ]
        )
        
        return results
    
    
    def write_index(self):
        # FAISS 인덱스를 디스크에 저장
        faiss.write_index(self.vector_store.index, self.index_file_path)
        

    async def read_index(self):
        # PostgresDocstore에서 FAISS 정보 가져오기
        faiss_info = await self.psql_docstore.get_faiss_info()

        if faiss_info is not None:
            # FAISS 인덱스 파일 로드
            self.vector_store.index = faiss.read_index(faiss_info.index_file_path)

            # 데이터베이스에서 index_to_docstore_id 매핑 정보 로드
            mappings = await self.psql_docstore.get_chunked_data_by_faiss_info_id(faiss_info.id)
            self.vector_store.index_to_docstore_id = {mapping.vector_index: mapping.id for mapping in mappings}

            print(f"### {self.index_name} 인덱스와 매핑 정보를 디스크에서 로드했습니다.")
            # 인덱스의 기본 정보 출력
            # print(f"### PostgresDocstore에서 FAISS 정보 읽기 >> index_name={self.index_name}, index_file_path={faiss_info.index_file_path}")
            # print(f"### Total vectors in index: {self.vector_store.index.ntotal}")  # 저장된 벡터 개수 출력
            # print(f"### Dimension of vectors: {self.vector_store.index.d}")  # 벡터의 차원 출력
        else:
            # raise ValueError(f"{self.index_name}에 대한 FAISS 정보가 존재하지 않습니다.")
            print(f"### {self.index_name}에 대한 FAISS 정보가 존재하지 않습니다.")


        # 체크하기! = 첫 번째 벡터(예시) 조회 (자기자신과 비교 할시, 거리가 0이 나와야 정상임)
        # if self.vector_store.index.ntotal > 0:
        #     # 첫 번째 벡터와 유사한 벡터를 검색 (자신과의 유사도 검색)
        #     D, I = self.vector_store.index.search(self.vector_store.index.reconstruct(0).reshape(1, -1), 1)
        #     print(f"### First vector in index: {self.vector_store.index.reconstruct(0)}")
        #     print(f"### Distance: {D}, Index: {I}")
        # else:
        #     print("### Index is empty.")
        

    def restore_index_to_docstore_id(self):
        # 모든 ChunkedData 레코드를 조회하여 인덱스와 docstore_id를 매핑
        with get_async_session() as session:
            results = session.query(ChunkedData.vector_index, ChunkedData.org_resrc_id).all()
        
        # index_to_docstore_id 매핑 재구성
        self.vector_store.index_to_docstore_id = {vector_index: org_resrc_id for vector_index, org_resrc_id in results}
        print("### index_to_docstore_id 매핑이 복구되었습니다.")

    # 예제) 유사한 문서 검색
    # similar_docs = search_similar_documents(vector_store, query="test document")
    # for doc in similar_docs:
    #     print(f"Similar Document Content: {doc['content']}, Metadata: {doc['metadata']}")

    # 예제) 문서 추가
    # add_document_to_store(vector_store, document_id=1, content="This is a test document.", metadata={"source": "test"})

    @classmethod
    def clear_cache(cls):
        """클래스 캐시를 초기화합니다 (테스트나 필요시 호출)."""
        cls._loaded_indices.clear()
        print("### FAISS 인덱스 캐시가 초기화되었습니다.")

# 전역 변수로 vector_db 저장소 생성
_vector_dbs: Dict[str, FaissVectorDB] = {}

async def initialize_vector_dbs(session: AsyncSession):
    """초기에 필요한 모든 FaissVectorDB 인스턴스들을 생성"""
    global _vector_dbs
    
    # 필요한 모든 인덱스 이름들
    index_names = ["cg_code_assist"]  # 필요한 인덱스 이름들 나열
    
    for index_name in index_names:
        if index_name not in _vector_dbs:
            vector_db = await FaissVectorDB.create(index_name=index_name, session=session)
            _vector_dbs[index_name] = vector_db

async def get_vector_db(
    index_name: str,
    session: AsyncSession = Depends(get_async_session)
) -> FaissVectorDB:
    """벡터 DB 인스턴스를 가져오는 의존성 함수"""
    if index_name not in _vector_dbs:
        vector_db = await FaissVectorDB.create(index_name=index_name, session=session)
        _vector_dbs[index_name] = vector_db
    return _vector_dbs[index_name]

def vectordb_clear():
    _vector_dbs.clear()

# 캐시를 초기화하여 새로 로드 가능
# FaissVectorDB.clear_cache()  

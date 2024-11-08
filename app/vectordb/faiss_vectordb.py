import os
from typing import Dict, Optional
import faiss
# import json      # 메타데이터를 JSON으로 처리하기 위한 라이브러리
from langchain_community.vectorstores import FAISS
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from langchain_core.documents import Document

from app.db_model.database import SessionLocal
from app.db_model.database_models import FaissInfo, ChunkedData
from app.utils import get_embedding_model


class PostgresDocstore:
    def __init__(self, db_session: Session, index_name: str):
        """SQLAlchemy 세션을 주입받음"""
        self.session = db_session
        self.index_name = index_name
        self.index_file_path = f'data/vector/{self.index_name}.index' # ex) cg_text_to_sql, cg_code_assist
        
    def get_faiss_info(self) -> FaissInfo:
        """인덱스 이름으로 FAISS 정보를 조회합니다."""
        stmt = select(FaissInfo).where(FaissInfo.index_name == self.index_name)
        result = self.session.execute(stmt).scalar_one_or_none()
        
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
                

    def get_document(self, document_id) -> Optional[Dict[str, any]]:
        """OrgRSrcData 테이블에서 문서 조회"""
        stmt = select(ChunkedData).where(ChunkedData.id == document_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result:
            return {"content": result.content, "metadata": result.document_metadata}
        return None
    
    def get_chunked_data_by_faiss_info_id(self, faiss_info_id: int) -> list[ChunkedData]:
        """vector_index 조회"""

        return self.session.query(ChunkedData).filter(ChunkedData.faiss_info_id == faiss_info_id).all()

    def get_document_by_index(self, vector_index) -> Optional[Dict[str, any]]:
        """vector_index 조회"""
        # Numpy int64 값을 Python의 int로 변환
        vector_index = int(vector_index) 
        
        # stmt = select(ChunkedData).where((ChunkedData.vector_index == vector_index) & (ChunkedData.faiss_info_id == faiss_info_id))
        # result = self.session.execute(stmt).scalar_one_or_none()
        stmt = (
            select(ChunkedData)
            .join(FaissInfo, ChunkedData.faiss_info_id == FaissInfo.id)
            .where((ChunkedData.vector_index == vector_index) & (FaissInfo.index_name == self.index_name))
        )
        result = self.session.execute(stmt).scalar_one_or_none()
        
        if result:
            return {"content": result.content, "metadata": result.document_metadata}
        return None

    def delete_document(self, document_id) -> None:
        """OrgRSrcData 테이블에서 문서 삭제"""
        stmt = delete(ChunkedData).where(ChunkedData.id == document_id)
        self.session.execute(stmt)
        self.session.commit()
        



class FaissVectorDB:
    def __init__(self, db_session: Session, index_name: str):
        self.session = db_session
        self.index_name = index_name
        self.index_file_path = f'data/vector/{self.index_name}.index' # ex) cg_text_to_sql, cg_code_assist

        # 임베딩 모델 가져오기
        self.embeddings = get_embedding_model()
        self.embedding_dimension = self.embeddings.embed_query("임베딩 벡터 차원")

        # index 셋팅
        # •	IndexFlatL2: 정확한 유클리드 거리 계산을 수행하지만, 대규모 데이터에서 속도 저하 가능.
        # •	IndexFlatIP: 내적 기반 유사도 계산, 코사인 유사도와 유사한 결과 제공.
        # •	IndexLSH: 근사 검색을 위한 해싱 기반 방법으로 대규모 데이터에 적합.
        # •	IndexIVFFlat/IndexIVFPQ: 클러스터링을 통해 검색 속도 향상, 대규모 데이터에 적합.
        # •	IndexHNSW: 그래프 탐색 기반의 근사 검색, 높은 정확도와 빠른 속도 제공.
        # •	IndexPQ: 벡터를 양자화하여 메모리 절약을 추구, 대규모 데이터에 유리.
        self.index = faiss.IndexFlatL2(len(self.embedding_dimension))
        
        self.psql_docstore = PostgresDocstore(db_session, index_name=self.index_name)

        # FAISS vector store 선언
        self.vector_store = FAISS(
            embedding_function=self.embeddings,
            index=self.index,
            docstore=self.psql_docstore,
            index_to_docstore_id={},
        )
        pass
    
    
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
            print(f"### 전체 벡터 개수: {total_vectors}")
            print(f"### self.vector_store.index_to_docstore_id: {self.vector_store.index_to_docstore_id}")
            
            # 모든 문서 정보를 저장할 리스트
            all_documents = []
            
            # 각 인덱스에 대해 문서 정보 조회
            for idx in range(total_vectors):
                # docstore_id 가져오기 
                docstore_id = self.vector_store.index_to_docstore_id.get(idx)
                print(f"##### docstore_id = {idx}, {docstore_id}")
                
                if docstore_id:
                    # PostgreSQL에서 문서 정보 조회
                    document = self.psql_docstore.get_document_by_index(idx)
                    if document:
                        all_documents.append(document)
            
            return all_documents
            
        except Exception as e:
            print(f"### 문서 목록 조회 중 오류 발생: {str(e)}")
            return []


    def search_similar_documents(self, query, k=10):
        # 쿼리를 임베딩으로 변환
        query_embedding = self.embeddings.embed_query(query)
        
        # 임베딩 벡터를 numpy 배열로 변환
        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # 벡터를 2차원 배열로 변환 (1x3072)
        query_embedding = query_embedding.reshape(1, -1)
        print(f"### query_embedding.shape = {query_embedding.shape}")

        # FAISS에서 유사한 벡터 검색 (k는 찾을 유사 벡터의 수)
        distances, indices = self.vector_store.index.search(query_embedding, k)

        # # 검색된 인덱스와 거리 출력
        # print(f"### Distances: {distances}, Indices: {indices}")
        # # 매핑된 문서 ID 정보 출력
        # print(f"### index_to_docstore_id mapping: {self.vector_store.index_to_docstore_id}")
        
        # PostgreSQL에서 문서 가져오기
        results = [
            self.psql_docstore.get_document_by_index(idx)
            for idx in indices[0] # 현재는 1개의 쿼리만을 사용하기 때문에 하드코딩, 다중 쿼리를 사용할 경우 수정되어야 함
            if idx != -1  # 유효하지 않은 인덱스 (-1) 무시
        ]
        
        return results
    
    
    def write_index(self):
        # FAISS 인덱스를 디스크에 저장
        faiss.write_index(self.vector_store.index, self.index_file_path)
        
        
    def read_index(self):
        # PostgresDocstore에서 FAISS 정보 가져오기
        faiss_info = self.psql_docstore.get_faiss_info()

        if faiss_info == None:
            raise ValueError(f"{self.index_name}에 대한 FAISS 정보가 존재하지 않습니다.")

        # 1. FAISS 인덱스 파일 로드
        self.vector_store.index = faiss.read_index(faiss_info.index_file_path)

        # 2. 데이터베이스에서 index_to_docstore_id 매핑 정보 로드
        mappings = self.psql_docstore.get_chunked_data_by_faiss_info_id(faiss_info.id)
        self.vector_store.index_to_docstore_id = {mapping.vector_index: mapping.id for mapping in mappings}

        print("### FAISS 인덱스와 매핑 정보가 성공적으로 로드되었습니다.")

        # 인덱스의 기본 정보 출력
        print(f"### PostgresDocstore에서 FAISS 정보 읽기 >> index_name={self.index_name}, index_file_path={faiss_info.index_file_path}")
        print(f"### Total vectors in index: {self.vector_store.index.ntotal}")  # 저장된 벡터 개수 출력
        print(f"### Dimension of vectors: {self.vector_store.index.d}")  # 벡터의 차원 출력

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
        results = self.session.query(ChunkedData.vector_index, ChunkedData.org_resrc_id).all()
        # index_to_docstore_id 매핑 재구성
        self.vector_store.index_to_docstore_id = {vector_index: org_resrc_id for vector_index, org_resrc_id in results}
        print("### index_to_docstore_id 매핑이 복구되었습니다.")

    # def restore_index_to_docstore_id(self):
    #     # 모든 ChunkedData 레코드 조회
    #     results = self.session.query(ChunkedData.vector_index, ChunkedData.org_resrc_id).all()
        
    #     # 매핑 정보 재구성
    #     self.vector_store.index_to_docstore_id = {vector_index: org_resrc_id for vector_index, org_resrc_id in results}

    # 예제) 유사한 문서 검색
    # similar_docs = search_similar_documents(vector_store, query="test document")
    # for doc in similar_docs:
    #     print(f"Similar Document Content: {doc['content']}, Metadata: {doc['metadata']}")

    # 예제) 문서 추가
    # add_document_to_store(vector_store, document_id=1, content="This is a test document.", metadata={"source": "test"})

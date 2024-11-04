
# https://python.langchain.com/v0.2/docs/integrations/vectorstores/faiss/#manage-vector-store
# 이 내용에 대한 실습
import numpy as np

import sys
import os
import uuid  # 청크 ID를 생성하기 위해 사용
from uuid import uuid4
from langchain_core.documents import Document
from app.db_model.database import SessionLocal
from app.vectordb.faiss_vectordb import FaissVectorDB

session = SessionLocal()
faissVectorDB = FaissVectorDB(session, index_name="cg_code_assist")


def test_read_index():
    ''' 
    faissVectorDB.read_index(file_path='data/vector/faiss_test.index')
    search_result = faissVectorDB.search_similar_documents(query="I had chocolate chip pancakes", k=10)
    print(f"### search_result = {search_result}")

    # 저장된 첫 번째 벡터와 쿼리 벡터의 거리 계산
    stored_vector = faissVectorDB.index.reconstruct(0)
    query_vector = np.array(faissVectorDB.embeddings.embed_query("I I had chocalate chip"), dtype=np.float32).reshape(1, -1)

    # 거리 계산 (예: L2 거리)
    distance = np.linalg.norm(stored_vector - query_vector)
    print(f"### Distance between stored vector and query vector: {distance}")
    '''
    
    faissVectorDB.read_index()
    search_result = faissVectorDB.search_similar_documents(query="whether", k=10)
    print(f"### search_result = {search_result}")

if __name__ == '__main__':
    
    test_read_index()

    

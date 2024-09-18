
# https://python.langchain.com/v0.2/docs/integrations/vectorstores/faiss/#manage-vector-store
# 이 내용에 대한 실습
import numpy as np

import sys
import os
import uuid  # 청크 ID를 생성하기 위해 사용
from uuid import uuid4
from langchain_core.documents import Document
from app.vectordb.faiss_vectordb import FaissVectorDB

faissVectorDB = FaissVectorDB()


def test_insert_write():

    document_1 = Document(
        page_content="I had chocalate chip pancakes and scrambled eggs for breakfast this morning.",
        metadata={"source": "tweet"},
    )

    document_2 = Document(
        page_content="The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.",
        metadata={"source": "news"},
    )

    document_3 = Document(
        page_content="Building an exciting new project with LangChain - come check it out!",
        metadata={"source": "tweet"},
    )

    document_4 = Document(
        page_content="Robbers broke into the city bank and stole $1 million in cash.",
        metadata={"source": "news"},
    )

    document_5 = Document(
        page_content="Wow! That was an amazing movie. I can't wait to see it again.",
        metadata={"source": "tweet"},
    )

    faissVectorDB.add_document_to_store(1, content="I had chocalate chip pancakes and scrambled eggs for breakfast this morning.", metadata={"source": "tweet"})
    faissVectorDB.write_index(file_path='data/vector/faiss_test.index')
    
    # documents = [
    #     document_1,
    #     document_2,
    #     document_3,
    #     document_4,
    #     document_5,
    # ]
    # uuids = [str(uuid4()) for _ in range(len(documents))]
    # vector_store.add_documents(documents=documents, ids=uuids)

def test_read_index():
    faissVectorDB.read_index(file_path='data/vector/faiss_test.index')
    search_result = faissVectorDB.search_similar_documents(query="I had chocolate chip pancakes", k=10)
    print(f"### search_result = {search_result}")

    # 저장된 첫 번째 벡터와 쿼리 벡터의 거리 계산
    stored_vector = faissVectorDB.index.reconstruct(0)
    query_vector = np.array(faissVectorDB.embeddings.embed_query("I I had chocalate chip"), dtype=np.float32).reshape(1, -1)

    # 거리 계산 (예: L2 거리)
    distance = np.linalg.norm(stored_vector - query_vector)
    print(f"### Distance between stored vector and query vector: {distance}")

if __name__ == '__main__':
    ''' 사용법
        # python upload_vectordb.py ../data/norway.txt db_desc
    '''
    print("====================")
    # test_insert_write()
    # test_read_index()
    
    
        
    # 예시 사용
    file_path = 'data/vector/faiss_test1.index'
    filename = os.path.basename(file_path)
    filename = os.path.splitext(filename)[0]
    
    print(f"Extracted filename: {filename}")
    

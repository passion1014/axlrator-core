import os
from elasticsearch import Elasticsearch
from app.vectordb.bm25_search import ElasticsearchBM25, retrieve_advanced
from app.vectordb.faiss_vectordb import FaissVectorDB

# 테스트 데이터 준비
test_documents = [
    {
        "original_content": "The quick brown fox jumps over the lazy dog.",
        "contextualized_content": "Foxes are swift animals that can jump high.",
        "doc_id": "doc1",
        "chunk_id": "chunk1",
        "original_index": 0
    },
    {
        "original_content": "The rain in Spain stays mainly in the plain.",
        "contextualized_content": "Spain experiences diverse weather patterns.",
        "doc_id": "doc2",
        "chunk_id": "chunk2",
        "original_index": 1
    },
    {
        "original_content": "A journey of a thousand miles begins with a single step.",
        "contextualized_content": "Great accomplishments often have humble beginnings.",
        "doc_id": "doc3",
        "chunk_id": "chunk3",
        "original_index": 2
    },
]

# 테스트 쿼리
test_query = "What does the fox do?"

# FAISS DB 초기화
class MockFaissVectorDB(FaissVectorDB):
    def __init__(self, documents):
        self.metadata = documents

    def search_similar_documents(self, query: str, k: int = 10):
        # Mock 시맨틱 검색 결과 반환
        return [
            {
                "content": doc["contextualized_content"],
                "metadata": {"doc_id": doc["doc_id"], "original_index": doc["original_index"]}
            }
            for doc in self.metadata[:k]
        ]

# 테스트 실행
def test_elasticsearch_bm25_and_faiss():
    from app.db_model.database import SessionLocal
    session = SessionLocal()

    # FAISS DB 및 Elasticsearch 초기화
    # db = MockFaissVectorDB(test_documents)
    
    db = FaissVectorDB(db_session=session, index_name="cg_terms") 
    es_bm25 = ElasticsearchBM25()

    # Elasticsearch 문서 인덱싱
    print("Indexing documents into Elasticsearch...")
    es_bm25.index_documents(test_documents)

    # 고급 검색 실행
    print("Running advanced search...")
    final_results, semantic_count, bm25_count = retrieve_advanced(
        query=test_query,
        db=db,
        es_bm25=es_bm25,
        k=3  # 상위 3개 결과
    )

    # 결과 출력
    print("\nFinal Results:")
    for result in final_results:
        print(f"Doc ID: {result['chunk']['doc_id']}, Score: {result['score']:.2f}")
        print(f"Content: {result['chunk']['original_content']}")
        print(f"From Semantic: {result['from_semantic']}, From BM25: {result['from_bm25']}")
        print("-" * 40)

    print(f"Semantic Results Count: {semantic_count}")
    print(f"BM25 Results Count: {bm25_count}")

# 테스트 실행
if __name__ == "__main__":
    test_elasticsearch_bm25_and_faiss()

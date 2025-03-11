# milvus_vector_db
from pymilvus import connections, Collection, DataType, FieldSchema, CollectionSchema, utility
import numpy as np
from typing import List, Dict, Any, Optional

class MilvusVectorDB:
    def __init__(self, host: Optional[str] = None, port: Optional[str] = None):
        """Milvus 벡터 DB 초기화

        Args:
            host: Milvus 서버 호스트 (optional, defaults to .env MILVUS_HOST or "localhost")
            port: Milvus 서버 포트 (optional, defaults to .env MILVUS_PORT or "19530")
        """
        from dotenv import load_dotenv
        import os

        # Load environment variables from .env file
        load_dotenv()

        # Use provided values or fall back to env vars or defaults
        self.host = host or os.getenv('MILVUS_HOST', 'localhost')
        self.port = port or os.getenv('MILVUS_PORT', '19530')
        self.connect()
        
    def connect(self):
        """Milvus 서버에 연결"""
        try:
            connections.connect(host=self.host, port=self.port)
            print("Successfully connected to Milvus")
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")
            raise

    def create_collection(self, collection_name: str, dim: int = 1536):
        """벡터 컬렉션 생성
        
        Args:
            collection_name: 컬렉션 이름
            dim: 벡터 차원 (기본값 1536 - OpenAI embedding 차원)
        """
        if utility.has_collection(collection_name):
            print(f"Collection {collection_name} already exists")
            return

        # 필드 정의
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        
        # 스키마 생성
        schema = CollectionSchema(fields=fields)
        
        # 컬렉션 생성
        collection = Collection(name=collection_name, schema=schema)
        
        # 인덱스 생성 (IVF_FLAT)
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="vector", index_params=index_params)
        print(f"Created collection {collection_name} with index")

    def insert_vectors(self, 
                      collection_name: str, 
                      vectors: List[List[float]], 
                      ids: List[int],
                      metadata: List[Dict] = None) -> List[int]:
        """벡터 데이터 삽입
        
        Args:
            collection_name: 컬렉션 이름
            vectors: 벡터 데이터 리스트
            ids: 벡터 ID 리스트
            metadata: 메타데이터 리스트
        
        Returns:
            삽입된 벡터의 ID 리스트
        """
        if not utility.has_collection(collection_name):
            raise ValueError(f"Collection {collection_name} does not exist")
            
        collection = Collection(collection_name)
        
        if metadata is None:
            metadata = [{} for _ in vectors]
            
        entities = [
            ids,  # id 필드
            vectors,  # vector 필드
            metadata  # metadata 필드
        ]
        
        collection.insert(entities)
        collection.flush()
        return ids

    def search_vectors(self, 
                      collection_name: str, 
                      query_vectors: List[List[float]], 
                      top_k: int = 5) -> List[Dict]:
        """벡터 검색
        
        Args:
            collection_name: 컬렉션 이름
            query_vectors: 검색할 쿼리 벡터 리스트
            top_k: 반환할 최근접 이웃 개수
            
        Returns:
            검색 결과 리스트 (ID, 거리, 메타데이터 포함)
        """
        collection = Collection(collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10}
        }
        
        results = collection.search(
            data=query_vectors,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["metadata"]
        )
        
        search_results = []
        for hits in results:
            hit_results = []
            for hit in hits:
                hit_results.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "metadata": hit.entity.get("metadata", {})
                })
            search_results.append(hit_results)
            
        collection.release()
        return search_results

    def delete_vectors(self, collection_name: str, ids: List[int]):
        """벡터 삭제
        
        Args:
            collection_name: 컬렉션 이름
            ids: 삭제할 벡터 ID 리스트
        """
        collection = Collection(collection_name)
        expr = f"id in {ids}"
        collection.delete(expr)

    def drop_collection(self, collection_name: str):
        """컬렉션 삭제
        
        Args:
            collection_name: 삭제할 컬렉션 이름
        """
        utility.drop_collection(collection_name)

    def disconnect(self):
        """Milvus 연결 해제"""
        connections.disconnect()

# ```
# 사용 예시:

# ```python example_usage.py
# # Milvus DB 인스턴스 생성
# milvus_db = MilvusVectorDB(host="localhost", port="19530")

# # 컬렉션 생성
# milvus_db.create_collection("document_vectors", dim=1536)

# # 벡터 삽입
# vectors = [[0.1, 0.2, ...], [0.3, 0.4, ...]]  # 1536 차원의 벡터
# ids = [1, 2]
# metadata = [{"doc_id": 1, "title": "doc1"}, {"doc_id": 2, "title": "doc2"}]
# milvus_db.insert_vectors("document_vectors", vectors, ids, metadata)

# # 벡터 검색
# query_vector = [[0.1, 0.2, ...]]  # 검색할 벡터
# results = milvus_db.search_vectors("document_vectors", query_vector, top_k=5)

# # 연결 해제
# milvus_db.disconnect()
# ```

# 이 구현에는 다음과 같은 주요 기능이 포함되어 있습니다:

# 1. Milvus 서버 연결 관리
# 2. 컬렉션 생성 및 인덱스 설정
# 3. 벡터 데이터 삽입
# 4. 벡터 검색
# 5. 벡터 삭제
# 6. 컬렉션 삭제

# 사용하기 전에 다음 패키지를 설치해야 합니다:

# ```bash
# pip install pymilvus
# ```

# 또한 Milvus 서버가 실행 중이어야 합니다. Docker를 사용하여 Milvus를 실행하는 것이 가장 간단한 방법입니다.
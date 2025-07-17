import os
from typing import List
from dotenv import load_dotenv
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, MilvusClient, connections
from axlrator_core.utils import get_embedding_model
from langchain_milvus import Milvus
from langchain.schema import Document
import numpy as np

load_dotenv()

URI = os.getenv('MILVUS_URI', 'http://localhost:19530')
INDEX_TYPE="FLAT"
METRIC_TYPE="L2"

def create_collection(collection_name:str):
    
    # Milvus 연결 확인 및 설정
    if not connections.has_connection("default"):
        connections.connect("default", uri=URI)

    client = MilvusClient(uri=URI)

    # 컬렉션 존재 여부 확인
    if not client.has_collection(collection_name):
        # 새로운 컬렉션 스키마 정의 (`id` 필드를 `VARCHAR`로 변경)
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),  # ID 필드 설정
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),  # 텍스트 필드 추가
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=3072, params={"dim": 3072}),  # 벡터 필드 설정, dim 추가 확인        
        ]

        schema = CollectionSchema(fields=fields, description=collection_name, enable_dynamic_field=True)
        
        # Milvus 컬렉션 생성 시 정확한 파라미터 전달
        collection = Collection(name=collection_name, schema=schema)
        
        # 인덱스 생성 (필수)
        collection.create_index(
            field_name="embedding",
            index_params={"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": 1024}}
        )
        
        collection.load()  # 컬렉션 로드 필수
    


def delete_collection(collection_name:str):
    client = MilvusClient(uri=URI)
    
    # 컬렉션 존재 여부 확인 후 삭제 (필요하면 활성화)
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)

class PyMilvusVectorStore:
    def __init__(self, collection_name: str, embedding_function):
        self.collection_name = collection_name
        self.embedding_function = embedding_function
        self.client = MilvusClient(uri=URI)


    def add_documents(self, docs: List[Document]):
        texts = [doc.page_content for doc in docs]
                
        raw_embeddings = self.embedding_function.embed_documents(texts)
        embeddings = [np.array(vec, dtype=np.float32).tolist() for vec in raw_embeddings]

        # data = [{"content": text, "embedding": embedding} for text, embedding in zip(texts, embeddings)]
        data = []
        for doc, embedding in zip(docs, embeddings):
            entry = {
                "content": doc.page_content,
                "embedding": embedding,
                **(doc.metadata or {})  # Include metadata as dynamic fields
            }
            data.append(entry)

        result_dict = self.client.insert(
            collection_name=self.collection_name,
            data=data
        )
        
        self.client.flush(self.collection_name)
        return result_dict

    def similarity_search(self, query: str, k: int = 3):
        query_vector = self.embedding_function.embed_query(query)
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            anns_field="embedding",
            search_params={"nprobe": 10},
            limit=k,
            # output_fields=["content"]
            output_fields=["*"]
        )
        return [
            {
                "id": hit["id"],
                "score": hit["distance"],
                # "content": hit["entity"].get("content")
                "content": hit["entity"].get("content"),
                "metadata": {k: v for k, v in hit["entity"].items() if k not in ("content", "embedding")}
            } for hit in results[0]
        ]
        
    def similarity_search_with_score(self, query: str, k: int = 3):
        query_vector = self.embedding_function.embed_query(query)
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            anns_field="embedding",
            search_params={"nprobe": 10},
            limit=k,
            # output_fields=["content"]
            output_fields=["*"]
        )
        return [
            {
                "id": hit["id"],
                "score": hit["distance"],
                # "content": hit["entity"].get("content")
                "content": hit["entity"].get("content"),
                "metadata": {k: v for k, v in hit["entity"].items() if k not in ("content", "embedding")}
            } for hit in results[0]
        ]

def get_vector_store(collection_name:str):
    # from pymilvus import MilvusClient
    client = MilvusClient(uri=URI)

    # Collection이 없을 경우 생성
    if not client.has_collection(collection_name=collection_name):
        from axlrator_core.vectordb.vector_store import create_collection
        create_collection(collection_name)
    
    embeddings = get_embedding_model()
    return PyMilvusVectorStore(collection_name, embeddings)

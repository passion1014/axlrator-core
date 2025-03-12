import os
from dotenv import load_dotenv
from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, MilvusClient, connections
from app.utils import get_embedding_model
from langchain_milvus import Milvus

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
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=50),  # 문자열 ID 필드 설정
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=3072, params={"dim": 3072})  # 벡터 필드 설정, dim 추가 확인
        ]

        schema = CollectionSchema(fields=fields, description="Vector collection with string ID", enable_dynamic_field=True)
        
        # Milvus 컬렉션 생성 시 정확한 파라미터 전달
        collection = Collection(name=collection_name, schema=schema)
        
        # 인덱스 생성 (필수)
        collection.create_index(
            field_name="vector",
            index_params={"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE, "params": {"nlist": 1024}}
        )
        
        collection.load()  # 컬렉션 로드 필수
        
    return get_vector_store(collection_name)


def delete_collection(collection_name:str):
    client = MilvusClient(uri=URI)
    
    # 컬렉션 존재 여부 확인 후 삭제 (필요하면 활성화)
    if client.has_collection(collection_name):
        client.drop_collection(collection_name)


def get_vector_store(collection_name:str):
    embeddings = get_embedding_model()
    vector_store = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": URI},
        collection_name=collection_name,
        index_params={"index_type": INDEX_TYPE, "metric_type": METRIC_TYPE},
    )
    
    return vector_store
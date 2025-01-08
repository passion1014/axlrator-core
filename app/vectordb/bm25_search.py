import os
import json
from typing import List, Dict, Any
from tqdm import tqdm
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from app.vectordb.faiss_vectordb import FaissVectorDB

# BM25 검색을 위한 Elasticsearch 래퍼 클래스
class ElasticsearchBM25:
    def __init__(self, index_name: str = "contextual_bm25_index"):
        elasticsearch_host = os.getenv("ELASTICSEARCH_HOST")
        
        self.es_client = Elasticsearch(elasticsearch_host)
        self.index_name = index_name
        self.create_index() # TODO = ElasticsearchBM25 서버 시작시 한번만 초기화 하고 사용할 수 있도록 수정 필요

    # Elasticsearch 인덱스 생성 및 설정
    def create_index(self):
        index_settings = {
            "settings": {
                "analysis": {"analyzer": {"default": {"type": "english"}}},
                "similarity": {"default": {"type": "BM25"}},
                "index.queries.cache.enabled": False  # 쿼리 캐시 비활성화
            },
            "mappings": {
                "properties": {
                    "content": {"type": "text", "analyzer": "english"},
                    "contextualized_content": {"type": "text", "analyzer": "english"},
                    "doc_id": {"type": "keyword", "index": False},
                    "chunk_id": {"type": "keyword", "index": False},
                    "original_index": {"type": "integer", "index": False},
                }
            },
        }
        if not self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.create(index=self.index_name, body=index_settings)
            print(f"### Created index: {self.index_name}")
        else :
            print(f"### Index already exists: {self.index_name}")

    # 문서 인덱싱 함수
    def index_documents(self, documents: List[Dict[str, Any]]):
        actions = [
            {
                "_index": self.index_name,
                "_source": {
                    "content": doc["original_content"],
                    "contextualized_content": doc["contextualized_content"],
                    "doc_id": doc["doc_id"],
                    "chunk_id": doc["chunk_id"],
                    "original_index": doc["original_index"],
                },
            }
            for doc in documents
        ]
        success, _ = bulk(self.es_client, actions)
        self.es_client.indices.refresh(index=self.index_name)
        return success

    # 검색 함수
    def search(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        self.es_client.indices.refresh(index=self.index_name)  # 검색 전 강제 새로고침
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "contextualized_content"],
                }
            },
            "size": k,
        }
        response = self.es_client.search(index=self.index_name, body=search_body)
        return [
            {
                "doc_id": hit["_source"]["doc_id"],
                "original_index": hit["_source"]["original_index"],
                "content": hit["_source"]["content"],
                "contextualized_content": hit["_source"]["contextualized_content"],
                "score": hit["_score"],
            }
            for hit in response["hits"]["hits"]
        ]
    
# Elasticsearch BM25 인덱스 생성 함수
# def create_elasticsearch_bm25_index(db: ContextualVectorDB):
def create_elasticsearch_bm25_index(index_name: str, org_resrc, chunk_list: List):
    documents = [
        {
            "_index": index_name,
            "original_content": chunk.content,
            "contextualized_content": chunk.context_chunk,
            "doc_id": org_resrc.id,
            "chunk_id": chunk.id,
            "original_index": chunk.seq, # 문서의 순서
        }
        for chunk in chunk_list
    ]
    
    print(f"### create_elasticsearch_bm25_index = {documents}")

    es_bm25 = ElasticsearchBM25(index_name=index_name)
    es_bm25.index_documents(documents)
    
    return es_bm25


# 고급 검색 함수 - 시맨틱 검색과 BM25 검색 결과를 결합
# def retrieve_advanced(query: str, db: ContextualVectorDB, es_bm25: ElasticsearchBM25, k: int, semantic_weight: float = 0.8, bm25_weight: float = 0.2):
def retrieve_advanced(query: str, db: FaissVectorDB, es_bm25: ElasticsearchBM25, k: int, semantic_weight: float = 0.8, bm25_weight: float = 0.2):
    num_chunks_to_recall = 150

    # 시맨틱 검색 수행
    semantic_results = db.search_similar_documents(query, k=num_chunks_to_recall) 
    # ranked_chunk_ids = [(result['metadata']['doc_id'], result['metadata']['original_index']) 
    #                     for result in semantic_results 
    #                     if result is not None and 'metadata' in result]
    ranked_chunk_ids = [
        (result['metadata'].get('doc_id', 'unknown_doc_id'), result['metadata'].get('original_index', -1))
        for result in semantic_results
        if result and 'metadata' in result
    ]    
    # 현재 search_similar_documents 결과는 content, metadata를 넘겨주고 있으며, metadata에 값이 존재하지 않는다. TODO
    
    # BM25 검색 수행
    bm25_results = es_bm25.search(query, k=num_chunks_to_recall)
    ranked_bm25_chunk_ids = [(result['doc_id'], result['original_index']) for result in bm25_results]

    # 결과 결합 및 점수 계산
    chunk_ids = list(set(ranked_chunk_ids + ranked_bm25_chunk_ids))
    chunk_id_to_score = {}

    # 각 청크 ID에 대해 시맨틱 검색과 BM25 검색 결과를 결합하여 최종 점수 계산
    for chunk_id in chunk_ids:
        score = 0
        # 시맨틱 검색 결과에 있는 경우 가중치를 적용한 점수 추가
        if chunk_id in ranked_chunk_ids:
            index = ranked_chunk_ids.index(chunk_id)
            score += semantic_weight * (1 / (index + 1))  # Weighted 1/n scoring for semantic
        if chunk_id in ranked_bm25_chunk_ids:
            index = ranked_bm25_chunk_ids.index(chunk_id)
            score += bm25_weight * (1 / (index + 1))  # Weighted 1/n scoring for BM25
        chunk_id_to_score[chunk_id] = score

    sorted_chunk_ids = sorted(
        chunk_id_to_score.keys(), key=lambda x: (chunk_id_to_score[x], x[0], x[1]), reverse=True
    )

    for index, chunk_id in enumerate(sorted_chunk_ids):
        chunk_id_to_score[chunk_id] = 1 / (index + 1)

    # 최종 결과 준비
    final_results = []
    semantic_count = 0
    bm25_count = 0
    for chunk_id in sorted_chunk_ids[:k]:
        # db.metadata 부분 수정 필요
        # chunk_metadata = next(chunk for chunk in db.metadata if chunk['doc_id'] == chunk_id[0] and chunk['original_index'] == chunk_id[1])
        chunk_metadata = next(chunk for chunk in db.metadata if chunk['doc_id'] == chunk_id[0])
        is_from_semantic = chunk_id in ranked_chunk_ids
        is_from_bm25 = chunk_id in ranked_bm25_chunk_ids
        final_results.append({
            'chunk': chunk_metadata,
            'score': chunk_id_to_score[chunk_id],
            'from_semantic': is_from_semantic,
            'from_bm25': is_from_bm25
        })
        
        if is_from_semantic and not is_from_bm25:
            semantic_count += 1
        elif is_from_bm25 and not is_from_semantic:
            bm25_count += 1
        else:  # it's in both
            semantic_count += 0.5
            bm25_count += 0.5

    return final_results, semantic_count, bm25_count

# JSONL 파일 로드 함수
def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r') as file:
        return [json.loads(line) for line in file]
    
    

# 고급 데이터베이스 평가 함수
# def evaluate_db_advanced(db: ContextualVectorDB, original_jsonl_path: str, k: int):
def evaluate_db_advanced(db: FaissVectorDB, original_jsonl_path: str, k: int):
    original_data = load_jsonl(original_jsonl_path)
    es_bm25 = create_elasticsearch_bm25_index(db)
    
    try:
        # 웜업 쿼리 실행
        warm_up_queries = original_data[:10]
        for query_item in warm_up_queries:
            _ = retrieve_advanced(query_item['query'], db, es_bm25, k)
        
        total_score = 0
        total_semantic_count = 0
        total_bm25_count = 0
        total_results = 0
        
        # 각 쿼리에 대한 평가 수행
        for query_item in tqdm(original_data, desc="Evaluating retrieval"):
            query = query_item['query']
            golden_chunk_uuids = query_item['golden_chunk_uuids']
            
            golden_contents = []
            for doc_uuid, chunk_index in golden_chunk_uuids:
                golden_doc = next((doc for doc in query_item['golden_documents'] if doc['uuid'] == doc_uuid), None)
                if golden_doc:
                    golden_chunk = next((chunk for chunk in golden_doc['chunks'] if chunk['index'] == chunk_index), None)
                    if golden_chunk:
                        golden_contents.append(golden_chunk['content'].strip())
            
            if not golden_contents:
                print(f"Warning: No golden contents found for query: {query}")
                continue
            
            retrieved_docs, semantic_count, bm25_count = retrieve_advanced(query, db, es_bm25, k)
            
            chunks_found = 0
            for golden_content in golden_contents:
                for doc in retrieved_docs[:k]:
                    retrieved_content = doc['chunk']['original_content'].strip()
                    if retrieved_content == golden_content:
                        chunks_found += 1
                        break
            
            query_score = chunks_found / len(golden_contents)
            total_score += query_score
            
            total_semantic_count += semantic_count
            total_bm25_count += bm25_count
            total_results += len(retrieved_docs)
        
        # 최종 결과 계산 및 출력
        total_queries = len(original_data)
        average_score = total_score / total_queries
        pass_at_n = average_score * 100
        
        semantic_percentage = (total_semantic_count / total_results) * 100 if total_results > 0 else 0
        bm25_percentage = (total_bm25_count / total_results) * 100 if total_results > 0 else 0
        
        results = {
            "pass_at_n": pass_at_n,
            "average_score": average_score,
            "total_queries": total_queries
        }
        
        print(f"Pass@{k}: {pass_at_n:.2f}%")
        print(f"Average Score: {average_score:.2f}")
        print(f"Total queries: {total_queries}")
        print(f"Percentage of results from semantic search: {semantic_percentage:.2f}%")
        print(f"Percentage of results from BM25: {bm25_percentage:.2f}%")
        
        return results, {"semantic": semantic_percentage, "bm25": bm25_percentage}
    
    finally:
        # Elasticsearch 인덱스 삭제
        if es_bm25.es_client.indices.exists(index=es_bm25.index_name):
            es_bm25.es_client.indices.delete(index=es_bm25.index_name)
            print(f"Deleted Elasticsearch index: {es_bm25.index_name}")
            


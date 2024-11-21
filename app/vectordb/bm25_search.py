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
        self.es_client = Elasticsearch("http://localhost:9200")
        self.index_name = index_name
        self.create_index()

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
            print(f"Created index: {self.index_name}")

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
def create_elasticsearch_bm25_index(db: ContextualVectorDB):
    es_bm25 = ElasticsearchBM25()
    es_bm25.index_documents(db.metadata) # TODO : metadata?
    return es_bm25

# 고급 검색 함수 - 시맨틱 검색과 BM25 검색 결과를 결합
# def retrieve_advanced(query: str, db: ContextualVectorDB, es_bm25: ElasticsearchBM25, k: int, semantic_weight: float = 0.8, bm25_weight: float = 0.2):
def retrieve_advanced(query: str, db: FaissVectorDB, es_bm25: ElasticsearchBM25, k: int, semantic_weight: float = 0.8, bm25_weight: float = 0.2):
    num_chunks_to_recall = 150

    # 시맨틱 검색 수행
    semantic_results = db.search_similar_documents(query, k=num_chunks_to_recall) 
    ranked_chunk_ids = [(result['metadata']['doc_id'], result['metadata']['original_index']) for result in semantic_results]

    # BM25 검색 수행
    bm25_results = es_bm25.search(query, k=num_chunks_to_recall)
    ranked_bm25_chunk_ids = [(result['doc_id'], result['original_index']) for result in bm25_results]

    # 결과 결합 및 점수 계산
    chunk_ids = list(set(ranked_chunk_ids + ranked_bm25_chunk_ids))
    chunk_id_to_score = {}

    for chunk_id in chunk_ids:
        score = 0
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
        chunk_metadata = next(chunk for chunk in db.metadata if chunk['doc_id'] == chunk_id[0] and chunk['original_index'] == chunk_id[1])
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
def evaluate_db_advanced(db: ContextualVectorDB, original_jsonl_path: str, k: int):
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
            



# -------------------------------------------
# 샘플
# -------------------------------------------
# import os
# import pickle
# import json
# import numpy as np
# import voyageai
# from typing import List, Dict, Any
# from tqdm import tqdm
# import anthropic
# import threading
# import time
# from concurrent.futures import ThreadPoolExecutor, as_completed

# # 문맥적 벡터 데이터베이스를 위한 클래스
# class ContextualVectorDB:
#     def __init__(self, name: str, voyage_api_key=None, anthropic_api_key=None):
#         # API 키 설정 - 환경변수에서 가져오거나 직접 전달
#         if voyage_api_key is None:
#             voyage_api_key = os.getenv("VOYAGE_API_KEY")
#         if anthropic_api_key is None:
#             anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
#         # Voyage와 Anthropic 클라이언트 초기화
#         self.voyage_client = voyageai.Client(api_key=voyage_api_key)
#         self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
#         self.name = name
#         self.embeddings = [] # 임베딩 저장 리스트
#         self.metadata = [] # 메타데이터 저장 리스트
#         self.query_cache = {} # 쿼리 캐시 딕셔너리
#         self.db_path = f"./data/{name}/contextual_vector_db.pkl" # DB 저장 경로

#         # 토큰 사용량 추적을 위한 카운터
#         self.token_counts = {
#             'input': 0,
#             'output': 0, 
#             'cache_read': 0,
#             'cache_creation': 0
#         }
#         self.token_lock = threading.Lock() # 스레드 안전을 위한 락

#     # 문서와 청크의 문맥을 파악하는 함수
#     def situate_context(self, doc: str, chunk: str) -> tuple[str, Any]:
#         # 전체 문서를 위한 프롬프트
#         DOCUMENT_CONTEXT_PROMPT = """
#         <document>
#         {doc_content}
#         </document>
#         """

#         # 청크를 위한 프롬프트
#         CHUNK_CONTEXT_PROMPT = """
#         Here is the chunk we want to situate within the whole document
#         <chunk>
#         {chunk_content}
#         </chunk>

#         Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
#         Answer only with the succinct context and nothing else.
#         """

#         # Claude API를 통한 문맥 생성
#         response = self.anthropic_client.beta.prompt_caching.messages.create(
#             model="claude-3-haiku-20240307",
#             max_tokens=1000,
#             temperature=0.0,
#             messages=[
#                 {
#                     "role": "user", 
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
#                             "cache_control": {"type": "ephemeral"} # 문서 프롬프트 캐싱
#                         },
#                         {
#                             "type": "text",
#                             "text": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk),
#                         },
#                     ]
#                 },
#             ],
#             extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
#         )
#         return response.content[0].text, response.usage

#     # 데이터 로딩 및 처리 함수
#     def load_data(self, dataset: List[Dict[str, Any]], parallel_threads: int = 1):
#         # 이미 로드된 경우 스킵
#         if self.embeddings and self.metadata:
#             print("Vector database is already loaded. Skipping data loading.")
#             return
#         # 저장된 DB가 있는 경우 로드
#         if os.path.exists(self.db_path):
#             print("Loading vector database from disk.")
#             self.load_db()
#             return

#         texts_to_embed = []
#         metadata = []
#         total_chunks = sum(len(doc['chunks']) for doc in dataset)

#         # 각 청크 처리를 위한 함수
#         def process_chunk(doc, chunk):
#             contextualized_text, usage = self.situate_context(doc['content'], chunk['content'])
#             # 토큰 사용량 업데이트
#             with self.token_lock:
#                 self.token_counts['input'] += usage.input_tokens
#                 self.token_counts['output'] += usage.output_tokens
#                 self.token_counts['cache_read'] += usage.cache_read_input_tokens
#                 self.token_counts['cache_creation'] += usage.cache_creation_input_tokens
            
#             return {
#                 'text_to_embed': f"{chunk['content']}\n\n{contextualized_text}",
#                 'metadata': {
#                     'doc_id': doc['doc_id'],
#                     'original_uuid': doc['original_uuid'],
#                     'chunk_id': chunk['chunk_id'],
#                     'original_index': chunk['original_index'],
#                     'original_content': chunk['content'],
#                     'contextualized_content': contextualized_text
#                 }
#             }

#         # 병렬 처리
#         print(f"Processing {total_chunks} chunks with {parallel_threads} threads")
#         with ThreadPoolExecutor(max_workers=parallel_threads) as executor:
#             futures = []
#             for doc in dataset:
#                 for chunk in doc['chunks']:
#                     futures.append(executor.submit(process_chunk, doc, chunk))
            
#             for future in tqdm(as_completed(futures), total=total_chunks, desc="Processing chunks"):
#                 result = future.result()
#                 texts_to_embed.append(result['text_to_embed'])
#                 metadata.append(result['metadata'])

#         # 임베딩 생성 및 저장
#         self._embed_and_store(texts_to_embed, metadata)
#         self.save_db()

#         # 토큰 사용량 로깅
#         print(f"Contextual Vector database loaded and saved. Total chunks processed: {len(texts_to_embed)}")
#         print(f"Total input tokens without caching: {self.token_counts['input']}")
#         print(f"Total output tokens: {self.token_counts['output']}")
#         print(f"Total input tokens written to cache: {self.token_counts['cache_creation']}")
#         print(f"Total input tokens read from cache: {self.token_counts['cache_read']}")
        
#         total_tokens = self.token_counts['input'] + self.token_counts['cache_read'] + self.token_counts['cache_creation']
#         savings_percentage = (self.token_counts['cache_read'] / total_tokens) * 100 if total_tokens > 0 else 0
#         print(f"Total input token savings from prompt caching: {savings_percentage:.2f}% of all input tokens used were read from cache.")
#         print("Tokens read from cache come at a 90 percent discount!")

#     # Voyage AI를 사용한 임베딩 생성 함수
#     def _embed_and_store(self, texts: List[str], data: List[Dict[str, Any]]):
#         batch_size = 128
#         result = [
#             self.voyage_client.embed(
#                 texts[i : i + batch_size],
#                 model="voyage-2"
#             ).embeddings
#             for i in range(0, len(texts), batch_size)
#         ]
#         self.embeddings = [embedding for batch in result for embedding in batch]
#         self.metadata = data

#     # 검색 함수
#     def search(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
#         # 쿼리 임베딩 생성 또는 캐시에서 가져오기
#         if query in self.query_cache:
#             query_embedding = self.query_cache[query]
#         else:
#             query_embedding = self.voyage_client.embed([query], model="voyage-2").embeddings[0]
#             self.query_cache[query] = query_embedding

#         if not self.embeddings:
#             raise ValueError("No data loaded in the vector database.")

#         # 유사도 계산 및 상위 결과 반환
#         similarities = np.dot(self.embeddings, query_embedding)
#         top_indices = np.argsort(similarities)[::-1][:k]
        
#         top_results = []
#         for idx in top_indices:
#             result = {
#                 "metadata": self.metadata[idx],
#                 "similarity": float(similarities[idx]),
#             }
#             top_results.append(result)
#         return top_results

#     # DB 저장 함수
#     def save_db(self):
#         data = {
#             "embeddings": self.embeddings,
#             "metadata": self.metadata,
#             "query_cache": json.dumps(self.query_cache),
#         }
#         os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
#         with open(self.db_path, "wb") as file:
#             pickle.dump(data, file)

#     # DB 로드 함수
#     def load_db(self):
#         if not os.path.exists(self.db_path):
#             raise ValueError("Vector database file not found. Use load_data to create a new database.")
#         with open(self.db_path, "rb") as file:
#             data = pickle.load(file)
#         self.embeddings = data["embeddings"]
#         self.metadata = data["metadata"]
#         self.query_cache = json.loads(data["query_cache"])
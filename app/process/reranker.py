

import os
from typing import Any, Dict, List
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
# from langchain.retrievers.document_compressors import FlashrankRerank
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from langchain.schema import Document
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForSequenceClassification
from app.utils import get_rerank_model, get_server_type
from app.vectordb.faiss_vectordb import FaissVectorDB


class AlfredReranker:
    '''
        ## 주요 특징 및 작동 방식

        1. **목적**: 검색된 문서들의 순위를 재조정하여 질문에 가장 관련성 높은 문서를 상위로 올림
        2. **구조**: 질문과 문서를 동시에 입력으로 받아 처리
        3. **작동 방식**:
        - 질문과 문서를 하나의 입력으로 사용하여 유사도를 직접 출력
        - Self-attention 메커니즘을 통해 질문과 문서를 동시에 분석
        4. **장점**:
        - 더 정확한 유사도 측정 가능
        - 질문과 문서 사이의 의미론적 유사성을 깊이 탐색
        5. **한계점**:
        - 연산 비용이 높고 시간이 오래 걸림
        - 대규모 문서 집합에 직접 적용하기 어려움

        ## Reranker의 주요 장점

        1. 더 정확한 유사도 측정
        2. 심층적인 의미론적 유사성 탐색
        3. 검색 결과 개선
        4. RAG 시스템 성능 향상
        5. 유연한 통합
        6. 다양한 사전 학습 모델 선택 가능

        ## Reranker 사용 시 문서 수 설정

        - 일반적으로 상위 5~10개 문서에 대해 reranking 수행
        - 최적의 문서 수는 실험과 평가를 통해 결정 필요

        ## Reranker 사용시 Trade-offs

        1. 정확도 vs 처리 시간
        2. 성능 향상 vs 계산 비용
        3. 검색 속도 vs 관련성 정확도
        4. 시스템 요구사항 충족
        5. 데이터셋 특성 고려
    
    '''
    _instance = None  # 싱글턴 인스턴스 저장 변수
    
    def __new__(cls, model_name: str = "BAAI/bge-reranker-v2-m3", device: str = None):
        if cls._instance is None:
            cls._instance = super(AlfredReranker, cls).__new__(cls)
            cls._instance._init_model(model_name, device)
        return cls._instance  # 항상 같은 인스턴스 반환

    def _init_model(self, model_name: str, device: str):
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)

    
    # def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str = None):
    #     self.api_key = os.getenv("COHERE_API_KEY")
    #     self.rerank_model = os.getenv("RERANK_MODEL_NAME")
    #     self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
    #     self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    #     self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device)


    def cross_encoder_faissdb(self, query: str, vectorDB: FaissVectorDB, k: int) -> List[Dict[str, Any]]:
        '''
        # Cross Encoder Reranker
        
        Cross Encoder Reranker는 질문과 문서를 동시에 입력으로 받아, 두 입력 간의 유사도를 직접 계산하여 문서의 순위를 재조정하는 모델
        이 모델은 Self-attention 메커니즘을 활용하여 질문과 문서의 의미론적 유사성을 깊이 있게 분석하며, 더 정확한 유사도 측정을 가능하게 한다.

        ## 실제 사용

        - 일반적으로 초기 검색에서 상위 k개의 문서에 대해서만 reranking 수행
        - Bi-encoder로 빠르게 후보를 추출한 후, Cross encoder로 정확도를 높이는 방식으로 활용

        ## 구현

        - Hugging Face의 cross encoder 모델 또는 BAAI/bge-reranker와 같은 모델 사용
        - LangChain 등의 프레임워크에서 CrossEncoderReranker 컴포넌트를 통해 쉽게 통합 가능

        '''
        # 상위 3개의 문서 선택
        compressor = CrossEncoderReranker(model="BAAI/bge-reranker-v2-m3", top_n=3)

        # 문서 압축 검색기 초기화
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=vectorDB.as_retriever(search_kwargs={"k": 10})
        )

        # 압축된 문서 검색
        compressed_docs = compression_retriever.invoke(query)

        # 결과값 출력하여 확인
        # print(
        #     f"\n{'-' * 100}\n".join(
        #         [f"Document {i+1}:\n\n" + d.page_content for i, d in enumerate(compressed_docs)]
        #     )
        # )
        
        return compressed_docs


    def cross_encoder(self, query: str, documents: List[Dict[str, Any]], k: int = 3) -> List[Dict[str, Any]]:
        '''
        크로스 인코더 모델을 사용하여 쿼리에 대한 관련성을 기준으로 문서 목록을 재정렬합니다.

        매개변수:
            query (str): 쿼리 문자열.
            documents (List[Dict[str, Any]]): 각 문서가 "page_content"와 같은 키를 가진 사전으로 표현된 문서 목록.
            k (int): 재정렬 후 반환할 상위 문서의 수.

        반환값:
            List[Dict[str, Any]]: 상위 k개의 재정렬된 문서 목록.
        '''
        if not documents:
            return []

        # Prepare inputs
        pairs = [(query, doc["content"]) for doc in documents]
        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512
        ).to(self.device)

        # Compute scores
        with torch.no_grad():
            scores = self.model(**inputs).logits.squeeze(-1)  # Extract scores

        # Attach scores and sort
        for i, doc in enumerate(documents):
            doc["score"] = scores[i].item()
        
        sorted_docs = sorted(documents, key=lambda x: x["score"], reverse=True)
        
        return sorted_docs[:k]




    # def cohere_rerank(self, query: str, target_list: List[Dict], vectorDB: FaissVectorDB, k: int) -> List[Dict[str, Any]]: 
    #     '''
    #     # Cohere Reranker

    #     Cohere Reranker는 Cohere의 API를 활용하여 질문과 문서 간의 유사도를 평가하고 문서의 순위를 재조정하는 기능을 제공합니다.
    #     이 모델은 문서의 의미론적 유사성을 분석하여, 주어진 질문에 가장 적합한 문서를 상위에 배치합니다.

    #     ## 실제 사용

    #     - 초기 검색에서 상위 k개의 문서에 대해서만 reranking을 수행하여 효율성을 높입니다.
    #     - Bi-encoder로 빠르게 후보를 추출한 후, Cohere Reranker로 정확도를 높이는 방식으로 활용됩니다.

    #     ## 구현

    #     - Cohere의 rerank API를 사용하여 문서의 순위를 재조정합니다.
    #     - API 호출 시, 질문과 문서 리스트를 입력으로 제공하며, 상위 k개의 문서를 반환합니다.
    #     - 반환된 문서는 relevance score에 따라 정렬되어 있습니다.
    #     '''

    #     def chunk_to_content(chunk: Dict[str, Any]) -> str:
    #         original_content = chunk['metadata']['original_content']
    #         contextualized_content = chunk['metadata']['contextualized_content']
    #         return f"{original_content}\n\nContext: {contextualized_content}" 

        
    #     co = cohere.Client( self.api_key )
        
    #     # Extract documents for reranking, using the contextualized content
    #     documents = [chunk_to_content(res) for res in target_list]

    #     response = co.rerank(
    #         model="rerank-english-v3.0",
    #         query=query,
    #         documents=documents,
    #         top_n=k
    #     )
        
    #     # 서버 부하를 줄이기 위한 딜레이 - 지금은 쓸데없어 보이므로 주석!
    #     # time.sleep(0.1)
        
    #     final_results = []
    #     for r in response.results:
    #         original_result = target_list[r.index]
    #         final_results.append({
    #             "chunk": original_result['metadata'],
    #             "score": r.relevance_score
    #         })
        
    #     return final_results

    # def flash_rank_rerank(self, query: str, target_list: List[Dict], vectorDB: FaissVectorDB, k: int) -> List[Dict[str, Any]]:
    #     # # LLM 초기화
    #     llm = ChatOpenAI(temperature=0)
        
    #     # 문서 압축기 초기화
    #     # compressor = FlashrankRerank(model="ms-marco-MultiBERT-L-12") #TODO model명은 환경변수로 추출
    #     compressor = FlashrankRerank(
    #         model_name="ms-marco-MultiBERT-L-12",
    #         top_n=k  # 상위 k개 결과 반환
    #     )
    

    #     # 문맥 압축 검색기 초기화
    #     compression_retriever = ContextualCompressionRetriever(
    #         base_compressor=compressor, 
    #         base_retriever=vectorDB.as_retriever(search_kwargs={"k": 10})
    #     )
        
    #     # 압축된 문서 검색
    #     compressed_docs = compression_retriever.invoke(query)
    #     return compressed_docs

alfred_reranker = AlfredReranker()  # 싱글턴

def get_reranker():
    return alfred_reranker

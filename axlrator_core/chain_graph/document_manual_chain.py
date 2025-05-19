from langchain_core.runnables import RunnableConfig
from axlrator_core.chain_graph.agent_state import AgentState, CodeAssistAutoCompletion, CodeAssistChatState, CodeAssistState
from axlrator_core.common.code_assist_utils import extract_code_blocks
from axlrator_core.common.string_utils import is_table_name
from axlrator_core.db_model.data_repository import RSrcTableColumnRepository, RSrcTableRepository
from axlrator_core.process.reranker import get_reranker
from langgraph.graph import StateGraph, END
from axlrator_core.utils import get_llm_model
from axlrator_core.vectordb.bm25_search import ElasticsearchBM25
from langfuse.callback import CallbackHandler
from langgraph.types import StreamWriter
from langfuse import Langfuse

import logging

from axlrator_core.vectordb.vector_store import get_vector_store


class DocumentManualChain:
    def __init__(self, session, index_name:str="manual_document"):
        self.index_name = index_name
        self.db_session = session
        self.es_bm25 = ElasticsearchBM25(index_name=index_name)
        self.model = get_llm_model().with_config(callbacks=[CallbackHandler()])
        self.langfuse = Langfuse()

    async def contextual_reranker(self, state: CodeAssistState, k: int=10, semantic_weight: float = 0.8, bm25_weight: float = 0.2) -> CodeAssistState:
        question = state['question']

        # VectorDB / BM25 조회
        vector_store = get_vector_store(collection_name=self.index_name)
        semantic_results = vector_store.similarity_search_with_score(query=question, k=10) 
        
        bm25_results = self.es_bm25.search(query=question, k=10) # elasticsearch 조회
        
        logging.info("## Step1. Semantic Results: %s", semantic_results)
        logging.info("## Step1. BM25 Results: %s", bm25_results)

        # VectorDB의 doc_id, original_index값 추출
        ranked_chunk_ids = [
            (
                result['id'], 
                result['id']
            )
            for result in semantic_results
        ]

        # BM25조회 결과의 doc_id, original_index값 추출
        ranked_bm25_chunk_ids = [
            (
                result['doc_id'], 
                result['original_index']
            ) 
            for result in bm25_results
        ]
        
        # 2개의 결과를 머지 (중복제거)
        chunk_ids = list(set(ranked_chunk_ids + ranked_bm25_chunk_ids))

        # 스코어 계산 및 랭크퓨전 (RRF와 유사함)
        chunk_id_to_score = {}
        for chunk_id in chunk_ids:
            score = 0
            if chunk_id in ranked_chunk_ids:
                score += semantic_weight * (1 / (ranked_chunk_ids.index(chunk_id) + 1))
            if chunk_id in ranked_bm25_chunk_ids:
                score += bm25_weight * (1 / (ranked_bm25_chunk_ids.index(chunk_id) + 1))
            chunk_id_to_score[chunk_id] = score
            
        # 정렬 (score, chunk_id의 1번째, chunk_id의 2번째)
        sorted_chunk_ids = sorted(
            chunk_id_to_score.keys(), 
            key=lambda x: (chunk_id_to_score[x], x[0], x[1]), 
            reverse=True
        )
        logging.info("### Step2. 랭크퓨전 결과 (sorted_chunk_ids) : %s", sorted_chunk_ids)
        
        # docid와 content/value를 매핑한 딕셔너리 생성
        # semantic_docid_to_content = {result['vector_index']: result['content'] for result in semantic_results}
        # bm25_docid_to_value = {result['doc_id']: result['content'] for result in bm25_results}
        
        # docid와 content/value를 매핑한 딕셔너리 생성
        semantic_docid_to_content = {
            (
                result['id'], 
                result['id']
            ): result['content']
            for result in semantic_results
        }
        bm25_docid_to_value = {
            (
                result.get('doc_id', None),
                result.get('original_index', None)
            ): result.get('content', '')
            for result in bm25_results
        }

        # 리랭킹 하기 전 정렬된 데이터 리스트
        sorted_documents = [{
            'score': chunk_id_to_score[chunk_id],
            'from_semantic': chunk_id in ranked_chunk_ids,
            'from_bm25': chunk_id in ranked_bm25_chunk_ids,
            'content': (
                semantic_docid_to_content.get(chunk_id, 'Content not found') if chunk_id in ranked_chunk_ids
                else bm25_docid_to_value.get(chunk_id, 'Value not found') if chunk_id in ranked_bm25_chunk_ids
                else ''
            )
        } for chunk_id in sorted_chunk_ids[:k]]
        
        logging.info("### Step3. 머지/정렬된 결과(sorted_documents) : %s", sorted_documents)
        
        # 리랭킹
        valid_documents = [doc for doc in sorted_documents if doc['content']]
        reranker = get_reranker()
        reranker.cross_encoder(query=question, documents=valid_documents)

        state['context'] = valid_documents

        return state

    async def search_similar_context(self, state: AgentState) -> AgentState:
        enriched_query = state['question']
        
        vector_store = get_vector_store(collection_name=self.index_name)
        docs = vector_store.similarity_search_with_score(query=enriched_query, k=2) 
        
        # state['context'] = "\n".join(doc['content'] for doc in docs)
        state['context'] = combine_documents_with_relevance(docs)
        return state

    def get_table_desc(self, state: AgentState) -> AgentState:
        context = state['question']
        table_json = {}
        table_names = context.split(',')
        
        rsrc_table_repo = RSrcTableRepository(session=self.db_session)
        rsrc_table_column_repo = RSrcTableColumnRepository(session=self.db_session)

        for table_name in table_names:
            if table_name.strip():
                table_data = rsrc_table_repo.get_data_by_table_name(table_name=table_name.strip())
                for table in table_data:
                    columns = rsrc_table_column_repo.get_data_by_table_id(rsrc_table_id=table.id)
                    column_jsons = [{
                        'name': column.column_name,
                        'type': column.column_type,
                        'desc': column.column_desc.strip()
                    } for column in columns]

                    table_json[table_name.strip()] = {
                        'table_name': table_name.strip(),
                        'columns': column_jsons
                    }

        state['context'] = table_json
        return state

    async def generate_response_astream(self, state: CodeAssistState, writer: StreamWriter) -> CodeAssistChatState:
        prompt = state['prompt']
        response = self.model.invoke(prompt)

        # AIMessage 객체에서 텍스트 콘텐츠 추출
        state['response'] = response.content if hasattr(response, 'content') else str(response)

        return state
    
    def choose_prompt_for_task(self, state: CodeAssistState) -> CodeAssistState:
        langfuse_prompt = self.langfuse.get_prompt("AXL_MANUAL_DOC_QUERY", version=1)
        state['prompt'] = langfuse_prompt.compile(
            reference=state['context'],
            query=state['question'],
        )
        return state

    def chain_manual_query(self) -> CodeAssistState:
        '''
        메뉴얼 질문
        '''
        graph = StateGraph(CodeAssistState)
        graph.add_node("contextual_reranker", self.contextual_reranker) # hybrid cotext search
        # graph.add_node("search_similar_context", self.search_similar_context) # 컨텍스트 정보 조회
        graph.add_node("choose_prompt_for_task", self.choose_prompt_for_task) # 프롬프트 선택
        graph.add_node("generate_response_astream", self.generate_response_astream) # 모델호출
        
        graph.set_entry_point("contextual_reranker")    
        graph.add_edge("contextual_reranker", "choose_prompt_for_task")
        graph.add_edge("choose_prompt_for_task", "generate_response_astream")
        graph.add_edge("generate_response_astream", END)

        chain = graph.compile() # CompiledStateGraph
        chain.with_config(callbacks=[CallbackHandler()])
        
        return chain
    


# Helper function: combine_documents_with_relevance
def combine_documents_with_relevance(docs):
    # combined_context = "\n".join([doc['content'] for doc in docs])
    if not docs:
        return ""

    combined_context = []
    for doc in docs[:2]:  # 앞에서 2개의 항목만 사용
        if doc['content'] not in combined_context:  # 중복 제거
            combined_context.append(doc['content'])

    return "\n".join(combined_context)





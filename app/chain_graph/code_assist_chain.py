from langchain_core.prompts import PromptTemplate
from app.chain_graph.agent_state import AgentState, CodeAssistState
from app.db_model.data_repository import RSrcTableColumnRepository, RSrcTableRepository
from app.db_model.database import SessionLocal
from app.prompts.code_prompt import AUTO_CODE_TASK_PROMPT, CODE_ASSIST_TASK_PROMPT, MAKE_CODE_COMMENT_PROMPT, MAKE_MAPDATAUTIL_PROMPT, TEXT_SQL_PROMPT
from langgraph.graph import StateGraph, END
from app.utils import get_llm_model
from app.vectordb.bm25_search import ElasticsearchBM25
from app.vectordb.faiss_vectordb import FaissVectorDB
from langfuse.callback import CallbackHandler

class CodeAssistChain:
    def __init__(self, index_name="cg_code_assist"):
        self.index_name = index_name
        self.db_session = SessionLocal()
        self.faissVectorDB = FaissVectorDB(db_session=self.db_session, index_name=index_name)
        self.es_bm25 = ElasticsearchBM25(index_name=index_name)
        self.model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def context_node(self, state: CodeAssistState, k: int, semantic_weight: float = 0.8, bm25_weight: float = 0.2) -> CodeAssistState:
        question = state['question']

        # VectorDB / BM25 조회
        semantic_results = self.faissVectorDB.search_similar_documents(query=question, k=50)
        bm25_results = self.es_bm25.search(query=question, k=50)

        # VectorDB의 doc_id, original_index값 추출
        ranked_chunk_ids = [
            (result['metadata'].get('doc_id', None), result['metadata'].get('original_index', None))
            for result in semantic_results
            if 'metadata' in result and isinstance(result['metadata'], dict)
        ]

        # BM25조회 결과의 doc_id, original_index값 추출
        ranked_bm25_chunk_ids = [(result['doc_id'], result['original_index']) for result in bm25_results]
        
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
        sorted_chunk_ids = sorted(chunk_id_to_score.keys(), key=lambda x: (chunk_id_to_score[x], x[0], x[1]), reverse=True)

        state['context'] = [{
            'score': chunk_id_to_score[chunk_id],
            'from_semantic': chunk_id in ranked_chunk_ids,
            'from_bm25': chunk_id in ranked_bm25_chunk_ids
        } for chunk_id in sorted_chunk_ids[:k]]

        return state

    def generate_node(self, state: CodeAssistState, prompt: str) -> CodeAssistState:
        response = self.model.invoke(prompt)
        state['response'] = response
        return state

    def chain_predicate(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("context_node", self.context_node)
        workflow.add_node("generate_node", self.generate_node)
        workflow.set_entry_point("context_node")
        workflow.add_edge("context_node", END)

        chain = workflow.compile()
        chain.with_config(callbacks=[CallbackHandler()])
        return chain

    def code_assist_chain(self, task_type: str):
        def get_context(state: AgentState) -> AgentState:
            enriched_query = state['question']
            docs = self.faissVectorDB.search_similar_documents(query=enriched_query, k=2)
            state['context'] = self.combine_documents_with_relevance(docs)
            return state

        def get_table_desc(state: AgentState) -> AgentState:
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

        def generate_response(state: AgentState) -> AgentState:
            if task_type == "01":
                prompt = AUTO_CODE_TASK_PROMPT.format(SOURCE_CODE=state['question'])
            elif task_type == "02":
                prompt = CODE_ASSIST_TASK_PROMPT.format(
                    REFERENCE_CODE=state['context'],
                    TASK=state['question'],
                    CURRENT_CODE=state['current_code']
                )
            elif task_type == "03":
                prompt = MAKE_CODE_COMMENT_PROMPT.format(SOURCE_CODE=state['question'])
            elif task_type == "04":
                prompt = MAKE_MAPDATAUTIL_PROMPT.format(TABLE_DESC=state['context'])
            elif task_type == "05":
                prompt = TEXT_SQL_PROMPT.format(TABLE_DESC=state['context'], SQL_REQUEST=state['sql_request'])
            else:
                prompt = CODE_ASSIST_TASK_PROMPT.format(
                    REFERENCE_CODE=state['context'],
                    TASK=state['question'],
                    CURRENT_CODE=state['current_code']
                )

            response = self.model.invoke(prompt)
            state['response'] = response
            return state

        workflow = StateGraph(AgentState)
        if task_type in ["01", "03"]:
            workflow.add_node("generate_response", generate_response)
            workflow.set_entry_point("generate_response")
            workflow.add_edge("generate_response", END)
        elif task_type in ["02", "04", "05"]:
            workflow.add_node("get_context", get_context if task_type == "02" else get_table_desc)
            workflow.add_node("generate_response", generate_response)
            workflow.set_entry_point("get_context")
            workflow.add_edge("get_context", "generate_response")
            workflow.add_edge("generate_response", END)

        chain = workflow.compile()
        chain.with_config(callbacks=[CallbackHandler()])
        return chain

    @staticmethod
    def combine_documents_with_relevance(docs):
        return "\n".join(doc['content'] for doc in docs)


# ------------------------------------------------
# 아래는 이전 버전 - 삭제필요
# ------------------------------------------------
# 임시로 사용하는 함수 - 추후에는 사용하지 않음
def code_assist_chain(type:str):
    
    session = SessionLocal()
    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_code_assist")

    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        # 질문의 추가 맥락 생성
        # enriched_query = contextual_enrichment(state['question'])  # 맥락을 추가로 풍부화
        enriched_query = state['question']
        print(f"### enriched_query = {enriched_query}")
        
        # 맥락 기반 검색
        docs = faissVectorDB.search_similar_documents(query=enriched_query, k=2)
        print(f"### search_result = {docs}")
        
        # 문서 결합
        state['context'] = combine_documents_with_relevance(docs)  # 단순 병합 대신 관련성을 고려하여 결합
        return state

    def get_table_desc(state: AgentState) -> AgentState:
        context = state['question']

        rsrc_table_repository = RSrcTableRepository(session=session)
        rsrc_table_column_repository = RSrcTableColumnRepository(session=session)

        table_json = {}
        table_names = context.split(',')
        for table_name in table_names:
            if table_name.strip():  # 빈 문자열이 아닌 경우에만 처리
                table_data = rsrc_table_repository.get_data_by_table_name(table_name=table_name.strip())
                for table in table_data:
                    columns = rsrc_table_column_repository.get_data_by_table_id(rsrc_table_id=table.id)
                    
                    column_jsons = []
                    for column in columns:
                        column_jsons.append({
                            'name': column.column_name,
                            # 'column_korean_name': column.column_korean_name,
                            'type': column.column_type,
                            'desc': column.column_desc.strip()
                        })
                    
                    table_json[table_name.strip()] = {
                        'table_name': table_name.strip(),
                        'columns': column_jsons
                    }
                    
        # 문서 결합
        state['context'] = table_json
        return state


    def generate_response(state: AgentState) -> AgentState:
        
        if ("01" == type) : # autocode
            prompt = AUTO_CODE_TASK_PROMPT.format(
                SOURCE_CODE=state['question']
            )
        elif ("02" == type) :
            prompt = CODE_ASSIST_TASK_PROMPT.format(
                REFERENCE_CODE=state['context'],
                TASK=state['question'],
                CURRENT_CODE=state['current_code']
            )
            
        elif ("03" == type) : # 주석생성하기
            prompt = MAKE_CODE_COMMENT_PROMPT.format(
                SOURCE_CODE=state['question']
            )

        elif ("04" == type) : # 테이블명으로 MapDataUtil 생성하기
            prompt = MAKE_MAPDATAUTIL_PROMPT.format(
                TABLE_DESC=state['context']
            )

        elif ("05" == type) : # SQL 생성하기
            prompt = TEXT_SQL_PROMPT.format(
                TABLE_DESC=state['context'],
                SQL_REQUEST=state['sql_request']
            )

        else:
            prompt = CODE_ASSIST_TASK_PROMPT.format(
                REFERENCE_CODE=state['context'],
                TASK=state['question'],
                CURRENT_CODE=state['current_code']
            )
            pass

        response = model.invoke(prompt)
        
        state['response'] = response
        return state

    workflow = StateGraph(AgentState)

    # 노드 정의

    # 워크플로우 정의
    if ("01" == type) : # autocode
        workflow.add_node("generate_response", generate_response)
        
        workflow.set_entry_point("generate_response")
        workflow.add_edge("generate_response", END)
        pass

    elif ("02" == type) :
        workflow.add_node("get_context", get_context)
        workflow.add_node("generate_response", generate_response)
        
        workflow.set_entry_point("get_context")
        workflow.add_edge("get_context", "generate_response")
        workflow.add_edge("generate_response", END)
        pass

    elif ("03" == type) : # make comment
        workflow.add_node("generate_response", generate_response)
        
        workflow.set_entry_point("generate_response")
        workflow.add_edge("generate_response", END)
        pass

    elif ("04" == type) : # Table 정보로 MapDataUtil 생성하기
        workflow.add_node("get_table_desc", get_table_desc)
        workflow.add_node("generate_response", generate_response)
        
        workflow.set_entry_point("get_table_desc")
        workflow.add_edge("get_table_desc", "generate_response")
        workflow.add_edge("generate_response", END)
        pass

    elif ("05" == type) : # SQL 생성하기
        workflow.add_node("get_table_desc", get_table_desc)
        workflow.add_node("generate_response", generate_response)
        
        workflow.set_entry_point("get_table_desc")
        workflow.add_edge("get_table_desc", "generate_response")
        workflow.add_edge("generate_response", END)
        pass


    else:
        workflow.add_node("get_context", get_context)
        workflow.add_node("generate_response", generate_response)
        
        workflow.set_entry_point("get_context")
        workflow.add_edge("get_context", "generate_response")
        workflow.add_edge("generate_response", END)
        pass
    
    chain = workflow.compile() # CompiledStateGraph
    chain.with_config(callbacks=[CallbackHandler()])
    
    return chain

# Helper function: contextual_enrichment
def contextual_enrichment(query):
    # LLM을 이용하여 질문의 의도를 확장하거나 관련 정보를 추가
    enriched_query = f"{query} | Additional Context: Extract function and variable relationships."
    return enriched_query

# Helper function: combine_documents_with_relevance
def combine_documents_with_relevance(docs):
    # combined_context = "\n".join([doc['content'] for doc in sorted(docs, key=lambda x: x['score'], reverse=True)])
    combined_context = "\n".join([doc['content'] for doc in docs])
    return combined_context


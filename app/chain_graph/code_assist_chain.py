from langchain_core.runnables import RunnableConfig
from app.chain_graph.agent_state import AgentState, CodeAssistAutoCompletion, CodeAssistChatState, CodeAssistState
from app.common.string_utils import is_table_name
from app.db_model.data_repository import RSrcTableColumnRepository, RSrcTableRepository
from app.process.reranker import get_reranker
from langgraph.graph import StateGraph, END
from app.utils import get_llm_model
from app.vectordb.bm25_search import ElasticsearchBM25
from langfuse.callback import CallbackHandler
from langgraph.types import StreamWriter
from langfuse import Langfuse

import logging

from app.vectordb.vector_store import get_vector_store


class CodeAssistChain:
    def __init__(self, session, index_name:str="cg_code_assist"):
        self.index_name = index_name
        self.db_session = session
        self.es_bm25 = ElasticsearchBM25(index_name=index_name)
        self.model = get_llm_model().with_config(callbacks=[CallbackHandler()])
        self.langfuse = Langfuse()

    async def contextual_reranker(self, state: CodeAssistState, k: int=10, semantic_weight: float = 0.8, bm25_weight: float = 0.2) -> CodeAssistState:
        question = state['question']

        # VectorDB / BM25 조회
        vector_store = get_vector_store(collection_name=self.index_name)
        semantic_results = vector_store.similarity_search_with_score(query=question, k=50) 
        
        bm25_results = self.es_bm25.search(query=question, k=50) # elasticsearch 조회
        
        logging.info("## Step1. Semantic Results: %s", semantic_results)
        logging.info("## Step1. BM25 Results: %s", bm25_results)

        # VectorDB의 doc_id, original_index값 추출
        ranked_chunk_ids = [
            (
                result['org_resrc_id'], 
                result['seq']
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
                result['org_resrc_id'], 
                result['seq']
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
        
        state['context'] = "\n".join(doc['content'] for doc in docs)
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

    async def generate_talk(self, state: CodeAssistChatState, writer: StreamWriter) -> CodeAssistChatState:
        thread_id = state.get('thread_id', -1)
        
        config = RunnableConfig(
            recursion_limit=10,  # 최대 10개의 노드까지 방문. 그 이상은 RecursionError 발생
            configurable={"thread_id": thread_id},  # 스레드 ID 설정
        )

        langfuse_prompt = self.langfuse.get_prompt("CHAT_PROMPT", version=1)
        prompt = langfuse_prompt.compile(QUESTION=state['question'])

        # 호출
        chunks = []
        async for chunk in self.model.astream(prompt, config=config):
            writer(chunk)
            chunks.append(chunk)
        state['response'] = "".join(str(chunks))
        return state

    # below code is no longer used.
    # each 'task_type' should be broken down into seperate 'def'
    #   task_type 01 -> generate_nextcode (make next code)
    #   task_type 02 -> generate_by_instruction (coding as ordered)
    #   task_type 03 -> generate_comment
    #   task_type 04 -> generate_DSC_mapdatautil (*DSC=Domain-Specific-Coding)
    #   task_type 05 -> generate_text2sql
    #   task_type ?? -> generate_talk
    # TODO : async, sync 둘다 가능하도록 변경 필요
    async def generate_response_astream(self, state: CodeAssistChatState, writer: StreamWriter) -> CodeAssistChatState:
        prompt = state['prompt']
        
        # Stream 방식
        chunks = []
        async for chunk in self.model.astream(prompt):
            writer(chunk)
            chunks.append(chunk)
        state['response'] = "".join(str(chunks))
        return state
    
    def choose_prompt_for_task(self, state: CodeAssistState) -> CodeAssistState:
        # valid_documents[0]['content']
        reference_code = combine_documents_with_relevance(state['context'])
        
        langfuse_prompt = self.langfuse.get_prompt("CODE_ASSIST_TASK_PROMPT", version=1)
        prompt = langfuse_prompt.compile(
            REFERENCE_CODE=reference_code,
            TASK=state['question'],
            CURRENT_CODE=state['current_code']
        )
        
        state['prompt'] = prompt
        
        return state

    def chain_codeassist(self) -> CodeAssistState:
        graph = StateGraph(CodeAssistState)
        graph.add_node("contextual_reranker", self.contextual_reranker) # 컨텍스트 정보 조회
        graph.add_node("choose_prompt_for_task", self.choose_prompt_for_task) # 프롬프트 선택
        graph.add_node("generate_response_astream", self.generate_response_astream) # 모델호출
        
        graph.set_entry_point("contextual_reranker")
        graph.add_edge("contextual_reranker", "choose_prompt_for_task")
        graph.add_edge("choose_prompt_for_task", "generate_response_astream")
        graph.add_edge("generate_response_astream", END)

        chain = graph.compile() # CompiledStateGraph
        chain.with_config(callbacks=[CallbackHandler()])
        
        return chain
    
    def chain_make_comment(self) -> CodeAssistState:
        pass
        # elif ("03" == type) : # 주석생성하기
        #     langfuse_prompt = langfuse.get_prompt("MAKE_CODE_COMMENT_PROMPT", version=1)
        #     prompt = langfuse_prompt.compile(
        #         SOURCE_CODE=state['question']
        #     )

    def chain_autocompletion(self) -> CodeAssistAutoCompletion:
        
        def _prompt_node(state: CodeAssistAutoCompletion) -> CodeAssistAutoCompletion:
            langfuse_prompt = self.langfuse.get_prompt("AXL_CODE_AUTOCOMPLETION")
            state['prompt'] = langfuse_prompt.compile(
                current_code=state['current_code']
            )
            
            return state

        def _generate_node(state: CodeAssistAutoCompletion) -> CodeAssistAutoCompletion:
            prompt = state['prompt']
            result = self.model.invoke(prompt)  # 동기 호출로 변경
            state['response'] = result.content
            return state            
        
        graph = StateGraph(CodeAssistAutoCompletion)
        graph.add_node("prompt_node", _prompt_node) # AXL_CODE_AUTOCOMPLETION
        graph.add_node("generate_node", _generate_node) # 모델호출
        
        graph.set_entry_point("prompt_node")
        graph.add_edge("prompt_node", "generate_node")
        graph.add_edge("generate_node", END)

        chain = graph.compile()
        chain.with_config(callbacks=[CallbackHandler()])
        
        return chain


# ------------------------------------------------
# 아래는 이전 버전 - 삭제필요
# ------------------------------------------------
# 임시로 사용하는 함수 - 추후에는 사용하지 않음
async def code_assist_chain(type:str, session):
    langfuse = Langfuse()
    
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    async def get_context(state: AgentState) -> AgentState:
        # 질문의 추가 맥락 생성
        # enriched_query = contextual_enrichment(state['question'])  # 맥락을 추가로 풍부화
        enriched_query = state['question']
        
        # 맥락 기반 검색
        vector_store = get_vector_store(collection_name="cg_code_assist")
        docs = vector_store.similarity_search_with_score(query=enriched_query, k=2) 
        
        # 문서 결합
        state['context'] = combine_documents_with_relevance(docs)  # 단순 병합 대신 관련성을 고려하여 결합
        return state

    async def get_table_desc(state: AgentState) -> AgentState:
        context = state['sql_request']
        
        if is_table_name(context):
            rsrc_table_repository = RSrcTableRepository(session=session)
            rsrc_table_column_repository = RSrcTableColumnRepository(session=session)

            table_json = {}
            table_names = context.split(',')
            for table_name in table_names:
                if table_name.strip():  # 빈 문자열이 아닌 경우에만 처리
                    table_data = await rsrc_table_repository.get_data_by_table_name(table_name=table_name.strip())
                    
                    for table in table_data:
                        columns = await rsrc_table_column_repository.get_data_by_table_id(rsrc_table_id=table.id)
                        
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
            state['current_code'] = ""
        else:
            state['context'] = ""
            state['current_code'] = context
            
        return state


    async def generate_response(state: AgentState, writer: StreamWriter) -> AgentState:
        
        if ("01" == type) : # autocode
            langfuse_prompt = langfuse.get_prompt("AUTO_CODE_TASK_PROMPT", version=1)
            prompt = langfuse_prompt.compile(SOURCE_CODE=state['question'])

        elif ("02" == type) :
            langfuse_prompt = langfuse.get_prompt("CODE_ASSIST_TASK_PROMPT", version=1)
            prompt = langfuse_prompt.compile(
                REFERENCE_CODE="", # state['context'],
                TASK=state['question'],
                CURRENT_CODE=state['current_code']
            )
            
        elif ("03" == type) : # 주석생성하기
            langfuse_prompt = langfuse.get_prompt("MAKE_CODE_COMMENT_PROMPT", version=1)
            prompt = langfuse_prompt.compile(
                SOURCE_CODE=state['question']
            )

        elif ("04" == type) : # 테이블명으로 MapDataUtil 생성하기
            langfuse_prompt = langfuse.get_prompt("MAKE_MAPDATAUTIL_PROMPT", version=1)
            prompt = langfuse_prompt.compile(
                TABLE_DESC=state['context']
            )

        elif ("05" == type) : # SQL 생성하기
            langfuse_prompt = langfuse.get_prompt("TEXT_SQL_PROMPT", version=1)
            prompt = langfuse_prompt.compile(
                TABLE_DESC=state['context'],
                SQL_REFERENCE=state['current_code'],
                SQL_REQUEST=state['question']
            )

        else:
            langfuse_prompt = langfuse.get_prompt("CODE_ASSIST_TASK_PROMPT", version=1)
            prompt = langfuse_prompt.compile(
                REFERENCE_CODE="", # state['context'],
                TASK=state['question'],
                CURRENT_CODE=state['current_code']
            )

        # Stream 방식
        chunks = []
        async for chunk in model.astream(prompt):
            writer(chunk)
            chunks.append(chunk)
        state['response'] = "".join(str(chunks))
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
        # workflow.add_node("generate_response", generate_response)
        
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


# Helper function: combine_documents_with_relevance
def combine_documents_with_relevance(docs):
    # combined_context = "\n".join([doc['content'] for doc in docs])
    if not docs:
        return ""

    combined_context = []
    for doc in docs[:3]:  # 앞에서 3개의 항목만 사용
        if doc['content'] not in combined_context:  # 중복 제거
            combined_context.append(doc['content'])

    return "\n".join(combined_context)





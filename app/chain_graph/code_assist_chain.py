from app.chain_graph.agent_state import AgentState
from app.db_model.data_repository import RSrcTableColumnRepository, RSrcTableRepository
from app.db_model.database import SessionLocal
from app.prompts.code_prompt import AUTO_CODE_TASK_PROMPT, CODE_ASSIST_TASK_PROMPT, MAKE_CODE_COMMENT_PROMPT, MAKE_MAPDATAUTIL_PROMPT, TEXT_SQL_PROMPT
from langgraph.graph import StateGraph, END
from app.utils import get_llm_model
from app.vectordb.faiss_vectordb import FaissVectorDB
from langfuse.callback import CallbackHandler

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


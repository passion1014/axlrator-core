from typing import TypedDict
from app.chain_graph.agent_state import AgentState
from app.db_model.database import SessionLocal
from app.prompts.code_prompt import CODE_ASSIST_TASK_PROMPT
from langgraph.graph import StateGraph, END
from app.utils import get_llm_model
from app.vectordb.faiss_vectordb import FaissVectorDB
from langfuse.callback import CallbackHandler




def create_rag_chain():
    # retriever 선언
    session = SessionLocal()
    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_code_assist")
    # faissVectorDB.read_index()

    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        
        # 질문의 추가 맥락 생성
        enriched_query = contextual_enrichment(state['question'])  # 맥락을 추가로 풍부화
        
        # 맥락 기반 검색
        docs = faissVectorDB.search_similar_documents(query=enriched_query, k=5)
        
        # 문서 결합
        state['context'] = combine_documents_with_relevance(docs)  # 단순 병합 대신 관련성을 고려하여 결합
        return state

    def generate_response(state: AgentState) -> AgentState:
        prompt = CODE_ASSIST_TASK_PROMPT.format(
            REFERENCE_CODE=state['context'],
            TASK=state['question'],
            CURRENT_CODE=''
        )
        response = model.invoke(prompt)
        
        state['response'] = response
        return state

    workflow = StateGraph(AgentState)

    # 노드 정의
    workflow.add_node("get_context", get_context)
    workflow.add_node("generate_response", generate_response)

    # 워크플로우 정의
    workflow.set_entry_point("get_context")
    workflow.add_edge("get_context", "generate_response")
    workflow.add_edge("generate_response", END)

    chain = workflow.compile()
    chain.with_config(callbacks=[CallbackHandler()])
    
    return chain

# Helper function: contextual_enrichment
def contextual_enrichment(query):
    # LLM을 이용하여 질문의 의도를 확장하거나 관련 정보를 추가
    enriched_query = f"{query} | Additional Context: Extract function and variable relationships."
    return enriched_query

# Helper function: combine_documents_with_relevance
def combine_documents_with_relevance(docs):
    combined_context = "\n".join([doc['content'] for doc in sorted(docs, key=lambda x: x['score'], reverse=True)])
    return combined_context

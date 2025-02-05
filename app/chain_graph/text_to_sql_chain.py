from app.chain_graph.agent_state import AgentState
from app.db_model.database import SessionLocal
from app.prompts.sql_prompt import SQL_QUERY_PROMPT
from app.utils import get_llm_model
from app.vectordb.faiss_vectordb import FaissVectorDB


from langfuse.callback import CallbackHandler
from langgraph.graph import END, StateGraph


def create_text_to_sql_chain():
    """
    text를 받아서 sql을 만들어줌
    """
    session = SessionLocal()

    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_text_to_sql")
    # faissVectorDB.read_index()

    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        docs = faissVectorDB.search_similar_documents(query=state['question'], k=5)

        state['context'] = docs # state['context'] = combine_documents(docs)
        return state

    def generate_response(state: AgentState) -> AgentState:
        prompt = SQL_QUERY_PROMPT.format(database_schema=state['context'], question=state['question'])
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
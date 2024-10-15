import os
from dotenv import load_dotenv
from typing import List, Tuple, TypedDict
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langserve.pydantic_v1 import BaseModel, Field
from app.prompts.code_prompt import CODE_ASSIST_TASK_PROMPT, CODE_SUMMARY_GENERATE_PROMPT
from app.prompts.sql_prompt import SQL_QUERY_PROMPT
from langgraph.graph import StateGraph, END
from langchain_community.vectorstores import FAISS
from app.prompts.prompts import ANSWER_PROMPT
from app.utils import combine_documents, merge_chat_history, get_embedding_model, get_llm_model
from app.vectordb.faiss_vectordb import FaissVectorDB
from .config import setup_logging
from langfuse.callback import CallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic

# .env 파일 로드
load_dotenv()

logger = setup_logging()


# FAISS 인덱스 경로 설정
# vector_index = os.getenv("VECTOR_DATABASE_INDEX")
# FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), f'../data/vector/{vector_index}')


# class ChatHistory(BaseModel):
#     chat_history: List[Tuple[str, str]] = Field(
#         ...,
#         extra={"widget": {"type": "chat", "input": "question"}},
#     )
#     question: str


class AgentState(TypedDict):
    # chat_history: List[Tuple[str, str]]
    question: str
    context: str
    response: str



# def load_vector_database():
#     warnings.warn("이 함수는 더 이상 사용되지 않으며 향후 버전에서 제거될 예정입니다. FaissVectorDB 클래스를 대신 사용하세요.", DeprecationWarning, stacklevel=2)
#     '''
#     Retriever를 반환하는 벡터 데이터베이스 로드 함수
#     '''
#     embeddings = get_embedding_model()
    
#     try:
#         db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
#         logger.info(f"----- FAISS index loaded from: {FAISS_INDEX_PATH}")
        
#     except ValueError as e:
#         logger.error(f"Error loading FAISS index: {e}")
#         db = FAISS.load_local(FAISS_INDEX_PATH, allow_dangerous_deserialization=True)
#         db.embeddings = embeddings

#     retriever = db.as_retriever(search_kwargs={"k": 1})    
#     logger.info(f"----- Number of items in FAISS index: {len(db.index_to_docstore_id)}")
    
#     return retriever



def create_rag_chain():
    # retriever 선언
    # retriever = load_vector_database()
    faissVectorDB = FaissVectorDB()
    faissVectorDB.read_index(index_name="cg_code_assist")
    
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        print(f"------------------------ get_context state['question'] = {state['question']}")
        docs = faissVectorDB.search_similar_documents(query=state['question'], k=5)
        print(f"### search_result = {docs}")

        state['context'] = docs # state['context'] = combine_documents(docs)
        return state

    def generate_response(state: AgentState) -> AgentState:        
        prompt = CODE_ASSIST_TASK_PROMPT.format(REFERENCE_CODE=state['context'], TASK=state['question'], CURRENT_CODE='') 
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

# text_to_sql 체인 생성
def create_text_to_sql_chain():
    """
    text를 받아서 sql을 만들어줌
    """
    faissVectorDB = FaissVectorDB()
    faissVectorDB.read_index(index_name="cg_text_to_sql")
    
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        print(f"------------------------ get_context state['question'] = {state['question']}")
        docs = faissVectorDB.search_similar_documents(query=state['question'], k=5)
        print(f"### search_result = {docs}")

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
    
    # prompt_chain = (
    #     SQL_QUERY_PROMPT | get_llm_model().with_config(callbacks=[CallbackHandler()]) | StrOutputParser()
    # )
    # return prompt_chain
    
    return chain

def create_summary_chain():
    """
    chunk를 받아서 summary를 만들어줌
    """
    prompt_chain = (
        CODE_SUMMARY_GENERATE_PROMPT | get_llm_model().with_config(callbacks=[CallbackHandler()])
    )
    return prompt_chain


# openai 체인 생성
def create_openai_chain():
    return ChatOpenAI(model="gpt-3.5-turbo-0125")

# anthropic 체인 생성
def create_anthropic_chain():
    return ChatAnthropic(model="claude-3-haiku-20240307")

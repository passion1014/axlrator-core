import json
import re
from dotenv import load_dotenv
from typing import TypedDict
from app.db_model.data_repository import ChunkedDataRepository
from app.db_model.database import SessionLocal
from app.prompts.code_prompt import CODE_ASSIST_TASK_PROMPT, CODE_SUMMARY_GENERATE_PROMPT
from app.prompts.sql_prompt import SQL_QUERY_PROMPT
from langgraph.graph import StateGraph, END
from app.prompts.term_conversion_prompt import TERM_CONVERSION_PROMPT
from app.utils import get_llm_model
from app.vectordb.faiss_vectordb import FaissVectorDB
from .config import setup_logging
from langfuse.callback import CallbackHandler
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
    session = SessionLocal()
    
    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_code_assist")
    # faissVectorDB.read_index()
    
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        print(f" ------------------------ get_context state['question'] = {state['question']}")
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
    session = SessionLocal()

    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_text_to_sql")
    # faissVectorDB.read_index()
    
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
    
    return chain



# 용어변환 체인 생성
def create_term_conversion_chain():
    """
    용어를 변환하기 위한 체인을 생성합니다
    """
    session = SessionLocal()

    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_terms") 
    # faissVectorDB.read_index()
    
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def get_context(state: AgentState) -> AgentState:
        docs = faissVectorDB.search_similar_documents(query=state['question'], k=5)
        print(f"### search_result = {docs}")

        # content 값만 추출하여 콤마로 구분된 문자열 생성
        context_string = ", ".join([doc['content'] for doc in docs if doc and 'content' in doc])
        print(f"### context_string = {context_string}")

        state['context'] = context_string
        return state

    def fetch_rdb_data(state: AgentState) -> AgentState:
        """
        RDB에서 데이터를 조회하여 state에 추가합니다.
        """
        try:
            chunkedDataRepository = ChunkedDataRepository(session=session)
            rdb_contexts = chunkedDataRepository.get_chunked_data_by_content(data_type='terms', content=state['question'])
            print(f"### get_chunked_data_by_content result = {rdb_contexts}")
            
        except Exception as e:
            print(f"### Error fetching RDB data: {e}")
            state['context'] += ", Error fetching RDB data"

        return state

    def generate_response(state: AgentState) -> AgentState:
        prompt = TERM_CONVERSION_PROMPT.format(korean_term=state['question'], related_info=state['context'])
        response = model.invoke(prompt)
        
        # AIMessage 객체에서 텍스트 콘텐츠 추출
        response_text = response.content if hasattr(response, 'content') else str(response)

        # <answer> 태그 안의 내용 추출 및 JSON 형태로 변환
        pattern = r"<answer>\s*snake_case:\s*(\w+)\s*camelCase:\s*(\w+)\s*</answer>"
        match = re.search(pattern, response_text)
        
        if match:
            parsed_response = {
                "snake_case": match.group(1),
                "camel_case": match.group(2)
            }
            state['response'] = json.dumps(parsed_response, ensure_ascii=False)
        else:
            state['response'] = json.dumps({"error": "No valid answer found"}, ensure_ascii=False)
        
        return state
    
    workflow = StateGraph(AgentState)

    # 노드 정의
    workflow.add_node("fetch_rdb_data", fetch_rdb_data)
    workflow.add_node("get_context", get_context)
    workflow.add_node("generate_response", generate_response)

    # 워크플로우 정의 
    workflow.set_entry_point("fetch_rdb_data")
    # workflow.add_edge("fetch_rdb_data", "generate_response", condition=lambda state: bool(state.get('context')))
    # workflow.add_edge("fetch_rdb_data", "get_context", condition=lambda state: not bool(state.get('context')))
    workflow.add_edge("fetch_rdb_data", "get_context")
    workflow.add_edge("get_context", "generate_response")
    workflow.add_edge("generate_response", END)

    chain = workflow.compile()
    chain.with_config(callbacks=[CallbackHandler()])
    
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
def create_llm_chain():
    return get_llm_model().with_config(callbacks=[CallbackHandler()])

# anthropic 체인 생성
def create_anthropic_chain():
    return ChatAnthropic(model="claude-3-haiku-20240307")

# 테스트용
def sample_chain():
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def generate_response(state: AgentState) -> AgentState:
        prompt = TERM_CONVERSION_PROMPT.format(korean_term=state['question'], related_info=state['context'])
        response = model.invoke(prompt)
        state['response'] = str(response)
        return state
    
    workflow = StateGraph(AgentState)

    # 노드 정의
    workflow.add_node("generate_response", generate_response)

    # 워크플로우 정의 
    workflow.set_entry_point("generate_response")
    workflow.add_edge("generate_response", END)

    chain = workflow.compile()
    chain.with_config(callbacks=[CallbackHandler()])
    
    return chain
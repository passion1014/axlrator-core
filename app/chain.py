import os
from dotenv import load_dotenv
from typing import List, Tuple, TypedDict
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langserve.pydantic_v1 import BaseModel, Field
from app.prompts.code_prompt import CODE_SUMMARY_GENERATE_PROMPT
from app.prompts.sql_prompt import SQL_QUERY_PROMPT
from langgraph.graph import StateGraph, END
from langchain_community.vectorstores import FAISS
from app.prompts.prompts import MERGE_QUESTION_PROMPT, ANSWER_PROMPT
from app.utils import combine_documents, merge_chat_history, get_embedding_model, get_llm_model
from .config import setup_logging
from langfuse.callback import CallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic

# .env 파일 로드
load_dotenv()

logger = setup_logging()

# FAISS 인덱스 경로 설정
vector_index = os.getenv("VECTOR_DATABASE_INDEX")
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), f'../data/vector/{vector_index}')


class ChatHistory(BaseModel):
    chat_history: List[Tuple[str, str]] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "question"}},
    )
    question: str


class AgentState(TypedDict):
    chat_history: List[Tuple[str, str]]
    question: str
    context: str
    response: str


def load_vector_database():
    '''
    Retriever를 반환하는 벡터 데이터베이스 로드 함수
    '''
    embeddings = get_embedding_model()
    
    try:
        db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        logger.info(f"----- FAISS index loaded from: {FAISS_INDEX_PATH}")
        
    except ValueError as e:
        logger.error(f"Error loading FAISS index: {e}")
        db = FAISS.load_local(FAISS_INDEX_PATH, allow_dangerous_deserialization=True)
        db.embeddings = embeddings

    retriever = db.as_retriever(search_kwargs={"k": 1})    
    logger.info(f"----- Number of items in FAISS index: {len(db.index_to_docstore_id)}")
    
    return retriever



def create_rag_chain():
    # retriever 선언
    retriever = load_vector_database()
    
    # 모델 선언
    model = get_llm_model()

    def get_context(state: AgentState) -> AgentState:
        chat_history = merge_chat_history(state['chat_history'])
        standalone_question_prompt = MERGE_QUESTION_PROMPT.format(
            chat_history=chat_history, question=state['question']
        )
        standalone_question_response = model.invoke(standalone_question_prompt)
        standalone_question = standalone_question_response.content if isinstance(standalone_question_response, AIMessage) else str(standalone_question_response)
        docs = retriever.get_relevant_documents(standalone_question)
        state['context'] = combine_documents(docs)
        return state

    def generate_response(state: AgentState) -> AgentState:        
        prompt = ANSWER_PROMPT.format(context=state['context'], question=state['question'])
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
    chain.with_types(input_type=ChatHistory).with_config(callbacks=[CallbackHandler()])
    
    return chain

# text_to_sql 체인 생성
def create_text_to_sql_chain():
    """
    text를 받아서 sql을 만들어줌
    """
    prompt_chain = (
        SQL_QUERY_PROMPT | get_llm_model().with_config(callbacks=[CallbackHandler()]) | StrOutputParser()
    )
    return prompt_chain

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

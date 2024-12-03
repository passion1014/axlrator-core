from app.chain_graph.agent_state import AgentState
from app.db_model.data_repository import ChunkedDataRepository
from app.db_model.database import SessionLocal
from app.process.compound_word_splitter import CompoundWordSplitter
from app.prompts.term_conversion_prompt import TERM_CONVERSION_PROMPT
from app.utils import get_llm_model
from app.vectordb.faiss_vectordb import FaissVectorDB


from langfuse.callback import CallbackHandler
from langgraph.graph import END, StateGraph


import json
import re


def create_term_conversion_chain():
    """
    용어를 변환하기 위한 체인을 생성합니다
    """
    session = SessionLocal()
    faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_terms")
    
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])
    

    def get_context(state: AgentState) -> AgentState:
        docs = faissVectorDB.search_similar_documents(query=state['question'], k=5)
        print(f"### [create_term_conversion_chain] search_result = {docs}")

        # content 값만 추출하여 콤마로 구분된 문자열 생성
        context_string = ", ".join([doc['content'] for doc in docs if doc and 'content' in doc])
        print(f"### [create_term_conversion_chain] context_string = {context_string}")

        state['context'] = context_string
        return state

    def get_db_data(state: AgentState) -> AgentState:
        """
        RDB에서 데이터를 조회하여 state에 추가합니다.
        """
        try:
            chunkedDataRepository = ChunkedDataRepository(session=session)
            rdb_contexts = chunkedDataRepository.get_chunked_data_by_content(data_type='terms', content=state['question'])
            print(f"### get_chunked_data_by_content result = {rdb_contexts}")
            
            # content 컬럼 값만 추출하여 콤마로 구분된 문자열 생성
            content_values = [data.content for data in rdb_contexts if hasattr(data, 'content')]
            content_string = ", ".join(content_values)
            print(f"### Extracted content values: {content_string}")

            state['context'] = content_string
        except Exception as e:
            print(f"### Error fetching RDB data: {e}")

        return state

    def generate_response(state: AgentState) -> AgentState:
        prompt = TERM_CONVERSION_PROMPT.format(korean_term=state['question'], related_info=state['context'])
        response = model.invoke(prompt)

        # AIMessage 객체에서 텍스트 콘텐츠 추출
        response_text = response.content if hasattr(response, 'content') else str(response)

        # <answer> 태그 안의 내용 추출 및 JSON 형태로 변환
        # pattern = r"<answer>\s*snake_case:\s*(\w+)\s*camelCase:\s*(\w+)\s*</answer>"
        pattern = r"<answer>\s*snake_case:\s*\[?([\w_]+)\]?\s*camel_case:\s*\[?([\w_]+)\]?\s*</answer>"
        match = re.search(pattern, response_text, re.DOTALL)
        
        print(f"        ####### response_text={response_text}")
        print(f"        ####### matchz={match}")

        if match:
            state['response'] = f"{state['question']} = {match.group(1)}({match.group(2)})"
        else:
            state['response'] = "None"
        return state

    workflow = StateGraph(AgentState)

    # 조건

    # 노드 정의
    workflow.add_node("get_db_data", get_db_data)
    workflow.add_node("get_context", get_context)
    workflow.add_node("generate_response", generate_response)

    # 워크플로우 정의 
    workflow.set_entry_point("get_db_data")
    workflow.add_edge("get_db_data", "get_context") 
    workflow.add_edge("get_context", "generate_response")
    workflow.add_edge("generate_response", END)

    chain = workflow.compile()
    chain.with_config(callbacks=[CallbackHandler()])

    return chain
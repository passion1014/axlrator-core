from axlrator_core.chain_graph.agent_state import AgentState
from axlrator_core.common.utils import get_llm_model
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from langgraph.graph import END, StateGraph


# def create_term_conversion_chain():
#     """
#     용어를 변환하기 위한 체인을 생성합니다
#     """
#     session = get_async_session()
#     faissVectorDB = FaissVectorDB(db_session=session, index_name="cg_terms")
#     langfuse = Langfuse()
    
#     # 모델 선언
#     model = get_llm_model().with_config(callbacks=[CallbackHandler()])
    

#     def get_context(state: AgentState) -> AgentState:
#         docs = faissVectorDB.search_similar_documents(query=state['question'], k=5)

#         # content 값만 추출하여 콤마로 구분된 문자열 생성
#         context_string = ", ".join([doc['content'] for doc in docs if doc and 'content' in doc])

#         state['context'] = context_string
#         return state

#     def get_db_data(state: AgentState) -> AgentState:
#         """
#         RDB에서 데이터를 조회하여 state에 추가합니다.
#         """
#         try:
#             chunkedDataRepository = ChunkedDataRepository(session=session)
#             rdb_contexts = chunkedDataRepository.get_chunked_data_by_content(data_type='terms', content=state['question'])
            
#             # content 컬럼 값만 추출하여 콤마로 구분된 문자열 생성
#             content_values = [data.content for data in rdb_contexts if hasattr(data, 'content')]
#             content_string = ", ".join(content_values)

#             state['context'] = content_string
#         except Exception as e:
#             print(f"### Error fetching RDB data: {e}")

#         return state

#     def generate_response(state: AgentState) -> AgentState:
#         langfuse_prompt = langfuse.get_prompt("TERM_CONVERSION_PROMPT1", version=1)
#         prompt = langfuse_prompt.compile(korean_term=state['question'], related_info=state['context'])
#         response = model.invoke(prompt)

#         # AIMessage 객체에서 텍스트 콘텐츠 추출
#         response_text = response.content if hasattr(response, 'content') else str(response)

#         # <answer> 태그 안의 내용 추출 및 JSON 형태로 변환
#         pattern = r"<answer>\s*snake_case:\s*\[?([\w_]+)\]?\s*camel_case:\s*\[?([\w_]+)\]?\s*</answer>"
#         match = re.search(pattern, response_text, re.DOTALL)

#         if match:
#             state['response'] = f"{state['question']} = {match.group(1)}({match.group(2)})"
#         else:
#             state['response'] = "None"
#         return state

#     workflow = StateGraph(AgentState)

#     # 조건

#     # 노드 정의
#     workflow.add_node("get_db_data", get_db_data)
#     workflow.add_node("get_context", get_context)
#     workflow.add_node("generate_response", generate_response)

#     # 워크플로우 정의 
#     workflow.set_entry_point("get_db_data")
#     workflow.add_edge("get_db_data", "get_context") 
#     workflow.add_edge("get_context", "generate_response")
#     workflow.add_edge("generate_response", END)

#     chain = workflow.compile()
#     chain.with_config(callbacks=[CallbackHandler()])

#     return chain


def create_term_conversion_chain():
    """
    용어를 변환하기 위한 체인을 생성합니다
    """
    langfuse = Langfuse()
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])
    
    def generate_response(state: AgentState) -> AgentState:
        langfuse_prompt = langfuse.get_prompt("TERM_CONVERSION_PROMPT2")
        prompt = langfuse_prompt.compile(request=state['question'], context=state['context'])
        response = model.invoke(prompt)

        # AIMessage 객체에서 텍스트 콘텐츠 추출
        state['response'] = response.content if hasattr(response, 'content') else str(response)

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

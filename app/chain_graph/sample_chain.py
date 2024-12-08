# 테스트용
from app.chain_graph.agent_state import AgentState
from app.prompts.term_conversion_prompt import TERM_CONVERSION_PROMPT1
from app.utils import get_llm_model


from langfuse.callback import CallbackHandler
from langgraph.graph import END, StateGraph


def sample_chain():
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])

    def generate_response(state: AgentState) -> AgentState:
        prompt = TERM_CONVERSION_PROMPT1.format(korean_term=state['question'], related_info=state['context'])
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
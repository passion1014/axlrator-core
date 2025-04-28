# 테스트용
from axlrator_core.chain_graph.agent_state import AgentState
from axlrator_core.utils import get_llm_model
from langfuse.callback import CallbackHandler
from langgraph.graph import END, StateGraph
from langfuse import Langfuse

def sample_chain():
    # 모델 선언
    model = get_llm_model().with_config(callbacks=[CallbackHandler()])
    langfuse = Langfuse()

    def generate_response(state: AgentState) -> AgentState:
        langfuse_prompt = langfuse.get_prompt("TERM_CONVERSION_PROMPT1", version=1)
        prompt = langfuse_prompt.compile(korean_term=state['question'], related_info=state['context'])

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
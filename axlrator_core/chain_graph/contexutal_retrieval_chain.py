from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langfuse import Langfuse
# from langfuse.callback import CallbackHandler
from langchain_core.prompts import PromptTemplate
from axlrator_core.utils import get_llm_model

class CreateSummaryState(TypedDict):
    prompt: str
    content: str
    response: str


def chain_create_summary():
    """
    chunk를 받아서 summary를 만들어줌
    """
    # callback_handler = CallbackHandler()

    def _get_summary_prompt(state: CreateSummaryState) -> CreateSummaryState:
        langfuse_prompt = Langfuse().get_prompt("CODE_SUMMARY_GENERATE_PROMPT")
        state['prompt'] = langfuse_prompt.compile(
            CODE_CHUNK=state.get('content', '')
        )
        return state

    def _generate_summary(state: CreateSummaryState) -> CreateSummaryState:
        result = get_llm_model().invoke(state['prompt']) 
        state['response'] = result.content
        return state
    
    graph = StateGraph(CreateSummaryState)
    graph.add_node("get_summary_prompt", _get_summary_prompt)
    graph.add_node("generate_summary", _generate_summary)
    
    graph.set_entry_point("get_summary_prompt")
    graph.add_edge("get_summary_prompt", "generate_summary")
    graph.add_edge("generate_summary", END)

    return graph.compile()


# 설계
'''
node1 = 데이터조회(Semantic, BM25) + 랭크퓨전(RRF유사)
node2 = re-ranker
node3 = generation
'''

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from axlrator_core.utils import get_llm_model
from langfuse.callback import CallbackHandler
from langfuse import Langfuse
from langchain_core.runnables import Runnable

class UiConvertState(TypedDict):
    prompt: str
    from_code: str
    to_code: str # 변환후 결과 코드
    from_type: str
    to_type: str

class UiConvertChain:
    def __init__(self, session, index_name:str="cg_code_assist"):
        self.index_name = index_name
        self.db_session = session
        # self.es_bm25 = ElasticsearchBM25(index_name=index_name)
        self.model = get_llm_model().with_config(callbacks=[CallbackHandler()])
        self.langfuse = Langfuse()


    def chain_convert(self) -> Runnable[UiConvertState, UiConvertState]:
        ''' 화면 전환
        '''
        def _prompt_node(state: UiConvertState) -> UiConvertState:

            from_type = state.get('from_type', '')
            to_type = state.get('to_type', '')
            
            langfuse_prompt = self.langfuse.get_prompt("AXL_UI_CONVERSION_01")
            # if (request_type == "01") : # class 주석
            #     langfuse_prompt = self.langfuse.get_prompt("AXL_CODE_AUTOCOMPLETION_CLASS")
            # else : # 기타
            #     langfuse_prompt = self.langfuse.get_prompt("AXL_CODE_AUTOCOMPLETION")

            state['prompt'] = langfuse_prompt.compile(
                from_code=state['from_code']
            )
            
            return state

        def _generate_node(state: UiConvertState) -> UiConvertState:
            prompt = state['prompt']
            result = self.model.invoke(prompt)  # 동기 호출로 변경
            state['to_code'] = result.content
            return state
        
        
        graph = StateGraph(UiConvertState)
        graph.add_node("prompt_node", _prompt_node)
        graph.add_node("generate_node", _generate_node) 
        
        graph.set_entry_point("prompt_node")
        graph.add_edge("prompt_node", "generate_node")
        graph.add_edge("generate_node", END)
        
        chain = graph.compile()
        
        return chain
from axlrator_core.utils import get_llm_model

from langfuse import Langfuse
from langfuse.callback import CallbackHandler
from langchain_core.prompts import PromptTemplate


def create_summary_chain():
    """
    chunk를 받아서 summary를 만들어줌
    """
    langfuse = Langfuse()
    langfuse_prompt = langfuse.get_prompt("AUTO_CODE_TASK_PROMPT", version=1)
    
    CODE_SUMMARY_GENERATE_PROMPT = PromptTemplate.from_template(
        langfuse_prompt.get_langchain_prompt(),
        metadata={"langfuse_prompt": langfuse_prompt},
    )
    
    prompt_chain = (
        CODE_SUMMARY_GENERATE_PROMPT | get_llm_model().with_config(callbacks=[CallbackHandler()])
    )
    return prompt_chain


# 설계
'''
node1 = 데이터조회(Semantic, BM25) + 랭크퓨전(RRF유사)
node2 = re-ranker
node3 = generation
'''

from app.prompts.code_prompt import CODE_SUMMARY_GENERATE_PROMPT
from app.utils import get_llm_model


from langfuse.callback import CallbackHandler


def create_summary_chain():
    """
    chunk를 받아서 summary를 만들어줌
    """
    prompt_chain = (
        CODE_SUMMARY_GENERATE_PROMPT | get_llm_model().with_config(callbacks=[CallbackHandler()])
    )
    return prompt_chain
import json
from axlrator_core.chain_graph.contexutal_retrieval_chain import chain_create_summary
from axlrator_core.formatter.code_formatter import parse_augmented_chunk
from langfuse.callback import CallbackHandler

def generate_code_context(chunk_content:str):
    """chunk를 받아서 LLM을 사용하여 summary를 만듬"""
    callback_handler = CallbackHandler()

    # create_summary_chain 호출
    summary_chain = chain_create_summary()
    
    # 요약 생성을 위한 프롬프트 입력
    inputs = {
        "content": chunk_content
    }
    
    # message = summary_chain.invoke(inputs, config={"callbacks": [callback_handler]})
    # langfuse 서버 3.x 대로 올리고 로그 트레이싱 작업 추가하기
    message = summary_chain.invoke(inputs)

    return message['result']

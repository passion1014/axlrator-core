

import json
from axlrator_core.chain_graph.contexutal_retrieval_chain import create_summary_chain
from axlrator_core.formatter.code_formatter import parse_augmented_chunk


def  generate_code_context(chunk_content:str):
    """chunk를 받아서 LLM을 사용하여 summary를 만듬"""

    # create_summary_chain 호출
    summary_chain = create_summary_chain()
    
    # 요약 생성을 위한 프롬프트 입력
    inputs = {
        "SOURCE_CODE": chunk_content
    }
    
    summary_ai_message = summary_chain.invoke(inputs) # result = AIMessage 타입
    parsed_ai_message = parse_augmented_chunk(summary_ai_message.content)
    parsed_json_message = json.loads(parsed_ai_message.model_dump_json())  # Pydantic v2의 기본 json 메서드를 사용해 JSON으로 변환
    result = json.dumps(parsed_json_message, ensure_ascii=False, indent=4)

    return result

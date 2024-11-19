

import json
from app.chain import create_summary_chain
from app.formatter.code_formatter import parse_augmented_chunk


def  generate_code_context(chunk_content:str):
    """chunk를 받아서 LLM을 사용하여 summary를 만듬"""

    # check - Dao클래스는 패스 (건설공제 기준)
    # if isinstance(chunk, JavaChunkMeta):
    #     chunk.
    
    # create_summary_chain 호출
    summary_chain = create_summary_chain()
    
    # 요약 생성을 위한 프롬프트 입력
    inputs = {
        "CODE_CHUNK": chunk_content
    }
    
    # summary_chain 실행
    try:
        summary_ai_message = summary_chain.invoke(inputs) # result = AIMessage 타입
        parsed_ai_message = parse_augmented_chunk(summary_ai_message.content)
        parsed_json_message = json.loads(parsed_ai_message.model_dump_json())  # Pydantic v2의 기본 json 메서드를 사용해 JSON으로 변환
        result = json.dumps(parsed_json_message, ensure_ascii=False, indent=4)

    except Exception as e:
        result = ""
        print(f"에러발생-summary chain execution: {e}")
    
    return result

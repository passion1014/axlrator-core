from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from axlrator_core.config import TEMPLATE_DIR, setup_logging
from pydantic import BaseModel

from axlrator_core.chain_graph.term_conversion_chain import create_term_conversion_chain
from axlrator_core.process.compound_word_splitter import CompoundWordSplitter
from axlrator_core.common.utils import remove_markdown_code_block


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)



# 질문을 위한 요청 모델 정의
class SQLRequest(BaseModel):
    question: str

class CodeRequest(BaseModel):
    question: str


# 용어변환 페이지 
@router.get("/terms", response_class=HTMLResponse)
async def ui_code(request: Request):
    return templates.TemplateResponse("completion/termsconversion.html", {"request": request, "message": "용어변환"})



# code assist 요청 엔드포인트
@router.post("/api/conv")
async def term_conversion_endpoint(request: CodeRequest):
    result = {}
    input_text = request.question
    
    # 입력된 text의 한글 단어를 추출하여 용어집을 만든다.
    extract_korean_words = CompoundWordSplitter.extract_korean_words(input_text)

    # 입력값이 한글 1단어만 들어왔을 경우 전환된 값을 그대로 출력
    if len(extract_korean_words) == 1 and input_text == extract_korean_words[0]:
        conv_result = CompoundWordSplitter.conv_compound_word(input_text)
        if conv_result and len(conv_result) > 0:
            # return {"response": conv_result}
            result["context"] = conv_result
            return result

    # 용어집을 생성
    split_words = []
    for word in extract_korean_words:
        split_result = CompoundWordSplitter.split_compound_word(word)
        if split_result:
            split_words.append(split_result[0])
    
    merge_meta_voca = CompoundWordSplitter.merge_translations(split_words)
    result["context"] = merge_meta_voca
    
    # LLM 호출
    state = {
        "question": input_text, 
        "context": ", ".join([f"{key}={value}" for key, value in merge_meta_voca.items()])
    }
    llm_response = create_term_conversion_chain().invoke(state)
    
    if llm_response["response"] and not isinstance(llm_response["response"], list):
        result["response"] = remove_markdown_code_block(llm_response["response"])
    else:
        result = llm_response
    
    return result

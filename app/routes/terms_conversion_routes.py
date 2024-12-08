from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, setup_logging
from pydantic import BaseModel

from app.chain_graph.term_conversion_chain import create_term_conversion_chain, create_term_conversion_chain2
from app.process.compound_word_splitter import CompoundWordSplitter


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
    input_text = request.question
    
    # 입력된 text의 한글 단어를 추출하여 용어집을 만든다.
    extract_korean_words = CompoundWordSplitter.extract_korean_words(input_text)

    # 입력값이 한글 1단어만 들어왔을 경우 전환된 값을 그대로 출력
    if len(extract_korean_words) == 1 and input_text == extract_korean_words[0]:
        split_result = CompoundWordSplitter.conv_compound_word(input_text)
        if split_result and len(split_result) > 0:
            return {"response": split_result}

    # 용어집을 생성
    split_words = []
    for word in extract_korean_words:
        result = CompoundWordSplitter.split_compound_word(word)
        if result:
            split_words.append(result[0])
    
    merge_meta_voca = CompoundWordSplitter.merge_translations(split_words)
    context = ", ".join([f"{key}={value}" for key, value in merge_meta_voca.items()])
    
    # LLM 호출
    chain = create_term_conversion_chain2()
    state = {
        "question": input_text, 
        "context": context
    }
    
    response = chain.invoke(state)
    
    if response["response"] and not isinstance(response["response"], list):
        response = {"response": [response["response"]]}
    
    return response

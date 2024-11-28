from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, setup_logging
from pydantic import BaseModel

from app.chain import create_term_conversion_chain
from app.process.compound_word_splitter import CompoundWordSplitter


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/code", response_class=HTMLResponse)
async def ui_code(request: Request):
    return templates.TemplateResponse("sample/code.html", {"request": request, "message": "코드 자동 생성 (Test버전)"})



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
    split_result = CompoundWordSplitter.split_compound_word(request.question)
    
    # split_result 값이 있으면 return
    if split_result and len(split_result) > 0:
        return {"response": split_result}
    
    chain = create_term_conversion_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}

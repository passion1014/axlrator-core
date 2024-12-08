# app/routes/upload_routes.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import BaseModel
from app.chain_graph.sample_chain import sample_chain
from app.config import TEMPLATE_DIR, setup_logging

logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)


class SampleRequest(BaseModel):
    indexname: str
    question: str


@router.get("/code", response_class=HTMLResponse)
async def ui_code(request: Request):
    return templates.TemplateResponse("sample/code.html", {"request": request, "message": "코드 자동 생성 (Test버전)"})


# code assist 요청 엔드포인트
@router.post("/api/sample")
async def sample_endpoint(request: SampleRequest):
    chain = sample_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}

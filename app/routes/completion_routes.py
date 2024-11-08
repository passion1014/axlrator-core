from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model import database_models
from app.db_model.database import get_db
from requests import Session

logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/code", response_class=HTMLResponse)
async def ui_code(request: Request):
    return templates.TemplateResponse("sample/code.html", {"request": request, "message": "코드 자동 생성 (Test버전)"})



@router.get("/terms", response_class=HTMLResponse)
async def ui_terms(request: Request):
    return templates.TemplateResponse("completion/terms.html", {"request": request, "message": "용어변환"})

@router.get("/api/terms")
async def get_terms(db: Session = Depends(get_db)):
    

    results = {
        "보증번호": ["aslkdfj", "asldfj", "sadkfjsdflk"],
        "부동산담보대출금액": ["qwe123", "zxc456", "vbn789"]
    }
    return [{"title": title, "items": items} for title, items in results.items()]

    
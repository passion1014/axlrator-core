from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import Session
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model import database_models
from app.db_model.database import get_db


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/list", response_class=HTMLResponse)
async def ui_faiss_list(request: Request):
    return templates.TemplateResponse("faissList.html", {"request": request, "message": "건설공제 파일 업로드 (Test버전)"})


# FAISS Info 데이터를 가져오는 엔드포인트
@router.get("/api/faiss_info")
async def get_faiss_info(db: Session = Depends(get_db)):
    faiss_info_list = db.query(database_models.FaissInfo).all()
    return [{"id": info.id,
            "index_name": info.index_name,
            "index_desc": info.index_desc,
            "index_file_path": info.index_file_path,
            "modified_at": info.modified_at,
            "created_at": info.created_at,
            "modified_by": info.modified_by,
            "created_by": info.created_by} for info in faiss_info_list]

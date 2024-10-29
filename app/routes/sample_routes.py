# app/routes/upload_routes.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model.database import get_db
from app.vectordb.upload_vectordb import vector_upload
from fastapi import Form


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)

@router.get("/code", response_class=HTMLResponse)
async def ui_code(request: Request):
    return templates.TemplateResponse("sample/code.html", {"request": request, "message": "코드 자동 생성 (Test버전)"})


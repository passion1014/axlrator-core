# app/routes/upload_routes.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import Session
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model import database_models
from app.db_model.database import get_db
from app.vectordb.upload_vectordb import vector_upload
from fastapi import Form
import json


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)


@router.get("/uploadData", response_class=HTMLResponse)
async def display_upload_page(request: Request):
    return templates.TemplateResponse("uploadData.html", {"request": request, "message": "건설공제 파일 업로드 (Test버전)"})


@router.post("/api/uploadFile")
async def upload_file(files: list[UploadFile] = File(...)):
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    
    # 파일 저장 로직
    for file in files:
        try:
            file_location = upload_dir / file.filename
            with file_location.open("wb") as f:
                f.write(await file.read())
            saved_files.append(str(file_location))
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {file.filename}")

    # 벡터 업로드 로직
    if saved_files:
        try:
            file_path = saved_files[0]
            index_name = Path(file_path).stem
            vector_upload(file_path, index_name)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return {"filenames": saved_files}


@router.post("/api/uploadFile")
async def upload_file(files: list[UploadFile] = File(...), selectedIds: str = Form(...)):
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    
    # 파일 저장 로직
    for file in files:
        try:
            file_location = upload_dir / file.filename
            with file_location.open("wb") as f:
                f.write(await file.read())
            saved_files.append(str(file_location))
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {file.filename}")

    # 선택된 인덱스 ID 파싱
    selected_ids = json.loads(selectedIds)

    # 벡터 업로드 로직
    if saved_files and selected_ids:
        try:
            file_path = saved_files[0]
            # selected_ids[0]을 사용하여 인덱스명으로 업로드 진행
            index_name = selected_ids[0]
            vector_upload(file_path, index_name)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return {"filenames": saved_files, "selectedIds": selected_ids}


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

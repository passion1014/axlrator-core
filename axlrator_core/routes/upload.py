# app/routes/upload_routes.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request, Form
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import Session
from axlrator_core.config import TEMPLATE_DIR, setup_logging
from axlrator_core.db_model import database_models
from axlrator_core.db_model.data_repository import FaissInfoRepository
from axlrator_core.db_model.database import get_async_session
from axlrator_core.process.content_chunker import file_chunk_and_save
from axlrator_core.process.vectorize_process import process_vectorize
from axlrator_core.vectordb.bm25_search import create_elasticsearch_bm25_index
import json


logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)


@router.get("/uploadData", response_class=HTMLResponse)
async def ui_upload_page(request: Request):
    return templates.TemplateResponse("uploadData.html", {"request": request, "message": "건설공제 파일 업로드 (Test버전)"})


@router.get("/faisslist", response_class=HTMLResponse)
async def ui_faiss_list(request: Request):
    return templates.TemplateResponse("faissList.html", {"request": request, "message": "건설공제 파일 업로드 (Test버전)"})


@router.post("/api/uploadFile")
async def upload_file(files: list[UploadFile] = File(...), selectedId: str = Form(...), session: Session = Depends(get_async_session)):
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    
    faissinfo_repository = FaissInfoRepository(session=session)

    # faiss_info 조회
    selected_id = json.loads(selectedId) # 선택된 인덱스 ID 파싱
    faiss_info = faissinfo_repository.get_faiss_by_id(faiss_info_id=selected_id)
    
    # 파일 저장 로직
    for file in files:
        # try:
            file_location = upload_dir / file.filename
            with file_location.open("wb") as f:
                f.write(await file.read())
            saved_files.append(str(file_location))
            
            # 파일 청킹 및 RDB 저장
            org_resrc, chunk_list = await file_chunk_and_save(str(file_location), session=session)

            # elasticsearch 저장
            create_elasticsearch_bm25_index(index_name=faiss_info.index_name, org_resrc=org_resrc, chunk_list=chunk_list)

            # 벡터처리 및 벡터DB에 저장
            await process_vectorize(collection_name=faiss_info.index_name, session=session, org_resrc=org_resrc)
            
        # except Exception as e:
        #     logger.error(f"Error saving file {file.filename}: {str(e)}")
        #     raise HTTPException(status_code=500, detail=f"Error saving file: {file.filename}")

    return {"filenames": saved_files, "selectedIds": selected_id}


# FAISS Info 데이터를 가져오는 엔드포인트
@router.get("/api/faiss_info")
async def get_faiss_info(db: Session = Depends(get_async_session)):
    faiss_info_list = db.query(database_models.FaissInfo).all()
    return [{"id": info.id
            , "index_name": info.index_name
            , "index_desc": info.index_desc
            , "index_file_path": info.index_file_path
            , "modified_at": info.modified_at
            , "created_at": info.created_at
            , "modified_by": info.modified_by
            , "created_by": info.created_by} for info in faiss_info_list]

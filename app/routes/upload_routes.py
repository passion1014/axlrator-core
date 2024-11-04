# app/routes/upload_routes.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from pathlib import Path

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from requests import Session
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model import database_models
from app.db_model.data_repository import FaissInfoRepository
from app.db_model.database import SessionLocal, get_db
from app.process.content_chunker import file_chunk_and_save
from fastapi import Form
import json

from app.process.vectorize_process import process_vectorize
from app.vectordb.faiss_vectordb import FaissVectorDB


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
async def upload_file(files: list[UploadFile] = File(...), selectedId: str = Form(...)):
    session = SessionLocal()
    
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []
    
    faissinfo_repository = FaissInfoRepository(session=session)
    
    # 파일 저장 로직
    for file in files:
        try:
            file_location = upload_dir / file.filename
            with file_location.open("wb") as f:
                f.write(await file.read())
            saved_files.append(str(file_location))
            print(f'### 처리된 파일 = {str(file_location)}')
            org_resrc, chunk_list = file_chunk_and_save(str(file_location), session=session)
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {file.filename}")

    # 선택된 인덱스 ID 파싱
    selected_id = json.loads(selectedId)
    
    # faiss_info 조회
    faiss_info = faissinfo_repository.get_faiss_info_by_id(faiss_info_id=selected_id)
    
    # faiss_vector_db = FaissVectorDB(db_session=session, index_name=index_name)
    # faiss_info = faiss_vector_db.psql_docstore.get_faiss_info()
    # if faiss_info is None:
    #     faiss_info = faiss_vector_db.psql_docstore.insert_faiss_info()
    #     print(f"# 기저장된 {index_name}의 FAISS 정보가 없습니다. 생성합니다.")

    # 벡터처리
    process_vectorize(index_name=faiss_info.index_name, session=session, org_resrc=org_resrc, faiss_info=faiss_info)


    # 벡터 업로드 로직
    # if saved_files and selected_ids:
    #     try:
    #         file_path = saved_files[0]
    #         # selected_ids[0]을 사용하여 인덱스명으로 업로드 진행
    #         index_name = selected_ids[0]
    #         vector_upload(file_path, index_name)
    #     except Exception as e:
    #         logger.error(f"Error processing file {file_path}: {str(e)}")
    #         raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return {"filenames": saved_files, "selectedIds": selected_id}


# FAISS Info 데이터를 가져오는 엔드포인트
@router.get("/api/faiss_info")
async def get_faiss_info(db: Session = Depends(get_db)):
    faiss_info_list = db.query(database_models.FaissInfo).all()
    return [{"id": info.id
            , "index_name": info.index_name
            , "index_desc": info.index_desc
            , "index_file_path": info.index_file_path
            , "modified_at": info.modified_at
            , "created_at": info.created_at
            , "modified_by": info.modified_by
            , "created_by": info.created_by} for info in faiss_info_list]

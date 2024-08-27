from http.client import HTTPException
from fastapi import FastAPI, File, Request, UploadFile
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langserve import add_routes
from app.config import setup_logging
from app.chain import create_chain
from langfuse.callback import CallbackHandler
from langchain_core.output_parsers import StrOutputParser

from app.prompts.sql_prompt import SQL_QUERY_PROMPT
from app.utils import get_llm_model
from app.vectordb.upload_vectordb import vector_upload
from .db_model.database import engine, SessionLocal
from .db_model import database_models


# ---------------------------------------
# 로깅 설정
# ---------------------------------------
logger = setup_logging()


# ---------------------------------------
# SQLAlchemy
# ---------------------------------------
# 데이터베이스 테이블 생성하기
database_models.Base.metadata.create_all(bind=engine)


# 종속성 만들기 : 요청 당 독립적인 데이터베이스 세션/연결이 필요하고 요청이 완료되면 닫음
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# ---------------------------------------
# FastAPI 앱 설정
# ---------------------------------------
app = FastAPI (
    title="Construction Guarantee Server",
    version="1.0",
    description="AI Server for Construction Guarantee Company",
)

# 랭퓨즈 저장을 위한 핸들러
langfuse_handler = CallbackHandler() # Langfuse CallbackHandler 초기화

# ---------------------------------------
# 체인 생성
# ---------------------------------------
rag_chain = create_chain().with_config(callbacks=[langfuse_handler])

prompt_chain = (
    SQL_QUERY_PROMPT | get_llm_model().with_config(callbacks=[langfuse_handler]) | StrOutputParser()
)

# 라우트 추가
add_routes(app, prompt_chain, path="/prompt", enable_feedback_endpoint=True)
add_routes(app, rag_chain, path="/rag", enable_feedback_endpoint=True)

add_routes(
    app,
    ChatOpenAI(model="gpt-3.5-turbo-0125"),
    path="/openai",
)
add_routes(
    app,
    ChatAnthropic(model="claude-3-haiku-20240307"),
    path="/anthropic",
)

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory="templates")

@app.get("/uploadData", response_class=HTMLResponse)
async def read_root(request: Request):
    # 템플릿을 렌더링하면서 데이터 전달
    return templates.TemplateResponse("index.html", {"request": request, "message": "Hello, FastAPI!"})
    

# 정적 파일 경로 설정
# app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# # CORS 설정 (필요 시)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 파일 업로드 처리 경로
@app.post("/api/uploadFile")
async def upload_file(files: list[UploadFile] = File(...)):
    upload_folder = Path("data/uploads")
    upload_folder.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        file_location = upload_folder / file.filename
        with open(file_location, "wb") as f:
            f.write(await file.read())
        saved_files.append(str(file_location))

    # 파일이 하나라고 가정하고 처리 (필요에 따라 여러 파일 처리 가능)
    if len(saved_files) > 0:
        file_path = saved_files[0]
        index_name = file_path.split("/")[-1].split(".")[0]  # 파일 이름을 인덱스 이름으로 사용

        # main 함수 호출
        try:
            vector_upload(file_path, index_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    return {"filenames": saved_files}



if __name__ == "__main__":
    import uvicorn
    # 서버 실행
    uvicorn.run(app, host="localhost", port=8000)

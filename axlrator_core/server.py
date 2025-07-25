import argparse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import warnings

import logging
# ---------------------------------------
# 파라미터 처리
# ---------------------------------------
parser = argparse.ArgumentParser(description="FastAPI 서버 실행 옵션")
parser.add_argument("--env", type=str, default=".env", help="Path to .env file") # 환경변수 파일 경로
parser.add_argument("--host", type=str, default="0.0.0.0", help="서버 호스트") # 서버 호스트 주소
parser.add_argument("--port", type=int, default=8000, help="서버 포트") # 서버 포트 번호
parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화") # 디버그 모드 설정
parser.add_argument("--reload", action="store_true") # 코드 변경시 자동 리로드
parser.add_argument("--cert-file", type=str, default=None) # SSL 인증서 파일
parser.add_argument("--key-file", type=str, default=None) # SSL 키 파일
args = parser.parse_args()
print(f"args = {args}")


# 환경변수 파일 로드
load_dotenv(dotenv_path=args.env, override=True)





import argparse
from pydantic import BaseModel
# LLM 모델 관련 import
from axlrator_core.utils import get_llm_model
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from axlrator_core.config import STATIC_DIR
from axlrator_core.process.reranker import AlfredReranker

# client service
from axlrator_core.routes import (
    code_assist,
    document_manual,
    open_webui,
    terms_conversion,
    ui_converter,
    upload,
    user_service,
    vector_db,
    view,
)


# admin service 
from axlrator_core.routes.admin import (
    faiss_vector,
    milvus_vector,
)

from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from langfuse.callback import CallbackHandler
from axlrator_core.db_model.database import get_async_session_ctx
import uvicorn

import warnings
warnings.simplefilter("always", UserWarning)# 항상 경고를 표시하도록 설정

import logging
logging.basicConfig(level=logging.INFO) # 로그설정



@asynccontextmanager
async def lifespan(webServerApp: FastAPI):
    """애플리케이션 시작/종료 시 실행될 코드"""
    global reranker
    
    # session_ctx = get_async_session_CTX()
    # async with session_ctx as session:
    #     await initialize_vector_dbs(session)
    #     try:
    #         yield
    #     finally:
    #         vectordb_clear()
    yield


# FastAPI 앱 설정
app = FastAPI(
    title="Alfred Server",
    version="1.0",
    description="AI Server for Construction Guarantee Company",
    lifespan=lifespan
)

app.add_middleware(
    SessionMiddleware,
    secret_key="cgcgcg",
    session_cookie="session_cookie",
    max_age=24 * 60 * 60  # 24시간
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 또는 특정 도메인만 허용할 수도 있음
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (OPTIONS 포함)
    allow_headers=["*"],  # 모든 요청 헤더 허용
)

# 정적 파일 경로 및 Jinja2 템플릿 설정
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 임의 타입 허용을 위한 Pydantic 설정 추가
class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


# ---------------------------------------
# 라우터 등록
# ---------------------------------------

# 웹 페이지
app.include_router(view.router, prefix="/view") # 화면용 라우터
app.include_router(open_webui.router, prefix="/aifred-oi") # 기본 라우터

# 관리자
app.include_router(faiss_vector.router, prefix="/admin/faiss-vector")
app.include_router(milvus_vector.router, prefix="/admin/milvus-vector")

# 사용자
app.include_router(user_service.router, prefix="/user")
app.include_router(upload.router, prefix="/upload")
app.include_router(vector_db.router, prefix="/faiss") # TODO admin.faiss로 옮겨야 함
app.include_router(terms_conversion.router, prefix="/termsconversion")
app.include_router(code_assist.router, prefix="/codeassist")
app.include_router(document_manual.router, prefix="/manual")
app.include_router(ui_converter.router, prefix="/uiconv") # UI 컨버터

print('''
 █████╗ ██╗  ██╗██╗     ██████╗  █████╗ ████████╗ ██████╗ ██████╗ 
██╔══██╗╚██╗██╔╝██║     ██╔══██╗██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
███████║ ╚███╔╝ ██║     ██████╔╝███████║   ██║   ██║   ██║██████╔╝
██╔══██║ ██╔██╗ ██║     ██╔══██╗██╔══██║   ██║   ██║   ██║██╔══██╗
██║  ██║██╔╝ ██╗███████╗██║  ██║██║  ██║   ██║   ╚██████╔╝██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═                                       
''')

# 체인 등록
# from langserve import add_routes
# code_assist_chain = CodeAssistChain(index_name="cg_code_assist")
# add_routes(webServerApp, get_llm_model().with_config(callbacks=[CallbackHandler()]), path="/llm", enable_feedback_endpoint=True)
# add_routes(webServerApp, create_text_to_sql_chain(), path="/sql", enable_feedback_endpoint=True)
# add_routes(webServerApp, code_assist_chain(type="01"), path="/autocode", enable_feedback_endpoint=True)
# add_routes(webServerApp, code_assist_chain(type="02"), path="/codeassist", enable_feedback_endpoint=True)
# add_routes(webServerApp, create_anthropic_chain(), path="/anthropic", enable_feedback_endpoint=True)
# add_routes(webServerApp, code_assist_chain.code_assist_chain(type="01"), path="/autocode", enable_feedback_endpoint=True)


# Stream 처리를 위한 서비스 등록

# ---------------------------------------
# SQLAlchemy 데이터베이스 설정 및 초기화
# ---------------------------------------
# def initialize_database():
#     database_models.Base.metadata.create_all(bind=engine)
# initialize_database()

# ---------------------------------------
# 애플리케이션 실행
# 로컬 : python -m app.server --env .env.test --port 8001 --debug debug
# ---------------------------------------
if __name__ == "__main__":
    print(f"Starting server on {args.host}:{args.port} (debug={args.debug})")
    uvicorn.run(app, 
                host=args.host, 
                port=args.port, 
                reload=args.debug,
                ssl_certfile=args.cert_file,  # 인증서 파일 추가
                ssl_keyfile=args.key_file,  # 키 파일 추가
                )
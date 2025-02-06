import argparse
from dotenv import load_dotenv

# ---------------------------------------
# 파라미터 처리
# ---------------------------------------
parser = argparse.ArgumentParser(description="FastAPI 서버 실행 옵션")
parser.add_argument("--env", type=str, default=".env", help="Path to .env file") # 값이 없을 경우 .env 기본 설정
parser.add_argument("--host", type=str, default="0.0.0.0", help="서버 호스트")
parser.add_argument("--port", type=int, default=8000, help="서버 포트")
parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
parser.add_argument("--cert-file", type=str, default=None)
parser.add_argument("--key-file", type=str, default=None)
args = parser.parse_args()

# .env 파일 로드
load_dotenv(dotenv_path=args.env, override=True)


import argparse
from pydantic import BaseModel
# from app.chain_graph.code_assist_chain import code_assist_chain 
from app.utils import get_llm_model
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.config import STATIC_DIR

from app.chain_graph.code_assist_chain import CodeAssistChain

from app.routes.view_routes import router as view_routes
from app.routes.upload_routes import router as upload_routes
from app.routes.faiss_routes import router as faiss_routes
from app.routes.sample_routes import router as sample_routes
from app.routes.terms_conversion_routes import router as terms_conversion_routes
from app.routes.code_assist_routes import router as code_assist_routes
from app.routes.user_service_routes import router as user_service_routes
from starlette.middleware.sessions import SessionMiddleware

from langfuse.callback import CallbackHandler
import uvicorn

import warnings
warnings.simplefilter("always", UserWarning)# 항상 경고를 표시하도록 설정

import logging
logging.basicConfig(level=logging.INFO) # 로그설정



# FastAPI 앱 설정
webServerApp = FastAPI(
    title="Construction Guarantee Server",
    version="1.0",
    description="AI Server for Construction Guarantee Company",
)

webServerApp.add_middleware(
    SessionMiddleware,
    secret_key="cgcgcg",
    session_cookie="session_cookie",
    max_age=24 * 60 * 60  # 24시간
)

# 정적 파일 경로 및 Jinja2 템플릿 설정
webServerApp.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 임의 타입 허용을 위한 Pydantic 설정 추가
class CustomBaseModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True


# ---------------------------------------
# 라우터 등록
# ---------------------------------------
code_assist_chain = CodeAssistChain(index_name="cg_code_assist")

# 웹 페이지
webServerApp.include_router(view_routes, prefix="/view") # 화면용 라우터


webServerApp.include_router(user_service_routes, prefix="/user") # 사용자 처리 라우터

webServerApp.include_router(upload_routes, prefix="/upload") # 업로드 라우터
webServerApp.include_router(faiss_routes, prefix="/faiss") # faiss 라우터
webServerApp.include_router(terms_conversion_routes, prefix="/termsconversion") # 용어변환을 위한 라우터
webServerApp.include_router(code_assist_routes, prefix="/codeassist") # 코드생성 위한 라우터
webServerApp.include_router(sample_routes, prefix="/sample") # <-- 해당 파일과 라우트들은 삭제 예정

# 아래는 삭제 - 플러그인용으로 따로 만들지 않고 도메인에 따라 관리
# webServerApp.include_router(eclipse_router, prefix="/plugin") # eclipse plugin 라우터 등록

# 체인 등록
# from langserve import add_routes
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
    uvicorn.run(webServerApp, 
                host=args.host, 
                port=args.port, 
                reload=args.debug,
                ssl_certfile=args.cert_file,  # 인증서 파일 추가
                ssl_keyfile=args.key_file  # 키 파일 추가                
                )



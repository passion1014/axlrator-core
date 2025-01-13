from dotenv import load_dotenv

load_dotenv(dotenv_path=".env") # .env, .env.testcase

import argparse
from pydantic import BaseModel
from app.chain_graph.rag_chain import create_rag_chain
# from app.chain_graph.code_assist_chain import code_assist_chain 
from app.utils import get_llm_model
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.config import STATIC_DIR

from app.routes.view_routes import router as view_routes
from app.routes.upload_routes import router as upload_routes
from app.routes.faiss_routes import router as faiss_routes
from app.routes.sample_routes import router as sample_routes
from app.routes.terms_conversion_routes import router as terms_conversion_routes
# from app.routes.code_assist_routes import router as code_assist_routes

from langfuse.callback import CallbackHandler
import uvicorn

# ---------------------------------------
# 파라미터 처리
# ---------------------------------------
parser = argparse.ArgumentParser(description="FastAPI 서버 실행 옵션")
parser.add_argument("--host", type=str, default="0.0.0.0", help="서버 호스트")
parser.add_argument("--port", type=int, default=8001, help="서버 포트")
parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
args = parser.parse_args()


# FastAPI 앱 설정
webServerApp = FastAPI(
    title="Construction Guarantee Server",
    version="1.0",
    description="AI Server for Construction Guarantee Company",
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
# 웹 페이지
webServerApp.include_router(view_routes, prefix="/view") # 화면용 라우터

webServerApp.include_router(upload_routes, prefix="/upload") # 업로드 라우터
webServerApp.include_router(faiss_routes, prefix="/faiss") # faiss 라우터
webServerApp.include_router(terms_conversion_routes, prefix="/termsconversion") # 용어변환을 위한 라우터
# webServerApp.include_router(code_assist_routes, prefix="/codeassist") # 코드생성 위한 라우터
webServerApp.include_router(sample_routes, prefix="/sample") # <-- 해당 파일과 라우트들은 삭제 예정

# 아래는 삭제 - 플러그인용으로 따로 만들지 않고 도메인에 따라 관리
# webServerApp.include_router(eclipse_router, prefix="/plugin") # eclipse plugin 라우터 등록

# 체인 등록
# from langserve import add_routes
# add_routes(webServerApp, create_text_to_sql_chain(), path="/sql", enable_feedback_endpoint=True)
# add_routes(webServerApp, create_rag_chain(), path="/rag", enable_feedback_endpoint=True)
# add_routes(webServerApp, code_assist_chain(type="01"), path="/autocode", enable_feedback_endpoint=True)
# add_routes(webServerApp, code_assist_chain(type="02"), path="/codeassist", enable_feedback_endpoint=True)
# add_routes(webServerApp, get_llm_model().with_config(callbacks=[CallbackHandler()]), path="/llm", enable_feedback_endpoint=True)
# add_routes(webServerApp, create_anthropic_chain(), path="/anthropic", enable_feedback_endpoint=True)


# Stream 처리를 위한 서비스 등록


# ---------------------------------------
# SQLAlchemy 데이터베이스 설정 및 초기화
# ---------------------------------------
# def initialize_database():
#     database_models.Base.metadata.create_all(bind=engine)
# initialize_database()

# ---------------------------------------
# 애플리케이션 실행
# ---------------------------------------
if __name__ == "__main__":
    print(f"Starting server on {args.host}:{args.port} (debug={args.debug})")
    uvicorn.run(webServerApp, host=args.host, port=args.port, reload=args.debug)



from fastapi.staticfiles import StaticFiles
from langserve import add_routes
from app.chain import create_anthropic_chain, create_openai_chain, create_rag_chain, create_text_to_sql_chain
from fastapi import FastAPI
from app.config import STATIC_DIR
from app.routes.upload_routes import router as upload_router

import uvicorn


# FastAPI 앱 설정
webServerApp = FastAPI(
    title="Construction Guarantee Server",
    version="1.0",
    description="AI Server for Construction Guarantee Company",
)
# 정적 파일 경로 및 Jinja2 템플릿 설정
webServerApp.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------
# 라우터 등록
# ---------------------------------------

# 업로드 라우터 등록
webServerApp.include_router(upload_router, prefix="/upload")

# 체인 등록
add_routes(webServerApp, create_text_to_sql_chain(), path="/prompt", enable_feedback_endpoint=True)
add_routes(webServerApp, create_rag_chain(), path="/rag", enable_feedback_endpoint=True)
add_routes(webServerApp, create_openai_chain(), path="/openai", enable_feedback_endpoint=True)
add_routes(webServerApp, create_anthropic_chain(), path="/anthropic", enable_feedback_endpoint=True)


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
    uvicorn.run(webServerApp, host="0.0.0.0", port=8000)
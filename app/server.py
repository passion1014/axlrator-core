import os
from fastapi.staticfiles import StaticFiles
from langserve import add_routes
from app.chain import create_anthropic_chain, create_llm_chain, create_rag_chain, create_term_conversion_chain, create_text_to_sql_chain
from fastapi import FastAPI
from app.config import STATIC_DIR
from app.routes.upload_routes import router as upload_routes
from app.routes.faiss_routes import router as faiss_routes
from app.routes.eclipse_routes import router as eclipse_router
from app.routes.sample_routes import router as sample_routes
from app.routes.terms_conversion_routes import router as terms_conversion_routes

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
webServerApp.include_router(upload_routes, prefix="/upload") # 업로드 라우터
webServerApp.include_router(faiss_routes, prefix="/faiss") # faiss 라우터
webServerApp.include_router(terms_conversion_routes, prefix="/termsconversion") # 용어변환을 위한 라우터
webServerApp.include_router(sample_routes, prefix="/sample") # <-- 해당 파일과 라우트들은 삭제 예정

# 아래는 삭제 - 플러그인용으로 따로 만들지 않고 도메인에 따라 관리
# webServerApp.include_router(eclipse_router, prefix="/plugin") # eclipse plugin 라우터 등록

# 체인 등록
# add_routes(webServerApp, create_text_to_sql_chain(), path="/sql", enable_feedback_endpoint=True)
add_routes(webServerApp, create_rag_chain(), path="/rag", enable_feedback_endpoint=True)
add_routes(webServerApp, create_llm_chain(), path="/llm", enable_feedback_endpoint=True)
# add_routes(webServerApp, create_anthropic_chain(), path="/anthropic", enable_feedback_endpoint=True)

# 플러그인 용

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



# create_text_to_sql_chain
#  - 사용자 질의
#  - 질의에 맞는 테이블 유사도 조회 -> 예) SAMPLE_simple.simple 조회 (건설공제 테이블 상세 정보)
#  - 조회된 테이블을 컨텍스트로 셋팅
#  - text to sql 호출


from fastapi import FastAPI
from langserve import add_routes
from app.config import setup_logging
from app.chain import create_chain
from langgraph.graph import END, StateGraph
from IPython.display import Image, display
from langfuse.callback import CallbackHandler
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
# 체인 생성
# ---------------------------------------
langfuse_handler = CallbackHandler() # Langfuse CallbackHandler 초기화
chain = create_chain().with_config(callbacks=[langfuse_handler])


# ---------------------------------------
# FastAPI 앱 설정
# ---------------------------------------
app = FastAPI (
    title="LangChain Server",
    version="1.0",
    description="Spin up a simple api server using Langchain's Runnable interfaces with LangGraph",
)
# 라우트 추가
add_routes(app, chain, path="/prompt", enable_feedback_endpoint=True)

    
if __name__ == "__main__":
    import uvicorn
    # 서버 실행
    uvicorn.run(app, host="localhost", port=8000)

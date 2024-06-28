from fastapi import FastAPI
from langserve import add_routes
from app.config import setup_logging
from app.chain import create_chain
# from langgraph.graph import END, StateGraph, MessagesState

# 로깅 설정
logger = setup_logging()

# FastAPI 앱 생성
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="Spin up a simple api server using Langchain's Runnable interfaces",
)

# 체인 생성
chain = create_chain()

# 라우트 추가
add_routes(app, chain, path="/prompt", enable_feedback_endpoint=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
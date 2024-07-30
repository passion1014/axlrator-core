from fastapi import FastAPI
from langserve import add_routes
from app.config import setup_logging
from app.chain import create_chain
from langgraph.graph import END, StateGraph
from IPython.display import Image, display
from langfuse.callback import CallbackHandler

# Langfuse CallbackHandler 초기화
langfuse_handler = CallbackHandler()

# 로깅 설정
logger = setup_logging()

# FastAPI 앱 생성
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="Spin up a simple api server using Langchain's Runnable interfaces with LangGraph",
)

# 체인 생성
chain = create_chain().with_config(callbacks=[langfuse_handler])

    
try:
    # 실행 가능한 객체의 그래프를 mermaid 형식의 PNG로 그려서 표시합니다. 
    display(
        # xray=True는 추가적인 세부 정보를 포함합니다.
        Image(chain.get_graph(xray=True).draw_mermaid_png())
    ) 
except:
    pass


# 라우트 추가
add_routes(app, chain, path="/prompt", enable_feedback_endpoint=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
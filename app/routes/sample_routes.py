# app/routes/upload_routes.py
import logging
from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from openai import BaseModel
from app.chain_graph.code_assist_chain import code_assist_chain
from app.chain_graph.rag_chain import create_rag_chain
from app.chain_graph.sample_chain import sample_chain
from app.config import TEMPLATE_DIR, setup_logging
from app.utils import get_llm_model

logger = setup_logging()
router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATE_DIR)


class SampleRequest(BaseModel):
    indexname: str
    question: str


@router.get("/code", response_class=HTMLResponse)
async def ui_code(request: Request):
    return templates.TemplateResponse("sample/code.html", {"request": request, "message": "코드 자동 생성 (Test버전)"})

@router.get("/chat", response_class=HTMLResponse)
async def ui_chat(request: Request):
    return templates.TemplateResponse("sample/chat.html", {"request": request, "message": "코드 자동 생성 (Test버전)"})


# code assist 요청 엔드포인트
@router.post("/api/sample")
async def sample_endpoint(request: SampleRequest):
    chain = sample_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}


# WebSocket 사용: 클라이언트에서 요청을 받고 워크플로우 실행
@router.websocket("/api/chat_ainvoke")
async def chat_websocket_ainvoke(websocket: WebSocket):
    await websocket.accept()
    try:
        chain = code_assist_chain(type="01")

        while True:
            # 클라이언트로부터 질문 받기
            # data = await websocket.receive_json()
            data = await websocket.receive_text()

            # 워크플로우 실행
            state = {"question": data}
            final_state = await chain.ainvoke(state)

            # 응답 스트리밍
            response_obj = final_state['response']
            
            # response_obj에서 content를 가져옴
            response = response_obj.content
            
            logging.info(f"Type of response_obj.content: {type(response_obj.content)}")

            await websocket.send_text(response)
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


# WebSocket 사용: 클라이언트에서 요청을 받고 워크플로우 실행
@router.websocket("/api/chat")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()

    chain = code_assist_chain(type="01")

    while True:
        # 클라이언트로부터 질문 받기
        data = await websocket.receive_text()

        # 워크플로우 실행
        state = {"question": data}
        
        async for output in chain.astream(state, stream_mode="updates"):
            # stream_mode="updates" yields dictionaries with output keyed by node name
            for key, value in output.items():
                print(f"Output from node '{key}':")
                print("---")
                print(f"value = {value['response'].content}")
                await websocket.send_text(value['response'].content)
                # print(value["messages"][-1].pretty_print())
            print("\n---\n")
        
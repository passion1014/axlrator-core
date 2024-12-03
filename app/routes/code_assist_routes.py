from fastapi import APIRouter
from openai import BaseModel
from app.chain_graph import code_assist_chain
from app.config import setup_logging

logger = setup_logging()
router = APIRouter()

class CodeAssistRequest(BaseModel):
    indexname: str
    question: str
    current_code: str


# code assist 요청 엔드포인트
@router.post("/api/code")
async def sample_endpoint(request: CodeAssistRequest):
    print(f"### request = {str(request)}")
    # chain = code_assist_chain()
    # state = {"question": request.question}
    # response = chain.invoke(state)
    # return {"response": response}
    pass

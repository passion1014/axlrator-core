# app/routes/upload_routes.py
from fastapi import APIRouter
from openai import BaseModel
from app.chain_graph.sample_chain import sample_chain
from app.config import setup_logging

logger = setup_logging()
router = APIRouter()

class SampleRequest(BaseModel):
    indexname: str
    question: str


# code assist 요청 엔드포인트
@router.post("/api/sample")
async def sample_endpoint(request: SampleRequest):
    chain = sample_chain()
    state = {"question": request.question}
    response = chain.invoke(state)
    
    return {"response": response}

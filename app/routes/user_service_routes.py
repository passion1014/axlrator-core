import json
from typing import List
from fastapi import APIRouter
from openai import BaseModel
from app.config import setup_logging
from app.db_model.data_repository import ChatHistoryRepository, UserInfoRepository
from app.db_model.database import SessionLocal
from app.db_model.database_models import ChatHistory, UserInfo

logger = setup_logging()
router = APIRouter()

class LoginInfo(BaseModel):
    user_id: str
    password: str

class CallHistoryInfo(BaseModel):
    user_id: str
    type_cd: str # code_assist:코드생성, text2sql:SQL생성


@router.post("/api/login")
async def login(request: LoginInfo):
    print(f"### {request}")

    user_service = UserService()
    
    # user_id로 조회
    user_info = user_service.get_user_by_id(request.user_id)
    if user_info:
        return {"response": user_info}
    
    # 없으면 저장
    user_info = UserInfo(user_id=request.user_id, password=request.password, email=f"{request.user_id}@temp.com")
    user_info = user_service.create_user(user_info)
    
    user_dict = {key: value for key, value in user_info.__dict__.items() if not key.startswith('_')} # 인스턴스를 딕셔너리로 변환
    user_json = json.dumps(user_dict, ensure_ascii=False) # 딕셔너리를 JSON으로 변환
    
    return {"response": user_json}


@router.post("/api/history")
async def history(request: CallHistoryInfo):
    print(f"### {request}")

    chatHistoryService = ChatHistoryService()
    list = chatHistoryService.get_chat_history_by_user_id(request.user_id)

    return {"response": list}



class UserService:
    def __init__(self):
        self.session = SessionLocal()
        self.user_info_repository = UserInfoRepository(self.session)

    def get_user_by_id(self, user_id: str):
        """
        주어진 사용자 ID로 사용자를 조회합니다.
        """
        return self.user_info_repository.get_user_by_id(user_id)

    def get_user_by_email(self, email: str):
        """
        주어진 이메일로 사용자를 조회합니다.
        """
        return self.user_info_repository.get_user_by_email(email)

    def get_all_users(self):
        """
        모든 사용자를 조회합니다.
        """
        return self.user_info_repository.get_all_users()

    def create_user(self, user_data: dict):
        """
        새로운 사용자를 생성합니다.
        """
        return self.user_info_repository.create_user(user_data)

    def update_user(self, user_id: str, user_data: dict):
        """
        주어진 사용자 ID로 사용자를 업데이트합니다.
        """
        return self.user_info_repository.update_user(user_id, user_data)

    def delete_user(self, user_id: str):
        """
        주어진 사용자 ID로 사용자를 삭제합니다.
        """
        self.user_info_repository.delete_user(user_id)
        

class ChatHistoryService:
    def __init__(self):
        self.session = SessionLocal()
        self.chat_history_repository = ChatHistoryRepository(self.session)

    def get_chat_history_by_user_id(self, user_id: str) -> List[ChatHistory]:
        return self.chat_history_repository.get_chat_history_by_user_id(user_id=user_id)
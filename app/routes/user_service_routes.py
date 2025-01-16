from app.config import setup_logging
from app.db_model.data_repository import ChatHistoryRepository, UserInfoRepository
from app.db_model.database import SessionLocal
from app.db_model.database_models import ChatHistory, UserInfo
from fastapi import FastAPI, APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import Optional
from typing import List

# 라우터 정의
router = APIRouter()

class LoginRequest(BaseModel):
    user_id: str
    password: str

@router.post("/api/login")
async def login(request: Request, loginRequest: LoginRequest):
    print(f"### {loginRequest}")

    user_service = UserService()
    
    # user_id로 조회
    user_info = user_service.get_user_by_id(loginRequest.user_id)
    if user_info:
        if user_info.password == loginRequest.password:
            # 사용자 정보를 세션에 저장
            request.session["user_info"] = {
                "user_id": user_info.user_id,
                "email": user_info.email,
            }
            return {"message": ""}
        else:
            return JSONResponse(
                content={"message": "비밀번호가 일치하지 않습니다."},
                status_code=400
            )
    else:
        # 없으면 사용자 정보 저장
        user_info = UserInfo(
            user_id=loginRequest.user_id, 
            password=loginRequest.password, 
            email=f"{loginRequest.user_id}@temp.com"
        )
        user_info = user_service.create_user(user_info)
        # 사용자 정보를 세션에 저장
        request.session["user_info"] = {
            "user_id": user_info.user_id,
            "email": user_info.email,
        }
        return {"message": f"계정 {loginRequest.user_id}이 생성 되었습니다."}

@router.post("/api/logout")
async def login(request: Request):
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)
    if user_info:
        # 세션에서 사용자 정보 제거
        del request.session['user_info']
    
    return {"message": "로그아웃 되었습니다."}

@router.get("/api/history")
async def history(request: Request, type_code: str):
    print(f"### {request}")
     # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)
    print(user_info)

    chatHistoryService = ChatHistoryService()
    list = chatHistoryService.get_chat_history_by_user_id_and_type_code(user_info['user_id'], type_code)

    return {"response": list}

class UserService:
    def __init__(self):
        self.session = SessionLocal()
        self.user_info_repository = UserInfoRepository(self.session)

    def get_user_by_id(self, user_id: str):
        """
        주어진 사용자 ID로 사용자를 조회합니다.
        
        Args:
            user_id: 조회할 사용자 ID
            
        Returns:
            조회된 사용자 정보. 없으면 None 반환
        """
        return self.user_info_repository.get_user_by_id(user_id)

    def get_user_by_email(self, email: str):
        """
        주어진 이메일로 사용자를 조회합니다.
        
        Args:
            email: 조회할 사용자 이메일
            
        Returns:
            조회된 사용자 정보. 없으면 None 반환
        """
        return self.user_info_repository.get_user_by_email(email)

    def get_all_users(self):
        """
        모든 사용자를 조회합니다.
        
        Returns:
            모든 사용자 정보 리스트
        """
        return self.user_info_repository.get_all_users()

    def create_user(self, user_data: dict):
        """
        새로운 사용자를 생성합니다.
        
        Args:
            user_data: 생성할 사용자 정보
            
        Returns:
            생성된 사용자 정보
        """
        return self.user_info_repository.create_user(user_data)

    def update_user(self, user_id: str, user_data: dict):
        """
        주어진 사용자 ID로 사용자를 업데이트합니다.
        
        Args:
            user_id: 업데이트할 사용자 ID
            user_data: 업데이트할 사용자 정보
            
        Returns:
            업데이트된 사용자 정보
        """
        return self.user_info_repository.update_user(user_id, user_data)

    def delete_user(self, user_id: str):
        """
        주어진 사용자 ID로 사용자를 삭제합니다.
        
        Args:
            user_id: 삭제할 사용자 ID
        """
        self.user_info_repository.delete_user(user_id)



class ChatHistoryService:
    def __init__(self):
        self.session = SessionLocal()
        self.chat_history_repository = ChatHistoryRepository(self.session)

    def get_chat_history_by_user_id_and_type_code(self, user_id: str, type_code: str) -> List[ChatHistory]:
        return self.chat_history_repository.get_chat_history_by_user_id_and_type_code(user_id=user_id, type_code=type_code)
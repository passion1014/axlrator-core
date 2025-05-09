from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from requests import Session
# from app.config import setup_logging
from axlrator_core.db_model.database import get_async_session
from axlrator_core.db_model.data_repository import ChatHistoryRepository, UserInfoRepository
from axlrator_core.db_model.database_models import ChatHistory, UserInfo
from sqlalchemy.ext.asyncio import AsyncSession

# 라우터 정의
router = APIRouter()

class LoginInfo(BaseModel):
    user_id: str
    password: str
class HistoryInfo(BaseModel):
    data: str
    title: str
    type_code: str

@router.post("/api/login")
async def login(
    request: Request, 
    loginRequest: LoginInfo,
    session: AsyncSession = Depends(get_async_session)
):
    user_service = UserService(session=session)
    
    # user_id로 조회
    user_info = await user_service.get_user_by_id(loginRequest.user_id)
    if user_info:
        if user_info.password == loginRequest.password:
            # 사용자 정보를 세션에 저장
            request.session["user_info"] = {
                "id": user_info.id,
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
        user_info = await user_service.create_user(user_info)
        # 사용자 정보를 세션에 저장
        request.session["user_info"] = {
            "id": user_info.id,
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
async def history(request: Request, type_code: str, session: AsyncSession = Depends(get_async_session)):
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)

    chatHistoryService = ChatHistoryService(session=session)
    list = await chatHistoryService.get_chat_history_by_user_id_and_type_code(user_info['user_id'], type_code)

    return {"response": list}


@router.post("/api/history")
async def create_chat_history(request: Request, historyInfo: HistoryInfo, session: AsyncSession = Depends(get_async_session)):
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)

    history = {
        'title': historyInfo.title,
        'type_code': historyInfo.type_code,
        'data': historyInfo.data,
        'user_info_id': user_info['id'],
        'modified_at': datetime.now(),
        'created_at':  datetime.now(),
        'created_by':  user_info['user_id'],
        'modified_by': user_info['user_id'],
    }
    chatHistoryService = ChatHistoryService(session=session)
    await chatHistoryService.create_chat_history(history)

    return {"message": ""}


@router.post("/api/deletehistory")
async def delete_chat_history(request: Request, session: AsyncSession = Depends(get_async_session)):
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)
    
    data = await request.json()
    chat_id = data.get('id')

    chatHistoryService = ChatHistoryService(session=session)
    await chatHistoryService.delete_chat_history(chat_id, user_info['id']);
    return {"message": ""}

@router.post("/api/deleteallhistory")
async def delete_all_chat_history(request: Request, session: AsyncSession = Depends(get_async_session)):
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)

    chatHistoryService = ChatHistoryService(session=session)
    await chatHistoryService.delete_all_chat_history(user_info['id']);

    return {"message": ""}

class UserService:
    def __init__(self, session:AsyncSession):
        self.user_info_repository = UserInfoRepository(session=session)

    async def get_user_by_id(self, user_id: str):
        """
        주어진 사용자 ID로 사용자를 조회합니다.
        
        Args:
            user_id: 조회할 사용자 ID
            
        Returns:
            조회된 사용자 정보. 없으면 None 반환
        """        
        return await self.user_info_repository.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str):
        """
        주어진 이메일로 사용자를 조회합니다.
        """
        return await self.user_info_repository.get_user_by_email(email)

    async def get_all_users(self):
        """
        모든 사용자를 조회합니다.
        """
        return await self.user_info_repository.get_all_users()

    async def create_user(self, user_data: dict):
        """
        새로운 사용자를 생성합니다.
        """
        return await self.user_info_repository.create_user(user_data)

    async def update_user(self, user_id: str, user_data: dict):
        """
        주어진 사용자 ID로 사용자를 업데이트합니다.
        """
        return await self.user_info_repository.update_user(user_id, user_data)

    async def delete_user(self, user_id: str):
        """
        주어진 사용자 ID로 사용자를 삭제합니다.
        """
        await self.user_info_repository.delete_user(user_id)


class ChatHistoryService:
    def __init__(self, session:AsyncSession):
        self.chat_history_repository = ChatHistoryRepository(session=session)

    async def get_chat_history_by_user_id_and_type_code(self, user_id: str, type_code: str) -> List[ChatHistory]:
        return await self.chat_history_repository.get_chat_history_by_user_id_and_type_code(user_id=user_id, type_code=type_code)
    
    async def create_chat_history(self, history: dict) -> ChatHistory:
        return await self.chat_history_repository.create_chat_history(history)  
    
    async def delete_chat_history(self, chat_id: int, userInfo_id: int) -> ChatHistory:
        return await self.chat_history_repository.delete_chat_history(chat_id, userInfo_id)  
    
    async def delete_all_chat_history(self, user_info_id: int) -> ChatHistory:
        return await self.chat_history_repository.delete_all_chat_history(user_info_id)  

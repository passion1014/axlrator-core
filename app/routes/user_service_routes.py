import json
from fastapi import FastAPI, APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from openai import BaseModel
from app.config import setup_logging
from app.db_model.data_repository import UserInfoRepository
from app.db_model.database import SessionLocal
from app.db_model.database_models import UserInfo
from uuid import uuid4

logger = setup_logging()
router = APIRouter()

session_data = {}
# 세션 미들웨어
# app = FastAPI()
# app.add_middleware(SessionMiddleware, secret_key="cgcgcg")

class LoginRequest(BaseModel):
    user_id: str
    password: str


@router.post("/api/login")
async def login(request: LoginRequest):
    print(f"### {request}")

    user_service = UserService()
    
    # user_id로 조회
    user_info = user_service.get_user_by_id(request.user_id)
    if user_info:
        if user_info.password == request.password:
            return ""
        else:
            return JSONResponse(
                content={"message": "비밀번호가 일치하지 않습니다."},
                status_code=400
            )
    else:
        # 없으면 사용자 정보 저장
        user_info = UserInfo(user_id=request.user_id, password=request.password, email=f"{request.user_id}@temp.com")
        user_info = user_service.create_user(user_info)
    
        # 사용자 정보를 세션에 저장
        session_id = str(uuid4())
        session_data[session_id] = user_info
         # 쿠키로 세션 아이디를 전달
        # response = {"session_id": session_id}
        response = {"message": f"계정 {request.user_id}이 생성 되었습니다."}
        # 쿠키에 HttpOnly 속성을 추가하여 JavaScript에서 접근할 수 없게 만듦
        cookie = f"session_id={session_id}; Path=/; HttpOnly"
        # return response, {"headers": {"Set-Cookie": cookie}}
        return {"message": f"계정 {request.user_id}이 생성 되었습니다."}

        # request.session['user_info'] = user_info

        # user_dict = {key: value for key, value in user_info.__dict__.items() if not key.startswith('_')} # 인스턴스를 딕셔너리로 변환
        # user_json = json.dumps(user_dict, ensure_ascii=False) # 딕셔너리를 JSON으로 변환
        # return {"message": f"계정 {request.user_id}이 생성 되었습니다."}
    

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
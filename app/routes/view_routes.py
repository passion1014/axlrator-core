from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, setup_logging
from app.db_model.database import SessionLocal
from app.db_model.data_repository import ChatHistoryRepository, UserInfoRepository
from app.db_model.database_models import ChatHistory, UserInfo

logger = setup_logging()
router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIR)



@router.get("/login", response_class=HTMLResponse)
async def view_login(request: Request):
    return templates.TemplateResponse("view/member/login.html", {"request": request, "message": "로그인"})


# 사용자(code assist)
#     - 용어변환
#     - 프로그램 코드 생성
#     - SQL 생성
#     - RAG 요청
# view/code/**
@router.get("/code/{subpath:path}", response_class=HTMLResponse)
async def view_code(request: Request):
    print(f"Requested URL path: {request.url.path}")

    url_path = request.url.path


    user_info = request.session.get('user_info', None)
    if not user_info:
        if "/chatplain" in url_path:
            # 사용자 정보 user_info테이블에 없으면 저장
            user_info = insert_ip_to_database(request.client.host) 
            

            # 사용자 정보를 세션에 저장
            request.session["user_info"] = {
                "id": user_info.id,
                "user_id": user_info.user_id,
                "email": user_info.email,
            }
        else:
            return RedirectResponse(url="/view/login")
            
    if "/conversion" in url_path:
        return templates.TemplateResponse("view/code/conversion.html", {"request": request, "message": "용어변환", "user_info":user_info })
    elif "/completion" in url_path:
        return templates.TemplateResponse("view/code/completion.html", {"request": request, "message": "프로그램 코드 생성", "user_info":user_info })
    elif "/completion2" in url_path:
        return templates.TemplateResponse("view/code/completion.html", {"request": request, "message": "프로그램 코드 생성2", "user_info":user_info })
    elif "/text2sql" in url_path:
        return templates.TemplateResponse("view/code/text2sql.html", {"request": request, "message": "SQL 생성", "user_info":user_info })    
    elif "/chatplain" in url_path: #sidebar, header 없는 채팅 화면
        return templates.TemplateResponse("view/code/chatplain.html", {"request": request, "message": "Code Chat", "user_info":user_info })   
    elif "/chat" in url_path:
        return templates.TemplateResponse("view/code/chat.html", {"request": request, "message": "Code Chat", "user_info":user_info })    
    else :
        return templates.TemplateResponse("error.html", {"request": request, "message": "요청하신 페이지를 찾을 수 없습니다.", "user_info":user_info }, status_code=404)


def insert_ip_to_database(ip: str):
    user_service = UserService()
    user_info = user_service.get_user_by_id(ip)

    if not user_info:        
        # 없으면 사용자 정보 저장
        user_info = UserInfo(
            user_id = ip, 
            password = ip, 
            email=f"{ip}@temp.com"
        )
        user_info = user_service.create_user(user_info)
     
    return user_info

# 관리자
#     - VectorDB 조회
#     - VectorDB 추가/삭제(팝업)
#     - VectorDB Index 관리
#     - VectorDB Index 생성 (팝업)
#     - 원본 리소스 조회
#     - 원본 리소스 청크 조회
# view/admin/**
@router.get("/admin/{subpath:path}", response_class=HTMLResponse)
async def view_admin(request: Request):
    print(f"Requested URL path: {request.url.path}")
    
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)

    url_path = request.url.path
    
    if "/vector-data-list" in url_path:
        return templates.TemplateResponse("view/admin/vector-data-list.html", {"request": request, "message": "VectorDB 조회", "user_info":user_info })
    elif "/vector-index-list" in url_path:
        return templates.TemplateResponse("view/admin/vector-index-list.html", {"request": request, "message": "VectorDB Index 관리", "user_info":user_info })
    elif "/org-resrc-list" in url_path:
        return templates.TemplateResponse("view/admin/org-resrc-list.html", {"request": request, "message": "원본 리소스 조회", "user_info":user_info })
    elif "/org-resrc-chunk-list" in url_path:
        return templates.TemplateResponse("view/admin/org-resrc-chunk-list.html", {"request": request, "message": "원본 리소스 청크 조회", "user_info":user_info })
    else :
        return templates.TemplateResponse("error.html", {"request": request, "message": "요청하신 페이지를 찾을 수 없습니다."}, status_code=404)


# 워크플로우 관리
#     - 작업 대상 조회
#     - 작업 대상 추가/삭제 (팝업)
# view/workflow/**
@router.get("/workflow/{subpath:path}", response_class=HTMLResponse)
async def view_workflow(request: Request):
    print(f"Requested URL path: {request.url.path}")
    
    # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)

    url_path = request.url.path
    
    if "/task-target-list" in url_path:
        return templates.TemplateResponse("view/workflow/task-target-list.html", {"request": request, "message": "작업대상조회", "user_info":user_info })
    else :
        return templates.TemplateResponse("error.html", {"request": request, "message": "요청하신 페이지를 찾을 수 없습니다."}, status_code=404)


# 임시코드        
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
        if (user_id == 'admin'): # admin은 임시로 일단 로그인
            return UserInfo(user_id='admin', password='admin', email='admin@temp.com', user_name='관리자', is_active=True)
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

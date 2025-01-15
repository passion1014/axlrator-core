from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, setup_logging

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

     # 세션에서 사용자 정보 가져오기
    user_info = request.session.get('user_info', None)
    if not user_info:
        return RedirectResponse(url="/view/login")
    
    url_path = request.url.path
    
    if "/conversion" in url_path:
        return templates.TemplateResponse("view/code/conversion.html", {"request": request, "message": "용어변환", "user_info":user_info })
    elif "/completion" in url_path:
        return templates.TemplateResponse("view/code/completion.html", {"request": request, "message": "프로그램 코드 생성", "user_info":user_info })
    elif "/text2sql" in url_path:
        return templates.TemplateResponse("view/code/text2sql.html", {"request": request, "message": "SQL 생성", "user_info":user_info })
    elif "/chat" in url_path:
        return templates.TemplateResponse("view/code/chat.html", {"request": request, "message": "RAG 요청", "user_info":user_info })
    else :
        return templates.TemplateResponse("error.html", {"request": request, "message": "요청하신 페이지를 찾을 수 없습니다.", "user_info":user_info }, status_code=404)


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
    
    url_path = request.url.path
    
    if "/vector-data-list" in url_path:
        return templates.TemplateResponse("view/admin/vector-data-list.html", {"request": request, "message": "VectorDB 조회"})
    elif "/vector-index-list" in url_path:
        return templates.TemplateResponse("view/admin/vector-index-list.html", {"request": request, "message": "VectorDB Index 관리"})
    elif "/org-resrc-list" in url_path:
        return templates.TemplateResponse("view/admin/org-resrc-list.html", {"request": request, "message": "원본 리소스 조회"})
    elif "/org-resrc-chunk-list" in url_path:
        return templates.TemplateResponse("view/admin/org-resrc-chunk-list.html", {"request": request, "message": "원본 리소스 청크 조회"})
    else :
        return templates.TemplateResponse("error.html", {"request": request, "message": "요청하신 페이지를 찾을 수 없습니다."}, status_code=404)


# 워크플로우 관리
#     - 작업 대상 조회
#     - 작업 대상 추가/삭제 (팝업)
# view/workflow/**
@router.get("/workflow/{subpath:path}", response_class=HTMLResponse)
async def view_workflow(request: Request):
    print(f"Requested URL path: {request.url.path}")
    
    url_path = request.url.path
    
    if "/task-target-list" in url_path:
        return templates.TemplateResponse("view/workflow/task-target-list.html", {"request": request, "message": "작업대상조회"})
    else :
        return templates.TemplateResponse("error.html", {"request": request, "message": "요청하신 페이지를 찾을 수 없습니다."}, status_code=404)
    
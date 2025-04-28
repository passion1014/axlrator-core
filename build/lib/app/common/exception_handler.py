import functools
from fastapi import Request
from typing import Callable, Any

from axlrator_core.config import setup_logging

logger = setup_logging()

def handle_exceptions(func: Callable) -> Callable:
    """
    공통 예외 처리 데코레이터
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        request: Request = kwargs.get("request")  # request 객체 가져오기
        try:
            return await func(*args, **kwargs)  # 원래 함수 실행
        except Exception as e:
            logger.error(f"{request.url.path} 요청 처리 중 오류 발생: {str(e)}")
            return {
                "success": False,
                "message": f"오류 발생: {str(e)}"
            }
    return wrapper

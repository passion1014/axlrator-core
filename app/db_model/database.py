# 필요한 라이브러리 import하기
from contextlib import asynccontextmanager
import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import create_engine

database_url = os.getenv("DATABASE_URL")

# SQLAlchemy engine 생성하기 - Connection Pool 설정
async_engine = create_async_engine(
    database_url, 
    echo=True,  # 로깅 활성화 (운영에서는 False 추천)
    pool_size=10,  # 유지할 커넥션 수 (기본: 5)
    max_overflow=20,  # 최대 초과 커넥션 수 (기본: 10)
    pool_timeout=30,  # 커넥션 가져올 때 최대 대기 시간 (초)
    pool_recycle=1800,  # 사용하지 않는 커넥션 재사용 시간 (초)
    pool_pre_ping=True  # 연결이 유효한지 사전 체크 (연결 끊김 방지)
)

# DB 세션 생성하기
_AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)


engine = create_engine(
    database_url, 
    echo=True,  # 로깅 활성화 (운영에서는 False 추천)
    pool_size=10,  # 유지할 커넥션 수 (기본: 5)
    max_overflow=20,  # 최대 초과 커넥션 수 (기본: 10)
    pool_timeout=30,  # 커넥션 가져올 때 최대 대기 시간 (초)
    pool_recycle=1800,  # 사용하지 않는 커넥션 재사용 시간 (초)
    pool_pre_ping=True  # 연결이 유효한지 사전 체크 (연결 끊김 방지)
)

# DB 세션 생성하기 (동기 세션)
_SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Base class 생성하기
Base = declarative_base()

@asynccontextmanager
async def get_async_session_CTX():
    async with _AsyncSessionLocal() as session:
        yield session

async def get_async_session() -> AsyncSession:
    async with _AsyncSessionLocal() as session:
        yield session

# @asynccontextmanager
# async def get_async_session_generator():
#     async with _AsyncSessionLocal() as session:
#         yield session
    # db = _AsyncSessionLocal()
    # try:
    #     yield db
    # finally:
    #     await db.close()
        
def get_session():
    
    return _SessionLocal


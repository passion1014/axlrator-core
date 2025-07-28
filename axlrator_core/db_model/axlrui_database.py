import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# .env에 AXLRUI_DATABASE_URL이 정의돼 있어야 함
load_dotenv()
axlrui_database_url = os.getenv("AXLRUI_DATABASE_URL")

# 엔진 및 세션팩토리 구성
axlrui_engine = create_engine(
    axlrui_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

_SessionLocal = sessionmaker(bind=axlrui_engine, autocommit=False, autoflush=False)


# Base class 생성하기
Base = declarative_base()


def get_axlrui_session():
    return _SessionLocal()
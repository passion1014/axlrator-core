# 필요한 라이브러리 import하기
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# SQLAlchemy engine 생성하기
# engine = create_engine("postgresql://ragserver:ragserver@localhost/ragserver")
engine = create_engine("postgresql://ragserver:ragserver@langfuse-main-db-1:5432/ragserver")

# DB 세션 생성하기
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class 생성하기
Base = declarative_base()

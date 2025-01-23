# 공통 환경 설정
from dotenv import load_dotenv
import os

# 작업디렉토리를 상위경로로 변경
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
os.chdir(parent_dir)

# 환경변수 설정
load_dotenv(dotenv_path=".env", override=True)

from typing import Literal
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver  # 동기용 PostgresSaver 사용
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # 삭제: 비동기용은 더 이상 필요
from psycopg_pool import ConnectionPool  # 동기용 ConnectionPool 사용

DB_URI = os.getenv("DATABASE_URL")
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

# 동기 함수로 변경
def setup_postgres_pool():
    with ConnectionPool(
        # Example configuration
        conninfo='postgresql://ragserver:ragserver@rag_server-db-1:5432/ragserver',
        max_size=20,
        kwargs=connection_kwargs,
    ) as pool:
        checkpointer = PostgresSaver(pool)  # 동기용 checkpointer 사용

        # NOTE: you need to call .setup() the first time you're using your checkpointer
        checkpointer.setup()

# 동기 함수 실행
setup_postgres_pool()


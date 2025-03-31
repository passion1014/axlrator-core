import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Alembic Config 객체
config = context.config
fileConfig(config.config_file_name)

from app.db_model.database_alembic import Base
from app.db_model import database_models  # 실제 모델 불러와야 자동 감지 가능

target_metadata = Base.metadata

# 환경 변수 또는 ini에서 DB URL 불러오기
config.set_main_option("sqlalchemy.url", os.getenv("ALEMBIC_DB_URL", config.get_main_option("sqlalchemy.url")))

def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

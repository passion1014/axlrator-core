import csv
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 작업디렉토리를 상위경로로 변경
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
os.chdir(parent_dir)

# 환경변수 설정
load_dotenv(dotenv_path=".env.testcase", override=True)
database_url = os.getenv("DATABASE_URL")




from app.db_model.database import get_async_session
from app.db_model.database_models import RSrcTable, RSrcTableColumn


# SQLAlchemy engine 생성하기
engine = create_engine(database_url) # 로컬에서 실행시
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def insert_data_from_file(file_path):
    # 데이터베이스 세션 생성
    session = get_async_session()
    
    try:
        # 파일 읽기
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            
            table_map = {}  # TABLE_NAME과 RSrcTable 객체 매핑
            
            for row in csv_reader:
                table_name = row['TABLE_NAME'].strip()
                column_name = row['COLUMN_NAME'].strip()
                data_type = row['DATA_TYPE'].strip()
                comment = row['COMMENT'].strip()
                
                # RSrcTable 존재 여부 확인
                if table_name not in table_map:
                    # 새로운 테이블 추가
                    new_table = RSrcTable(
                        table_name=table_name,
                        table_desc=f"Description for {table_name}",
                        created_at=datetime.now(),
                        modified_at=datetime.now(),
                        created_by="system",
                        modified_by="system"
                    )
                    session.add(new_table)
                    session.flush()  # ID를 가져오기 위해 flush 호출
                    table_map[table_name] = new_table
                
                # 테이블 컬럼 추가
                new_column = RSrcTableColumn(
                    column_name=column_name,
                    column_korean_name=f"Korean name for {column_name}",
                    column_type=data_type,
                    column_desc=comment,
                    rsrc_table_id=table_map[table_name].id,
                    created_at=datetime.now(),
                    modified_at=datetime.now(),
                    created_by="system",
                    modified_by="system"
                )
                session.add(new_column)
        
        # 모든 데이터 커밋
        session.commit()
        print("Data inserted successfully.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    # 파일 경로 설정
    FILE_PATH = "db_schema_sample_data.csv"  # 파일 경로를 적절히 수정하세요

    insert_data_from_file(FILE_PATH)
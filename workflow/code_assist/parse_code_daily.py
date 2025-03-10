from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import os
import re
import xml.etree.ElementTree as ET

# 외부 모듈 import
from app.process.content_chunker import file_chunk_and_save
from app.db_model.database import get_async_session
from app.vectordb.bm25_search import create_elasticsearch_bm25_index

# DAG 기본 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 26),
    'retries': 1,
}

dag = DAG(
    'workflow_parse_dag',
    default_args=default_args,
    schedule_interval='@daily',
)

def find_files(project_dir, output_dir):
    extensions = ['.java', '.xml', '.js', '.ddl_simple']
    file_list = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(tuple(extensions)):
                file_list.append(os.path.join(root, file))
    
    output_path = f"{output_dir}/found_files.txt"
    with open(output_path, 'w') as f:
        for file_path in file_list:
            f.write(file_path + '\n')

find_files_task = PythonOperator(
    task_id='find_files',
    python_callable=find_files,
    op_kwargs={'project_dir': '/path/to/project', 'output_dir': '/path/to/output'},
    dag=dag,
)

# 추가 태스크 변환 필요
# file_chunk_and_save, create_elasticsearch_bm25_index 등을 PythonOperator로 변환하여 연결해야 함

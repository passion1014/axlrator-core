from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
from airflow.utils.task_group import TaskGroup
from datetime import datetime
import os, asyncio

@task()
def find_files(project_dir, output_dir):
    extensions = ['.java', '.xml', '.js', '.ddl_simple']
    file_list = []
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith(tuple(extensions)):
                file_list.append(os.path.join(root, file))

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'found_files.txt')
    with open(output_file, 'w') as f:
        for file_path in file_list:
            f.write(file_path + '\n')

    return file_list  # 동적 태스크 매핑용

@task()
def parse_file(file_path, output_dir):
    from axlrator_core.db_model.database import get_async_session_ctx
    from axlrator_core.process.content_chunker import file_chunk_and_save
    from axlrator_core.vectordb.bm25_search import create_elasticsearch_bm25_index

    async def async_run():
        async with get_async_session_ctx() as session:
            org_resrc, chunk_list = await file_chunk_and_save(file_path, session=session)
            create_elasticsearch_bm25_index(index_name='cg_code_assist', org_resrc=org_resrc, chunk_list=chunk_list)

            output_file = os.path.join(output_dir, f'parsed_{os.path.basename(file_path)}.txt')
            with open(output_file, 'w') as f:
                for chunk in chunk_list:
                    f.write(str(chunk) + '\n')

    asyncio.run(async_run())

with DAG(
    dag_id='code_processing_pipeline',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    PROJECT_DIR = '/your/project'
    OUTPUT_DIR = '/your/output'

    files = find_files(project_dir=PROJECT_DIR, output_dir=OUTPUT_DIR)
    files.expand(file_path=files, output_dir=[OUTPUT_DIR]*100).map(parse_file)

from datetime import datetime
import os
import re
import xml.etree.ElementTree as ET
import luigi

from app.process.content_chunker import JavaChunkMeta, SQLChunkMeta, chunk_file, file_chunk_and_save
from app.db_model.database import SessionLocal


class FindFiles(luigi.Task):
    project_dir = luigi.Parameter()
    output_dir = luigi.Parameter()  # 중간 디렉토리 경로 전달

    extensions = ['.java', '.xml', '.js', '.ddl_simple']

    def output(self):
        # 파일 목록을 저장할 파일을 지정
        return luigi.LocalTarget(f'{self.output_dir}/found_files.txt')

    def run(self):
        # 경로에서 파일을 찾아 리스트로 저장
        file_list = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(tuple(self.extensions)):
                    file_list.append(os.path.join(root, file))

        # 결과를 output 파일에 저장
        with self.output().open('w') as f:
            for file_path in file_list:
                f.write(file_path + '\n')


# Luigi Task: 각 파일 파싱
class ParseFile(luigi.Task):
    file_path = luigi.Parameter()
    output_dir = luigi.Parameter()  # 중간 디렉토리 경로 전달
    
    session = SessionLocal()

    def output(self):
        output_file = f'{self.output_dir}/parsed_{os.path.basename(self.file_path)}.txtt'
        return luigi.LocalTarget(output_file)

    def run(self):
        try:
            # 파일을 청크로 분할하고 DB에 저장
            # chunk_list에는 JavaChunkMeta 또는 SQLChunkMeta 객체들이 담김
            # chunk_list의 각 객체는 코드 조각과 메타데이터(함수명, 테이블명 등)를 포함
            org_resrc, chunk_list = file_chunk_and_save(self.file_path, session=self.session)
            
            # 파일로 작성
            with self.output().open('w') as f:
                for item in chunk_list:
                    f.write(item.get('code', '') + '\n==============================')  # get으로 변경

        except Exception as e:
            self.session.rollback()
            print(f"### Error processing file {self.file_path}: {e}")

# Luigi Task: 모든 파일을 처리하는 메인 Task
class ProcessAllFiles(luigi.Task):
    project_dir = luigi.Parameter()
    # index_name = luigi.Parameter()

    def requires(self):
        return FindFiles(self.project_dir, output_dir=self.output_dir())

    def output(self):
        # return luigi.LocalTarget('workflow/working/all_files_parsed.txt')
        return luigi.LocalTarget(f'{self.output_dir()}/all_files_parsed.txt')

    def output_dir(self):
        # 오늘 날짜 + 시분초로 중간 디렉토리 생성
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f'workflow/working/{current_time}'

        # 디렉토리가 없으면 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        return output_dir

    def run(self):
        # FindFiles 작업에서 생성한 파일 목록을 읽어들임
        find_files_task = self.requires()
        
        # 파일 목록을 읽기
        with find_files_task.output().open('r') as f:
            for file_path in f:
                file_path = file_path.strip()
                parse_task = ParseFile(file_path=file_path, output_dir=self.output_dir())
                luigi.build([parse_task], local_scheduler=True)
                
        # 모든 파일 처리가 완료되면 완료 파일 생성
        with self.output().open('w') as f:
            f.write('All files have been parsed.\n')

# Luigi 실행: 프로젝트 폴더 지정
if __name__ == "__main__":
    dir = "/app/rag_server/data/input/program"
    # dir = "/app/rag_data/DDL"
    luigi.build([ProcessAllFiles(project_dir=dir)], local_scheduler=True)


# python workflow_parse_code.py ProcessAllFiles --project-dir /your/project/path --index-name your_index_name --local-scheduler
# python -m workflow.workflow_parse_code

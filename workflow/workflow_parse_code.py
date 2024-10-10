from datetime import datetime
import os
import re
import xml.etree.ElementTree as ET
import luigi

from app.process.content_chunker import JavaChunkMeta, chunk_file
from app.db_model.database_models import OrgRSrc, OrgRSrcCode, ChunkedData
from app.db_model.database import SessionLocal
from app.vectordb.faiss_vectordb import FaissVectorDB
from app.process.java_parser import parse_java_file


class FindFiles(luigi.Task):
    project_dir = luigi.Parameter()
    output_dir = luigi.Parameter()  # 중간 디렉토리 경로 전달

    extensions = ['.java', '.xml', '.js']

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
        # output_file = f'workflow/working/parsed_{os.path.basename(self.file_path)}.txtt'
        output_file = f'{self.output_dir}/parsed_{os.path.basename(self.file_path)}.txtt'
        return luigi.LocalTarget(output_file)

    def run(self):
        try:
            # 원본 파일 정보 저장
            org_resrc = OrgRSrc(
                resrc_name = os.path.basename(self.file_path),  # 파일명
                resrc_type = '01',  # 가정
                resrc_path = self.file_path,
                resrc_desc = 'Parsed Java class',
                # last_modified_time = class_info.get('last_modified'), # 추후 어떤 값을 셋팅 할지 확인 필요
            )
            self.session.add(org_resrc)
            self.session.flush() # org_resrc.id를 얻기 위해 flush를 한다. but commit 되기 전임

            # 파일 chunking
            chunk_list = chunk_file(self.file_path)
            
            # chunking 데이터 저장
            for idx, chunk in enumerate(chunk_list, start=1):
                if chunk is None:
                    continue
                
                if isinstance(chunk, JavaChunkMeta):
                    data_name = chunk.function_name # 함수명
                    data_type = 'code'  # 데이터 유형 (예: code)
                    context_chunk = chunk.summary  # 컨텍스트 청크
                    document_metadata = chunk.summary   # 문서의 메타데이터
                else: # 알 수 없는 유형의 데이터
                    data_name = 'unknown'
                    data_type = 'unknown'
                    context_chunk = 'unknown'
                    document_metadata = 'unknown'

                chunked_data = ChunkedData(
                    seq = idx + 1,  # 순번
                    org_resrc_id = org_resrc.id,  # OrgRSrc의 외래키
                    data_name = data_name,
                    data_type = data_type,
                    content = chunk.chunk_content,  # 내용
                    context_chunk = context_chunk,
                    document_metadata = document_metadata
                    # faiss_info_id = self.faiss_info_id,
                )
                self.session.add(chunked_data)

            # 세션 커밋
            self.session.commit()            
            
            # 파일로 작성
            with self.output().open('w') as f:
                for item in chunk_list:
                    f.write(item.get('code', '') + '\n==============================')  # get으로 변경

        except Exception as e:
            self.session.rollback()
            print(f"### Error processing file {self.file_path}: {e}")        
        
        

    # # Java 파일 파싱 (함수별로 split)
    # def parse_java(self):
    #     class_info, methods = parse_java_file(self.file_path)
        
    #     return class_info, methods

    # XML 파일 파싱 (MyBatis 형식)
    def parse_xml(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        # MyBatis 매퍼 추출 예시 (select, insert, update 등 태그)
        queries = []
        for elem in root.findall('.//select'):
            queries.append(ET.tostring(elem, encoding='unicode'))
        return queries

    # JS 파일 파싱 (함수별로 split)
    def parse_js(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 간단한 함수 추출 패턴 (function 키워드 사용)
        pattern = r'function\s+(\w+)\s*\(.*?\)\s*\{'
        functions = re.findall(pattern, content)
        return functions

# Luigi Task: 모든 파일을 처리하는 메인 Task
class ProcessAllFiles(luigi.Task):
    project_dir = luigi.Parameter()
    index_name = luigi.Parameter()

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
        print(f"### ProcessAllFiles run / index_name = {str(self.index_name)}")
        
        # # FAISS_INFO에 저장 및 .index 파일 생성
        # faissVectorDB = FaissVectorDB()
        # faiss_info = faissVectorDB.write_index(file_path=f'data/vector/{self.index_name}.index',
        #                                        index_name=self.index_name, 
        #                                        index_desc='프로그램 분석')

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
    # /app/rag_data/is_modon_proto
    dir = "/app/rag_data/is_modon_proto//src/main/java/com/modon/control/weather/controller"
    luigi.build([ProcessAllFiles(project_dir=dir, index_name="is_modon_proto")], local_scheduler=True)


    
# python workflow_parse_code.py ProcessAllFiles --project-dir /your/project/path --index-name your_index_name --local-scheduler
# python -m workflow.workflow_parse_code

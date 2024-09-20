import os
import re
import xml.etree.ElementTree as ET
import luigi

from app.db_model.database_models import OrgRSrc, OrgRSrcCode, ChunkedData
from app.db_model.database import SessionLocal
from app.vectordb.faiss_vectordb import FaissVectorDB
from workflow.parse_java import parse_java_file

# Luigi Task: 프로젝트 내 파일 탐색
class FindFiles(luigi.Task):
    project_dir = luigi.Parameter()

    extensions = ['.java', '.xml', '.js']

    def output(self):
        # 더 이상 파일 출력하지 않음, 하지만 여전히 Luigi의 Task 구조에서는 output을 요구할 수 있으므로 비어 있는 파일 지정
        return luigi.LocalTarget('workflow/working/found_files_dummy.txt')

    def run(self):
        # print(f"### FindFiles run / index_name = {str(self.index_name)}")
        
        # 경로에서 파일을 찾아 리스트로 저장
        self.file_list = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(tuple(self.extensions)):
                    self.file_list.append(os.path.join(root, file))

        # 결과 확인을 위한 파일 출력
        with self.output().open('w') as f:
            for file_path in self.file_list:
                f.write(file_path + '\n')

    def get_file_list(self):
        return self.file_list



# Luigi Task: 각 파일 파싱
class ParseFile(luigi.Task):
    file_path = luigi.Parameter()
    # faiss_info_id = luigi.Parameter()
    
    session = SessionLocal()

    def output(self):
        output_file = f'workflow/working/parsed_{os.path.basename(self.file_path)}.txtt'
        return luigi.LocalTarget(output_file)

    def run(self):
        if self.file_path.endswith('.java'):
            class_info, functions = self.parse_java()

            # OrgRSrc에 저장
            org_resrc = OrgRSrc(
                resrc_name = class_info.get('class_name'), 
                resrc_type = '01',  # 가정
                resrc_path = self.file_path,
                resrc_desc = 'Parsed Java class',
                # last_modified_time = class_info.get('last_modified'), # 추후 어떤 값을 셋팅 할지 확인 필요
            )
            self.session.add(org_resrc)
            self.session.commit()
            
            # OrgRSrcCode에 저장
            org_resrc_code = OrgRSrcCode(
                project_info = '', # 추후 어떤 값을 셋팅 할지 확인 필요
                package_name = class_info.get('package'),
                class_type = class_info.get('class_type'),
                class_name = class_info.get('class_name'),
                class_extends = class_info.get('extends'),
                class_implements = class_info.get('implements'),
                class_imports = ', '.join(class_info.get('imports', [])),  # 기본값을 빈 리스트로
                class_attributes = ', '.join([f"{field['type']} {field['name']}" for field in class_info.get('fields', [])]),  # 기본값 빈 리스트
                # class_methods_cnt = class_info.get('method_count', 0)  # 기본값 0
            )
            self.session.add(org_resrc_code)
            self.session.commit()
            

            print(f"#### 함수 갯수 = {len(functions)}")
            for idx, method in enumerate(functions):
                chunked_data = ChunkedData(
                    seq=idx + 1,  # 순번
                    org_resrc_id=org_resrc.id,  # OrgRSrc의 외래키
                    data_name=method.get('name'),  # 함수명
                    data_type='function',  # 데이터 유형 (예: function)
                    content=method.get('code'),  # 함수 내용
                    # faiss_info_id = self.faiss_info_id,
                )
                self.session.add(chunked_data)

            # 세션 커밋
            self.session.commit()            
            
            result = functions

        else:
            # 해당 조건에 맞지 않으면 무시
            print(f"Skipping file: {self.file_path}")
            result = ""
        
        # 파일로 작성
        with self.output().open('w') as f:
            for item in result:
                f.write(item.get('code', '') + '\n==============================')  # get으로 변경

    # Java 파일 파싱 (함수별로 split)
    def parse_java(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 간단한 함수 추출 패턴
        # pattern = r'public\s+.*?\s+(\w+)\(.*?\)\s*\{'
        # functions = re.findall(pattern, content)
        
        class_info, methods = parse_java_file(self.file_path)
        
        # 각 메서드의 코드만 배열에 담기
        # functions = [method['code'] for method in methods]

        return class_info, methods

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
        return FindFiles(self.project_dir)

    def output(self):
        return luigi.LocalTarget('workflow/working/all_files_parsed.txt')

    def run(self):
        print(f"### ProcessAllFiles run / index_name = {str(self.index_name)}")
        
        # # FAISS_INFO에 저장 및 .index 파일 생성
        # faissVectorDB = FaissVectorDB()
        # faiss_info = faissVectorDB.write_index(file_path=f'data/vector/{self.index_name}.index',
        #                                        index_name=self.index_name, 
        #                                        index_desc='프로그램 분석')

        # FindFiles Task로부터 파일 경로 리스트를 메모리에서 가져옴
        find_files_task = self.requires()
        file_paths = find_files_task.get_file_list()

        # 각 파일을 처리하는 ParseFile Task 실행 (yield 대신 직접 호출)
        for file_path in file_paths:
            parse_task = ParseFile(file_path=file_path)
            luigi.build([parse_task], local_scheduler=True)

        # 모든 파일 처리가 완료되면 완료 파일 생성
        with self.output().open('w') as f:
            f.write('All files have been parsed.\n')


# Luigi 실행: 프로젝트 폴더 지정
if __name__ == "__main__":
    luigi.build([ProcessAllFiles(project_dir="/app/rag_data/is_modon_proto", index_name="is_modon_proto")], local_scheduler=True)
    

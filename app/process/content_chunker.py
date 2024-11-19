from datetime import datetime
import json
import os
import re

from app.chain import create_summary_chain
from app.db_model.data_repository import ChunkedDataRepository, OrgRSrcRepository
from app.db_model.database import SessionLocal
from app.db_model.database_models import OrgRSrc
from app.formatter.code_formatter import parse_augmented_chunk
from app.process.contextual_process import generate_code_context
from app.process.java_parser import parse_java_file

class BaseChunkMeta:
    def __init__(self, chunk_content, start_line=-1, end_line=-1, type="base"):
        """
        BaseChunkMeta 객체를 초기화

        :param chunk_content: 코드 또는 콘텐츠의 실제 청크
        :param start_line: 청크의 시작 줄 번호
        :param end_line: 청크의 끝 줄 번호
        """
        self.chunk_content = chunk_content
        self.start_line = start_line
        self.end_line = end_line
        self.type = type
        self.summary = f"Chunk from line {self.start_line} to {self.end_line}"

    def __repr__(self):
        return (f"BaseChunkMeta(start_line={self.start_line}, end_line={self.end_line})")

    def set_summary(self, summary):
        """청크 요약 설정"""
        self.summary = summary
    
    def to_json(self):
        """청크 메타 정보를 JSON 문자열로 변환"""
        return json.dumps({
            "chunk_content": self.chunk_content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "type": self.type,
            "summary": self.summary,
        })


class JavaChunkMeta(BaseChunkMeta):
    def __init__(self, chunk_content, class_signature=None, class_package=None, class_fields=None, function_name=None, return_type=None, parameters=None):
        """
        JavaChunkMeta 객체를 초기화합니다.
        """
        super().__init__(chunk_content=chunk_content, type="java")
        self.class_signature = class_signature
        self.class_package = class_package
        self.class_fields = class_fields
        self.function_name = function_name
        self.return_type = return_type
        self.parameters = parameters
        self.set_summary(f"Java function '{self.function_name}' ({self.return_type}) ({self.parameters})")

    def __repr__(self):
        return (f"JavaChunkMeta:{self.to_json()}")

    def to_json(self):
        """청크 메타 정보를 JSON 문자열로 변환"""
        # BaseChunkMeta의 to_json을 활용하여 확장
        base_data = json.loads(super().to_json())
        base_data.update({
            "class_signature": self.class_signature,
            "class_package": self.class_package,
            "class_fields": self.class_fields,
            "function_name": self.function_name,
            "return_type": self.return_type,
            "parameters": self.parameters
        })
        return json.dumps(base_data)


class SQLChunkMeta(BaseChunkMeta):
    def __init__(self, chunk_content, table_name=None, table_korean_name=None ):
        super().__init__(chunk_content=chunk_content, type="DDL")
        self.table_name = table_name
        self.table_korean_name = table_korean_name
        self.set_summary(f"DDL 테이블 '{self.table_name}'")

    def __repr__(self):
        return (f"SQLChunkMeta:{self.to_json()}")

    def to_json(self):
        """청크 메타 정보를 JSON 문자열로 변환"""
        # BaseChunkMeta의 to_json을 활용하여 확장
        base_data = json.loads(super().to_json())
        base_data.update({
            "table_name": self.table_name,
            "table_korean_name": self.table_korean_name,
        })
        return json.dumps(base_data)


class TermsDataChunkMeta(BaseChunkMeta):
    def __init__(self, chunk_content, code=None, value=None ):
        super().__init__(chunk_content=chunk_content, type="TERMS")
        self.code = code
        self.value = value
        self.set_summary(f"{self.code} = {self.value}")

    def __repr__(self):
        return (f"TermsDataChunkMeta:{self.to_json()}")

    def to_json(self):
        """청크 메타 정보를 JSON 문자열로 변환"""
        # BaseChunkMeta의 to_json을 활용하여 확장
        base_data = json.loads(super().to_json())
        base_data.update({
            "code": self.code,
            "value": self.value,
        })
        return json.dumps(base_data)



def read_file(file_path):
    """Read the content of the given file path."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_chunks(chunks, extension, last_modified):
    """chunk를 데이터베이스에 저장"""
    for idx, chunk in enumerate(chunks, 1):
        print("=============================================")
        
def get_file_extension(file_path):
    """Return the file extension of the given file path."""
    return os.path.splitext(file_path)[1].lower()

def split_java_file(content:str) -> list[BaseChunkMeta]:
    """자바 소스코드 분할 처리"""
    class_info, method_infos = parse_java_file(content)
    
    # chunks 선언
    chunks = []
    
    # 클래스 정보로 JavaChunkMeta 생성
    for method in method_infos:
        code_chunk = JavaChunkMeta (
            chunk_content=method['code'],
            class_signature=class_info['class_signature'],
            class_package=class_info['package'],
            class_fields=class_info['fields'],
            function_name=method['name'],
            return_type=method['return_type'],
            parameters=method['parameters']
        )
        chunks.append(code_chunk)
    
    return chunks

def split_ddl_simple(content:str) -> list[BaseChunkMeta]:
    # '### '로 텍스트를 split해서 리스트로 반환
    split_text = content.split('### ')
    
    # 첫 번째 요소는 비어있을 수 있으므로 제거
    if split_text[0] == '':
        split_text = split_text[1:]
    
    # 각 요소 앞에 'TABLE '를 붙여서 원래 구조를 유지
    split_text = ['TABLE ' + section.strip() for section in split_text]
    
    
    # chunks 선언
    chunks = []
    for text in split_text:
        match = re.search(r'TABLE (\w+)\(([^)]+)\)', text)
        if match:
            table_name = match.group(1)  # 영문 테이블명
            table_korean_name = match.group(2)  # 한글명
        
        # BaseChunkMeta 객체 생성
        chunk = SQLChunkMeta(
            chunk_content=text,
            table_name=table_name,
            table_korean_name=table_korean_name,
        )
        
        # 추가 정보 설정
        # chunk.set_summary(f"DDL Simple 테이블: {table_name}")
        
        chunks.append(chunk)
    
    return chunks

def split_terms(content:str) -> list[BaseChunkMeta]:
    # 라인별로 split
    split_text = content.splitlines()
    
    # 빈 라인 제거
    split_text = [line for line in split_text if line.strip()]
    
    # 첫 번째 요소는 비어있을 수 있으므로 제거 
    if split_text[0] == '':
        split_text = split_text[1:]
    
    # 각 요소 앞에 'TERMS '를 붙여서 원래 구조를 유지
    # split_text = ['TERMS ' + section.strip() for section in split_text]
    
    # chunks 선언
    chunks = []
    for text in split_text:
        parts = text.split('=')
        code = parts[0]  # 영문 용어명
        value = parts[1]  # 한글명
        
        # TermsDataChunkMeta 객체 생성
        chunk = TermsDataChunkMeta(
            chunk_content=text,
            code=code,
            value=value,
        )
        
        chunks.append(chunk)
    
    return chunks


def get_file_type(file_path: str) -> str:
    """파일 경로를 받아서 파일 타입을 반환합니다.
    
    Args:
        file_path: 파일 경로
        
    Returns:
        str: 파일 타입 (java, ddl, terms, xml 등)
    """
    extension = get_file_extension(file_path)
    
    # 확장자별 파일 타입 결정
    if extension == ".java":
        return "java"
    elif extension == ".ddl_simple": 
        return "ddl"
    elif extension == ".terms":
        return "terms"
    elif extension == ".xml":
        return "xml"
    else:
        return "unknown"

    

def chunk_file(file_path) -> list[BaseChunkMeta]:
    """Main function to chunk a file based on its extension."""
    file_name = os.path.basename(file_path)
    content = read_file(file_path)
    extension = get_file_extension(file_path)
    file_type = get_file_type(file_path)

    # 파일 확장자에 따라 청크 분할 로직 선택
    if file_type == "java":
        chunks = split_java_file(content)
    elif file_type == "ddl":
        chunks = split_ddl_simple(content)
    elif file_type == "terms":
        chunks = split_terms(content)
    elif file_type == "xml":
        print(f"xml 파일 처리 예정")
    else:
        print(f"File type 'file_type={file_type} : extension={extension}' is not supported for chunking.")

    # 파일의 최종 수정일 가져오기 
    last_modified = os.path.getmtime(file_path)
    last_modified = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')

    # summary 추가
    if file_type == 'java' and "Dao.java" not in file_name:
        for chunk in chunks:
            # 코드 요약정보 생성    
            summary = generate_code_context(chunk.chunk_content)
            chunk.set_summary(summary)
    
    # 청크 정보 저장
    # save_chunks(chunks, extension, last_modified)
    return chunks


def file_chunk_and_save(file_path: str, session=None) -> tuple[OrgRSrc, list]:
    """
    파일을 청크로 분할하고 DB에 저장합니다.
    
    Args:
        file_path: 파일 경로
        org_resrc_id: 원본 리소스 ID
        session: DB 세션
        
    Returns:
        청크 리스트
    """
    
    if session is None:
        session = SessionLocal()
        
    chunk_list = []
    try:
        # 원본 파일 정보 저장
        orgRSrcRepository = OrgRSrcRepository(session=session)
        org_resrc = orgRSrcRepository.create_org_resrc(file_path=file_path, type="01", desc="JAVA")
        
        print(f" ### org_resrc = {str(org_resrc)}")

        # 파일 chunking
        chunk_list = chunk_file(file_path)
        
        # chunking 데이터 저장
        for idx, chunk in enumerate(chunk_list, start=1):
            if chunk is None:
                continue
            
            print(f"청크 타입: {type(chunk)}")
            
            if isinstance(chunk, JavaChunkMeta):
                data_name = chunk.function_name # 함수명
                data_type = 'code'  # 데이터 유형 (예: code)
                context_chunk = chunk.summary  # 컨텍스트 청크
                document_metadata = chunk.summary   # 문서의 메타데이터
                
            elif isinstance(chunk, SQLChunkMeta):
                data_name = chunk.table_name + f"({chunk.table_korean_name})" # 함수명
                data_type = 'DDL'  # 데이터 유형 (예: code)
                context_chunk = chunk.summary  # 컨텍스트 청크
                document_metadata = chunk.summary   # 문서의 메타데이터

            elif isinstance(chunk, TermsDataChunkMeta):
                data_name = chunk.code # 함수명
                data_type = 'terms'  # 데이터 유형 (예: javascript)
                context_chunk = chunk.summary  # 컨텍스트 청크
                document_metadata = chunk.summary   # 문서의 메타데이터

            else: # 알 수 없는 유형의 데이터
                data_name = 'unknown'
                data_type = 'unknown'
                context_chunk = 'unknown'
                document_metadata = 'unknown'

            chunkedDataRepository = ChunkedDataRepository(session=session)
            chunked_data = chunkedDataRepository.create_chunked_data(idx + 1
                                                                    , org_resrc.id
                                                                    , data_name
                                                                    , data_type
                                                                    , chunk.chunk_content
                                                                    , context_chunk
                                                                    , document_metadata)
        # 세션 커밋
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"### Error processing file {file_path}: {e}")
    
    return org_resrc, chunk_list



    # # Java 파일 파싱 (함수별로 split)
    # def parse_java(self):
    #     class_info, methods = parse_java_file(self.file_path)
        
    #     return class_info, methods

    # # XML 파일 파싱 (MyBatis 형식)
    # def parse_xml(self):
    #     tree = ET.parse(self.file_path)
    #     root = tree.getroot()

    #     # MyBatis 매퍼 추출 예시 (select, insert, update 등 태그)
    #     queries = []
    #     for elem in root.findall('.//select'):
    #         queries.append(ET.tostring(elem, encoding='unicode'))
    #     return queries

    # # JS 파일 파싱 (함수별로 split)
    # def parse_js(self):
    #     with open(self.file_path, 'r', encoding='utf-8') as f:
    #         content = f.read()

    #     # 간단한 함수 추출 패턴 (function 키워드 사용)
    #     pattern = r'function\s+(\w+)\s*\(.*?\)\s*\{'
    #     functions = re.findall(pattern, content)
    #     return functions

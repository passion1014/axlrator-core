from datetime import datetime
import json
import os

from app.chain import create_summary_chain
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


def read_file(file_path):
    """Read the content of the given file path."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def save_chunks(chunks, extension, last_modified):
    """chunk를 데이터베이스에 저장"""
    for idx, chunk in enumerate(chunks, 1):
        print(chunk)
        
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

def make_summary_with_llm(chunk:BaseChunkMeta):
    """chunk를 받아서 summary를 만들어줌"""

    # create_summary_chain 호출
    summary_chain = create_summary_chain()

    # 요약 생성을 위한 프롬프트 입력
    inputs = {
        "CODE_CHUNK": chunk.chunk_content
    }
    
    # summary_chain 실행
    try:
        result = summary_chain.invoke(inputs)
        print(f"Summary Chain Output: {result}")
    except Exception as e:
        result = ""
        print(f"Error during summary chain execution: {e}")
    
    return result


def chunk_file(file_path) -> list[BaseChunkMeta]:
    """Main function to chunk a file based on its extension."""
    content = read_file(file_path)
    extension = get_file_extension(file_path)


    # 파일 확장자에 따라 청크 분할 로직 선택
    if extension == ".java":
        chunks = split_java_file(content)
        
    elif extension == ".xml":
        # chunks = split_xml_file(content, llm_splitter)
        # output_path = os.path.join(os.path.dirname(file_path), "chunks")
        # write_chunks(chunks, output_path)
        print(f"xml 파일 처리 예정")
        
    else:
        print(f"File extension '{extension}' is not supported for chunking.")

    # 파일의 최종 수정일 가져오기 
    last_modified = os.path.getmtime(file_path)
    datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')

    # summary 추가
    for chunk in chunks:
        summary = make_summary_with_llm(chunk)
        chunk.set_summary(summary)

    # 청크 정보 저장
    save_chunks(chunks, extension, last_modified)



if __name__ == "__main__":
    file_path = input("Enter the path to the file you want to chunk: ").strip()
    if os.path.isfile(file_path):
        chunk_file(file_path)
    else:
        print("Invalid file path. Please check and try again.")



import os
import re
from typing import Optional

def remove_comments(code: str) -> str:
    """
    Java 코드에서 주석을 제거하는 함수입니다.

    이 함수는 다음과 같은 작업을 수행합니다:
    1. AppLog.info를 포함하는 줄을 제거합니다.
    2. 단일 줄 주석 (//)을 제거합니다. 단, 문자열 내부의 '//'는 제거하지 않습니다.
    3. 여러 줄 주석 (/* */)을 제거합니다.

    Args:
        code (str): 주석을 제거할 Java 코드 문자열

    Returns:
        str: 주석이 제거된 Java 코드 문자열
    """
    def is_within_string(line, index):
        # Check if the index falls within a string (either single or double quotes)
        quote_chars = ['"', "'"]
        inside_string = False
        quote_char = None
        for i, char in enumerate(line):
            if char in quote_chars:
                if inside_string and char == quote_char:
                    inside_string = False
                elif not inside_string:
                    inside_string = True
                    quote_char = char
            if i == index:
                return inside_string
        return inside_string

    # Step 1: Remove lines containing `AppLog.info`
    lines = code.splitlines()
    filtered_lines = [line for line in lines if 'AppLog.info' not in line]

    # Step 2: Remove single-line comments first
    comment_removed_lines = []
    
    single_line_comment_pattern = re.compile(r'//.*?$')

    for line in filtered_lines:
        # Remove single-line comments, but check if it's inside a string
        result = []
        start = 0

        for match in single_line_comment_pattern.finditer(line):
            if not is_within_string(line, match.start()):
                # Add the part before the comment
                result.append(line[start:match.start()])
                start = match.end()

        result.append(line[start:])  # Append the remaining part of the line
        final_line = ''.join(result)

        if final_line.strip():  # Avoid empty lines
            comment_removed_lines.append(final_line)

    # Step 3: Remove multi-line block comments
    cleaned_code = '\n'.join(comment_removed_lines)

    # Use regular expression to handle block comments
    block_comment_pattern = re.compile(r'/\*[\s\S]*?\*/', re.MULTILINE)
    cleaned_code = re.sub(block_comment_pattern, '', cleaned_code)

    return cleaned_code



# 클래스 정보 추출
def extract_class_info(java_code: str) -> dict[str, Optional[str]]:
    """
    주어진 Java 코드에서 클래스 정보를 추출합니다.

    :param java_code: Java 코드 문자열
    :return: 클래스 정보를 담은 딕셔너리
    """
    class_info = {
        'class_signature': None,  # 클래스 시그니처
        'package': None,        # 패키지명
        'class_type': None,     # 클래스유형
        'class_name': None,     # 클래스명
        'extends': None,        # 상속자
        'implements': [],       # 구현자 목록
        'imports': [],          # 클래스 import 목록
        'fields': [],           # 클래스 어트리뷰트 목록
        'methods': [],          # 메소드명 목록
        'method_count': 0,      # 메소드 갯수
        'last_modified': None   # 최종 수정일
    }
    
    # 클래스 시그니처 추출
    class_signature = extract_class_signature(java_code)
    if class_signature:
        class_info['class_signature'] = class_signature

    # 패키지 추출
    package_match = re.search(r'package\s+([\w\.]+);', java_code)
    if package_match:
        class_info['package'] = package_match.group(1)

    # import 추출
    imports = re.findall(r'import\s+([\w\.]+);', java_code)
    class_info['imports'].extend(imports)

    # 클래스 정보 추출 (class, interface, enum, abstract class 등)
    class_match = re.search(r'(class|interface|enum|abstract\s+class)\s+(\w+)', java_code)
    if class_match:
        class_info['class_type'] = class_match.group(1)
        class_info['class_name'] = class_match.group(2)

    # extends 추출
    extends_match = re.search(r'extends\s+(\w+)', java_code)
    if extends_match:
        class_info['extends'] = extends_match.group(1)

    # implements 추출
    implements_match = re.search(r'implements\s+([\w\s,]+)', java_code)
    if implements_match:
        class_info['implements'] = [imp.strip() for imp in implements_match.group(1).split(',')]

    return class_info

def extract_class_signature(java_code: str) -> Optional[str]:
    """
    주어진 Java 파일에서 클래스 시그니처를 추출합니다.
    """
    class_signature_pattern = re.compile(r'^\s*(public|protected|private)?\s*(abstract|final)?\s*class\s+(\w+)(\s+extends\s+\w+)?(\s+implements\s+[\w, ]+)?', re.MULTILINE)
    match = class_signature_pattern.search(java_code)
    if match:
        return match.group(0)  # 전체 매치된 클래스 시그니처 반환
    else:
        return None


def extract_method_code(java_code: str, start_pos: int) -> str:
    """
    주어진 Java 코드에서 메서드 본문을 추출합니다.

    :param java_code: Java 코드 문자열
    :param start_pos: 메서드 시작 위치
    :return: 메서드 본문 문자열
    """
    code_lines = java_code.splitlines()
    method_code_lines = []
    brace_count = 0
    in_method = False

    for i in range(start_pos, len(code_lines)):
        line = code_lines[i].strip()

        # 중괄호로 시작과 끝을 체크
        brace_count += line.count('{')
        brace_count -= line.count('}')

        # 메서드 시작
        if '{' in line and not in_method:
            in_method = True

        if in_method:
            method_code_lines.append(line)

        # 중괄호가 모두 닫혔다면 메서드 종료
        if in_method and brace_count == 0:
            break

    return '\n'.join(method_code_lines)


# 메서드 정보 추출 함수
def extract_methods_from_java(java_code: str) -> list[dict[str, str]]:
    """
    주어진 Java 코드에서 메서드 정보를 추출합니다.

    :param java_code: Java 코드 문자열
    :return: 메서드 정보의 리스트
    """
    methods = []

    # 메서드 시그니처 찾기 (public, private, protected 등 접근제어자 포함)
    method_pattern = re.compile(r'\b(public|private|protected)?\s*(static)?\s*([\w<>\[\]]+)\s+(\w+)\s*\([^)]*\)\s*(throws\s+[\w\s,]+)?\s*\{')

    for match in method_pattern.finditer(java_code):
        return_type = match.group(3)
        method_name = match.group(4)
        parameters = match.group(5)

        # 메서드의 시작 위치
        start_pos = match.start()

        # 메서드 본문 추출
        method_code = extract_method_code(java_code, java_code[:start_pos].count('\n'))

        # 메서드 정보 저장
        method_info = {
            'name': method_name,
            'return_type': return_type,
            'parameters': parameters,
            'code': method_code
        }
        methods.append(method_info)

    return methods


def parse_java_file(java_code: str) -> tuple[dict[str, Optional[str]], list[dict[str, str]]]:
    """
    Java 코드를 파싱하여 클래스 정보와 메서드 정보를 추출합니다.

    :param java_code: Java 코드 문자열
    :return: 클래스 정보와 메서드 정보의 튜플
    """
    # 주석 제거
    java_code = remove_comments(java_code)
    
    # # 파일 열기 (쓰기 모드)
    # with open("java_x_comment.java", "w") as file:
    #     # 파일에 쓰기
    #     file.write(java_code)

    # 클래스 정보 추출
    class_info = extract_class_info(java_code)

    # 메서드 정보 추출
    methods = extract_methods_from_java(java_code)
    class_info['methods'] = [method['name'] for method in methods]
    class_info['method_count'] = len(methods)

    # 파일의 최종 수정일 가져오기 #TODO 상위 프로세스로 move
    # last_modified = os.path.getmtime(file_path)
    # class_info['last_modified'] = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')

    return class_info, methods

def parse_java_directory(directory_path: str, output_file: str) -> None:
    """
    주어진 디렉토리 내의 모든 Java 파일을 파싱하여 클래스 정보와 메서드 정보를 추출하고 결과를 출력 파일에 저장합니다.

    :param directory_path: Java 파일이 있는 디렉토리 경로
    :param output_file: 결과를 저장할 출력 파일 경로
    """
    # 출력 파일 열기 (쓰기 모드)
    with open(output_file, 'w', encoding='utf-8') as f_out:
        # 디렉토리 내의 모든 폴더 및 파일을 재귀적으로 탐색
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                # 확장자가 .java인 파일에 대해 처리
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    f_out.write(f"Parsing file: {file_path}\n")
                    f_out.write("=" * 40 + "\n")

                    # Java 파일 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        java_code = f.read()
                        
                    # Java 파일을 파싱하여 클래스 정보 및 메서드 정보 추출
                    class_info, methods = parse_java_file(java_code)

                    # 클래스 정보 출력
                    f_out.write("Class Info:\n")
                    f_out.write(str(class_info) + "\n")
                    
                    # 메서드 정보 출력
                    f_out.write("\nMethods:\n")
                    for method in methods:
                        f_out.write(f"Method: {method['name']}\n")
                        f_out.write(f"Return Type: {method['return_type']}\n")
                        f_out.write(f"Parameters: {method['parameters']}\n")
                        f_out.write(f"Code:\n{method['code']}\n")
                        f_out.write("-" * 40 + "\n")
                    
                    f_out.write("\n\n")  # 파일 간 구분을 위한 공백 추가

# 테스트용 메인 함수
if __name__ == '__main__':
    directory_path = "/app/rag_server/data/input/program"  # 실제 Java 파일 경로
    output_file = "output.txt"  # 결과를 저장할 출력 파일 경로

    # 디렉토리 내 모든 Java 파일에 대해 파싱 수행 및 결과를 파일에 쓰기
    parse_java_directory(directory_path, output_file)
    
    # # Java 파일 읽기
    # with open("java_x_comment.java", 'r', encoding='utf-8') as f:
    #     java_code = f.read()
        
    #     extract_methods_from_java(java_code)



def should_skip_by_line_count(function_body: str, max_lines: int = 3) -> bool:
    """
    함수의 라인 수를 기준으로 건너뛸지 여부를 확인합니다.
    Args:
        function_body (str): 함수 본문 문자열
        max_lines (int): 건너뛰기 전 허용되는 최대 라인 수
    
    Returns:
        bool: 함수를 건너뛰어야 하면 True, 그렇지 않으면 False
    """
    # 함수 본문을 라인 단위로 분할
    lines = function_body.split("\n")
    
    # 빈 줄과 주석만 있는 줄 제거
    meaningful_lines = [
        line for line in lines 
        if line.strip() and not line.strip().startswith("//")
    ]

    # 의미있는 라인 수가 max_lines 이하인지 확인
    return len(meaningful_lines) <= max_lines

# # Example usage:
# if __name__ == "__main__":
#     # Sample function body as a string
#     sample_function_body = """
#     def example_function():
#         # This is an example function
#         return 42
#     """
#     # Check if the function should be skipped
#     skip = should_skip_by_line_count(sample_function_body, max_lines=3)
#     if skip:
#         print("Function skipped.")
#     else:
#         print("Function processed.")

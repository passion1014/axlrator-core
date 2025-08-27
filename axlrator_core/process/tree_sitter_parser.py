# 필요한 모듈 설치
# pip install git+https://github.com/tree-sitter/py-tree-sitter.git@v0.20.1
# git clone https://github.com/tree-sitter/tree-sitter-java.git

# axlrator-core/
# ├── vendor/
# │   └── tree-sitter-java/         <-- 여기 clone
# └── build/
#     └── my-languages.so           <-- 자동 생성됨

# # Java 파서 빌드 (최초 1회만 실행하면 됨)
# Language.build_library(
#     'build/my-languages.so',  # 출력 위치
#     ['vendor/tree-sitter-java']  # Java 파서 경로
# )


from tree_sitter import Language, Parser
from charset_normalizer import from_bytes
import json
import os

class JavaASTParser:
    def __init__(self, lib_path='build/my-languages.so'):
        self.language = Language(lib_path, 'java')
        self.parser = Parser()
        self.parser.set_language(self.language)

    def _parse_tree_from_file(self, file_path):
        with open(file_path, 'rb') as f:
            source_code = f.read()
        return self.parser.parse(source_code)

    def parse_file(self, file_path):
        """파일을 파싱하여 S-expression 형태의 AST 반환"""
        tree = self._parse_tree_from_file(file_path)
        return tree.root_node.sexp()

    def extract_methods(self, file_path):
        """Java 파일에서 메서드 이름 목록을 추출"""
        tree = self._parse_tree_from_file(file_path)
        methods = []

        def walk(node):
            if node.type == 'method_declaration':
                for child in node.children:
                    if child.type == 'identifier':
                        methods.append(child.text.decode())
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return methods

    def find_control_structures(self, file_path):
        """제어 구조(if, for, while)를 추출"""
        tree = self._parse_tree_from_file(file_path)
        found = []

        def walk(node):
            if node.type in ('if_statement', 'for_statement', 'while_statement'):
                found.append({
                    'type': node.type,
                    'start': node.start_point,
                    'end': node.end_point
                })
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return found

    def detect_long_methods(self, file_path, max_lines=30):
        """지정한 줄 수보다 긴 메서드를 탐지"""
        tree = self._parse_tree_from_file(file_path)
        long_methods = []

        def get_method_name(node):
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode()
            return '<unknown>'

        for node in tree.root_node.children:
            if node.type == 'method_declaration':
                line_span = node.end_point[0] - node.start_point[0]
                if line_span > max_lines:
                    long_methods.append({
                        'name': get_method_name(node),
                        'lines': line_span
                    })

        return long_methods

    def parse_as_json(self, file_path):
        """AST를 JSON(dict) 형식으로 반환"""
        tree = self._parse_tree_from_file(file_path)

        def _ast_to_dict(node):
            return {
                'type': node.type,
                'start': node.start_point,
                'end': node.end_point,
                'children': [_ast_to_dict(c) for c in node.children]
            }

        return _ast_to_dict(tree.root_node)

    def extract_variables(self, file_path):
        """Java 파일에서 변수 이름 목록을 추출"""
        tree = self._parse_tree_from_file(file_path)
        variables = []

        def walk(node):
            if node.type == 'variable_declarator':
                for child in node.children:
                    if child.type == 'identifier':
                        variables.append(child.text.decode())
            for child in node.children:
                walk(child)

        walk(tree.root_node)
        return variables

    def _decode_source_code(self, raw_bytes):
        match = from_bytes(raw_bytes).best()
        if match:
            print("[debug] Detected encoding:", match.encoding)
            try:
                decoded = match.output().decode(errors='ignore')
            except:
                try:
                    decoded = raw_bytes.decode('utf-16', errors='ignore')
                except:
                    decoded = raw_bytes.decode('utf-8', errors='ignore')
        else:
            try:
                decoded = raw_bytes.decode('utf-16', errors='ignore')
            except:
                decoded = raw_bytes.decode('utf-8', errors='ignore')
        # 특수 문자 제거
        return decoded.replace('\x00', '').replace('\uFFFD', '')

    def extract_methods_with_body(self, file_path):
        """메서드 이름과 메서드 본문 코드를 추출"""
        with open(file_path, 'rb') as f:
            source_code = f.read()
        
        source_text = self._decode_source_code(source_code)
        
        tree = self.parser.parse(source_text.encode())
        root = tree.root_node

        methods = []

        def walk(node):
            if node.type == 'method_declaration':
                name = '<unknown>'
                for child in node.children:
                    if child.type == 'identifier':
                        name = child.text.decode()
                        break
                method_code = source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
                methods.append({
                    'name': name,
                    'body': method_code
                })
            for child in node.children:
                walk(child)

        walk(root)
        return methods

    def build_call_tree(self, file_path):
        """메서드 호출 관계를 분석하여 call tree JSON 생성"""
        with open(file_path, 'rb') as f:
            source_code = f.read()
        tree = self.parser.parse(source_code)
        root = tree.root_node

        call_tree = {}

        def walk(node, current_method=None):
            if node.type == 'method_declaration':
                for child in node.children:
                    if child.type == 'identifier':
                        current_method = child.text.decode()
                        call_tree[current_method] = []
                        break
            elif node.type == 'method_invocation' and current_method:
                for child in node.children:
                    if child.type == 'identifier':
                        call_tree[current_method].append(child.text.decode())
                        break
            for child in node.children:
                walk(child, current_method)

        walk(root)

        return json.dumps(call_tree, indent=2)

    def build_project_call_tree(self, project_dir):
        """프로젝트 전체에서 메서드 호출 트리를 통합 생성"""
        full_call_tree = {}

        for root, _, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'rb') as f:
                            source_code = f.read()
                        tree = self.parser.parse(source_code)
                        root_node = tree.root_node

                        def walk(node, current_method=None):
                            if node.type == 'method_declaration':
                                for child in node.children:
                                    if child.type == 'identifier':
                                        current_method = child.text.decode()
                                        full_call_tree.setdefault(current_method, [])
                                        break
                            elif node.type == 'method_invocation' and current_method:
                                for child in node.children:
                                    if child.type == 'identifier':
                                        full_call_tree[current_method].append(child.text.decode())
                                        break
                            for child in node.children:
                                walk(child, current_method)

                        walk(root_node)
                    except Exception as e:
                        print(f"[warn] Failed to parse {file_path}: {e}")

        return json.dumps(full_call_tree, indent=2)

if __name__ == "__main__":
    parser = JavaASTParser()
    file_path = '/Users/passion1014/project/axlrator/axlrator-core/data/input/program/AdditonExtensionBCServiceImpl.java'

    # print("=== S-Expression ===")
    # print(parser.parse_file(file_path))

    # print("\n=== Method Names ===")
    # print(parser.extract_methods(file_path))

    # print("\n=== Control Structures ===")
    # print(parser.find_control_structures(file_path))

    # print("\n=== Long Methods ===")
    # print(parser.detect_long_methods(file_path, max_lines=30))

    # print("\n=== Variable Names ===")
    # print(parser.extract_variables(file_path))

    # print("\n=== AST as JSON ===")
    # import json
    # print(json.dumps(parser.parse_as_json(file_path), indent=2))
    
    # methods = parser.extract_methods_with_body(file_path)
    # for m in methods:
    #     print(f"▶ {m['name']}\n{m['body']}\n")

    # print("\n=== Call Tree ===")
    # print(parser.build_call_tree(file_path))

    # print("\n=== Project-wide Call Tree ===")
    print(parser.build_project_call_tree('/Users/passion1014/project/axlrator/axlrator-core/data/input/'))
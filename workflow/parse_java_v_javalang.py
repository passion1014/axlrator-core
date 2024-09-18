import os
import re
import time
import javalang

# Java 코드 예시
java_code = '''
public class HelloWorld {
    public static void main(String[] args) { // {{
        System.out.println("Hello, World"); // 이 주석은 { }가 포함되어 있습니다.
        if (true) {
            /* 여러 줄 주석
               {{{
                   
                   
                   
               }
            */
            System.out.println("This is a block");
        }
    }

    public void sayHello() { // {
        System.out.println("Hello");
    }

    private int add(int a, int b) {
        return a + b;
    }
}
'''

def extract_class_info(java_code):
    tokens = javalang.tokenizer.tokenize(java_code)
    parser = javalang.parser.Parser(tokens)
    tree = parser.parse()

    class_info = {
        'package': None,
        'class_type': None,
        'class_name': None,
        'extends': None,
        'implements': None,
        'imports': [],
        'fields': [],
        'methods': [],
        'method_count': 0,
        'last_modified': None  # 최종 수정일을 저장할 필드 추가
    }

    # 패키지 추출
    for _, node in tree.filter(javalang.tree.PackageDeclaration):
        class_info['package'] = node.name

    # import 문 추출
    # for _, node in tree.filter(javalang.tree.ImportDeclaration):
    #     class_info['imports'].append(node.path)
    # import 구문을 수동으로 추출 (정규 표현식 사용)
    import_lines = re.findall(r'import\s+([\w\.]+);', java_code)
    class_info['imports'].extend(import_lines)


    # 클래스 타입, 이름, extends, implements 추출
    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        class_info['class_type'] = 'class'  # 현재 예시는 클래스로 제한
        class_info['class_name'] = node.name
        if node.extends:
            class_info['extends'] = node.extends.name
        if node.implements:
            class_info['implements'] = [impl.name for impl in node.implements]

    # 클래스 필드(변수, 상수) 추출
    for _, node in tree.filter(javalang.tree.FieldDeclaration):
        field_type = node.type.name
        for declarator in node.declarators:
            class_info['fields'].append({
                'name': declarator.name,
                'type': field_type,
                'is_constant': node.modifiers and 'final' in node.modifiers,
                'modifiers': node.modifiers
            })

    # 메서드 추출
    for _, node in tree.filter(javalang.tree.MethodDeclaration):
        method_name = node.name
        class_info['methods'].append(method_name)

    # 메서드 갯수
    class_info['method_count'] = len(class_info['methods'])

    return class_info


# 메서드를 추출하는 함수 (AST 노드 기반)
def extract_methods_from_ast(java_code):
    # Java 코드 파싱
    tokens = javalang.tokenizer.tokenize(java_code)
    parser = javalang.parser.Parser(tokens)
    tree = parser.parse()

    methods = []
    # 메서드 노드 추출 (MethodDeclaration)
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        method_name = node.name  # 메서드 이름
        return_type = node.return_type.name if node.return_type else 'void'  # 반환 타입
        parameters = [(param.type.name, param.name) for param in node.parameters]  # 매개변수 목록
        
        # 메서드 시작 및 종료 위치
        start_pos = node.position.line
        # 메서드의 전체 소스코드를 추출
        method_code = extract_method_code(java_code, node)

        methods.append({
            'name': method_name,
            'return_type': return_type,
            'parameters': parameters,
            'start_line': start_pos,
            'code': method_code
        })
    
    return methods

# 실제 메서드의 코드를 추출하는 함수 (node의 위치를 기반으로 추출)
def extract_method_code(java_code, method_node):
    start_line = method_node.position.line - 1  # 메서드 시작 줄
    code_lines = java_code.splitlines()
    brace_count = 0
    method_code_lines = []
    in_method = False
    in_block_comment = False  # 블록 주석 내에 있는지 여부 추적

    for i, line in enumerate(code_lines):
        if i >= start_line:
            # 블록 주석 시작
            if '/*' in line:
                in_block_comment = True
            
            # 블록 주석 종료
            if '*/' in line:
                in_block_comment = False
                continue  # 블록 주석 라인은 처리하지 않음

            # 라인 주석은 무시
            if '//' in line:
                line = line.split('//')[0]

            # 블록 주석이 아닌 코드만 처리
            if not in_block_comment:
                if '{' in line:
                    brace_count += line.count('{')
                    in_method = True  # 메서드 시작
                if '}' in line:
                    brace_count -= line.count('}')

                method_code_lines.append(line)

                if in_method and brace_count == 0:  # 중괄호가 모두 닫히면 메서드 종료
                    break

    return '\n'.join(method_code_lines)

if __name__ == '__main__':
    # Java 코드에서 메서드 추출
    methods = extract_methods_from_ast(java_code)

    # 추출된 메서드 출력
    for method in methods:
        print(f"Method: {method['name']}")
        print(f"Return Type: {method['return_type']}")
        print(f"Parameters: {method['parameters']}")
        print(f"Start Line: {method['start_line']}")
        print(f"Code:\n{method['code']}")
        print("-" * 40)
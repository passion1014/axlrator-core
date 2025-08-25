# Tree-sitter Java AST 분석 예제

# 필요한 모듈 설치
# pip install git+https://github.com/tree-sitter/py-tree-sitter.git

from tree_sitter import Language, Parser

# Java 파서 빌드 (최초 1회만 실행하면 됨)
Language.build_library(
    'build/my-languages.so',  # 출력 위치
    ['vendor/tree-sitter-java']  # Java 파서 경로
)

# 빌드된 라이브러리에서 Java 파서 로딩
JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# 테스트할 Java 코드 입력
source_code = b"""
public class Hello {
  public static void main(String[] args) {
    System.out.println(\"Hello, world!\");
  }
}
"""

# AST 파싱
tree = parser.parse(source_code)
print(tree.root_node.sexp())

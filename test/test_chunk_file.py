import os
from datetime import datetime
import sys

# 현재 스크립트의 상위 경로를 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.process.content_chunker import chunk_file

# 테스트할 파일 경로 설정
# file_path = "/Users/passion1014/project/langchain/rag_data/is_modon_proto/src/main/java/com/modon/control/farm/service/FarmServiceImpl.java"
file_path = "/app/rag_data/is_modon_proto/src/main/java/com/modon/control/farm/service/FarmServiceImpl.java"
# 테스트용 파일 경로 출력
print(f"Testing chunk_file with file: {file_path}")

# 테스트 함수
def test_chunk_file(file_path):
    """Test the chunk_file function."""
    if os.path.isfile(file_path):
        print("Valid file path. Proceeding with chunking...")
        chunk_file(file_path)  # 실제 chunking 함수 호출
    else:
        print(f"Invalid file path: {file_path}. Please check the file and try again.")

# 테스트 실행
if __name__ == "__main__":
    test_chunk_file(file_path)
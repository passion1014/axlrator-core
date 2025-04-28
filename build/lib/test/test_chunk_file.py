import os
from datetime import datetime
import sys
import unittest

# 현재 스크립트의 상위 경로를 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from axlrator_core.process.content_chunker import chunk_file


class TestChunkFile(unittest.TestCase):
    def setUp(self):
        """테스트 전에 실행되는 메서드."""
        self.file_path = "/app/rag_data/is_modon_proto//src/main/java/com/modon/control/weather/controller/WeatherController.java"
        # file_path가 실제로 존재하는지 여부를 미리 확인
        print(f"Testing chunk_file with file: {self.file_path}")

    def test_chunk_file(self):
        """chunk_file 함수에 대한 테스트."""
        if os.path.isfile(self.file_path):
            print("Valid file path. Proceeding with chunking...")
            chunk_file(self.file_path)  # 실제 chunking 함수 호출
        else:
            self.fail(f"Invalid file path: {self.file_path}. Please check the file and try again.")


# 테스트 실행
# /app/rag_server 에서 아래 명령어 실행
# python -m unittest discover -s test -p "test_chunk_file.py"
if __name__ == "__main__":
    unittest.main()
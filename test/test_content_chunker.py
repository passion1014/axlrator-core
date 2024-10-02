import unittest
import os
import sys
# 현재 스크립트의 상위 경로를 추가
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/process')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from app.process.content_chunker import split_java_file, save_chunks

class TestContentChunker(unittest.TestCase):
    
    def setUp(self):
        """Setup test environment."""
        self.test_java_code = """
        public class TestClass {
            // This is a sample Java method
            public void firstMethod() {
                System.out.println("First Method");
            }

            /* Another method */
            private int secondMethod(int value) {
                return value * 2;
            }

            protected void thirdMethod() {
                // Third method content
                System.out.println("Third Method");
            }
        }
        """
        self.expected_chunks = [
            "public class TestClass {\n    // This is a sample Java method\n    public void firstMethod() {\n        System.out.println(\"First Method\");\n    }\n\n    /* Another method */",
            "    private int secondMethod(int value) {\n        return value * 2;\n    }\n",
            "    protected void thirdMethod() {\n        // Third method content\n        System.out.println(\"Third Method\");\n    }\n}"
        ]
        self.output_path = "test_chunks"


    def test_split_java_file(self):
        """Test splitting Java file into chunks."""
        chunks = split_java_file(self.test_java_code)
        
        # Check if the chunks match the expected result
        self.assertEqual(chunks, self.expected_chunks)
    
    def test_write_chunks(self):
        """Test if chunks are written to the output directory correctly."""
        chunks = split_java_file(self.test_java_code)
        save_chunks(chunks, self.output_path)

        # Check if the output path directory exists
        self.assertTrue(os.path.exists(self.output_path))

        # Check if the correct number of chunk files were created
        chunk_files = [f for f in os.listdir(self.output_path) if f.startswith('chunk_')]
        self.assertEqual(len(chunk_files), len(chunks))

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.output_path):
            for file in os.listdir(self.output_path):
                os.remove(os.path.join(self.output_path, file))
            os.rmdir(self.output_path)

if __name__ == "__main__":
    unittest.main(buffer=True)
    
# 실행 명령어
# python -m unittest discover -s test -p "test_content_chunker.py"

# 1.	python -m unittest:
# •	unittest 모듈을 실행하기 위해 Python의 -m 옵션을 사용합니다. 이 옵션은 해당 모듈을 실행 가능한 스크립트로 취급하여 실행하는 역할을 합니다.
# •	unittest는 Python의 기본 테스트 프레임워크로, 단위 테스트를 작성하고 실행하는 데 사용됩니다.
# 2.	discover:
# •	discover는 unittest에 내장된 기능으로, 특정 디렉토리에서 테스트를 자동으로 검색하고 실행합니다. 이 옵션을 통해 테스트 파일을 수동으로 지정하지 않고 지정된 디렉토리에서 자동으로 찾을 수 있습니다.
# 3.	-s test:
# •	-s는 --start-directory의 약어로, 테스트를 검색할 시작 디렉토리를 지정합니다.
# •	이 경우 test 디렉토리에서 테스트 파일을 찾도록 지정되어 있습니다. 즉, test 폴더에서 테스트를 검색합니다.
# 4.	-p "test_content_chunker.py":
# •	-p는 --pattern의 약어로, 테스트 파일 이름의 패턴을 지정합니다.
# •	"test_content_chunker.py"는 검색할 테스트 파일의 이름을 지정합니다. 이 패턴에 해당하는 파일을 찾게 됩니다.

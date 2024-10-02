# 현재 스크립트의 상위 경로를 추가
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 테스트 코드
from app.chain import create_summary_chain

# LangSmith 로그 업로드 비활성화 설정 추가
os.environ["LANGSMITH_LOGGING"] = "False"

def test_create_summary_chain():
    """Test the create_summary_chain function by providing a code chunk."""
    
    # 가상의 코드 청크
    code_chunk = """
    def reverse_string(s: str) -> str:
        chars = list(s)
        left, right = 0, len(chars) - 1
        while left < right:
            chars[left], chars[right] = chars[right], chars[left]
            left += 1
            right -= 1
        return ''.join(chars)
    """
    
    # create_summary_chain 호출
    summary_chain = create_summary_chain()

    # 요약 생성을 위한 프롬프트 입력
    inputs = {
        "CODE_CHUNK": code_chunk
    }
    
    # summary_chain 실행
    try:
        result = summary_chain.invoke(inputs)
        print("Summary Chain Output:")
        print(result)
    except Exception as e:
        print(f"Error during summary chain execution: {e}")

# 테스트 실행
if __name__ == "__main__":
    test_create_summary_chain()
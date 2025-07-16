from pydantic import BaseModel, Field
import re

# Pydantic 모델 정의
class AugmentedChunkMetadata(BaseModel):
    function_name: str = Field(description="Name of the function")
    summary: str = Field(description="Summary of the function's purpose")
    features: list[str] = Field(description="Key features or operations")
    related_questions: list[str] = Field(description="related questions")
    # code: str = Field(description="The original code chunk")

# Augmented Chunk 파싱 함수
def parse_augmented_chunk(text: str) -> AugmentedChunkMetadata:
    # 함수명 추출 - <function_name> 태그 사이의 내용을 가져옴
    function_name = re.search(r"<function_name>(.*?)</function_name>", text).group(1)
    
    # 요약 추출 - <summary> 태그 사이의 내용을 가져옴
    summary = re.search(r"<summary>(.*?)</summary>", text).group(1)
    
    # <features> 태그 블록만 추출
    features_block = re.search(r"<features>(.*?)</features>", text, re.DOTALL)
    if features_block:
        features = [
            f.strip() for f in re.findall(r"- (.*?)\n", features_block.group(1))
        ]
    else:
        features = []
    
    # related_questions 태그 전체 내용 추출
    related_block = re.search(
        r"<related_questions>(.*?)</related_questions>", text, re.DOTALL
    )
    if related_block:
        # 각 항목('- '로 시작하는 줄)을 리스트로 추출
        related_questions = [
            q.strip() for q in re.findall(r"- (.*?)\n", related_block.group(1))
        ]
    else:
        related_questions = []

    # code = re.search(r"<code>(.*?)</code>", text, re.DOTALL).group(1).strip()

    # JSON 변환을 위한 모델 인스턴스 생성
    return AugmentedChunkMetadata(
        function_name=function_name,
        summary=summary,
        features=features,
        related_questions=related_questions,
        # code=code
    )

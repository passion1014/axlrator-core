from pydantic import BaseModel, Field
import re

# Pydantic 모델 정의
class AugmentedChunkMetadata(BaseModel):
    function_name: str = Field(description="Name of the function")
    summary: str = Field(description="Summary of the function's purpose")
    features: list[str] = Field(description="Key features or operations")
    # code: str = Field(description="The original code chunk")

# Augmented Chunk 파싱 함수
def parse_augmented_chunk(text: str) -> AugmentedChunkMetadata:
    # 함수명 추출 - <function_name> 태그 사이의 내용을 가져옴
    function_name = re.search(r"<function_name>(.*?)</function_name>", text).group(1)
    
    # 요약 추출 - <summary> 태그 사이의 내용을 가져옴
    summary = re.search(r"<summary>(.*?)</summary>", text).group(1)
    
    # features 태그 전체 내용 추출 
    features = re.findall(r"<features>\s*-(.*?)\s*</features>", text, re.DOTALL)
    
    # features 목록에서 각 항목('-' 로 시작하는) 추출하여 공백 제거
    features = [feature.strip() for feature in re.findall(r"- (.*?)\n", text)]

    # code = re.search(r"<code>(.*?)</code>", text, re.DOTALL).group(1).strip()

    # JSON 변환을 위한 모델 인스턴스 생성
    return AugmentedChunkMetadata(
        function_name=function_name,
        summary=summary,
        features=features,
        # code=code
    )

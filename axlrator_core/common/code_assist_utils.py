import re
from typing import List, Dict

def extract_code_blocks(markdown_text: str) -> List[str]:
    print(f"######## markdown_text = {markdown_text}")

    # 마크다운 코드 블록 패턴
    pattern = r"```(?:\w+)?\n(.*?)```"
    code_blocks = re.findall(pattern, markdown_text, re.DOTALL)

    # 코드 블록이 하나라도 있으면 그것들만 반환
    if code_blocks:
        return [block.strip() for block in code_blocks]

    # 마크다운 코드 블록이 없으면 전체 텍스트를 반환
    return [markdown_text.strip()]

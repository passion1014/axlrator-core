import re
from typing import List, Dict

def extract_code_blocks(markdown_text: str) -> List[str]:
    # 대괄호가 텍스트에 포함되어 있으면 첫 번째 코드 블록만 반환
    if "[" in markdown_text and "]" in markdown_text:
        pattern = r"```(?:\w+)?\n(.*?)```"
        match = re.search(pattern, markdown_text, re.DOTALL)
        return [match.group(1).strip()] if match else []

    # 대괄호가 없으면 전체 코드 블록 추출
    pattern = r"```(?:\w+)?\n(.*?)```"
    code_blocks = re.findall(pattern, markdown_text, re.DOTALL)
    return [block.strip() for block in code_blocks]
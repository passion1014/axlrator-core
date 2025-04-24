import re
from typing import List, Dict
# 코드 블록 추출 함수
def extract_code_blocks(markdown_text: str) -> List[str]:
    pattern = r"```(?:\w+)?\n(.*?)```"
    code_blocks = re.findall(pattern, markdown_text, re.DOTALL)
    return [block.strip() for block in code_blocks]
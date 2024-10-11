import re

def extract_table_and_korean_name(text):
    # 정규표현식으로 영문명(테이블명)과 한글명을 각각 추출
    match = re.search(r'TABLE (\w+)\(([^)]+)\)', text)
    if match:
        table_name = match.group(1)  # 영문 테이블명
        korean_name = match.group(2)  # 한글명
        return table_name, korean_name
    return None, None

# 예시 텍스트
input_text = """
TABLE ZGU_GUAS_ISSU_CNTC( ){
CHNG_SRNO=변경일련번호, CNRC_MNNO=계약관리번호, QTRT=지분율, RPPR_NM=대표자명, SQNO=순번, SRNO=일련번호, TDNM=상호
}
"""

# 함수 실행
table_name, korean_name = extract_table_and_korean_name(input_text)

# 결과 출력
print("Table Name (영문명):", table_name)
print("Korean Name (한글명):", korean_name)
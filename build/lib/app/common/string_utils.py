
import re

def contains_sql_keyword(text):
    """입력된 텍스트에 SQL 예약어가 포함되어 있는지 확인"""

    # 기본적인 SQL 예약어 리스트
    SQL_KEYWORDS = {
        "SELECT", "FROM", "WHERE", "JOIN", "INNER", "OUTER", "LEFT", "RIGHT", "GROUP", "ORDER", "BY",
        "INSERT", "UPDATE", "DELETE", "INTO", "VALUES", "SET", "CREATE", "DROP", "ALTER", "TABLE", "INDEX",
        "UNION", "DISTINCT", "PRIMARY", "FOREIGN", "KEY", "DEFAULT", "CONSTRAINT", "CHECK", "REFERENCES",
        "EXISTS", "NULL", "NOT", "AND", "OR", "AS", "LIKE", "IN", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE", "END"
    }

    words = re.findall(r'\b\w+\b', text.upper())  # 대소문자 무시하고 단어 추출
    found_keywords = set(words) & SQL_KEYWORDS  # 예약어와 교집합 찾기
    return list(found_keywords) if found_keywords else None


def is_table_name(text):
    """영어 알파벳, 언더바, 콤마, 공백만 포함하는지 확인"""
    is_regex = bool(re.fullmatch(r'[A-Za-z_, ]*', text))
    is_sql_keyword = contains_sql_keyword(text)
    
    return is_regex and not is_sql_keyword
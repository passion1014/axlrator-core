import re
from html import escape
from typing import Annotated, List, Optional, Sequence, TypedDict
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph.message import add_messages

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


def is_table_name(text):
    """영어 알파벳, 언더바, 콤마, 공백만 포함하는지 확인"""

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


    is_regex = bool(re.fullmatch(r'[A-Za-z_, ]*', text))
    is_sql_keyword = contains_sql_keyword(text)
    
    return is_regex and not is_sql_keyword


def format_chat_history_tagsafe(
    chat_history: Annotated[Sequence[BaseMessage], add_messages]
) -> str:
    result = []
    for chat in chat_history:
        escape_content = escape( chat.content.strip() )
        
        if isinstance(chat, HumanMessage):
            result.append(f"<USER>\n{escape_content}\n</USER>")
            
        elif isinstance(chat, AIMessage):
            result.append(f"<ASSISTANT>\n{escape_content}\n</ASSISTANT>")
            
        elif isinstance(chat, SystemMessage):
            result.append(f"<SYSTEM>\n{escape_content}\n</SYSTEM>")

        else:
            print(f"######## Unknown message type: {type(chat)}")
            result.append(f"<UNKNOWN>\n{escape_content}\n</UNKNOWN>")
            
    return "\n\n".join(result)


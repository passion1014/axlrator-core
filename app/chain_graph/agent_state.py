"""Define the shared values."""

from typing import Dict, Optional, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated

class AgentState(TypedDict):
    """
    임시로 사용하는 데이터클래스
    - 데이터 저장을 주목적으로 하는 클래스, 모든 필드는 키워드 인자를 사용해야 함
    """

    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""

    # chat_history: List[Tuple[str, str]]
    question: str
    context: str
    response: str
    current_code: str # code assist를 위한 항목
    sql_request: str

class CodeAssistState(TypedDict):
    """
    코드 어시스트용 데이터클래스
    """
    prompt: str
    question: str
    context: Annotated[list[dict], "컨텍스트 조회 결과 리스트"]
    current_code: str
    response: str


class CodeAssistChatState(TypedDict):
    question: str
    current_code: str
    thread_id: str
    chat_history: Optional[list[Dict]] = None

class CodeAssistAutoCompletion(TypedDict):
    prompt: str
    current_code: str
    response: str


__all__ = [
    "AgentState",
    "CodeAssistState",
    "CodeAssistChatState",
]


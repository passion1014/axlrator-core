"""Define the shared values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated


@dataclass(kw_only=True)
class AgentState(TypedDict):
    """Main graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    """The messages in the conversation."""

    # chat_history: List[Tuple[str, str]]
    question: str
    context: str
    response: str
    current_code: str # code assist를 위한 항목
    sql_request: str


__all__ = [
    "AgentState",
]



from typing import List, Tuple, TypedDict, Annotated


class AgentState(TypedDict):
    ''' 
    에이전트의 현재 상태를 나타내는 클래스입니다.

    Attributes:
        chat_history (List[Tuple[str, str]]): 대화 기록을 저장하는 리스트입니다. 
                                              각 튜플은 (대화자, 대화내용) 형식입니다.
        question (str): 현재 처리 중인 질문입니다.
        context (str): 질문에 대한 관련 컨텍스트 정보입니다.
        response (str): 에이전트가 생성한 응답입니다.
    '''
    chat_history: List[Tuple[str, str]]
    question: str
    context: str
    response: str

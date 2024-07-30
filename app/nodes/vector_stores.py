from app.database import load_vector_database
from app.nodes.core import AgentState
from app.prompts import CONDENSE_QUESTION_PROMPT, ANSWER_PROMPT
from app.utils import combine_documents, format_chat_history
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage

'''
아래 조건을 참고해서 faiss vectorDB를 읽는 함수를 만들어줘
- langGraph 방식
- 아래 AgentStat를 사용하는 함수
    class AgentState(TypedDict):
        chat_history: List[Tuple[str, str]]
        question: str
        context: str
        response: str


retrive_db 함수를 만들어서 faiss vectorDB를 저장하는 함수를 만들어
'''


def retrive_db(state: AgentState) -> AgentState:
    openai_model = ChatOpenAI(temperature=0)
    claude_model = ChatAnthropic(model="claude-3-sonnet-20240229")

    retriever = load_vector_database()

    # 프롬프트 생성
    chat_history = format_chat_history(state['chat_history'])
    standalone_question_prompt = CONDENSE_QUESTION_PROMPT.format(
        chat_history=chat_history, question=state['question']
    )
    standalone_question_response = openai_model.invoke(standalone_question_prompt)
    standalone_question = standalone_question_response.content if isinstance(standalone_question_response, AIMessage) else str(standalone_question_response)
    docs = retriever.get_relevant_documents(standalone_question)
    state['context'] = combine_documents(docs)
    return state



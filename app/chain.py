from typing import List, Tuple, TypedDict, Annotated
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langserve.pydantic_v1 import BaseModel, Field
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from app.database import load_vector_database
from app.prompts import CONDENSE_QUESTION_PROMPT, ANSWER_PROMPT
from app.utils import combine_documents, format_chat_history
from langgraph.graph import StateGraph, END
from langfuse.decorators import observe, langfuse_context



class ChatHistory(BaseModel):
    chat_history: List[Tuple[str, str]] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "question"}},
    )
    question: str

class AgentState(TypedDict):
    chat_history: List[Tuple[str, str]]
    question: str
    context: str
    response: str

def create_chain():
    # retriever 선언
    retriever = load_vector_database()
    
    # 사용할 모델 선언
    # model = ChatOpenAI(temperature=0)
    # model = ChatAnthropic(model="claude-3-sonnet-20240229")
    model = ChatOllama(model="EEVE-Korean-10.8B:latest")

    def get_context(state: AgentState) -> AgentState:
        chat_history = format_chat_history(state['chat_history'])
        standalone_question_prompt = CONDENSE_QUESTION_PROMPT.format(
            chat_history=chat_history, question=state['question']
        )
        standalone_question_response = model.invoke(standalone_question_prompt)
        standalone_question = standalone_question_response.content if isinstance(standalone_question_response, AIMessage) else str(standalone_question_response)
        docs = retriever.get_relevant_documents(standalone_question)
        state['context'] = combine_documents(docs)
        return state

    def generate_response(state: AgentState) -> AgentState:        
        prompt = ANSWER_PROMPT.format(context=state['context'], question=state['question'])
        response = model.invoke(prompt) 

        state['response'] = response

        return state

    workflow = StateGraph(AgentState)

    workflow.add_node("get_context", get_context)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("get_context")
    workflow.add_edge("get_context", "generate_response")
    workflow.add_edge("generate_response", END)

    chain = workflow.compile()
        
    return chain.with_types(input_type=ChatHistory)
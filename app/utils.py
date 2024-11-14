from typing import List, Tuple
from langchain_core.prompts import format_document
from app.prompts.prompts import DEFAULT_DOCUMENT_PROMPT
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def get_embedding_model():
    '''
    임베딩 모델 가져오기
    '''
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
    
    embeddings = None

    if embedding_model in ['nomic-embed-text']:
        from langchain.embeddings import OllamaEmbeddings
        
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://host.docker.internal:11434"  # Ollama의 기본 URL입니다.
        )
        
    elif  embedding_model in ['text-embedding-3-large']:
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(model=embedding_model)
        
    else:
        raise ValueError("ENV 환경변수가 설정되지 않았습니다.")

    return embeddings


def get_llm_model():
    '''
    LLM 모델 가져오기
    '''
    llm_model = os.getenv("LLM_MODEL_NAME")

    model = None

    if llm_model in ['EEVE-Korean-10.8B:latest', 'gemma2:9b', 'gemma2:27b']: # ChatOllama
        from langchain_community.chat_models import ChatOllama
        model = ChatOllama(model=llm_model, base_url="http://host.docker.internal:11434")
        
    elif llm_model in ['gpt-3.5-turbo']: # ChatOpenAI
        from langchain_community.chat_models import ChatOpenAI
        model = ChatOpenAI(model=llm_model)

    elif llm_model in ['claude-3-sonnet-20240229']: # ChatAnthropic
        from langchain_anthropic import ChatAnthropic
        model = ChatAnthropic(
            model=llm_model,
            # temperature=0,
            # max_tokens=1024,
            # timeout=None,
            # max_retries=2,
        )                
    else:
        raise ValueError("ENV 환경변수가 설정되지 않았습니다.")
    
    return model


def combine_documents(docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


def merge_chat_history(chat_history: List[Tuple]) -> str:
    buffer = ""
    for dialogue_turn in chat_history:
        human = "Human: " + dialogue_turn[0]
        ai = "Assistant: " + dialogue_turn[1]
        buffer += "\n" + "\n".join([human, ai])
    return buffer

def ensure_dict(x):
    if isinstance(x, dict):
        return x
    elif hasattr(x, "__dict__"):
        return x.__dict__
    else:
        return {"input": x}
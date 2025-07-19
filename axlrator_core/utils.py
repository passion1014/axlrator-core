import re
from typing import List, Tuple
from langchain_core.prompts import format_document
import os

def get_embedding_model():
    '''
    임베딩 모델 가져오기
    '''
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
    ollama_url = os.getenv("OLLAMA_URL")
    embeddings = None

    if embedding_model in ['nomic-embed-text', 'bge-m3:latest']:
        from langchain.embeddings import OllamaEmbeddings
        
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=ollama_url  # Ollama의 기본 URL입니다.
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
    ollama_url = os.getenv("OLLAMA_URL")
    model = None

    if llm_model in ['gemma3:27b','EEVE-Korean-10.8B:latest', 'gemma2:9b', 'gemma2:27b', 'llama3.3:latest', 'qwq:latest', 'phi4:latest']: # ChatOllama
        from langchain_community.chat_models import ChatOllama
        model = ChatOllama(model=llm_model, base_url=ollama_url)
        
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

def get_rerank_model():
    '''
    Rerank 모델 가져오기
    '''
    rerank_model_name = os.getenv("RERANK_MODEL_NAME")
    model = None

    if rerank_model_name in ['BAAI/bge-reranker-v2-m3']:
        if get_server_type() == "P":
            model_kwargs = {}
        else:
            # model_kwargs = {'device': 'cpu', 'trust_remote_code': True, "batch_size": 2,}
            model_kwargs = {'device': 'cpu',}

        from langchain_community.cross_encoders import HuggingFaceCrossEncoder
        model = HuggingFaceCrossEncoder(model_name=rerank_model_name, model_kwargs=model_kwargs)
    else:
        raise ValueError("지원되지 않는 Rerank 모델입니다.")
    
    return model

def get_server_type():
    """
    서버 타입을 .env 파일에서 읽어옵니다.
    """
    environment = os.getenv("ENVIRONMENT")
    if environment == "production":
        return "P"
    elif environment == "development":
        return "D"
    else:
        raise ValueError("알 수 없는 서버 타입입니다.")

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

def remove_markdown_code_block(text: str) -> str:
    # 이 함수는 주어진 텍스트에서 마크다운 코드 블록을 제거합니다.
    # 마크다운 코드 블록은 ```로 시작하고 끝나는 부분을 의미합니다.
    return re.sub(r"^```[\w]*\n|\n```$", "", text)

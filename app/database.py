from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import OllamaEmbeddings
from app.config import FAISS_INDEX_PATH, setup_logging

logger = setup_logging()

def load_vector_database():
    # embeddings = OpenAIEmbeddings()
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11434"  # Ollama의 기본 URL입니다. 필요에 따라 변경하세요.
    )
    
    try:
        db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        logger.info(f"----- FAISS index loaded from: {FAISS_INDEX_PATH}")
        
    except ValueError as e:
        logger.error(f"Error loading FAISS index: {e}")
        db = FAISS.load_local(FAISS_INDEX_PATH, allow_dangerous_deserialization=True)
        db.embeddings = embeddings

    retriever = db.as_retriever(search_kwargs={"k": 1})    
    logger.info(f"----- Number of items in FAISS index: {len(db.index_to_docstore_id)}")
    
    return retriever
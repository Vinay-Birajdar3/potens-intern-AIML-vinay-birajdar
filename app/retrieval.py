from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app import config


_embedding_model = None
_vector_db = None


def get_embedding_model():
    """
    Load the embedding model only when needed.
    """
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL
        )

    return _embedding_model


def get_vector_db():
    """
    Load the Chroma database only when needed.
    """
    global _vector_db

    if _vector_db is None:
        _vector_db = Chroma(
            persist_directory=config.CHROMA_DB_PATH,
            embedding_function=get_embedding_model()
        )

    return _vector_db


def retrieve_documents(query: str):
    """
    Retrieve the most relevant chunks.
    """
    db = get_vector_db()

    results = db.similarity_search_with_score(
        query=query,
        k=config.TOP_K
    )

    return results
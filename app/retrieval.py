from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app import config


embedding_model = HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL
)


def get_vector_db():
    """
    Load the existing Chroma database.
    """

    return Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embedding_model
    )


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
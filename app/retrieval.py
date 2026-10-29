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
            persist_directory=str(config.resolve_chroma_db_path()),
            collection_name=config.CHROMA_COLLECTION,
            embedding_function=get_embedding_model(),
        )

    return _vector_db


def retrieve_documents(query: str):
    """
    Retrieve unique, sufficiently close chunks from the existing vector index.

    Chroma returns squared-L2 distances for this index; lower scores are better.
    """
    normalized_query = " ".join(query.split())
    if not normalized_query:
        return []

    db = get_vector_db()
    results = db.similarity_search_with_score(
        query=normalized_query,
        k=max(config.TOP_K, config.RETRIEVAL_FETCH_K),
    )

    unique_results = []
    seen_chunks = set()

    for document, distance in results:
        if distance > config.MAX_RETRIEVAL_DISTANCE:
            continue

        normalized_content = " ".join(document.page_content.casefold().split())
        if not normalized_content or normalized_content in seen_chunks:
            continue

        seen_chunks.add(normalized_content)
        unique_results.append((document, distance))
        if len(unique_results) == config.TOP_K:
            break

    return unique_results
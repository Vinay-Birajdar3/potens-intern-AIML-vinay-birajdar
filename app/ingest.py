import gc
import hashlib
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import config

logger = logging.getLogger(__name__)
_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL
        )
    return _embedding_model


def load_documents():
    documents_path = Path(config.DOCUMENTS_PATH)
    if not documents_path.is_dir():
        raise FileNotFoundError(f"Documents directory does not exist: {documents_path}")

    loader = PyPDFDirectoryLoader(config.DOCUMENTS_PATH)
    documents = loader.load()

    if not documents:
        raise ValueError(f"No readable PDF pages were found in {documents_path}.")

    logger.info("Loaded %s PDF pages.", len(documents))
    return documents


def split_documents(documents):
    """
    Split pages into chunks and retain normalized source metadata for filtering.
    """
    if config.CHUNK_SIZE <= 0 or not 0 <= config.CHUNK_OVERLAP < config.CHUNK_SIZE:
        raise ValueError("CHUNK_SIZE must be positive and CHUNK_OVERLAP smaller than it.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = text_splitter.split_documents(documents)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i + 1
        source = str(chunk.metadata.get("source", "Unknown"))
        chunk.metadata["source_name"] = source.replace("\\", "/").rsplit("/", 1)[-1]

    if not chunks:
        raise ValueError("No non-empty text chunks were created from the PDF pages.")

    logger.info("Created %s text chunks.", len(chunks))

    return chunks


def create_vector_store(chunks):
    """
    Build a replacement index beside the active one and swap only after success.
    """
    if not chunks:
        raise ValueError("Refusing to replace the vector index with an empty index.")

    target = Path(config.CHROMA_DB_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not target.is_dir():
        raise NotADirectoryError(f"Vector index path is not a directory: {target}")

    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=target.parent))
    backup = None
    vector_db = None

    try:
        chunk_ids = [
            hashlib.sha256(
                (
                    f"{chunk.metadata.get('source_name', 'Unknown')}:"
                    f"{chunk.metadata.get('page', 0)}:{chunk.metadata.get('chunk_id')} "
                    f"{chunk.page_content}"
                ).encode("utf-8")
            ).hexdigest()
            for chunk in chunks
        ]
        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("Duplicate chunk IDs were generated during ingestion.")

        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=get_embedding_model(),
            ids=chunk_ids,
            collection_name=config.CHROMA_COLLECTION,
            persist_directory=str(staging),
        )
        if not (staging / "chroma.sqlite3").is_file():
            raise RuntimeError("Chroma did not create a persistent vector index.")

        del vector_db
        vector_db = None
        gc.collect()

        if target.exists():
            backup = Path(
                tempfile.mkdtemp(prefix=f".{target.name}.backup-", dir=target.parent)
            )
            backup.rmdir()
            os.replace(target, backup)

        try:
            os.replace(staging, target)
        except OSError:
            if backup is not None and backup.exists() and not target.exists():
                os.replace(backup, target)
            raise

        if backup is not None:
            shutil.rmtree(backup)
        logger.info("Stored %s chunks in %s.", len(chunks), target)
        return None
    finally:
        if vector_db is not None:
            del vector_db
            gc.collect()
        if staging.exists():
            shutil.rmtree(staging)


def main():

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger.info("Loading documents...")
    documents = load_documents()

    logger.info("Splitting documents...")
    chunks = split_documents(documents)

    logger.info("Creating vector database...")
    create_vector_store(chunks)

    logger.info("Ingestion completed successfully.")


if __name__ == "__main__":
    main()
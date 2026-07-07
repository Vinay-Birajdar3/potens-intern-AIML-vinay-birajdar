import os
import shutil
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import config


embedding_model = HuggingFaceEmbeddings(
    model_name=config.EMBEDDING_MODEL
)


def load_documents():
    loader = PyPDFDirectoryLoader(config.DOCUMENTS_PATH)
    documents = loader.load()

    print(f"Loaded {len(documents)} pages.")

    return documents

def split_documents(documents):
    """
    Split documents into smaller chunks for better retrieval.
    """

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

    print(f"Created {len(chunks)} chunks.")

    return chunks

def create_vector_store(chunks):
    """
    Create a Chroma vector database from document chunks.
    """

    # Delete old database if it exists
    if os.path.exists(config.CHROMA_DB_PATH):
        shutil.rmtree(config.CHROMA_DB_PATH)

    # Create Chroma vector database
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=config.CHROMA_DB_PATH
    )

    print(f"Stored {len(chunks)} chunks in ChromaDB.")

    return vector_db


def main():

    print("Loading documents...")
    documents = load_documents()

    print("Splitting documents...")
    chunks = split_documents(documents)

    print("Creating vector database...")
    create_vector_store(chunks)

    print("Ingestion completed successfully!")


if __name__ == "__main__":
    main()
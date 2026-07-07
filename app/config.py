from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Project Paths
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")
CHROMA_DB_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Chunking Strategy
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Number of retrieved chunks
TOP_K = 4
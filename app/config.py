from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env
load_dotenv()

# API settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APP_API_KEY = os.getenv("APP_API_KEY")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
if APP_ENV not in {"development", "production", "test"}:
    raise ValueError("APP_ENV must be development, production, or test.")

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "1"))
GROQ_MAX_COMPLETION_TOKENS = int(os.getenv("GROQ_MAX_COMPLETION_TOKENS", "512"))
if GROQ_TIMEOUT_SECONDS <= 0 or GROQ_MAX_RETRIES < 0 or GROQ_MAX_COMPLETION_TOKENS <= 0:
    raise ValueError("Groq timeout, retry, and completion-token settings are invalid.")

LIVE_EVALUATION_ENABLED = os.getenv("LIVE_EVALUATION_ENABLED", "true").strip().lower() in {
    "1",
    "true",
    "yes",
}
RAG_EVAL_REPORT_PATH = os.getenv(
    "RAG_EVAL_REPORT_PATH",
    "../rag-evaluations/rag_evaluation_report.xlsx",
)

# Project Paths
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.getenv("CHROMA_PATH", "./chroma_db"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "langchain")

# Embedding Model
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

# Chunking Strategy
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Retrieval and request limits
TOP_K = int(os.getenv("TOP_K", "4"))
RETRIEVAL_FETCH_K = int(os.getenv("RETRIEVAL_FETCH_K", str(TOP_K * 4)))
MAX_RETRIEVAL_DISTANCE = float(os.getenv("MAX_RETRIEVAL_DISTANCE", "1.0"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "6000"))
MAX_QUESTION_CHARS = int(os.getenv("MAX_QUESTION_CHARS", "2000"))

if CHUNK_SIZE <= 0 or not 0 <= CHUNK_OVERLAP < CHUNK_SIZE:
    raise ValueError("CHUNK_SIZE must be positive and CHUNK_OVERLAP smaller than it.")
if TOP_K <= 0 or RETRIEVAL_FETCH_K < TOP_K:
    raise ValueError("RETRIEVAL_FETCH_K must be greater than or equal to positive TOP_K.")
if MAX_RETRIEVAL_DISTANCE <= 0 or MAX_CONTEXT_CHARS <= 0 or MAX_QUESTION_CHARS <= 0:
    raise ValueError("Retrieval distance and text limits must be positive.")


def resolve_chroma_db_path() -> Path:
    target = Path(CHROMA_DB_PATH)
    if (target / "chroma.sqlite3").is_file():
        return target

    legacy_path = target.parent
    if target.name == "index" and (legacy_path / "chroma.sqlite3").is_file():
        return legacy_path

    return target

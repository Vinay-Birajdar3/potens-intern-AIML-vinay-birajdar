from functools import lru_cache

from groq import Groq

from app import config


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required to call the language model.")

    return Groq(
        api_key=config.GROQ_API_KEY,
        timeout=config.GROQ_TIMEOUT_SECONDS,
        max_retries=config.GROQ_MAX_RETRIES,
    )

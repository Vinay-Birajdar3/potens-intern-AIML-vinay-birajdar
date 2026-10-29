import logging
import sqlite3

import chromadb
from fastapi import FastAPI, HTTPException, status

from app import config
from app.api import router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PolicyLens API",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "PolicyLens API is running!"
    }


@app.get("/health/live")
def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
def readiness():
    if config.APP_ENV == "production" and (
        not config.APP_API_KEY or len(config.APP_API_KEY) < 32
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured securely.",
        )

    database_path = config.resolve_chroma_db_path()
    if not (database_path / "chroma.sqlite3").is_file():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector index is not available.",
        )

    try:
        client = chromadb.PersistentClient(path=str(database_path))
        collection = client.get_collection(name=config.CHROMA_COLLECTION)
        if collection.count() == 0:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The vector index is empty.",
            )
    except (chromadb.errors.ChromaError, OSError, sqlite3.Error) as exc:
        logger.exception("Vector index readiness check failed.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector index is unavailable.",
        ) from exc

    return {"status": "ready"}
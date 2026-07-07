from fastapi import FastAPI

from app.api import router

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
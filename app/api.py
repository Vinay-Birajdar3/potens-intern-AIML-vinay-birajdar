from fastapi import APIRouter
from pydantic import BaseModel

from app.retrieval import retrieve_documents
from app.rag import generate_answer
from app.contradiction import check_contradiction
from app.translation import (
    detect_language,
    translate_to_english,
    translate_from_english
)

router = APIRouter()


# -----------------------------
# Request Models
# -----------------------------

class AskRequest(BaseModel):
    question: str


class ContradictRequest(BaseModel):
    document1: str
    document2: str
    topic: str


# -----------------------------
# Ask Endpoint
# -----------------------------

@router.post("/ask")
def ask_question(request: AskRequest):

    # Detect input language
    language = detect_language(request.question)

    # Translate to English if necessary
    english_question = request.question

    if language != "english":
        english_question = translate_to_english(request.question)

    # Retrieve relevant chunks
    retrieved_docs = retrieve_documents(english_question)

    # Generate answer in English
    response = generate_answer(
        english_question,
        retrieved_docs
    )

    # Translate answer back to original language
    if language != "english":
        response["answer"] = translate_from_english(
            response["answer"],
            language
        )

    return response


# -----------------------------
# Contradict Endpoint
# -----------------------------

@router.post("/contradict")
def contradict(request: ContradictRequest):

    result = check_contradiction(
        document1=request.document1,
        document2=request.document2,
        topic=request.topic
    )

    return {
        "result": result
    }
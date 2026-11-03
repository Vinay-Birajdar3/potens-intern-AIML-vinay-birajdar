import time
import secrets
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from app import config
from app.retrieval import retrieve_documents
from app.rag import generate_answer
from app.contradiction import check_contradiction
from app.translation import (
    detect_language,
    translate_to_english,
)
from app.evaluation import (
    create_evaluation_job,
    evaluate_question,
    get_evaluation_job,
    run_evaluation_job,
)

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if not config.APP_API_KEY:
        if config.APP_ENV == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API authentication is not configured.",
            )
        return

    if config.APP_ENV == "production" and len(config.APP_API_KEY) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured securely.",
        )

    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not secrets.compare_digest(credentials.credentials, config.APP_API_KEY)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -----------------------------
# Request Models
# -----------------------------

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=config.MAX_QUESTION_CHARS)

    @field_validator("question")
    @classmethod
    def trim_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be blank.")
        return value


class ContradictRequest(BaseModel):
    document1: Literal[
        "employee_handbook",
        "leave_policy",
        "work_from_home",
        "travel_policy",
        "information_security",
        "code_of_conduct",
        "anti_harassment",
        "data_privacy",
        "employee_benefits",
        "procurement_vendor",
        "incident_response",
        "conflict_of_interest",
        "remote_work_equipment",
    ]
    document2: Literal[
        "employee_handbook",
        "leave_policy",
        "work_from_home",
        "travel_policy",
        "information_security",
        "code_of_conduct",
        "anti_harassment",
        "data_privacy",
        "employee_benefits",
        "procurement_vendor",
        "incident_response",
        "conflict_of_interest",
        "remote_work_equipment",
    ]
    topic: str = Field(min_length=1, max_length=200)

    @field_validator("topic")
    @classmethod
    def trim_topic(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Topic must not be blank.")
        return value


# -----------------------------
# Ask Endpoint
# -----------------------------

@router.post("/ask", dependencies=[Depends(require_api_key)])
def ask_question(request: AskRequest, background_tasks: BackgroundTasks):
    start_time = time.perf_counter()

    language = detect_language(request.question)
    english_question = request.question

    if language != "english":
        english_question = translate_to_english(request.question)

    retrieved_docs = retrieve_documents(english_question)

    response = generate_answer(
        english_question,
        retrieved_docs,
        response_language=language,
    )

    response_latency = time.perf_counter() - start_time
    if config.LIVE_EVALUATION_ENABLED:
        evaluation_id, response["evaluation"] = create_evaluation_job(response_latency)
        background_tasks.add_task(
            run_evaluation_job,
            evaluation_id,
            english_question,
            retrieved_docs,
            response,
            latency_seconds=response_latency,
        )
    else:
        response["evaluation"] = evaluate_question(
            english_question,
            retrieved_docs,
            response,
            latency_seconds=response_latency,
        )

    return response


@router.get("/evaluation/{evaluation_id}", dependencies=[Depends(require_api_key)])
def get_question_evaluation(evaluation_id: str):
    evaluation = get_evaluation_job(evaluation_id)
    if evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The evaluation is no longer available.",
        )
    return evaluation


# -----------------------------
# Contradict Endpoint
# -----------------------------

@router.post("/contradict", dependencies=[Depends(require_api_key)])
def contradict(request: ContradictRequest):

    result = check_contradiction(
        document1=request.document1,
        document2=request.document2,
        topic=request.topic
    )

    return {
        "result": result
    }

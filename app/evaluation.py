"""RAG evaluation backed by DeepEval instead of heuristic similarity scores."""

from __future__ import annotations

import time

from app.deepeval_integration import run_rag_evaluation


def _unavailable_evaluation(latency_seconds: float, message: str):
    """Keep answer delivery available when an LLM-as-a-judge run cannot run."""
    return {
        "evaluator": "deepeval",
        "evaluation_status": "unavailable",
        "evaluation_error": message,
        "answer_relevancy": None,
        "faithfulness": None,
        "context_relevancy": None,
        "context_precision": None,
        "context_recall": None,
        "overall_score": None,
        "metric_reasons": {},
        "latency_seconds": round(latency_seconds, 3),
        "evaluation_latency_seconds": None,
        "tokens_used": None,
        "cost_per_query": None,
    }


def evaluate_question(
    question: str,
    retrieved_docs,
    response: dict,
    latency_seconds: float = 0.0,
    expected_answer: str | None = None,
):
    """Evaluate a RAG response with DeepEval's LLM-as-a-judge metrics.

    Precision and recall need an expected answer. They are therefore ``None``
    for a live user question and are populated by the offline golden suite.
    """
    contexts = []
    for item in retrieved_docs or []:
        doc = item[0] if isinstance(item, tuple) and item else item
        content = getattr(doc, "page_content", "") or ""
        if content.strip():
            contexts.append(content)

    if not contexts:
        return _unavailable_evaluation(
            latency_seconds,
            "DeepEval was skipped because no document context was retrieved.",
        )

    evaluation_started = time.perf_counter()
    try:
        metrics = run_rag_evaluation(
            question=question,
            answer=response.get("answer", "") or "",
            retrieval_context=contexts,
            expected_answer=expected_answer,
        )
    except Exception as exc:  # The answer should not fail if the judge is unavailable.
        return _unavailable_evaluation(
            latency_seconds,
            f"DeepEval could not run: {exc}",
        )

    scores = {name: result["score"] for name, result in metrics.items()}
    core_scores = [
        scores["answer_relevancy"],
        scores["faithfulness"],
        scores["contextual_relevancy"],
    ]

    return {
        "evaluator": "deepeval",
        "evaluation_status": "completed",
        "answer_relevancy": scores["answer_relevancy"],
        "faithfulness": scores["faithfulness"],
        "context_relevancy": scores["contextual_relevancy"],
        "context_precision": scores.get("contextual_precision"),
        "context_recall": scores.get("contextual_recall"),
        "overall_score": round(sum(core_scores) / len(core_scores), 3),
        "metric_reasons": {name: result["reason"] for name, result in metrics.items()},
        "latency_seconds": round(latency_seconds, 3),
        "evaluation_latency_seconds": round(time.perf_counter() - evaluation_started, 3),
        "tokens_used": None,
        "cost_per_query": None,
    }

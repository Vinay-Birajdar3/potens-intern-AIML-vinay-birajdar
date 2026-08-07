"""DeepEval helpers for RAG quality checks.

DeepEval's LLM-as-a-judge metrics make additional model calls. They can be
used for live responses or, preferably, for scheduled evaluation runs and CI.
"""

from __future__ import annotations

import os
from typing import Any, Iterable


class DeepEvalSetupError(RuntimeError):
    """Raised when DeepEval or its required judge configuration is missing."""


def _load_deepeval():
    try:
        from deepeval.metrics import (
            AnswerRelevancyMetric,
            ContextualPrecisionMetric,
            ContextualRecallMetric,
            ContextualRelevancyMetric,
            FaithfulnessMetric,
        )
        from deepeval.models import DeepEvalBaseLLM
        from deepeval.test_case import LLMTestCase
    except ImportError as exc:
        raise DeepEvalSetupError(
            "DeepEval is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    return {
        "AnswerRelevancyMetric": AnswerRelevancyMetric,
        "ContextualPrecisionMetric": ContextualPrecisionMetric,
        "ContextualRecallMetric": ContextualRecallMetric,
        "ContextualRelevancyMetric": ContextualRelevancyMetric,
        "DeepEvalBaseLLM": DeepEvalBaseLLM,
        "FaithfulnessMetric": FaithfulnessMetric,
        "LLMTestCase": LLMTestCase,
    }


def build_groq_judge(model_name: str | None = None):
    """Return a schema-aware Groq adapter suitable for DeepEval metrics."""
    modules = _load_deepeval()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise DeepEvalSetupError("GROQ_API_KEY must be set to run DeepEval.")

    from groq import Groq

    base_model = modules["DeepEvalBaseLLM"]
    # Match the application's Groq model by default. A larger judge can still
    # be selected explicitly with DEEPEVAL_GROQ_MODEL.
    selected_model = model_name or os.getenv("DEEPEVAL_GROQ_MODEL", "llama-3.1-8b-instant")

    class GroqJudge(base_model):
        def __init__(self):
            self.client = Groq(api_key=api_key)

        def load_model(self):
            return self.client

        def generate(self, prompt: str, schema=None):
            request: dict[str, Any] = {
                "model": selected_model,
                "temperature": 0,
                "messages": [{"role": "user", "content": prompt}],
            }
            if schema is not None:
                request["response_format"] = {"type": "json_object"}

            result = self.client.chat.completions.create(**request)
            content = result.choices[0].message.content or ""
            return schema.model_validate_json(content) if schema is not None else content

        async def a_generate(self, prompt: str, schema=None):
            return self.generate(prompt, schema)

        def get_model_name(self):
            return f"Groq/{selected_model}"

    return GroqJudge()


def run_rag_evaluation(
    question: str,
    answer: str,
    retrieval_context: Iterable[str],
    expected_answer: str | None = None,
    judge_model: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Score one RAG answer and return each DeepEval score and explanation."""
    modules = _load_deepeval()
    contexts = [text for text in retrieval_context if text and text.strip()]
    if not contexts:
        raise ValueError("DeepEval requires at least one retrieved context chunk.")

    test_case_args = {
        "input": question,
        "actual_output": answer,
        "retrieval_context": contexts,
    }
    if expected_answer:
        test_case_args["expected_output"] = expected_answer

    judge = build_groq_judge(judge_model)
    metrics = [
        ("answer_relevancy", modules["AnswerRelevancyMetric"](model=judge, include_reason=True, async_mode=False)),
        ("faithfulness", modules["FaithfulnessMetric"](model=judge, include_reason=True, async_mode=False)),
        ("contextual_relevancy", modules["ContextualRelevancyMetric"](model=judge, include_reason=True, async_mode=False)),
    ]
    if expected_answer:
        metrics.extend([
            ("contextual_precision", modules["ContextualPrecisionMetric"](model=judge, include_reason=True, async_mode=False)),
            ("contextual_recall", modules["ContextualRecallMetric"](model=judge, include_reason=True, async_mode=False)),
        ])

    test_case = modules["LLMTestCase"](**test_case_args)
    results: dict[str, dict[str, Any]] = {}
    for name, metric in metrics:
        metric.measure(test_case)
        results[name] = {
            "score": round(float(metric.score), 3),
            "passed": bool(metric.is_successful()),
            "reason": metric.reason,
        }
    return results

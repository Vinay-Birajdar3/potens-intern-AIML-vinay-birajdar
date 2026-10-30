"""RAG evaluation backed by DeepEval."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill

from app import config
from app.deepeval_integration import run_rag_evaluation

logger = logging.getLogger(__name__)
_report_lock = Lock()
_evaluation_jobs_lock = Lock()
_evaluation_jobs: dict[str, tuple[float, dict]] = {}
_REPORT_HISTORY_LIMIT = 100
_EVALUATION_JOB_LIMIT = 256
_EVALUATION_JOB_TTL_SECONDS = 1800
_REPORT_SHEET = "RAG Evaluations"
_REPORT_HEADERS = [
    "Evaluated at (UTC)",
    "Question",
    "Answer",
    "Evaluation status",
    "Overall score",
    "Answer relevancy",
    "Faithfulness",
    "Context relevancy",
    "Context precision",
    "Context recall",
    "Request latency (s)",
    "Evaluation latency (s)",
    "Metric explanations",
    "Evaluation error",
]


def _report_row(record: dict) -> list:
    evaluation = record.get("evaluation") or {}
    return [
        record.get("evaluated_at"),
        record.get("question"),
        record.get("answer"),
        evaluation.get("evaluation_status"),
        evaluation.get("overall_score"),
        evaluation.get("answer_relevancy"),
        evaluation.get("faithfulness"),
        evaluation.get("context_relevancy"),
        evaluation.get("context_precision"),
        evaluation.get("context_recall"),
        evaluation.get("latency_seconds"),
        evaluation.get("evaluation_latency_seconds"),
        json.dumps(evaluation.get("metric_reasons", {}), ensure_ascii=False),
        evaluation.get("evaluation_error"),
    ]


def _legacy_report_records(report_path: Path) -> list[dict]:
    legacy_path = report_path.with_suffix(".json")
    if not legacy_path.exists():
        return []
    try:
        legacy_report = json.loads(legacy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Could not read the previous JSON RAG report at {legacy_path}."
        ) from exc
    records = legacy_report.get("evaluations") if isinstance(legacy_report, dict) else None
    if not isinstance(records, list):
        raise RuntimeError(f"The previous JSON RAG report at {legacy_path} is invalid.")
    return records[-_REPORT_HISTORY_LIMIT:]


def _set_literal_cell(cell, value) -> None:
    cell.value = value
    if isinstance(value, str):
        cell.data_type = "s"
        cell.alignment = Alignment(vertical="top", wrap_text=True)


def record_evaluation(
    question: str,
    response: dict,
    evaluation: dict,
) -> None:
    report_path = Path(config.RAG_EVAL_REPORT_PATH)
    with _report_lock:
        try:
            if report_path.exists():
                workbook = load_workbook(report_path)
                if _REPORT_SHEET not in workbook.sheetnames:
                    raise RuntimeError(
                        f"The Excel RAG report at {report_path} is missing the "
                        f"'{_REPORT_SHEET}' worksheet."
                    )
                worksheet = workbook[_REPORT_SHEET]
                headers = [cell.value for cell in worksheet[1]]
                if headers != _REPORT_HEADERS:
                    raise RuntimeError(
                        f"The Excel RAG report at {report_path} has unexpected columns."
                    )
                records = list(worksheet.iter_rows(min_row=2, values_only=True))
            else:
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = _REPORT_SHEET
                records = [_report_row(item) for item in _legacy_report_records(report_path)]

            current_record = {
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
                "question": question,
                "answer": response.get("answer", ""),
                "evaluation": evaluation,
            }
            records = (records + [_report_row(current_record)])[-_REPORT_HISTORY_LIMIT:]

            worksheet.delete_rows(1, worksheet.max_row)
            for column, header in enumerate(_REPORT_HEADERS, start=1):
                cell = worksheet.cell(row=1, column=column)
                cell.value = header
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="243B64")
                cell.alignment = Alignment(vertical="center", wrap_text=True)

            for row_number, record in enumerate(records, start=2):
                for column, value in enumerate(record, start=1):
                    _set_literal_cell(worksheet.cell(row=row_number, column=column), value)
                for column in range(5, 13):
                    worksheet.cell(row=row_number, column=column).number_format = "0.00"

            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = f"A1:N{len(records) + 1}"
            worksheet.row_dimensions[1].height = 30
            for column, width in {
                "A": 27, "B": 42, "C": 60, "D": 20,
                "E": 14, "F": 17, "G": 14, "H": 19,
                "I": 19, "J": 17, "K": 19, "L": 22,
                "M": 70, "N": 55,
            }.items():
                worksheet.column_dimensions[column].width = width
            if records:
                for column in "EFGHIJ":
                    worksheet.conditional_formatting.add(
                        f"{column}2:{column}{len(records) + 1}",
                        ColorScaleRule(
                            start_type="num",
                            start_value=0,
                            start_color="F4CCCC",
                            mid_type="num",
                            mid_value=0.5,
                            mid_color="FFF2CC",
                            end_type="num",
                            end_value=1,
                            end_color="D9EAD3",
                        ),
                    )

            report_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    prefix=f".{report_path.stem}.",
                    suffix=".xlsx",
                    dir=report_path.parent,
                    delete=False,
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                workbook.save(temp_path)
                os.replace(temp_path, report_path)
            finally:
                if temp_path is not None and temp_path.exists():
                    temp_path.unlink()
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(
                f"Could not update the Excel RAG evaluation report at {report_path}."
            ) from exc


def _persist_evaluation(question: str, response: dict, metrics: dict) -> dict:
    try:
        record_evaluation(question, response, metrics)
    except RuntimeError as exc:
        logger.exception("Could not persist live RAG evaluation.")
        metrics["report_error"] = str(exc)
    return metrics


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


def _disabled_evaluation(latency_seconds: float):
    return {
        "evaluator": "deepeval",
        "evaluation_status": "disabled",
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


def pending_evaluation(latency_seconds: float):
    return {
        "evaluator": "deepeval",
        "evaluation_status": "pending",
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


def create_evaluation_job(latency_seconds: float) -> tuple[str, dict]:
    job_id = uuid.uuid4().hex
    result = pending_evaluation(latency_seconds)
    result["evaluation_id"] = job_id
    with _evaluation_jobs_lock:
        _purge_expired_evaluation_jobs()
        while len(_evaluation_jobs) >= _EVALUATION_JOB_LIMIT:
            oldest_job_id = next(iter(_evaluation_jobs))
            _evaluation_jobs.pop(oldest_job_id)
        _evaluation_jobs[job_id] = (time.monotonic(), result)
    return job_id, result


def _purge_expired_evaluation_jobs() -> None:
    now = time.monotonic()
    expired_jobs = [
        job_id
        for job_id, (created_at, _) in _evaluation_jobs.items()
        if now - created_at > _EVALUATION_JOB_TTL_SECONDS
    ]
    for job_id in expired_jobs:
        _evaluation_jobs.pop(job_id)


def get_evaluation_job(job_id: str) -> dict | None:
    with _evaluation_jobs_lock:
        _purge_expired_evaluation_jobs()
        job = _evaluation_jobs.get(job_id)
        return dict(job[1]) if job else None


def run_evaluation_job(
    job_id: str,
    question: str,
    retrieved_docs,
    response: dict,
    latency_seconds: float,
) -> None:
    try:
        result = evaluate_question(
            question,
            retrieved_docs,
            response,
            latency_seconds=latency_seconds,
        )
    except Exception as exc:
        logger.exception("Live RAG evaluation job %s failed.", job_id)
        result = _unavailable_evaluation(
            latency_seconds,
            f"DeepEval could not run: {exc}",
        )
    result["evaluation_id"] = job_id
    with _evaluation_jobs_lock:
        if job_id in _evaluation_jobs:
            _evaluation_jobs[job_id] = (time.monotonic(), result)


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
    if not config.LIVE_EVALUATION_ENABLED and expected_answer is None:
        return _disabled_evaluation(latency_seconds)

    contexts = []
    for item in retrieved_docs or []:
        doc = item[0] if isinstance(item, tuple) and item else item
        content = getattr(doc, "page_content", "") or ""
        if content.strip():
            contexts.append(content)

    if not contexts:
        result = _unavailable_evaluation(
            latency_seconds,
            "DeepEval was skipped because no document context was retrieved.",
        )
        return _persist_evaluation(question, response, result)

    evaluation_started = time.perf_counter()
    try:
        metrics = run_rag_evaluation(
            question=question,
            answer=response.get("answer", "") or "",
            retrieval_context=contexts,
            expected_answer=expected_answer,
        )
    except Exception as exc:  # The answer should not fail if the judge is unavailable.
        result = _unavailable_evaluation(
            latency_seconds,
            f"DeepEval could not run: {exc}",
        )
        return _persist_evaluation(question, response, result)

    scores = {name: result["score"] for name, result in metrics.items()}
    core_scores = [
        scores["answer_relevancy"],
        scores["faithfulness"],
        scores["contextual_relevancy"],
    ]

    result = {
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
    return _persist_evaluation(question, response, result)

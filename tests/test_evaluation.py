import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import load_workbook

from app.evaluation import evaluate_question


class EvaluationTests(unittest.TestCase):
    @patch("app.evaluation.config.LIVE_EVALUATION_ENABLED", False)
    @patch("app.evaluation.run_rag_evaluation")
    def test_live_evaluation_is_disabled_without_judge_calls(self, evaluate):
        metrics = evaluate_question("A question", [], {"answer": "An answer."})

        self.assertEqual(metrics["evaluation_status"], "disabled")
        self.assertIsNone(metrics["overall_score"])
        evaluate.assert_not_called()

    @patch("app.evaluation.config.LIVE_EVALUATION_ENABLED", True)
    @patch("app.evaluation.run_rag_evaluation")
    def test_evaluate_question_returns_metrics(self, evaluate):
        evaluate.return_value = {
            "answer_relevancy": {"score": 0.9, "reason": "Relevant."},
            "faithfulness": {"score": 1.0, "reason": "Grounded."},
            "contextual_relevancy": {"score": 0.8, "reason": "Relevant context."},
        }
        retrieved_docs = [
            type(
                "Doc",
                (),
                {"page_content": "Managers are responsible for ensuring compliance.", "metadata": {}}
            )()
        ]
        response = {"answer": "Managers are responsible for ensuring compliance."}

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.xlsx"
            with patch("app.evaluation.config.RAG_EVAL_REPORT_PATH", str(report_path)):
                metrics = evaluate_question(
                    "Who is responsible for ensuring compliance?",
                    retrieved_docs,
                    response,
                )

        self.assertIn("context_precision", metrics)
        self.assertIn("answer_relevancy", metrics)
        self.assertEqual(metrics["evaluator"], "deepeval")
        self.assertEqual(metrics["evaluation_status"], "completed")
        self.assertIsNone(metrics["context_precision"])
        self.assertIsNone(metrics["context_recall"])
        self.assertEqual(metrics["overall_score"], 0.9)
        evaluate.assert_called_once()

    @patch("app.evaluation.config.LIVE_EVALUATION_ENABLED", True)
    @patch("app.evaluation.run_rag_evaluation", side_effect=RuntimeError("rate limit"))
    def test_evaluation_failure_does_not_block_answer(self, evaluate):
        retrieved_docs = [
            type("Doc", (), {"page_content": "A policy excerpt.", "metadata": {}})()
        ]

        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "app.evaluation.config.RAG_EVAL_REPORT_PATH",
                str(Path(directory) / "report.xlsx"),
            ):
                metrics = evaluate_question(
                    "What is the policy?",
                    retrieved_docs,
                    {"answer": "An answer."},
                )

        self.assertEqual(metrics["evaluation_status"], "unavailable")
        self.assertIn("rate limit", metrics["evaluation_error"])
        self.assertIsNone(metrics["overall_score"])
        evaluate.assert_called_once()

    @patch("app.evaluation.config.LIVE_EVALUATION_ENABLED", True)
    @patch("app.evaluation.run_rag_evaluation")
    def test_live_evaluations_update_external_report_and_retain_latest_100(self, evaluate):
        evaluate.return_value = {
            "answer_relevancy": {"score": 1.0, "reason": "Relevant."},
            "faithfulness": {"score": 1.0, "reason": "Grounded."},
            "contextual_relevancy": {"score": 1.0, "reason": "Relevant context."},
        }
        retrieved_docs = [
            type("Doc", (), {"page_content": "A policy excerpt.", "metadata": {}})()
        ]

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "rag_evaluation_report.json"
            report_path = report_path.with_suffix(".xlsx")
            with patch("app.evaluation.config.RAG_EVAL_REPORT_PATH", str(report_path)):
                for index in range(101):
                    evaluate_question(
                        f"Question {index}",
                        retrieved_docs,
                        {"answer": f"Answer {index}"},
                    )

            workbook = load_workbook(report_path, data_only=True)
            worksheet = workbook["RAG Evaluations"]
            rows = list(worksheet.iter_rows(values_only=True))

        self.assertEqual(rows[0][1], "Question")
        self.assertEqual(len(rows) - 1, 100)
        self.assertEqual(rows[1][1], "Question 1")
        self.assertEqual(rows[-1][1], "Question 100")
        self.assertEqual(worksheet.freeze_panes, "A2")
        self.assertEqual(worksheet.auto_filter.ref, "A1:N101")
        workbook.close()

    @patch("app.evaluation.config.LIVE_EVALUATION_ENABLED", True)
    @patch("app.evaluation.run_rag_evaluation")
    def test_existing_json_report_is_migrated_to_excel_on_update(self, evaluate):
        evaluate.return_value = {
            "answer_relevancy": {"score": 1.0, "reason": "Relevant."},
            "faithfulness": {"score": 0.9, "reason": "Grounded."},
            "contextual_relevancy": {"score": 0.8, "reason": "Relevant context."},
        }
        retrieved_docs = [
            type("Doc", (), {"page_content": "A policy excerpt.", "metadata": {}})()
        ]

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "rag_evaluation_report.xlsx"
            legacy_path = report_path.with_suffix(".json")
            legacy_path.write_text(json.dumps({
                "evaluations": [{
                    "evaluated_at": "2026-01-01T00:00:00+00:00",
                    "question": "Existing question",
                    "answer": "Existing answer",
                    "evaluation": {
                        "evaluation_status": "completed",
                        "answer_relevancy": 0.7,
                        "faithfulness": 0.8,
                        "context_relevancy": 0.6,
                    },
                }],
            }), encoding="utf-8")
            with patch("app.evaluation.config.RAG_EVAL_REPORT_PATH", str(report_path)):
                evaluate_question(
                    "New question",
                    retrieved_docs,
                    {"answer": "New answer"},
                )

            workbook = load_workbook(report_path, read_only=True, data_only=True)
            rows = list(workbook["RAG Evaluations"].iter_rows(values_only=True))
            workbook.close()

        self.assertEqual(rows[1][1:3], ("Existing question", "Existing answer"))
        self.assertEqual(rows[2][1:3], ("New question", "New answer"))


if __name__ == "__main__":
    unittest.main()

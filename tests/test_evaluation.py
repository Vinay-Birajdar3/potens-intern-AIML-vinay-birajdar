import unittest
from unittest.mock import patch

from app.evaluation import evaluate_question


class EvaluationTests(unittest.TestCase):
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

    @patch("app.evaluation.run_rag_evaluation", side_effect=RuntimeError("rate limit"))
    def test_evaluation_failure_does_not_block_answer(self, evaluate):
        retrieved_docs = [
            type("Doc", (), {"page_content": "A policy excerpt.", "metadata": {}})()
        ]

        metrics = evaluate_question("What is the policy?", retrieved_docs, {"answer": "An answer."})

        self.assertEqual(metrics["evaluation_status"], "unavailable")
        self.assertIn("rate limit", metrics["evaluation_error"])
        self.assertIsNone(metrics["overall_score"])
        evaluate.assert_called_once()


if __name__ == "__main__":
    unittest.main()

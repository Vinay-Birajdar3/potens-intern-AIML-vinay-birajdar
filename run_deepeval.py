"""Run DeepEval against the project's RAG golden questions.

Usage: python run_deepeval.py
Set DEEPEVAL_GROQ_MODEL to use a different Groq judge model.
"""

import json
from pathlib import Path

from app.deepeval_integration import run_rag_evaluation
from app.rag import generate_answer
from app.retrieval import retrieve_documents


# Golden questions are used only by DeepEval's reference-based metrics.
EVAL_CASES = [
    {
        "question": "Who is responsible for ensuring compliance in the employee handbook?",
        "expected_answer": "Managers are responsible for ensuring compliance and answering questions.",
    },
    {
        "question": "What is required before business travel can be approved?",
        "expected_answer": "Business travel requires prior approval from the reporting manager and, where applicable, the finance department.",
    },
    {
        "question": "What should employees do to protect company information?",
        "expected_answer": "Employees should protect company information and follow security controls.",
    },
    {
        "question": "What makes someone eligible for remote work?",
        "expected_answer": "Remote work is available for eligible roles based on business requirements and manager approval.",
    },
    {
        "question": "What leave types are available under the leave policy?",
        "expected_answer": "The policy lists annual, casual, sick, maternity/paternity, bereavement, and unpaid leave.",
    },
]


def main() -> None:
    results = []
    for case in EVAL_CASES:
        retrieved_docs = retrieve_documents(case["question"])
        response = generate_answer(case["question"], retrieved_docs)
        contexts = [doc.page_content for doc, _ in retrieved_docs]
        metrics = run_rag_evaluation(
            question=case["question"],
            answer=response["answer"],
            retrieval_context=contexts,
            expected_answer=case["expected_answer"],
        )
        results.append({"question": case["question"], "metrics": metrics})

    output_path = Path("deepeval_report.json")
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"\nReport saved to {output_path.resolve()}")


if __name__ == "__main__":
    main()

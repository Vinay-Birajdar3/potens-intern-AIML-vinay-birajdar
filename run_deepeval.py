"""Run DeepEval against the project's RAG golden questions.

Usage: python run_deepeval.py
Set DEEPEVAL_GROQ_MODEL to use a different Groq judge model.
"""

import json
from pathlib import Path

from app.deepeval_integration import run_rag_evaluation
from app.rag import generate_answer
from app.retrieval import retrieve_documents
from evaluate_rag import EVAL_CASES


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

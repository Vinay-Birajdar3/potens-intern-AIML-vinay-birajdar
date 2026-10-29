from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.rag import generate_answer


def test_no_retrieved_context_abstains_without_calling_model():
    with patch("app.rag.get_groq_client") as get_client:
        result = generate_answer("What is the policy?", [])

    assert result == {
        "answer": "The provided documents do not contain sufficient information.",
        "citations": [],
    }
    get_client.assert_not_called()


def test_non_english_abstention_uses_the_requested_language():
    with patch("app.rag.get_groq_client") as get_client:
        result = generate_answer("Translated question", [], response_language="hindi")

    assert result["answer"] == "दिए गए दस्तावेज़ों में पर्याप्त जानकारी उपलब्ध नहीं है।"
    get_client.assert_not_called()


def test_generation_uses_configured_language_model_and_language():
    document = type(
        "Document",
        (),
        {
            "page_content": "Employees need manager approval.",
            "metadata": {"source_name": "Leave_Policy.pdf", "page": 0, "chunk_id": 1},
        },
    )()
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content="उत्तर")),
        ],
    )

    with (
        patch("app.rag.get_groq_client", return_value=client),
        patch("app.rag.config.GROQ_MODEL", "test-model"),
    ):
        result = generate_answer(
            "Translate the question",
            [(document, 0.5)],
            response_language="hindi",
        )

    assert result["answer"] == "उत्तर"
    assert result["citations"][0]["source"] == "Leave_Policy.pdf"
    call = client.chat.completions.create.call_args.kwargs
    assert call["model"] == "test-model"
    assert "Answer in Hindi" in call["messages"][1]["content"]
    assert "[1]" in call["messages"][1]["content"]

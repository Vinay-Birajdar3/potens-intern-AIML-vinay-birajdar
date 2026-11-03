from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.rag import _generate_cached_answer, generate_answer


def test_no_retrieved_context_abstains_without_calling_model():
    with patch("app.rag.get_groq_client") as get_client:
        result = generate_answer("What is the policy?", [])

    assert result == {
        "answer": "The provided documents do not contain sufficient information.",
        "citations": [],
    }
    get_client.assert_not_called()


def test_markdown_policy_citation_has_no_fake_page_number():
    document = type(
        "Document",
        (),
        {
            "page_content": "Sample policy content.",
            "metadata": {
                "source_name": "Data_Privacy_and_Retention_Policy.md",
                "chunk_id": 1,
            },
        },
    )()
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="A grounded answer."))],
    )
    _generate_cached_answer.cache_clear()

    with patch("app.rag.get_groq_client", return_value=client):
        result = generate_answer("What is the policy?", [(document, 0.1)])

    assert result["citations"][0]["page"] is None
    assert "Page: Not applicable" in client.chat.completions.create.call_args.kwargs[
        "messages"
    ][1]["content"]
    _generate_cached_answer.cache_clear()


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


def test_identical_grounded_prompt_uses_cached_answer():
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
            SimpleNamespace(message=SimpleNamespace(content="Manager approval is required.")),
        ],
    )
    _generate_cached_answer.cache_clear()

    with (
        patch("app.rag.get_groq_client", return_value=client),
        patch("app.rag.config.GROQ_MODEL", "cache-test-model"),
    ):
        first = generate_answer("Is approval needed?", [(document, 0.2)])
        second = generate_answer("Is approval needed?", [(document, 0.2)])

    assert first == second
    client.chat.completions.create.assert_called_once()
    _generate_cached_answer.cache_clear()

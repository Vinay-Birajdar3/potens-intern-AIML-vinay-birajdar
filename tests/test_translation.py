from unittest.mock import patch

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.translation import detect_language


def test_ascii_english_skips_remote_language_detection():
    with patch("app.translation.get_groq_client") as get_client:
        assert detect_language("How many leave days are available?") == "english"

    get_client.assert_not_called()


def test_marathi_detection_uses_low_reasoning_and_enough_output_tokens():
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content="marathi")),
        ],
    )

    with patch("app.translation.get_groq_client", return_value=client):
        language = detect_language("धोरणानुसार कोणते खर्च परतफेड करता येतील?")

    assert language == "marathi"
    call = client.chat.completions.create.call_args.kwargs
    assert call["reasoning_effort"] == "low"
    assert call["max_completion_tokens"] == 64

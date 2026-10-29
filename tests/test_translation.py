from unittest.mock import patch

from app.translation import detect_language


def test_ascii_english_skips_remote_language_detection():
    with patch("app.translation.get_groq_client") as get_client:
        assert detect_language("How many leave days are available?") == "english"

    get_client.assert_not_called()

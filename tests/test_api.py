from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_ask_rejects_blank_and_oversized_questions():
    with (
        patch("app.api.config.APP_ENV", "development"),
        patch("app.api.config.APP_API_KEY", ""),
        TestClient(app) as client,
    ):
        blank = client.post("/ask", json={"question": "   "})
        oversized = client.post("/ask", json={"question": "x" * 2001})

    assert blank.status_code == 422
    assert oversized.status_code == 422


def test_production_ask_requires_a_configured_api_key():
    with (
        patch("app.api.config.APP_ENV", "production"),
        patch("app.api.config.APP_API_KEY", ""),
        TestClient(app) as client,
    ):
        response = client.post("/ask", json={"question": "What is the policy?"})

    assert response.status_code == 503


def test_ask_requires_the_configured_bearer_token():
    with (
        patch("app.api.config.APP_ENV", "development"),
        patch("app.api.config.APP_API_KEY", "local-test-token"),
        patch("app.api.detect_language", return_value="english"),
        patch("app.api.retrieve_documents", return_value=[]),
        patch(
            "app.api.generate_answer",
            return_value={
                "answer": "The provided documents do not contain sufficient information.",
                "citations": [],
            },
        ),
        patch(
            "app.api.evaluate_question",
            return_value={"evaluation_status": "disabled"},
        ),
        TestClient(app) as client,
    ):
        unauthorized = client.post(
            "/ask",
            json={"question": "What is the policy?"},
        )
        authorized = client.post(
            "/ask",
            json={"question": "What is the policy?"},
            headers={"Authorization": "Bearer local-test-token"},
        )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200

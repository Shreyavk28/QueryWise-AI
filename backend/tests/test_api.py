
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ask_question_success():
    mock_result = {
        "sql": "SELECT product_name FROM products LIMIT 100",
        "columns": ["product_name"],
        "rows": [{"product_name": "Laptop"}],
        "row_count": 1,
    }

    with (
        patch("app.main.generate_sql", return_value="SELECT product_name FROM products"),
        patch("app.main.execute_readonly_query", return_value=mock_result),
    ):
        response = client.post(
            "/api/ask",
            json={"question": "Show products"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["row_count"] == 1
    assert response.json()["rows"][0]["product_name"] == "Laptop"


def test_ask_question_invalid_input():
    response = client.post(
        "/api/ask",
        json={"question": "Hi"},
    )

    assert response.status_code == 422


def test_ask_question_rate_limit():
    with patch(
        "app.main.generate_sql",
        side_effect=Exception("429 Too Many Requests"),
    ):
        response = client.post(
            "/api/ask",
            json={"question": "Show total revenue"},
        )

    assert response.status_code == 429
    assert "quota" in response.json()["detail"].lower() or (
        "rate-limit" in response.json()["detail"].lower()
        or "rate limit" in response.json()["detail"].lower()
    )


def test_ask_question_unexpected_error():
    with patch(
        "app.main.generate_sql",
        side_effect=RuntimeError("Unexpected test error"),
    ):
        response = client.post(
            "/api/ask",
            json={"question": "Show total revenue"},
        )

    assert response.status_code == 500
    assert "try again later" in response.json()["detail"].lower()
    

def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_db_health_endpoint():
    mock_result = {
        "status": "success",
        "database": "connected",
        "test_result": 1,
    }

    with patch("app.main.check_database", return_value=mock_result):
        response = client.get("/api/db-health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_unsupported_question():
    with patch(
        "app.main.generate_sql",
        side_effect=ValueError(
            "This question cannot be answered using the available database schema."
        ),
    ):
        response = client.post(
            "/api/ask",
            json={"question": "Tell me a joke"},
        )

    assert response.status_code == 400
    assert "cannot be answered" in response.json()["detail"].lower()


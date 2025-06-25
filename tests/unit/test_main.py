"""Tests for the main application module."""

from fastapi.testclient import TestClient

from eq_cir_proxy_service.main import app


def test_root():
    """Tests the response JSON upon navigating to the root."""
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

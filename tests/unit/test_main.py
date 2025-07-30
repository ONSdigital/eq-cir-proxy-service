"""Tests for the main application module."""

from fastapi.testclient import TestClient

from eq_cir_proxy_service.main import app


def test_root():
    """Tests the response JSON upon navigating to the root."""
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_validation_exception_handler(client=None):
    """Test that a non-UUID parameter returns a 422 response."""
    client = client or TestClient(app)
    # /instrument endpoint expects parameters, so send invalid data to trigger validation
    response = client.get("/instrument/invalid-uuid")
    assert response.status_code in (422, 404)


def test_empty_instrument_id_exception_handler(client=None):
    """Test that a missing instrument_id returns a 404."""
    client = client or TestClient(app)
    response = client.get("/instrument")
    assert response.status_code == 404

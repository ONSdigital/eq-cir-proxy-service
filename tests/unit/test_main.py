"""Tests for the main application module."""

import pytest
from fastapi.testclient import TestClient

from eq_cir_proxy_service.main import app


def test_root():
    """Tests the response JSON upon navigating to the root."""
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_status_endpoint(client=None):
    """Test the GET /status endpoint."""
    client = client or TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_status_unsupported_method(method, client=None):
    """Test that unsupported methods on /status return 405."""
    client = client or TestClient(app)
    response = client.request(method, "/status")
    assert response.status_code == 405


def test_status_logs(caplog):
    """Test that accessing the /status endpoint logs the correct message."""
    client = TestClient(app)
    with caplog.at_level("INFO"):
        response = client.get("/status")
    assert response.status_code == 200
    assert "Health check endpoint." in caplog.text


def test_validation_exception_handler(client=None):
    """Test that a non-UUID parameter returns a 422 response."""
    client = client or TestClient(app)
    # /instrument endpoint expects parameters, so send invalid data to trigger validation
    response = client.get("/instrument/invalid-uuid")
    assert response.status_code == 422


def test_empty_instrument_id_exception_handler(client=None):
    """Test that a missing instrument_id returns a 404."""
    client = client or TestClient(app)
    response = client.get("/instrument")
    assert response.status_code == 404

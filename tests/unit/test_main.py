"""Sample test to prevent checks failing - to be deleted when further tests are implemented."""

from eq_cir_proxy_service.main import app
from fastapi.testclient import TestClient


def test_root():
    """Tests the response JSON upon navigating to the root."""
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

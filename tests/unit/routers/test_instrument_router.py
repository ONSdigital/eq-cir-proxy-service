"""Unit tests for the instrument router, specifically for the get_instrument_by_uuid endpoint."""

from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from eq_cir_proxy_service.routers import instrument_router
from eq_cir_proxy_service.routers.instrument_router import router

# Set up FastAPI test app and client
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_get_instrument_by_uuid_success() -> None:
    """Should return 200 and correct instrument data when given a valid UUID."""
    instrument_id = str(uuid4())
    response = client.get(f"/instrument/{instrument_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == instrument_id
    assert data["validator_version"] == "1.0.0"


def test_get_instrument_by_uuid_with_version() -> None:
    """Should return 200 and correct instrument data when version is supplied."""
    instrument_id = str(uuid4())
    version = "2.0.0"
    response = client.get(f"/instrument/{instrument_id}?version={version}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == instrument_id


def test_get_instrument_by_uuid_invalid_uuid() -> None:
    """Should return 422 when given an invalid UUID."""
    response = client.get("/instrument/not-a-uuid")
    assert response.status_code == 422


def test_get_instrument_by_uuid_invalid_version(monkeypatch: pytest.MonkeyPatch) -> None:
    """Should return 400 when validate_version raises an HTTPException."""
    instrument_id = str(uuid4())

    def mock_validate_version(_version: str) -> None:
        raise HTTPException(
            status_code=400,
            detail={"status": "fail", "message": "Invalid version"},
        )

    monkeypatch.setattr(instrument_router, "validate_version", mock_validate_version)

    response = client.get(f"/instrument/{instrument_id}?version=bad-version")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["status"] == "fail"
    assert "message" in data["detail"]


class MockInternalError(Exception):
    """Custom exception for internal error simulation."""


def test_get_instrument_by_uuid_internal_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Should return 500 when an unexpected error occurs during validation."""
    instrument_id = str(uuid4())

    def mock_validate_version(_version: str) -> None:
        raise MockInternalError

    monkeypatch.setattr(instrument_router, "validate_version", mock_validate_version)

    response = client.get(f"/instrument/{instrument_id}?version=1.0.0")
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["status"] == "error"
    assert "message" in data["detail"]

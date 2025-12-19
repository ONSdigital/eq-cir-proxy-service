"""Unit tests for the instrument conversion service."""

import os
from dataclasses import dataclass

import pytest
from fastapi import HTTPException, status
from httpx import RequestError

from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.services.instrument.conversion import (
    convert_instrument,
    safe_parse,
)

FAKE_API_URL = "http://fake-service"
FAKE_CONVERT_ENDPOINT = "/convert"


@dataclass
class DummyResponse:
    """Dummy response for testing."""

    json_data: dict

    def raise_for_status(self):
        """Simulate raise_for_status (no-op for testing)."""

    def json(self):
        """Return the JSON data."""
        return self.json_data


@dataclass
class DummyAsyncClient:
    """Dummy async client for testing."""

    expected_instrument: dict
    expected_instrument_metadata: dict
    expected_response: dict
    target_version: str

    async def __aenter__(self):
        """Simulate async context manager enter."""
        return self

    async def __aexit__(self, *_):
        """Simulate async context manager exit."""

    async def post(self, url, **kwargs):
        """Simulate post method to check parameters and return dummy response."""
        assert url == "/convert"
        assert kwargs["json"] == {"instrument": self.expected_instrument}
        assert kwargs["params"] == {
            "current_version": self.expected_instrument_metadata.get("validator_version"),
            "target_version": self.target_version,
        }
        return DummyResponse(self.expected_response)


@dataclass
class DummyIAPClient:
    """Dummy IAP client for testing."""

    error = "failure"

    async def __aenter__(self):
        """Simulate async context manager enter."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Simulate async context manager exit."""

    async def post(self, *_args, **_kwargs):
        """Simulate a post that raises RequestError."""
        raise RequestError(self.error, request=None)

    def __call__(self, *_args, **_kwargs):
        """Simulate callable to return self."""
        return self


@pytest.mark.asyncio
async def test_convert_instrument_missing_version(caplog):
    """Should raise 404 if validator_version is missing."""
    caplog.set_level("INFO")
    instrument = {"id": "123", "sections": []}  # no validator_version
    instrument_metadata = {}

    with pytest.raises(HTTPException) as excinfo:
        await convert_instrument(instrument, instrument_metadata, "1.0.0")

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert excinfo.value.detail["message"] == exception_messages.EXCEPTION_400_INVALID_INSTRUMENT
    assert any(
        record.levelname == "ERROR" and "Instrument version is missing" in record.message for record in caplog.records
    )


@pytest.mark.asyncio
async def test_convert_instrument_same_version(caplog):
    """Should return the same instrument if versions match."""
    caplog.set_level("INFO")
    instrument = {"id": "123", "sections": []}
    instrument_metadata = {"validator_version": "1.0.0"}
    result = await convert_instrument(instrument, instrument_metadata, "1.0.0")
    assert result == instrument
    assert any(
        record.levelname == "INFO" and "Instrument version matches the target" in record.message
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_convert_instrument_higher_version():
    """Should raise 400 if instrument version > target version."""
    instrument = {"id": "123", "sections": []}
    instrument_metadata = {"validator_version": "2.0.0"}

    with pytest.raises(HTTPException) as excinfo:
        await convert_instrument(instrument, instrument_metadata, "1.0.0")

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert excinfo.value.detail["message"] == exception_messages.EXCEPTION_400_INVALID_CONVERSION


@pytest.mark.asyncio
async def test_convert_instrument_lower_version_success(monkeypatch):
    """Should call Converter Service and return converted instrument if instrument version < target version."""
    instrument = {"id": "123", "sections": []}
    instrument_metadata = {"validator_version": "1.0.0"}
    target_version = "2.0.0"
    fake_response_data = {"id": "123", "sections": []}

    def dummy_get_api_client(*_args, **_kwargs):
        return DummyAsyncClient(
            expected_instrument=instrument,
            expected_instrument_metadata=instrument_metadata,
            expected_response=fake_response_data,
            target_version=target_version,
        )

    monkeypatch.setattr(
        "eq_cir_proxy_service.services.instrument.conversion.get_api_client",
        dummy_get_api_client,
    )
    monkeypatch.setenv("CONVERTER_SERVICE_API_BASE_URL", FAKE_API_URL)
    monkeypatch.setenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT", FAKE_CONVERT_ENDPOINT)

    result = await convert_instrument(instrument, instrument_metadata, target_version)

    assert result == fake_response_data


@pytest.mark.asyncio
async def test_convert_instrument_request_error_with_iap(monkeypatch):
    """Should raise 500 if Converter Service request fails (IAP client version)."""
    instrument = {"id": "123", "sections": []}
    instrument_metadata = {"validator_version": "1.0.0"}
    target_version = "2.0.0"

    monkeypatch.setattr(
        "eq_cir_proxy_service.services.instrument.conversion.get_api_client",
        DummyIAPClient(),
    )
    monkeypatch.setenv("CONVERTER_SERVICE_API_BASE_URL", FAKE_API_URL)
    monkeypatch.setenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT", FAKE_CONVERT_ENDPOINT)
    monkeypatch.setenv("CONVERTER_SERVICE_IAP_CLIENT_ID", "dummy-client-id")

    with pytest.raises(HTTPException) as excinfo:
        await convert_instrument(instrument, instrument_metadata, target_version)

    assert excinfo.value.status_code == 500
    assert excinfo.value.detail["message"] == "Error connecting to Converter Service."


@pytest.mark.asyncio
async def test_retrieve_instrument_missing_converter_endpoint(mocker):
    """Test convert_instrument raises HTTPException if CONVERTER_SERVICE_CONVERT_CI_ENDPOINT exists but has no value."""
    instrument = {"id": "123", "sections": []}
    instrument_metadata = {"validator_version": "1.0.0"}
    target_version = "2.0.0"
    # Patch environment to include CONVERTER_SERVICE_API_BASE_URL but not CONVERTER_SERVICE_CONVERT_CI_ENDPOINT
    mocker.patch.dict(
        os.environ,
        {"CONVERTER_SERVICE_API_BASE_URL": "http://fake-url", "CONVERTER_SERVICE_CONVERT_CI_ENDPOINT": ""},
        clear=True,
    )
    with pytest.raises(HTTPException) as exc_info:
        await convert_instrument(instrument, instrument_metadata, target_version)
    exc = exc_info.value
    assert exc.status_code == 500
    assert exc.detail["message"] == "CONVERTER_SERVICE_CONVERT_CI_ENDPOINT configuration is missing."


def test_safe_parse_valid(monkeypatch):
    """Tests the safe_parse function with a valid version."""

    class DummyVersion:  # pylint: disable=too-few-public-methods
        """Dummy version parser for testing."""

        @staticmethod
        def parse(s: str):
            """Parses a version string."""
            return f"parsed-{s}"

    monkeypatch.setattr("eq_cir_proxy_service.services.instrument.conversion.Version", DummyVersion)

    result = safe_parse("current", "1.2.3")
    assert result == "parsed-1.2.3"


@pytest.mark.parametrize(
    "version_type, version_value",
    [
        ("current", "abc"),
        ("target", "???"),
    ],
)
def test_safe_parse_invalid_version(version_type, version_value, monkeypatch):
    """Tests the safe_parse function with an invalid version."""

    class DummyVersion:  # pylint: disable=too-few-public-methods
        """Dummy version parser for testing."""

        @staticmethod
        def parse(s: str):
            """Parses a version string."""
            error_message = "invalid version"
            if s == "valid":
                return "parsed-valid"
            raise ValueError(error_message)

    monkeypatch.setattr("eq_cir_proxy_service.services.instrument.conversion.Version", DummyVersion)

    # valid target
    assert safe_parse(version_type, "valid") == "parsed-valid"

    # bad target
    with pytest.raises(HTTPException) as exc_info:
        safe_parse(version_type, version_value)

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.detail["status"] == "error"
    assert exc.detail["message"] == f"Invalid {version_type} version: {version_value}"

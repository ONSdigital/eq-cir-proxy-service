"""Unit tests for the instrument conversion service."""

import os

import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient, RequestError

from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.services.instrument.instrument_conversion_service import (
    convert_instrument,
    safe_parse,
)


@pytest.mark.asyncio
async def test_convert_instrument_missing_version(caplog):
    """Should raise 404 if validator_version is missing."""
    instrument = {"id": "123", "sections": []}  # no validator_version

    with pytest.raises(HTTPException) as excinfo:
        await convert_instrument(instrument, "1.0.0")

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert excinfo.value.detail["message"] == exception_messages.EXCEPTION_400_INVALID_INSTRUMENT
    assert "Instrument version is missing" in caplog.text


@pytest.mark.asyncio
async def test_convert_instrument_same_version(caplog):
    """Should return the same instrument if versions match."""
    caplog.set_level("INFO")
    instrument = {"id": "123", "validator_version": "1.0.0", "sections": []}
    result = await convert_instrument(instrument, "1.0.0")
    assert result == instrument
    assert "Instrument version matches the target" in caplog.text


@pytest.mark.asyncio
async def test_convert_instrument_higher_version():
    """Should raise 400 if instrument version > target version."""
    instrument = {"id": "123", "validator_version": "2.0.0", "sections": []}

    with pytest.raises(HTTPException) as excinfo:
        await convert_instrument(instrument, "1.0.0")

    assert excinfo.value.status_code == status.HTTP_400_BAD_REQUEST
    assert excinfo.value.detail["message"] == exception_messages.EXCEPTION_400_INVALID_CONVERSION


@pytest.mark.asyncio
async def test_convert_instrument_lower_version_success(fake_post, monkeypatch):
    """Should call converter service and return converted instrument if instrument version < target version."""
    instrument = {"id": "123", "validator_version": "1.0.0", "sections": []}
    target_version = "2.0.0"
    fake_response_data = {"id": "123", "validator_version": "2.0.0"}

    fake_post["set_response"](fake_response_data)

    monkeypatch.setenv("CONVERTER_SERVICE_API_BASE_URL", "http://fake-service")
    monkeypatch.setenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT", "/convert")

    result = await convert_instrument(instrument, target_version)

    assert result == fake_response_data

    captured = fake_post["captured"]
    assert isinstance(captured["args"][0], AsyncClient)
    assert captured["args"][1] == "http://fake-service/convert"
    assert captured["kwargs"]["json"] == {"instrument": instrument}
    assert captured["kwargs"]["params"] == {
        "current_version": "1.0.0",
        "target_version": "2.0.0",
    }


@pytest.mark.asyncio
async def test_convert_instrument_request_error(monkeypatch):
    """Should raise 500 if converter service request fails."""
    instrument = {"id": "123", "validator_version": "1.0.0", "sections": []}
    target_version = "2.0.0"
    error = "failure"

    async def _raise_error(_client, _url, **_kwargs):
        raise RequestError(error, request=None)

    monkeypatch.setattr(AsyncClient, "post", _raise_error)
    monkeypatch.setenv("CONVERTER_SERVICE_API_BASE_URL", "http://fake-service")
    monkeypatch.setenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT", "/convert")

    with pytest.raises(HTTPException) as excinfo:
        await convert_instrument(instrument, target_version)

    assert excinfo.value.status_code == 500
    assert excinfo.value.detail["message"] == "Error connecting to Converter service."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "environment_variables",
    [
        # No URL
        ({}),
        # Empty URL
        ({"CONVERTER_SERVICE_API_BASE_URL": ""}),
    ],
)
async def test_retrieve_instrument_missing_converter_base_url(environment_variables, mocker):
    """Test convert_instrument raises HTTPException if CONVERTER_SERVICE_API_BASE_URL is missing or empty."""
    instrument = {"id": "123", "validator_version": "1.0.0", "sections": []}
    target_version = "2.0.0"
    # Patch environment to remove CONVERTER_SERVICE_API_BASE_URL
    mocker.patch.dict(os.environ, environment_variables, clear=True)
    with pytest.raises(HTTPException) as exc_info:
        await convert_instrument(instrument, target_version)
    exc = exc_info.value
    assert exc.status_code == 500
    assert exc.detail["message"] == "CONVERTER_SERVICE_API_BASE_URL configuration is missing."


@pytest.mark.asyncio
async def test_retrieve_instrument_missing_converter_endpoint(mocker):
    """Test convert_instrument raises HTTPException if CONVERTER_SERVICE_CONVERT_CI_ENDPOINT exists but has no value."""
    instrument = {"id": "123", "validator_version": "1.0.0", "sections": []}
    target_version = "2.0.0"
    # Patch environment to include CONVERTER_SERVICE_API_BASE_URL but not CONVERTER_SERVICE_CONVERT_CI_ENDPOINT
    mocker.patch.dict(
        os.environ,
        {"CONVERTER_SERVICE_API_BASE_URL": "http://fake-url", "CONVERTER_SERVICE_CONVERT_CI_ENDPOINT": ""},
        clear=True,
    )
    with pytest.raises(HTTPException) as exc_info:
        await convert_instrument(instrument, target_version)
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

    monkeypatch.setattr("eq_cir_proxy_service.services.instrument.instrument_conversion_service.Version", DummyVersion)

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
            error_message = "bad version"
            if s == "good":
                return "parsed-good"
            raise ValueError(error_message)

    monkeypatch.setattr("eq_cir_proxy_service.services.instrument.instrument_conversion_service.Version", DummyVersion)

    # good current
    assert safe_parse("current", "good") == "parsed-good"

    # bad target
    with pytest.raises(HTTPException) as exc_info:
        safe_parse(version_type, version_value)

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.detail["status"] == "error"
    assert exc.detail["message"] == f"Invalid {version_type} version: {version_value}"

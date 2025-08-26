"""Unit tests for the instrument conversion service."""

import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient, RequestError

from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.services.instrument.instrument_conversion_service import (
    convert_instrument,
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

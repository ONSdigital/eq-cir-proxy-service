"""Unit tests for the instrument retrieval service."""

import os
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from eq_cir_proxy_service.services.instrument import instrument_retrieval_service
from eq_cir_proxy_service.services.instrument.instrument_retrieval_service import (
    retrieve_instrument,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, json_data, text_data, side_effect, expected_result, expected_exception",
    [
        # 200 OK case
        (200, {"id": "123"}, "", None, {"id": "123"}, None),
        # 404 Not Found case
        (404, None, "Not Found", None, None, HTTPException),
        # 500 Server Error case
        (500, None, "Internal Server Error", None, None, HTTPException),
        # Connection/Timeout error case
        (None, None, None, httpx.RequestError("Timeout"), None, HTTPException),
    ],
)
async def test_retrieve_instrument(
    status_code,
    json_data,
    text_data,
    side_effect,
    expected_result,
    expected_exception,
    mocker,
):
    """Test the retrieve_instrument function with various scenarios."""
    instrument_id = uuid4()

    # Set up fake environment variables
    base_url = "http://fake-base-url/"
    endpoint = "fake-endpoint"
    mocker.patch.dict(os.environ, {"CIR_API_BASE_URL": base_url, "CIR_RETRIEVE_CI_ENDPOINT": endpoint})

    # Mock response object unless we're simulating an exception
    if side_effect is None:
        mock_response = mocker.Mock()
        mock_response.status_code = status_code
        mock_response.text = text_data
        if json_data is not None:
            mock_response.json.return_value = json_data
        async_mock_get = mocker.AsyncMock(return_value=mock_response)
    else:
        async_mock_get = mocker.AsyncMock(side_effect=side_effect)

    # Patch httpx.get
    mock_get = mocker.patch(
        "eq_cir_proxy_service.services.instrument.instrument_retrieval_service.AsyncClient.get",
        async_mock_get,
    )

    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            await retrieve_instrument(instrument_id)
        assert exc_info.value.status_code == (status_code if status_code is not None else 500)
    else:
        result = await retrieve_instrument(instrument_id)
        assert result == expected_result

    # Only assert call if not simulating an exception before call
    mock_get.assert_called_once_with(f"{base_url}{endpoint}", params={"guid": str(instrument_id)})


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "environment_variables",
    [
        # No URL
        ({}),
        # Empty URL
        ({"CIR_API_BASE_URL": ""}),
    ],
)
async def test_retrieve_instrument_missing_cir_base_url(environment_variables, mocker):
    """Test retrieve_instrument raises HTTPException if CIR_API_BASE_URL is missing or empty."""
    instrument_id = uuid4()
    # Patch environment to remove CIR_API_BASE_URL
    mocker.patch.dict(os.environ, environment_variables, clear=True)
    with pytest.raises(HTTPException) as exc_info:
        await instrument_retrieval_service.retrieve_instrument(instrument_id)
    exc = exc_info.value
    assert exc.status_code == 500
    assert exc.detail["message"] == "CIR_API_BASE_URL configuration is missing."


@pytest.mark.asyncio
async def test_retrieve_instrument_missing_cir_endpoint(mocker):
    """Test retrieve_instrument raises HTTPException if CIR_RETRIEVE_CI_ENDPOINT exists but has no value."""
    instrument_id = uuid4()
    # Patch environment to include CIR_API_BASE_URL but not CIR_RETRIEVE_CI_ENDPOINT
    mocker.patch.dict(os.environ, {"CIR_API_BASE_URL": "http://fake-url", "CIR_RETRIEVE_CI_ENDPOINT": ""}, clear=True)
    with pytest.raises(HTTPException) as exc_info:
        await instrument_retrieval_service.retrieve_instrument(instrument_id)
    exc = exc_info.value
    assert exc.status_code == 500
    assert exc.detail["message"] == "CIR_RETRIEVE_CI_ENDPOINT configuration is missing."

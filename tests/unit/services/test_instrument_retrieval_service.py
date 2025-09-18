"""Unit tests for the instrument retrieval service."""

import os
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from eq_cir_proxy_service.services.instrument import instrument_retrieval_service
from eq_cir_proxy_service.services.instrument.instrument_retrieval_service import (
    retrieve_instrument,
)


@pytest.mark.asyncio
async def test_retrieve_instrument_success(mocker):
    """Test the retrieve_instrument function with a successful response."""
    instrument_id = uuid4()

    # Set up fake environment variables
    base_url = "http://fake-base-url/"
    endpoint = "fake-endpoint"
    mocker.patch.dict(os.environ, {"CIR_API_BASE_URL": base_url, "CIR_RETRIEVE_CI_ENDPOINT": endpoint})

    # Create a fake response
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "123"}

    async def fake_get(*_args, **_kwargs):
        return mock_response

    class FakeClient:
        """Fake client for testing."""

        async def get(self, *args, **kwargs):
            """Simulate an async GET request."""
            return await fake_get(*args, **kwargs)

        async def aclose(self):
            """Simulate closing the client."""

    @asynccontextmanager
    async def fake_api_client(**_kwargs):
        yield FakeClient()

    # Patch the iap.get_api_client used inside the service
    mocker.patch(
        "eq_cir_proxy_service.services.instrument.instrument_retrieval_service.get_api_client",
        fake_api_client,
    )

    result = await retrieve_instrument(instrument_id)
    assert result == {"id": "123"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, text_data, side_effect",
    [
        # 404 Not Found case
        (404, "Not Found", None),
        # 500 Server Error case
        (500, "Internal Server Error", None),
        # Connection/Timeout error case
        (None, None, httpx.RequestError("Timeout")),
    ],
)
async def test_retrieve_instrument_exception(
    status_code,
    text_data,
    side_effect,
    mocker,
):
    """Test the retrieve_instrument function with various exception scenarios."""
    instrument_id = uuid4()

    # Set up fake environment variables
    base_url = "http://fake-base-url/"
    endpoint = "fake-endpoint"
    mocker.patch.dict(
        os.environ,
        {"CIR_API_BASE_URL": base_url, "CIR_RETRIEVE_CI_ENDPOINT": endpoint},
    )

    async def fake_get(*_args, **_kwargs):
        """Simulate an async GET request."""
        if side_effect:
            raise side_effect
        mock_response = mocker.Mock()
        mock_response.status_code = status_code
        mock_response.text = text_data
        return mock_response

    class FakeClient:
        """Fake client for testing."""

        async def get(self, *args, **kwargs):
            """Simulate an async GET request."""
            return await fake_get(*args, **kwargs)

        async def aclose(self):  # needed for cleanup
            """Simulate closing the client."""

    @asynccontextmanager
    async def fake_api_client(**_kwargs):
        yield FakeClient()

    mocker.patch(
        "eq_cir_proxy_service.services.instrument.instrument_retrieval_service.get_api_client",
        fake_api_client,
    )

    with pytest.raises(HTTPException) as exc_info:
        await retrieve_instrument(instrument_id)

    # Expect 500 for request errors, or passthrough status otherwise
    expected_status = status_code if status_code is not None else 500
    assert exc_info.value.status_code == expected_status


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

"""Unit tests for the instrument retrieval service."""

import os
from uuid import uuid4

import httpx
import pytest

from eq_cir_proxy_service.services.instrument import retrieval
from eq_cir_proxy_service.services.instrument.retrieval import (
    retrieve_instrument,
)
from tests.unit.conftest import (
    get_fake_api_client,
    make_mock_response,
    run_exception_test,
    run_missing_endpoint_test,
)


@pytest.mark.asyncio
async def test_retrieve_instrument_success(mocker):
    """Test the retrieve_instrument function with a successful response."""
    instrument_id = uuid4()

    # Set up mocked environment variables
    base_url = "http://fake-base-url/"
    endpoint = "fake-endpoint"
    mocker.patch.dict(os.environ, {"CIR_API_BASE_URL": base_url, "CIR_RETRIEVE_CI_ENDPOINT": endpoint})

    # Create a mocked response
    mock_response = make_mock_response(mocker, 200, {"id": "123"})

    async def mock_get(*_args, **_kwargs):
        return mock_response

    # Patch the iap.get_api_client used inside the service
    mocker.patch(
        "eq_cir_proxy_service.services.instrument.retrieval.get_api_client",
        get_fake_api_client(mock_get),
    )

    result = await retrieve_instrument(instrument_id)
    assert result == {"id": "123"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, text_data, side_effect",
    [
        (404, "Not Found", None),
        (500, "Internal Server Error", None),
        (None, None, httpx.RequestError("Timeout")),
    ],
)
async def test_retrieve_instrument_exception(status_code, text_data, side_effect, mocker):
    """Test exceptions in the retrieve_instrument function."""
    instrument_id = uuid4()
    await run_exception_test(
        mocker,
        "eq_cir_proxy_service.services.instrument.retrieval.get_api_client",
        retrieve_instrument,
        instrument_id,
        status_code,
        text_data,
        side_effect,
        {"CIR_API_BASE_URL": "http://fake-base-url/", "CIR_RETRIEVE_CI_ENDPOINT": "fake-endpoint"},
    )


@pytest.mark.asyncio
async def test_retrieve_instrument_missing_cir_endpoint(mocker):
    """Test missing endpoint configuration in the retrieve_instrument function."""
    instrument_id = uuid4()
    await run_missing_endpoint_test(
        mocker,
        retrieval.retrieve_instrument,
        instrument_id,
        {"CIR_API_BASE_URL": "http://fake-url", "CIR_RETRIEVE_CI_ENDPOINT": ""},
        "CIR_RETRIEVE_CI_ENDPOINT configuration is missing.",
    )

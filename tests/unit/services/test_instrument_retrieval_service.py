"""Unit tests for the instrument retrieval service."""

import os
from uuid import uuid4

import pytest
import requests
from fastapi import HTTPException

from eq_cir_proxy_service.services.instrument.instrument_retrieval_service import (
    retrieve_instrument,
)


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
        (None, None, None, requests.RequestException("Timeout"), None, HTTPException),
    ],
)
def test_retrieve_instrument(
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
        mock_get_return = mock_response
    else:
        mock_get_return = side_effect

    # Patch requests.get
    mock_get = mocker.patch(
        "eq_cir_proxy_service.services.instrument.instrument_retrieval_service.requests.get",
        side_effect=[mock_get_return],
    )

    if expected_exception:
        with pytest.raises(expected_exception) as exc_info:
            retrieve_instrument(instrument_id)
        assert exc_info.value.status_code == (status_code if status_code is not None else 500)
    else:
        result = retrieve_instrument(instrument_id)
        assert result == expected_result

    # Only assert call if not simulating an exception before call
    mock_get.assert_called_once_with(f"{base_url}{endpoint}", params={"guid": str(instrument_id)}, timeout=10)

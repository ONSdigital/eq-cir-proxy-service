"""Configuration for unit tests."""

from __future__ import annotations

import os
from collections.abc import Awaitable
from contextlib import asynccontextmanager
from typing import Any, Callable

import pytest
from fastapi import HTTPException
from httpx import AsyncClient


class FakeClient:
    """A fake HTTP client for testing purposes."""

    def __init__(self):
        """Initialise the fake client."""
        self.mock_get: Callable[..., Awaitable[Any]] | None = None

    async def get(self, *args, **kwargs):
        """Simulate an async GET request."""
        none_error = "FakeClient.mock_get must be set before calling get()"
        if self.mock_get is None:
            raise RuntimeError(none_error)
        return await self.mock_get(*args, **kwargs)

    async def aclose(self):
        """Simulate closing the client."""


def make_mock_response(mocker, status_code=200, json_data=None, text_data=None):
    """Create a mocked HTTP response."""
    mock_response = mocker.Mock()
    mock_response.status_code = status_code
    if json_data is not None:
        mock_response.json.return_value = json_data
    if text_data is not None:
        mock_response.text = text_data
    return mock_response


def get_fake_api_client(mock_get):
    """Provide a fake API client with a custom mock_get method."""

    @asynccontextmanager
    async def fake_api_client(**_kwargs):
        client = FakeClient()
        client.mock_get = mock_get
        yield client

    return fake_api_client


@pytest.fixture
def mock_post(monkeypatch):
    """Fixture to patch AsyncClient.post and capture calls + response."""
    captured = {}

    class DummyResponse:  # pylint: disable=too-few-public-methods
        """Minimal dummy response object that mimics httpx.Response for tests."""

        def __init__(self, data, status_code=200):
            """Initialise the dummy response with JSON data and status code."""
            self._data = data
            self.status_code = status_code

        def json(self):
            """Return the mock JSON response data."""
            return self._data

    async def _mock_post(*args, **kwargs):
        """Mock AsyncClient.post that captures call args/kwargs and returns a DummyResponse."""
        captured["args"] = args
        captured["kwargs"] = kwargs
        return DummyResponse(captured.get("response_data", {}))

    monkeypatch.setattr(AsyncClient, "post", _mock_post)

    return {
        "captured": captured,
        "set_response": lambda data, status_code=200: captured.update(response_data=data, status_code=status_code),
    }


async def run_exception_test(
    mocker,
    patch_path: str,
    test_func,
    instrument_id,
    status_code,
    text_data,
    side_effect,
    env_vars,
):
    """Shared logic for exception tests in instrument services."""
    mocker.patch.dict(os.environ, env_vars)

    async def mock_get(*_args, **_kwargs):
        if side_effect:
            raise side_effect
        mock_response = mocker.Mock()
        mock_response.status_code = status_code
        mock_response.text = text_data
        return mock_response

    mocker.patch(
        patch_path,
        get_fake_api_client(mock_get),
    )

    with pytest.raises(HTTPException) as exc_info:
        await test_func(instrument_id)

    expected_status = status_code if status_code is not None else 500
    assert exc_info.value.status_code == expected_status


async def run_missing_endpoint_test(
    mocker,
    test_func,
    instrument_id,
    env_vars,
    expected_message,
):
    """Shared logic for missing endpoint tests in instrument services."""
    mocker.patch.dict(os.environ, env_vars, clear=True)
    with pytest.raises(HTTPException) as exc_info:
        await test_func(instrument_id)
    exc = exc_info.value
    assert exc.status_code == 500
    assert exc.detail["message"] == expected_message

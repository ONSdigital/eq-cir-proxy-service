"""Configuration for unit tests."""

import pytest
from httpx import AsyncClient


@pytest.fixture
def fake_post(monkeypatch):
    """Fixture to patch AsyncClient.post and capture calls + response."""
    captured = {}

    class DummyResponse:  # pylint: disable=too-few-public-methods
        """Minimal dummy response object that mimics httpx.Response for tests."""

        def __init__(self, data, status_code=200):
            """Initialise the dummy response with JSON data and status code."""
            self._data = data
            self.status_code = status_code

        def json(self):
            """Return the fake JSON response data."""
            return self._data

    async def _fake_post(*args, **kwargs):
        """Fake AsyncClient.post that captures call args/kwargs and returns a DummyResponse."""
        captured["args"] = args
        captured["kwargs"] = kwargs
        return DummyResponse(captured.get("response_data", {}))

    monkeypatch.setattr(AsyncClient, "post", _fake_post)

    return {
        "captured": captured,
        "set_response": lambda data, status_code=200: captured.update(response_data=data, status_code=status_code),
    }

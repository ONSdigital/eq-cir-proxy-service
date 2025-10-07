"""Tests for the IAP utility functions."""

import pytest

from eq_cir_proxy_service.utils import iap


def test_get_iap_token_success(monkeypatch):
    """Tests that get_iap_token successfully fetches a token."""
    monkeypatch.setattr(iap.google.oauth2.id_token, "fetch_id_token", lambda *_: "fake-token")
    assert iap.get_iap_token("fake-audience") == "fake-token"


def test_get_iap_token_failure(monkeypatch):
    """Tests that get_iap_token raises RuntimeError when token fetch fails."""
    monkeypatch.setattr(iap.google.oauth2.id_token, "fetch_id_token", lambda *_: None)
    with pytest.raises(RuntimeError, match="Failed to fetch IAP token"):
        iap.get_iap_token("fake-audience")


@pytest.mark.asyncio
async def test_get_api_client_missing_iap_env(monkeypatch):
    """Test that get_api_client sets up the client with correct parameters for local."""
    monkeypatch.setenv("URL_ENV", "https://localhost:1234")
    monkeypatch.delenv("IAP_ENV", raising=False)  # Ensure IAP_ENV is not set
    async with iap.get_api_client(url_env="URL_ENV", iap_env="IAP_ENV") as client:
        assert client.base_url.host == "localhost"


@pytest.mark.asyncio
async def test_get_api_client_empty_iap_env(monkeypatch):
    """Test that get_api_client sets up the client with correct parameters for local."""
    monkeypatch.setenv("URL_ENV", "https://localhost:1234")
    monkeypatch.setenv("IAP_ENV", "")
    async with iap.get_api_client(url_env="URL_ENV", iap_env="IAP_ENV") as client:
        assert client.base_url.host == "localhost"


@pytest.mark.asyncio
async def test_get_api_client_gcp(monkeypatch):
    """Test that get_api_client sets up the client with correct parameters for GCP."""
    monkeypatch.setenv("URL_ENV", "https://example.com")
    monkeypatch.setenv("IAP_ENV", "fake-audience")

    monkeypatch.setattr(iap, "get_iap_token", lambda _: "fake-token")

    async with iap.get_api_client(url_env="URL_ENV", iap_env="IAP_ENV") as client:
        assert client.base_url.host == "example.com"
        assert client.headers["Authorization"] == "Bearer fake-token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url_env, iap_env",
    [
        # get_cir_client
        ("CIR_API_BASE_URL", "CIR_IAP_CLIENT_ID"),
        # get_converter_service_client
        (
            "CONVERTER_SERVICE_API_BASE_URL",
            "CONVERTER_SERVICE_IAP_CLIENT_ID",
        ),
    ],
)
async def test_get_client(url_env, iap_env, monkeypatch):
    """Test the get_converter_service_client function."""
    called_args = {}

    def fake_api_client(url_env, iap_env):  # pylint: disable=unused-argument
        called_args.update(locals())

        class FakeClient:
            """Fake client for testing."""

            async def __aenter__(self):
                return "fake-client"

            async def __aexit__(self, exc_type, exc, tb):
                return None

        return FakeClient()

    monkeypatch.setattr(iap, "get_api_client", fake_api_client)

    async with iap.get_api_client(url_env=url_env, iap_env=iap_env) as client:
        assert client == "fake-client"

    assert called_args["url_env"] == url_env
    assert called_args["iap_env"] == iap_env


@pytest.mark.asyncio
async def test_get_api_client_gcp_missing_url_env(monkeypatch):
    """Test that get_api_client raises RuntimeError if url_env is missing or empty."""
    monkeypatch.delenv("URL_ENV", raising=False)  # Ensure URL_ENV is not set
    monkeypatch.setenv("IAP_ENV", "fake-audience")
    with pytest.raises(RuntimeError, match="Missing or empty environment variable: URL_ENV"):
        async with iap.get_api_client(url_env="URL_ENV", iap_env="IAP_ENV"):
            pass


@pytest.mark.asyncio
async def test_get_api_client_gcp_empty_url_env(monkeypatch):
    """Test that get_api_client raises RuntimeError if url_env is set but empty."""
    monkeypatch.setenv("URL_ENV", "")
    monkeypatch.setenv("IAP_ENV", "fake-audience")
    with pytest.raises(RuntimeError, match="Missing or empty environment variable: URL_ENV"):
        async with iap.get_api_client(url_env="URL_ENV", iap_env="IAP_ENV"):
            pass

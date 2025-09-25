"""Tests for the IAP utility functions."""

import pytest

from eq_cir_proxy_service.utils import iap


def test_unknown_env_error():
    """Tests the unknown_env_error function."""
    env = "invalid_env"
    expected_message = f"Unknown ENV: {env}"
    assert iap.unknown_env_error(env) == expected_message


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
async def test_get_api_client_local(monkeypatch):
    """Test that get_api_client sets up the client with correct parameters for local."""
    monkeypatch.setenv("ENV", "local")
    async with iap.get_api_client(local_url="http://localhost:1234", url_env="URL_ENV", iap_env="IAP_ENV") as client:
        assert client.base_url.host == "localhost"


@pytest.mark.asyncio
async def test_get_api_client_gcp(monkeypatch):
    """Test that get_api_client sets up the client with correct parameters for GCP."""
    monkeypatch.setenv("ENV", "gcp")
    monkeypatch.setenv("URL_ENV", "https://example.com")
    monkeypatch.setenv("IAP_ENV", "fake-audience")

    monkeypatch.setattr(iap, "get_iap_token", lambda _: "fake-token")

    async with iap.get_api_client(local_url="http://localhost:1234", url_env="URL_ENV", iap_env="IAP_ENV") as client:
        assert client.base_url.host == "example.com"
        assert client.headers["Authorization"] == "Bearer fake-token"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "local_url, url_env, iap_env",
    [
        # get_cir_client
        ("http://localhost:5004", "CIR_API_BASE_URL", "CIR_IAP_CLIENT_ID"),
        # get_converter_service_client
        (
            "http://localhost:5010",
            "CONVERTER_SERVICE_API_BASE_URL",
            "CONVERTER_SERVICE_IAP_CLIENT_ID",
        ),
    ],
)
async def test_get_client(local_url, url_env, iap_env, monkeypatch):
    """Test the get_converter_service_client function."""
    monkeypatch.setenv("ENV", "local")

    called_args = {}

    def fake_api_client(local_url, url_env, iap_env):  # pylint: disable=unused-argument
        called_args.update(locals())

        class FakeClient:
            """Fake client for testing."""

            async def __aenter__(self):
                return "fake-client"

            async def __aexit__(self, exc_type, exc, tb):
                return None

        return FakeClient()

    monkeypatch.setattr(iap, "get_api_client", fake_api_client)

    async with iap.get_api_client(local_url=local_url, url_env=url_env, iap_env=iap_env) as client:
        assert client == "fake-client"

    assert called_args["local_url"] == local_url
    assert called_args["url_env"] == url_env
    assert called_args["iap_env"] == iap_env


@pytest.mark.asyncio
async def test_get_cir_client_invalid_env(monkeypatch):
    """Ensure ValueError is raised when ENV is unknown."""
    monkeypatch.setenv("ENV", "nonsense")

    with pytest.raises(ValueError, match="Unknown ENV: nonsense"):
        async with iap.get_api_client(
            local_url="http://localhost:5004",
            url_env="CIR_API_BASE_URL",
            iap_env="CIR_IAP_CLIENT_ID",
        ):
            pass  # should never reach here


@pytest.mark.asyncio
async def test_get_api_client_gcp_missing_url_env(monkeypatch):
    """Test that get_api_client raises RuntimeError if url_env is missing or empty."""
    monkeypatch.setenv("ENV", "gcp")
    monkeypatch.delenv("URL_ENV", raising=False)  # Ensure URL_ENV is not set
    monkeypatch.setenv("IAP_ENV", "fake-audience")
    with pytest.raises(RuntimeError, match="Missing or empty environment variable: URL_ENV"):
        async with iap.get_api_client(local_url="http://localhost:1234", url_env="URL_ENV", iap_env="IAP_ENV"):
            pass


@pytest.mark.asyncio
async def test_get_api_client_gcp_missing_iap_env(monkeypatch):
    """Test that get_api_client raises RuntimeError if iap_env is missing or empty."""
    monkeypatch.setenv("ENV", "gcp")
    monkeypatch.setenv("URL_ENV", "https://example.com")
    monkeypatch.delenv("IAP_ENV", raising=False)  # Ensure IAP_ENV is not set
    with pytest.raises(RuntimeError, match="Missing or empty environment variable: IAP_ENV"):
        async with iap.get_api_client(local_url="http://localhost:1234", url_env="URL_ENV", iap_env="IAP_ENV"):
            pass


@pytest.mark.asyncio
async def test_get_api_client_gcp_empty_url_env(monkeypatch):
    """Test that get_api_client raises RuntimeError if url_env is set but empty."""
    monkeypatch.setenv("ENV", "gcp")
    monkeypatch.setenv("URL_ENV", "")
    monkeypatch.setenv("IAP_ENV", "fake-audience")
    with pytest.raises(RuntimeError, match="Missing or empty environment variable: URL_ENV"):
        async with iap.get_api_client(local_url="http://localhost:1234", url_env="URL_ENV", iap_env="IAP_ENV"):
            pass


@pytest.mark.asyncio
async def test_get_api_client_gcp_empty_iap_env(monkeypatch):
    """Test that get_api_client raises RuntimeError if iap_env is set but empty."""
    monkeypatch.setenv("ENV", "gcp")
    monkeypatch.setenv("URL_ENV", "https://example.com")
    monkeypatch.setenv("IAP_ENV", "")
    with pytest.raises(RuntimeError, match="Missing or empty environment variable: IAP_ENV"):
        async with iap.get_api_client(local_url="http://localhost:1234", url_env="URL_ENV", iap_env="IAP_ENV"):
            pass

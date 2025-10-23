"""Utility functions for handling IAP authentication and HTTP clients."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import google.oauth2.id_token
from google.auth.transport import requests
from httpx import AsyncClient
from structlog import get_logger

logger = get_logger()


def get_iap_token(audience: str) -> str:
    """Fetch an ID token for the IAP-secured resource (blocking)."""
    token: str = google.oauth2.id_token.fetch_id_token(requests.Request(), audience)  # type: ignore[no-untyped-call]
    if token is None:
        logger.error("Failed to fetch IAP token", audience=audience)
        error_message = f"Failed to fetch IAP token for audience {audience}"
        raise RuntimeError(error_message)
    return token


@asynccontextmanager
async def get_api_client(*, url_env: str, iap_env: str) -> AsyncIterator[AsyncClient]:
    """Context-managed httpx.AsyncClient that switches between IAP and non-IAP connections.

    :param url_env: environment variable holding the base URL of the API
    :param iap_env: environment variable holding the IAP client ID of the API
    :raises RuntimeError: if the base URL environment variable is missing or empty

    :yields: an httpx.AsyncClient instance
    """
    base_url = os.getenv(url_env)
    audience = os.getenv(iap_env)

    if not base_url:
        logger.error("Missing or empty environment variable for GCP base URL", var=url_env)
        base_url_error = f"Missing or empty environment variable: {url_env}"
        raise RuntimeError(base_url_error)

    if audience:
        logger.info("Using GCP API client", url_env=url_env, iap_env=iap_env)
        client = AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {get_iap_token(audience)}"},
        )
    else:
        logger.info("No IAP client ID set. Using local API client.")
        client = AsyncClient(base_url=base_url)

    yield client
    await client.aclose()

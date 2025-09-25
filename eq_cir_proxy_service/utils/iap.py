"""Utility functions for handling IAP authentication and HTTP clients."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

import google.auth.transport.requests
import google.oauth2.id_token
from httpx import AsyncClient
from structlog import get_logger

logger = get_logger()


def get_iap_token(audience: str) -> str:
    """Fetch an ID token for the IAP-secured resource (blocking)."""
    request = google.auth.transport.requests.Request()  # type: ignore[no-untyped-call]
    token = google.oauth2.id_token.fetch_id_token(request, audience)  # type: ignore[no-untyped-call]
    if token is None:
        logger.error("Failed to fetch IAP token", audience=audience)
        error_message = f"Failed to fetch IAP token for audience {audience}"
        raise RuntimeError(error_message)
    return cast(str, token)


def unknown_env_error(env: str) -> str:
    """Returns an error message for unknown environment."""
    return f"Unknown ENV: {env}"


@asynccontextmanager
async def get_api_client(*, local_url: str, url_env: str, iap_env: str) -> AsyncIterator[AsyncClient]:
    """Context-managed httpx.AsyncClient that switches between local and GCP/IAP.

    local_url: base URL when ENV=local
    url_env: environment variable holding the GCP base URL
    iap_env: environment variable holding the IAP client ID
    """
    env = os.getenv("ENV", "local")

    if env == "local":
        logger.info("Using local API client", local_url=local_url)
        client = AsyncClient(base_url=local_url)
    elif env == "gcp":
        logger.info("Using GCP API client", url_env=url_env, iap_env=iap_env)

        base_url = os.getenv(url_env)
        audience = os.getenv(iap_env)

        if not base_url:
            logger.error("Missing or empty environment variable for GCP base URL", var=url_env)
            base_url_error = f"Missing or empty environment variable: {url_env}"
            raise RuntimeError(base_url_error)
        if not audience:
            logger.error("Missing or empty environment variable for IAP client ID", var=iap_env)
            iap_error = f"Missing or empty environment variable: {iap_env}"
            raise RuntimeError(iap_error)

        client = AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {get_iap_token(audience)}"},
        )
    else:
        logger.error("Unknown ENV configuration", env=env)
        raise ValueError(unknown_env_error(env))

    try:
        yield client
    finally:
        await client.aclose()

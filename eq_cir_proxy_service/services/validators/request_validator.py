"""This module contains the request validators for the EQ CIR Proxy Service."""

from __future__ import annotations

import semver
from fastapi import HTTPException, status

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.exception import exception_messages

logger = logging.getLogger(__name__)


def validate_version(version: str) -> None:
    """Checks if the version matches the regex pattern.

    Parameters:
    - version: The version to validate.
    """
    try:
        semver.VersionInfo.parse(version)
    except ValueError as exception:
        logger.exception("Invalid version: %s", version)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": exception_messages.EXCEPTION_400_INVALID_VERSION},
        ) from exception

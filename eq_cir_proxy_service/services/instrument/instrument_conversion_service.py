"""This module requests conversion of the instrument from Converter Service."""

import os

from fastapi import HTTPException, status
from httpx import RequestError
from semver import Version
from structlog import get_logger

from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.types.custom_types import Instrument
from eq_cir_proxy_service.utils.iap import get_api_client

logger = get_logger()


def safe_parse(source: str, version: str) -> Version:
    """Safely parses a version string into a Version object."""
    try:
        return Version.parse(version)
    except ValueError as e:
        # Logs full traceback with context
        logger.exception("Error parsing version:", source=source, version=version)
        # Client sees only this clean message
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": f"Invalid {source} version: {version}",
            },
        ) from e


async def convert_instrument(instrument: Instrument, target_version: str) -> Instrument:
    """Requests conversion of the instrument from Converter Service.

    Parameters:
    - instrument: The instrument.
    - current_version: The current version of the instrument.
    - target_version: The target version of the instrument.

    Returns:
    - dict: The converted instrument.
    """
    if not instrument.get("validator_version"):
        logger.error("Instrument version is missing")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": exception_messages.EXCEPTION_400_INVALID_INSTRUMENT},
        )

    current_version = str(instrument["validator_version"])
    parsed_current_version = safe_parse("current", current_version)
    parsed_target_version = safe_parse("target", target_version)

    if parsed_current_version < parsed_target_version:
        logger.debug(
            "Instrument requires updating. Requesting conversion of instrument by Converter Service...",
            current_version=current_version,
            target_version=target_version,
        )

        converter_service_endpoint = os.getenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT", "/schema")

        if not converter_service_endpoint:
            logger.error("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT is not configured.")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "CONVERTER_SERVICE_CONVERT_CI_ENDPOINT configuration is missing.",
                },
            )

        async with get_api_client(
            url_env="CONVERTER_SERVICE_API_BASE_URL",
            iap_env="CONVERTER_SERVICE_IAP_CLIENT_ID",
        ) as converter_service_api_client:
            try:
                response = await converter_service_api_client.post(
                    converter_service_endpoint,
                    json={"instrument": instrument},
                    params={"current_version": current_version, "target_version": target_version},
                )
            except RequestError as e:
                logger.exception("Error occurred while converting instrument.", error=e)
                raise HTTPException(
                    status_code=500,
                    detail={
                        "status": "error",
                        "message": "Error connecting to Converter Service.",
                    },
                ) from e

        instrument_data: Instrument = response.json()
        return instrument_data

    if parsed_current_version == parsed_target_version:
        logger.info("Instrument version matches the target")
        return instrument

    logger.warning("Instrument version is higher than target")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"status": "error", "message": exception_messages.EXCEPTION_400_INVALID_CONVERSION},
    )

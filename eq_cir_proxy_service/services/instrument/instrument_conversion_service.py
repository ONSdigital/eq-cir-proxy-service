"""This module requests conversion of the instrument from Converter Service."""

import os

from fastapi import HTTPException, status
from httpx import AsyncClient, RequestError
from semver import Version

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.types.custom_types import Instrument

logger = logging.getLogger(__name__)


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

    current_version: str = str(instrument["validator_version"])
    parsed_current_version = Version.parse(current_version)
    parsed_target_version = Version.parse(target_version)

    if parsed_current_version < parsed_target_version:
        logger.info("Instrument requires updating")
        logger.info("Calling converter service...")
        logger.info("Requesting conversion for instrument from %s to %s...", current_version, target_version)

        converter_service_base_url = os.getenv("CONVERTER_SERVICE_API_BASE_URL")
        converter_service_endpoint = os.getenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT")
        url = f"{converter_service_base_url}{converter_service_endpoint}"
        try:
            async with AsyncClient(timeout=10) as client:
                response = await client.post(
                    url,
                    json={"instrument": instrument},
                    params={"current_version": str(current_version), "target_version": target_version},
                )
        except RequestError as e:
            logger.exception("Error occurred while converting instrument: %s")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Error connecting to Converter service.",
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

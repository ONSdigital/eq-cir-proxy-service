"""This module requests conversion of the instrument from Converter Service."""

import os
from uuid import UUID

import httpx
from fastapi import HTTPException

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.exceptions.exception_messages import (
    EXCEPTION_404_INSTRUMENT_NOT_FOUND,
    EXCEPTION_500_INSTRUMENT_PROCESSING,
)
from eq_cir_proxy_service.types.custom_types import Instrument

logger = logging.getLogger(__name__)


async def convert_instrument(instrument: Instrument, current_version, target_version) -> Instrument:
    """Requests conversion of the instrument from Converter Service.

    Parameters:
    - instrument: The instrument.
    - current_version: The current version of the instrument.
    - target_version: The target version of the instrument.

    Returns:
    - dict: The converted instrument.
    """
    logger.info("Requesting conversion for instrument from %s to %s...", current_version, target_version)

    converter_service_base_url = os.getenv("CONVERTER_SERVICE_API_BASE_URL")
    converter_service_endpoint = os.getenv("CONVERTER_SERVICE_CONVERT_CI_ENDPOINT")
    url = f"{converter_service_base_url}{converter_service_endpoint}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json={"instrument": instrument}, params={"current_version": current_version, "target_version": target_version})
    except httpx.RequestError as e:
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

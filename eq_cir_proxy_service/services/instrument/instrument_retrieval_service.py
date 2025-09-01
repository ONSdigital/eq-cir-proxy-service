"""This module retrieves the instrument from CIR using the instrument_id."""

import os
from uuid import UUID

from fastapi import HTTPException
from httpx import AsyncClient, RequestError
from structlog import get_logger

from eq_cir_proxy_service.exceptions.exception_messages import (
    EXCEPTION_404_INSTRUMENT_NOT_FOUND,
    EXCEPTION_500_INSTRUMENT_PROCESSING,
)
from eq_cir_proxy_service.types.custom_types import Instrument

logger = get_logger()


async def retrieve_instrument(instrument_id: UUID) -> Instrument:
    """Retrieves the instrument from CIR.

    Parameters:
    - instrument_id: The ID of the instrument.

    Returns:
    - Instrument: The retrieved instrument.
    """
    logger.info("Retrieving instrument %s from CIR...", instrument_id)

    cir_base_url = os.getenv("CIR_API_BASE_URL")
    cir_endpoint = os.getenv("CIR_RETRIEVE_CI_ENDPOINT", "/v2/retrieve_collection_instrument")

    if not cir_base_url:
        logger.error("CIR_API_BASE_URL is not configured.")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "CIR_API_BASE_URL configuration is missing.",
            },
        )
    if not cir_endpoint:
        logger.error("CIR_RETRIEVE_CI_ENDPOINT is not configured.")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "CIR_RETRIEVE_CI_ENDPOINT configuration is missing.",
            },
        )

    url = f"{cir_base_url}{cir_endpoint}"
    try:
        async with AsyncClient() as client:
            response = await client.get(url, params={"guid": str(instrument_id)})
    except RequestError as e:
        logger.exception("Error occurred while retrieving instrument: %s")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Error connecting to CIR service.",
            },
        ) from e

    if response.status_code == 200:
        logger.info("Instrument %s retrieved successfully.", instrument_id)
        instrument_data: Instrument = response.json()
        return instrument_data

    if response.status_code == 404:
        logger.error("Instrument %s not found. Response: %s", instrument_id, response.text)
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": EXCEPTION_404_INSTRUMENT_NOT_FOUND,
            },
        )

    logger.error("Failed to retrieve instrument %s. Status %d: %s", instrument_id, response.status_code, response.text)
    raise HTTPException(
        status_code=500,
        detail={
            "status": "error",
            "message": EXCEPTION_500_INSTRUMENT_PROCESSING,
        },
    )

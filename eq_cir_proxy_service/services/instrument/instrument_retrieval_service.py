"""This module retrieves the instrument from CIR using the instrument_id."""

import os
from uuid import UUID

from fastapi import HTTPException
from httpx import RequestError
from structlog import get_logger

from eq_cir_proxy_service.exceptions.exception_messages import (
    EXCEPTION_404_INSTRUMENT_NOT_FOUND,
    EXCEPTION_500_INSTRUMENT_PROCESSING,
)
from eq_cir_proxy_service.types.custom_types import Instrument
from eq_cir_proxy_service.utils.iap import get_api_client

logger = get_logger()


async def retrieve_instrument(instrument_id: UUID) -> Instrument:
    """Retrieves the instrument from CIR.

    Parameters:
    - instrument_id: The ID of the instrument.

    Returns:
    - Instrument: The retrieved instrument.
    """
    logger.debug("Retrieving instrument from CIR...", instrument_id=instrument_id)

    cir_endpoint = os.getenv("CIR_RETRIEVE_CI_ENDPOINT", "/v2/retrieve_collection_instrument")

    if not cir_endpoint:
        logger.error("CIR_RETRIEVE_CI_ENDPOINT is not configured.")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "CIR_RETRIEVE_CI_ENDPOINT configuration is missing.",
            },
        )

    async with get_api_client(
        local_url="http://localhost:5004",
        url_env="CIR_API_BASE_URL",
        iap_env="CIR_IAP_CLIENT_ID",
    ) as cir_api:
        try:
            response = await cir_api.get(cir_endpoint, params={"guid": str(instrument_id)})
        except RequestError as e:
            logger.exception("Error occurred while retrieving instrument.", error=e)
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Error connecting to CIR service.",
                },
            ) from e

    if response.status_code == 200:
        logger.info("Instrument retrieved successfully.", instrument_id=instrument_id)
        instrument_data: Instrument = response.json()
        return instrument_data

    if response.status_code == 404:
        logger.error("Instrument not found. Response: ", instrument_id=instrument_id, response_text=response.text)
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": EXCEPTION_404_INSTRUMENT_NOT_FOUND,
            },
        )

    logger.error(
        "Failed to retrieve instrument.",
        instrument_id=instrument_id,
        status=response.status_code,
        response_text=response.text,
    )
    raise HTTPException(
        status_code=500,
        detail={
            "status": "error",
            "message": EXCEPTION_500_INSTRUMENT_PROCESSING,
        },
    )

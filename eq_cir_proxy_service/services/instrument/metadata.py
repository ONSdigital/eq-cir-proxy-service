"""This module retrieves the instrument metadata from CIR using the instrument_id."""

import os
from uuid import UUID

from fastapi import HTTPException
from httpx import RequestError
from structlog import get_logger

from eq_cir_proxy_service.exceptions.exception_messages import (
    EXCEPTION_404_INSTRUMENT_METADATA_NOT_FOUND,
    EXCEPTION_500_INSTRUMENT_METADATA_PROCESSING,
)
from eq_cir_proxy_service.types.custom_types import InstrumentMetadata
from eq_cir_proxy_service.utils.check_endpoint import check_endpoint_configured
from eq_cir_proxy_service.utils.iap import get_api_client

logger = get_logger()


async def retrieve_instrument_metadata(instrument_id: UUID) -> InstrumentMetadata:
    """Retrieves the instrument metadata from CIR.

    Parameters:
    - instrument_id: The ID of the instrument.

    Returns:
    - Instrument: The retrieved instrument.
    """
    logger.debug("Retrieving instrument metadata from CIR...", instrument_id=instrument_id)

    cir_endpoint = os.getenv("CIR_RETRIEVE_CI_METADATA_ENDPOINT", "/v3/ci-metadata")

    check_endpoint_configured(
        endpoint=cir_endpoint,
        endpoint_name="CIR_RETRIEVE_CI_METADATA_ENDPOINT",
        endpoint_error_message="CIR_RETRIEVE_CI_METADATA_ENDPOINT configuration is missing.",
    )

    async with get_api_client(
        url_env="CIR_API_BASE_URL",
        iap_env="CIR_IAP_CLIENT_ID",
    ) as cir_api_client:
        try:
            response = await cir_api_client.get(cir_endpoint, params={"guid": str(instrument_id)})
        except RequestError as e:
            logger.exception("Error occurred while retrieving instrument metadata.", error=e)
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Error connecting to CIR service.",
                },
            ) from e

    if response.status_code == 200:
        logger.info("Instrument metadata retrieved successfully.", instrument_id=instrument_id)
        instrument_data: InstrumentMetadata = response.json()
        return instrument_data

    if response.status_code == 404:
        logger.error(
            "Instrument metadata not found. Response: ",
            instrument_id=instrument_id,
            response_text=response.text,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": EXCEPTION_404_INSTRUMENT_METADATA_NOT_FOUND,
            },
        )

    logger.error(
        "Failed to retrieve instrument metadata.",
        instrument_id=instrument_id,
        status=response.status_code,
        response_text=response.text,
    )
    raise HTTPException(
        status_code=500,
        detail={
            "status": "error",
            "message": EXCEPTION_500_INSTRUMENT_METADATA_PROCESSING,
        },
    )

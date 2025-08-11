"""This module retrieves the instrument from CIR using the instrument_id."""

import os
from uuid import UUID

import requests
from fastapi import HTTPException

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.exceptions.exception_messages import (
    EXCEPTION_404_INSTRUMENT_NOT_FOUND,
    EXCEPTION_500_INSTRUMENT_PROCESSING,
)
from eq_cir_proxy_service.types.custom_types import Instrument

logger = logging.getLogger(__name__)


def retrieve_instrument(instrument_id: UUID) -> Instrument:
    """Retrieves the instrument from CIR.

    Parameters:
    - instrument_id: The ID of the instrument.
    - target_version: The target version of the instrument.

    Returns:
    - dict: The retrieved instrument.
    """
    logger.info("Retrieving instrument %s from CIR...", instrument_id)

    cir_base_url = os.getenv("CIR_API_BASE_URL")
    cir_endpoint = os.getenv("CIR_RETRIEVE_CI_ENDPOINT")
    url = f"{cir_base_url}{cir_endpoint}"
    try:
        response = requests.get(url, params={"guid": str(instrument_id)}, timeout=10)
    except requests.RequestException as e:
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

"""Module defines the instrument router for handling requests related to instruments in the EQ CIR Proxy Service."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query, status
from semver import compare

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.services.instrument import instrument_conversion_service, instrument_retrieval_service
from eq_cir_proxy_service.services.validators.request_validator import (
    validate_version,
)
from eq_cir_proxy_service.types.custom_types import Instrument

router = APIRouter()
logger = logging.getLogger(__name__)
INSTRUMENT_ID_PATH = Path(..., description="UUIDv4 of the instrument")


@router.get("/instrument/{instrument_id}")
async def get_instrument_by_uuid(
    instrument_id: UUID = INSTRUMENT_ID_PATH,
    version: str = Query(description="Optional version of the instrument"),
) -> Instrument:
    """Retrieve an instrument by its UUID and optional version."""
    logger.info("Receiving the instrument id...")
    logger.debug("Received instrument id: %s", instrument_id)

    try:
        logger.debug("Received version: %s", version)
        logger.info("Validating the version...")
        validate_version(version)
        target_version = version

        instrument = await instrument_retrieval_service.retrieve_instrument(instrument_id)

        if not instrument.get("validator_version"):
            logger.error("Instrument version is missing")
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"status": "error", "message": exception_messages.EXCEPTION_400_INVALID_INSTRUMENT},
            )

        version_compare = compare(instrument.get("validator_version"), target_version)
        if version_compare < 0:
            logger.info("Instrument requires updating")
            logger.info("Calling converter service...")
            converted_instrument = await instrument_conversion_service.convert_instrument(instrument, instrument.get("validator_version"), target_version)
            return converted_instrument
        elif version_compare == 0:
            logger.info("Instrument version matches the target")
            return instrument
        else:
            logger.warning("Instrument version is higher than target")
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"status": "error", "message": exception_messages.EXCEPTION_400_INVALID_CONVERSION},
            )

    except HTTPException:
        raise  # re-raise so FastAPI handles it properly
    except Exception as exc:
        logger.exception("An exception occurred while processing the instrument")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": exception_messages.EXCEPTION_500_INSTRUMENT_PROCESSING,
            },
        ) from exc

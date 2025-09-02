"""Module defines the instrument router for handling requests related to instruments in the EQ CIR Proxy Service."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query
from structlog import get_logger

from eq_cir_proxy_service.exceptions import exception_messages
from eq_cir_proxy_service.services.instrument import (
    instrument_conversion_service,
    instrument_retrieval_service,
)
from eq_cir_proxy_service.services.validators.request_validator import (
    validate_version,
)
from eq_cir_proxy_service.types.custom_types import Instrument

router = APIRouter()
logger = get_logger()
INSTRUMENT_ID_PATH = Path(..., description="UUIDv4 of the instrument")


@router.get("/instrument/{instrument_id}")
async def get_instrument_by_uuid(
    instrument_id: UUID = INSTRUMENT_ID_PATH,
    version: str = Query(description="Validator version of the instrument required"),
) -> Instrument:
    """Retrieve an instrument by its UUID and version."""
    logger.info("Receiving the instrument id...")
    logger.debug("Instrument received successfully.", instrument_id=instrument_id)

    try:
        logger.debug("Received version.", version=version)
        logger.info("Validating the version...")
        validate_version(version)
        target_version = version

        instrument = await instrument_retrieval_service.retrieve_instrument(instrument_id)

        return await instrument_conversion_service.convert_instrument(instrument, target_version)

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

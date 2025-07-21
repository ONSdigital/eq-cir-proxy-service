"""Module defines the instrument router for handling requests related to instruments in the EQ CIR Proxy Service."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Query

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.exception import exception_messages
from eq_cir_proxy_service.services.schema import schema_retrieval_service
from eq_cir_proxy_service.services.validators.request_validator import (
    validate_version,
)
from eq_cir_proxy_service.types.custom_types import Schema

router = APIRouter()
logger = logging.getLogger(__name__)
INSTRUMENT_ID_PATH = Path(..., description="UUIDv4 of the instrument")


@router.get("/instrument/{instrument_id}")
async def get_instrument_by_uuid(
    instrument_id: UUID = INSTRUMENT_ID_PATH,
    version: str = Query(default=None, description="Optional version of the instrument"),
) -> Schema:
    """Retrieve an instrument by its UUID and optional version."""
    logger.info("Receiving the instrument id...")
    logger.debug("Received instrument id: %s", instrument_id)

    try:
        if version is not None:
            logger.debug("Received version: %s", version)
            logger.info("Validating the version...")
            validate_version(version)

        return await schema_retrieval_service.retrieve_schema(instrument_id, version)

    except HTTPException:
        raise  # re-raise so FastAPI handles it properly
    except Exception as exc:
        logger.exception("An exception occurred while processing the schema")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": exception_messages.EXCEPTION_500_SCHEMA_PROCESSING,
            },
        ) from exc

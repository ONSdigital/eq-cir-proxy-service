"""This module retrieves the schema from CIR using the instrument_id."""

from uuid import UUID

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.types.custom_types import Schema

logger = logging.getLogger(__name__)


async def retrieve_instrument(instrument_id: UUID, target_version: str) -> Schema:
    """Retrieves the instrument from CIR.

    Parameters:
    - instrument_id: The ID of the instrument.
    - target_version: The target version of the instrument.

    Returns:
    - dict: The retrieved instrument.
    """
    logger.info("Retrieving the instrument...")

    # TODO: Implement the call to CIR to retrieve the instrument
    # For now, return a dummy instrument
    instrument = {
        "language": "en",
        "mime_type": "application/json/ons/eq",
        "schema_version": "0.0.1",
        "data_version": "0.0.1",
        "survey_id": "999",
        "form_type": "0001",
        "title": "Dummy Schema",
        "id": instrument_id,
        "validator_version": "1.0.0",
        "theme": "business",
        "metadata": [
            {"name": "ru_ref", "type": "string"},
            {"name": "ru_name", "type": "string"},
        ],
    }

    logger.debug("Instrument validator version: %s", instrument["validator_version"])
    logger.debug("Required validator version: %s", target_version)

    return dict(instrument)

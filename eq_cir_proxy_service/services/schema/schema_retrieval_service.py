"""This module retrieves the schema from CIR using the instrument_id."""

from uuid import UUID

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.types.custom_types import Schema

logger = logging.getLogger(__name__)


async def retrieve_schema(instrument_id: UUID, target_version: str) -> Schema:
    """Retrieves the schema from CIR.

    Parameters:
    - instrument_id: The ID of the instrument.
    - target_version: The target version of the schema.

    Returns:
    - dict: The retrieved schema.
    """
    logger.info("Retrieving the schema...")

    # TODO: Implement the call to CIR to retrieve the schema
    # For now, return a dummy schema
    schema = {
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

    logger.debug("Schema validator version: %s", schema["validator_version"])
    logger.debug("Required validator version: %s", target_version)

    return dict(schema)

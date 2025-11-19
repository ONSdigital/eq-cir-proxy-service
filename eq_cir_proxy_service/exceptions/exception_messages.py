"""This module contains the exception messages for the EQ CIR Proxy Service."""

import typing

EXCEPTION_500_INSTRUMENT_PROCESSING = "Error encountered while processing the instrument_id."

EXCEPTION_500_INSTRUMENT_METADATA_PROCESSING = "Error encountered while processing the instrument metadata."

EXCEPTION_400_INVALID_VERSION = (
    "Invalid version format. The version must be in the format x.y.z where x, y, z are numbers."
)

EXCEPTION_404_INSTRUMENT_NOT_FOUND = "Instrument not found for the provided instrument_id."

EXCEPTION_404_INSTRUMENT_METADATA_NOT_FOUND = "Instrument metadata not found for the provided instrument_id."

EXCEPTION_400_INVALID_CONVERSION = "Target version is lower than instrument version."

EXCEPTION_400_INVALID_INSTRUMENT = "Received instrument is not valid."


def exception_404_missing_instrument_id(path: str) -> str:
    """Returns the exception message for a missing instrument_id."""
    return f"404 - instrument_id not provided or route not found: {path}"


def exception_422_invalid_instrument_id(instrument_id: typing.Any) -> typing.Any:
    """Returns the exception message for an invalid instrument_id."""
    return f"Invalid UUID received for instrument_id: {instrument_id}"

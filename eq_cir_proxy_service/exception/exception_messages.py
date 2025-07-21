"""This module contains the exception messages for the EQ CIR Proxy Service."""

EXCEPTION_500_INSTRUMENT_PROCESSING = "Error encountered while processing the instrument_id"

EXCEPTION_400_EMPTY_INSTRUMENT_ID = "Input instrument id is empty"

EXCEPTION_400_INVALID_VERSION = (
    "Invalid version format. The version must be in the format x.y.z where x, y, z are numbers."
)

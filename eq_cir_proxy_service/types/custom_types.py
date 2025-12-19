"""This module defines custom types used in the EQ CIR Proxy Service."""

from collections.abc import Mapping

# Define the type for the instrument
Instrument = dict[str, bool | int | str | list | object]

# Define the type for the instrument metadata
InstrumentMetadata = Mapping[str, bool | int | str]

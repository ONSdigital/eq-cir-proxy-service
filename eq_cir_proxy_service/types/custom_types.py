"""This module defines custom types used in the EQ CIR Proxy Service."""

# Define the type for the instrument
Instrument = dict[str, bool | int | str | list | object]

# Define the type for the instrument
InstrumentMetadata = list[dict[str, bool | int | str]]

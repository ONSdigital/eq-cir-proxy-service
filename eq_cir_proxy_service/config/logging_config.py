"""Configure the logging level for the application."""

import logging
import os


def get_log_level() -> int:
    """Get the logging level from the LOG_LEVEL environment variable, or use the default value of INFO."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    return int(getattr(logging, log_level, logging.INFO))


logging.basicConfig(
    level=get_log_level(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

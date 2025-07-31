"""Unit tests for logging configuration."""

import logging
import os

import pytest

from eq_cir_proxy_service.config import logging_config


@pytest.mark.parametrize(
    "env_value, expected_level",
    [
        ("", logging.INFO),  # Default log level
        ("DEBUG", logging.DEBUG),  # Custom log level
    ],
)
def test_get_log_level(env_value, expected_level):
    """Test that the logging level is set correctly based on the LOG_LEVEL environment variable."""
    os.environ["LOG_LEVEL"] = env_value
    log_level = logging_config.get_log_level()
    assert log_level == expected_level

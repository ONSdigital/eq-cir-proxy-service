"""Unit tests for logging configuration."""

import logging
import os

from eq_cir_proxy_service.config import logging_config


def test_get_log_level():
    """Test that the logging level is set to INFO by default."""
    os.environ["LOG_LEVEL"] = ""
    log_level = logging_config.get_log_level()
    assert log_level == logging.INFO


def test_get_log_level_custom():
    """Test that the logging level is set to DEBUG when the LOG_LEVEL environment variable is set to DEBUG."""
    os.environ["LOG_LEVEL"] = "DEBUG"
    log_level = logging_config.get_log_level()
    assert log_level == logging.DEBUG

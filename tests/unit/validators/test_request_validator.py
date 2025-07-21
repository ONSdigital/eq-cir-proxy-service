"""Unit tests for the request validator module, specifically for the version validation function."""

import pytest
from fastapi import HTTPException

from eq_cir_proxy_service.services.validators.request_validator import validate_version


def test_validate_version_valid():
    """Test that the validate_version function correctly validates valid version strings."""
    # Should not raise exception for valid version
    valid_versions = [
        "1.0.0",
        "0.1.2",
        "10.20.30",
        "999.999.999",
    ]
    for version in valid_versions:
        validate_version(version)


def test_validate_version_invalid():
    """Test that the validate_version function raises HTTPException for invalid version strings."""
    # Should raise HTTPException for invalid version
    invalid_versions = [
        "1.0",
        "1.0.0.0",
        "a.b.c",
        "1.0.a",
        "01.0.0",
        "1.00.0",
        "1.0.00",
        "1..0",
        "",
        None,
    ]
    for version in invalid_versions:
        if version is None:
            with pytest.raises(TypeError):
                validate_version(version)
        else:
            with pytest.raises(HTTPException) as exc_info:
                validate_version(version)
            assert exc_info.value.status_code == 400

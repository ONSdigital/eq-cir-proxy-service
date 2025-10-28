"""Unit tests for the request validator module, specifically for the version validation function."""

import pytest
from fastapi import HTTPException

from eq_cir_proxy_service.services.validators.request import validate_version


@pytest.mark.parametrize(
    "version",
    [
        "1.0.0",
        "0.1.2",
        "10.20.30",
        "999.999.999",
    ],
)
def test_validate_version_valid(version):
    """Test that the validate_version function correctly validates valid version strings."""
    # Should not raise exception for valid version
    assert validate_version(version) is None


@pytest.mark.parametrize(
    "version",
    [
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
    ],
)
def test_validate_version_invalid(version):
    """Test that the validate_version function raises HTTPException for invalid version strings."""
    # Should raise HTTPException for invalid version
    if version is None:
        with pytest.raises(TypeError):
            assert validate_version(version) is None
    else:
        with pytest.raises(HTTPException) as exc_info:
            validate_version(version)
        assert exc_info.value.status_code == 400

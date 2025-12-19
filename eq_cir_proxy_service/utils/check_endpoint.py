"""Check endpoint utility functions."""

from fastapi import HTTPException
from structlog import get_logger

logger = get_logger()


def check_endpoint_configured(endpoint: str, endpoint_name: str, endpoint_error_message: str) -> None:
    """Check if the given endpoint is configured.

    Args:
        endpoint (str): The endpoint URL to check.
        endpoint_name (str): The name of the endpoint for logging purposes.
        endpoint_error_message (str): The error message to use if the endpoint is not configured.

    Raises:
        ValueError: If the endpoint is not configured.
    """
    if not endpoint:
        logger.error("%s is not configured.", endpoint_name)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": endpoint_error_message,
            },
        )

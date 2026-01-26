"""Check endpoint utility functions."""

from fastapi import HTTPException
from structlog import get_logger

logger = get_logger()


def check_endpoint_configured(endpoint: str, endpoint_name: str) -> None:
    """Check if the given endpoint is configured.

    Args:
        endpoint (str): The endpoint URL to check.
        endpoint_name (str): The name of the endpoint for logging purposes.

    Raises:
        ValueError: If the endpoint is not configured.
    """
    if not endpoint:
        logger.error("%s is not configured.", endpoint_name)
        endpoint_error_message = f"{endpoint_name} configuration is missing."
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": endpoint_error_message,
            },
        )

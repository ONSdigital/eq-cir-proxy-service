"""This module contains a sample FastAPI router for testing purposes."""

from fastapi import APIRouter, HTTPException

router = APIRouter()

"""Endpoint to return `Hello world`."""


@router.get(
    "/sample",
    response_model=dict[str, bool | int | str | list | object],
)
async def get_hello_world() -> dict[str, bool | int | str | list | object]:
    """Returns a sample dictionary with a `Hello world` message."""

    try:
        return await {"message": "Hello world"}

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Sample error"},
        ) from exc

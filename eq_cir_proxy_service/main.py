"""Entry point for the FastAPI application."""

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from eq_cir_proxy_service.config.logging_config import setup_logging
from eq_cir_proxy_service.exceptions.exception_messages import (
    exception_404_missing_instrument_id,
    exception_422_invalid_instrument_id,
)
from eq_cir_proxy_service.routers import instrument

# Load .env file
load_dotenv(".env")

setup_logging()

app = FastAPI()
logger = structlog.get_logger()


@app.get("/")
async def root() -> dict:
    """Root endpoint returning JSON response."""
    return {"message": "Hello World"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Custom exception handler for validation errors, to allow logging of any errors."""
    for error in exc.errors():
        loc = error.get("loc", [])
        if "path" in loc and "instrument_id" in loc:
            invalid_instrument_id = request.path_params.get("instrument_id")
            logger.warning(exception_422_invalid_instrument_id(invalid_instrument_id))

    logger.error("Validation error details: ", error=exc.errors())

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Custom exception handler for HTTP exceptions, to log /instrument 404 errors."""
    if exc.status_code == 404 and request.url.path.startswith("/instrument"):
        logger.error(exception_404_missing_instrument_id(request.url.path))
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(instrument.router)

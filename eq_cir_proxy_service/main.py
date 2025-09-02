"""Entry point for the FastAPI application."""

import logging
import os
import sys

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from eq_cir_proxy_service.exceptions.exception_messages import (
    exception_404_missing_instrument_id,
    exception_422_invalid_instrument_id,
)
from eq_cir_proxy_service.routers import instrument_router

# Load .env file
load_dotenv(".env")

LOG_LEVEL = logging.DEBUG if os.getenv("LOG_LEVEL") == "DEBUG" else logging.INFO

error_log_handler = logging.StreamHandler(sys.stderr)
error_log_handler.setLevel(logging.ERROR)


renderer_processor = (
    structlog.dev.ConsoleRenderer() if LOG_LEVEL == logging.DEBUG else structlog.processors.JSONRenderer()
)

logging.basicConfig(level=LOG_LEVEL, format="%(message)s", stream=sys.stdout)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        renderer_processor,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

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


app.include_router(instrument_router.router)

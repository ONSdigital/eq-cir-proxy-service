"""Entry point for the FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from eq_cir_proxy_service.config.logging_config import logging
from eq_cir_proxy_service.routers import instrument_router

app = FastAPI()
logger = logging.getLogger(__name__)


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
            logger.warning("Invalid UUID received for instrument_id: %s", request.path_params.get("instrument_id"))

    logger.error("Validation error details: %s", exc.errors())

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Custom exception handler for HTTP exceptions, to log /instrument 404 errors."""
    if exc.status_code == 404 and request.url.path.startswith("/instrument"):
        logger.error("404 - instrument_id not provided or route not found: %s", request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


app.include_router(instrument_router.router)

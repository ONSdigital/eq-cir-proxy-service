"""This module is the entry point of the FastAPI application."""

import fastapi

from eq_cir_proxy_service.routers import sample_router

app = fastapi.FastAPI()

app.include_router(sample_router.router)


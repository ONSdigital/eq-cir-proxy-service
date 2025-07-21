"""Entry point for the FastAPI application."""

from fastapi import FastAPI

from eq_cir_proxy_service.routers import instrument_router

app = FastAPI()


@app.get("/")
async def root() -> dict:
    """Root endpoint returning JSON response."""
    return {"message": "Hello World"}


app.include_router(instrument_router.router)

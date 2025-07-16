"""Entry point for the FastAPI application."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root() -> dict:
    """Root endpoint returning JSON response."""
    return {"message": "Hello World"}
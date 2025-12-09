"""Vercel entrypoint - imports FastAPI app from app.api.main."""
from app.api.main import app

__all__ = ["app"]


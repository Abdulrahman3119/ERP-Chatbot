"""FastAPI application factory and configuration."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import chat, health, root


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="IDO Assistant API",
        version="1.0.0",
        description="AI-powered assistant for interacting with the IDO system",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(root.router)
    app.include_router(health.router)
    app.include_router(chat.router)

    return app


# Create app instance
app = create_app()


"""FastAPI application factory and configuration."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback


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

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        import os
        error_detail = {
            "error": type(exc).__name__,
            "message": str(exc),
        }
        # Include traceback in non-production
        if os.getenv("VERCEL_ENV") != "production":
            error_detail["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_detail
        )

    # Validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body}
        )

    # Import and include routers
    try:
        from app.api.routers import chat, health, root
        
        app.include_router(root.router)
        app.include_router(health.router)
        app.include_router(chat.router)
    except ImportError as e:
        # If routers fail to import, create a minimal error endpoint
        @app.get("/")
        async def error_root():
            return {
                "error": "Router Import Failed",
                "message": str(e),
                "help": "Check that all router modules are properly configured"
            }

    return app


# Create app instance - this will be imported by the handler
app = create_app()


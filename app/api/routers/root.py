"""Root router for API information."""
from fastapi import APIRouter
from app.api.schemas import RootResponse

router = APIRouter(tags=["root"])


@router.get("/", response_model=RootResponse)
async def root():
    """
    Root endpoint with API information and guidance.
    
    Returns:
        API information and available endpoints
    """
    return RootResponse(
        service="IDO Assistant API",
        status="ok",
        endpoints={
            "health": "/health",
            "chat": "/chat",
            "docs": "/docs",
        },
        message="Send POST /chat with credentials and message",
        request_format={
            "message": "User prompt (required)",
            "conversation_id": "Optional conversation ID for context",
            "include_history": "Whether to include conversation history (default: true)",
            "openai_api_key": "OpenAI API key (optional if set in env)",
            "ido_base_url": "IDO system base URL (optional if set in env)",
            "ido_api_key": "IDO API key (optional if set in env)",
            "ido_api_secret": "IDO API secret (optional if set in env)",
        },
        note="Credentials can be provided in request or as environment variables",
    )


from functools import lru_cache
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field 

from app.config import Settings, load_settings
from app.presentation.agent import build_agent


class Message(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    include_history: bool = Field(True, description="Whether to include conversation history")
    # Credentials - can be provided in request or fallback to environment variables
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    ido_base_url: Optional[str] = Field(None, description="IDO system base URL")
    ido_api_key: Optional[str] = Field(None, description="IDO API key")
    ido_api_secret: Optional[str] = Field(None, description="IDO API secret")


class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings from environment variables (fallback)."""
    return load_settings()


def create_settings_from_request(
    openai_api_key: Optional[str] = None,
    ido_base_url: Optional[str] = None,
    ido_api_key: Optional[str] = None,
    ido_api_secret: Optional[str] = None,
) -> Settings:
    """Create Settings from request credentials, with fallback to environment variables."""
    from app.config import load_settings
    import os
    
    # Try to load from environment as fallback
    try:
        env_settings = load_settings()
        final_openai_key = openai_api_key or env_settings.openai_api_key
        final_base_url = ido_base_url or env_settings.erpnext_base_url
        final_api_key = ido_api_key or env_settings.erpnext_api_key
        final_api_secret = ido_api_secret or env_settings.erpnext_api_secret
    except ValueError:
        # No environment variables set, use request values only
        final_openai_key = openai_api_key
        final_base_url = ido_base_url
        final_api_key = ido_api_key
        final_api_secret = ido_api_secret
    
    # Validate that we have all required credentials
    missing = []
    if not final_openai_key:
        missing.append("openai_api_key")
    if not final_base_url:
        missing.append("ido_base_url")
    if not final_api_key:
        missing.append("ido_api_key")
    if not final_api_secret:
        missing.append("ido_api_secret")
    
    if missing:
        raise ValueError(
            f"Missing required credentials: {', '.join(missing)}. "
            "Provide them in the request or set as environment variables."
        )
    
    # Use default values for other settings
    default_timeout = 15
    default_max_records = 100
    default_max_iterations = 10
    default_filter_types = (
        "Data", "Date", "Datetime", "DateTime", "Link", "Select", "Int", "Float"
    )
    
    return Settings(
        openai_api_key=final_openai_key,
        erpnext_base_url=final_base_url,
        erpnext_api_key=final_api_key,
        erpnext_api_secret=final_api_secret,
        request_timeout=default_timeout,
        max_records_limit=default_max_records,
        max_iterations=default_max_iterations,
        filter_field_types=default_filter_types,
    )


def build_agent_for_request(settings: Settings):
    """Build agent instance with provided settings."""
    return build_agent(settings)


# In-memory conversation storage (for short-term memory)
# In production, use Redis or a database
conversation_store: Dict[str, Dict] = {}


def get_conversation_history(conversation_id: Optional[str]) -> List[Dict]:
    """Retrieve conversation history for a given ID."""
    if not conversation_id:
        return []
    
    conversation = conversation_store.get(conversation_id)
    if not conversation:
        return []
    
    # Check if conversation is expired (24 hours)
    if datetime.now() - conversation.get("created_at", datetime.now()) > timedelta(hours=24):
        del conversation_store[conversation_id]
        return []
    
    return conversation.get("messages", [])


def save_conversation_message(
    conversation_id: str, role: str, content: str
) -> None:
    """Save a message to conversation history."""
    if conversation_id not in conversation_store:
        conversation_store[conversation_id] = {
            "created_at": datetime.now(),
            "messages": [],
        }
    
    conversation_store[conversation_id]["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    
    # Keep only last 20 messages for context
    messages = conversation_store[conversation_id]["messages"]
    if len(messages) > 20:
        conversation_store[conversation_id]["messages"] = messages[-20:]


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title="IDO Assistant API", version="1.0.0")

    # Allow public cross-origin access; tighten origins if needed.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        """Landing endpoint with basic guidance."""
        return {
            "service": "IDO Assistant API",
            "status": "ok",
            "endpoints": {
                "health": "/health",
                "chat": "/chat",
                "docs": "/docs",
            },
            "message": "Send POST /chat with credentials and message",
            "request_format": {
                "message": "User prompt (required)",
                "conversation_id": "Optional conversation ID for context",
                "include_history": "Whether to include conversation history (default: true)",
                "openai_api_key": "OpenAI API key (optional if set in env)",
                "ido_base_url": "IDO system base URL (optional if set in env)",
                "ido_api_key": "IDO API key (optional if set in env)",
                "ido_api_secret": "IDO API secret (optional if set in env)",
            },
            "note": "Credentials can be provided in request or as environment variables",
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest):
        try:
            # Create settings from request credentials (with fallback to env vars)
            settings = create_settings_from_request(
                openai_api_key=body.openai_api_key,
                ido_base_url=body.ido_base_url,
                ido_api_key=body.ido_api_key,
                ido_api_secret=body.ido_api_secret,
            )
            
            # Build agent with request-specific settings
            agent = build_agent_for_request(settings)
            
            # Generate or use conversation ID
            conversation_id = body.conversation_id or f"conv_{datetime.now().timestamp()}"
            
            # Build message history
            messages = []
            if body.include_history:
                history = get_conversation_history(conversation_id)
                messages.extend(history)
            
            # Add current user message
            messages.append({"role": "user", "content": body.message})
            
            # Save user message
            save_conversation_message(conversation_id, "user", body.message)
            
            # Invoke agent with conversation history
            result = agent.invoke(
                {"messages": messages},
                max_iterations=settings.max_iterations,
            )
            
            # Get assistant response
            assistant_reply = result["messages"][-1].content
            
            # Save assistant response
            save_conversation_message(conversation_id, "assistant", assistant_reply)
            
            return ChatResponse(
                reply=assistant_reply,
                conversation_id=conversation_id,
            )
        except ValueError as exc:
            # Handle missing credentials error
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - surface as HTTP error
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()


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


class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings."""
    return load_settings()


@lru_cache
def get_agent():
    """Build and cache the agent instance."""
    settings = get_settings()
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
            "message": "Send POST /chat with {'message': '<your prompt>'}",
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest):
        try:
            settings = get_settings()
            agent = get_agent()
            
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
        except Exception as exc:  # pragma: no cover - surface as HTTP error
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()


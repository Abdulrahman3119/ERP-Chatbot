from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field 

from app.config import Settings, load_settings
from app.presentation.agent import build_agent


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User prompt")


class ChatResponse(BaseModel):
    reply: str


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings."""
    return load_settings()


@lru_cache
def get_agent():
    """Build and cache the agent instance."""
    settings = get_settings()
    return build_agent(settings)


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
            result = agent.invoke(
                {"messages": [{"role": "user", "content": body.message}]},
                max_iterations=settings.max_iterations,
            )
            return ChatResponse(reply=result["messages"][-1].content)
        except Exception as exc:  # pragma: no cover - surface as HTTP error
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    return app


app = create_app()


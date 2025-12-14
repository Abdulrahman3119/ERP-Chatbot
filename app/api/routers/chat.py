"""Chat router for handling chat requests."""
from fastapi import APIRouter, HTTPException
from app.api.schemas import ChatRequest, ChatResponse
from app.api.dependencies import create_settings_from_request
from app.api.services import conversation_service, agent_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat requests with the AI assistant.
    
    Args:
        request: Chat request with message and optional credentials
    
    Returns:
        Chat response with assistant reply and conversation ID
    
    Raises:
        HTTPException: If there's an error processing the request
    """
    try:
        # Create settings from request (with fallback to env vars)
        settings = create_settings_from_request(request)
        # Generate or use conversation ID
        conversation_id = (
            request.conversation_id 
            or conversation_service.generate_conversation_id()
        )
        
        # Build message history
        messages = []
        if request.include_history:
            history = conversation_service.get_history(conversation_id)
            messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": request.message})
        
        # Save user message
        conversation_service.save_message(
            conversation_id, 
            "user", 
            request.message
        )
        
        # Build agent with settings
        agent = agent_service.build_agent(settings)
        
        # Invoke agent with conversation history
        result = agent.invoke(
            {"messages": messages},
            max_iterations=settings.max_iterations,
        )
        
        # Get assistant response
        assistant_reply = result["messages"][-1].content
        
        # Save assistant response
        conversation_service.save_message(
            conversation_id, 
            "assistant", 
            assistant_reply
        )
        
        return ChatResponse(
            reply=assistant_reply,
            conversation_id=conversation_id,
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as exc:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(exc)}"
        ) from exc


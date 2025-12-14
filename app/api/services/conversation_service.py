"""Service for managing conversation storage and history."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ConversationService:
    """Service for managing conversation storage."""
    
    def __init__(self):
        """Initialize conversation storage."""
        # In-memory conversation storage (for short-term memory)
        # In production, use Redis or a database
        self._store: Dict[str, Dict] = {}
        self._expiration_hours = 24
        self._max_messages = 20
    
    def get_history(self, conversation_id: Optional[str]) -> List[Dict]:
        """
        Retrieve conversation history for a given ID.
        
        Args:
            conversation_id: Optional conversation ID
        
        Returns:
            List of message dictionaries
        """
        if not conversation_id:
            return []
        
        conversation = self._store.get(conversation_id)
        if not conversation:
            return []
        
        # Check if conversation is expired
        created_at = conversation.get("created_at", datetime.now())
        if datetime.now() - created_at > timedelta(hours=self._expiration_hours):
            del self._store[conversation_id]
            return []
        
        return conversation.get("messages", [])
    
    def save_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str
    ) -> None:
        """
        Save a message to conversation history.
        
        Args:
            conversation_id: Conversation ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if conversation_id not in self._store:
            self._store[conversation_id] = {
                "created_at": datetime.now(),
                "messages": [],
            }
        
        self._store[conversation_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Keep only last N messages for context
        messages = self._store[conversation_id]["messages"]
        if len(messages) > self._max_messages:
            self._store[conversation_id]["messages"] = messages[-self._max_messages:]
    
    def generate_conversation_id(self) -> str:
        """
        Generate a new conversation ID.
        
        Returns:
            New conversation ID string
        """
        return f"conv_{datetime.now().timestamp()}"


# Global instance
conversation_service = ConversationService()


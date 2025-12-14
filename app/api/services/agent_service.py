"""Service for building and managing agent instances."""
from functools import lru_cache
from app.config import Settings
from app.presentation.agent import build_agent


class AgentService:
    """Service for managing agent instances."""
    
    @staticmethod
    def build_agent(settings: Settings):
        """
        Build agent instance with provided settings.
        
        Args:
            settings: Application settings
        
        Returns:
            Configured agent instance
        """
        return build_agent(settings)
    
    @lru_cache(maxsize=1)
    def get_cached_agent(self, settings_hash: str):
        """
        Get cached agent instance (for same settings).
        Note: This is a simple cache - in production, use a proper cache.
        """
        # This is a placeholder - actual implementation would need
        # to reconstruct settings from hash, which is complex
        # For now, we'll build fresh each time
        pass


# Global instance
agent_service = AgentService()


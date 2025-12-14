"""FastAPI dependencies for dependency injection."""
from typing import Optional
from fastapi import HTTPException
from app.config import Settings, load_settings
from app.api.schemas import ChatRequest


def get_settings_from_env() -> Settings:
    """
    Dependency to load settings from environment variables.
    Raises HTTPException if settings are missing.
    """
    try:
        return load_settings()
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {str(e)}"
        ) from e


def create_settings_from_request(request: ChatRequest) -> Settings:
    """
    Create Settings from request credentials with fallback to environment variables.
    
    Args:
        request: ChatRequest with optional credentials
    
    Returns:
        Settings object with merged credentials
    
    Raises:
        HTTPException: If required credentials are missing
    """
    from app.config import Settings
    
    # Try to get env settings
    try:
        env_settings = load_settings()
    except ValueError:
        env_settings = None
    
    # Merge request credentials with env settings
    final_openai_key = request.openai_api_key
    final_base_url = request.ido_base_url
    final_api_key = request.ido_api_key
    final_api_secret = request.ido_api_secret
    
    if env_settings:
        final_openai_key = final_openai_key or env_settings.openai_api_key
        final_base_url = final_base_url or env_settings.erpnext_base_url
        final_api_key = final_api_key or env_settings.erpnext_api_key
        final_api_secret = final_api_secret or env_settings.erpnext_api_secret
    
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
        raise HTTPException(
            status_code=400,
            detail=(
                f"Missing required credentials: {', '.join(missing)}. "
                "Provide them in the request or set as environment variables."
            )
        )
    
    # Use default values for other settings
    default_timeout = 120
    default_max_records = 100
    default_max_iterations = 10
    default_filter_types = (
        "Data", "Date", "Datetime", "DateTime", "Link", "Select", "Int", "Float"
    )
    
    # Override with env settings if available
    if env_settings:
        default_timeout = env_settings.request_timeout
        default_max_records = env_settings.max_records_limit
        default_max_iterations = env_settings.max_iterations
        default_filter_types = env_settings.filter_field_types
    
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


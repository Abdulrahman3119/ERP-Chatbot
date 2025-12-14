import os
from dataclasses import dataclass
from typing import Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in the project root (parent of app directory)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    openai_api_key: str
    erpnext_base_url: str
    erpnext_api_key: str
    erpnext_api_secret: str
    request_timeout: int = 120
    max_records_limit: int = 100
    max_iterations: int = 10
    filter_field_types: Tuple[str, ...] = (
        "Data",
        "Date",
        "Datetime",
        "DateTime",
        "Link",
        "Select",
        "Int",
        "Float",
    )


def load_settings() -> Settings:
    """Load settings from environment variables (optional - can be overridden by request).
    
    Returns Settings with environment variable values, or raises ValueError if none are set.
    This is used as a fallback when credentials are not provided in the request.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    erpnext_base_url = os.getenv("ERPNEXT_BASE_URL")
    erpnext_api_key = os.getenv("ERPNEXT_API_KEY")
    erpnext_api_secret = os.getenv("ERPNEXT_API_SECRET")

    # If no environment variables are set, raise error
    # (credentials must come from request or env)
    if not any([openai_api_key, erpnext_base_url, erpnext_api_key, erpnext_api_secret]):
        raise ValueError(
            "No credentials provided. Either set environment variables or provide credentials in the request."
        )

    # Use empty strings as defaults if not set (will be overridden by request if provided)
    return Settings(
        openai_api_key=openai_api_key or "",
        erpnext_base_url=erpnext_base_url or "",
        erpnext_api_key=erpnext_api_key or "",
        erpnext_api_secret=erpnext_api_secret or "",
    )


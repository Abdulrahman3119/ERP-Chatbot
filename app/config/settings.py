import os
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    openai_api_key: str
    erpnext_base_url: str
    erpnext_api_key: str
    erpnext_api_secret: str
    request_timeout: int = 15
    max_records_limit: int = 100
    max_iterations: int = 10
    filter_field_types: Tuple[str, ...] = (
        "Data",
        "Date",
        "Link",
        "Select",
        "Int",
        "Float",
    )


def load_settings() -> Settings:
    """Load settings from environment variables with basic validation."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    erpnext_base_url = os.getenv("ERPNEXT_BASE_URL")
    erpnext_api_key = os.getenv("ERPNEXT_API_KEY")
    erpnext_api_secret = os.getenv("ERPNEXT_API_SECRET")

    missing = [
        name
        for name, value in {
            "OPENAI_API_KEY": openai_api_key,
            "ERPNEXT_BASE_URL": erpnext_base_url,
            "ERPNEXT_API_KEY": erpnext_api_key,
            "ERPNEXT_API_SECRET": erpnext_api_secret,
        }.items()
        if not value
    ]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return Settings(
        openai_api_key=openai_api_key,
        erpnext_base_url=erpnext_base_url,
        erpnext_api_key=erpnext_api_key,
        erpnext_api_secret=erpnext_api_secret,
    )


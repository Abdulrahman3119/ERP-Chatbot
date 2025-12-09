import json
from datetime import datetime

from langchain_core.tools import tool

from app.application.doctype_service import DocTypeService


def build_tools(service: DocTypeService):
    """Create LangChain tool wrappers bound to the DocType service."""

    @tool
    def analyze_doctype(name: str) -> str:
        """Checks if a DocType exists in ERPNext and returns its fields."""
        try:
            result = service.analyze_doctype(name)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def get_doctype_info(doctype: str, filter_fields=None, filters=None) -> str:
        """Fetches documents for a given DocType with optional field filtering."""
        try:
            result = service.get_doctype_info(doctype, filter_fields, filters)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return json.dumps(
                {"error": True, "doctype": doctype, "message": str(exc)},
                ensure_ascii=False,
            )

    @tool
    def fetch_doctype_with_filters(doctype_name: str) -> str:
        """Fetches DocType data and applies automatic filtering."""
        try:
            result = service.fetch_doctype_with_filters(doctype_name)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a given city (demo tool)."""
        return f"It's always sunny in {city}!"

    @tool
    def get_current_time() -> str:
        """Get the current time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return [
        analyze_doctype,
        get_doctype_info,
        fetch_doctype_with_filters,
        get_weather,
        get_current_time,
    ]


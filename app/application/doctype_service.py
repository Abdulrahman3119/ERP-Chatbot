import json
from typing import Dict, List, Optional, Sequence

from app.infrastructure.erpnext_client import ERPNextClient


class DocTypeService:
    """Application service encapsulating DocType operations."""

    def __init__(self, client: ERPNextClient, filter_field_types: Sequence[str]):
        self.client = client
        self.filter_field_types = filter_field_types

    def analyze_doctype(self, name: str) -> Dict:
        """Return info about a DocType and suggested filters."""
        data = self.client.get(
            "/api/resource/DocType",
            params={"fields": json.dumps(["name"]), "limit_page_length": 0},
        )

        doctypes_list = [d["name"] for d in data.get("data", [])]
        normalized = name.lower()
        normalized_doctypes = {d.lower(): d for d in doctypes_list}

        if normalized in normalized_doctypes:
            doctype_name = normalized_doctypes[normalized]
            fields_data = self.client.get(
                f"/api/resource/DocType/{doctype_name}",
                params={"fields": json.dumps(["fields"])},
            )
            fields = fields_data.get("data", {}).get("fields", [])
            filter_fields = [
                field.get("fieldname")
                for field in fields
                if field.get("fieldtype") in self.filter_field_types
            ]

            return {
                "exists": True,
                "matched_doctype": doctype_name,
                "all_fields": [field.get("fieldname") for field in fields],
                "filter_fields": filter_fields[:10],
            }

        close_matches = get_close_matches(name, doctypes_list, n=5, cutoff=0.4)
        return {
            "exists": False,
            "input": name,
            "suggestions": close_matches,
        }

    def get_doctype_info(
        self,
        doctype: str,
        filter_fields: Optional[List[str]] = None,
        filters: Optional[List[List]] = None,
    ) -> Dict:
        """Fetch documents for a DocType, optionally applying filters."""
        params = {"limit_page_length": 0}
        if filter_fields:
            params["fields"] = json.dumps(filter_fields)
        if filters:
            params["filters"] = json.dumps(filters)

        data = self.client.get(f"/api/resource/{doctype}", params)
        documents = data.get("data", [])

        return {
            "doctype": doctype,
            "count": len(documents),
            "total_available": data.get("total_count", len(documents)),
            "documents": documents,
        }

    def fetch_doctype_with_filters(self, doctype_name: str) -> Dict:
        """Analyze a DocType and fetch filtered data in one step."""
        analysis = self.analyze_doctype(doctype_name)
        if not analysis.get("exists"):
            return analysis

        matched_doctype = analysis["matched_doctype"]
        filter_fields = analysis.get("filter_fields") or []
        doctype_data = self.get_doctype_info(matched_doctype, filter_fields)

        if doctype_data.get("error"):
            return doctype_data

        filtered_data = doctype_data.get("documents", [])
        applied_filter = None
        if filter_fields and filtered_data:
            first_filter = filter_fields[0]
            filtered_data = [record for record in filtered_data if record.get(first_filter)]
            applied_filter = first_filter

        return {
            "doctype": matched_doctype,
            "total_records": doctype_data.get("count", 0),
            "filtered_records": len(filtered_data),
            "applied_filter": applied_filter,
            "records": filtered_data[:20],
        }


def get_close_matches(word: str, possibilities: List[str], n: int = 3, cutoff: float = 0.6) -> List[str]:
    """Thin wrapper to avoid importing difflib at presentation layer."""
    from difflib import get_close_matches as difflib_get_close_matches

    return difflib_get_close_matches(word, possibilities, n=n, cutoff=cutoff)


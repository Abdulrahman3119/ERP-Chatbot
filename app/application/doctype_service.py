import json
from typing import Dict, List, Optional, Sequence

from app.infrastructure.ido_client import IDOClient


class DocTypeService:
    """Application service encapsulating DocType operations."""

    def __init__(self, client: IDOClient, filter_field_types: Sequence[str]):
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
            
            # Also identify date/datetime fields explicitly
            date_fields = [
                field.get("fieldname")
                for field in fields
                if field.get("fieldtype") in ["Date", "Datetime", "DateTime"]
            ]

            return {
                "exists": True,
                "matched_doctype": doctype_name,
                "all_fields": [field.get("fieldname") for field in fields],
                "filter_fields": filter_fields[:10],
                "date_fields": date_fields,  # Explicitly list date fields
            }

        close_matches = get_close_matches(name, doctypes_list, n=5, cutoff=0.4)
        return {
            "exists": False,
            "input": name,
            "suggestions": close_matches,
        }

    def analyze_doctype_for_creation(self, name: str) -> Dict:
        """Analyze DocType fields to identify required and optional fields for record creation.
        
        Returns detailed field information including:
        - Required fields (mandatory)
        - Optional fields
        - Field types and constraints
        - Default values
        - Read-only fields (should be excluded)
        """
        analysis = self.analyze_doctype(name)
        if not analysis.get("exists"):
            return analysis
        
        doctype_name = analysis["matched_doctype"]
        
        # Get detailed field information
        fields_data = self.client.get(
            f"/api/resource/DocType/{doctype_name}",
            params={"fields": json.dumps(["fields"])},
        )
        fields = fields_data.get("data", {}).get("fields", [])
        
        # Categorize fields
        required_fields = []
        optional_fields = []
        read_only_fields = []
        field_details = {}
        
        # Fields to exclude from creation (system fields)
        excluded_fields = {
            "name", "creation", "modified", "modified_by", "owner", 
            "docstatus", "idx", "doctype", "parent", "parentfield", 
            "parenttype", "amended_from"
        }
        
        for field in fields:
            fieldname = field.get("fieldname")
            if not fieldname or fieldname in excluded_fields:
                continue
            
            fieldtype = field.get("fieldtype", "")
            reqd = field.get("reqd", 0)  # Required flag
            read_only = field.get("read_only", 0)  # Read-only flag
            default = field.get("default", None)
            options = field.get("options", "")  # For Select fields
            label = field.get("label", fieldname)
            
            field_info = {
                "fieldname": fieldname,
                "label": label,
                "fieldtype": fieldtype,
                "default": default,
                "options": options if options else None,
                "description": field.get("description", ""),
            }
            
            field_details[fieldname] = field_info
            
            if read_only:
                read_only_fields.append(fieldname)
            elif reqd:
                required_fields.append(fieldname)
            else:
                optional_fields.append(fieldname)
        
        return {
            "exists": True,
            "doctype": doctype_name,
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "read_only_fields": read_only_fields,
            "field_details": field_details,
            "summary": {
                "total_fields": len(field_details),
                "required_count": len(required_fields),
                "optional_count": len(optional_fields),
                "read_only_count": len(read_only_fields),
            }
        }

    def create_doctype_record(
        self, 
        doctype: str, 
        data: Dict,
        validate: bool = True
    ) -> Dict:
        """Create a new record in the specified DocType.
        
        Args:
            doctype: Name of the DocType
            data: Dictionary of field values for the new record
            validate: Whether to validate required fields before creation
            
        Returns:
            Dictionary with created record data or error information
        """
        try:
            # Validate required fields if requested
            if validate:
                analysis = self.analyze_doctype_for_creation(doctype)
                if not analysis.get("exists"):
                    return {
                        "error": True,
                        "message": f"DocType '{doctype}' not found",
                        "suggestions": analysis.get("suggestions", []),
                    }
                
                required_fields = analysis.get("required_fields", [])
                missing_fields = [
                    field for field in required_fields 
                    if field not in data or data.get(field) is None or data.get(field) == ""
                ]
                
                if missing_fields:
                    field_details = analysis.get("field_details", {})
                    missing_info = [
                        {
                            "field": field,
                            "label": field_details.get(field, {}).get("label", field),
                            "type": field_details.get(field, {}).get("fieldtype", "Unknown"),
                        }
                        for field in missing_fields
                    ]
                    return {
                        "error": True,
                        "message": f"Missing required fields: {', '.join(missing_fields)}",
                        "missing_fields": missing_info,
                        "required_fields": required_fields,
                    }
            
            # Create the record via POST request
            endpoint = f"/api/resource/{doctype}"
            response = self.client.post(endpoint, data=data)
            
            return {
                "success": True,
                "doctype": doctype,
                "record": response.get("data", {}),
                "name": response.get("data", {}).get("name"),
                "message": f"Record created successfully in {doctype}",
            }
            
        except Exception as exc:
            error_msg = str(exc)
            # Try to extract more detailed error from response if available
            if hasattr(exc, 'response') and hasattr(exc.response, 'json'):
                try:
                    error_data = exc.response.json()
                    error_msg = error_data.get("exc_type", error_msg)
                    if "message" in error_data:
                        error_msg = error_data["message"]
                except:
                    pass
            
            return {
                "error": True,
                "doctype": doctype,
                "message": f"Failed to create record: {error_msg}",
            }

    def get_doctype_info(
        self,
        doctype: str,
        filter_fields: Optional[List[str]] = None,
        filters: Optional[List[List]] = None,
        limit: Optional[int] = None,
    ) -> Dict:
        """Fetch documents for a DocType, optionally applying filters.
        
        Args:
            doctype: Name of the DocType
            filter_fields: List of field names to include in response
            filters: List of filters in format [[doctype, field, operator, value], ...]
            limit: Maximum number of records to return (0 = no limit)
        """
        params = {}
        
        # Set limit (0 means no limit in IDO/ERPNext)
        if limit is not None:
            params["limit_page_length"] = limit
        else:
            params["limit_page_length"] = 0  # Default to no limit
        
        # Add field filtering
        if filter_fields:
            # Validate and clean field names
            valid_fields = [f for f in filter_fields if f]
            if valid_fields:
                params["fields"] = json.dumps(valid_fields)
        
        # Add filters - IDO/ERPNext expects filters as JSON array
        if filters:
            # Validate filter format
            validated_filters = []
            for filter_item in filters:
                if isinstance(filter_item, list) and len(filter_item) >= 3:
                    # Ensure filter has at least [doctype, field, operator, value]
                    if len(filter_item) == 3:
                        # If only 3 items, assume [field, operator, value] and prepend doctype
                        validated_filters.append([doctype] + filter_item)
                    elif len(filter_item) >= 4:
                        # Full format [doctype, field, operator, value]
                        validated_filters.append(filter_item[:4])
            
            if validated_filters:
                params["filters"] = json.dumps(validated_filters)
                # Debug: log the filters being sent (remove in production if needed)
                import logging
                logging.debug(f"Applying filters to {doctype}: {params['filters']}")

        try:
            data = self.client.get(f"/api/resource/{doctype}", params)
            documents = data.get("data", [])

            return {
                "doctype": doctype,
                "count": len(documents),
                "total_available": data.get("total_count", len(documents)),
                "documents": documents,
                "filters_applied": bool(filters),
                "fields_requested": filter_fields,
            }
        except Exception as exc:
            return {
                "error": True,
                "doctype": doctype,
                "message": str(exc),
                "count": 0,
                "documents": [],
            }

    def fetch_doctype_with_filters(
        self, 
        doctype_name: str, 
        filters: Optional[List[List]] = None,
        filter_fields: Optional[List[str]] = None
    ) -> Dict:
        """Analyze a DocType and fetch filtered data in one step.
        
        Args:
            doctype_name: Name of the DocType to fetch
            filters: Optional list of filters in format [[doctype, field, operator, value], ...]
            filter_fields: Optional list of fields to include in response
        """
        analysis = self.analyze_doctype(doctype_name)
        if not analysis.get("exists"):
            return analysis

        matched_doctype = analysis["matched_doctype"]
        
        # Use provided filter_fields or get from analysis
        if filter_fields is None:
            filter_fields = analysis.get("filter_fields") or []
        
        # Fetch data with proper server-side filtering
        doctype_data = self.get_doctype_info(
            matched_doctype, 
            filter_fields=filter_fields if filter_fields else None,
            filters=filters
        )

        if doctype_data.get("error"):
            return doctype_data

        documents = doctype_data.get("documents", [])

        return {
            "doctype": matched_doctype,
            "total_records": doctype_data.get("count", 0),
            "total_available": doctype_data.get("total_available", 0),
            "filtered_records": len(documents),
            "applied_filters": filters if filters else None,
            "filter_fields_used": filter_fields,
            "records": documents[:100],  # Return more records, limit to 100
        }


def get_close_matches(word: str, possibilities: List[str], n: int = 3, cutoff: float = 0.6) -> List[str]:
    """Thin wrapper to avoid importing difflib at presentation layer."""
    from difflib import get_close_matches as difflib_get_close_matches

    return difflib_get_close_matches(word, possibilities, n=n, cutoff=cutoff)


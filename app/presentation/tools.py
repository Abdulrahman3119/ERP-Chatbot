import json
from datetime import datetime, timedelta

from langchain_core.tools import tool

from app.application.doctype_service import DocTypeService
from app.application.report_service import ReportService


def build_tools(service: DocTypeService, report_service: ReportService):
    """Create LangChain tool wrappers bound to the DocType and Report services."""

    @tool
    def analyze_doctype(name: str) -> str:
        """Checks if a DocType exists in IDO and returns its fields.
        
        This is CRITICAL for date queries - use this to find the correct date field name
        before building date filters. Look for fields with types: Date, Datetime, or fields
        with names containing 'date', 'time', 'created', 'modified', 'scheduled'.
        """
        try:
            result = service.analyze_doctype(name)
            # Enhance result with date field suggestions
            if result.get("exists"):
                all_fields = result.get("all_fields", [])
                # Find potential date fields
                date_field_candidates = [
                    f for f in all_fields 
                    if any(keyword in f.lower() for keyword in ['date', 'time', 'created', 'modified', 'scheduled', 'due'])
                ]
                if date_field_candidates:
                    result["suggested_date_fields"] = date_field_candidates[:5]
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def analyze_doctype_for_creation(name: str) -> str:
        """Analyze a DocType to understand required and optional fields for creating new records.
        
        Use this BEFORE creating a new record to understand:
        - Which fields are required (must be provided)
        - Which fields are optional
        - Field types and constraints
        - Default values
        
        Returns detailed field information to guide record creation.
        """
        try:
            result = service.analyze_doctype_for_creation(name)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def create_doctype_record(doctype: str, data: str, validate: bool = True) -> str:
        """Create a new record in a DocType.
        
        IMPORTANT WORKFLOW:
        1. FIRST call analyze_doctype_for_creation(doctype) to understand required fields
        2. Collect all required field values from the user
        3. Optionally collect optional field values
        4. Call this function with the data as a JSON string
        
        Args:
            doctype: Name of the DocType (e.g., "Cleaning Work Order")
            data: JSON string containing field values (e.g., '{"customer": "ABC Corp", "date": "2024-01-15"}')
            validate: Whether to validate required fields (default: True)
        
        Returns:
            JSON string with created record information or error details
        """
        try:
            data_dict = json.loads(data) if isinstance(data, str) else data
            result = service.create_doctype_record(doctype, data_dict, validate=validate)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as exc:
            return json.dumps({
                "error": True,
                "message": f"Invalid JSON in data parameter: {str(exc)}",
            }, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({
                "error": True,
                "message": str(exc),
            }, ensure_ascii=False)

    @tool
    def get_doctype_info(
        doctype: str, 
        filter_fields: str = None, 
        filters: str = None,
        limit: int = None
    ) -> str:
        """Fetches documents for a given DocType with optional field filtering and filters.
        
        IMPORTANT: If filtering by date (today, yesterday, etc.):
        1. FIRST call get_current_time() to get the actual current date
        2. Use the current_date from get_current_time() in your filters
        3. Then call this function with the date filters
        
        Args:
            doctype: Name of the DocType (e.g., "Cleaning Work Order")
            filter_fields: Optional JSON string array of field names to include (e.g., '["name", "date", "status"]')
            filters: Optional JSON string of filters in format [[doctype, field, operator, value], ...]
                    Example: '[["Cleaning Work Order", "date", ">=", "2024-01-15"], ["Cleaning Work Order", "date", "<=", "2024-01-15"]]'
            limit: Optional maximum number of records to return
        """
        try:
            field_list = json.loads(filter_fields) if filter_fields else None
            filter_list = json.loads(filters) if filters else None
            result = service.get_doctype_info(
                doctype, 
                filter_fields=field_list, 
                filters=filter_list,
                limit=limit
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as exc:
            return json.dumps(
                {"error": True, "doctype": doctype, "message": f"Invalid JSON: {str(exc)}"},
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps(
                {"error": True, "doctype": doctype, "message": str(exc)},
                ensure_ascii=False,
            )

    @tool
    def fetch_doctype_with_filters(
        doctype_name: str, 
        filters: str = None,
        filter_fields: str = None
    ) -> str:
        """Fetches DocType data with optional filters.
        
        Args:
            doctype_name: Name of the DocType to fetch
            filters: Optional JSON string of filters in format [[doctype, field, operator, value], ...]
            filter_fields: Optional JSON string array of field names to include
        """
        try:
            filter_list = json.loads(filters) if filters else None
            field_list = json.loads(filter_fields) if filter_fields else None
            result = service.fetch_doctype_with_filters(
                doctype_name, 
                filters=filter_list,
                filter_fields=field_list
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as exc:
            return json.dumps({
                "error": True, 
                "message": f"Invalid JSON in filters or filter_fields: {str(exc)}"
            }, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def generate_report(
        report_type: str,
        doctype: str,
        filters: str = None,
        group_by: str = None,
        include_summary: bool = True,
    ) -> str:
        """Generate a comprehensive report from IDO data with high accuracy.
        
        Args:
            report_type: Type of report (e.g., 'sales', 'inventory', 'financial', 'custom')
            doctype: The DocType to generate report from
            filters: JSON string of filters to apply (optional)
            group_by: Field to group results by (optional)
            include_summary: Whether to include summary statistics (default: True)
        """
        try:
            filter_dict = json.loads(filters) if filters else None
            result = report_service.generate_report(
                report_type=report_type,
                doctype=doctype,
                filters=filter_dict,
                group_by=group_by,
                include_summary=include_summary,
            )
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def build_date_filter(date_field: str, date_type: str = "today", doctype: str = None) -> str:
        """Build a date filter for IDO queries. This tool automatically gets the current date.
        
        IMPORTANT: This tool internally gets the current date, so you don't need to call get_current_time() first.
        However, if you need the date for display in your response, still call get_current_time().
        
        Args:
            date_field: The name of the date field to filter on (e.g., 'creation', 'date', 'scheduled_date')
            date_type: Type of date filter - 'today', 'yesterday', 'this_week', 'this_month', 'this_year'
            doctype: Optional DocType name (will be added to filter if provided)
        
        Returns:
            JSON string of filter in format [[doctype, field, operator, value], ...]
            For "today", returns two filters: [>= today_start] and [<= today_end]
        """
        try:
            # Get current time first
            now = datetime.now()
            
            filters = []
            
            if date_type == "today":
                # Filter for today: use ISO date format (YYYY-MM-DD)
                # Use range filter to handle both Date and DateTime fields
                today_date = now.strftime("%Y-%m-%d")
                today_start = f"{today_date} 00:00:00"
                today_end = f"{today_date} 23:59:59"
                
                if doctype:
                    # Use range filter: >= start of day AND <= end of day
                    # This works for both Date and DateTime fields
                    filters.append([doctype, date_field, ">=", today_start])
                    filters.append([doctype, date_field, "<=", today_end])
                else:
                    filters.append([date_field, ">=", today_start])
                    filters.append([date_field, "<=", today_end])
            elif date_type == "yesterday":
                yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
                if doctype:
                    filters.append([doctype, date_field, ">=", yesterday + " 00:00:00"])
                    filters.append([doctype, date_field, "<=", yesterday + " 23:59:59"])
                else:
                    filters.append([date_field, ">=", yesterday + " 00:00:00"])
                    filters.append([date_field, "<=", yesterday + " 23:59:59"])
            elif date_type == "this_week":
                # Start of week (Monday)
                days_since_monday = now.weekday()
                week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")
                if doctype:
                    filters.append([doctype, date_field, ">=", week_start])
                else:
                    filters.append([date_field, ">=", week_start])
            elif date_type == "this_month":
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")
                if doctype:
                    filters.append([doctype, date_field, ">=", month_start])
                else:
                    filters.append([date_field, ">=", month_start])
            elif date_type == "this_year":
                year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")
                if doctype:
                    filters.append([doctype, date_field, ">=", year_start])
                else:
                    filters.append([date_field, ">=", year_start])
            else:
                # Default to today
                today_date = now.strftime("%Y-%m-%d")
                today_start = f"{today_date} 00:00:00"
                today_end = f"{today_date} 23:59:59"
                if doctype:
                    filters.append([doctype, date_field, ">=", today_start])
                    filters.append([doctype, date_field, "<=", today_end])
                else:
                    filters.append([date_field, ">=", today_start])
                    filters.append([date_field, "<=", today_end])
            
            return json.dumps(filters, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"error": True, "message": str(exc)}, ensure_ascii=False)

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a given city (demo tool)."""
        return f"It's always sunny in {city}!"

    @tool
    def get_current_time() -> str:
        """MANDATORY: Get the current date and time. 
        
        YOU MUST CALL THIS TOOL FIRST when the user asks about:
        - "today", "yesterday", "tomorrow"
        - "this week", "this month", "this year"
        - Any relative date reference
        - Date-based queries like "how many X today"
        
        Returns JSON with current date information including:
        - current_date: "YYYY-MM-DD" format (use this for filters)
        - current_date_display: "Month Day, Year" format (use this in responses)
        - today_start, today_end: For date range filtering
        
        CRITICAL: Never assume the current date. Always call this tool first for date queries.
        """
        now = datetime.now()
        return json.dumps({
            "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_date": now.strftime("%Y-%m-%d"),
            "current_date_display": now.strftime("%B %d, %Y"),
            "current_year": now.year,
            "current_month": now.month,
            "current_day": now.day,
            "day_of_week": now.strftime("%A"),
            "iso_format": now.isoformat(),
            "today_start": now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "today_end": now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat(),
            "yesterday": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        }, ensure_ascii=False)

    return [
        analyze_doctype,
        analyze_doctype_for_creation,
        get_doctype_info,
        fetch_doctype_with_filters,
        create_doctype_record,
        generate_report,
        get_current_time,
        build_date_filter,
        get_weather,
    ]


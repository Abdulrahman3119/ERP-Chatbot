import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app.infrastructure.ido_client import IDOClient
from app.application.doctype_service import DocTypeService


class ReportService:
    """Service for generating comprehensive reports from IDO data."""

    def __init__(self, client: IDOClient, doctype_service: DocTypeService):
        self.client = client
        self.doctype_service = doctype_service

    def generate_report(
        self,
        report_type: str,
        doctype: str,
        filters: Optional[Dict] = None,
        group_by: Optional[str] = None,
        include_summary: bool = True,
    ) -> Dict:
        """Generate a comprehensive report with high accuracy.
        
        Args:
            report_type: Type of report (sales, inventory, financial, custom)
            doctype: The DocType to generate report from
            filters: Dictionary of filters to apply
            group_by: Field to group results by
            include_summary: Whether to include summary statistics
            
        Returns:
            Dictionary containing formatted report data
        """
        try:
            # First verify the DocType exists
            analysis = self.doctype_service.analyze_doctype(doctype)
            if not analysis.get("exists"):
                return {
                    "error": True,
                    "message": f"DocType '{doctype}' not found",
                    "suggestions": analysis.get("suggestions", []),
                }

            matched_doctype = analysis["matched_doctype"]
            all_fields = analysis.get("all_fields", [])
            
            # Determine relevant fields based on report type
            relevant_fields = self._get_relevant_fields(report_type, all_fields, matched_doctype)
            
            # Build filters
            filter_list = self._build_filters(filters, matched_doctype, all_fields)
            
            # Fetch data
            data = self.doctype_service.get_doctype_info(
                matched_doctype,
                filter_fields=relevant_fields,
                filters=filter_list if filter_list else None,
            )
            
            documents = data.get("documents", [])
            
            # Process and format the report
            report_data = self._process_report_data(
                documents=documents,
                report_type=report_type,
                doctype=matched_doctype,
                group_by=group_by,
                include_summary=include_summary,
                relevant_fields=relevant_fields,
            )
            
            return report_data
            
        except Exception as exc:
            return {
                "error": True,
                "message": f"Error generating report: {str(exc)}",
            }

    def _get_relevant_fields(
        self, report_type: str, all_fields: List[str], doctype: str
    ) -> List[str]:
        """Determine relevant fields based on report type."""
        # Common important fields
        common_fields = ["name", "creation", "modified", "owner", "status"]
        
        # Type-specific field patterns
        type_patterns = {
            "sales": ["customer", "total", "amount", "grand_total", "net_total", "date", "status"],
            "inventory": ["item", "quantity", "warehouse", "stock", "rate", "amount"],
            "financial": ["account", "debit", "credit", "balance", "amount", "party"],
            "custom": [],
        }
        
        relevant = set(common_fields)
        patterns = type_patterns.get(report_type.lower(), [])
        
        # Find matching fields
        for field in all_fields:
            field_lower = field.lower()
            if any(pattern in field_lower for pattern in patterns):
                relevant.add(field)
        
        # Always include filterable fields
        analysis = self.doctype_service.analyze_doctype(doctype)
        filter_fields = analysis.get("filter_fields", [])
        relevant.update(filter_fields[:10])
        
        return list(relevant)[:20]  # Limit to 20 fields

    def _build_filters(
        self, filters: Optional[Dict], doctype: str, all_fields: List[str]
    ) -> Optional[List[List]]:
        """Build filter list from dictionary with proper validation.
        
        IDO/ERPNext filter format: [[doctype, field, operator, value], ...]
        Valid operators: =, !=, >, <, >=, <=, like, not like, in, not in, is, is not
        """
        if not filters:
            return None
        
        filter_list = []
        for key, value in filters.items():
            # Validate field exists
            if key not in all_fields:
                # Try case-insensitive match
                key_lower = key.lower()
                matching_field = next(
                    (f for f in all_fields if f.lower() == key_lower), 
                    None
                )
                if not matching_field:
                    # Skip invalid fields but log for debugging
                    continue
                key = matching_field
            
            # Handle different value types
            if isinstance(value, dict):
                # Handle operators like {"<": "2024-01-01"} or {"in": ["val1", "val2"]}
                for op, val in value.items():
                    # Validate operator
                    valid_operators = ["=", "!=", ">", "<", ">=", "<=", "like", "not like", "in", "not in", "is", "is not"]
                    if op.lower() in [o.lower() for o in valid_operators]:
                        # Find exact operator match
                        op_match = next((o for o in valid_operators if o.lower() == op.lower()), "=")
                        filter_list.append([doctype, key, op_match, val])
            elif isinstance(value, list):
                # Handle list values (use "in" operator)
                if value:  # Only add if list is not empty
                    filter_list.append([doctype, key, "in", value])
            elif value is not None:
                # Default to equality operator
                filter_list.append([doctype, key, "=", value])
        
        return filter_list if filter_list else None

    def _process_report_data(
        self,
        documents: List[Dict],
        report_type: str,
        doctype: str,
        group_by: Optional[str],
        include_summary: bool,
        relevant_fields: List[str],
    ) -> Dict:
        """Process and format report data with summaries and insights."""
        if not documents:
            return {
                "report_type": report_type,
                "doctype": doctype,
                "total_records": 0,
                "message": "No data found matching the criteria",
                "summary": {},
                "data": [],
            }
        
        # Group data if requested
        grouped_data = {}
        if group_by and group_by in relevant_fields:
            for doc in documents:
                key = doc.get(group_by, "Unknown")
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(doc)
        else:
            grouped_data["All"] = documents
        
        # Calculate summary statistics
        summary = {}
        if include_summary:
            summary = self._calculate_summary(documents, relevant_fields, report_type)
        
        # Format report sections
        sections = []
        for group_key, group_docs in grouped_data.items():
            sections.append({
                "group": group_key,
                "count": len(group_docs),
                "records": group_docs[:50],  # Limit records per group
            })
        
        return {
            "report_type": report_type,
            "doctype": doctype,
            "generated_at": datetime.now().isoformat(),
            "total_records": len(documents),
            "grouped_by": group_by,
            "summary": summary,
            "sections": sections,
            "key_insights": self._generate_insights(documents, summary, report_type),
        }

    def _calculate_summary(
        self, documents: List[Dict], relevant_fields: List[str], report_type: str
    ) -> Dict:
        """Calculate summary statistics."""
        summary = {
            "total_count": len(documents),
        }
        
        # Find numeric fields for calculations
        numeric_fields = []
        for field in relevant_fields:
            if any(term in field.lower() for term in ["amount", "total", "quantity", "rate", "price", "cost", "debit", "credit", "balance"]):
                numeric_fields.append(field)
        
        # Calculate totals and averages
        for field in numeric_fields[:5]:  # Limit to 5 numeric fields
            values = []
            for doc in documents:
                val = doc.get(field)
                if val is not None:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        pass
            
            if values:
                summary[f"{field}_total"] = sum(values)
                summary[f"{field}_average"] = sum(values) / len(values) if values else 0
                summary[f"{field}_min"] = min(values)
                summary[f"{field}_max"] = max(values)
                summary[f"{field}_count"] = len(values)
        
        # Date-based statistics
        date_fields = [f for f in relevant_fields if "date" in f.lower() or "creation" in f.lower()]
        if date_fields:
            date_field = date_fields[0]
            dates = []
            for doc in documents:
                date_str = doc.get(date_field)
                if date_str:
                    try:
                        dates.append(datetime.fromisoformat(date_str.replace("Z", "+00:00")))
                    except (ValueError, AttributeError):
                        pass
            
            if dates:
                summary["earliest_date"] = min(dates).isoformat()
                summary["latest_date"] = max(dates).isoformat()
                summary["date_range_days"] = (max(dates) - min(dates)).days
        
        return summary

    def _generate_insights(
        self, documents: List[Dict], summary: Dict, report_type: str
    ) -> List[str]:
        """Generate key insights from the data."""
        insights = []
        
        if summary.get("total_count", 0) == 0:
            insights.append("No records found matching the criteria.")
            return insights
        
        # Count-based insights
        total = summary.get("total_count", 0)
        insights.append(f"Total records analyzed: {total}")
        
        # Numeric insights
        for key, value in summary.items():
            if key.endswith("_total") and isinstance(value, (int, float)):
                field_name = key.replace("_total", "")
                avg = summary.get(f"{field_name}_average", 0)
                insights.append(f"{field_name.title()}: Total = {value:,.2f}, Average = {avg:,.2f}")
        
        # Date range insights
        if "date_range_days" in summary:
            days = summary["date_range_days"]
            insights.append(f"Data spans {days} days")
        
        return insights[:10]  # Limit to 10 insights


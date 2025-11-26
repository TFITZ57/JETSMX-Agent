"""
Airtable formula query builder for programmatic filter construction.
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime


class QueryBuilder:
    """Build complex Airtable formulas programmatically."""
    
    @staticmethod
    def equals(field: str, value: Any) -> str:
        """Field equals value."""
        if isinstance(value, str):
            return f"{{{field}}} = '{value}'"
        elif isinstance(value, bool):
            return f"{{{field}}} = {str(value).upper()}"
        elif value is None:
            return f"{{{field}}} = BLANK()"
        else:
            return f"{{{field}}} = {value}"
    
    @staticmethod
    def not_equals(field: str, value: Any) -> str:
        """Field not equals value."""
        if isinstance(value, str):
            return f"{{{field}}} != '{value}'"
        elif isinstance(value, bool):
            return f"{{{field}}} != {str(value).upper()}"
        elif value is None:
            return f"{{{field}}} != BLANK()"
        else:
            return f"{{{field}}} != {value}"
    
    @staticmethod
    def contains(field: str, value: str) -> str:
        """Field contains substring."""
        return f"FIND('{value}', {{{field}}}) > 0"
    
    @staticmethod
    def greater_than(field: str, value: Union[int, float, str]) -> str:
        """Field greater than value."""
        if isinstance(value, str):
            return f"{{{field}}} > '{value}'"
        return f"{{{field}}} > {value}"
    
    @staticmethod
    def less_than(field: str, value: Union[int, float, str]) -> str:
        """Field less than value."""
        if isinstance(value, str):
            return f"{{{field}}} < '{value}'"
        return f"{{{field}}} < {value}"
    
    @staticmethod
    def greater_or_equal(field: str, value: Union[int, float, str]) -> str:
        """Field greater than or equal to value."""
        if isinstance(value, str):
            return f"{{{field}}} >= '{value}'"
        return f"{{{field}}} >= {value}"
    
    @staticmethod
    def less_or_equal(field: str, value: Union[int, float, str]) -> str:
        """Field less than or equal to value."""
        if isinstance(value, str):
            return f"{{{field}}} <= '{value}'"
        return f"{{{field}}} <= {value}"
    
    @staticmethod
    def is_empty(field: str) -> str:
        """Field is empty/blank."""
        return f"{{{field}}} = BLANK()"
    
    @staticmethod
    def is_not_empty(field: str) -> str:
        """Field is not empty."""
        return f"{{{field}}} != BLANK()"
    
    @staticmethod
    def in_list(field: str, values: List[Any]) -> str:
        """Field value is in list of values."""
        conditions = [QueryBuilder.equals(field, v) for v in values]
        return QueryBuilder.or_(*conditions)
    
    @staticmethod
    def and_(*conditions: str) -> str:
        """Combine conditions with AND."""
        if len(conditions) == 0:
            return ""
        if len(conditions) == 1:
            return conditions[0]
        return f"AND({', '.join(conditions)})"
    
    @staticmethod
    def or_(*conditions: str) -> str:
        """Combine conditions with OR."""
        if len(conditions) == 0:
            return ""
        if len(conditions) == 1:
            return conditions[0]
        return f"OR({', '.join(conditions)})"
    
    @staticmethod
    def not_(condition: str) -> str:
        """Negate a condition."""
        return f"NOT({condition})"
    
    @staticmethod
    def date_is_after(field: str, date: Union[str, datetime]) -> str:
        """Date field is after given date."""
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        return f"IS_AFTER({{{field}}}, '{date}')"
    
    @staticmethod
    def date_is_before(field: str, date: Union[str, datetime]) -> str:
        """Date field is before given date."""
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        return f"IS_BEFORE({{{field}}}, '{date}')"
    
    @staticmethod
    def date_is_same(field: str, date: Union[str, datetime], unit: str = "day") -> str:
        """Date field is same as given date (day, week, month, year)."""
        if isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        return f"IS_SAME({{{field}}}, '{date}', '{unit}')"


class QueryHelper:
    """High-level query helpers for common patterns."""
    
    @staticmethod
    def find_by_email(email: str) -> str:
        """Find record by email address."""
        return QueryBuilder.equals("Email", email)
    
    @staticmethod
    def find_by_name(name: str) -> str:
        """Find record by name (exact match)."""
        return QueryBuilder.equals("Applicant Name", name)
    
    @staticmethod
    def find_by_name_contains(name: str) -> str:
        """Find records where name contains substring."""
        return QueryBuilder.contains("Applicant Name", name)
    
    @staticmethod
    def find_by_pipeline_stage(stage: str) -> str:
        """Find pipeline records by stage."""
        return QueryBuilder.equals("Pipeline Stage", stage)
    
    @staticmethod
    def find_by_stages(stages: List[str]) -> str:
        """Find pipeline records in any of the given stages."""
        return QueryBuilder.in_list("Pipeline Stage", stages)
    
    @staticmethod
    def find_active_applicants() -> str:
        """Find applicants currently in active pipeline stages."""
        active_stages = [
            "New",
            "Profile Generated",
            "HR Screen – Approved",
            "Outreach Draft Created",
            "Initial Email Sent",
            "Awaiting Applicant Reply",
            "Applicant Responded",
            "Phone Probe Scheduled",
            "Phone Probe Complete",
            "Video Interview Scheduled",
            "Interview Complete"
        ]
        return QueryBuilder.in_list("Pipeline Stage", active_stages)
    
    @staticmethod
    def find_with_faa_ap() -> str:
        """Find applicants with FAA A&P certification."""
        return QueryBuilder.equals("Has FAA A&P", True)
    
    @staticmethod
    def find_contractors_by_status(status: str) -> str:
        """Find contractors by status."""
        return QueryBuilder.equals("Contractor Status", status)
    
    @staticmethod
    def find_recent_interactions(days: int = 7) -> str:
        """Find interactions in the last N days."""
        from datetime import datetime, timedelta
        cutoff = datetime.now() - timedelta(days=days)
        return QueryBuilder.date_is_after("Timestamp", cutoff)
    
    @staticmethod
    def build_search_query(
        table: str,
        search_term: str,
        search_fields: Optional[List[str]] = None
    ) -> str:
        """Build a search query across multiple fields."""
        if not search_fields:
            # Default fields by table
            if table.lower() == "applicants":
                search_fields = ["Applicant Name", "Email", "Location"]
            elif table.lower() == "applicant_pipeline":
                search_fields = ["Applicant Name", "Primary Email"]
            elif table.lower() == "contractors":
                search_fields = ["Contractor ID", "Name", "Email"]
            elif table.lower() == "interactions":
                search_fields = ["Summary"]
            else:
                search_fields = []
        
        if not search_fields:
            return ""
        
        conditions = [QueryBuilder.contains(field, search_term) for field in search_fields]
        return QueryBuilder.or_(*conditions)


def build_complex_query(filters: List[Dict[str, Any]], operator: str = "AND") -> str:
    """
    Build a complex query from a list of filter dictionaries.
    
    Args:
        filters: List of filter dicts with keys: field, op, value
        operator: "AND" or "OR" to combine filters
        
    Example:
        filters = [
            {"field": "Has FAA A&P", "op": "equals", "value": True},
            {"field": "Years in Aviation", "op": ">=", "value": 5}
        ]
        query = build_complex_query(filters, "AND")
    """
    conditions = []
    
    for f in filters:
        field = f.get("field")
        op = f.get("op")
        value = f.get("value")
        
        if op == "equals" or op == "==" or op == "=":
            conditions.append(QueryBuilder.equals(field, value))
        elif op == "not_equals" or op == "!=" or op == "≠":
            conditions.append(QueryBuilder.not_equals(field, value))
        elif op == "contains":
            conditions.append(QueryBuilder.contains(field, value))
        elif op == ">" or op == "greater_than":
            conditions.append(QueryBuilder.greater_than(field, value))
        elif op == "<" or op == "less_than":
            conditions.append(QueryBuilder.less_than(field, value))
        elif op == ">=" or op == "greater_or_equal":
            conditions.append(QueryBuilder.greater_or_equal(field, value))
        elif op == "<=" or op == "less_or_equal":
            conditions.append(QueryBuilder.less_or_equal(field, value))
        elif op == "is_empty":
            conditions.append(QueryBuilder.is_empty(field))
        elif op == "is_not_empty":
            conditions.append(QueryBuilder.is_not_empty(field))
        elif op == "in":
            conditions.append(QueryBuilder.in_list(field, value))
        elif op == "date_after":
            conditions.append(QueryBuilder.date_is_after(field, value))
        elif op == "date_before":
            conditions.append(QueryBuilder.date_is_before(field, value))
    
    if not conditions:
        return ""
    
    if operator.upper() == "AND":
        return QueryBuilder.and_(*conditions)
    else:
        return QueryBuilder.or_(*conditions)


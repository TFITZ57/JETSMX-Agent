"""
Main Airtable Agent - Central orchestration layer for all Airtable operations.
"""
from typing import Dict, Any, Optional, List
from agents.airtable.conversational import ConversationalAgent
from agents.airtable.query_engine import QueryEngine, QueryPlanner
from agents.airtable.bulk_operations import BulkOperationManager
from tools.airtable.export import (
    export_to_csv,
    export_to_json,
    export_to_excel,
    ExportFormatter
)
from tools.airtable.analytics import Analytics, PipelineAnalytics, ApplicantAnalytics
from tools.airtable.schema import get_schema_manager
from tools.airtable_tools import (
    create_record,
    update_record,
    get_record,
    find_records
)
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger
from shared.logging.audit import log_audit_event

logger = setup_logger(__name__)
settings = get_settings()


class AirtableAgent:
    """
    Central Airtable Agent providing both conversational and programmatic interfaces.
    
    Capabilities:
    - Natural language queries via conversational mode
    - Direct programmatic operations
    - Advanced filtering and aggregation
    - Bulk operations with validation
    - Data export in multiple formats
    - Schema introspection
    """
    
    def __init__(self, base_id: Optional[str] = None):
        """
        Initialize the Airtable Agent.
        
        Args:
            base_id: Airtable base ID (defaults to settings)
        """
        self.base_id = base_id or settings.airtable_base_id
        
        # Core components
        self.conversational = ConversationalAgent()
        self.query_engine = QueryEngine(self.base_id)
        self.query_planner = QueryPlanner(self.query_engine)
        self.bulk_ops = BulkOperationManager(self.base_id)
        self.schema = get_schema_manager()
        
        logger.info(f"Airtable Agent initialized for base {self.base_id}")
    
    # ========================================================================
    # CONVERSATIONAL INTERFACE
    # ========================================================================
    
    def ask(self, question: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Natural language interface - ask questions in plain English.
        
        Args:
            question: Natural language question
            conversation_history: Optional conversation history
            
        Returns:
            Natural language response
            
        Examples:
            >>> agent.ask("How many applicants do we have?")
            "You have 47 applicants in the database."
            
            >>> agent.ask("Show me applicants with FAA A&P")
            "Found 23 applicants with FAA A&P certification..."
        """
        return self.conversational.query(question, conversation_history)
    
    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================
    
    def query(
        self,
        table: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        formula: Optional[str] = None,
        max_records: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query records from a table.
        
        Args:
            table: Table name
            filters: List of filter dicts (field, op, value)
            formula: Raw Airtable formula
            max_records: Maximum records to return
            sort: List of (field, direction) tuples
            
        Returns:
            List of records
        """
        if filters:
            return self.query_engine.filter_query(table, filters, max_records=max_records)
        else:
            return self.query_engine.simple_query(
                table,
                formula=formula,
                max_records=max_records,
                sort=sort
            )
    
    def search(
        self,
        table: str,
        search_term: str,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for records containing a term.
        
        Args:
            table: Table name
            search_term: Text to search for
            fields: Fields to search in (defaults to all searchable fields)
            
        Returns:
            List of matching records
        """
        return self.query_engine.search(table, search_term, fields)
    
    def get(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by ID.
        
        Args:
            table: Table name
            record_id: Record ID
            
        Returns:
            Record dict or None
        """
        return self.query_engine.get_by_id(table, record_id)
    
    def find_by_email(self, table: str, email: str) -> List[Dict[str, Any]]:
        """Find records by email address."""
        return self.query_engine.get_by_email(table, email)
    
    def find_by_name(
        self,
        table: str,
        name: str,
        exact: bool = True
    ) -> List[Dict[str, Any]]:
        """Find records by name (exact or partial match)."""
        return self.query_engine.get_by_name(table, name, exact)
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def create(
        self,
        table: str,
        fields: Dict[str, Any],
        initiated_by: str = "airtable_agent",
        reason: str = "Record creation"
    ) -> Dict[str, Any]:
        """
        Create a new record.
        
        Args:
            table: Table name
            fields: Field values
            initiated_by: Who initiated this
            reason: Reason for creation
            
        Returns:
            Created record
        """
        # Audit log
        log_audit_event(
            action="create_record",
            resource_type="airtable_record",
            resource_id=f"{table}:new",
            initiated_by=initiated_by,
            details={"table": table, "reason": reason}
        )
        
        return create_record(self.base_id, table, fields)
    
    def update(
        self,
        table: str,
        record_id: str,
        fields: Dict[str, Any],
        replace: bool = False,
        initiated_by: str = "airtable_agent",
        reason: str = "Record update"
    ) -> Dict[str, Any]:
        """
        Update an existing record.
        
        Args:
            table: Table name
            record_id: Record ID
            fields: Fields to update
            replace: If True, replace all fields. If False, merge.
            initiated_by: Who initiated this
            reason: Reason for update
            
        Returns:
            Updated record
        """
        # Audit log
        log_audit_event(
            action="update_record",
            resource_type="airtable_record",
            resource_id=f"{table}:{record_id}",
            initiated_by=initiated_by,
            details={"table": table, "reason": reason, "replace": replace}
        )
        
        return update_record(self.base_id, table, record_id, fields, replace)
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    def bulk_create(
        self,
        table: str,
        records: List[Dict[str, Any]],
        **kwargs
    ):
        """Create multiple records in batch."""
        return self.bulk_ops.create_many(table, records, **kwargs)
    
    def bulk_update(
        self,
        table: str,
        updates: List[Dict[str, Any]],
        **kwargs
    ):
        """Update multiple records in batch."""
        return self.bulk_ops.update_many(table, updates, **kwargs)
    
    def bulk_delete(
        self,
        table: str,
        record_ids: List[str],
        **kwargs
    ):
        """Delete multiple records in batch."""
        return self.bulk_ops.delete_many(table, record_ids, **kwargs)
    
    def upsert(
        self,
        table: str,
        records: List[Dict[str, Any]],
        key_field: str,
        **kwargs
    ):
        """Upsert (update or insert) records based on key field."""
        return self.bulk_ops.upsert_many(table, records, key_field, **kwargs)
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def count(
        self,
        table: str,
        filters: Optional[List[Dict]] = None
    ) -> int:
        """Count records matching criteria."""
        records = self.query(table, filters=filters)
        return len(records)
    
    def aggregate(
        self,
        table: str,
        agg_type: str,
        field: str,
        group_by: Optional[str] = None,
        filters: Optional[List[Dict]] = None
    ) -> Any:
        """
        Perform aggregation on records.
        
        Args:
            table: Table name
            agg_type: "count", "sum", "avg", "min", "max"
            field: Field to aggregate
            group_by: Field to group by (optional)
            filters: Optional filters
            
        Returns:
            Aggregation result
        """
        records = self.query(table, filters=filters)
        
        if group_by:
            if agg_type == "count":
                return Analytics.count_by_field(records, group_by)
            elif agg_type == "sum":
                return Analytics.group_and_sum(records, group_by, field)
            elif agg_type == "avg":
                return Analytics.group_and_average(records, group_by, field)
        else:
            if agg_type == "count":
                return len(records)
            elif agg_type == "sum":
                return Analytics.sum_field(records, field)
            elif agg_type == "avg":
                return Analytics.average_field(records, field)
            elif agg_type == "min":
                return Analytics.min_field(records, field)
            elif agg_type == "max":
                return Analytics.max_field(records, field)
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def export(
        self,
        table: str,
        format: str = "csv",
        filters: Optional[List[Dict]] = None
    ) -> str:
        """
        Export records to CSV, JSON, or Excel.
        
        Args:
            table: Table name
            format: "csv", "json", or "excel"
            filters: Optional filters
            
        Returns:
            Exported data as string (or base64 for Excel)
        """
        records = self.query(table, filters=filters)
        
        if format == "csv":
            return export_to_csv(records)
        elif format == "json":
            return export_to_json(records)
        elif format == "excel":
            import base64
            data = export_to_excel(records)
            return base64.b64encode(data).decode()
        else:
            raise ValueError(f"Unknown export format: {format}")
    
    # ========================================================================
    # SCHEMA OPERATIONS
    # ========================================================================
    
    def get_schema(self, table: Optional[str] = None) -> Any:
        """
        Get schema information.
        
        Args:
            table: Table name (None for all tables)
            
        Returns:
            Schema description
        """
        if table:
            return self.schema.describe_table(table)
        else:
            return self.schema.describe_all_tables()
    
    def get_tables(self) -> List[str]:
        """Get list of all tables."""
        return self.schema.get_tables()
    
    def validate(self, table: str, fields: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate fields against schema.
        
        Args:
            table: Table name
            fields: Field values to validate
            
        Returns:
            (is_valid, list_of_errors)
        """
        return self.schema.validate_record(table, fields)


# ========================================================================
# GLOBAL INSTANCE
# ========================================================================

_airtable_agent = None


def get_airtable_agent() -> AirtableAgent:
    """Get or create the global Airtable agent instance."""
    global _airtable_agent
    if _airtable_agent is None:
        _airtable_agent = AirtableAgent()
    return _airtable_agent


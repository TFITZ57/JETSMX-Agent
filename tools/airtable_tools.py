"""
Airtable API wrapper tools for JetsMX Agent Framework.

Provides typed, retry-enabled functions for interacting with Airtable bases,
tables, and records. All functions include structured logging and error handling.
"""
from typing import Dict, List, Optional, Any
from pyairtable import Api
from pyairtable.api.base import Base
from pyairtable.api.table import Table
from pyairtable.models import fields
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from shared.config.settings import get_settings
from shared.config.constants import MAX_RETRIES, RETRY_BACKOFF_FACTOR, RETRY_MIN_WAIT, RETRY_MAX_WAIT
from shared.logging.logger import setup_logger, log_with_context

logger = setup_logger(__name__)
settings = get_settings()

# Retry policy for transient failures
retry_policy = retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=RETRY_BACKOFF_FACTOR, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError))
)


def _get_api_client() -> Api:
    """
    Get or create Airtable API client.
    
    Returns:
        Configured Airtable API client
    """
    return Api(settings.airtable_api_key)


def _get_base(base_id: Optional[str] = None) -> Base:
    """
    Get Airtable base instance.
    
    Args:
        base_id: Base ID. If None, uses default from settings.
        
    Returns:
        Airtable Base instance
    """
    api = _get_api_client()
    base_id = base_id or settings.airtable_base_id
    return api.base(base_id)


def _get_table(base_id: str, table_name: str) -> Table:
    """
    Get Airtable table instance.
    
    Args:
        base_id: Base ID
        table_name: Table name or ID
        
    Returns:
        Airtable Table instance
    """
    base = _get_base(base_id)
    return base.table(table_name)


@retry_policy
def list_bases() -> List[Dict[str, Any]]:
    """
    List all Airtable bases accessible with the configured API key.
    
    Returns:
        List of base metadata dicts with 'id' and 'name' keys
        
    Raises:
        Exception: If API call fails after retries
    """
    try:
        api = _get_api_client()
        bases = api.bases()
        
        result = [{"id": base.id, "name": base.name} for base in bases]
        
        log_with_context(
            logger, "info", "Listed Airtable bases",
            count=len(result)
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to list Airtable bases",
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def list_tables(base_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all tables in an Airtable base.
    
    Args:
        base_id: Base ID. If None, uses default from settings.
        
    Returns:
        List of table metadata dicts with 'id' and 'name' keys
        
    Raises:
        Exception: If API call fails after retries
    """
    base_id = base_id or settings.airtable_base_id
    
    try:
        base = _get_base(base_id)
        tables = base.tables()
        
        result = [{"id": table.id, "name": table.name} for table in tables]
        
        log_with_context(
            logger, "info", "Listed Airtable tables",
            base_id=base_id,
            count=len(result)
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to list Airtable tables",
            base_id=base_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def get_record(
    base_id: str,
    table: str,
    record_id: str
) -> Dict[str, Any]:
    """
    Fetch a single record from Airtable by ID.
    
    Args:
        base_id: Airtable base ID
        table: Table name or ID
        record_id: Record ID to fetch
        
    Returns:
        Record dict with 'id', 'fields', and 'createdTime' keys
        
    Raises:
        Exception: If record not found or API call fails
    """
    try:
        table_instance = _get_table(base_id, table)
        record = table_instance.get(record_id)
        
        result = {
            "id": record["id"],
            "fields": record["fields"],
            "createdTime": record.get("createdTime")
        }
        
        log_with_context(
            logger, "info", "Fetched Airtable record",
            base_id=base_id,
            table=table,
            record_id=record_id,
            field_count=len(result["fields"])
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to fetch Airtable record",
            base_id=base_id,
            table=table,
            record_id=record_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def find_records(
    base_id: str,
    table: str,
    formula: Optional[str] = None,
    view: Optional[str] = None,
    max_records: Optional[int] = None,
    sort: Optional[List[tuple]] = None
) -> List[Dict[str, Any]]:
    """
    Find records in an Airtable table with optional filters.
    
    Args:
        base_id: Airtable base ID
        table: Table name or ID
        formula: Airtable formula for filtering (e.g., "{Email}='test@example.com'")
        view: View name to use for filtering/sorting
        max_records: Maximum number of records to return
        sort: List of (field_name, direction) tuples, e.g., [("Name", "asc")]
        
    Returns:
        List of record dicts with 'id', 'fields', and 'createdTime' keys
        
    Raises:
        Exception: If API call fails after retries
    """
    try:
        table_instance = _get_table(base_id, table)
        
        # Build query parameters
        kwargs = {}
        if formula:
            kwargs["formula"] = formula
        if view:
            kwargs["view"] = view
        if max_records:
            kwargs["max_records"] = max_records
        if sort:
            kwargs["sort"] = sort
        
        records = table_instance.all(**kwargs)
        
        result = [
            {
                "id": record["id"],
                "fields": record["fields"],
                "createdTime": record.get("createdTime")
            }
            for record in records
        ]
        
        log_with_context(
            logger, "info", "Found Airtable records",
            base_id=base_id,
            table=table,
            formula=formula,
            view=view,
            count=len(result)
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to find Airtable records",
            base_id=base_id,
            table=table,
            formula=formula,
            view=view,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def create_record(
    base_id: str,
    table: str,
    fields: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new record in an Airtable table.
    
    Args:
        base_id: Airtable base ID
        table: Table name or ID
        fields: Dict of field names to values
        
    Returns:
        Created record dict with 'id', 'fields', and 'createdTime' keys
        
    Raises:
        Exception: If creation fails or validation errors occur
    """
    try:
        table_instance = _get_table(base_id, table)
        record = table_instance.create(fields)
        
        result = {
            "id": record["id"],
            "fields": record["fields"],
            "createdTime": record.get("createdTime")
        }
        
        log_with_context(
            logger, "info", "Created Airtable record",
            base_id=base_id,
            table=table,
            record_id=result["id"],
            field_count=len(fields)
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to create Airtable record",
            base_id=base_id,
            table=table,
            field_count=len(fields),
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def update_record(
    base_id: str,
    table: str,
    record_id: str,
    fields: Dict[str, Any],
    replace: bool = False
) -> Dict[str, Any]:
    """
    Update an existing record in an Airtable table.
    
    Args:
        base_id: Airtable base ID
        table: Table name or ID
        record_id: Record ID to update
        fields: Dict of field names to new values
        replace: If True, replace all fields. If False, merge with existing.
        
    Returns:
        Updated record dict with 'id', 'fields', and 'createdTime' keys
        
    Raises:
        Exception: If update fails or record not found
    """
    try:
        table_instance = _get_table(base_id, table)
        
        if replace:
            record = table_instance.update(record_id, fields, replace=True)
        else:
            record = table_instance.update(record_id, fields)
        
        result = {
            "id": record["id"],
            "fields": record["fields"],
            "createdTime": record.get("createdTime")
        }
        
        log_with_context(
            logger, "info", "Updated Airtable record",
            base_id=base_id,
            table=table,
            record_id=record_id,
            field_count=len(fields),
            replace=replace
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to update Airtable record",
            base_id=base_id,
            table=table,
            record_id=record_id,
            field_count=len(fields),
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def batch_update(
    base_id: str,
    table: str,
    records: List[Dict[str, Any]],
    replace: bool = False
) -> List[Dict[str, Any]]:
    """
    Batch update multiple records in an Airtable table.
    
    Args:
        base_id: Airtable base ID
        table: Table name or ID
        records: List of dicts with 'id' and 'fields' keys
        replace: If True, replace all fields. If False, merge with existing.
        
    Returns:
        List of updated record dicts with 'id', 'fields', and 'createdTime' keys
        
    Raises:
        Exception: If batch update fails
        
    Example:
        records = [
            {"id": "rec123", "fields": {"Status": "Complete"}},
            {"id": "rec456", "fields": {"Status": "In Progress"}}
        ]
        batch_update(base_id, "Tasks", records)
    """
    try:
        table_instance = _get_table(base_id, table)
        
        updated_records = table_instance.batch_update(records, replace=replace)
        
        result = [
            {
                "id": record["id"],
                "fields": record["fields"],
                "createdTime": record.get("createdTime")
            }
            for record in updated_records
        ]
        
        log_with_context(
            logger, "info", "Batch updated Airtable records",
            base_id=base_id,
            table=table,
            count=len(records),
            replace=replace
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to batch update Airtable records",
            base_id=base_id,
            table=table,
            count=len(records),
            error=str(e),
            error_type=type(e).__name__
        )
        raise


# Additional convenience function for batch create
@retry_policy
def batch_create(
    base_id: str,
    table: str,
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Batch create multiple records in an Airtable table.
    
    Args:
        base_id: Airtable base ID
        table: Table name or ID
        records: List of dicts with 'fields' key containing field values
        
    Returns:
        List of created record dicts with 'id', 'fields', and 'createdTime' keys
        
    Raises:
        Exception: If batch create fails
        
    Example:
        records = [
            {"fields": {"Name": "John", "Email": "john@example.com"}},
            {"fields": {"Name": "Jane", "Email": "jane@example.com"}}
        ]
        batch_create(base_id, "Applicants", records)
    """
    try:
        table_instance = _get_table(base_id, table)
        
        created_records = table_instance.batch_create(records)
        
        result = [
            {
                "id": record["id"],
                "fields": record["fields"],
                "createdTime": record.get("createdTime")
            }
            for record in created_records
        ]
        
        log_with_context(
            logger, "info", "Batch created Airtable records",
            base_id=base_id,
            table=table,
            count=len(records)
        )
        
        return result
        
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to batch create Airtable records",
            base_id=base_id,
            table=table,
            count=len(records),
            error=str(e),
            error_type=type(e).__name__
        )
        raise


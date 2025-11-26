"""
Pydantic models for Airtable Agent REST API requests.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Natural language query request."""
    query: str = Field(..., description="Natural language query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Optional conversation history"
    )


class AdvancedQueryRequest(BaseModel):
    """Structured query with filters and sorting."""
    table: str = Field(..., description="Table name to query")
    filters: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of filters (field, op, value)"
    )
    formula: Optional[str] = Field(
        None,
        description="Raw Airtable formula"
    )
    search_term: Optional[str] = Field(
        None,
        description="Text to search for"
    )
    search_fields: Optional[List[str]] = Field(
        None,
        description="Fields to search in"
    )
    max_records: Optional[int] = Field(
        100,
        description="Maximum records to return",
        ge=1,
        le=1000
    )
    sort: Optional[List[tuple]] = Field(
        None,
        description="List of (field, direction) tuples"
    )


class RecordCreateRequest(BaseModel):
    """Request to create a record."""
    fields: Dict[str, Any] = Field(..., description="Field values for new record")
    initiated_by: str = Field("api_user", description="Who is initiating this")
    reason: str = Field("API create request", description="Reason for creation")


class RecordUpdateRequest(BaseModel):
    """Request to update a record."""
    fields: Dict[str, Any] = Field(..., description="Fields to update")
    replace: bool = Field(False, description="Replace all fields or merge")
    initiated_by: str = Field("api_user", description="Who is initiating this")
    reason: str = Field("API update request", description="Reason for update")


class BulkCreateRequest(BaseModel):
    """Request to create multiple records."""
    table: str = Field(..., description="Table name")
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of record dicts with 'fields' key"
    )
    batch_size: int = Field(10, description="Records per batch", ge=1, le=100)
    validate: bool = Field(True, description="Validate before creating")
    initiated_by: str = Field("api_user", description="Who is initiating this")
    reason: str = Field("Bulk create via API", description="Reason for bulk create")


class BulkUpdateRequest(BaseModel):
    """Request to update multiple records."""
    table: str = Field(..., description="Table name")
    updates: List[Dict[str, Any]] = Field(
        ...,
        description="List of dicts with 'id' and 'fields' keys"
    )
    batch_size: int = Field(10, description="Records per batch", ge=1, le=100)
    validate: bool = Field(True, description="Validate before updating")
    replace: bool = Field(False, description="Replace all fields or merge")
    initiated_by: str = Field("api_user", description="Who is initiating this")
    reason: str = Field("Bulk update via API", description="Reason for bulk update")


class BulkDeleteRequest(BaseModel):
    """Request to delete multiple records."""
    table: str = Field(..., description="Table name")
    record_ids: List[str] = Field(..., description="List of record IDs to delete")
    batch_size: int = Field(10, description="Records per batch", ge=1, le=100)
    initiated_by: str = Field("api_user", description="Who is initiating this")
    reason: str = Field("Bulk delete via API", description="Reason for bulk delete")
    confirm: bool = Field(
        False,
        description="Must be True to execute delete"
    )


class ExportRequest(BaseModel):
    """Request to export data."""
    table: str = Field(..., description="Table name")
    format: str = Field("csv", description="Export format (csv, json, excel)")
    filters: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional filters"
    )
    include_id: bool = Field(True, description="Include record ID column")
    max_records: Optional[int] = Field(
        None,
        description="Maximum records to export"
    )


class AnalyticsRequest(BaseModel):
    """Request to run analytics query."""
    table: str = Field(..., description="Table name")
    agg_type: str = Field(
        ...,
        description="Aggregation type (count, sum, avg, min, max)"
    )
    field: Optional[str] = Field(None, description="Field to aggregate")
    group_by: Optional[str] = Field(None, description="Field to group by")
    filters: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional filters"
    )


class UpsertRequest(BaseModel):
    """Request to upsert records."""
    table: str = Field(..., description="Table name")
    records: List[Dict[str, Any]] = Field(
        ...,
        description="List of record dicts with 'fields' key"
    )
    key_field: str = Field(..., description="Field to use for matching existing records")
    batch_size: int = Field(10, description="Records per batch", ge=1, le=100)
    initiated_by: str = Field("api_user", description="Who is initiating this")
    reason: str = Field("Upsert via API", description="Reason for upsert")


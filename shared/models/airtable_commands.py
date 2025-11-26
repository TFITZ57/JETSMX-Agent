"""
Pydantic models for Airtable Agent Pub/Sub commands.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AirtableCommand(BaseModel):
    """Base model for Airtable commands via Pub/Sub."""
    command_id: str = Field(..., description="Unique command ID")
    command_type: str = Field(..., description="Type of command")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Command timestamp")
    initiated_by: str = Field("pubsub_system", description="Who initiated this command")
    callback_url: Optional[str] = Field(None, description="URL to post results to")
    callback_topic: Optional[str] = Field(None, description="Pub/Sub topic to publish results to")


class QueryCommand(AirtableCommand):
    """Command to query records."""
    command_type: str = "query"
    table: str = Field(..., description="Table name")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Filters")
    max_records: Optional[int] = Field(100, description="Max records")


class BulkCreateCommand(AirtableCommand):
    """Command to bulk create records."""
    command_type: str = "bulk_create"
    table: str = Field(..., description="Table name")
    records: List[Dict[str, Any]] = Field(..., description="Records to create")
    batch_size: int = Field(10, description="Batch size")
    validate: bool = Field(True, description="Validate before creating")


class BulkUpdateCommand(AirtableCommand):
    """Command to bulk update records."""
    command_type: str = "bulk_update"
    table: str = Field(..., description="Table name")
    updates: List[Dict[str, Any]] = Field(..., description="Updates to apply")
    batch_size: int = Field(10, description="Batch size")
    validate: bool = Field(True, description="Validate before updating")
    replace: bool = Field(False, description="Replace all fields or merge")


class BulkDeleteCommand(AirtableCommand):
    """Command to bulk delete records."""
    command_type: str = "bulk_delete"
    table: str = Field(..., description="Table name")
    record_ids: List[str] = Field(..., description="Record IDs to delete")
    batch_size: int = Field(10, description="Batch size")


class ExportCommand(AirtableCommand):
    """Command to export data."""
    command_type: str = "export"
    table: str = Field(..., description="Table name")
    format: str = Field("csv", description="Export format")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Filters")
    upload_to: Optional[str] = Field(None, description="Cloud Storage path to upload to")


class AnalyticsCommand(AirtableCommand):
    """Command to run analytics."""
    command_type: str = "analytics"
    table: str = Field(..., description="Table name")
    agg_type: str = Field(..., description="Aggregation type")
    field: Optional[str] = Field(None, description="Field to aggregate")
    group_by: Optional[str] = Field(None, description="Field to group by")
    filters: Optional[List[Dict[str, Any]]] = Field(None, description="Filters")


class CommandResult(BaseModel):
    """Result of a command execution."""
    command_id: str = Field(..., description="Original command ID")
    success: bool = Field(..., description="Whether command succeeded")
    result: Optional[Any] = Field(None, description="Command result")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Result timestamp")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")


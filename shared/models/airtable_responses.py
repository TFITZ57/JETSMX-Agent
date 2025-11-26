"""
Pydantic models for Airtable Agent REST API responses.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    """Response from natural language query."""
    success: bool = Field(..., description="Whether query succeeded")
    response: str = Field(..., description="Natural language response")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for follow-up")


class RecordsResponse(BaseModel):
    """Response with list of records."""
    success: bool = Field(..., description="Whether query succeeded")
    count: int = Field(..., description="Number of records returned")
    records: List[Dict[str, Any]] = Field(..., description="List of records")
    has_more: bool = Field(False, description="Whether there are more records")


class RecordResponse(BaseModel):
    """Response with single record."""
    success: bool = Field(..., description="Whether operation succeeded")
    record: Optional[Dict[str, Any]] = Field(None, description="Record data")
    error: Optional[str] = Field(None, description="Error message if failed")


class BulkOperationResponse(BaseModel):
    """Response from bulk operation."""
    success: bool = Field(..., description="Whether operation succeeded")
    successful: List[Dict[str, Any]] = Field(..., description="Successfully processed records")
    failed: List[Dict[str, Any]] = Field(..., description="Failed records")
    errors: List[str] = Field(..., description="Error messages")
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")
    total_count: int = Field(..., description="Total operations attempted")
    success_rate: float = Field(..., description="Success rate percentage")


class ExportResponse(BaseModel):
    """Response from export operation."""
    success: bool = Field(..., description="Whether export succeeded")
    format: str = Field(..., description="Export format")
    record_count: int = Field(..., description="Number of records exported")
    data: str = Field(..., description="Exported data (string or base64)")
    filename: Optional[str] = Field(None, description="Suggested filename")
    error: Optional[str] = Field(None, description="Error message if failed")


class AnalyticsResponse(BaseModel):
    """Response from analytics query."""
    success: bool = Field(..., description="Whether analytics succeeded")
    result: Any = Field(..., description="Analytics result (number or dict)")
    error: Optional[str] = Field(None, description="Error message if failed")


class SchemaResponse(BaseModel):
    """Response with schema information."""
    success: bool = Field(..., description="Whether operation succeeded")
    schema: Any = Field(..., description="Schema information")
    error: Optional[str] = Field(None, description="Error message if failed")


class TablesResponse(BaseModel):
    """Response with list of tables."""
    success: bool = Field(..., description="Whether operation succeeded")
    tables: List[str] = Field(..., description="List of table names")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Agent version")
    base_id: str = Field(..., description="Connected Airtable base ID")
    capabilities: Dict[str, bool] = Field(..., description="Enabled capabilities")


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type/category")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


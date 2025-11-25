"""
Pydantic models for API responses.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Generic API response."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None


class AirtableRecordResponse(BaseModel):
    """Response from Airtable record operations."""
    id: str
    fields: Dict[str, Any]
    created_time: Optional[str] = None


class GmailDraftResponse(BaseModel):
    """Response from Gmail draft creation."""
    draft_id: str
    message_id: str
    thread_id: Optional[str] = None


class GmailMessageResponse(BaseModel):
    """Response from Gmail message operations."""
    message_id: str
    thread_id: str
    label_ids: Optional[List[str]] = None


class CalendarEventResponse(BaseModel):
    """Response from Calendar event operations."""
    event_id: str
    summary: str
    start_time: str
    end_time: str
    meet_link: Optional[str] = None
    attendees: Optional[List[str]] = None


class DriveFileResponse(BaseModel):
    """Response from Drive file operations."""
    file_id: str
    name: str
    mime_type: str
    web_view_link: Optional[str] = None
    download_link: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Response from Chat message posting."""
    message_name: str
    space: str
    created_time: str


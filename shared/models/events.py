"""
Pydantic models for event payloads.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class AirtableWebhookPayload(BaseModel):
    """Payload from Airtable webhook."""
    table_id: str
    record_id: str
    changed_fields: List[str]
    new_values: Dict[str, Any]
    old_values: Optional[Dict[str, Any]] = None


class GmailNotificationPayload(BaseModel):
    """Payload from Gmail push notification."""
    thread_id: str
    message_id: str
    from_email: str = Field(alias="from")
    to_email: str = Field(alias="to")
    subject: str
    body_text: str
    received_at: datetime


class DriveFileCreatedPayload(BaseModel):
    """Payload from Drive file created event."""
    file_id: str
    name: str
    mime_type: str
    parents: List[str]
    created_time: datetime


class ChatCommandPayload(BaseModel):
    """Payload from Google Chat command."""
    space: str
    user: str
    command: str
    args: str
    timestamp: datetime


class PubSubMessage(BaseModel):
    """Pub/Sub message wrapper."""
    data: bytes
    attributes: Optional[Dict[str, str]] = None
    message_id: str
    publish_time: datetime


class EventContext(BaseModel):
    """Context for event processing."""
    event_name: str
    trigger: str
    applicant_pipeline_id: Optional[str] = None
    applicant_id: Optional[str] = None
    file_id: Optional[str] = None
    thread_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

